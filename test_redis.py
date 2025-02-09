"""
测试Redis连接
"""

from src.core.redis_manager import RedisManager
import sys

def test_redis_connection():
    try:
        print("正在初始化Redis管理器...")
        rm = RedisManager()
        
        print("正在测试Redis连接...")
        response = rm.redis_client.ping()
        
        if response:
            print("Redis连接成功！")
            print(f"服务器信息: {rm.redis_client.info()}")
        else:
            print("Redis连接失败：无法ping通服务器")
            
    except Exception as e:
        print(f"Redis连接出错: {str(e)}")
        sys.exit(1)
        
if __name__ == "__main__":
    test_redis_connection()