"""
策略基类

定义了所有策略都需要实现的基本接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseStrategy(ABC):
    def __init__(self):
        self.is_running = False
        
    @abstractmethod
    async def start(self):
        """启动策略"""
        pass
        
    @abstractmethod
    async def stop(self):
        """停止策略"""
        pass
        
    @abstractmethod
    async def process_price_update(self, exchange_id: str, symbol: str, price_data: Dict[str, Any]):
        """处理价格更新
        
        Args:
            exchange_id: 交易所ID
            symbol: 交易对
            price_data: 价格数据
        """
        pass
        
    @abstractmethod
    def calculate_opportunity(self, exchange_id: str, symbol: str, price_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """计算交易机会
        
        Args:
            exchange_id: 交易所ID
            symbol: 交易对
            price_data: 价格数据
            
        Returns:
            Dict 包含交易机会的详细信息，如果没有机会则返回None
        """
        pass
        
    @abstractmethod
    async def execute_trade(self, opportunity: Dict[str, Any]):
        """执行交易
        
        Args:
            opportunity: 交易机会详情
        """
        pass 