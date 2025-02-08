"""
市场数据处理模块

此模块提供了处理交易所市场数据的核心功能，包括市场类型管理、数据过滤和分类等功能。
它能够处理不同类型的市场（如现货、期货等）和不同计价货币的交易对。

主要功能：
1. 市场类型管理
   - 支持多种市场类型（spot, future, margin等）
   - 灵活的市场类型启用/禁用机制
   - 自动过滤无效市场类型

2. 交易对处理
   - 按计价货币分类
   - 支持多计价货币
   - 自动过滤无效交易对

3. 数据结构管理
   - 高效的数据组织
   - 支持快速查询和过滤
   - 错误处理和异常管理

使用示例：
    processor = MarketProcessor(exchange_instance)
    
    # 获取启用的市场类型
    enabled_types = processor.get_enabled_market_types(market_types)
    
    # 处理市场数据
    market_sets = processor.process_markets(markets, Config, market_types)

依赖：
- ExchangeInstance: 用于获取交易所实例

注意：
- 所有市场数据处理都包含错误处理机制
- 支持灵活的配置选项
- 建议在使用前检查市场类型配置
"""

from typing import Dict, List, Set

from .exchange_instance import ExchangeInstance


class MarketProcessor:
    """
    市场数据处理类
    
    此类负责处理和组织交易所的市场数据，包括市场类型管理和交易对分类。
    它提供了一系列方法来过滤和组织市场数据，使其更易于使用和管理。
    
    属性：
        exchange_instance (ExchangeInstance): 交易所实例管理器
    
    使用示例：
        processor = MarketProcessor(exchange_instance)
        enabled_types = processor.get_enabled_market_types(market_types)
        market_sets = processor.process_markets(markets, Config, market_types)
    """
    
    def __init__(self, exchange_instance: ExchangeInstance):
        """
        初始化市场数据处理器
        
        Args:
            exchange_instance (ExchangeInstance): 交易所实例管理器
        """
        self.exchange_instance = exchange_instance

    def get_enabled_market_types(self, market_types: Dict[str, bool]) -> List[str]:
        """
        获取已启用的市场类型列表
        
        此方法会过滤配置中的市场类型，只返回已启用的类型。
        
        Args:
            market_types (Dict[str, bool]): 市场类型配置字典，
                键为市场类型名称，值为布尔值表示是否启用
        
        Returns:
            List[str]: 已启用的市场类型列表
            
        示例：
            market_types = {
                'spot': True,
                'future': False,
                'margin': True
            }
            enabled = processor.get_enabled_market_types(market_types)
            # 返回: ['spot', 'margin']
        """
        return [mtype for mtype, enabled in market_types.items() if enabled]

    def process_markets(self, markets: dict, config: dict, market_types: Dict[str, bool]) -> Dict[
        str, Dict[str, Set[str]]]:
        """
        处理市场数据
        
        此方法是核心处理函数，它会：
        1. 创建空的数据结构
        2. 遍历所有市场数据
        3. 按市场类型和计价货币分类
        4. 处理异常情况
        
        Args:
            markets (dict): 原始市场数据
            config (dict): 配置信息，包含计价货币和类型配置
            market_types (Dict[str, bool]): 市场类型配置
            
        Returns:
            Dict[str, Dict[str, Set[str]]]: 处理后的市场数据，格式为：
                {
                    market_type: {
                        quote_currency: {symbol1, symbol2, ...}
                    }
                }
                
        示例：
            markets = {
                'BTC/USDT': {'quote': 'USDT', 'type': 'spot'},
                'ETH/USDT': {'quote': 'USDT', 'type': 'spot'}
            }
            result = processor.process_markets(markets, Config, market_types)
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
        
        此方法处理单个交易对的数据，将其分类到适当的市场类型和计价货币集合中。
        
        Args:
            symbol (str): 交易对符号（如 'BTC/USDT'）
            market (dict): 市场信息字典
            market_sets (Dict[str, Dict[str, Set[str]]]): 市场集合
            config (dict): 配置信息
            
        注意：
            - 如果计价货币不在配置中，该市场将被忽略
            - 如果市场类型不匹配，该市场将被忽略
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
        创建空的市场集合数据结构
        
        此方法创建一个嵌套的字典结构，用于存储不同市场类型和计价货币的交易对。
        
        Args:
            market_types (Dict[str, bool]): 市场类型配置
            config (dict): 配置信息
            
        Returns:
            Dict[str, Dict[str, Set[str]]]: 空的市场集合数据结构
            
        示例返回结构：
            {
                'spot': {
                    'USDT': set(),
                    'BTC': set()
                },
                'margin': {
                    'USDT': set(),
                    'BTC': set()
                }
            }
        """
        return {mtype: {quote: set() for quote in config['quote_currencies']}
                for mtype in self.get_enabled_market_types(market_types)}
