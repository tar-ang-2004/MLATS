"""
Redis Cache Configuration and Utilities
Provides caching for ML model results and application data
"""

import redis
import json
import pickle
import hashlib
import logging
from datetime import timedelta
from typing import Any, Optional, Union
from functools import wraps

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache wrapper with JSON and pickle serialization support"""
    
    def __init__(self, redis_url: str = 'redis://localhost:6379/0'):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            # Test connection
            self.redis_client.ping()
            self.connected = True
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Cache will be disabled.")
            self.redis_client = None
            self.connected = False
    
    def _make_key(self, key: str, prefix: str = "ats") -> str:
        """Generate cache key with prefix"""
        return f"{prefix}:{key}"
    
    def _serialize_value(self, value: Any, use_pickle: bool = False) -> bytes:
        """Serialize value for Redis storage"""
        if use_pickle:
            return pickle.dumps(value)
        else:
            return json.dumps(value, default=str).encode('utf-8')
    
    def _deserialize_value(self, data: bytes, use_pickle: bool = False) -> Any:
        """Deserialize value from Redis"""
        if use_pickle:
            return pickle.loads(data)
        else:
            return json.loads(data.decode('utf-8'))
    
    def get(self, key: str, use_pickle: bool = False, prefix: str = "ats") -> Optional[Any]:
        """Get value from cache"""
        if not self.connected:
            return None
        
        try:
            cache_key = self._make_key(key, prefix)
            data = self.redis_client.get(cache_key)
            if data is None:
                return None
            return self._deserialize_value(data, use_pickle)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600, use_pickle: bool = False, prefix: str = "ats") -> bool:
        """Set value in cache with TTL"""
        if not self.connected:
            return False
        
        try:
            cache_key = self._make_key(key, prefix)
            serialized_value = self._serialize_value(value, use_pickle)
            return self.redis_client.setex(cache_key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str, prefix: str = "ats") -> bool:
        """Delete key from cache"""
        if not self.connected:
            return False
        
        try:
            cache_key = self._make_key(key, prefix)
            return bool(self.redis_client.delete(cache_key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def flush_pattern(self, pattern: str, prefix: str = "ats") -> int:
        """Delete all keys matching pattern"""
        if not self.connected:
            return 0
        
        try:
            full_pattern = self._make_key(pattern, prefix)
            keys = self.redis_client.keys(full_pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache flush error for pattern {pattern}: {e}")
            return 0

# Global cache instance
cache = RedisCache()

def cache_result(ttl: int = 3600, key_func: Optional[callable] = None, use_pickle: bool = False):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
        key_func: Optional function to generate cache key
        use_pickle: Use pickle instead of JSON serialization
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation based on function name and args
                arg_str = str(args) + str(sorted(kwargs.items()))
                cache_key = f"{func.__name__}:{hashlib.md5(arg_str.encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key, use_pickle=use_pickle)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl, use_pickle=use_pickle)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            return result
        
        return wrapper
    return decorator

def get_file_hash(file_content: bytes) -> str:
    """Generate hash for file content to use as cache key"""
    return hashlib.sha256(file_content).hexdigest()

def get_job_description_hash(job_description: str) -> str:
    """Generate hash for job description to use as cache key"""
    return hashlib.md5(job_description.encode()).hexdigest()[:16]