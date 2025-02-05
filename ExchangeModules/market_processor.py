from typing import Dict, List, Set

from .exchange_instance import ExchangeInstance


class MarketProcessor:
    def __init__(self, exchange_instance: ExchangeInstance):
        self.exchange_instance = exchange_instance

    def get_enabled_market_types(self, market_types: Dict[str, bool]) -> List[str]:
        """
        获取启用的市场类型
        
        Args:
            market_types: 市场类型配置字典
            
        Returns:
            List[str]: 启用的市场类型列表
        """
        return [mtype for mtype, enabled in market_types.items() if enabled]

    def process_markets(self, markets: dict, config: dict, market_types: Dict[str, bool]) -> Dict[
        str, Dict[str, Set[str]]]:
        """
        处理市场数据
        
        Args:
            markets: 市场数据
            config: 配置信息
            market_types: 市场类型配置
            
        Returns:
            Dict[str, Dict[str, Set[str]]]: 处理后的市场数据
        """
        market_sets = self._get_empty_market_sets(market_types, config)
        for symbol, market in markets.items():
            try:
                self._process_single_market(symbol, market, market_sets, config)
            except Exception as e:
                print(f"处理市场 {symbol} 时发生错误: {str(e)}")
                continue
        return market_sets

    def _process_single_market(self, symbol: str, market: dict,
                               market_sets: Dict[str, Dict[str, Set[str]]], config: dict):
        """
        处理单个市场数据
        
        Args:
            symbol: 交易对符号
            market: 市场信息
            market_sets: 市场集合
            config: 配置信息
        """
        quote = market['quote']
        if quote not in config['quote_currencies']:
            return

        market_type = market.get('type', '')
        for enabled_type in self.get_enabled_market_types(config['type_configs']):
            type_config = config['type_configs'][enabled_type]
            if market_type == type_config['type']:
                market_sets[enabled_type][quote].add(symbol)

    def _get_empty_market_sets(self, market_types: Dict[str, bool], config: dict) -> Dict[str, Dict[str, Set[str]]]:
        """
        获取空的市场集合
        
        Args:
            market_types: 市场类型配置
            config: 配置信息
            
        Returns:
            Dict[str, Dict[str, Set[str]]]: 空的市场集合
        """
        return {mtype: {quote: set() for quote in config['quote_currencies']}
                for mtype in self.get_enabled_market_types(market_types)}
