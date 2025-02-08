"""
交易所连接基础模块
负责处理与交易所的基础连接功能
"""

import ccxt.async_support as ccxt
import asyncio
from typing import Dict, Any, Optional
from src.Config.exchange_config import EXCHANGE_CONFIGS

class ExchangeConnection:
    """交易所连接基础类"""
    
    def __init__(self, exchange_id: str):
        """
        初始化交易所连接
        :param exchange_id: 交易所ID
        """
        self.exchange_id = exchange_id
        self.config = EXCHANGE_CONFIGS.get(exchange_id, {})
        self.exchange: Optional[ccxt.Exchange] = None
        self.markets = {}
        self.initialized = False
        
    def initialize(self) -> bool:
        """
        初始化交易所连接
        :return: 是否成功
        """
        try:
            if not self.config:
                raise ValueError(f"未找到交易所 {self.exchange_id} 的配置")
                
            # 创建交易所实例
            exchange_class = getattr(ccxt, self.exchange_id)
            self.exchange = exchange_class(self.config)
            
            # 加载市场数据
            self.markets = self.exchange.load_markets()
            self.initialized = True
            
            print(f"成功连接到交易所 {self.exchange_id}")
            return True
            
        except Exception as e:
            print(f"连接交易所 {self.exchange_id} 时发生错误: {str(e)}")
            return False
    
    def check_connection(self) -> bool:
        """
        检查连接状态
        :return: 连接是否正常
        """
        try:
            if not self.initialized:
                return False
            
            # 尝试获取服务器时间来测试连接
            self.exchange.fetch_time()
            return True
            
        except Exception as e:
            print(f"检查交易所 {self.exchange_id} 连接时发生错误: {str(e)}")
            return False
    
    def get_balance(self) -> Dict[str, Any]:
        """
        获取账户余额
        :return: 余额信息
        """
        try:
            if not self.initialized:
                raise ValueError("交易所连接未初始化")
            
            return self.exchange.fetch_balance()
            
        except Exception as e:
            print(f"获取 {self.exchange_id} 余额时发生错误: {str(e)}")
            return {}
    
    def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取市场信息
        :param symbol: 交易对
        :return: 市场信息
        """
        try:
            if not self.initialized:
                raise ValueError("交易所连接未初始化")
            
            return self.markets.get(symbol, {})
            
        except Exception as e:
            print(f"获取 {self.exchange_id} 市场信息时发生错误: {str(e)}")
            return {}
    
    def close(self):
        """关闭连接"""
        try:
            if self.exchange:
                self.exchange.close()
                self.initialized = False
                print(f"已关闭与交易所 {self.exchange_id} 的连接")
        except Exception as e:
            print(f"关闭交易所 {self.exchange_id} 连接时发生错误: {str(e)}") 