import os
import json
import redis
from typing import Any, Optional
from src.Environment.cache_config import CACHE_CONFIG, CacheStrategy

class CacheManager:
    def __init__(self):
        self.strategy = CACHE_CONFIG["strategy"]
        if self.strategy == CacheStrategy.REDIS:
            self.redis_client = redis.Redis(
                host=CACHE_CONFIG["redis"]["host"],
                port=CACHE_CONFIG["redis"]["port"],
                password=CACHE_CONFIG["redis"]["password"],
                db=CACHE_CONFIG["redis"]["db"]
            )
        elif self.strategy == CacheStrategy.LOCAL:
            os.makedirs(CACHE_CONFIG["local"]["output_dir"], exist_ok=True)

    def _get_redis_key(self, key: str) -> str:
        return f"{CACHE_CONFIG['redis']['key_prefix']}{key}"

    def _get_local_path(self, key: str) -> str:
        filename = f"{key}{CACHE_CONFIG['local']['file_extension']}"
        return os.path.join(CACHE_CONFIG["local"]["output_dir"], filename)

    def set(self, key: str, value: Any, expire: int = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 键名
            value: 值
            expire: 过期时间（秒），仅在Redis模式下有效
        """
        if self.strategy == CacheStrategy.NO_CACHE:
            return

        if self.strategy == CacheStrategy.REDIS:
            redis_key = self._get_redis_key(key)
            data_str = json.dumps(value, ensure_ascii=False)
            if expire:
                self.redis_client.setex(redis_key, expire, data_str)
            else:
                self.redis_client.set(redis_key, data_str)
        
        elif self.strategy == CacheStrategy.LOCAL:
            local_path = self._get_local_path(key)
            with open(local_path, 'w', encoding='utf-8') as f:
                json.dump(value, f, 
                         indent=CACHE_CONFIG["local"]["indent"],
                         ensure_ascii=CACHE_CONFIG["local"]["ensure_ascii"])

    def get(self, key: str) -> Optional[Any]:
        if self.strategy == CacheStrategy.NO_CACHE:
            return None

        if self.strategy == CacheStrategy.REDIS:
            redis_key = self._get_redis_key(key)
            value = self.redis_client.get(redis_key)
            if value:
                return json.loads(value)
        
        elif self.strategy == CacheStrategy.LOCAL:
            local_path = self._get_local_path(key)
            if os.path.exists(local_path):
                with open(local_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        return None

    def delete(self, key: str) -> None:
        if self.strategy == CacheStrategy.NO_CACHE:
            return

        if self.strategy == CacheStrategy.REDIS:
            redis_key = self._get_redis_key(key)
            self.redis_client.delete(redis_key)
        
        elif self.strategy == CacheStrategy.LOCAL:
            local_path = self._get_local_path(key)
            if os.path.exists(local_path):
                os.remove(local_path) 