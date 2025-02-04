import json
from asyncio import WindowsSelectorEventLoopPolicy, gather, run, set_event_loop_policy
from typing import Dict, List, Set

from exchange_config import EXCHANGES, EXCHANGE_CONFIGS, MARKET_TYPES, QUOTE_CURRENCIES
from exchange_instance import ExchangeInstance


class ExchangeMonitor:
    def __init__(self):
        self.exchange_instance = ExchangeInstance()
        self.common_symbols: Dict[str, Dict[str, Set[str]]] = {}
        self._initialize_common_symbols()

    def _initialize_common_symbols(self):
        """初始化交易对字典"""
        for market_type in MARKET_TYPES:
            self.common_symbols[market_type] = {quote: set() for quote in QUOTE_CURRENCIES}

    async def initialize(self):
        """初始化所有配置的交易所"""
        for exchange_id in EXCHANGES:
            try:
                await self._initialize_exchange(exchange_id)
            except Exception as e:
                print(f"Error initializing {exchange_id}: {str(e)}")

    async def _initialize_exchange(self, exchange_id: str):
        """初始化单个交易所"""
        await self.exchange_instance.get_rest_instance(exchange_id)
        await self.exchange_instance.get_ws_instance(exchange_id)

    def get_enabled_market_types(self) -> List[str]:
        """获取启用的市场类型"""
        return [mtype for mtype, enabled in MARKET_TYPES.items() if enabled]

    def get_markets(self, exchange_id: str) -> Dict[str, Dict[str, Set[str]]]:
        """获取指定交易所的所有交易对"""
        try:
            exchange = self.exchange_instance._rest_instances[exchange_id]
            config = EXCHANGE_CONFIGS[exchange_id]
            markets = exchange.load_markets()
            return self._process_markets(markets, config)
        except Exception as e:
            print(f"Error getting markets for {exchange_id}: {str(e)}")
            return self._get_empty_market_sets()

    def _get_empty_market_sets(self) -> Dict[str, Dict[str, Set[str]]]:
        """获取空的市场集合"""
        return {mtype: {quote: set() for quote in QUOTE_CURRENCIES}
                for mtype in self.get_enabled_market_types()}

    def _process_markets(self, markets: dict, config: dict) -> Dict[str, Dict[str, Set[str]]]:
        """处理市场数据"""
        market_sets = self._get_empty_market_sets()

        for symbol, market in markets.items():
            try:
                self._process_single_market(symbol, market, market_sets, config)
            except Exception as e:
                print(f"Error processing market {symbol}: {str(e)}")
                continue

        return market_sets

    def _process_single_market(self, symbol: str, market: dict,
                               market_sets: Dict[str, Dict[str, Set[str]]], config: dict):
        """处理单个市场数据"""
        quote = market['quote']
        if quote not in QUOTE_CURRENCIES:
            return

        market_type = market.get('type', '')
        for enabled_type in self.get_enabled_market_types():
            type_config = config['type_configs'][enabled_type]
            if market_type == type_config['type']:
                market_sets[enabled_type][quote].add(symbol)

    def find_common_symbols(self):
        """找出所有交易所共有的交易对"""
        first_exchange = True

        for exchange_id in EXCHANGES:
            market_sets = self.get_markets(exchange_id)
            self._update_common_symbols(market_sets, first_exchange)
            first_exchange = False

    def _update_common_symbols(self, market_sets: Dict[str, Dict[str, Set[str]]],
                               is_first: bool):
        """更新共同交易对"""
        for market_type, quotes in market_sets.items():
            for quote, symbols in quotes.items():
                if is_first:
                    self.common_symbols[market_type][quote] = symbols
                else:
                    if market_type in self.common_symbols:
                        self.common_symbols[market_type][quote] &= symbols

    async def monitor_exchange(self, exchange_id: str):
        """监控单个交易所的价格"""
        exchange = self.exchange_instance._ws_instances[exchange_id]
        enabled_types = self.get_enabled_market_types()

        while True:
            try:
                await self._monitor_exchange_markets(exchange_id, exchange, enabled_types)
            except Exception as e:
                await self._handle_monitor_error(exchange_id, exchange, e)

    async def _monitor_exchange_markets(self, exchange_id: str, exchange, enabled_types: List[str]):
        """监控交易所的市场"""
        for market_type in enabled_types:
            for quote in QUOTE_CURRENCIES:
                for symbol in self.common_symbols[market_type][quote]:
                    await self._monitor_symbol(exchange_id, exchange, symbol, market_type, quote)

    async def _monitor_symbol(self, exchange_id: str, exchange,
                              symbol: str, market_type: str, quote: str):
        """监控单个交易对"""
        try:
            ticker = await exchange.watch_ticker(symbol)
            if ticker and ticker.get('last'):
                self._print_ticker_info(exchange_id, market_type, symbol, quote, ticker['last'])
        except Exception as e:
            print(f"Error getting {symbol} from {exchange_id}: {str(e)}")

    def _print_ticker_info(self, exchange_id: str, market_type: str,
                           symbol: str, quote: str, price: float):
        """打印价格信息"""
        print(json.dumps({
            "exchange": exchange_id,
            "type"    : market_type,
            "symbol"  : symbol,
            "quote"   : quote,
            "price"   : price
        }))

    async def _handle_monitor_error(self, exchange_id: str, exchange, error: Exception):
        """处理监控错误"""
        print(f"Error monitoring {exchange_id}: {str(error)}")
        await exchange.close()
        try:
            await self.exchange_instance.get_ws_instance(exchange_id)
        except Exception as reconnect_error:
            print(f"Failed to reconnect to {exchange_id}: {str(reconnect_error)}")

    async def start_monitoring(self):
        """启动所有交易所的监控"""
        await self.initialize()
        self.find_common_symbols()
        self._print_common_symbols()

        monitoring_tasks = [self.monitor_exchange(exchange_id) for exchange_id in EXCHANGES]
        print("\n开始监控实时价格...")
        await gather(*monitoring_tasks)

    def _print_common_symbols(self):
        """打印共同交易对信息"""
        for market_type in self.get_enabled_market_types():
            for quote in QUOTE_CURRENCIES:
                symbols = list(self.common_symbols[market_type][quote])
                print(f"\n所有交易所共有的{quote} {market_type}交易对 (共{len(symbols)}个):")
                print(json.dumps(symbols, ensure_ascii=False, indent=2))

    async def close(self):
        """关闭所有连接"""
        await self.exchange_instance.close_all()


async def main():
    monitor = ExchangeMonitor()
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n正在关闭连接...")
        await monitor.close()
    except Exception as e:
        print(f"发生错误: {str(e)}")
        await monitor.close()


if __name__ == "__main__":
    # 在Windows下设置事件循环策略
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    run(main())
