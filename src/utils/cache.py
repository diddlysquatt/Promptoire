"""
Caching system for Promptoire to improve performance.
Provides LRU cache with TTL support and automatic cleanup.
"""

import time
import threading
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict
import json
import os
import hashlib


class CacheEntry:
    """Represents a single cache entry with TTL"""

    def __init__(self, value: Any, ttl: Optional[int] = None):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def access(self) -> Any:
        """Access the cached value and update statistics"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value

    def to_dict(self) -> Dict:
        """Convert cache entry to dictionary for serialization"""
        return {
            'value': self.value,
            'created_at': self.created_at,
            'ttl': self.ttl,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        """Create cache entry from dictionary"""
        entry = cls(data['value'], data['ttl'])
        entry.created_at = data['created_at']
        entry.access_count = data['access_count']
        entry.last_accessed = data['last_accessed']
        return entry


class LRUCache:
    """Thread-safe LRU cache with TTL support"""

    def __init__(self, max_size: int = 1000, cleanup_interval: int = 300):
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired_cleanups': 0
        }
        self._last_cleanup = time.time()

    def _cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items"""
        current_time = time.time()

        # Only cleanup if enough time has passed
        if current_time - self._last_cleanup < self.cleanup_interval:
            return 0

        expired_keys = []
        for key, entry in self._cache.items():
            if entry.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]
            self._stats['expired_cleanups'] += 1

        self._last_cleanup = current_time
        return len(expired_keys)

    def _ensure_capacity(self) -> None:
        """Ensure cache doesn't exceed max_size by removing oldest entries"""
        while len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats['evictions'] += 1

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            # Cleanup expired entries periodically
            self._cleanup_expired()

            if key not in self._cache:
                self._stats['misses'] += 1
                return None

            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                self._stats['misses'] += 1
                self._stats['expired_cleanups'] += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._stats['hits'] += 1
            return entry.access()

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        with self._lock:
            # Cleanup expired entries periodically
            self._cleanup_expired()

            # Ensure capacity
            if key not in self._cache:
                self._ensure_capacity()

            # Add or update entry
            self._cache[key] = CacheEntry(value, ttl)
            self._cache.move_to_end(key)

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'expired_cleanups': 0
            }

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0

            return {
                **self._stats,
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': hit_rate,
                'utilization': len(self._cache) / self.max_size
            }

    def get_keys(self) -> list:
        """Get all cache keys"""
        with self._lock:
            return list(self._cache.keys())

    def get_entry_info(self, key: str) -> Optional[Dict]:
        """Get detailed information about a cache entry"""
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            return {
                'key': key,
                'created_at': entry.created_at,
                'ttl': entry.ttl,
                'access_count': entry.access_count,
                'last_accessed': entry.last_accessed,
                'is_expired': entry.is_expired(),
                'age_seconds': time.time() - entry.created_at
            }


