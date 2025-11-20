"""Redis Cache Client for Face Recognition System.

Provides caching for:
- Face embeddings
- User metadata
- Search results
- Frequent queries

Target: Reduce latency from 500ms to <50ms
"""

import logging
import json
import pickle
from typing import Any, Dict, List, Optional
from datetime import timedelta

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("⚠️ redis package not installed. Install with: pip install redis")


class RedisClient:
    """Redis cache client for face recognition system."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        enabled: bool = True,
        default_ttl: int = 3600,  # 1 hour
    ):
        """Initialize Redis client.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (optional)
            enabled: Enable Redis (False for local-only mode)
            default_ttl: Default TTL in seconds
        """
        self.enabled = enabled and REDIS_AVAILABLE
        self.default_ttl = default_ttl
        self.client = None
        self.host = host
        self.port = port

        if self.enabled:
            try:
                self.client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    decode_responses=False,  # Handle binary data
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                # Test connection
                self.client.ping()
                logger.info(f"✅ Redis client initialized: {host}:{port}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to connect to Redis: {e}")
                self.enabled = False
                self.client = None

    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create namespaced cache key."""
        return f"facerecog:{prefix}:{identifier}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.enabled:
            return None

        try:
            value = self.client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.warning(f"⚠️ Redis GET error for key {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = default_ttl)

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            ttl = ttl or self.default_ttl
            serialized = pickle.dumps(value)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis SET error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.enabled:
            return False

        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis DELETE error for key {key}: {e}")
            return False

    def get_embedding(self, user_id: str) -> Optional[Dict]:
        """Get cached embedding for user.

        Args:
            user_id: User ID

        Returns:
            Cached embedding data or None
        """
        key = self._make_key("embedding", user_id)
        return self.get(key)

    def set_embedding(
        self,
        user_id: str,
        embedding_data: Dict,
        ttl: int = 3600,
    ) -> bool:
        """Cache embedding for user.

        Args:
            user_id: User ID
            embedding_data: Embedding data to cache
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        key = self._make_key("embedding", user_id)
        return self.set(key, embedding_data, ttl)

    def get_user_metadata(self, user_id: str) -> Optional[Dict]:
        """Get cached user metadata.

        Args:
            user_id: User ID

        Returns:
            Cached user data or None
        """
        key = self._make_key("user", user_id)
        return self.get(key)

    def set_user_metadata(
        self,
        user_id: str,
        user_data: Dict,
        ttl: int = 1800,
    ) -> bool:
        """Cache user metadata.

        Args:
            user_id: User ID
            user_data: User data to cache
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        key = self._make_key("user", user_id)
        return self.set(key, user_data, ttl)

    def get_search_result(self, image_hash: str) -> Optional[Dict]:
        """Get cached search result.

        Args:
            image_hash: Hash of the search image

        Returns:
            Cached search result or None
        """
        key = self._make_key("search", image_hash)
        return self.get(key)

    def set_search_result(
        self,
        image_hash: str,
        result: Dict,
        ttl: int = 300,  # 5 minutes
    ) -> bool:
        """Cache search result.

        Args:
            image_hash: Hash of the search image
            result: Search result to cache
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        key = self._make_key("search", image_hash)
        return self.set(key, result, ttl)

    def invalidate_user(self, user_id: str) -> bool:
        """Invalidate all cache entries for a user.

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            keys = [
                self._make_key("embedding", user_id),
                self._make_key("user", user_id),
            ]
            self.client.delete(*keys)
            logger.info(f"✅ Invalidated cache for user {user_id}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis invalidation error for user {user_id}: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern.

        Args:
            pattern: Pattern to match (e.g., "facerecog:search:*")

        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                count = self.client.delete(*keys)
                logger.info(f"✅ Cleared {count} keys matching pattern: {pattern}")
                return count
            return 0
        except Exception as e:
            logger.warning(f"⚠️ Redis clear pattern error: {e}")
            return 0

    def health_check(self) -> Dict[str, Any]:
        """Check Redis health.

        Returns:
            Health status dict
        """
        result = {
            "enabled": self.enabled,
            "connected": False,
            "host": self.host,
            "port": self.port,
        }

        if self.enabled and self.client:
            try:
                self.client.ping()
                info = self.client.info()
                result["connected"] = True
                result["version"] = info.get("redis_version", "unknown")
                result["used_memory"] = info.get("used_memory_human", "unknown")
                result["connected_clients"] = info.get("connected_clients", 0)
            except Exception as e:
                result["error"] = str(e)
                logger.warning(f"⚠️ Redis health check failed: {e}")

        return result

    def close(self):
        """Close Redis connection."""
        if self.client:
            try:
                self.client.close()
                logger.info("✅ Redis connection closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing Redis connection: {e}")
