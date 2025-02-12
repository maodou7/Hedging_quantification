"""
日志配置模块
"""
import os
import logging

LOGGING_CONFIG = {
    "log_level": "DEBUG",
    "log_format": "%(asctime)s.%(msecs)03d - %(process)d:%(thread)d - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    "log_dir": "logs",
    "max_file_size": 10485760,  # 10MB
    "backup_count": 10,
    "console_output": True,
    "file_output": True,
    "async_logging": True,
    "batch_size": 100,
    "batch_interval": 1.0,
    "log_rate_limit": 5,  # 秒
    "module_levels": {
        "exchange": "DEBUG",
        "config": "DEBUG",
        "ccxt": "INFO",
        "aiohttp": "WARNING"
    },
    
    # 日志文件路径（按级别分离）
    "log_files": {
        "debug": "debug.log",
        "info": "info.log",
        "warning": "warning.log",
        "error": "error.log",
        "critical": "critical.log"
    },
    
    # 日志处理器配置
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
            "level": "INFO"
        },
        "file": {
            "class": "concurrent_log_handler.ConcurrentRotatingFileHandler",
            "formatter": "detailed",
            "level": "DEBUG",
            "encoding": "utf8"
        }
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
            "format": "%(asctime)s.%(msecs)03d - %(process)d:%(thread)d - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "verbose": {
            "format": "%(asctime)s.%(msecs)03d - %(process)d:%(thread)d - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(module)s.%(funcName)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    }
}

# 日志过滤器配置
class ModuleFilter:
    def __init__(self, module_name, level):
        self.module_name = module_name
        self.level = level

    def filter(self, record):
        if record.name.startswith(self.module_name):
            return record.levelno >= getattr(logging, self.level)
        return True

# 应用模块级别日志配置
for module, level in LOGGING_CONFIG["module_levels"].items():
    logging.getLogger(module).setLevel(level)

# 确保日志目录存在
os.makedirs(LOGGING_CONFIG["log_dir"], exist_ok=True)
