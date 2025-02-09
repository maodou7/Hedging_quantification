"""
缓存配置模块
"""
from src.config.exchange import REDIS_CONFIG, MARKET_STRUCTURE_CONFIG, CACHE_MODE

class CacheStrategy:
    """缓存策略类"""
    
    def __init__(self, cache_mode: str = CACHE_MODE):
        """初始化缓存策略"""
        self.cache_mode = cache_mode
        self.redis_config = REDIS_CONFIG
        self.market_structure_config = MARKET_STRUCTURE_CONFIG
        
    def should_cache(self, data_type: str) -> bool:
        """判断是否应该缓存指定类型的数据"""
        if self.cache_mode == "none":
            return False
        elif self.cache_mode == "all":
            return True
        elif self.cache_mode == "selective":
            return data_type in self.market_structure_config.get("cache_types", [])
        return False
        
    def get_cache_key(self, data_type: str, identifier: str) -> str:
        """生成缓存键"""
        prefix = self.market_structure_config.get("cache_prefix", "market")
        return f"{prefix}:{data_type}:{identifier}"
        
    def get_cache_ttl(self, data_type: str) -> int:
        """获取缓存的生存时间（秒）"""
        default_ttl = self.market_structure_config.get("default_cache_ttl", 3600)
        ttl_map = self.market_structure_config.get("cache_ttl", {})
        return ttl_map.get(data_type, default_ttl)
        
    def get_redis_config(self) -> dict:
        """获取Redis配置"""
        return self.redis_config
        
CACHE_CONFIG = {
    "strategy": CacheStrategy(),
    "redis": REDIS_CONFIG,
    "market_structure": MARKET_STRUCTURE_CONFIG
} 