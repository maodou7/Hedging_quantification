import json
from asyncio import gather, run

from exchange_config import EXCHANGES, EXCHANGE_CONFIGS, MARKET_TYPES, QUOTE_CURRENCIES
from exchange_instance import ExchangeInstance


class ExchangeMonitor:
    def __init__(self):
        self.exchange_instance = ExchangeInstance()
        self.common_symbols = {}
        # 初始化所有市场类型的字典
        for market_type in MARKET_TYPES:
            self.common_symbols[market_type] = {quote: set() for quote in QUOTE_CURRENCIES}

    async def initialize(self):
        """初始化所有配置的交易所"""
        for exchange_id in EXCHANGES:
            try:
                # 获取REST和WebSocket实例
                await self.exchange_instance.get_rest_instance(exchange_id)
                await self.exchange_instance.get_ws_instance(exchange_id)
            except Exception as e:
                print(f"Error initializing {exchange_id}: {str(e)}")

    def get_enabled_market_types(self):
        """获取启用的市场类型"""
        return [mtype for mtype, enabled in MARKET_TYPES.items() if enabled]

    def get_markets(self, exchange_id):
        """获取指定交易所的所有交易对"""
        try:
            exchange = self.exchange_instance._rest_instances[exchange_id]
            config = EXCHANGE_CONFIGS[exchange_id]
            markets = exchange.load_markets()

            # 为每个启用的市场类型创建集合
            market_sets = {}
            for market_type in self.get_enabled_market_types():
                market_sets[market_type] = {quote: set() for quote in QUOTE_CURRENCIES}

            for symbol, market in markets.items():
                try:
                    quote = market['quote']
                    if quote not in QUOTE_CURRENCIES:
                        continue

                    # 检查市场类型
                    market_type = market.get('type', '')

                    # 检查每个启用的市场类型
                    for enabled_type in self.get_enabled_market_types():
                        type_config = config['type_configs'][enabled_type]
                        if market_type == type_config['type']:
                            market_sets[enabled_type][quote].add(symbol)

                except Exception as e:
                    print(f"Error processing market {symbol} for {exchange_id}: {str(e)}")
                    continue

            return market_sets

        except Exception as e:
            print(f"Error getting markets for {exchange_id}: {str(e)}")
            return {mtype: {quote: set() for quote in QUOTE_CURRENCIES}
                    for mtype in self.get_enabled_market_types()}

    def find_common_symbols(self):
        """找出所有交易所共有的交易对"""
        first_exchange = True

        for exchange_id in EXCHANGES:
            market_sets = self.get_markets(exchange_id)

            if first_exchange:
                for market_type, quotes in market_sets.items():
                    for quote, symbols in quotes.items():
                        self.common_symbols[market_type][quote] = symbols
                first_exchange = False
            else:
                for market_type, quotes in market_sets.items():
                    for quote, symbols in quotes.items():
                        if market_type in self.common_symbols:
                            self.common_symbols[market_type][quote] &= symbols

    async def monitor_exchange(self, exchange_id):
        """监控单个交易所的价格"""
        exchange = self.exchange_instance._ws_instances[exchange_id]
        enabled_types = self.get_enabled_market_types()

        while True:
            try:
                for market_type in enabled_types:
                    for quote in QUOTE_CURRENCIES:
                        for symbol in self.common_symbols[market_type][quote]:
                            try:
                                ticker = await exchange.watch_ticker(symbol)
                                if ticker and ticker.get('last'):
                                    print(json.dumps({
                                        "exchange": exchange_id,
                                        "type"    : market_type,
                                        "symbol"  : symbol,
                                        "quote"   : quote,
                                        "price"   : ticker['last']
                                    }))
                            except Exception as e:
                                print(f"Error getting {symbol} from {exchange_id}: {str(e)}")

            except Exception as e:
                print(f"Error monitoring {exchange_id}: {str(e)}")
                await exchange.close()
                try:
                    await self.exchange_instance.get_ws_instance(exchange_id)
                except Exception as reconnect_error:
                    print(f"Failed to reconnect to {exchange_id}: {str(reconnect_error)}")
                    continue

    async def start_monitoring(self):
        """启动所有交易所的监控"""
        await self.initialize()

        # 找出共有的交易对
        self.find_common_symbols()

        # 只打印已启用的市场类型的交易对
        for market_type in self.get_enabled_market_types():
            for quote in QUOTE_CURRENCIES:
                symbols = list(self.common_symbols[market_type][quote])
                print(f"\n所有交易所共有的{quote} {market_type}交易对 (共{len(symbols)}个):")
                print(json.dumps(symbols, ensure_ascii=False, indent=2))

        monitoring_tasks = []
        for exchange_id in EXCHANGES:
            task = self.monitor_exchange(exchange_id)
            monitoring_tasks.append(task)

        print("\n开始监控实时价格...")
        await gather(*monitoring_tasks)

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
    run(main())
