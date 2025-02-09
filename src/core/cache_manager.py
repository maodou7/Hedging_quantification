import os
import json
import redis
import logging
from typing import Any, Optional
from src.config.cache import CACHE_CONFIG, CacheStrategy

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        logger.info("[缓存] 初始化缓存管理器...")
        self.strategy = CACHE_CONFIG["strategy"]
        logger.info(f"[缓存] 使用缓存策略: {self.strategy}")
        
        if self.strategy == CacheStrategy.REDIS:
            try:
                self.redis_client = redis.Redis(
                    host=CACHE_CONFIG["redis"]["host"],
                    port=CACHE_CONFIG["redis"]["port"],
                    password=CACHE_CONFIG["redis"]["password"],
                    db=CACHE_CONFIG["redis"]["db"]
                )
                # 测试连接
                self.redis_client.ping()
                logger.info("[缓存] Redis连接成功")
            except Exception as e:
                logger.error(f"[缓存] Redis连接失败: {str(e)}")
                raise
                
        elif self.strategy == CacheStrategy.LOCAL:
            try:
                cache_dir = CACHE_CONFIG["local"]["output_dir"]
                os.makedirs(cache_dir, exist_ok=True)
                logger.info(f"[缓存] 本地缓存目录: {cache_dir}")
            except Exception as e:
                logger.error(f"[缓存] 创建本地缓存目录失败: {str(e)}")
                raise

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
            logger.debug("[缓存] 未启用缓存，跳过设置")
            return

        try:
            if self.strategy == CacheStrategy.REDIS:
                redis_key = self._get_redis_key(key)
                data_str = json.dumps(value, ensure_ascii=False)
                if expire:
                    self.redis_client.setex(redis_key, expire, data_str)
                    logger.debug(f"[缓存] 设置Redis键值对: {redis_key}, 过期时间: {expire}秒")
                else:
                    self.redis_client.set(redis_key, data_str)
                    logger.debug(f"[缓存] 设置Redis键值对: {redis_key}")
            
            elif self.strategy == CacheStrategy.LOCAL:
                local_path = self._get_local_path(key)
                with open(local_path, 'w', encoding='utf-8') as f:
                    json.dump(value, f, 
                             indent=CACHE_CONFIG["local"]["indent"],
                             ensure_ascii=CACHE_CONFIG["local"]["ensure_ascii"])
                logger.debug(f"[缓存] 写入本地文件: {local_path}")
                
        except Exception as e:
            logger.error(f"[缓存] 设置缓存失败: {str(e)}")
            raise

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 键名
            
        Returns:
            缓存的值，如果不存在则返回None
        """
        if self.strategy == CacheStrategy.NO_CACHE:
            logger.debug("[缓存] 未启用缓存，返回None")
            return None

        try:
            if self.strategy == CacheStrategy.REDIS:
                redis_key = self._get_redis_key(key)
                value = self.redis_client.get(redis_key)
                if value:
                    logger.debug(f"[缓存] 获取Redis键值对: {redis_key}")
                    return json.loads(value)
                logger.debug(f"[缓存] Redis键不存在: {redis_key}")
            
            elif self.strategy == CacheStrategy.LOCAL:
                local_path = self._get_local_path(key)
                if os.path.exists(local_path):
                    with open(local_path, 'r', encoding='utf-8') as f:
                        logger.debug(f"[缓存] 读取本地文件: {local_path}")
                        return json.load(f)
                logger.debug(f"[缓存] 本地文件不存在: {local_path}")
                
        except Exception as e:
            logger.error(f"[缓存] 获取缓存失败: {str(e)}")
            
        return None

    def delete(self, key: str) -> None:
        """
        删除缓存
        
        Args:
            key: 键名
        """
        if self.strategy == CacheStrategy.NO_CACHE:
            logger.debug("[缓存] 未启用缓存，跳过删除")
            return

        try:
            if self.strategy == CacheStrategy.REDIS:
                redis_key = self._get_redis_key(key)
                self.redis_client.delete(redis_key)
                logger.debug(f"[缓存] 删除Redis键: {redis_key}")
            
            elif self.strategy == CacheStrategy.LOCAL:
                local_path = self._get_local_path(key)
                if os.path.exists(local_path):
                    os.remove(local_path)
                    logger.debug(f"[缓存] 删除本地文件: {local_path}")
                else:
                    logger.debug(f"[缓存] 本地文件不存在，无需删除: {local_path}")
                    
        except Exception as e:
            logger.error(f"[缓存] 删除缓存失败: {str(e)}")
            raise 