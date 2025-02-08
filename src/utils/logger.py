"""
日志工具类

提供统一的日志记录功能
"""

import logging
import os
from datetime import datetime
from src.Config.exchange_config import LOGGING_CONFIG

class ArbitrageLogger:
    def __init__(self):
        # 创建日志目录
        log_dir = LOGGING_CONFIG['log_dir']
        os.makedirs(log_dir, exist_ok=True)
        
        # 设置日志文件路径
        log_file = os.path.join(log_dir, LOGGING_CONFIG['log_file'])
        
        # 创建日志记录器
        self.logger = logging.getLogger('arbitrage')
        self.logger.setLevel(getattr(logging, LOGGING_CONFIG['log_level']))
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, LOGGING_CONFIG['log_level']))
        file_handler.setFormatter(logging.Formatter(LOGGING_CONFIG['log_format']))
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LOGGING_CONFIG['log_level']))
        console_handler.setFormatter(logging.Formatter(LOGGING_CONFIG['log_format']))
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def info(self, message: str):
        """记录信息级别的日志"""
        self.logger.info(message)
        
    def warning(self, message: str):
        """记录警告级别的日志"""
        self.logger.warning(message)
        
    def error(self, message: str):
        """记录错误级别的日志"""
        self.logger.error(message)
        
    def debug(self, message: str):
        """记录调试级别的日志"""
        self.logger.debug(message)
        
    def critical(self, message: str):
        """记录严重错误级别的日志"""
        self.logger.critical(message)

    def log_market_data(self, exchange: str, symbol: str, bid: float, ask: float):
        """记录市场数据"""
        self.logger.info(
            f"市场数据 - 交易所: {exchange}, 交易对: {symbol}, "
            f"买一价: {bid:.8f}, 卖一价: {ask:.8f}"
        )
        
    def log_arbitrage_opportunity(self, buy_exchange: str, sell_exchange: str,
                                symbol: str, profit: float, amount: float):
        """记录套利机会"""
        self.logger.info(
            f"套利机会 - 买入交易所: {buy_exchange}, 卖出交易所: {sell_exchange}, "
            f"交易对: {symbol}, 数量: {amount:.8f}, 预期利润: {profit:.8f}"
        )
        
    def log_trade_execution(self, exchange: str, symbol: str, side: str,
                          amount: float, price: float, status: str):
        """记录交易执行"""
        self.logger.info(
            f"交易执行 - 交易所: {exchange}, 交易对: {symbol}, "
            f"方向: {side}, 数量: {amount:.8f}, "
            f"价格: {price:.8f}, 状态: {status}"
        )
        
    def log_error(self, error_type: str, error_msg: str):
        """记录错误信息"""
        self.logger.error(f"错误 - 类型: {error_type}, 信息: {error_msg}")
        
    def log_risk_check(self, check_type: str, result: bool, reason: str = None):
        """记录风险检查结果"""
        status = "通过" if result else "未通过"
        message = f"风险检查 - 类型: {check_type}, 结果: {status}"
        if reason:
            message += f", 原因: {reason}"
        self.logger.info(message)
        
    def log_daily_summary(self, total_trades: int, total_profit: float,
                         success_rate: float):
        """记录每日总结"""
        self.logger.info(
            f"每日总结 - 总交易次数: {total_trades}, "
            f"总收益: {total_profit:.8f}, 成功率: {success_rate:.2%}"
        ) 