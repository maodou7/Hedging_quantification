"""
交易所配置模块
包含交易所连接信息和市场结构配置
"""
import os
from typing import Dict, List, Set, Optional, Any
from dotenv import load_dotenv
import ccxt
import asyncio
import logging
from typing import Dict, Any, Optional, List
from src.core.cache_manager import CacheManager

# Add rate limit handling
from ccxt.base.errors import RateLimitExceeded

def get_exchange_config(exchange_id: str) -> Dict[str, Any]:
    """获取交易所配置"""
    if exchange_id not in EXCHANGE_CONFIGS:
        return None
    return EXCHANGE_CONFIGS[exchange_id]

# 加载环境变量
load_dotenv()

# 功能开关配置
FEATURE_FLAGS = {
    "monitoring": {
        "enabled": True,           # 是否启用市场监控
        "price_update_interval": 1,  # 价格更新间隔(秒)
        "depth_update_interval": 5,  # 深度更新间隔(秒)
        "trade_update_interval": 1   # 成交更新间隔(秒)
    },
    "machine_learning": {
        "enabled": True,           # 是否启用机器学习
        "min_data_points": 1000,   # 开始训练所需的最小数据点数
        "update_interval": 3600,   # 模型更新间隔(秒)
        "prediction_threshold": 0.001,  # 预测阈值
        "models": {
            "lstm": {
                "enabled": True,
                "batch_size": 32,
                "epochs": 100,
                "sequence_length": 60
            },
            "xgboost": {
                "enabled": False
            }
        }
    },
    "trading": {
        "enabled": True,           # 是否启用交易
        "max_open_orders": 5,      # 最大未完成订单数
        "min_profit_threshold": 0.002,  # 最小利润阈值
        "risk_management": {
            "max_position_size": 1000,  # 最大持仓量
            "max_daily_loss": 100,      # 最大日亏损
            "max_drawdown": 0.1         # 最大回撤
        }
    },
    
    # 策略控制配置
    "strategies": {
        "mode": "mixed",  # single: 单一策略, mixed: 混合策略
        
        # 三角套利策略
        "triangular_arbitrage": {
            "enabled": True,
            "min_profit_threshold": 0.001,  # 最小利润率
            "max_trade_amount": 1000,      # 最大交易金额
            "pairs": ["BTC/USDT", "ETH/USDT", "ETH/BTC"],  # 三角套利对
            "update_interval": 1,          # 更新间隔(秒)
            "execution_timeout": 5,        # 执行超时时间(秒)
            "risk_control": {
                "max_slippage": 0.001,     # 最大滑点
                "min_volume_threshold": 1000  # 最小交易量阈值
            }
        },
        
        # 统计套利策略
        "statistical_arbitrage": {
            "enabled": True,
            "window_size": 3600,          # 观察窗口大小(秒)
            "z_score_threshold": 2.0,     # z分数阈值
            "pairs": [                    # 配对交易对
                ["BTC/USDT_binance", "BTC/USDT_okx"],
                ["ETH/USDT_binance", "ETH/USDT_okx"]
            ],
            "position_holding_time": 3600,  # 持仓时间(秒)
            "max_position_value": 10000,   # 最大持仓价值
            "correlation_threshold": 0.8    # 相关性阈值
        },
        
        # 期现套利策略
        "spot_future_arbitrage": {
            "enabled": True,
            "min_spread_threshold": 0.002,  # 最小价差阈值
            "max_leverage": 5,             # 最大杠杆倍数
            "funding_rate_threshold": 0.001, # 资金费率阈值
            "pairs": ["BTC/USDT", "ETH/USDT"],  # 交易对
            "position_limit": {
                "BTC": 1.0,                # BTC最大持仓量
                "ETH": 10.0                # ETH最大持仓量
            },
            "hedge_ratio": 1.0,            # 对冲比例
            "margin_ratio": 0.5            # 保证金比例
        },
        
        # 价差套利策略
        "spread_arbitrage": {
            "enabled": True,
            "min_profit_threshold": 0.002,  # 最小利润阈值
            "trade_amount": 1000,          # 交易金额
            "max_open_orders": 5,          # 最大挂单数
            "price_decimal": 8,            # 价格小数位
            "amount_decimal": 8,           # 数量小数位
            "update_interval": 1,          # 更新间隔(秒)
            "execution_timeout": 5         # 执行超时时间(秒)
        },
        
        # 混合策略配置
        "mixed_strategy": {
            "enabled": True,
            "strategy_weights": {          # 策略权重
                "triangular_arbitrage": 0.3,
                "statistical_arbitrage": 0.2,
                "spot_future_arbitrage": 0.3,
                "spread_arbitrage": 0.2
            },
            "capital_allocation": {        # 资金分配
                "triangular_arbitrage": 0.3,
                "statistical_arbitrage": 0.2,
                "spot_future_arbitrage": 0.3,
                "spread_arbitrage": 0.2
            },
            "risk_limits": {
                "max_total_position": 50000,  # 最大总持仓
                "max_single_strategy_loss": 1000,  # 单个策略最大亏损
                "max_total_loss": 3000        # 总体最大亏损
            },
            "rebalance_interval": 3600,    # 再平衡间隔(秒)
            "performance_threshold": {      # 策略表现阈值
                "min_sharpe_ratio": 1.5,    # 最小夏普比率
                "min_win_rate": 0.6         # 最小胜率
            }
        }
    }
}

