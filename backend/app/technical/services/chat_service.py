import uuid
from datetime import datetime, timezone
from sqlalchemy import select, desc
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import ChatSession, ChatMessage
from app.logger import logger


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ChatService:

    def create_session(self, title: str | None = None) -> dict:
        session_id = str(uuid.uuid4())
        now = _now()
        db = get_db()
        try:
            session = ChatSession(
                id=session_id,
                title=title,
                llm_provider="gpt-oss",
                message_count=0,
                last_active_at=now,
                created_at=now,
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return self._session_dict(session)
        finally:
            db.close()

    def get_session(self, session_id: str) -> dict | None:
        db = get_db()
        try:
            row = db.get(ChatSession, session_id)
            return self._session_dict(row) if row else None
        finally:
            db.close()

    def list_sessions(self, limit: int = 20) -> list[dict]:
        db = get_db()
        try:
            rows = db.execute(
                select(ChatSession)
                .order_by(desc(ChatSession.last_active_at))
                .limit(limit)
            ).scalars().all()
            return [self._session_dict(r) for r in rows]
        finally:
            db.close()

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent_type: str | None = None,
    ) -> dict:
        msg_id = str(uuid.uuid4())
        now = _now()
        db = get_db()
        try:
            msg = ChatMessage(
                id=msg_id,
                session_id=session_id,
                role=role,
                content=content,
                llm_intent_type=intent_type,
                created_at=now,
            )
            db.add(msg)
            session = db.get(ChatSession, session_id)
            if session:
                session.message_count = (session.message_count or 0) + 1
                session.last_active_at = now
                if not session.title and role == "user":
                    session.title = content[:60]
            db.commit()
            db.refresh(msg)
            return self._msg_dict(msg)
        finally:
            db.close()

    def get_messages(self, session_id: str, limit: int = 50) -> list[dict]:
        db = get_db()
        try:
            rows = db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at)
                .limit(limit)
            ).scalars().all()
            return [self._msg_dict(r) for r in rows]
        finally:
            db.close()

    def delete_session(self, session_id: str) -> bool:
        db = get_db()
        try:
            row = db.get(ChatSession, session_id)
            if not row:
                return False
            db.delete(row)
            db.commit()
            return True
        finally:
            db.close()

    # ─── Serialisers ──────────────────────────────────────────────────────────

    def _session_dict(self, s: ChatSession) -> dict:
        return {
            "id": s.id,
            "title": s.title,
            "llm_provider": s.llm_provider,
            "llm_model": s.llm_model,
            "message_count": s.message_count,
            "last_active_at": s.last_active_at.isoformat() if s.last_active_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }

    def _msg_dict(self, m: ChatMessage) -> dict:
        return {
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role,
            "content": m.content,
            "llm_intent_type": m.llm_intent_type,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }


chat_service = ChatService()
