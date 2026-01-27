import json
import os
import threading
import uuid
from datetime import datetime, timezone


DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "messages.json")


class ChatManager:
    """Handles message storage and retrieval."""

    def __init__(self):
        self._lock = threading.Lock()
        self._ensure_data_file()

    def _ensure_data_file(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        if not os.path.exists(DATA_FILE):
            self._write_messages([])

    def _read_messages(self):
        with open(DATA_FILE, "r") as f:
            return json.load(f)

    def _write_messages(self, messages):
        with open(DATA_FILE, "w") as f:
            json.dump(messages, f, indent=2)

    def add_message(self, username, content, filename=None):
        """Add a new message. Returns the created message dict."""
        message = {
            "id": str(uuid.uuid4()),
            "username": username,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "filename": filename,
        }
        with self._lock:
            messages = self._read_messages()
            messages.append(message)
            self._write_messages(messages)
        return message

    def get_messages(self, limit=50):
        """Return the most recent messages, up to `limit`."""
        with self._lock:
            messages = self._read_messages()
        return messages[-limit:]
