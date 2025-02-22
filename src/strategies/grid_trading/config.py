"""网格交易策略配置

此模块定义了网格交易策略的参数配置和验证规则。
"""

from typing import Dict, Any

# 默认策略配置
DEFAULT_CONFIG = {
    # 交易对设置
    'symbol': 'BTC/USDT',        # 交易对
    'exchange': 'binance',        # 交易所
    
    # 网格参数
    'grid_num': 10,              # 网格数量
    'upper_price': 50000.0,      # 上限价格
    'lower_price': 40000.0,      # 下限价格
    'grid_invest_amount': 1000,   # 每格投资金额(USDT)
    
    # 风控参数
    'max_position': 1.0,         # 最大持仓量(BTC)
    'stop_loss_pct': 0.05,       # 止损百分比
    'take_profit_pct': 0.03,     # 止盈百分比
    
    # 执行参数
    'order_type': 'limit',       # 订单类型：market/limit
    'price_precision': 2,        # 价格精度
    'amount_precision': 6,        # 数量精度
    'min_amount': 0.0001,        # 最小交易量
    'min_notional': 10,          # 最小交易金额
    
    # 其他设置
    'enable_taker': False,       # 是否允许吃单
    'enable_hedge': False,       # 是否启用对冲
    'auto_rebalance': True,      # 是否自动再平衡
}

def validate_config(config: Dict[str, Any]) -> bool:
    """验证策略配置
    
    Args:
        config: 策略配置字典
        
    Returns:
        bool: 配置是否有效
        
    Raises:
        ValueError: 配置验证失败时抛出
    """
    # 验证必需参数
    required_fields = ['symbol', 'exchange', 'grid_num', 'upper_price', 'lower_price']
    for field in required_fields:
        if field not in config:
            raise ValueError(f'缺少必需参数: {field}')
    
    # 验证参数类型和范围
    if not isinstance(config['grid_num'], int) or config['grid_num'] < 2:
        raise ValueError('grid_num必须是大于1的整数')
        
    if config['upper_price'] <= config['lower_price']:
        raise ValueError('upper_price必须大于lower_price')
        
    if config['grid_invest_amount'] <= 0:
        raise ValueError('grid_invest_amount必须大于0')
        
    # 验证精度设置
    if config['price_precision'] < 0 or config['amount_precision'] < 0:
        raise ValueError('精度设置必须大于等于0')
        
    return True

# 导出配置
__all__ = ['DEFAULT_CONFIG', 'validate_config']