"""
日志记录器

负责记录:
1. 系统运行日志
2. 交易记录
3. 价格数据
4. 错误信息
"""

import logging
import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler

class ArbitrageLogger:
    """套利系统日志记录器"""
    
    def __init__(self):
        # 创建日志目录
        self._create_directories()
        
        # 配置主日志记录器
        self.logger = logging.getLogger('arbitrage')
        self.logger.setLevel(logging.INFO)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 添加文件处理器
        file_handler = RotatingFileHandler(
            'logs/arbitrage.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
    def _create_directories(self):
        """创建必要的目录"""
        directories = [
            'logs',
            'data',
            'data/price_data',
            'data/trade_data',
            'data/order_data',
            'data/position_data'
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
        
    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
        
    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
        
    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)
        
    def record_trade(self, trade_data: Dict[str, Any]):
        """记录交易数据"""
        try:
            # 添加时间戳
            trade_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 将交易数据写入CSV文件
            trade_file = 'data/trade_data/trades.csv'
            df = pd.DataFrame([trade_data])
            
            if os.path.exists(trade_file):
                df.to_csv(trade_file, mode='a', header=False, index=False)
            else:
                df.to_csv(trade_file, index=False)
                
            # 同时记录到日志
            self.info(f"新交易记录: {json.dumps(trade_data, ensure_ascii=False)}")
            
        except Exception as e:
            self.error(f"记录交易数据时发生错误: {str(e)}")
            
    def record_price(self, symbol: str, exchange: str, price_data: Dict[str, Any], interval: str = "1m"):
        """记录价格数据"""
        try:
            # 添加时间戳和交易所信息
            price_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            price_data['exchange'] = exchange
            
            # 将价格数据写入CSV文件
            price_file = f'data/price_data/{symbol.replace("/", "_")}_{interval}.csv'
            df = pd.DataFrame([price_data])
            
            if os.path.exists(price_file):
                df.to_csv(price_file, mode='a', header=False, index=False)
            else:
                df.to_csv(price_file, index=False)
                
        except Exception as e:
            self.error(f"记录价格数据时发生错误: {str(e)}")
            
    def record_order(self, order_data: Dict[str, Any]):
        """记录订单数据"""
        try:
            # 添加时间戳
            order_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 将订单数据写入CSV文件
            order_file = 'data/order_data/orders.csv'
            df = pd.DataFrame([order_data])
            
            if os.path.exists(order_file):
                df.to_csv(order_file, mode='a', header=False, index=False)
            else:
                df.to_csv(order_file, index=False)
                
            # 同时记录到日志
            self.info(f"新订单记录: {json.dumps(order_data, ensure_ascii=False)}")
            
        except Exception as e:
            self.error(f"记录订单数据时发生错误: {str(e)}")
            
    def record_position(self, position_data: Dict[str, Any]):
        """记录持仓数据"""
        try:
            # 添加时间戳
            position_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 将持仓数据写入CSV文件
            position_file = 'data/position_data/positions.csv'
            df = pd.DataFrame([position_data])
            
            if os.path.exists(position_file):
                df.to_csv(position_file, mode='a', header=False, index=False)
            else:
                df.to_csv(position_file, index=False)
                
        except Exception as e:
            self.error(f"记录持仓数据时发生错误: {str(e)}")
            
    def get_latest_trades(self, limit: int = 100) -> pd.DataFrame:
        """获取最新交易记录"""
        try:
            trade_file = 'data/trade_data/trades.csv'
            if not os.path.exists(trade_file):
                return pd.DataFrame()
            return pd.read_csv(trade_file).tail(limit)
        except Exception as e:
            self.error(f"获取交易记录时发生错误: {str(e)}")
            return pd.DataFrame()
            
    def get_price_history(self, symbol: str, interval: str = "1m", limit: int = 1000) -> pd.DataFrame:
        """获取价格历史数据"""
        try:
            price_file = f'data/price_data/{symbol.replace("/", "_")}_{interval}.csv'
            if not os.path.exists(price_file):
                return pd.DataFrame()
            return pd.read_csv(price_file).tail(limit)
        except Exception as e:
            self.error(f"获取价格历史数据时发生错误: {str(e)}")
            return pd.DataFrame()

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