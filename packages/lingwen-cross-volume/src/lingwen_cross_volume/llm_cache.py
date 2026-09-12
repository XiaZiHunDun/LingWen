import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path


class LLMCache:
    """Phase 9.12: in-memory + JSON disk cache (Q5).

    - key = SHA256(chapter_content + prompt_id + model_id)
    - in-memory dict (L1) + JSON file (L2 persistent)
    - hit returns dict, miss returns None
    - corrupted JSON auto-deletes + rebuilds
    - atomic write via tempfile + rename (avoids half-written corruption)
    """

    DEFAULT_PATH = Path.home() / ".cache" / "lingwen" / "llm_cache.json"

    def __init__(self, cache_path: Path | None = None) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self._mem: dict[str, dict] = {}
        self._path = cache_path or self.DEFAULT_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    @staticmethod
    def make_key(chapter_content: str, prompt_id: str, model_id: str) -> str:
        h = hashlib.sha256()
        h.update(chapter_content.encode("utf-8"))
        h.update(b"\x00")
        h.update(prompt_id.encode("utf-8"))
        h.update(b"\x00")
        h.update(model_id.encode("utf-8"))
        return h.hexdigest()

    def get(self, key: str) -> dict | None:
        return self._mem.get(key)

    def put(self, key: str, value: dict) -> None:
        self._mem[key] = value
        self._save()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            self._mem = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            self.logger.warning("Cache %s corrupted, rebuilding: %s", self._path, e)
            self._path.unlink(missing_ok=True)
            self._mem = {}

    def _save(self) -> None:
        # atomic write: tempfile + rename
        fd, tmp = tempfile.mkstemp(dir=self._path.parent, prefix=".cache_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._mem, f, ensure_ascii=False)
            os.replace(tmp, self._path)
        except Exception:
            Path(tmp).unlink(missing_ok=True)
            raise
