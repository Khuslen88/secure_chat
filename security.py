import os

import bleach


class SecurityUtils:
    """Input sanitization and security utilities."""

    # Allowed HTML tags (empty = strip all tags)
    ALLOWED_TAGS = []

    @staticmethod
    def sanitize_message(content):
        """Strip all HTML/script tags from message content.

        Uses bleach to remove dangerous markup. Returns cleaned plain text.
        """
        return bleach.clean(content, tags=SecurityUtils.ALLOWED_TAGS, strip=True).strip()

    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".docx", ".gif", ".csv", ".xlsx"}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

    # Magic byte signatures for content-type verification
    MAGIC_BYTES = {
        ".png": b"\x89PNG",
        ".jpg": b"\xff\xd8\xff",
        ".jpeg": b"\xff\xd8\xff",
        ".gif": b"GIF8",
        ".pdf": b"%PDF",
        ".xlsx": b"PK",  # XLSX files are ZIP archives
        ".docx": b"PK",  # DOCX files are also ZIP archives
    }

    @staticmethod
    def validate_file(filename, file_size, file_stream):
        """Validate an uploaded file for security.

        Checks extension whitelist, file size cap, and magic bytes
        to confirm file content matches its claimed type.

        Args:
            filename: The original filename from the upload.
            file_size: Size in bytes of the uploaded file.
            file_stream: The file stream (supports .read() and .seek()).

        Returns:
            (is_valid, error_message) tuple.
        """
        if not filename:
            return False, "No filename provided."

        ext = os.path.splitext(filename)[1].lower()

        if ext not in SecurityUtils.ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(SecurityUtils.ALLOWED_EXTENSIONS))
            return False, f"File type '{ext}' is not allowed. Accepted types: {allowed}"

        if file_size > SecurityUtils.MAX_FILE_SIZE:
            max_mb = SecurityUtils.MAX_FILE_SIZE // (1024 * 1024)
            return False, f"File too large ({file_size // 1024}KB). Maximum size is {max_mb}MB."

        if file_size == 0:
            return False, "File is empty."

        # Magic bytes check — verify content matches extension
        expected_magic = SecurityUtils.MAGIC_BYTES.get(ext)
        if expected_magic:
            header = file_stream.read(len(expected_magic))
            file_stream.seek(0)
            if header != expected_magic:
                return False, f"File content does not match its '{ext}' extension. Possible disguised file."

        return True, None