# 交易所列表
EXCHANGES = ["binance", "bybit", "okx", "huobi", "gateio"]

# 定义要监控的交易对
DEFAULT_SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
SYMBOLS = DEFAULT_SYMBOLS  # 直接使用默认交易对列表

# 报价货币
QUOTE_CURRENCIES = ["USDT"]

# 市场类型
MARKET_TYPES = {
    "spot": True,      # 现货市场
    "futures": False,  # 期货市场
    "swap": False,     # 永续合约市场
    "margin": False    # 杠杆市场
}

# Redis配置
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "password": os.getenv("REDIS_PASSWORD", ""),
    "db": int(os.getenv("REDIS_DB", "0")),
    "decode_responses": True
}

# 缓存策略配置
CACHE_MODE = {
    "active_strategy": os.getenv("CACHE_STRATEGY", "redis"),  # 可选: redis, memory, none
    
    # Redis缓存策略配置
    "redis": {
        "enabled": True,
        "update_interval": 60,  # 缓存更新间隔(秒)
        "cleanup_interval": 3600,  # 缓存清理间隔(秒)
        "max_items": 10000,  # 最大缓存项数
        "ttl": 3600,  # 默认过期时间(秒)
        "compression": True,  # 是否启用数据压缩
        "serializer": "pickle",  # 序列化方式：pickle, json, msgpack
        "retry_options": {
            "max_retries": 3,
            "retry_delay": 1,  # 重试延迟(秒)
            "timeout": 5  # 连接超时(秒)
        }
    },
    
    # 本地共享内存缓存策略配置
    "memory": {
        "enabled": True,
        "backend": "shared_memory",  # windows下使用mmap，linux下使用shm
        "max_size": 1024 * 1024 * 512,  # 最大内存使用(512MB)
        "update_interval": 30,  # 更新间隔(秒)
        "cleanup_interval": 1800,  # 清理间隔(秒)
        "ttl": 1800,  # 默认过期时间(秒)
        "max_items": 5000,  # 最大缓存条目数
        "sync_interval": 5,  # 同步间隔(秒)
        "compression": True,  # 是否启用数据压缩
        "persistence": {
            "enabled": True,  # 是否启用持久化
            "interval": 300,  # 持久化间隔(秒)
            "path": "data/cache"  # 持久化文件路径
        }
    },
    
    # 无缓存策略（消息队列）配置
    "none": {
        "enabled": True,
        "queue_type": "memory",  # 队列类型：memory, redis
        "max_queue_size": 10000,  # 最大队列大小
        "batch_size": 100,  # 批处理大小
        "flush_interval": 1,  # 刷新间隔(秒)
        "retry_options": {
            "max_retries": 3,
            "retry_delay": 1
        },
        "monitoring": {
            "enabled": True,
            "metrics_interval": 60  # 指标收集间隔(秒)
        }
    },
    
    # 系统适配配置
    "system_adapter": {
        "windows": {
            "shared_memory_impl": "mmap",
            "lock_type": "file",
            "ipc_method": "named_pipe"
        },
        "linux": {
            "shared_memory_impl": "shm",
            "lock_type": "posix",
            "ipc_method": "unix_socket"
        }
    }
}