class PersistentCache:
    """Cache that can persist to disk for faster startup times"""

    def __init__(self, cache_dir: str = "cache", max_memory_size: int = 500):
        self.cache_dir = cache_dir
        self.max_memory_size = max_memory_size

        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)

        # Memory cache for frequently accessed items
        self.memory_cache = LRUCache(max_memory_size)

        # Persistent cache files
        self.cache_file = os.path.join(cache_dir, "persistent_cache.json")
        self.cache_index_file = os.path.join(cache_dir, "cache_index.json")

        # Load existing cache from disk
        self._load_persistent_cache()

    def _get_cache_filename(self, key: str) -> str:
        """Generate safe filename for cache key"""
        # Use SHA256 hash to create safe filename
        hash_obj = hashlib.sha256(key.encode('utf-8'))
        return hash_obj.hexdigest() + ".cache"

    def _load_persistent_cache(self) -> None:
        """Load cache index from disk"""
        try:
            if os.path.exists(self.cache_index_file):
                with open(self.cache_index_file, 'r', encoding='utf-8') as f:
                    self.cache_index = json.load(f)
            else:
                self.cache_index = {}
        except Exception:
            self.cache_index = {}

    def _save_persistent_cache(self) -> None:
        """Save cache index to disk"""
        try:
            with open(self.cache_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f)
        except Exception:
            pass  # Fail silently for cache operations

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (memory first, then disk)"""
        # Try memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            return value

        # Try persistent cache
        if key in self.cache_index:
            cache_info = self.cache_index[key]
            cache_file = os.path.join(self.cache_dir, self._get_cache_filename(key))

            try:
                # Check if file exists and hasn't expired
                if os.path.exists(cache_file):
                    if cache_info.get('ttl') is None or \
                       (time.time() - cache_info['created_at']) <= cache_info['ttl']:

                        with open(cache_file, 'rb') as f:
                            value = f.read()

                        # Put back into memory cache
                        self.memory_cache.set(key, value, cache_info.get('ttl'))
                        return value
                    else:
                        # Expired, remove from index and delete file
                        del self.cache_index[key]
                        try:
                            os.remove(cache_file)
                        except OSError:
                            pass
                        self._save_persistent_cache()
            except Exception:
                # Remove corrupted entry
                if key in self.cache_index:
                    del self.cache_index[key]
                    self._save_persistent_cache()

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None, persist: bool = True) -> None:
        """Set value in cache"""
        # Always store in memory cache
        self.memory_cache.set(key, value, ttl)

        # Persist to disk if requested and value is serializable
        if persist:
            try:
                cache_file = os.path.join(self.cache_dir, self._get_cache_filename(key))

                # Only persist if value is JSON serializable or bytes
                if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(value, f)
                elif isinstance(value, bytes):
                    with open(cache_file, 'wb') as f:
                        f.write(value)
                else:
                    # Not serializable, skip persistence
                    return

                # Update index
                self.cache_index[key] = {
                    'created_at': time.time(),
                    'ttl': ttl,
                    'filename': self._get_cache_filename(key)
                }
                self._save_persistent_cache()

            except Exception:
                # Fail silently for cache operations
                pass

    def delete(self, key: str) -> bool:
        """Delete key from both memory and persistent cache"""
        # Delete from memory cache
        memory_deleted = self.memory_cache.delete(key)

        # Delete from persistent cache
        persistent_deleted = False
        if key in self.cache_index:
            cache_file = os.path.join(self.cache_dir, self.cache_index[key]['filename'])
            try:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                del self.cache_index[key]
                self._save_persistent_cache()
                persistent_deleted = True
            except Exception:
                pass

        return memory_deleted or persistent_deleted

    def clear(self) -> None:
        """Clear all cache entries"""
        # Clear memory cache
        self.memory_cache.clear()

        # Clear persistent cache
        try:
            # Delete all cache files
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache') or filename.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass

            # Clear index
            self.cache_index = {}
            self._save_persistent_cache()
        except Exception:
            pass

    def cleanup_expired(self) -> int:
        """Clean up expired entries from persistent cache"""
        current_time = time.time()
        expired_keys = []

        for key, cache_info in list(self.cache_index.items()):
            if cache_info.get('ttl') is not None:
                if current_time - cache_info['created_at'] > cache_info['ttl']:
                    expired_keys.append(key)

        for key in expired_keys:
            self.delete(key)

        return len(expired_keys)

    def get_stats(self) -> Dict:
        """Get comprehensive cache statistics"""
        memory_stats = self.memory_cache.get_stats()

        # Calculate persistent cache stats
        persistent_size = len(self.cache_index)
        total_cache_files = 0
        cache_dir_size = 0

        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    total_cache_files += 1
                    cache_dir_size += os.path.getsize(file_path)
        except Exception:
            pass

        return {
            'memory_cache': memory_stats,
            'persistent_cache': {
                'entries': persistent_size,
                'total_files': total_cache_files,
                'disk_size_bytes': cache_dir_size,
                'disk_size_mb': cache_dir_size / (1024 * 1024)
            }
        }


# Global cache instance for the application
_cache_instance = None


def get_cache(cache_type: str = "memory", **kwargs) -> Any:
    """Get cache instance"""
    global _cache_instance

    if _cache_instance is None:
        if cache_type == "persistent":
            _cache_instance = PersistentCache(**kwargs)
        else:
            _cache_instance = LRUCache(**kwargs)

    return _cache_instance


def clear_global_cache() -> None:
    """Clear the global cache instance"""
    global _cache_instance
    if _cache_instance:
        _cache_instance.clear()
    _cache_instance = None