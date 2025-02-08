"""
环境配置模块
包含各种配置信息，如缓存策略、数据库连接等
"""

from .cache_config import CacheStrategy, CACHE_CONFIG

__all__ = ['CacheStrategy', 'CACHE_CONFIG'] 