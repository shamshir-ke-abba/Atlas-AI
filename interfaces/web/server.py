"""
Atlas V3 Browser API

Headless FastAPI interface for LAN/browser clients.
"""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import MODEL_NAME, OLLAMA_HOST, WEB_HOST, WEB_PORT
from core.logger import get_logger
from interfaces.web.runtime import WebAtlasRuntime


logger = get_logger("web")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Atlas AI Browser API",
    version="3.2",
)

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)

runtime = WebAtlasRuntime()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None


class ConversationRequest(BaseModel):
    session_id: Optional[str] = None


class ToolRunRequest(BaseModel):
    session_id: Optional[str] = None
    action: str = ""
    expression: str = ""
    arguments: Dict[str, Any] = Field(default_factory=dict)


def session_id_from(
    request: Request,
    supplied: Optional[str] = None,
) -> str:
    if supplied:
        return supplied

    header = request.headers.get("X-Atlas-Session")
    if header:
        return header

    return secrets.token_urlsafe(18)


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico")
def favicon():
    path = STATIC_DIR / "favicon.ico"
    if path.exists():
        return FileResponse(path)
    raise HTTPException(404)


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "atlas-web",
        "version": "3.2",
        "model": MODEL_NAME,
        "ollama": OLLAMA_HOST,
        "host": WEB_HOST,
        "port": WEB_PORT,
    }


@app.get("/api/status")
def status(request: Request):
    sid = session_id_from(request)
    return runtime.status(sid)


@app.get("/api/tools")
def tools():
    return {
        "tools": runtime.tools.metadata(),
        "status": runtime.tools.status(),
    }


@app.get("/api/memory")
def memory():
    return {
        "memory": runtime.memory.all(),
    }


@app.post("/api/tools/{tool_name}/run")
def run_tool(
    tool_name: str,
    payload: ToolRunRequest,
    request: Request,
):
    sid = session_id_from(request, payload.session_id)

    try:
        return runtime.execute_tool(
            sid,
            tool_name,
            action=payload.action,
            expression=payload.expression,
            arguments=payload.arguments,
        )

    except Exception as exc:
        logger.exception(
            "Browser tool execution failed: %s",
            tool_name,
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.get("/api/conversations")
def conversations():
    data = runtime.conversations()
    result = []

    for conversation_id, item in data.items():
        result.append({
            "id": conversation_id,
            "title": item.get("title", "New Chat"),
            "created": item.get("created"),
            "message_count": len(item.get("messages", [])),
        })

    return {
        "conversations": result,
    }


@app.post("/api/conversations")
def create_conversation(request: ConversationRequest):
    sid = request.session_id or secrets.token_urlsafe(18)
    conversation_id = runtime.create_conversation(sid)

    return {
        "session_id": sid,
        "conversation_id": conversation_id,
    }


@app.get("/api/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    request: Request,
):
    sid = session_id_from(request)

    try:
        messages = runtime.load_conversation(
            sid,
            conversation_id,
        )

        session = runtime.session(sid)

        return {
            "id": conversation_id,
            "title": session.conversation.current_title,
            "messages": messages,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    request: Request,
):
    sid = session_id_from(request)

    try:
        replacement = runtime.delete_conversation(
            sid,
            conversation_id,
        )

        return {
            "ok": True,
            "replacement": replacement,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@app.post("/api/chat")
def chat(request: ChatRequest):
    sid = request.session_id or secrets.token_urlsafe(18)

    def generate():
        for event in runtime.chat_stream(
            sid,
            request.message,
            request.conversation_id,
        ):
            yield (
                json.dumps(
                    event,
                    ensure_ascii=False,
                )
                + "\n"
            )

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Atlas-Session": sid,
        },
    )


@app.post("/stream")
def legacy_stream(request: ChatRequest):
    return chat(request)
