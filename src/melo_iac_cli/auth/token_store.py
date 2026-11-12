import os
import tempfile
from pathlib import Path


class TokenStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def save(self, token: str) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # mkstemp creates the file as 0o600 regardless of umask, so the token
        # is never readable by others; os.replace swaps it in atomically.
        fd, tmp = tempfile.mkstemp(
            dir=self._path.parent, prefix=f".{self._path.name}."
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(token)
            os.replace(tmp, self._path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

    def load(self) -> str | None:
        try:
            return self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None

    def clear(self) -> None:
        self._path.unlink(missing_ok=True)
