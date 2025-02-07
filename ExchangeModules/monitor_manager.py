"""
交易所监控管理模块

此模块提供了一个完整的交易所价格监控系统，能够同时监控多个交易所的多个交易对的实时价格。
它通过WebSocket连接实现高效的实时数据获取，并提供了完善的错误处理和自动重连机制。

主要功能：
1. 多交易所监控
   - 支持同时监控多个交易所
   - 自动管理WebSocket连接
   - 智能的错误处理和重连机制

2. 实时价格监控
   - 支持多种市场类型
   - 支持多种计价货币
   - 实时价格更新和展示
   - 支持超高精度价格显示

3. 系统管理
   - 统一的初始化接口
   - 灵活的配置管理
   - 完善的错误处理

使用示例：
    # 创建监控管理器
    manager = MonitorManager(exchange_instance, config)
    
    # 初始化交易所连接
    await manager.initialize(['binance', 'okex'])
    
    # 开始监控
    manager.start_monitoring(['binance', 'okex'])
    
    # 运行监控任务
    await manager.monitor_exchange('binance')

依赖：
- ExchangeInstance: 交易所实例管理
- MarketProcessor: 市场数据处理
- CommonSymbolsFinder: 共同交易对查找

注意：
- 确保网络连接稳定
- 正确配置交易所API参数
- 监控任务应在异步环境中运行
"""

import json
from decimal import Decimal
from typing import List

from .common_symbols_finder import CommonSymbolsFinder
from .exchange_instance import ExchangeInstance
from .market_processor import MarketProcessor


class MonitorManager:
    """
    交易所监控管理类
    
    此类负责管理和协调整个交易所监控系统，包括初始化连接、
    启动监控、处理数据和错误处理等核心功能。
    
    属性：
        exchange_instance (ExchangeInstance): 交易所实例管理器
        market_processor (MarketProcessor): 市场数据处理器
        common_symbols_finder (CommonSymbolsFinder): 共同交易对查找器
        config (dict): 系统配置信息
    
    使用示例：
        manager = MonitorManager(exchange_instance, config)
        await manager.initialize(['binance'])
        manager.start_monitoring(['binance'])
        await manager.monitor_exchange('binance')
    """
    
    def __init__(self, exchange_instance: ExchangeInstance, config: dict):
        """
        初始化监控管理器
        
        Args:
            exchange_instance (ExchangeInstance): 交易所实例管理器
            config (dict): 系统配置信息，包含市场类型和计价货币等配置
        """
        self.exchange_instance = exchange_instance
        self.market_processor = MarketProcessor(exchange_instance)
        self.common_symbols_finder = CommonSymbolsFinder(exchange_instance, self.market_processor, config)
        self.config = config

    async def initialize(self, exchanges: List[str]):
        """
        初始化所有配置的交易所连接
        
        此方法会为每个交易所创建REST和WebSocket连接。
        如果某个交易所初始化失败，会打印错误信息但继续处理其他交易所。
        
        Args:
            exchanges (List[str]): 要初始化的交易所ID列表
            
        示例：
            await manager.initialize(['binance', 'okex'])
        """
        for exchange_id in exchanges:
            try:
                await self.exchange_instance.get_rest_instance(exchange_id)
                await self.exchange_instance.get_ws_instance(exchange_id)
            except Exception as e:
                print(f"初始化 {exchange_id} 时发生错误: {str(e)}")

    async def monitor_exchange(self, exchange_id: str):
        """
        监控单个交易所的价格数据
        
        此方法会持续监控指定交易所的所有配置的交易对的价格。
        它使用WebSocket连接实时获取数据，并在发生错误时自动重试。
        
        Args:
            exchange_id (str): 要监控的交易所ID
            
        注意：
            - 此方法会无限循环运行，直到发生不可恢复的错误
            - 所有错误都会被捕获并处理，不会导致程序崩溃
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
        监控交易所的所有市场
        
        此方法遍历所有启用的市场类型和计价货币，
        监控每个符合条件的交易对的价格。
        
        Args:
            exchange_id (str): 交易所ID
            exchange: 交易所WebSocket实例
            enabled_types (List[str]): 启用的市场类型列表
            
        注意：
            此方法是内部使用的，通常不应直接调用
        """
        for market_type in enabled_types:
            for quote in self.config['quote_currencies']:
                for symbol in self.common_symbols_finder.common_symbols[market_type][quote]:
                    await self._monitor_symbol(exchange_id, exchange, symbol, market_type, quote)

    async def _monitor_symbol(self, exchange_id: str, exchange,
                              symbol: str, market_type: str, quote: str):
        """
        监控单个交易对的价格
        
        此方法通过WebSocket获取单个交易对的实时价格数据，
        并在成功获取数据时打印价格信息。
        
        Args:
            exchange_id (str): 交易所ID
            exchange: 交易所WebSocket实例
            symbol (str): 交易对符号（如 'BTC/USDT'）
            market_type (str): 市场类型
            quote (str): 计价货币
            
        注意：
            - 价格获取失败会打印错误信息但不会中断监控
            - 此方法是内部使用的，通常不应直接调用
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
        
        此方法将价格信息格式化为JSON并打印输出。使用Decimal处理高精度价格，
        避免科学计数法表示，保持价格的完整精度。
        
        Args:
            exchange_id (str): 交易所ID
            market_type (str): 市场类型
            symbol (str): 交易对符号
            quote (str): 计价货币
            price (float): 最新价格
            
        输出格式示例：
            {
                "exchange": "binance",
                "type": "spot",
                "symbol": "BTC/USDT",
                "quote": "USDT",
                "price": "0.000009404"
            }
        """
        # 使用Decimal处理价格，避免科学计数法
        price_decimal = Decimal(str(price))
        formatted_price = format(price_decimal, 'f')  # 使用普通十进制格式
        
        # 移除末尾多余的0，但保留必要的小数位
        formatted_price = formatted_price.rstrip('0').rstrip('.') if '.' in formatted_price else formatted_price
        
        print(json.dumps({
            "exchange": exchange_id,
            "type": market_type,
            "symbol": symbol,
            "quote": quote,
            "price": formatted_price
        }, ensure_ascii=False))

    async def _handle_monitor_error(self, exchange_id: str, exchange, error: Exception):
        """
        处理监控过程中的错误
        
        此方法实现了错误处理和自动重连机制：
        1. 打印错误信息
        2. 关闭现有连接
        3. 尝试重新建立连接
        
        Args:
            exchange_id (str): 交易所ID
            exchange: 发生错误的交易所实例
            error (Exception): 捕获到的错误
            
        注意：
            - 重连失败会打印错误信息但不会抛出异常
            - 此方法是内部使用的，通常不应直接调用
        """
        print(f"监控 {exchange_id} 时发生错误: {str(error)}")
        await exchange.close()
        try:
            await self.exchange_instance.get_ws_instance(exchange_id)
        except Exception as reconnect_error:
            print(f"重新连接 {exchange_id} 失败: {str(reconnect_error)}")

    def start_monitoring(self, exchanges: List[str]):
        """
        启动所有交易所的监控
        
        此方法执行监控启动前的准备工作：
        1. 查找共同交易对
        2. 打印交易对信息
        3. 准备开始监控
        
        Args:
            exchanges (List[str]): 要监控的交易所列表
            
        示例：
            manager.start_monitoring(['binance', 'okex'])
        """
        self.common_symbols_finder.find_common_symbols(exchanges)
        self.common_symbols_finder.print_common_symbols()
        print("\n开始监控实时价格...")
