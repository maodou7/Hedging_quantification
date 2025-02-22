"""
缓存配置模块
"""
import os
from enum import Enum
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class CacheStrategy(Enum):
    NO_CACHE = "no_cache"
    REDIS = "redis"
    LOCAL = "local"

# 从环境变量获取 Redis 配置
REDIS_HOST = os.getenv('REDIS_HOST', '192.168.186.129')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'Aaa2718..')
REDIS_DB = int(os.getenv('REDIS_DB', '0'))

CACHE_CONFIG = {
    "strategy": CacheStrategy.LOCAL,  # 默认使用本地缓存
    "redis": {
        "host": REDIS_HOST,
        "port": REDIS_PORT,
        "password": REDIS_PASSWORD,
        "db": REDIS_DB,
        "key_prefix": "hedging_",
        "decode_responses": True,
        "socket_timeout": 5,
        "socket_connect_timeout": 5
    },
    "local": {
        "output_dir": "cache",
        "file_extension": ".json",
        "indent": 2,
        "ensure_ascii": False
    },
    # 是否使用 Redis
    'use_redis': True,
    
    # Redis 配置
    'redis_host': REDIS_HOST,
    'redis_port': REDIS_PORT,
    'redis_db': REDIS_DB,
    'redis_password': REDIS_PASSWORD,
    'redis_key_prefix': 'hedging:',
    'redis_timeout': 5,  # 连接超时时间(秒)
    
    # 内存缓存配置
    'memory_cache_size': 1000,  # 最大缓存条目数
    'memory_cache_ttl': 3600,   # 默认过期时间(秒)
    
    # 缓存键配置
    'key_separator': ':',       # 键名分隔符
    'key_prefix': 'hedging',    # 键名前缀
    
    # 序列化配置
    'serialization': {
        'ensure_ascii': False,  # JSON序列化是否确保ASCII编码
        'indent': 4            # JSON序列化缩进空格数
    }
}