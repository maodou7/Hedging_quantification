"""
Redis管理器模块
负责管理Redis连接和操作
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
import redis.asyncio as redis
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis管理器类"""
    
    def __init__(self):
        """初始化Redis管理器"""
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_password = os.getenv("REDIS_PASSWORD", "")
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.redis = None
        self.pubsub = None
        
        logger.info(f"Redis配置: host={self.redis_host}, port={self.redis_port}, db={self.redis_db}")
        
    async def initialize(self):
        """初始化Redis连接"""
        try:
            logger.info("正在连接Redis服务器...")
            
            # 创建Redis连接
            self.redis = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password,
                db=self.redis_db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                max_connections=10
            )
            
            # 测试连接
            logger.info("正在测试Redis连接...")
            await self.redis.ping()
            logger.info(f"Redis连接成功: {self.redis_host}:{self.redis_port}")
            
            # 创建发布/订阅对象
            self.pubsub = self.redis.pubsub()
            
            return True
        except redis.ConnectionError as e:
            logger.error(f"Redis连接错误: {str(e)}")
            return False
        except redis.TimeoutError as e:
            logger.error(f"Redis连接超时: {str(e)}")
            return False
        except redis.AuthenticationError as e:
            logger.error(f"Redis认证失败: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
            return False
    
    async def cleanup(self):
        """清理Redis连接"""
        if self.redis:
            try:
                await self.redis.close()
                logger.info("Redis连接已关闭")
            except Exception as e:
                logger.error(f"关闭Redis连接时发生错误: {str(e)}")
    
    async def set(self, key: str, value: Any, expire: int = None) -> bool:
        """设置键值对"""
        if not self.redis:
            logger.error("Redis连接未初始化")
            return False
            
        try:
            # 序列化值
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            # 设置键值对
            await self.redis.set(key, value)
            
            # 设置过期时间
            if expire:
                await self.redis.expire(key, expire)
            
            return True
        except Exception as e:
            logger.error(f"设置键值对失败: {str(e)}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """获取键值"""
        if not self.redis:
            logger.error("Redis连接未初始化")
            return None
            
        try:
            value = await self.redis.get(key)
            
            # 尝试反序列化
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"获取键值失败: {str(e)}")
            return None
    
    async def delete(self, key: str) -> bool:
        """删除键"""
        if not self.redis:
            logger.error("Redis连接未初始化")
            return False
            
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"删除键失败: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.redis:
            logger.error("Redis连接未初始化")
            return False
            
        try:
            return await self.redis.exists(key)
        except Exception as e:
            logger.error(f"检查键是否存在失败: {str(e)}")
            return False
    
    async def publish(self, channel: str, message: Any) -> bool:
        """发布消息"""
        if not self.redis:
            logger.error("Redis连接未初始化")
            return False
            
        try:
            # 序列化消息
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
            
            # 发布消息
            await self.redis.publish(channel, message)
            return True
        except Exception as e:
            logger.error(f"发布消息失败: {str(e)}")
            return False
    
    async def subscribe(self, channel: str, callback):
        """订阅频道"""
        if not self.redis:
            logger.error("Redis连接未初始化")
            return
            
        try:
            await self.pubsub.subscribe(channel)
            logger.info(f"已订阅频道: {channel}")
            
            # 处理消息
            while True:
                try:
                    message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                    if message:
                        try:
                            # 尝试反序列化消息
                            try:
                                data = json.loads(message['data'])
                            except json.JSONDecodeError:
                                data = message['data']
                            
                            # 调用回调函数
                            await callback(data)
                        except Exception as e:
                            logger.error(f"处理订阅消息失败: {str(e)}")
                            continue
                    
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"获取订阅消息失败: {str(e)}")
                    await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"订阅频道失败: {str(e)}")
    
    async def unsubscribe(self, channel: str):
        """取消订阅"""
        if not self.redis:
            logger.error("Redis连接未初始化")
            return False
            
        try:
            await self.pubsub.unsubscribe(channel)
            logger.info(f"已取消订阅频道: {channel}")
            return True
        except Exception as e:
            logger.error(f"取消订阅失败: {str(e)}")
            return False
    
    async def get_keys(self, pattern: str = "*") -> List[str]:
        """获取匹配模式的所有键"""
        if not self.redis:
            logger.error("Redis连接未初始化")
            return []
            
        try:
            return await self.redis.keys(pattern)
        except Exception as e:
            logger.error(f"获取键列表失败: {str(e)}")
            return []
    
    async def clear_all(self) -> bool:
        """清空所有数据"""
        if not self.redis:
            logger.error("Redis连接未初始化")
            return False
            
        try:
            await self.redis.flushdb()
            logger.info("已清空所有数据")
            return True
        except Exception as e:
            logger.error(f"清空数据失败: {str(e)}")
            return False
    
    async def get_info(self) -> Dict[str, Any]:
        """获取Redis服务器信息"""
        if not self.redis:
            logger.error("Redis连接未初始化")
            return {}
            
        try:
            info = await self.redis.info()
            result = {
                'version': info['redis_version'],
                'uptime_in_seconds': info['uptime_in_seconds'],
                'connected_clients': info['connected_clients'],
                'used_memory_human': info['used_memory_human'],
                'total_commands_processed': info['total_commands_processed']
            }
            logger.info(f"Redis服务器信息: {result}")
            return result
        except Exception as e:
            logger.error(f"获取Redis信息失败: {str(e)}")
            return {} 