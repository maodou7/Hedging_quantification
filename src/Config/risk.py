"""
风险管理配置模块
"""

RISK_CONFIG = {
    # 基本风险参数
    'max_position_value': 10000,  # 最大持仓价值（USDT）
    'max_drawdown': 0.1,         # 最大回撤（10%）
    
    # 风险限制
    'limits': {
        'daily_loss_limit': 1000,   # 每日最大亏损（USDT）
        'position_limit': 5,         # 最大持仓数量
        'leverage_limit': 3,         # 最大杠杆倍数
        'concentration_limit': 0.3   # 单个资产最大集中度（30%）
    },
    
    # 风险预警配置
    'risk_alerts': {
        'enabled': True,
        'email_alerts': True,        # 是否发送邮件警报
        'telegram_alerts': False,    # 是否发送Telegram警报
        'alert_levels': {
            'critical': {
                'loss_threshold': -0.05,     # 亏损阈值（5%）
                'exposure_threshold': 0.8,    # 敞口阈值（80%）
                'margin_threshold': 0.2       # 保证金阈值（20%）
            },
            'warning': {
                'loss_threshold': -0.03,     # 亏损阈值（3%）
                'exposure_threshold': 0.6,    # 敞口阈值（60%）
                'margin_threshold': 0.4       # 保证金阈值（40%）
            },
            'info': {
                'loss_threshold': -0.01,     # 亏损阈值（1%）
                'exposure_threshold': 0.4,    # 敞口阈值（40%）
                'margin_threshold': 0.6       # 保证金阈值（60%）
            }
        }
    },
    
    # 风险分析配置
    'risk_analysis': {
        'enabled': True,
        'var_confidence_level': 0.95,    # VaR置信水平
        'var_time_horizon': 1,           # VaR时间范围（天）
        'stress_test_scenarios': {
            'market_crash': -0.2,        # 市场崩溃（-20%）
            'high_volatility': 0.05,     # 高波动性（5%）
            'liquidity_crisis': 0.1      # 流动性危机（10%）
        },
        'correlation_window': 30,        # 相关性分析窗口（天）
        'update_interval': 3600          # 更新间隔（秒）
    },
    
    # 止损配置
    'stop_loss': {
        'enabled': True,
        'trailing': True,               # 是否启用追踪止损
        'threshold': -0.02,             # 止损阈值（-2%）
        'trailing_distance': 0.01,      # 追踪止损距离（1%）
        'min_profit_threshold': 0.005   # 最小利润阈值（0.5%）
    },
    
    # 仓位管理配置
    'position_management': {
        'enabled': True,
        'auto_reduce': True,            # 是否自动减仓
        'max_positions': 10,            # 最大持仓数量
        'position_sizing': {
            'method': 'fixed_risk',     # 仓位计算方法
            'risk_per_trade': 0.01,     # 每笔交易风险（1%）
            'kelly_fraction': 0.5       # 凯利系数
        }
    }
} 