# 交易所配置
EXCHANGE_CONFIGS = {
    'binance': {
        'name': 'Binance',
        'api_key': os.getenv('BINANCE_API_KEY', ''),
        'api_secret': os.getenv('BINANCE_SECRET', ''),
        'market_types': ['spot'],
        'quote_currencies': ['USDT', 'BUSD'],
        'rate_limits': {
            'requests_per_second': 20,
            'orders_per_second': 10
        },
        'timeout': 30000
    },
    'bybit': {
        'name': 'Bybit',
        'api_key': os.getenv('BYBIT_API_KEY', ''),
        'api_secret': os.getenv('BYBIT_SECRET', ''),
        'market_types': ['spot'],
        'quote_currencies': ['USDT'],
        'rate_limits': {
            'requests_per_second': 10,
            'orders_per_second': 5
        },
        'timeout': 30000
    },
    'okx': {
        'name': 'OKX',
        'api_key': os.getenv('OKX_API_KEY', ''),
        'api_secret': os.getenv('OKX_SECRET', ''),
        'password': os.getenv('OKX_PASSWORD', ''),
        'market_types': ['spot'],
        'quote_currencies': ['USDT'],
        'rate_limits': {
            'requests_per_second': 20,
            'orders_per_second': 10
        },
        'timeout': 30000
    },
    'huobi': {
        'name': 'Huobi',
        'api_key': os.getenv('HUOBI_API_KEY', ''),
        'api_secret': os.getenv('HUOBI_SECRET', ''),
        'market_types': ['spot'],
        'quote_currencies': ['USDT'],
        'rate_limits': {
            'requests_per_second': 10,
            'orders_per_second': 5
        },
        'timeout': 30000
    },
    'gateio': {
        'name': 'Gate.io',
        'api_key': os.getenv('GATEIO_API_KEY', ''),
        'api_secret': os.getenv('GATEIO_SECRET', ''),
        'market_types': ['spot'],
        'quote_currencies': ['USDT'],
        'rate_limits': {
            'requests_per_second': 10,
            'orders_per_second': 5
        },
        'timeout': 30000
    }
}

# 市场结构配置
MARKET_STRUCTURE_CONFIG = {
    "cache_prefix": "market",
    "cache_types": ["orderbook", "ticker", "trades"],
    "default_cache_ttl": 3600,
    "cache_ttl": {
        "orderbook": 60,
        "ticker": 30,
        "trades": 300
    }
}

logger = logging.getLogger("arbitrage")

