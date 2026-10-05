from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.technical.services.chat_service import chat_service
from app.technical.agents.message_bus import agent_message_bus
from app.technical.shared.schemas import AgentTask
from app.logger import logger

router = APIRouter(prefix="/chat", tags=["chat"])


class CreateSessionRequest(BaseModel):
    title: str | None = None


class SendMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


# ─── Sessions ─────────────────────────────────────────────────────────────────

@router.post("/sessions", status_code=201)
def create_session(body: CreateSessionRequest):
    return chat_service.create_session(title=body.title)


@router.get("/sessions")
def list_sessions(limit: int = 20):
    return {"sessions": chat_service.list_sessions(limit=limit)}


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: str):
    deleted = chat_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")


# ─── Messages ─────────────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: str):
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = chat_service.get_messages(session_id)
    return {"messages": messages}


@router.post("/sessions/{session_id}/messages")
def send_message(session_id: str, body: SendMessageRequest):
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Persist user message
    chat_service.add_message(session_id, role="user", content=body.message)

    # Build history for the LLM (last 20 stored messages)
    history = chat_service.get_messages(session_id, limit=20)
    history_payload = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m["role"] in ("user", "assistant")
    ]

    # Dispatch to chat agent
    result = agent_message_bus.dispatch(AgentTask(
        from_agent="chat_route",
        to_agent="chat_agent",
        task_type="CHAT_TURN",
        payload={
            "user_message": body.message,
            "history": history_payload[:-1],  # exclude the message we just added
        },
    ))

    if result.status == "FAILED":
        err = result.errors[0].message if result.errors else "Chat agent failed"
        logger.error("Chat agent failed", error=err)
        raise HTTPException(status_code=500, detail=err)

    data = result.data or {}
    reply = data.get("reply", "")
    intent = data.get("intent", "GENERAL")

    # Persist assistant response
    chat_service.add_message(session_id, role="assistant", content=reply, intent_type=intent)

    return {
        "role": "assistant",
        "content": reply,
        "intent": intent,
        "session_id": session_id,
    }
