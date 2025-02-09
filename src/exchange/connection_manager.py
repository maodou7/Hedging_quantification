"""
交易所连接管理器模块
"""
import logging
from typing import Dict, Optional
from src.config.exchange import EXCHANGES
from .exchange_connection import ExchangeConnection

logger = logging.getLogger(__name__)

class ConnectionManager:
    """交易所连接管理器类"""
    
    def __init__(self):
        """初始化交易所连接管理器"""
        self._connections: Dict[str, ExchangeConnection] = {}
        
    def get_connection(self, exchange_id: str) -> Optional[ExchangeConnection]:
        """获取指定交易所的连接实例"""
        if exchange_id not in EXCHANGES:
            logger.error(f"未知的交易所ID: {exchange_id}")
            return None
            
        if exchange_id not in self._connections:
            try:
                self._connections[exchange_id] = ExchangeConnection(EXCHANGES[exchange_id])
            except Exception as e:
                logger.error(f"创建交易所连接失败: {e}")
                return None
                
        return self._connections[exchange_id]
        
    def close_all(self):
        """关闭所有交易所连接"""
        for connection in self._connections.values():
            try:
                connection.close()
            except Exception as e:
                logger.error(f"关闭交易所连接失败: {e}")
                
        self._connections.clear() 