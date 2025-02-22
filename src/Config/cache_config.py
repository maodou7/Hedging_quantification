"""缓存配置管理模块

此模块定义了系统的缓存存储结构和配置，用于统一管理所有缓存文件的存储位置和访问策略。
"""

import os
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent

# 缓存根目录
CACHE_ROOT = ROOT_DIR / 'cache'

# 确保缓存目录存在
CACHE_ROOT.mkdir(exist_ok=True)

# 市场数据缓存目录
MARKET_DATA_DIR = CACHE_ROOT / 'market_data'
SYMBOLS_CACHE_DIR = MARKET_DATA_DIR / 'symbols'
ORDERBOOKS_CACHE_DIR = MARKET_DATA_DIR / 'orderbooks'
TICKERS_CACHE_DIR = MARKET_DATA_DIR / 'tickers'

# 订单数据缓存目录
ORDER_DATA_DIR = CACHE_ROOT / 'order_data'
ACTIVE_ORDERS_DIR = ORDER_DATA_DIR / 'active'
HISTORY_ORDERS_DIR = ORDER_DATA_DIR / 'history'

# 持仓数据缓存目录
POSITION_DATA_DIR = CACHE_ROOT / 'position_data'
CURRENT_POSITIONS_DIR = POSITION_DATA_DIR / 'current'
HISTORY_POSITIONS_DIR = POSITION_DATA_DIR / 'history'

# 交易数据缓存目录
TRADE_DATA_DIR = CACHE_ROOT / 'trade_data'
EXECUTED_TRADES_DIR = TRADE_DATA_DIR / 'executed'
PENDING_TRADES_DIR = TRADE_DATA_DIR / 'pending'

# 临时文件目录
TEMP_DIR = CACHE_ROOT / 'temp'

# 创建所有缓存子目录
for directory in [
    MARKET_DATA_DIR, SYMBOLS_CACHE_DIR, ORDERBOOKS_CACHE_DIR, TICKERS_CACHE_DIR,
    ORDER_DATA_DIR, ACTIVE_ORDERS_DIR, HISTORY_ORDERS_DIR,
    POSITION_DATA_DIR, CURRENT_POSITIONS_DIR, HISTORY_POSITIONS_DIR,
    TRADE_DATA_DIR, EXECUTED_TRADES_DIR, PENDING_TRADES_DIR,
    TEMP_DIR
]:
    directory.mkdir(parents=True, exist_ok=True)

# 缓存配置
CACHE_CONFIG = {
    # 缓存策略
    'strategy': 'local',  # 可选: local, redis, none
    
    # 文件缓存配置
    'file_cache': {
        'root_dir': str(CACHE_ROOT),
        'max_age': 86400,  # 文件最大保存时间（秒）
        'cleanup_interval': 3600,  # 清理间隔（秒）
    },
    
    # Redis缓存配置
    'redis': {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'password': None,
        'socket_timeout': 5,
    },
    
    # 内存缓存配置
    'memory': {
        'max_size': 1000,  # 最大缓存条目数
        'ttl': 3600,  # 默认过期时间（秒）
    }
}

# 导出所有缓存目录路径
__all__ = [
    'CACHE_ROOT',
    'MARKET_DATA_DIR',
    'SYMBOLS_CACHE_DIR',
    'ORDERBOOKS_CACHE_DIR',
    'TICKERS_CACHE_DIR',
    'ORDER_DATA_DIR',
    'ACTIVE_ORDERS_DIR',
    'HISTORY_ORDERS_DIR',
    'POSITION_DATA_DIR',
    'CURRENT_POSITIONS_DIR',
    'HISTORY_POSITIONS_DIR',
    'TRADE_DATA_DIR',
    'EXECUTED_TRADES_DIR',
    'PENDING_TRADES_DIR',
    'TEMP_DIR',
    'CACHE_CONFIG'
]