"""
Step 63: In-Memory Caching Layer
TTL-based cache with LRU eviction. Drop-in replacement for Redis in dev/hackathon mode.
"""
import time, logging, hashlib, json
from typing import Any, Optional
from collections import OrderedDict

logger = logging.getLogger("ahos.cache")

class CacheEntry:
    __slots__ = ("value", "expires_at", "hits")
    def __init__(self, value: Any, ttl: float):
        self.value = value
        self.expires_at = time.time() + ttl
        self.hits = 0
    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

class CacheLayer:
    """In-memory TTL cache with LRU eviction, namespacing, and stats."""
    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "sets": 0}

    def _make_key(self, namespace: str, key: str) -> str:
        return f"{namespace}:{key}"

    def get(self, namespace: str, key: str) -> Optional[Any]:
        full_key = self._make_key(namespace, key)
        entry = self._store.get(full_key)
        if entry is None:
            self._stats["misses"] += 1
            return None
        if entry.is_expired:
            del self._store[full_key]
            self._stats["misses"] += 1
            return None
        entry.hits += 1
        self._stats["hits"] += 1
        self._store.move_to_end(full_key)
        return entry.value

    def set(self, namespace: str, key: str, value: Any, ttl: Optional[float] = None):
        full_key = self._make_key(namespace, key)
        if full_key in self._store:
            del self._store[full_key]
        while len(self._store) >= self.max_size:
            evicted_key, _ = self._store.popitem(last=False)
            self._stats["evictions"] += 1
            logger.debug(f"Cache evicted: {evicted_key}")
        self._store[full_key] = CacheEntry(value, ttl or self.default_ttl)
        self._stats["sets"] += 1

    def invalidate(self, namespace: str, key: str) -> bool:
        full_key = self._make_key(namespace, key)
        if full_key in self._store:
            del self._store[full_key]
            return True
        return False

    def invalidate_namespace(self, namespace: str) -> int:
        keys = [k for k in self._store if k.startswith(f"{namespace}:")]
        for k in keys:
            del self._store[k]
        return len(keys)

    def clear(self):
        self._store.clear()

    def get_stats(self) -> dict:
        total = self._stats["hits"] + self._stats["misses"]
        return {
            **self._stats,
            "size": len(self._store),
            "max_size": self.max_size,
            "hit_rate": round(self._stats["hits"] / total * 100, 1) if total > 0 else 0.0,
        }

    def cache_key_from_dict(self, data: dict) -> str:
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

cache = CacheLayer()
