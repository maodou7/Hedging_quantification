"""
交易所配置模块
包含交易所连接信息和市场结构配置
"""
import os
from typing import Dict, List, Set
from dotenv import load_dotenv
import ccxt

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

# 市场类型
MARKET_TYPES = {
    "spot": True,      # 现货市场
    "futures": False,  # 期货市场
    "swap": True      # 永续合约市场
}

# Redis配置
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "password": os.getenv("REDIS_PASSWORD", ""),
    "db": int(os.getenv("REDIS_DB", "0")),
    "decode_responses": True
}

# 缓存模式
CACHE_MODE = os.getenv("CACHE_MODE", "selective")

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

def get_exchange_config(exchange_name: str) -> Dict:
    """获取交易所配置，从环境变量中读取敏感信息"""
    base_config = {
        'enableRateLimit': True,
        'timeout': 30000,
        'options': {
            'defaultType': 'spot',  # 默认为现货，但支持切换到swap
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

def get_common_symbols(exchanges: List[str]) -> List[str]:
    """获取所有交易所共有的交易对"""
    all_symbols: Dict[str, Set[str]] = {}
    
    for exchange_id in exchanges:
        try:
            # 创建交易所实例
            exchange_class = getattr(ccxt, exchange_id)
            exchange_config = get_exchange_config(exchange_id)
            exchange = exchange_class(exchange_config)
            
            # 加载市场
            exchange.load_markets()
            
            # 获取现货和永续合约的所有交易对
            spot_symbols = set()
            swap_symbols = set()
            
            for symbol, market in exchange.markets.items():
                # 只考虑USDT计价的交易对
                if not symbol.endswith('/USDT'):
                    continue
                    
                if market.get('spot'):
                    spot_symbols.add(symbol)
                elif market.get('swap') or market.get('future'):
                    # 有些交易所用future表示永续合约
                    if market.get('contract') and market.get('linear'):
                        swap_symbols.add(symbol)
            
            # 合并现货和永续的交易对
            all_symbols[exchange_id] = spot_symbols.union(swap_symbols)
            
        except Exception as e:
            print(f"获取{exchange_id}交易对时出错: {str(e)}")
            all_symbols[exchange_id] = set()
    
    # 找出所有交易所的交易对交集
    common_symbols = set.intersection(*all_symbols.values()) if all_symbols else set()
    
    # 转换为列表并排序
    return sorted(list(common_symbols))

# 报价货币
QUOTE_CURRENCIES = ["USDT"]

# 动态获取共有交易对
COMMON_SYMBOLS = get_common_symbols(EXCHANGES)

# 所有支持的交易对
SYMBOLS = {
    exchange_id: COMMON_SYMBOLS
    for exchange_id in EXCHANGES
}

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

# 交易所完整配置（动态获取）
EXCHANGE_CONFIGS = {name: get_exchange_config(name) for name in EXCHANGES} 