import json
from typing import List

from .common_symbols_finder import CommonSymbolsFinder
from .exchange_instance import ExchangeInstance
from .market_processor import MarketProcessor


class MonitorManager:
    def __init__(self, exchange_instance: ExchangeInstance, config: dict):
        self.exchange_instance = exchange_instance
        self.market_processor = MarketProcessor(exchange_instance)
        self.common_symbols_finder = CommonSymbolsFinder(exchange_instance, self.market_processor, config)
        self.config = config

    async def initialize(self, exchanges: List[str]):
        """
        初始化所有配置的交易所
        
        Args:
            exchanges: 交易所列表
        """
        for exchange_id in exchanges:
            try:
                await self.exchange_instance.get_rest_instance(exchange_id)
                await self.exchange_instance.get_ws_instance(exchange_id)
            except Exception as e:
                print(f"初始化 {exchange_id} 时发生错误: {str(e)}")

    async def monitor_exchange(self, exchange_id: str):
        """
        监控单个交易所的价格
        
        Args:
            exchange_id: 交易所ID
        """
        exchange = self.exchange_instance._ws_instances[exchange_id]
        enabled_types = self.market_processor.get_enabled_market_types(self.config['market_types'])

        while True:
            try:
                await self._monitor_exchange_markets(exchange_id, exchange, enabled_types)
            except Exception as e:
                await self._handle_monitor_error(exchange_id, exchange, e)

    async def _monitor_exchange_markets(self, exchange_id: str, exchange, enabled_types: List[str]):
        """
        监控交易所的市场
        
        Args:
            exchange_id: 交易所ID
            exchange: 交易所实例
            enabled_types: 启用的市场类型列表
        """
        for market_type in enabled_types:
            for quote in self.config['quote_currencies']:
                for symbol in self.common_symbols_finder.common_symbols[market_type][quote]:
                    await self._monitor_symbol(exchange_id, exchange, symbol, market_type, quote)

    async def _monitor_symbol(self, exchange_id: str, exchange,
                              symbol: str, market_type: str, quote: str):
        """
        监控单个交易对
        
        Args:
            exchange_id: 交易所ID
            exchange: 交易所实例
            symbol: 交易对符号
            market_type: 市场类型
            quote: 计价货币
        """
        try:
            ticker = await exchange.watch_ticker(symbol)
            if ticker and ticker.get('last'):
                self._print_ticker_info(exchange_id, market_type, symbol, quote, ticker['last'])
        except Exception as e:
            print(f"获取 {exchange_id} 的 {symbol} 数据时发生错误: {str(e)}")

    def _print_ticker_info(self, exchange_id: str, market_type: str,
                           symbol: str, quote: str, price: float):
        """
        打印价格信息
        
        Args:
            exchange_id: 交易所ID
            market_type: 市场类型
            symbol: 交易对符号
            quote: 计价货币
            price: 价格
        """
        print(json.dumps({
            "exchange": exchange_id,
            "type"    : market_type,
            "symbol"  : symbol,
            "quote"   : quote,
            "price"   : price
        }, ensure_ascii=False))

    async def _handle_monitor_error(self, exchange_id: str, exchange, error: Exception):
        """
        处理监控错误
        
        Args:
            exchange_id: 交易所ID
            exchange: 交易所实例
            error: 错误信息
        """
        print(f"监控 {exchange_id} 时发生错误: {str(error)}")
        await exchange.close()
        try:
            await self.exchange_instance.get_ws_instance(exchange_id)
        except Exception as reconnect_error:
            print(f"重新连接 {exchange_id} 失败: {str(reconnect_error)}")

    def start_monitoring(self, exchanges: List[str]):
        """
        开始监控所有交易所
        
        Args:
            exchanges: 交易所列表
        """
        self.common_symbols_finder.find_common_symbols(exchanges)
        self.common_symbols_finder.print_common_symbols()
        print("\n开始监控实时价格...")
