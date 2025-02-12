"""
启动配置管理模块
管理不同环境和系统下的启动参数
"""
import os
from typing import Dict, Any

# 启动模式配置
STARTUP_CONFIG = {
    # 运行环境配置
    "environment": {
        "development": {
            "description": "开发环境",
            "server": "uvicorn",
            "reload": True,
            "debug": True,
            "log_level": "debug",
        },
        "testing": {
            "description": "测试环境",
            "server": "uvicorn",
            "reload": False,
            "debug": True,
            "log_level": "info",
        },
        "production": {
            "description": "生产环境",
            "server": "gunicorn",
            "reload": False,
            "debug": False,
            "log_level": "warning",
        }
    },

    # 系统特定配置
    "system": {
        "linux": {
            "worker_class": "uvicorn.workers.UvicornWorker",
            "worker_tmp_dir": "/dev/shm",
            "max_requests": 1000,
            "max_requests_jitter": 50,
            "preload_app": True,
            "fd_limit": 65535,
            "use_systemd": True,
        },
        "windows": {
            "worker_class": "uvicorn.workers.UvicornWorker",
            "worker_tmp_dir": None,
            "max_requests": 0,
            "max_requests_jitter": 0,
            "preload_app": False,
            "fd_limit": None,
            "use_systemd": False,
        }
    },

    # 资源限制配置
    "resources": {
        "min_workers": 2,
        "max_workers": 8,
        "memory_per_worker": 0.5,  # GB
        "cpu_multiplier": 2,
        "timeout": 300,
        "graceful_timeout": 60,
    },

    # 日志配置
    "logging": {
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S",
        "file_logging": {
            "enabled": True,
            "path": "logs",
            "max_size": 100 * 1024 * 1024,  # 100MB
            "backup_count": 10,
        }
    },

    # 监控配置
    "monitoring": {
        "enabled": True,
        "prometheus": True,
        "statsd": False,
        "metrics_path": "/metrics",
    },

    # 服务管理配置
    "service": {
        "name": "crypto-arbitrage",
        "description": "Crypto Arbitrage Trading System",
        "user": "root",
        "group": "root",
        "restart": "always",
        "restart_sec": 3,
    }
}

def get_startup_config() -> Dict[str, Any]:
    """获取当前环境的启动配置"""
    env = os.getenv("ENV", "development")
    return {
        "environment": STARTUP_CONFIG["environment"][env],
        "system": STARTUP_CONFIG["system"],
        "resources": STARTUP_CONFIG["resources"],
        "logging": STARTUP_CONFIG["logging"],
        "monitoring": STARTUP_CONFIG["monitoring"],
        "service": STARTUP_CONFIG["service"],
    } 