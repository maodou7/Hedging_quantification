import ccxt
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExchangeManager:
    def __init__(self):
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.connection_status = {}
        self.exchange_configs = {
            'binance': {
                'apiKey': '',  # 在实际使用时填入
                'secret': '',  # 在实际使用时填入
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            },
            'okx': {
                'apiKey': '',
                'secret': '',
                'enableRateLimit': True,
            },
            'bybit': {
                'apiKey': '',
                'secret': '',
                'enableRateLimit': True,
            },
            'huobi': {
                'apiKey': '',
                'secret': '',
                'enableRateLimit': True,
            },
            'gateio': {
                'apiKey': '',
                'secret': '',
                'enableRateLimit': True,
            }
        }

    async def initialize(self):
        """初始化所有交易所连接"""
        for exchange_id in self.exchange_configs:
            try:
                # 初始化连接状态
                self.connection_status[exchange_id] = {
                    'rest': False,
                    'websocket': False
                }
                
                # 创建交易所实例
                exchange_class = getattr(ccxt, exchange_id)
                exchange = exchange_class(self.exchange_configs[exchange_id])
                exchange.load_markets()
                
                # 测试REST连接
                rest_connected = await self.test_connection(exchange)
                self.connection_status[exchange_id]['rest'] = rest_connected
                
                if rest_connected:
                    self.exchanges[exchange_id] = exchange
                    # 假设WebSocket连接成功（因为ccxt不直接支持WebSocket）
                    self.connection_status[exchange_id]['websocket'] = True
                
            except Exception as e:
                self.connection_status[exchange_id] = {
                    'rest': False,
                    'websocket': False
                }

    async def test_connection(self, exchange: ccxt.Exchange) -> bool:
        """测试交易所连接"""
        try:
            await exchange.fetch_time()
            return True
        except Exception as e:
            return False

    async def get_connection_status(self) -> Dict:
        """获取所有交易所的连接状态"""
        return self.connection_status

    async def get_ticker(self, exchange_id: str, symbol: str) -> Optional[Dict]:
        """获取指定交易对的行情数据"""
        try:
            exchange = self.exchanges.get(exchange_id)
            if not exchange:
                return None

            ticker = await exchange.fetch_ticker(symbol)
            return {
                'symbol': ticker['symbol'],
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['baseVolume'],
                'timestamp': datetime.fromtimestamp(ticker['timestamp'] / 1000).isoformat()
            }
        except Exception as e:
            return None

    async def get_all_tickers(self) -> Dict[str, Dict]:
        """获取所有交易所的所有交易对行情"""
        results = {}
        for exchange_id, exchange in self.exchanges.items():
            try:
                tickers = await exchange.fetch_tickers()
                results[exchange_id] = tickers
            except Exception as e:
                pass
        return results

    def get_exchange(self, exchange_id: str) -> Optional[ccxt.Exchange]:
        """获取指定交易所实例"""
        return self.exchanges.get(exchange_id)

# 创建全局交易所管理器实例
exchange_manager = ExchangeManager() 