"""
配置验证模块
负责验证各个配置项的有效性
"""
from typing import Dict, Any, List, Optional
from enum import Enum
import re
import os
from dataclasses import dataclass

class ConfigError(Exception):
    """配置错误异常"""
    pass

@dataclass
class ValidatorResult:
    """验证结果"""
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def add_error(self, error: str):
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)
    
    def merge(self, other: 'ValidatorResult'):
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def is_dev_mode() -> bool:
        """判断是否为开发环境"""
        return os.getenv("ENV", "development").lower() == "development"
    
    @staticmethod
    def validate_cache_config(config: Dict) -> ValidatorResult:
        """验证缓存配置"""
        result = ValidatorResult()
        
        # 验证Redis配置
        if config.get("strategy") == "redis":
            redis_config = config.get("redis", {})
            if not redis_config.get("host"):
                result.add_error("Redis host不能为空")
            if not isinstance(redis_config.get("port"), int):
                result.add_error("Redis port必须是整数")
            if redis_config.get("port") < 1 or redis_config.get("port") > 65535:
                result.add_error("Redis port必须在1-65535之间")
            if redis_config.get("socket_timeout", 0) < 1:
                result.add_warning("Redis socket_timeout过小可能导致连接不稳定")
        
        # 验证本地缓存配置
        if config.get("strategy") == "local":
            local_config = config.get("local", {})
            if not local_config.get("output_dir"):
                result.add_error("本地缓存输出目录不能为空")
            if not os.path.exists(local_config.get("output_dir", "")):
                result.add_warning("本地缓存输出目录不存在，将自动创建")
        
        return result
    
    @staticmethod
    def validate_database_config(config: Dict) -> ValidatorResult:
        """验证数据库配置"""
        result = ValidatorResult()
        is_dev = ConfigValidator.is_dev_mode()
        
        # 验证PostgreSQL配置
        if config.get("main", {}).get("enabled", False):
            main_db = config["main"]
            if not main_db.get("database") and not is_dev:
                result.add_warning("主数据库名称未配置")
            if main_db.get("pool_size", 0) < 5:
                result.add_warning("数据库连接池大小过小可能影响性能")
            if main_db.get("pool_size", 0) > 100:
                result.add_warning("数据库连接池大小过大可能消耗过多资源")
        
        # 验证InfluxDB配置
        if config.get("timeseries", {}).get("enabled", False):
            ts_db = config["timeseries"]
            if not ts_db.get("token") and not is_dev:
                result.add_warning("InfluxDB token未配置")
            if not ts_db.get("bucket") and not is_dev:
                result.add_warning("InfluxDB bucket未配置")
            if ts_db.get("batch_size", 0) > 10000:
                result.add_warning("InfluxDB批处理大小过大可能导致内存压力")
        
        # 验证Redis配置
        if config.get("cache", {}).get("enabled", False):
            cache_db = config.get("cache", {})
            if cache_db.get("max_connections", 0) < 10:
                result.add_warning("Redis最大连接数过小可能影响性能")
        
        # 验证备份配置
        if config.get("backup", {}).get("enabled", False):
            backup = config.get("backup", {})
            if backup.get("interval", 0) < 3600:
                result.add_warning("备份间隔小于1小时可能影响系统性能")
            if not os.path.exists(backup.get("path", "")):
                result.add_warning("备份目录不存在，将自动创建")
        
        return result
    
    @staticmethod
    def validate_notification_config(config: Dict) -> ValidatorResult:
        """验证通知配置"""
        result = ValidatorResult()
        is_dev = ConfigValidator.is_dev_mode()
        
        # 验证邮件配置
        if config.get("email", {}).get("enabled", False):
            email_config = config["email"]
            if not is_dev:
                if not email_config.get("smtp_host"):
                    result.add_warning("SMTP主机未配置")
                if not email_config.get("smtp_user") or not email_config.get("smtp_password"):
                    result.add_warning("SMTP用户名和密码未配置")
                if not email_config.get("notification_email"):
                    result.add_warning("通知邮箱未配置")
        
        # 验证Telegram配置
        if config.get("telegram", {}).get("enabled", False):
            telegram_config = config["telegram"]
            if not is_dev:
                if not telegram_config.get("bot_token"):
                    result.add_warning("Telegram bot token未配置")
                if not telegram_config.get("chat_id"):
                    result.add_warning("Telegram chat ID未配置")
        
        # 验证通知级别配置
        for level, level_config in config["levels"].items():
            if level_config.get("retry_count", 0) > 5:
                result.add_warning(f"{level}级别的重试次数过多可能导致消息延迟")
        
        # 验证通知聚合配置
        if config.get("aggregation", {}).get("enabled"):
            agg = config["aggregation"]
            if agg.get("window_size", 0) < 60:
                result.add_warning("聚合窗口小于1分钟可能导致消息过于频繁")
            if agg.get("max_events", 0) > 50:
                result.add_warning("单个窗口最大事件数过大可能导致消息太长")
        
        return result
    
    @staticmethod
    def validate_exchange_config(config: Dict) -> ValidatorResult:
        """验证交易所配置"""
        result = ValidatorResult()
        is_dev = ConfigValidator.is_dev_mode()
        
        # 验证交易所列表
        if not config.get("EXCHANGES"):
            result.add_error("交易所列表不能为空")
        
        # 验证交易对配置
        symbols = config.get("SYMBOLS", {})
        for market_type, symbol_list in symbols.items():
            if not isinstance(symbol_list, list):
                result.add_error(f"{market_type}的交易对列表必须是数组")
            for symbol in symbol_list:
                if not re.match(r'^[A-Z0-9]+/[A-Z0-9]+(?::[A-Z0-9]+)?$', symbol):
                    result.add_error(f"无效的交易对格式: {symbol}")
        
        # 验证市场类型
        market_types = config.get("MARKET_TYPES", {})
        if not any(market_types.values()):
            result.add_error("至少需要启用一种市场类型")
        
        # 验证交易所配置
        for exchange_id, exchange_config in config.get("EXCHANGE_CONFIGS", {}).items():
            if not is_dev:
                if not exchange_config.get("apiKey"):
                    result.add_warning(f"{exchange_id}未配置API密钥")
                if exchange_config.get("test", False):
                    result.add_warning(f"{exchange_id}正在使用测试模式")
        
        return result
    
    @staticmethod
    def validate_risk_config(config: Dict) -> ValidatorResult:
        """验证风险管理配置"""
        result = ValidatorResult()
        
        # 验证基本参数
        if config.get("max_position_value", 0) <= 0:
            result.add_error("最大持仓价值必须大于0")
        if config.get("max_drawdown", 0) <= 0:
            result.add_error("最大回撤必须大于0")
        
        # 验证风险限制
        limits = config.get("limits", {})
        if limits.get("daily_loss_limit", 0) <= 0:
            result.add_error("每日亏损限制必须大于0")
        if limits.get("position_limit", 0) <= 0:
            result.add_error("持仓限制必须大于0")
        
        # 验证风险预警
        alerts = config.get("risk_alerts", {})
        if alerts.get("enabled"):
            critical = alerts.get("alert_levels", {}).get("critical", {})
            if critical.get("loss_threshold", 0) >= 0:
                result.add_error("严重亏损阈值必须小于0")
            if critical.get("exposure_threshold", 0) <= 0:
                result.add_error("严重敞口阈值必须大于0")
        
        # 验证风险分析
        analysis = config.get("risk_analysis", {})
        if analysis.get("enabled"):
            if analysis.get("var_confidence_level", 0) < 0.9:
                result.add_warning("VaR置信水平过低可能无法有效评估风险")
            if analysis.get("stress_test_scenarios", {}).get("market_crash", 0) > -0.1:
                result.add_warning("市场崩溃情景的跌幅过小，可能无法充分测试极端情况")
        
        return result
    
    @staticmethod
    def validate_monitor_config(config: Dict) -> ValidatorResult:
        """验证监控配置"""
        result = ValidatorResult()
        
        # 验证基本参数
        if config.get("interval_ms", 0) < 100:
            result.add_warning("更新间隔小于100ms可能导致性能问题")
        if config.get("max_queue_size", 0) < 100:
            result.add_warning("队列大小过小可能导致数据丢失")
        
        # 验证价格监控配置
        price_monitor = config.get("price_monitor", {})
        if price_monitor.get("depth_level", 0) > 50:
            result.add_warning("订单簿深度过大可能影响性能")
        if price_monitor.get("snapshot_interval", 0) < 0.5:
            result.add_warning("快照间隔过小可能导致数据冗余")
        
        # 验证系统监控配置
        sys_monitor = config.get("system_monitor", {})
        if sys_monitor.get("enabled"):
            if sys_monitor.get("cpu_threshold", 0) > 90:
                result.add_warning("CPU阈值过高可能导致系统不稳定")
            if sys_monitor.get("memory_threshold", 0) > 90:
                result.add_warning("内存阈值过高可能导致系统不稳定")
            if sys_monitor.get("check_interval", 0) < 10:
                result.add_warning("系统检查间隔过小可能影响性能")
        
        # 验证性能监控配置
        perf_monitor = config.get("performance_monitor", {})
        if perf_monitor.get("enabled"):
            if perf_monitor.get("sample_interval", 0) < 30:
                result.add_warning("性能采样间隔过小可能影响系统性能")
            if perf_monitor.get("history_size", 0) > 10000:
                result.add_warning("历史记录大小过大可能占用过多内存")
        
        return result
    
    @staticmethod
    def validate_trading_config(config: Dict) -> ValidatorResult:
        """验证交易配置"""
        result = ValidatorResult()
        
        # 验证套利配置
        arb_config = config.get("ARBITRAGE_CONFIG", {})
        if arb_config.get("min_profit_usdt", 0) <= 0:
            result.add_error("最小利润必须大于0")
        if arb_config.get("max_slippage_percent", 0) <= 0:
            result.add_error("最大滑点必须大于0")
        if arb_config.get("order_book_depth", 0) > 50:
            result.add_warning("订单簿深度过大可能影响性能")
        
        # 验证策略配置
        strategy_config = config.get("STRATEGY_CONFIG", {})
        for strategy_name, strategy in strategy_config.items():
            if strategy.get("enabled"):
                if strategy.get("min_profit_threshold", 0) <= 0:
                    result.add_error(f"{strategy_name}的最小利润阈值必须大于0")
                if strategy.get("max_position_size", 0) <= 0:
                    result.add_error(f"{strategy_name}的最大持仓规模必须大于0")
                if strategy.get("update_interval", 0) < 1:
                    result.add_warning(f"{strategy_name}的更新间隔过小可能影响性能")
        
        return result

