"""
测试Redis连接
"""

import asyncio
import os
from src.core.redis_manager import RedisManager
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_redis_connection():
    """测试Redis连接"""
    redis_manager = RedisManager()
    
    # 初始化连接
    success = await redis_manager.initialize()
    if success:
        print("Redis连接成功！")
        
        # 测试基本操作
        await redis_manager.set("test_key", "test_value")
        value = await redis_manager.get("test_key")
        print(f"测试键值对: {value}")
        
        # 清理
        await redis_manager.delete("test_key")
        await redis_manager.cleanup()
    else:
        print("Redis连接失败！")

if __name__ == "__main__":
    asyncio.run(test_redis_connection())