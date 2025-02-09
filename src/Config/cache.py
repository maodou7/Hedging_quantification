"""
缓存配置模块
"""
from enum import Enum

class CacheStrategy(Enum):
    NO_CACHE = "no_cache"
    REDIS = "redis"
    LOCAL = "local"

CACHE_CONFIG = {
    "strategy": CacheStrategy.LOCAL,  # 默认使用本地缓存
    "redis": {
        "host": "localhost",
        "port": 6379,
        "password": None,  # 从环境变量获取
        "db": 0,
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
    }
} 