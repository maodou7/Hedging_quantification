"""
配置模块
包含所有系统配置的集中管理
"""

import logging
import os
from .cache import CACHE_CONFIG
from .exchange import (
    EXCHANGES,
    EXCHANGE_CONFIGS,
    MARKET_TYPES,
    QUOTE_CURRENCIES,
    COMMON_SYMBOLS,
    SYMBOLS,
    DEFAULT_FEES
)
from .monitoring import MONITOR_CONFIG, MARKET_STRUCTURE_CONFIG
from .risk import RISK_CONFIG
from .trading import ARBITRAGE_CONFIG, STRATEGY_CONFIG, INDICATOR_CONFIG
from .database import DATABASE_CONFIG
from .notification import NOTIFICATION_CONFIG
from .validator import validate_all_configs, ConfigError
from .migration import config_migration
from .reload import config_reload
from .log_config import LOGGING_CONFIG

# 确保日志目录存在
os.makedirs(LOGGING_CONFIG["log_dir"], exist_ok=True)

# 配置日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(LOGGING_CONFIG["log_level"])

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(LOGGING_CONFIG["log_level"])
console_formatter = logging.Formatter(LOGGING_CONFIG["formatters"]["default"]["format"],
                                   LOGGING_CONFIG["formatters"]["default"]["datefmt"])
console_handler.setFormatter(console_formatter)

# 创建文件处理器
# 使用默认的info日志文件路径
file_handler = logging.FileHandler(f"{LOGGING_CONFIG['log_dir']}/{LOGGING_CONFIG['log_files']['info']}")
file_handler.setLevel(LOGGING_CONFIG["log_level"])
file_formatter = logging.Formatter(LOGGING_CONFIG["formatters"]["detailed"]["format"],
                                LOGGING_CONFIG["formatters"]["detailed"]["datefmt"])
file_handler.setFormatter(file_formatter)

# 添加处理器到日志记录器
if LOGGING_CONFIG["console_output"]:
    logger.addHandler(console_handler)
if LOGGING_CONFIG["file_output"]:
    logger.addHandler(file_handler)

__all__ = [
    'CACHE_CONFIG',
    'EXCHANGES',
    'EXCHANGE_CONFIGS',
    'MARKET_TYPES',
    'QUOTE_CURRENCIES',
    'COMMON_SYMBOLS',
    'SYMBOLS',
    'DEFAULT_FEES',
    'MONITOR_CONFIG',
    'MARKET_STRUCTURE_CONFIG',
    'RISK_CONFIG',
    'ARBITRAGE_CONFIG',
    'STRATEGY_CONFIG',
    'INDICATOR_CONFIG',
    'LOGGING_CONFIG',
    'DATABASE_CONFIG',
    'NOTIFICATION_CONFIG',
    'validate_all_configs',
    'ConfigError',
    'config_migration',
    'config_reload'
]

def init_config():
    """初始化配置系统"""
    try:
        # 验证配置前确保交易所配置正确
        from .exchange import EXCHANGE_CONFIGS
        if not isinstance(EXCHANGE_CONFIGS, dict) or any(not isinstance(v, dict) for v in EXCHANGE_CONFIGS.values()):
            raise ConfigError("交易所配置格式错误，必须为字典类型")

        # 验证配置
        validation_result = validate_all_configs()
        if not validation_result.is_valid:
            error_msg = "\n".join(validation_result.errors)
            raise ConfigError(f"配置验证失败:\n{error_msg}")
        
        # 打印警告信息
        if validation_result.warnings:
            warning_msg = "\n".join(validation_result.warnings)
            logger.warning(f"配置警告:\n{warning_msg}")
        
        # 执行待处理的配置迁移
        for config_name in ["trading", "risk", "monitoring", "database", "notification"]:
            pending_migrations = config_migration.get_pending_migrations(config_name)
            if pending_migrations:
                logger.info(f"发现{config_name}的待处理迁移: {len(pending_migrations)}个")
                config_migration.migrate(config_name)
        
        # 启动配置热重载
        config_reload.start()
        
        logger.info("配置系统初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"配置系统初始化失败: {e}")
        return False

def reload_config():
    """重新加载所有配置"""
    try:
        config_reload.reload_all()
        logger.info("所有配置已重新加载")
        return True
    except Exception as e:
        logger.error(f"重新加载配置失败: {e}")
        return False

# 在导入时初始化配置系统
init_config()
