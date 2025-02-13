"""
交易所配置模块
包含交易所连接信息和市场结构配置
"""
import os
from typing import Dict, List, Set
from dotenv import load_dotenv
import ccxt

# Add rate limit handling
from ccxt.base.errors import RateLimitExceeded

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
    "swap": False      # 永续合约市场
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

# 动态获取共有交易对（异步）
async def update_common_symbols():
    """更新共有交易对列表"""
    from src.core.cache_manager import cache
    try:
        global COMMON_SYMBOLS
        new_symbols = await get_common_symbols_async()
        if new_symbols:
            COMMON_SYMBOLS = new_symbols
            await cache.set("common_symbols", new_symbols, ex=3600)  # 缓存1小时
    except Exception as e:
        from src.utils.logger import ArbitrageLogger
        ArbitrageLogger().error(f"更新交易对失败: {str(e)}")

# 初始化时立即更新
import asyncio
try:
    COMMON_SYMBOLS = asyncio.run(update_common_symbols()) or DEFAULT_SYMBOLS
except:
    COMMON_SYMBOLS = DEFAULT_SYMBOLS

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

def get_exchange_config(exchange_name: str) -> Dict:
    """获取交易所配置，从环境变量中读取敏感信息"""
    base_config = {
        'enableRateLimit': True,
        'timeout': 30000,
        'options': {
            'defaultType': 'spot',  # 默认为现货
            'adjustForTimeDifference': True,
            'recvWindow': 60000,
            'createMarketBuyOrderRequiresPrice': False,
            'warnOnFetchOHLCVLimitArgument': False,
            'fetchOrderBookLimit': 100,
            'defaultMarginMode': 'cross',  # 默认全仓模式
            'defaultPositionType': 'isolated'  # 默认逐仓模式
        },
        'rateLimit': 100,
        'httpExceptions': {
            '429': True,  # 处理请求过多的错误
            '418': True,  # 处理IP封禁
            '404': True,  # 处理资源不存在
            '403': True,  # 处理权限错误
            '400': True   # 处理请求错误
        }
    }
    
    # 从环境变量获取API密钥
    api_configs = {
        'binance': {
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_SECRET'),
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True,
                'warnOnFetchOHLCVLimitArgument': False,
                'recvWindow': 60000,
                'createMarketBuyOrderRequiresPrice': False,
                'fetchTradesMethod': 'publicGetAggTrades',
                'defaultContractType': 'perpetual'  # 永续合约
            }
        },
        'bybit': {
            'apiKey': os.getenv('BYBIT_API_KEY'),
            'secret': os.getenv('BYBIT_SECRET'),
            'options': {
                'defaultType': 'spot',
                'defaultContractType': 'perpetual'
            }
        },
        'okx': {
            'apiKey': os.getenv('OKX_API_KEY'),
            'secret': os.getenv('OKX_SECRET'),
            'password': os.getenv('OKX_PASSWORD'),
            'options': {
                'defaultType': 'spot',
                'defaultContractType': 'swap'  # OKX的永续合约称为swap
            }
        },
        'huobi': {
            'apiKey': os.getenv('HUOBI_API_KEY'),
            'secret': os.getenv('HUOBI_SECRET'),
            'options': {
                'defaultType': 'spot',
                'defaultContractType': 'swap'
            }
        },
        'gateio': {
            'apiKey': os.getenv('GATEIO_API_KEY'),
            'secret': os.getenv('GATEIO_SECRET'),
            'options': {
                'defaultType': 'spot',
                'defaultContractType': 'swap'
            }
        }
    }
    
    if exchange_name not in api_configs:
        raise ValueError(f"不支持的交易所: {exchange_name}")
    
    # 合并基础配置和特定配置
    exchange_config = base_config.copy()
    specific_config = api_configs[exchange_name]
    
    # 合并options
    if 'options' in specific_config:
        exchange_config['options'].update(specific_config['options'])
    # 合并其他配置
    for key, value in specific_config.items():
        if key != 'options':
            exchange_config[key] = value
    
    return exchange_config

# 交易所完整配置（动态获取）
EXCHANGE_CONFIGS = {name: get_exchange_config(name) for name in EXCHANGES}

def initialize_common_symbols(symbols: List[str]):
    """初始化共有交易对"""
    global COMMON_SYMBOLS
    COMMON_SYMBOLS = symbols

async def get_common_symbols_async(max_retries: int = 3) -> List[str]:
    """
    异步获取所有交易所共同支持的交易对（带重试机制）
    返回所有交易所都支持的交易对的交集
    """
    from src.utils.logger import ArbitrageLogger
    logger = ArbitrageLogger()
    
    async def fetch_exchange_symbols(exchange_id: str) -> Set[str]:
        """异步获取单个交易所的交易对"""
        for attempt in range(max_retries):
            try:
                exchange_class = getattr(ccxt, exchange_id)
                exchange = exchange_class()
                await exchange.load_markets()
                markets = exchange.markets
                
                # 过滤有效交易对
                valid_symbols = set()
                for symbol, market in markets.items():
                    if market.get('active') and market['quote'] in QUOTE_CURRENCIES:
                        # 根据市场类型过滤
                        if market['type'] in MARKET_TYPES and MARKET_TYPES[market['type']]:
                            valid_symbols.add(symbol)
                
                logger.debug(f"[交易对] {exchange_id} 有效交易对数量: {len(valid_symbols)}")
                return valid_symbols
                
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"[交易对] 获取 {exchange_id} 交易对失败: {str(e)}")
                    return set()
                logger.warning(f"[交易对] {exchange_id} 获取失败，将在5秒后重试 ({attempt+1}/{max_retries})")
                await asyncio.sleep(5)
        return set()

    try:
        tasks = [fetch_exchange_symbols(ex_id) for ex_id in EXCHANGES]
        results = await asyncio.gather(*tasks)
        
        common_symbols = None
        for exchange_id, symbols in zip(EXCHANGES, results):
            if not symbols:
                continue
            if common_symbols is None:
                common_symbols = symbols
            else:
                common_symbols &= symbols
            logger.info(f"[交易对] {exchange_id} 共同交易对剩余数量: {len(common_symbols or [])}")

        if not common_symbols:
            logger.warning("[交易对] 未找到共同交易对，使用默认列表")
            return DEFAULT_SYMBOLS
            
        common_list = sorted(list(common_symbols))
        logger.info(f"[交易对] 最终共同交易对数量: {len(common_list)}")
        return common_list
        
    except Exception as e:
        logger.error(f"[交易对] 获取共同交易对失败: {str(e)}")
        return DEFAULT_SYMBOLS
