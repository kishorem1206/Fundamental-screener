# backend/app/services/chat_service.py — Beginner Explanation

> **Source file:** `backend/app/services/chat_service.py`

---

## 1. What is this file?

Database access layer for the AI Chat feature. Manages `chat_sessions` and `chat_messages` tables — creating sessions, storing messages, loading history, and auto-generating titles.

---

## 2. What is a chat session?

A session is a conversation thread. Each session:
- Has a unique UUID `id`
- Has an auto-generated `title` (first 60 chars of the first user message)
- Tracks `message_count` and `last_active_at`

---

## 3. Key operations

### `create_session(title=None) → dict`
Creates a new row in `chat_sessions`. The title is optional — if not provided, it's set automatically when the first user message arrives.

### `add_message(session_id, role, content, intent_type=None) → dict`
Stores one message and increments `message_count` on the parent session. Also bumps `last_active_at` so sessions are sorted by recency in the sidebar.

```python
if not session.title and role == "user":
    session.title = content[:60]
```

The first user message in a session auto-titles the chat.

### `get_messages(session_id, limit=50) → list[dict]`
Returns messages ordered by `created_at` ascending — oldest first, so the chat renders in the right order.

### `delete_session(session_id) → bool`
Deletes the session row; `chat_messages` rows cascade-delete automatically (see the `ondelete="CASCADE"` foreign key in models.py).

---

## 4. Database pattern

Uses the existing `get_db()` factory with manual `try/finally` cleanup:

```python
db = get_db()
try:
    ...do work...
    db.commit()
finally:
    db.close()
```

This is the same pattern used by `ClassificationService` and `StockSeedLoader`.

---

## 5. `_session_dict` / `_msg_dict`

Converts SQLAlchemy ORM objects to plain Python dicts. This avoids returning ORM objects outside the DB session (which would cause `DetachedInstanceError`). The route layer serialises these dicts to JSON via FastAPI's JSONResponse.
