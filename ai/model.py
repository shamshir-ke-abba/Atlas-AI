"""
AtlasAI Model - Local LLM via Ollama
"""

import logging
import requests
from typing import Generator, Optional
from config import MODEL_NAME, OLLAMA_HOST, TEMPERATURE, MAX_TOKENS

logger = logging.getLogger(__name__)


class AtlasModel:
    """Local model interface via Ollama."""
    
    def __init__(self):
        self.model_name = MODEL_NAME
        self.host = OLLAMA_HOST
        self.temperature = TEMPERATURE
        self.max_tokens = MAX_TOKENS

    def generate(self, prompt: str, stream: bool = True) -> Generator[str, None, None]:
        """Generate response from LLM."""
        
        try:
            url = f"{self.host}/api/generate"
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": self.temperature,
                "stream": stream,
            }
            
            response = requests.post(url, json=payload, stream=stream)
            response.raise_for_status()
            
            if stream:
                for line in response.iter_lines():
                    if line:
                        try:
                            import json
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except:
                            pass
            else:
                import json
                data = response.json()
                if "response" in data:
                    yield data["response"]
                    
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.host}")
            yield f"Error: Ollama not running at {self.host}"
        except Exception as e:
            logger.error(f"Model error: {e}")
            yield f"Error: {str(e)}"

    def is_available(self) -> bool:
        """Check if model is available."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False