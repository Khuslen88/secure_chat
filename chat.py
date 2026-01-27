import json
import os
import threading
import uuid
from datetime import datetime, timezone

from config import Config
from security import SecurityUtils


class ConversationManager:
    """Manages AI chat conversation histories.

    Each conversation is stored as a separate JSON file in
    data/conversations/{conversation_id}.json.
    """

    def __init__(self):
        self._lock = threading.Lock()
        os.makedirs(Config.CONVERSATIONS_DIR, exist_ok=True)

    def _conv_path(self, conversation_id):
        return os.path.join(Config.CONVERSATIONS_DIR, f"{conversation_id}.json")

    def _read_conversation(self, conversation_id):
        path = self._conv_path(conversation_id)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    def _write_conversation(self, data):
        path = self._conv_path(data["id"])
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def create_conversation(self):
        """Create a new conversation and return its ID."""
        conv_id = str(uuid.uuid4())
        data = {
            "id": conv_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "messages": [],
        }
        with self._lock:
            self._write_conversation(data)
        return conv_id

    def add_message(self, conversation_id, role, content):
        """Add a message to a conversation.

        User messages are sanitized via SecurityUtils. Returns the message dict.
        """
        if role == "user":
            content = SecurityUtils.sanitize_message(content)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with self._lock:
            data = self._read_conversation(conversation_id)
            if data is None:
                return None
            data["messages"].append(message)
            data["updated_at"] = message["timestamp"]
            self._write_conversation(data)

        return message

    def get_history(self, conversation_id):
        """Get conversation history in Anthropic API format.

        Returns list of {"role": ..., "content": ...} dicts,
        trimmed to MAX_CONVERSATION_HISTORY most recent messages.
        """
        with self._lock:
            data = self._read_conversation(conversation_id)
        if data is None:
            return []

        messages = data["messages"][-Config.MAX_CONVERSATION_HISTORY:]
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    def get_full_conversation(self, conversation_id):
        """Get full conversation data including timestamps."""
        with self._lock:
            return self._read_conversation(conversation_id)

    def list_conversations(self):
        """List all conversations with metadata for the sidebar."""
        result = []
        with self._lock:
            for filename in os.listdir(Config.CONVERSATIONS_DIR):
                if not filename.endswith(".json"):
                    continue
                path = os.path.join(Config.CONVERSATIONS_DIR, filename)
                with open(path, "r") as f:
                    data = json.load(f)
                preview = ""
                if data["messages"]:
                    first_user = next(
                        (m for m in data["messages"] if m["role"] == "user"), None
                    )
                    if first_user:
                        preview = first_user["content"][:80]
                result.append({
                    "id": data["id"],
                    "created_at": data["created_at"],
                    "updated_at": data["updated_at"],
                    "preview": preview,
                    "message_count": len(data["messages"]),
                })
        result.sort(key=lambda c: c["updated_at"], reverse=True)
        return result

    def clear_conversation(self, conversation_id):
        """Delete a conversation file. Returns True if deleted."""
        path = self._conv_path(conversation_id)
        with self._lock:
            if os.path.exists(path):
                os.remove(path)
                return True
        return False
