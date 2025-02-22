"""
Redis 管理器

负责管理 Redis 连接和操作
"""

import logging
from typing import Any, Dict, List, Optional
import redis.asyncio as redis
from src.config.cache import CACHE_CONFIG

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis 管理器类"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
        
    def __init__(self):
        if not self.initialized:
            self.redis_client = None
            self.initialized = True
            
    async def initialize(self) -> bool:
        """
        初始化 Redis 连接
        
        Returns:
            bool: 是否初始化成功
        """
        try:
            if CACHE_CONFIG['use_redis']:
                self.redis_client = redis.Redis(
                    host=CACHE_CONFIG['redis_host'],
                    port=CACHE_CONFIG['redis_port'],
                    db=CACHE_CONFIG['redis_db'],
                    password=CACHE_CONFIG['redis_password'],
                    socket_timeout=CACHE_CONFIG['redis_timeout'],
                    decode_responses=True
                )
                # 测试连接
                await self.redis_client.ping()
                logger.info("Redis 连接成功")
                return True
        except redis.TimeoutError:
            logger.error(f"Redis连接超时: Timeout connecting to {CACHE_CONFIG['redis_host']}:{CACHE_CONFIG['redis_port']}")
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
        return False
        
    def get_redis_url(self) -> str:
        """
        获取 Redis URL
        
        Returns:
            str: Redis URL
        """
        password = f":{CACHE_CONFIG['redis_password']}@" if CACHE_CONFIG['redis_password'] else ""
        return f"redis://{password}{CACHE_CONFIG['redis_host']}:{CACHE_CONFIG['redis_port']}/{CACHE_CONFIG['redis_db']}"
        
    async def close(self):
        """关闭 Redis 连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置键值对
        
        Args:
            key: 键名
            value: 值
            expire: 过期时间(秒)
            
        Returns:
            bool: 是否设置成功
        """
        if not self.redis_client:
            logger.error("Redis连接未初始化")
            return False
            
        try:
            # 序列化值
            if not isinstance(value, (str, int, float, bool)):
                value = json.dumps(value)
                
            # 设置键值对
            if expire:
                await self.redis_client.setex(key, expire, value)
            else:
                await self.redis_client.set(key, value)
                
            return True
        except Exception as e:
            logger.error(f"设置键值对失败: {str(e)}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取键值
        
        Args:
            key: 键名
            
        Returns:
            Optional[Any]: 值,不存在返回None
        """
        if not self.redis_client:
            logger.error("Redis连接未初始化")
            return None
            
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None
                
            # 尝试反序列化
            try:
                return json.loads(value)
            except:
                return value
        except Exception as e:
            logger.error(f"获取键值失败: {str(e)}")
            return None
    
    async def delete(self, key: str) -> bool:
        """
        删除键
        
        Args:
            key: 键名
            
        Returns:
            bool: 是否删除成功
        """
        if not self.redis_client:
            logger.error("Redis连接未初始化")
            return False
            
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"删除键失败: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 键名
            
        Returns:
            bool: 是否存在
        """
        if not self.redis_client:
            logger.error("Redis连接未初始化")
            return False
            
        try:
            return await self.redis_client.exists(key)
        except Exception as e:
            logger.error(f"检查键是否存在失败: {str(e)}")
            return False
    
    async def publish(self, channel: str, message: Any) -> bool:
        """
        发布消息
        
        Args:
            channel: 频道名
            message: 消息内容
            
        Returns:
            bool: 是否发布成功
        """
        if not self.redis_client:
            logger.error("Redis连接未初始化")
            return False
            
        try:
            # 序列化消息
            if not isinstance(message, (str, int, float, bool)):
                message = json.dumps(message)
                
            # 发布消息
            await self.redis_client.publish(channel, message)
            return True
        except Exception as e:
            logger.error(f"发布消息失败: {str(e)}")
            return False
    
    async def subscribe(self, channel: str, callback):
        """
        订阅频道
        
        Args:
            channel: 频道名
            callback: 回调函数
        """
        if not self.redis_client:
            logger.error("Redis连接未初始化")
            return
            
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel)
            
            while True:
                message = await pubsub.get_message()
                if message and message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                    except:
                        data = message['data']
                    await callback(data)
        except Exception as e:
            logger.error(f"订阅频道失败: {str(e)}")
    
    async def unsubscribe(self, channel: str):
        """
        取消订阅
        
        Args:
            channel: 频道名
        """
        if not self.redis_client:
            logger.error("Redis连接未初始化")
            return False
            
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.unsubscribe(channel)
            return True
        except Exception as e:
            logger.error(f"取消订阅失败: {str(e)}")
            return False
    
    async def get_keys(self, pattern: str = "*") -> List[str]:
        """
        获取匹配模式的所有键
        
        Args:
            pattern: 匹配模式
            
        Returns:
            List[str]: 键列表
        """
        if not self.redis_client:
            logger.error("Redis连接未初始化")
            return []
            
        try:
            return await self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"获取键列表失败: {str(e)}")
            return []
    
    async def clear_all(self) -> bool:
        """
        清空所有数据
        
        Returns:
            bool: 是否清空成功
        """
        if not self.redis_client:
            logger.error("Redis连接未初始化")
            return False
            
        try:
            await self.redis_client.flushdb()
            logger.info("已清空所有数据")
            return True
        except Exception as e:
            logger.error(f"清空数据失败: {str(e)}")
            return False
    
    async def get_info(self) -> Dict[str, Any]:
        """
        获取Redis服务器信息
        
        Returns:
            Dict[str, Any]: 服务器信息
        """
        if not self.redis_client:
            logger.error("Redis连接未初始化")
            return {}
            
        try:
            info = await self.redis_client.info()
            result = {
                'version': info['redis_version'],
                'uptime': info['uptime_in_seconds'],
                'connected_clients': info['connected_clients'],
                'used_memory': info['used_memory_human'],
                'total_commands_processed': info['total_commands_processed']
            }
            return result
        except Exception as e:
            logger.error(f"获取服务器信息失败: {str(e)}")
            return {} 