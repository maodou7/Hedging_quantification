"""
交易所配置文件
包含交易所连接、市场结构、缓存等相关配置
"""

# Redis配置
REDIS_CONFIG = {
    "host": "192.168.186.129",  # Redis服务器地址
    "port": 6379,               # Redis端口
    "password": "Aaa2718..",    # Redis密码
    "db": 0,                    # 使用的数据库编号
    "key_prefix": "market_structure:",  # 键前缀
    "decode_responses": True,    # 自动解码响应
    "socket_timeout": 5,        # 套接字超时时间
    "socket_connect_timeout": 5  # 连接超时时间
}

# 缓存模式
CACHE_MODE = 3  # 1: Redis缓存, 2: 本地文件缓存, 3: 不使用缓存（消息队列）

# 市场结构配置
MARKET_STRUCTURE_CONFIG = {
    "output_dir": "./market_structures",  # 输出目录
    "file_extension": ".json",  # 文件扩展名
    "include_comments": True,  # 是否包含注释
    "indent": 4,  # JSON缩进
    "ensure_ascii": False,  # 允许非ASCII字符
    "update_interval": 3600,  # 市场结构更新间隔(秒)
    "min_volume": 1000,      # 最小交易量(USDT)
    "min_price": 0.00000001  # 最小价格
}

# 支持的交易所列表
EXCHANGES = [
    "binance",
    "okx",
    "bybit",
    "huobi",
    "gateio"
]

# 全局市场类型开关
MARKET_TYPES = {
    'spot': True,   # 是否开启现货
    'swap': True,   # 是否开启永续合约
    'future': False,  # 暂不开启交割合约
    'option': False  # 暂不开启期权
}

# 支持的计价货币
QUOTE_CURRENCIES = [
    "USDT",
    "USD",
    "BUSD"
]

# 监控配置
MONITOR_CONFIG = {
    "mode": "realtime",  # 监控模式: "realtime" 或 "ratelimited"
    "interval_ms": 100,  # 限流模式下的更新间隔（毫秒）
    "max_queue_size": 1000,  # 本地缓存队列大小
    "print_price": True,  # 是否打印价格数据
    "error_retry_delay": 1,  # 错误重试延迟（秒）
    "update_interval": 1.0,  # 数据更新间隔（秒）
    "health_check_interval": 60.0,  # 健康检查间隔（秒）
    "retry_interval": 5.0,  # 重试间隔（秒）
    "max_retries": 3,  # 最大重试次数
    "timeout": 10,  # 超时时间（秒）
    "log_level": "INFO"  # 日志级别
}

# 交易所特定配置
EXCHANGE_CONFIGS = {
    'bybit': {
        'apiKey': 'lEfy155N4ChJ39saut',
        'secret': '6h0zpumtBnibaj9g9Ev1Gh4CHytIq08sFxzF',
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
            'rateLimit': 100  # 限制请求频率为每秒10次
        },
        'timeout': 30000
    },
    'binance': {
        'apiKey': 'CS3Fb8HyP3VNQe5eNWDVC8Oq9YNizCent7zzumcG3DWRfrFPVgI5eOqvO7lmHpgL',
        'secret': 'FwjjyENXMgkbEEUXYMMasO6a4YkdWUbNqBihM1FHO4vI6dwUNhPoBRPsWHGkJ0JY',
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
            'rateLimit': 100
        },
        'timeout': 30000
    },
    'okx': {
        'apiKey': 'e9af7444-5ae3-4ba2-8de8-209c8ee7ec85',
        'secret': '41E38C9D30894DF247540654FC823BD1',
        'password': 'Aaa2718..',
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
            'rateLimit': 200  # OKX需要更严格的限制
        },
        'timeout': 30000
    },
    'huobi': {
        'apiKey': '69d85e1f-795605d7-ed2htwf5tf-a49b5',
        'secret': 'f165570e-4c44e715-ce566f6d-8ded6',
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
            'rateLimit': 100
        },
        'timeout': 30000
    },
    'gateio': {
        'apiKey': 'c46f42a6a538cb65dad12a85c4d2bc6e',
        'secret': 'f0aba6d64a8bfca88bf6f60ca40f24cd9b583536adb0fc63671a4afa47ca2b9b',
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
            'rateLimit': 100
        },
        'timeout': 30000
    }
}

# 通用交易对列表
COMMON_SYMBOLS = {
    'spot': [
        'BTC/USDT',   # 比特币/USDT
        'ETH/USDT',   # 以太坊/USDT
        'BNB/USDT',   # 币安币/USDT
        'XRP/USDT',   # 瑞波币/USDT
        'DOGE/USDT',  # 狗狗币/USDT
        'ADA/USDT',   # 卡尔达诺/USDT
        'SOL/USDT',   # 索拉纳/USDT
        'DOT/USDT',   # 波卡/USDT
        'LTC/USDT'    # 莱特币/USDT
    ],
    'swap': [
        'BTC/USDT:USDT',   # 比特币永续合约
        'ETH/USDT:USDT',   # 以太坊永续合约
        'BNB/USDT:USDT',   # 币安币永续合约
        'XRP/USDT:USDT',   # 瑞波币永续合约
        'DOGE/USDT:USDT',  # 狗狗币永续合约
        'ADA/USDT:USDT',   # 卡尔达诺永续合约
        'SOL/USDT:USDT',   # 索拉纳永续合约
        'DOT/USDT:USDT',   # 波卡永续合约
        'LTC/USDT:USDT'    # 莱特币永续合约
    ]
}