def get_or_create_eventloop():
    """获取或创建事件循环"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

async def get_common_symbols_async(max_retries: int = 3) -> List[str]:
    """
    异步获取所有交易所共有的交易对
    """
    try:
        common_symbols = set()
        first = True
        
        # 确保 EXCHANGE_CONFIGS 已定义
        exchange_configs = {name: get_exchange_config(name) for name in EXCHANGES}
        
        for exchange_name in EXCHANGES:
            try:
                config = exchange_configs[exchange_name]
                if not config:
                    logger.warning(f"未找到交易所 {exchange_name} 的配置")
                    continue
                
                # 创建交易所实例
                exchange_class = getattr(ccxt.async_support, exchange_name)
                exchange = exchange_class(config)
                
                # 加载市场数据
                markets = await exchange.load_markets()
                symbols = [symbol for symbol in markets.keys() if markets[symbol]['active'] and markets[symbol]['spot']]
                
                if not symbols:
                    logger.warning(f"交易所 {exchange_name} 没有可用的交易对")
                    continue
                
                if first:
                    common_symbols = set(symbols)
                    first = False
                else:
                    common_symbols &= set(symbols)
                    
            except Exception as e:
                logger.error(f"获取交易所 {exchange_name} 交易对时出错: {str(e)}")
                continue
            finally:
                if 'exchange' in locals():
                    await exchange.close()
        
        return list(common_symbols) if common_symbols else DEFAULT_SYMBOLS
        
    except Exception as e:
        logger.error(f"获取共有交易对失败: {str(e)}")
        return DEFAULT_SYMBOLS

async def update_common_symbols() -> Optional[List[str]]:
    """更新共有交易对列表"""
    try:
        cache = CacheManager()
        new_symbols = await get_common_symbols_async()
        if new_symbols:
            global COMMON_SYMBOLS
            COMMON_SYMBOLS = new_symbols
            await cache.set("common_symbols", new_symbols, expire=3600)  # 使用 expire 而不是 ex
        return new_symbols
    except Exception as e:
        logger.error(f"更新交易对失败: {str(e)}")
        return None

def initialize_common_symbols():
    """初始化共有交易对"""
    try:
        from src.utils.system_adapter import SystemAdapter
        system_adapter = SystemAdapter()
        
        # 获取或创建事件循环
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("事件循环已在运行，使用默认交易对")
                return DEFAULT_SYMBOLS
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        # 使用 run_until_complete 运行异步函数
        if not loop.is_closed():
            symbols = loop.run_until_complete(update_common_symbols())
            if symbols:
                return symbols
        return DEFAULT_SYMBOLS
    except Exception as e:
        logger.error(f"初始化交易对失败: {str(e)}")
        return DEFAULT_SYMBOLS
    finally:
        try:
            if 'loop' in locals() and not loop.is_closed() and not loop.is_running():
                loop.stop()
        except Exception as e:
            logger.error(f"停止事件循环失败: {str(e)}")

# 初始化 COMMON_SYMBOLS
COMMON_SYMBOLS = initialize_common_symbols()

# 要监控的交易对
SYMBOLS = COMMON_SYMBOLS

# 各交易所支持的交易对（按交易所API规范）
EXCHANGE_SYMBOLS = {
    "binance": ["BTC/USDT", "ETH/USDT", "BNB/USDT"],  # 使用斜杠分隔
    "bybit": ["BTC/USDT", "ETH/USDT", "BNB/USDT"],    # 同Binance格式
    "okx": ["BTC-USDT", "ETH-USDT", "BNB-USDT"],       # 使用短横线分隔
    "huobi": ["btcusdt", "ethusdt", "bnbusdt"],        # 全小写无分隔符
    "gateio": ["BTC_USDT", "ETH_USDT", "BNB_USDT"]     # 使用下划线分隔
}

def validate_symbol_format(exchange_id: str, symbol: str) -> bool:
    """根据交易所规范验证交易对格式"""
    try:
        # 获取交易所配置
        exchange_config = get_exchange_config(exchange_id)
        
        # 如果没有API密钥，使用基础配置
        if not exchange_config.get('apiKey'):
            exchange_config = {
                'enableRateLimit': True,
                'timeout': 30000,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True
                }
            }
            
        # 转换交易对格式
        if exchange_id == 'huobi':
            formatted_symbol = symbol.lower().replace('/', '').replace('-', '').replace('_', '')
        elif exchange_id == 'okx':
            formatted_symbol = symbol.replace('/', '-')
        elif exchange_id == 'gateio':
            formatted_symbol = symbol.replace('/', '_')
        else:  # binance, bybit等使用标准格式
            formatted_symbol = symbol
            
        # 创建交易所实例
        exchange_class = getattr(ccxt, exchange_id)
        instance = exchange_class(exchange_config)
        
        # 加载市场数据
        instance.load_markets()
        
        # 验证交易对
        market = instance.market(formatted_symbol)
        return (market['active'] and 
                market['quote'] in QUOTE_CURRENCIES and
                market['spot'])  # 只验证现货交易对
                
    except (ccxt.BadSymbol, AttributeError, KeyError) as e:
        from src.utils.logger import ArbitrageLogger
        ArbitrageLogger().debug(f"交易对格式验证失败 {exchange_id}/{symbol}: {str(e)}")
        return False
    except Exception as e:
        from src.utils.logger import ArbitrageLogger
        ArbitrageLogger().warning(f"交易对格式验证异常 {exchange_id}/{symbol}: {str(e)}")
        return False
    finally:
        if 'instance' in locals():
            try:
                instance.close()
            except Exception:
                pass

# 默认手续费率
DEFAULT_FEES = {
    "maker": 0.001,  # 0.1%
    "taker": 0.002   # 0.2%
}

# 指标配置
INDICATOR_CONFIG = {
    # 序列长度
    "sequence_length": FEATURE_FLAGS["machine_learning"]["models"]["lstm"]["sequence_length"],
    "prediction_length": 10,  # 预测未来10个时间点
    
    # 特征列表
    "features": [
        "close",    # 收盘价
        "volume",   # 成交量
        "rsi",      # RSI指标
        "macd",     # MACD指标
        "bid",      # 买一价
        "ask",      # 卖一价
        "spread"    # 买卖价差
    ],
    
    # 模型参数
    "model_params": {
        "hidden_size": 50,
        "num_layers": 2,
        "dropout": 0.2,
        "learning_rate": 0.001
    },
    
    # 训练参数
    "train_params": {
        "batch_size": FEATURE_FLAGS["machine_learning"]["models"]["lstm"]["batch_size"],
        "epochs": FEATURE_FLAGS["machine_learning"]["models"]["lstm"]["epochs"],
        "validation_split": 0.2
    }
}
def get_exchange_config(exchange_id: str) -> Dict[str, Any]:
    """获取交易所配置"""
    if exchange_id not in EXCHANGE_CONFIGS:
        return None
    return EXCHANGE_CONFIGS[exchange_id]
