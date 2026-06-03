import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    chapter: int
    checker: str
    content_hash: str
    timestamp: float
    ttl: float
    result: Dict[str, Any]

    def is_expired(self) -> bool:
        if self.ttl < 0:
            return False
        if self.ttl == 0:
            return True
        return (time.time() - self.timestamp) > self.ttl


class CheckerCache:
    """检测结果缓存"""

    def __init__(self, cache_dir: Optional[Path] = None, default_ttl: float = 7 * 24 * 3600):
        if cache_dir is None:
            self.cache_dir = Path("context/checker_cache")
        else:
            self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _content_hash(self, content: str) -> str:
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]

    def _get_cache_path(self, checker: str, chapter: int, content_hash: str) -> Path:
        checker_dir = self.cache_dir / checker
        checker_dir.mkdir(exist_ok=True)
        return checker_dir / f"ch{chapter:03d}_{content_hash}.json"

    def set(self, checker: str, chapter: int, content: str, result: Dict[str, Any], ttl_seconds: float = None):
        content_hash = self._content_hash(content)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        entry = CacheEntry(
            chapter=chapter, checker=checker, content_hash=content_hash,
            timestamp=time.time(), ttl=ttl, result=result
        )
        cache_path = self._get_cache_path(checker, chapter, content_hash)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(entry), f, ensure_ascii=False)

    def get(self, checker: str, chapter: int, content: str) -> Optional[Dict[str, Any]]:
        content_hash = self._content_hash(content)
        cache_path = self._get_cache_path(checker, chapter, content_hash)
        if not cache_path.exists():
            return None
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            entry = CacheEntry(**data)
            if entry.is_expired():
                cache_path.unlink()
                return None
            return entry.result
        except (json.JSONDecodeError, KeyError):
            return None

    def clear(self, checker: str = None, chapter: int = None):
        if checker is None:
            for f in self.cache_dir.rglob("*.json"):
                f.unlink()
        elif chapter is None:
            checker_dir = self.cache_dir / checker
            if checker_dir.exists():
                for f in checker_dir.glob("*.json"):
                    f.unlink()
        else:
            checker_dir = self.cache_dir / checker
            if checker_dir.exists():
                for f in checker_dir.glob(f"ch{chapter:03d}_*.json"):
                    f.unlink()