# 交易对配置
SYMBOLS = {
    "spot": COMMON_SYMBOLS['spot'],
    "swap": COMMON_SYMBOLS['swap'],
    "future": [],  # 暂不支持交割合约
    "option": []   # 暂不支持期权
}

# 默认手续费率
DEFAULT_FEES = {
    'bybit': {'maker': 0.001, 'taker': 0.001},
    'binance': {'maker': 0.001, 'taker': 0.001},
    'okx': {'maker': 0.0008, 'taker': 0.001}
}

# 套利配置
ARBITRAGE_CONFIG = {
    'min_profit_usdt': 1.0,         # 最小利润（USDT）
    'max_position_size': 10000.0,    # 最大持仓规模（USDT）
    'max_slippage_percent': 0.001,   # 最大允许滑点
    'default_fee_rate': 0.001,       # 默认交易手续费率
    'min_price_diff_percent': 0.001, # 最小价差百分比
    'min_profit_percent': 0.1,       # 最小利润率要求（0.1%）
    'order_book_depth': 20,          # 订单簿深度
    'price_window_size': 20,         # 价格历史窗口大小
    'update_interval': 1,            # 数据更新间隔（秒）
    'risk_control': {
        'max_drawdown': 0.1,         # 最大回撤
        'stop_loss_rate': 0.02,      # 止损率
        'take_profit_rate': 0.01     # 止盈率
    },
    'execution': {
        'timeout': 5,                # 执行超时（秒）
        'retry_times': 3,            # 重试次数
        'order_type': 'limit'        # 订单类型：market/limit
    }
}

# 风险管理配置
RISK_CONFIG = {
    'max_position_size': 10000.0,    # 最大持仓规模（USDT）
    'max_daily_loss': 100.0,         # 每日最大亏损（USDT）
    'max_trade_frequency': 10,       # 每分钟最大交易次数
    'min_profit_threshold': 1.0,     # 最小利润阈值（USDT）
    'max_order_amount': {            # 每个交易对的最大单笔交易量
        'BTC/USDT': 0.05,
        'ETH/USDT': 0.5
    },
    'min_volume_threshold': {        # 最小交易量阈值（24小时）
        'BTC/USDT': 1000,
        'ETH/USDT': 5000
    },
    'max_order_size': 1000,          # 最大单笔订单规模(USDT)
    'min_spread_ratio': 0.002,       # 最小价差比例
    'max_slippage': 0.001,           # 最大可接受滑点
    'max_daily_loss': -1000,         # 最大日亏损(USDT)
    'max_order_timeout': 30,         # 订单超时时间(秒)
    'position_update_interval': 5,    # 持仓更新间隔(秒)
    'risk_check_interval': 1         # 风险检查间隔(秒)
}

# 指标配置
INDICATOR_CONFIG = {
    'sma_periods': [5, 10, 20],      # SMA周期
    'rsi_period': 14,                # RSI周期
    'volatility_window': 20,         # 波动率计算窗口
    'price_history_size': 1000,      # 价格历史记录大小
    'sma_short_period': 5,           # 短期SMA周期
    'sma_long_period': 20,           # 长期SMA周期
    'rsi_overbought': 70,            # RSI超买阈值
    'rsi_oversold': 30,              # RSI超卖阈值
    'update_interval': 60            # 更新间隔（秒）
}

# 日志配置
LOGGING_CONFIG = {
    "log_level": "INFO",
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_dir": "logs",
    "log_file": "arbitrage.log",
    "max_file_size": 10485760,  # 10MB
    "backup_count": 5,
    "console_output": True,
    "file_output": True
}

# 数据存储配置
DATA_STORE_CONFIG = {
    "data_dir": "data",
    "price_data_dir": "price_data",
    "trade_data_dir": "trade_data",
    "order_data_dir": "order_data",
    "position_data_dir": "position_data",
    "file_format": "csv",
    "compression": None,
    "backup_enabled": True,
    "backup_interval": 86400,  # 24小时
    "cleanup_enabled": True,
    "max_data_age": 2592000,  # 30天
    "max_storage_size": 10737418240  # 10GB
}

# 策略配置
STRATEGY_CONFIG = {
    # 价差套利策略配置
    'spread_arbitrage': {
        'enabled': True,
        'min_profit_threshold': 0.002,  # 最小利润阈值
        'max_position_size': 10000,     # 最大持仓规模(USDT)
        'trade_amount': 100,            # 每次交易金额(USDT)
        'max_open_orders': 5,           # 最大挂单数量
        'price_decimal': 8,             # 价格小数位数
        'amount_decimal': 4             # 数量小数位数
    },
    
    # 三角套利策略配置
    'triangle_arbitrage': {
        'enabled': False,
        'min_profit_threshold': 0.003,  # 最小利润阈值
        'max_position_size': 10000,     # 最大持仓规模(USDT)
        'trade_amount': 100,            # 每次交易金额(USDT)
        'max_open_orders': 3,           # 最大挂单数量
        'price_decimal': 8,             # 价格小数位数
        'amount_decimal': 4             # 数量小数位数
    }
} 