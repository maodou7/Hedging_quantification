"""
市场结构获取模块

此模块负责从各个交易所获取详细的市场结构信息，并以标准化的格式保存。
主要功能包括：
1. 获取交易所的详细市场信息
2. 标准化市场数据结构
3. 将数据保存为JSON格式
4. 支持Redis和本地缓存

使用示例：
    fetcher = MarketStructureFetcher(exchange_instance)
    fetcher.fetch_and_save_market_structures(['binance', 'okx'])
"""

import json
import os
from typing import Dict, List, Union, Any, Set
import asyncio

from .exchange_instance import ExchangeInstance
from src.core.cache_manager import CacheManager
from src.core.cache_config import CACHE_CONFIG, CacheStrategy


class MarketStructureFetcher:
    """
    市场结构获取器
    
    此类负责从交易所获取详细的市场结构信息，并将其保存为标准化的格式。
    
    属性：
        exchange_instance (ExchangeInstance): 交易所实例管理器
        output_dir (str): 输出目录路径
        common_symbols (Dict[str, Set[str]]): 所有交易所共有的交易对，按市场类型分类
    """
    
    def __init__(self, exchange_instance: ExchangeInstance, output_dir: str = "market_structures"):
        """
        初始化市场结构获取器
        
        Args:
            exchange_instance (ExchangeInstance): 交易所实例管理器
            output_dir (str): 输出目录路径，默认为 "market_structures"
        """
        self.exchange_instance = exchange_instance
        self.output_dir = output_dir
        self.common_symbols: Dict[str, Set[str]] = {
            'spot': set(),
            'margin': set(),
            'future': set(),
            'swap': set(),
            'option': set()
        }
        self.cache_manager = CacheManager()
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def _format_number(self, exchange, symbol: str, value: Any, value_type: str) -> Union[str, Any]:
        """
        使用CCXT内置方法格式化数值
        
        Args:
            exchange: CCXT交易所实例
            symbol: 交易对符号
            value: 要格式化的值
            value_type: 值的类型 ('amount', 'price', 'cost')
            
        Returns:
            Union[str, Any]: 格式化后的值
        """
        if value is None:
            return None
        if isinstance(value, (float, int)):
            try:
                if value_type == 'amount':
                    return exchange.amount_to_precision(symbol, value)
                elif value_type == 'price':
                    return exchange.price_to_precision(symbol, value)
                elif value_type == 'cost':
                    return exchange.cost_to_precision(symbol, value)
                return str(value)
            except Exception:
                return str(value)
        return value
    
    def _process_market_data(self, exchange, market: Dict) -> Dict:
        """
        处理单个市场的数据
        
        Args:
            exchange: CCXT交易所实例
            market: 市场数据
            
        Returns:
            Dict: 处理后的市场数据
        """
        symbol = market.get('symbol')
        
        # 处理精度和限制
        precision = market.get('precision', {})
        limits = market.get('limits', {})
        
        processed_precision = {}
        for key, value in precision.items():
            if value is not None:
                processed_precision[key] = self._format_number(exchange, symbol, value, key)
        
        processed_limits = {}
        for limit_type, limit_values in limits.items():
            if isinstance(limit_values, dict):
                processed_limit = {}
                for key, value in limit_values.items():
                    processed_limit[key] = self._format_number(exchange, symbol, value, limit_type)
                processed_limits[limit_type] = processed_limit
        
        return {
            'id': market.get('id'),  # 交易所内部交易对ID
            '__comment_id': '交易所内部使用的交易对标识符',
            
            'symbol': symbol,  # 统一格式的交易对符号
            '__comment_symbol': '标准化的交易对符号，例如：BTC/USDT',
            
            'base': market.get('base'),  # 基础货币
            '__comment_base': '交易对中的基础货币，例如BTC/USDT中的BTC',
            
            'quote': market.get('quote'),  # 计价货币
            '__comment_quote': '交易对中的计价货币，例如BTC/USDT中的USDT',
            
            'baseId': market.get('baseId'),  # 交易所内部基础货币ID
            '__comment_baseId': '交易所内部使用的基础货币标识符',
            
            'quoteId': market.get('quoteId'),  # 交易所内部计价货币ID
            '__comment_quoteId': '交易所内部使用的计价货币标识符',
            
            'active': market.get('active', True),  # 交易对是否可用
            '__comment_active': '交易对是否处于可交易状态',
            
            'type': market.get('type', 'spot'),  # 市场类型
            '__comment_type': '市场类型：现货(spot)、永续(swap)、期货(future)、期权(option)',
            
            'spot': market.get('spot', False),  # 是否为现货市场
            '__comment_spot': '是否是现货交易市场',
            
            'margin': market.get('margin', False),  # 是否支持保证金交易
            '__comment_margin': '是否支持保证金交易',
            
            'future': market.get('future', False),  # 是否为期货市场
            '__comment_future': '是否是期货交易市场',
            
            'swap': market.get('swap', False),  # 是否为永续合约市场
            '__comment_swap': '是否是永续合约市场',
            
            'option': market.get('option', False),  # 是否为期权市场
            '__comment_option': '是否是期权交易市场',
            
            'contract': market.get('contract', False),  # 是否为合约市场
            '__comment_contract': '是否是合约市场（包括永续、期货、期权）',
            
            'settle': market.get('settle'),  # 结算货币
            '__comment_settle': '合约的结算货币',
            
            'settleId': market.get('settleId'),  # 交易所内部结算货币ID
            '__comment_settleId': '交易所内部使用的结算货币标识符',
            
            'contractSize': self._format_number(exchange, symbol, market.get('contractSize', 1), 'amount'),  # 合约面值
            '__comment_contractSize': '合约面值，表示一张合约代表的数量',
            
            'linear': market.get('linear'),  # 是否为线性合约
            '__comment_linear': '是否是线性合约（用计价货币结算）',
            
            'inverse': market.get('inverse'),  # 是否为反向合约
            '__comment_inverse': '是否是反向合约（用基础货币结算）',
            
            'expiry': market.get('expiry'),  # 到期时间戳
            '__comment_expiry': '合约到期的Unix时间戳',
            
            'expiryDatetime': market.get('expiryDatetime'),  # 到期时间ISO格式
            '__comment_expiryDatetime': '合约到期的ISO格式时间字符串',
            
            'strike': self._format_number(exchange, symbol, market.get('strike'), 'price'),  # 期权行权价
            '__comment_strike': '期权的行权价格',
            
            'optionType': market.get('optionType'),  # 期权类型
            '__comment_optionType': '期权类型：看涨(call)或看跌(put)',
            
            'taker': self._format_number(exchange, symbol, market.get('taker'), 'price'),  # taker手续费
            '__comment_taker': 'taker手续费率',
            
            'maker': self._format_number(exchange, symbol, market.get('maker'), 'price'),  # maker手续费
            '__comment_maker': 'maker手续费率',
            
            'percentage': market.get('percentage', True),  # 手续费是否为百分比
            '__comment_percentage': '手续费是否以百分比计算',
            
            'tierBased': market.get('tierBased', False),  # 是否基于等级的手续费
            '__comment_tierBased': '是否使用等级制手续费',
            
            'feeSide': market.get('feeSide'),  # 手续费计算方向
            '__comment_feeSide': '手续费计算方向：base（基础货币）或quote（计价货币）',
            
            'precision': processed_precision,  # 精度设置
            '__comment_precision': '交易精度设置，包括价格、数量、成本等的小数位数',
            
            'limits': processed_limits,  # 限制设置
            '__comment_limits': '交易限制，包括最小/最大交易数量、价格、成本等',
            
            'precisionMode': getattr(exchange, 'precisionMode', 'DECIMAL_PLACES'),  # 精度模式
            '__comment_precisionMode': '精度模式：DECIMAL_PLACES（小数位数）、SIGNIFICANT_DIGITS（有效数字）、TICK_SIZE（最小变动价位）',
            
            'info': market.get('info', {}),  # 原始信息
            '__comment_info': '交易所返回的原始未处理信息'
        }
    
    def set_common_symbols(self, symbols_by_type: Dict[str, List[str]]):
        """
        设置共有交易对列表
        
        Args:
            symbols_by_type (Dict[str, List[str]]): 按市场类型分类的共有交易对列表
                例如：{
                    'spot': ['BTC/USDT', 'ETH/USDT'],
                    'swap': ['BTC/USDT:USDT', 'ETH/USDT:USDT'],
                    'future': ['BTC/USDT-240628'],
                    'option': ['BTC/USDT-240628-50000-C'],
                    'margin': ['BTC/USDT']
                }
        """
        for market_type, symbols in symbols_by_type.items():
            if market_type in self.common_symbols:
                self.common_symbols[market_type] = set(symbols)
    
    async def fetch_market_structure(self, exchange_id: str) -> Dict:
        """异步获取指定交易所的市场结构"""
        # 尝试从缓存获取
        cache_key = f"market_structure:{exchange_id}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data:
            return cached_data

        try:
            # 异步获取交易所实例
            exchange = await self.exchange_instance.get_rest_instance(exchange_id)
            
            # 异步加载市场数据
            markets = await asyncio.get_event_loop().run_in_executor(
                None, exchange.load_markets
            )
            
            # 处理每个市场的数据
            processed_markets = {}
            for symbol, market in markets.items():
                # 检查是否为共有交易对
                market_type = market.get('type', 'spot')
                if (market_type in self.common_symbols and 
                    symbol in self.common_symbols[market_type]):
                    processed_markets[symbol] = self._process_market_data(exchange, market)
            
            # 保存到缓存
            self.cache_manager.set(cache_key, processed_markets)
            
            return processed_markets
        except Exception as e:
            print(f"获取{exchange_id}市场结构时发生错误: {str(e)}")
            return {}
    
    def _filter_comments(self, data: Dict) -> Dict:
        """
        过滤掉数据中的注释字段
        
        Args:
            data (Dict): 包含注释的数据字典
            
        Returns:
            Dict: 过滤掉注释后的数据字典
        """
        if not isinstance(data, dict):
            return data
            
        filtered_data = {}
        for key, value in data.items():
            # 跳过以__comment_开头的字段
            if key.startswith('__comment_'):
                continue
                
            # 递归处理嵌套的字典
            if isinstance(value, dict):
                filtered_data[key] = self._filter_comments(value)
            # 处理字典列表
            elif isinstance(value, list):
                filtered_data[key] = [
                    self._filter_comments(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                filtered_data[key] = value
                
        return filtered_data

    def save_market_structure(self, exchange_id: str, market_structure: Dict, include_comments: bool = True):
        """
        保存市场结构数据
        
        Args:
            exchange_id (str): 交易所ID
            market_structure (Dict): 市场结构数据
            include_comments (bool): 是否包含注释
        """
        if not market_structure:
            return
            
        # 如果是本地缓存策略，则保存到本地文件
        if CACHE_CONFIG["strategy"] == CacheStrategy.LOCAL:
            data = market_structure if include_comments else self._filter_comments(market_structure)
            filename = os.path.join(self.output_dir, f"{exchange_id}_market_structure.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
    
    async def fetch_and_save_market_structures(self, exchanges: List[str], include_comments: bool = True):
        """异步获取并保存多个交易所的市场结构"""
        tasks = []
        for exchange_id in exchanges:
            tasks.append(self.fetch_market_structure(exchange_id))
        
        results = await asyncio.gather(*tasks)
        
        for exchange_id, market_structure in zip(exchanges, results):
            if market_structure:
                self.save_market_structure(exchange_id, market_structure, include_comments) 