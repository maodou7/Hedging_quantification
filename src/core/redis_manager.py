"""
Redis通信管理器

负责:
1. Redis连接管理
2. 发布/订阅通信
3. 缓存管理
"""

import redis
import json
import asyncio
from typing import Dict, Any, Callable
from src.Config.exchange_config import REDIS_CONFIG

class RedisManager:
    """Redis管理器"""
    
    def __init__(self):
        # Redis连接
        self.redis_client = redis.Redis(
            host=REDIS_CONFIG.get('host', 'localhost'),
            port=REDIS_CONFIG.get('port', 6379),
            password=REDIS_CONFIG.get('password'),
            db=REDIS_CONFIG.get('db', 0),
            decode_responses=True,
            socket_timeout=REDIS_CONFIG.get('socket_timeout', 5),
            socket_connect_timeout=REDIS_CONFIG.get('socket_connect_timeout', 5)
        )
        
        # 发布/订阅客户端
        self.pubsub = self.redis_client.pubsub()
        
        # 频道名称
        self.PRICE_CHANNEL = "price_updates"
        self.COMMAND_CHANNEL = "system_commands"
        
        # 消息处理器
        self.message_handlers = {}
        
    def publish_price(self, price_data: Dict[str, Any]):
        """发布价格数据"""
        try:
            message = json.dumps(price_data)
            self.redis_client.publish(self.PRICE_CHANNEL, message)
        except Exception as e:
            print(f"[Redis] 发布价格数据失败: {str(e)}")
            
    def publish_command(self, command: str, data: Dict[str, Any] = None):
        """发布系统命令"""
        try:
            message = {
                "command": command,
                "data": data or {}
            }
            self.redis_client.publish(self.COMMAND_CHANNEL, json.dumps(message))
        except Exception as e:
            print(f"[Redis] 发布命令失败: {str(e)}")
            
    def subscribe_price(self, callback: Callable[[Dict[str, Any]], None]):
        """订阅价格数据"""
        self.message_handlers[self.PRICE_CHANNEL] = callback
        self.pubsub.subscribe(self.PRICE_CHANNEL)
        
    def subscribe_command(self, callback: Callable[[str, Dict[str, Any]], None]):
        """订阅系统命令"""
        self.message_handlers[self.COMMAND_CHANNEL] = callback
        self.pubsub.subscribe(self.COMMAND_CHANNEL)
        
    async def start_listening(self):
        """开始监听消息"""
        print("[Redis] 开始监听消息...")
        while True:
            try:
                message = self.pubsub.get_message()
                if message and message['type'] == 'message':
                    channel = message['channel']
                    data = json.loads(message['data'])
                    
                    # 调用对应的处理器
                    handler = self.message_handlers.get(channel)
                    if handler:
                        if channel == self.PRICE_CHANNEL:
                            handler(data)
                        elif channel == self.COMMAND_CHANNEL:
                            handler(data['command'], data['data'])
                            
                await asyncio.sleep(0.001)  # 避免CPU占用过高
                
            except Exception as e:
                print(f"[Redis] 处理消息失败: {str(e)}")
                
    def stop_listening(self):
        """停止监听"""
        self.pubsub.unsubscribe()
        self.pubsub.close()
        self.redis_client.close()
        print("[Redis] 已停止监听") 