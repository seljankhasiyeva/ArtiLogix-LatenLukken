import os

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth import verify_token
from app.llm.llm_service import chat, stream_chat

router = APIRouter()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

_sessions: dict[str, list[dict]] = {}


def _get_history(session_id: str) -> list[dict]:
    if session_id not in _sessions:
        _sessions[session_id] = []
    return _sessions[session_id]


class ChatRequest(BaseModel):
    message   : str
    session_id: str = "default"


@router.post("/message")
def send_message(
    req         : ChatRequest,
):
    role    = "logistics" 
    history = _get_history(req.session_id)

    answer, updated = chat(
        user_message = req.message,
        model        = GEMINI_MODEL,
        role         = role,
        history      = history,
    )
    _sessions[req.session_id] = updated

    return {
        "response"  : answer,
        "session_id": req.session_id,
        "role"      : role,
    }


@router.get("/stream")
def stream_message(
    message     : str,
    session_id  : str  = "default",
    current_user: dict = Depends(verify_token),
):
    role    = current_user.get("role", "marketplace")
    history = _get_history(session_id)

    def event_stream():
        for token in stream_chat(
            user_message = message,
            model        = GEMINI_MODEL,
            role         = role,
            history      = history,
        ):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type = "text/event-stream",
        headers    = {
            "Cache-Control"              : "no-cache",
            "X-Accel-Buffering"          : "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.delete("/session/{session_id}")
def clear_session(
    session_id  : str,
    current_user: dict = Depends(verify_token),
):
    _sessions.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}