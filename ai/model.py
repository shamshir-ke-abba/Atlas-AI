"""AtlasAI Model - Local LLM via Ollama
"""

import json
import logging
import socket
import threading
from typing import Generator, Optional
import requests
from config import MODEL_NAME, OLLAMA_HOST, TEMPERATURE, MAX_TOKENS

logger = logging.getLogger(__name__)


class AtlasModel:
    """Local model interface via Ollama with thread-safe socket cancellation."""
    
    def __init__(self):
        self.model_name = MODEL_NAME
        self.host = OLLAMA_HOST
        self.temperature = TEMPERATURE
        self.max_tokens = MAX_TOKENS
        self._lock = threading.Lock()
        self._active_response: Optional[requests.Response] = None
        self._session: Optional[requests.Session] = None
        self._cancelled: bool = False

    def cancel_current(self) -> bool:
        """Thread-safe, idempotent cancellation of the in-flight model request."""
        with self._lock:
            self._cancelled = True
            had_active = False

            resp = self._active_response
            if resp is not None:
                had_active = True
                # Shutdown and close underlying socket to immediately break any blocking reads
                try:
                    fp = getattr(resp.raw, "_fp", None)
                    if fp and hasattr(fp, "fp") and fp.fp:
                        sio = getattr(fp.fp, "raw", None)
                        if sio and hasattr(sio, "_sock") and sio._sock:
                            try:
                                sio._sock.shutdown(socket.SHUT_RDWR)
                            except Exception:
                                pass
                            try:
                                sio._sock.close()
                            except Exception:
                                pass
                except Exception:
                    pass

                try:
                    if hasattr(resp, "raw") and resp.raw is not None:
                        resp.raw.close()
                except Exception:
                    pass

                try:
                    resp.close()
                except Exception:
                    pass

                self._active_response = None

            if self._session is not None:
                had_active = True
                try:
                    self._session.close()
                except Exception:
                    pass
                self._session = None

            if had_active:
                logger.info("Active model request socket cancelled successfully.")
            return had_active

    def generate(self, prompt: str, stream: bool = True) -> Generator[str, None, None]:
        """Generate response from LLM."""
        with self._lock:
            self._cancelled = False
            self._active_response = None
            self._session = requests.Session()
            session = self._session

        try:
            url = f"{self.host}/api/generate"
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": self.temperature,
                "stream": stream,
                "keep_alive": "10m",
                "options": {
                    "num_predict": self.max_tokens,
                },
            }

            with self._lock:
                if self._cancelled:
                    return
            
            response = session.post(
                url,
                json=payload,
                stream=stream,
                timeout=(10, 300),
            )

            with self._lock:
                if self._cancelled:
                    try:
                        response.close()
                    except Exception:
                        pass
                    return
                self._active_response = response

            response.raise_for_status()
            
            if stream:
                for line in response.iter_lines():
                    with self._lock:
                        if self._cancelled:
                            break
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except Exception:
                            pass
            else:
                with self._lock:
                    if self._cancelled:
                        return
                data = response.json()
                if "response" in data:
                    yield data["response"]
                    
        except requests.exceptions.ConnectionError:
            with self._lock:
                cancelled = self._cancelled
            if cancelled:
                logger.info("Model request cancelled (ConnectionError).")
                return
            logger.error(f"Cannot connect to Ollama at {self.host}")
            yield f"Error: Ollama not running at {self.host}"
        except Exception as e:
            with self._lock:
                cancelled = self._cancelled
            if cancelled:
                logger.info("Model request cancelled (%s).", type(e).__name__)
                return
            logger.error(f"Model error: {e}")
            yield f"Error: {str(e)}"
        finally:
            with self._lock:
                if self._active_response is not None:
                    try:
                        self._active_response.close()
                    except Exception:
                        pass
                    self._active_response = None
                if self._session is not None:
                    try:
                        self._session.close()
                    except Exception:
                        pass
                    self._session = None

    def is_available(self) -> bool:
        """Check if model is available."""
        try:
            response = requests.get(
                f"{self.host}/api/tags",
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False
