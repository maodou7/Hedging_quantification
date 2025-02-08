"""
测试Redis连接
"""

import redis
from src.Config.exchange_config import REDIS_CONFIG

def test_redis_connection():
    try:
        # 创建Redis连接
        r = redis.Redis(
            host=REDIS_CONFIG['host'],
            port=REDIS_CONFIG['port'],
            password=REDIS_CONFIG['password'],
            db=REDIS_CONFIG['db'],
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        
        # 测试连接
        print("正在测试Redis连接...")
        response = r.ping()
        if response:
            print("Redis连接成功!")
            
            # 测试写入
            print("\n测试数据写入...")
            r.set("test_key", "test_value")
            value = r.get("test_key")
            print(f"写入的测试数据: {value}")
            
            # 清理测试数据
            r.delete("test_key")
            print("测试数据已清理")
            
        return True
        
    except redis.ConnectionError as e:
        print(f"Redis连接错误: {str(e)}")
        return False
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    test_redis_connection() 