import os


class Config:
    """Application configuration, loaded from environment variables."""

    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "4096"))
    MAX_CONVERSATION_HISTORY = int(os.environ.get("MAX_CONVERSATION_HISTORY", "50"))

    # Paths
    BASE_DIR = os.path.dirname(__file__)
    DATA_DIR = os.path.join(BASE_DIR, "data")
    UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
    KNOWLEDGE_BASE_DIR = os.path.join(DATA_DIR, "knowledge_base")
    EXTRACTED_TEXT_DIR = os.path.join(DATA_DIR, "knowledge_base", "extracted")
    CONVERSATIONS_DIR = os.path.join(DATA_DIR, "conversations")

    # File constraints
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

    # Company info
    COMPANY_NAME = os.environ.get("COMPANY_NAME", "Our Company")
