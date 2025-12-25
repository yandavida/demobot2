from typing import Protocol, Optional
from .schemas import ScenarioResponse

class ScenarioCache(Protocol):
    def get(self, key: str) -> Optional[ScenarioResponse]: ...
    def set(self, key: str, value: ScenarioResponse) -> None: ...

class InMemoryScenarioCache:
    def __init__(self, max_size: int = 128):
        self._cache = {}
        self._order = []
        self._max_size = max_size

    def get(self, key: str) -> Optional[ScenarioResponse]:
        return self._cache.get(key)

    def set(self, key: str, value: ScenarioResponse) -> None:
        if key not in self._cache and len(self._cache) >= self._max_size:
            # Simple FIFO eviction
            oldest = self._order.pop(0)
            del self._cache[oldest]
        if key not in self._cache:
            self._order.append(key)
        self._cache[key] = value

DEFAULT_SCENARIO_CACHE = InMemoryScenarioCache(max_size=128)
