"""
数据库配置模块
"""
import os

DATABASE_CONFIG = {
    # 主数据库配置（PostgreSQL）
    "main": {
        "enabled": True,
        "type": "postgresql",
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "crypto_arbitrage"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "echo": False
    },
    
    # 时序数据库配置（InfluxDB）
    "timeseries": {
        "enabled": True,
        "type": "influxdb",
        "url": os.getenv("INFLUXDB_URL", "http://localhost:8086"),
        "token": os.getenv("INFLUXDB_TOKEN", ""),
        "org": os.getenv("INFLUXDB_ORG", "crypto_arbitrage"),
        "bucket": os.getenv("INFLUXDB_BUCKET", "market_data"),
        "batch_size": 5000,
        "flush_interval": 10000,  # 毫秒
        "retention_policy": {
            "name": "market_data_retention",
            "duration": "30d",
            "replication": 1
        }
    },
    
    # 缓存数据库配置（Redis）
    "cache": {
        "enabled": True,
        "type": "redis",
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "password": os.getenv("REDIS_PASSWORD", ""),
        "db": int(os.getenv("REDIS_DB", "0")),
        "decode_responses": True,
        "socket_timeout": 5,
        "socket_connect_timeout": 5,
        "max_connections": 100,
        "retry_on_timeout": True
    },
    
    # 消息队列配置（Redis Pub/Sub）
    "message_queue": {
        "enabled": True,
        "type": "redis",
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "password": os.getenv("REDIS_PASSWORD", ""),
        "db": int(os.getenv("REDIS_DB", "1")),
        "channels": {
            "market_data": "market_data",
            "trade_signals": "trade_signals",
            "system_events": "system_events",
            "alerts": "alerts"
        }
    },
    
    # 数据备份配置
    "backup": {
        "enabled": True,
        "type": "file",
        "path": "./backups",
        "interval": 86400,  # 24小时
        "keep_days": 7,
        "compress": True,
        "tables": [
            "trades",
            "orders",
            "positions",
            "balance_history",
            "system_events"
        ]
    },
    
    # 数据迁移配置
    "migration": {
        "enabled": True,
        "auto_migrate": True,
        "version_table": "schema_version",
        "scripts_path": "./migrations",
        "baseline_version": "001"
    },
    
    # 监控配置
    "monitoring": {
        "enabled": True,
        "slow_query_threshold": 1.0,  # 秒
        "connection_threshold": 80,    # 最大连接数的百分比
        "log_queries": False,
        "metrics_enabled": True,
        "metrics_interval": 60         # 秒
    }
} 