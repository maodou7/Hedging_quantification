from decimal import Decimal
from typing import Dict

# 默认配置
DEFAULT_CONFIG = {
    'symbol': 'BTC/USDT',  # 交易对
    'spot_exchange': 'binance',  # 现货交易所
    'futures_exchange': 'binance_futures',  # 期货交易所
    'min_basis_rate': 0.001,  # 最小基差率
    'trade_amount': 1000,  # 单次交易金额
    'max_slippage': 0.0005,  # 最大滑点
    'max_position': 10000,  # 最大持仓量
    'max_order_count': 5,  # 最大订单数量
    'stop_loss_rate': 0.01  # 止损率
}

def validate_config(config: Dict) -> bool:
    """验证策略配置
    
    Args:
        config: 策略配置字典
        
    Returns:
        bool: 配置是否有效
        
    Raises:
        ValueError: 配置无效时抛出异常
    """
    required_fields = [
        'symbol',
        'spot_exchange',
        'futures_exchange',
        'min_basis_rate',
        'trade_amount'
    ]
    
    # 检查必需字段
    for field in required_fields:
        if field not in config:
            raise ValueError(f'缺少必需配置项: {field}')
    
    # 验证交易所
    if config['spot_exchange'] == config['futures_exchange']:
        raise ValueError('现货交易所和期货交易所不能相同')
    
    # 验证数值范围
    if Decimal(str(config['min_basis_rate'])) <= 0:
        raise ValueError('最小基差率必须大于0')
    
    if Decimal(str(config['trade_amount'])) <= 0:
        raise ValueError('交易金额必须大于0')
    
    if 'max_slippage' in config and Decimal(str(config['max_slippage'])) < 0:
        raise ValueError('最大滑点不能为负数')
    
    if 'max_position' in config and Decimal(str(config['max_position'])) <= 0:
        raise ValueError('最大持仓量必须大于0')
    
    if 'max_order_count' in config and int(config['max_order_count']) <= 0:
        raise ValueError('最大订单数量必须大于0')
    
    if 'stop_loss_rate' in config and Decimal(str(config['stop_loss_rate'])) <= 0:
        raise ValueError('止损率必须大于0')
    
    return True