"""
交易所连接管理器
负责管理多个交易所的连接
"""

from typing import Dict, List, Optional
from src.exchange.exchange_connection import ExchangeConnection
from src.Config.exchange_config import EXCHANGES

class ConnectionManager:
    """交易所连接管理器"""
    
    def __init__(self):
        """初始化连接管理器"""
        self.connections: Dict[str, ExchangeConnection] = {}
        
    def initialize_all(self) -> Dict[str, bool]:
        """
        初始化所有交易所连接
        :return: 各交易所初始化结果
        """
        results = {}
        for exchange_id in EXCHANGES:
            results[exchange_id] = self.initialize_exchange(exchange_id)
        return results
    
    def initialize_exchange(self, exchange_id: str) -> bool:
        """
        初始化单个交易所连接
        :param exchange_id: 交易所ID
        :return: 是否成功
        """
        try:
            connection = ExchangeConnection(exchange_id)
            if connection.initialize():
                self.connections[exchange_id] = connection
                return True
            return False
        except Exception as e:
            print(f"初始化交易所 {exchange_id} 时发生错误: {str(e)}")
            return False
    
    def get_connection(self, exchange_id: str) -> Optional[ExchangeConnection]:
        """
        获取交易所连接
        :param exchange_id: 交易所ID
        :return: 交易所连接实例
        """
        return self.connections.get(exchange_id)
    
    def check_all_connections(self) -> Dict[str, bool]:
        """
        检查所有交易所连接状态
        :return: 各交易所连接状态
        """
        return {
            exchange_id: connection.check_connection()
            for exchange_id, connection in self.connections.items()
        }
    
    def get_all_balances(self) -> Dict[str, Dict]:
        """
        获取所有交易所的余额
        :return: 各交易所余额信息
        """
        return {
            exchange_id: connection.get_balance()
            for exchange_id, connection in self.connections.items()
        }
    
    def get_market_info(self, symbol: str) -> Dict[str, Dict]:
        """
        获取所有交易所的市场信息
        :param symbol: 交易对
        :return: 各交易所的市场信息
        """
        return {
            exchange_id: connection.get_market_info(symbol)
            for exchange_id, connection in self.connections.items()
        }
    
    def close_all(self):
        """清理所有交易所连接"""
        self.connections.clear()
        print("已清理所有交易所连接") 