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
    'USDT'
    # 'USDC'
    # 'USD'
    # 'BTC'
]

# 全局市场类型开关
MARKET_TYPES = {
    'spot'  : True,  # 是否开启现货
    'swap'  : True,  # 是否开启永续合约
    'option': False  # 是否开启期权
}

# 市场结构保存配置
MARKET_STRUCTURE_CONFIG = {
    'include_comments': True,  # 是否在保存的市场结构数据中包含中文注释
    'output_dir': 'market_structures',  # 市场结构数据保存目录
    'indent': 2,  # JSON文件缩进空格数
    'ensure_ascii': False  # 是否确保ASCII编码（设为False以正确显示中文）
}

# 交易所特殊配置
# type_configs: 各交易所不同市场类型的具体配置
EXCHANGE_CONFIGS = {
    'binance': {
        'type_configs': {
            'spot'  : {'type': 'spot'},
            'swap'  : {'type': 'swap'},
            'option': {'type': 'option'}  # binance期权
        }
    },
    'okx'    : {
        'type_configs': {
            'spot'  : {'type': 'spot'},
            'swap'  : {'type': 'swap'},
            'option': {'type': 'option'}  # okx期权
        }
    },
    'bybit'  : {
        'type_configs': {
            'spot'  : {'type': 'spot'},
            'swap'  : {'type': 'swap'},
            'option': {'type': 'options'}  # bybit期权使用'options'
        }
    },
    'huobi'  : {
        'type_configs': {
            'spot'  : {'type': 'spot'},
            'swap'  : {'type': 'swap'},
            'option': {'type': 'option'}  # huobi期权
        }
    },
    'gateio' : {
        'type_configs': {
            'spot'  : {'type': 'spot'},
            'swap'  : {'type': 'swap'},
            'option': {'type': 'delivery'}  # gate.io期权可能使用'delivery'
        }
    }
}
