"""
交易所连接管理模块
"""
import ccxt
import asyncio
import logging
from typing import Dict, Any, Optional

from src.config.exchange import EXCHANGE_CONFIGS  # 修改为正确的导入路径

logger = logging.getLogger(__name__)

class ExchangeConnection:
    """交易所连接类"""
    
    def __init__(self, exchange_id: str, config: Dict[str, Any]):
        self.exchange_id = exchange_id
        self.config = config
        self.exchange: Optional[ccxt.Exchange] = None
        self.initialized = False
        self.last_error: Optional[Exception] = None
        
    async def initialize(self) -> bool:
        """初始化交易所连接"""
        try:
            # 创建交易所实例
            exchange_class = getattr(ccxt, self.exchange_id)
            self.exchange = exchange_class(self.config)
            
            # 加载市场
            await self.exchange.load_markets()
            
            self.initialized = True
            logger.info(f"交易所 {self.exchange_id} 连接初始化成功")
            return True
            
        except Exception as e:
            self.last_error = e
            logger.error(f"交易所 {self.exchange_id} 连接初始化失败: {str(e)}")
            return False
    
    async def close(self):
        """关闭交易所连接"""
        if self.exchange:
            try:
                await self.exchange.close()
                logger.info(f"交易所 {self.exchange_id} 连接已关闭")
            except Exception as e:
                logger.error(f"关闭交易所 {self.exchange_id} 连接时发生错误: {str(e)}")
        
        self.initialized = False
        self.exchange = None
    
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
            
            return self.exchange.load_markets().get(symbol, {})
            
        except Exception as e:
            print(f"获取 {self.exchange_id} 市场信息时发生错误: {str(e)}")
            return {} 