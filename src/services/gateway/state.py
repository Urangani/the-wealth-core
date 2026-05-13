from __future__ import annotations

from typing import Any

_cache: dict[str, Any] = {}


def has_changed(key: str, value: Any) -> bool:
    prev = _cache.get(key)
    if prev != value:
        _cache[key] = value
        return True
    return False


def set(key: str, value: Any) -> None:
    _cache[key] = value


def get(key: str) -> Any:
    return _cache.get(key)
