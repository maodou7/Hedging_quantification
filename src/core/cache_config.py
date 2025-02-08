from enum import Enum
from src.Config.exchange_config import REDIS_CONFIG, MARKET_STRUCTURE_CONFIG, CACHE_MODE

class CacheStrategy(Enum):
    LOCAL = "local"
    REDIS = "redis"
    NO_CACHE = "no_cache"

# 根据CACHE_MODE设置缓存策略
def get_cache_strategy():
    if CACHE_MODE == 1:  # Redis缓存
        return CacheStrategy.REDIS
    elif CACHE_MODE == 2:  # 本地文件缓存
        return CacheStrategy.LOCAL
    else:  # 不使用缓存
        return CacheStrategy.NO_CACHE

CACHE_CONFIG = {
    "strategy": get_cache_strategy(),  # 根据配置设置缓存策略
    "redis": REDIS_CONFIG,
    "local": {
        "output_dir": "cache",  # 本地缓存目录
        "file_extension": ".json",
        "indent": 2,
        "ensure_ascii": False
    }
} 