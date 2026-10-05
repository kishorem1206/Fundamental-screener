# backend/app/routes/chat.py — Beginner Explanation

> **Source file:** `backend/app/routes/chat.py`

---

## 1. What is this file?

Defines the REST endpoints for AI Chat. There are two groups: session management (create/list/delete conversations) and message exchange (send a message, get a response).

---

## 2. Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/chat/sessions` | Create a new chat session |
| GET | `/chat/sessions` | List recent sessions (default 20) |
| GET | `/chat/sessions/{id}` | Get one session |
| DELETE | `/chat/sessions/{id}` | Delete a session and all its messages |
| GET | `/chat/sessions/{id}/messages` | Get message history |
| POST | `/chat/sessions/{id}/messages` | Send a user message, get AI reply |

---

## 3. The send-message flow

```
POST /chat/sessions/{id}/messages
  body: {"message": "Show me oversold stocks"}

1. Validate session exists
2. Persist user message via chat_service.add_message()
3. Load last 20 messages as history
4. Dispatch CHAT_TURN task to chat_agent via AgentMessageBus
5. Persist assistant reply via chat_service.add_message()
6. Return {role, content, intent, session_id}
```

The history passed to the agent excludes the message just added (we send it separately as `user_message`) to avoid sending it twice to the LLM.

---

## 4. Error handling

```python
if result.status == "FAILED":
    raise HTTPException(status_code=500, detail=err)
```

If the LLM call fails (Ollama not running, etc.), a 500 error is returned. The user message is already persisted but the assistant reply is not — the frontend can show an error state.

---

## 5. Session auto-creation

The route requires a pre-existing session ID. The frontend creates a session first (`POST /chat/sessions`) before sending the first message, or the `ChatPanel` component auto-creates one if the user types without selecting a session.
