import json
from typing import Dict, List, Set

from .exchange_instance import ExchangeInstance
from .market_processor import MarketProcessor


class CommonSymbolsFinder:
    def __init__(self, exchange_instance: ExchangeInstance, market_processor: MarketProcessor, config: dict):
        self.exchange_instance = exchange_instance
        self.market_processor = market_processor
        self.config = config
        self.common_symbols: Dict[str, Dict[str, Set[str]]] = {}
        self._initialize_common_symbols()

    def _initialize_common_symbols(self):
        """初始化交易对字典"""
        for market_type in self.market_processor.get_enabled_market_types(self.config['market_types']):
            self.common_symbols[market_type] = {quote: set() for quote in self.config['quote_currencies']}

    def get_markets(self, exchange_id: str) -> Dict[str, Dict[str, Set[str]]]:
        """
        获取指定交易所的所有交易对
        
        Args:
            exchange_id: 交易所ID
            
        Returns:
            Dict[str, Dict[str, Set[str]]]: 交易所的市场数据
        """
        try:
            exchange = self.exchange_instance._rest_instances[exchange_id]
            markets = exchange.load_markets()
            return self.market_processor.process_markets(
                markets,
                self.config,
                self.config['market_types']
            )
        except Exception as e:
            print(f"获取 {exchange_id} 的市场数据时发生错误: {str(e)}")
            return self._get_empty_market_sets()

    def _get_empty_market_sets(self) -> Dict[str, Dict[str, Set[str]]]:
        """获取空的市场集合"""
        return {mtype: {quote: set() for quote in self.config['quote_currencies']}
                for mtype in self.market_processor.get_enabled_market_types(self.config['market_types'])}

    def find_common_symbols(self, exchanges: List[str]):
        """
        找出所有交易所共有的交易对
        
        Args:
            exchanges: 交易所列表
        """
        first_exchange = True
        for exchange_id in exchanges:
            market_sets = self.get_markets(exchange_id)
            self._update_common_symbols(market_sets, first_exchange)
            first_exchange = False

    def _update_common_symbols(self, market_sets: Dict[str, Dict[str, Set[str]]], is_first: bool):
        """
        更新共同交易对
        
        Args:
            market_sets: 市场数据集合
            is_first: 是否是第一个交易所
        """
        for market_type, quotes in market_sets.items():
            for quote, symbols in quotes.items():
                if is_first:
                    self.common_symbols[market_type][quote] = symbols
                else:
                    if market_type in self.common_symbols:
                        self.common_symbols[market_type][quote] &= symbols

    def print_common_symbols(self):
        """打印共同交易对信息"""
        for market_type in self.market_processor.get_enabled_market_types(self.config['market_types']):
            for quote in self.config['quote_currencies']:
                symbols = list(self.common_symbols[market_type][quote])
                print(f"\n所有交易所共有的{quote} {market_type}交易对 (共{len(symbols)}个):")
                print(json.dumps(symbols, ensure_ascii=False, indent=2))
