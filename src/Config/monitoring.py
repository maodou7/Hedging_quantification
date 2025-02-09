"""
监控配置模块
"""

MONITOR_CONFIG = {
    "mode": "realtime",  # 监控模式: "realtime" 或 "ratelimited"
    "interval_ms": 100,  # 限流模式下的更新间隔（毫秒）
    "max_queue_size": 1000,  # 本地缓存队列大小
    "print_price": True,  # 是否打印价格数据
    "error_retry_delay": 1,  # 错误重试延迟（秒）
    "update_interval": 0.5,  # 数据更新间隔（秒）
    "health_check_interval": 30.0,  # 健康检查间隔（秒）
    "retry_interval": 3.0,  # 重试间隔（秒）
    "max_retries": 3,  # 最大重试次数
    "timeout": 5,  # 超时时间（秒）
    "log_level": "INFO",  # 日志级别
    
    # 价格监控配置
    "price_monitor": {
        "depth_level": 20,           # 订单簿深度
        "snapshot_interval": 1,       # 快照间隔（秒）
        "websocket_enabled": True,    # 是否启用WebSocket
        "rest_fallback": True,        # WebSocket断开时是否使用REST API
        "cache_ttl": 60,             # 缓存过期时间（秒）
        "alert_threshold": 0.01,      # 价格波动报警阈值（1%）
        "max_price_deviation": 0.05,  # 最大价格偏差（5%）
        "min_update_interval": 0.1,   # 最小更新间隔（秒）
    },
    
    # 系统监控配置
    "system_monitor": {
        "enabled": True,
        "cpu_threshold": 80,         # CPU使用率阈值（%）
        "memory_threshold": 80,      # 内存使用率阈值（%）
        "disk_threshold": 90,        # 磁盘使用率阈值（%）
        "network_threshold": 1000,   # 网络带宽阈值（Mbps）
        "check_interval": 60,        # 检查间隔（秒）
        "alert_interval": 300,       # 报警间隔（秒）
    },
    
    # 性能监控配置
    "performance_monitor": {
        "enabled": True,
        "latency_threshold": 1000,   # 延迟阈值（毫秒）
        "throughput_threshold": 100,  # 吞吐量阈值（每秒请求数）
        "error_rate_threshold": 0.01, # 错误率阈值（1%）
        "sample_interval": 60,        # 采样间隔（秒）
        "history_size": 1000,         # 历史记录大小
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