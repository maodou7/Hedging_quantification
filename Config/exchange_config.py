# 配置要监控的交易所（例如：binance、okx、bybit、huobi、gateio）
EXCHANGES = [
    'binance',
    'okx',
    'bybit',
    'huobi',
    'gateio'
]

# 要监控的计价币种（例如：ETH/USDT、ETH/BTC、ETH/USDC、ETH/USD）
QUOTE_CURRENCIES = [
    'USDT',
    'BUSD',
    'USDC'
    # 'USD'
    # 'BTC'
]

# 全局市场类型开关
MARKET_TYPES = {
    'spot': True,      # 现货市场
    'swap': True,      # 永续合约
    'future': False,   # 交割合约
    'margin': False    # 杠杆交易
}

# 市场结构保存配置
MARKET_STRUCTURE_CONFIG = {
    'min_volume_24h': 1000000,  # 最小24小时成交量
    'min_price': 0.00000001,    # 最小价格
    'max_price': 1000000        # 最大价格
}

# 交易所特殊配置
# type_configs: 各交易所不同市场类型的具体配置
EXCHANGE_CONFIGS = {
    'binance': {
        'has_ws': True,
        'rate_limit': True,
        'timeout': 30000,
        'quote_currencies': QUOTE_CURRENCIES,
        'market_types': MARKET_TYPES
    },
    'okx': {
        'has_ws': True,
        'rate_limit': True,
        'timeout': 30000,
        'quote_currencies': QUOTE_CURRENCIES,
        'market_types': MARKET_TYPES
    },
    'bybit': {
        'has_ws': True,
        'rate_limit': True,
        'timeout': 30000,
        'quote_currencies': QUOTE_CURRENCIES,
        'market_types': MARKET_TYPES
    },
    'huobi': {
        'has_ws': True,
        'rate_limit': True,
        'timeout': 30000,
        'quote_currencies': QUOTE_CURRENCIES,
        'market_types': MARKET_TYPES
    },
    'gateio': {
        'has_ws': True,
        'rate_limit': True,
        'timeout': 30000,
        'quote_currencies': QUOTE_CURRENCIES,
        'market_types': MARKET_TYPES
    }
}
