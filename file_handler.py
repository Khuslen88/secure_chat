import os

from werkzeug.utils import secure_filename

from config import Config
from security import SecurityUtils


UPLOAD_DIR = Config.UPLOAD_DIR


class FileHandler:
    """Handles secure file uploads and downloads."""

    def __init__(self):
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    def save_file(self, file_storage):
        """Validate and save an uploaded file.

        Args:
            file_storage: A Werkzeug FileStorage object from the request.

        Returns:
            (success, filename_or_error) — on success the saved filename,
            on failure an error message string.
        """
        filename = secure_filename(file_storage.filename or "")
        if not filename:
            return False, "Invalid filename."

        # Read content to measure size
        file_storage.stream.seek(0, os.SEEK_END)
        file_size = file_storage.stream.tell()
        file_storage.stream.seek(0)

        valid, err = SecurityUtils.validate_file(filename, file_size, file_storage.stream)
        if not valid:
            return False, err

        # Deduplicate: if file already exists, prepend a counter
        save_name = filename
        dest = os.path.join(UPLOAD_DIR, save_name)
        counter = 1
        while os.path.exists(dest):
            name, ext = os.path.splitext(filename)
            save_name = f"{name}_{counter}{ext}"
            dest = os.path.join(UPLOAD_DIR, save_name)
            counter += 1

        file_storage.save(dest)
        return True, save_name

    def get_file_path(self, filename):
        """Return the absolute path for a file if it exists, else None.

        Uses secure_filename to prevent path traversal.
        """
        safe_name = secure_filename(filename)
        if not safe_name:
            return None
        path = os.path.join(UPLOAD_DIR, safe_name)
        if os.path.isfile(path):
            return path
        return None
