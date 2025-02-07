"""
共同交易对查找模块

此模块提供了在多个交易所之间查找共同交易对的功能。它能够处理不同市场类型（如现货、期货等）
和不同计价货币的交易对，并找出在所有指定交易所中都可用的交易对。

主要功能：
1. 交易对查找
   - 支持多个交易所的交易对比较
   - 按市场类型和计价货币分类
   - 自动过滤不共同的交易对

2. 数据管理
   - 高效的集合操作
   - 灵活的数据结构
   - 错误处理机制

3. 结果展示
   - 格式化的输出
   - 统计信息显示
   - 分类展示结果

使用示例：
    finder = CommonSymbolsFinder(exchange_instance, market_processor, config)
    
    # 查找共同交易对
    finder.find_common_symbols(['binance', 'okex'])
    
    # 显示结果
    finder.print_common_symbols()

依赖：
- ExchangeInstance: 交易所实例管理
- MarketProcessor: 市场数据处理

注意：
- 确保所有交易所的API正常工作
- 考虑不同交易所的交易对命名差异
- 注意处理网络错误和超时情况
"""

import json
from typing import Dict, List, Set

from .exchange_instance import ExchangeInstance
from .market_processor import MarketProcessor


class CommonSymbolsFinder:
    """
    共同交易对查找类
    
    此类负责在多个交易所之间查找共同的交易对，支持按市场类型和计价货币进行分类。
    它使用集合操作来高效地找出所有交易所都支持的交易对。
    
    属性：
        exchange_instance (ExchangeInstance): 交易所实例管理器
        market_processor (MarketProcessor): 市场数据处理器
        config (dict): 系统配置信息
        common_symbols (Dict[str, Dict[str, Set[str]]]): 存储共同交易对的嵌套字典
    
    使用示例：
        finder = CommonSymbolsFinder(exchange_instance, market_processor, config)
        finder.find_common_symbols(['binance', 'okex'])
        finder.print_common_symbols()
    """
    
    def __init__(self, exchange_instance: ExchangeInstance, market_processor: MarketProcessor, config: dict):
        """
        初始化共同交易对查找器
        
        Args:
            exchange_instance (ExchangeInstance): 交易所实例管理器
            market_processor (MarketProcessor): 市场数据处理器
            config (dict): 系统配置信息，包含市场类型和计价货币配置
        """
        self.exchange_instance = exchange_instance
        self.market_processor = market_processor
        self.config = config
        self.common_symbols: Dict[str, Dict[str, Set[str]]] = {}
        self._initialize_common_symbols()

    def _initialize_common_symbols(self):
        """
        初始化交易对数据结构
        
        创建一个嵌套的字典结构来存储不同市场类型和计价货币的交易对集合。
        
        数据结构示例：
            {
                'spot': {
                    'USDT': set(),
                    'BTC': set()
                },
                'future': {
                    'USDT': set(),
                    'BTC': set()
                }
            }
        """
        for market_type in self.market_processor.get_enabled_market_types(self.config['market_types']):
            self.common_symbols[market_type] = {quote: set() for quote in self.config['quote_currencies']}

    def get_markets(self, exchange_id: str) -> Dict[str, Dict[str, Set[str]]]:
        """
        获取指定交易所的所有交易对数据
        
        此方法会从交易所获取市场数据，并使用市场处理器进行处理和分类。
        如果获取数据失败，会返回空的数据结构。
        
        Args:
            exchange_id (str): 交易所标识符
            
        Returns:
            Dict[str, Dict[str, Set[str]]]: 处理后的市场数据，格式为：
                {
                    market_type: {
                        quote_currency: {symbol1, symbol2, ...}
                    }
                }
                
        示例：
            markets = finder.get_markets('binance')
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
        """
        创建空的市场数据结构
        
        此方法创建一个与正常市场数据结构相同，但所有集合为空的数据结构。
        用于在获取市场数据失败时返回一个有效的空结构。
        
        Returns:
            Dict[str, Dict[str, Set[str]]]: 空的市场数据结构
        """
        return {mtype: {quote: set() for quote in self.config['quote_currencies']}
                for mtype in self.market_processor.get_enabled_market_types(self.config['market_types'])}

    def find_common_symbols(self, exchanges: List[str]):
        """
        查找所有交易所共有的交易对
        
        此方法会遍历所有指定的交易所，获取它们的市场数据，
        然后通过集合操作找出所有交易所都支持的交易对。
        
        Args:
            exchanges (List[str]): 要查找的交易所列表
            
        注意：
            - 第一个交易所的交易对集合会作为基准
            - 后续交易所的交易对会与基准集合求交集
            
        示例：
            finder.find_common_symbols(['binance', 'okex', 'huobi'])
        """
        first_exchange = True
        for exchange_id in exchanges:
            market_sets = self.get_markets(exchange_id)
            self._update_common_symbols(market_sets, first_exchange)
            first_exchange = False

    def _update_common_symbols(self, market_sets: Dict[str, Dict[str, Set[str]]], is_first: bool):
        """
        更新共同交易对集合
        
        此方法通过集合操作更新共同交易对。对于第一个交易所，直接使用其交易对集合；
        对于后续交易所，使用交集操作找出共同的交易对。
        
        Args:
            market_sets (Dict[str, Dict[str, Set[str]]]): 当前交易所的市场数据
            is_first (bool): 是否是第一个交易所
            
        注意：
            此方法是内部使用的，通常不应直接调用
        """
        for market_type, quotes in market_sets.items():
            for quote, symbols in quotes.items():
                if is_first:
                    self.common_symbols[market_type][quote] = symbols
                else:
                    if market_type in self.common_symbols:
                        self.common_symbols[market_type][quote] &= symbols

    def print_common_symbols(self):
        """
        打印共同交易对信息
        
        此方法以格式化的方式显示所有共同交易对，包括：
        - 按市场类型分类
        - 按计价货币分类
        - 显示每个类别的交易对数量
        
        输出示例：
            所有交易所共有的USDT spot交易对 (共50个):
            [
              "BTC/USDT",
              "ETH/USDT",
              ...
            ]
        """
        for market_type in self.market_processor.get_enabled_market_types(self.config['market_types']):
            for quote in self.config['quote_currencies']:
                symbols = list(self.common_symbols[market_type][quote])
                print(f"\n所有交易所共有的{quote} {market_type}交易对 (共{len(symbols)}个):")
                print(json.dumps(symbols, ensure_ascii=False, indent=2))
