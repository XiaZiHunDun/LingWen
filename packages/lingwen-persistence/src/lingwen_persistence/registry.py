import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type


@dataclass
class RegisteredStorage:
    name: str
    cls: Type
    db_path: Path
    kwargs: Dict[str, Any]
    instance: Optional[Any] = None


_registry: Dict[str, RegisteredStorage] = {}
_lock = threading.Lock()


def register(name: str, cls: Type, db_path: Path, **kwargs) -> None:
    with _lock:
        _registry[name] = RegisteredStorage(
            name=name,
            cls=cls,
            db_path=db_path,
            kwargs=kwargs,
            instance=None,
        )


def get(name: str, db_path: Optional[str | Path] = None) -> Any:
    with _lock:
        entry = _registry.get(name)
        if not entry:
            raise KeyError(f"No storage registered with name: {name}")

        effective_path = db_path if db_path is not None else entry.db_path

        if entry.instance is None or (db_path is not None and str(db_path) != str(entry.db_path)):
            if isinstance(effective_path, str):
                effective_path = Path(effective_path)
            if (
                str(effective_path) != ":memory:"
                and effective_path.parent
                and not effective_path.parent.exists()
            ):
                effective_path.parent.mkdir(parents=True, exist_ok=True)
            entry.instance = entry.cls(db_path=effective_path, **entry.kwargs)

        return entry.instance


def reset(name: str) -> None:
    with _lock:
        entry = _registry.get(name)
        if entry:
            entry.instance = None


def reset_all() -> None:
    with _lock:
        for entry in _registry.values():
            entry.instance = None


def is_registered(name: str) -> bool:
    return name in _registry


def list_registered() -> list[str]:
    return list(_registry.keys())


def get_registration(name: str) -> Optional[RegisteredStorage]:
    return _registry.get(name)


def registered_names() -> list[str]:
    return sorted(list(_registry.keys()))
