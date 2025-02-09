"""
日志配置模块
"""
import os

LOGGING_CONFIG = {
    "log_level": "INFO",
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_dir": "logs",
    "log_file": "arbitrage.log",
    "max_file_size": 10485760,  # 10MB
    "backup_count": 5,
    "console_output": True,
    "file_output": True,
    
    # 日志文件路径
    "log_files": {
        "main": "arbitrage.log",
        "error": "error.log",
        "trade": "trade.log",
        "position": "position.log",
        "performance": "performance.log"
    },
    
    # 日志格式
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "simple": {
            "format": "%(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    }
}

# 确保日志目录存在
os.makedirs(LOGGING_CONFIG["log_dir"], exist_ok=True) 