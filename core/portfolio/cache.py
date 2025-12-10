from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Generic, Optional, Tuple, TypeVar

from core.portfolio.hashing import stable_hash

KeyT = TypeVar("KeyT")
ValueT = TypeVar("ValueT")


@dataclass(frozen=True)
class CacheKey:
    namespace: str
    parameters: Tuple[object, ...] = field(default_factory=tuple)

    def __hash__(self) -> int:  # pragma: no cover - deterministic through stable_hash
        return hash((self.namespace, stable_hash(self.parameters)))


class InMemoryCache(Generic[KeyT, ValueT]):
    def __init__(self) -> None:
        self._store: Dict[KeyT, ValueT] = {}

    def get(self, key: KeyT) -> Optional[ValueT]:
        return self._store.get(key)

    def set(self, key: KeyT, value: ValueT) -> None:
        self._store[key] = value

    def __contains__(self, key: KeyT) -> bool:
        return key in self._store

    def clear(self) -> None:
        self._store.clear()
