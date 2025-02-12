"""
监控配置模块
"""

# 监控配置
MONITOR_CONFIG = {
    "interval_ms": 1000,  # 监控间隔（毫秒）
    "max_queue_size": 1000,  # 最大队列大小
    "error_retry_delay": 5,  # 错误重试延迟（秒）
    "print_price": True,  # 打印价格数据
    "max_reconnect_attempts": 5,  # 最大重连次数
    "reconnect_delay": 5,  # 重连延迟（秒）
    "exponential_backoff": True,  # 指数退避
    "debug_mode": True,  # 调试模式
    "log_websocket_messages": True,  # 记录WebSocket消息
    "log_level": "INFO",  # 日志级别改为INFO以减少日志量
    
    # WebSocket配置
    "websocket": {
        "ping_interval": 30,  # ping间隔（秒）
        "ping_timeout": 10,  # ping超时（秒）
        "close_timeout": 10,  # 关闭超时（秒）
        "heartbeat": True,  # 启用心跳
        "compression": None,  # 压缩方式
    },
    
    # 监控的交易对
    "symbols": [
        "BTC/USDT",
        "ETH/USDT",
        "BNB/USDT"
    ],
    
    # 价格更新阈值（百分比）
    "price_threshold": 0.1,
    
    # 深度监控配置
    "depth": {
        "enabled": False,  # 暂时关闭深度监控以专注于价格
        "levels": 20,
        "update_interval": 1000,
    },
    
    # 成交监控配置
    "trades": {
        "enabled": False,  # 暂时关闭成交监控以专注于价格
        "max_trades": 1000,
        "update_interval": 1000,
    }
}

# 市场结构配置
MARKET_STRUCTURE_CONFIG = {
    "output_dir": "./market_structures",  # 输出目录
    "file_extension": ".json",  # 文件扩展名
    "include_comments": True,  # 是否包含注释
    "indent": 4,  # JSON缩进
    "ensure_ascii": False,  # 允许非ASCII字符
    "update_interval": 3600,  # 市场结构更新间隔(秒)
    "min_volume": 1000,      # 最小交易量(USDT)
    "min_price": 0.00000001,  # 最小价格
    
    # 市场数据存储配置
    "storage": {
        "type": "file",              # 存储类型：file/database
        "compression": True,         # 是否压缩
        "backup_enabled": True,      # 是否启用备份
        "backup_interval": 86400,    # 备份间隔（秒）
        "cleanup_interval": 604800,  # 清理间隔（秒）
        "max_history_days": 30,      # 最大历史天数
    },
    
    # 市场分析配置
    "analysis": {
        "enabled": True,
        "volume_window": 24,         # 成交量分析窗口（小时）
        "volatility_window": 24,     # 波动率分析窗口（小时）
        "correlation_window": 72,    # 相关性分析窗口（小时）
        "update_interval": 3600,     # 分析更新间隔（秒）
    },
    
    # 数据验证配置
    "validation": {
        "enabled": True,
        "price_deviation_threshold": 0.1,  # 价格偏差阈值（10%）
        "volume_deviation_threshold": 0.2,  # 成交量偏差阈值（20%）
        "check_interval": 300,             # 检查间隔（秒）
        "min_data_points": 10,            # 最小数据点数
    }
} 