def validate_all_configs() -> ValidatorResult:
    """验证所有配置"""
    from . import (
        CACHE_CONFIG,
        EXCHANGES,
        EXCHANGE_CONFIGS,
        MARKET_TYPES,
        SYMBOLS,
        MONITOR_CONFIG,
        RISK_CONFIG,
        ARBITRAGE_CONFIG,
        STRATEGY_CONFIG,
        DATABASE_CONFIG,
        NOTIFICATION_CONFIG
    )
    
    result = ValidatorResult()
    
    # 验证缓存配置
    result.merge(ConfigValidator.validate_cache_config(CACHE_CONFIG))
    
    # 验证交易所配置
    result.merge(ConfigValidator.validate_exchange_config({
        "EXCHANGES": EXCHANGES,
        "EXCHANGE_CONFIGS": EXCHANGE_CONFIGS,
        "MARKET_TYPES": MARKET_TYPES,
        "SYMBOLS": SYMBOLS
    }))
    
    # 验证风险配置
    result.merge(ConfigValidator.validate_risk_config(RISK_CONFIG))
    
    # 验证监控配置
    result.merge(ConfigValidator.validate_monitor_config(MONITOR_CONFIG))
    
    # 验证交易配置
    result.merge(ConfigValidator.validate_trading_config({
        "ARBITRAGE_CONFIG": ARBITRAGE_CONFIG,
        "STRATEGY_CONFIG": STRATEGY_CONFIG
    }))
    
    # 验证数据库配置
    result.merge(ConfigValidator.validate_database_config(DATABASE_CONFIG))
    
    # 验证通知配置
    result.merge(ConfigValidator.validate_notification_config(NOTIFICATION_CONFIG))
    
    return result 