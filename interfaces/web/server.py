from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import json

from core.logger import get_logger
from interfaces.web.runtime import controller


logger = get_logger("web")


app = FastAPI(
    title="Atlas Web Interface",
    version="1.0",
)


app.mount(
    "/static",
    StaticFiles(
        directory="interfaces/web/static"
    ),
    name="static",
)


@app.on_event("startup")
def startup():

    logger.info(
        "Atlas Web Server started."
    )


@app.on_event("shutdown")
def shutdown():

    logger.info(
        "Atlas Web Server shutting down."
    )


@app.get("/")
def home():

    logger.info(
        "Web interface requested."
    )

    return FileResponse(
        "interfaces/web/static/index.html"
    )


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat(request: ChatRequest):

    logger.info(
        "Chat request received."
    )

    try:

        response = controller.chat(
            request.message
        )

        logger.info(
            "Chat request completed."
        )

        return {
            "response": response
        }

    except Exception:

        logger.exception(
            "Chat request failed."
        )

        raise HTTPException(
            status_code=500,
            detail="Atlas encountered an internal error.",
        )


@app.post("/stream")
def stream(request: ChatRequest):

    logger.info(
        "Streaming request received."
    )

    def generate():

        try:

            for chunk in controller.stream_chat(
                request.message
            ):

                yield (
                    json.dumps(
                        {
                            "chunk": chunk
                        }
                    )
                    + "\n"
                )

            logger.info(
                "Streaming request completed."
            )

        except Exception:

            logger.exception(
                "Streaming request failed."
            )

            # Send an error event to the client
            yield (
                json.dumps(
                    {
                        "error":
                        "Atlas encountered an internal error."
                    }
                )
                + "\n"
            )

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
    )