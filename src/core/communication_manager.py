"""
通信管理器模块

实现不同的进程间通信方式：
1. Redis通信 - 用于Redis缓存模式
2. 共享内存通信 - 用于本地缓存模式
3. 消息队列通信 - 用于无缓存模式
"""

import mmap
import json
import asyncio
from multiprocessing import Queue, shared_memory
from typing import Dict, Any, Callable
from abc import ABC, abstractmethod
from src.Config.exchange_config import REDIS_CONFIG, CACHE_MODE
from src.core.redis_manager import RedisManager

class CommunicationManager(ABC):
    """通信管理器基类"""
    
    @abstractmethod
    def publish_price(self, price_data: Dict[str, Any]):
        """发布价格数据"""
        pass
        
    @abstractmethod
    def publish_command(self, command: str, data: Dict[str, Any] = None):
        """发布系统命令"""
        pass
        
    @abstractmethod
    def subscribe_price(self, callback: Callable[[Dict[str, Any]], None]):
        """订阅价格数据"""
        pass
        
    @abstractmethod
    def subscribe_command(self, callback: Callable[[str, Dict[str, Any]], None]):
        """订阅系统命令"""
        pass
        
    @abstractmethod
    async def start_listening(self):
        """开始监听消息"""
        pass
        
    @abstractmethod
    def stop_listening(self):
        """停止监听"""
        pass

class SharedMemoryManager(CommunicationManager):
    """共享内存通信管理器 - 用于本地缓存模式"""
    
    def __init__(self):
        self.price_callbacks = []
        self.command_callbacks = []
        self.running = True
        
        # 创建共享内存块
        self.price_shm = shared_memory.SharedMemory(
            name='price_data',
            create=True,
            size=1024*1024  # 1MB
        )
        self.command_shm = shared_memory.SharedMemory(
            name='command_data',
            create=True,
            size=1024*1024  # 1MB
        )
        
    def publish_price(self, price_data: Dict[str, Any]):
        """发布价格数据到共享内存"""
        try:
            data = json.dumps(price_data).encode()
            self.price_shm.buf[:len(data)] = data
        except Exception as e:
            print(f"[共享内存] 发布价格数据失败: {str(e)}")
            
    def publish_command(self, command: str, data: Dict[str, Any] = None):
        """发布系统命令到共享内存"""
        try:
            message = json.dumps({
                "command": command,
                "data": data or {}
            }).encode()
            self.command_shm.buf[:len(message)] = message
        except Exception as e:
            print(f"[共享内存] 发布命令失败: {str(e)}")
            
    def subscribe_price(self, callback: Callable[[Dict[str, Any]], None]):
        """订阅价格数据"""
        self.price_callbacks.append(callback)
        
    def subscribe_command(self, callback: Callable[[str, Dict[str, Any]], None]):
        """订阅系统命令"""
        self.command_callbacks.append(callback)
        
    async def start_listening(self):
        """开始监听共享内存"""
        print("[共享内存] 开始监听消息...")
        last_price_data = b""
        last_command_data = b""
        
        while self.running:
            # 检查价格数据更新
            price_data = bytes(self.price_shm.buf[:1024*1024])
            if price_data != last_price_data and price_data.strip(b'\x00'):
                try:
                    data = json.loads(price_data.decode().strip('\x00'))
                    for callback in self.price_callbacks:
                        callback(data)
                    last_price_data = price_data
                except Exception as e:
                    print(f"[共享内存] 处理价格数据失败: {str(e)}")
                    
            # 检查命令数据更新
            command_data = bytes(self.command_shm.buf[:1024*1024])
            if command_data != last_command_data and command_data.strip(b'\x00'):
                try:
                    data = json.loads(command_data.decode().strip('\x00'))
                    for callback in self.command_callbacks:
                        callback(data["command"], data["data"])
                    last_command_data = command_data
                except Exception as e:
                    print(f"[共享内存] 处理命令数据失败: {str(e)}")
                    
            await asyncio.sleep(0.001)
            
    def stop_listening(self):
        """停止监听"""
        self.running = False
        self.price_shm.close()
        self.command_shm.close()
        self.price_shm.unlink()
        self.command_shm.unlink()
        print("[共享内存] 已停止监听")

class MessageQueueManager(CommunicationManager):
    """消息队列通信管理器 - 用于无缓存模式"""
    
    def __init__(self):
        self.price_queue = Queue()
        self.command_queue = Queue()
        self.price_callbacks = []
        self.command_callbacks = []
        self.running = True
        
    def publish_price(self, price_data: Dict[str, Any]):
        """发布价格数据到消息队列"""
        try:
            self.price_queue.put(price_data)
        except Exception as e:
            print(f"[消息队列] 发布价格数据失败: {str(e)}")
            
    def publish_command(self, command: str, data: Dict[str, Any] = None):
        """发布系统命令到消息队列"""
        try:
            message = {
                "command": command,
                "data": data or {}
            }
            self.command_queue.put(message)
        except Exception as e:
            print(f"[消息队列] 发布命令失败: {str(e)}")
            
    def subscribe_price(self, callback: Callable[[Dict[str, Any]], None]):
        """订阅价格数据"""
        self.price_callbacks.append(callback)
        
    def subscribe_command(self, callback: Callable[[str, Dict[str, Any]], None]):
        """订阅系统命令"""
        self.command_callbacks.append(callback)
        
    async def start_listening(self):
        """开始监听消息队列"""
        print("[消息队列] 开始监听消息...")
        while self.running:
            # 处理价格数据
            while not self.price_queue.empty():
                try:
                    data = self.price_queue.get_nowait()
                    for callback in self.price_callbacks:
                        callback(data)
                except Exception as e:
                    print(f"[消息队列] 处理价格数据失败: {str(e)}")
                    
            # 处理命令数据
            while not self.command_queue.empty():
                try:
                    message = self.command_queue.get_nowait()
                    for callback in self.command_callbacks:
                        callback(message["command"], message["data"])
                except Exception as e:
                    print(f"[消息队列] 处理命令数据失败: {str(e)}")
                    
            await asyncio.sleep(0.001)
            
    def stop_listening(self):
        """停止监听"""
        self.running = False
        print("[消息队列] 已停止监听")

def create_communication_manager() -> CommunicationManager:
    """创建通信管理器工厂方法"""
    if CACHE_MODE == 1:  # Redis缓存
        return RedisManager()
    elif CACHE_MODE == 2:  # 本地缓存
        return SharedMemoryManager()
    else:  # 无缓存
        return MessageQueueManager() 