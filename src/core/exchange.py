"""
交易所实例类
"""

import logging
import ccxt.async_support as ccxt
from typing import Dict, Any, Optional, List
from src.config.exchange import EXCHANGE_CONFIGS

logger = logging.getLogger('arbitrage')

class ExchangeInstance:
    """交易所实例类"""
    
    def __init__(self, exchange_id: str):
        """
        初始化交易所实例
        :param exchange_id: 交易所ID
        """
        self._exchange_id = exchange_id
        self._config = EXCHANGE_CONFIGS.get(exchange_id, {})
        self._exchange: Optional[ccxt.Exchange] = None
        self._connected = False
        
    async def connect(self) -> bool:
        """
        连接到交易所
        :return: 是否连接成功
        """
        try:
            if self._exchange is None:
                exchange_class = getattr(ccxt, self._exchange_id)
                self._exchange = exchange_class(self._config)
                await self._exchange.load_markets()
                self._connected = True
                logger.info(f"已连接到交易所 {self._exchange_id}")
            return True
        except Exception as e:
            logger.error(f"连接到交易所 {self._exchange_id} 失败: {str(e)}")
            self._connected = False
            return False
            
    @property
    def is_connected(self) -> bool:
        """
        是否已连接
        :return: 连接状态
        """
        return self._connected
        
    async def disconnect(self):
        """断开连接"""
        if self._exchange:
            try:
                await self._exchange.close()
                self._connected = False
                logger.info(f"已断开与交易所 {self._exchange_id} 的连接")
            except Exception as e:
                logger.error(f"断开与交易所 {self._exchange_id} 的连接时出错: {str(e)}")
            finally:
                self._exchange = None
                
    async def fetch_markets(self) -> List[Dict[str, Any]]:
        """
        获取市场信息
        :return: 市场信息列表
        """
        if not self._connected:
            await self.connect()
        try:
            markets = await self._exchange.fetch_markets()
            return markets
        except Exception as e:
            logger.error(f"获取交易所 {self._exchange_id} 市场信息失败: {str(e)}")
            return []
            
    async def fetch_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取行情
        :param symbol: 交易对
        :return: 行情信息
        """
        if not self._connected:
            await self.connect()
        try:
            ticker = await self._exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"获取交易所 {self._exchange_id} 行情失败: {str(e)}")
            return None
            
    async def fetch_trading_fees(self) -> Dict[str, Any]:
        """
        获取交易手续费
        :return: 手续费信息
        """
        if not self._connected:
            await self.connect()
        try:
            fees = await self._exchange.fetch_trading_fees()
            return fees
        except Exception as e:
            logger.error(f"获取交易所 {self._exchange_id} 手续费失败: {str(e)}")
            return {}
            
    async def fetch_funding_fees(self, symbol: str) -> Dict[str, Any]:
        """
        获取资金费率
        :param symbol: 交易对
        :return: 资金费率信息
        """
        if not self._connected:
            await self.connect()
        try:
            fees = await self._exchange.fetch_funding_rate(symbol)
            return fees
        except Exception as e:
            logger.error(f"获取交易所 {self._exchange_id} 资金费率失败: {str(e)}")
            return {}
            
    async def fetch_leverage_tiers(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        获取杠杆分层
        :param symbols: 交易对列表
        :return: 杠杆分层信息
        """
        if not self._connected:
            await self.connect()
        try:
            tiers = await self._exchange.fetch_leverage_tiers(symbols)
            return tiers
        except Exception as e:
            logger.error(f"获取交易所 {self._exchange_id} 杠杆分层失败: {str(e)}")
            return {} 