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
   - 符合CCXT精度规范

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
- 价格精度遵循CCXT规范
"""

import json
from typing import List
import time as import_time
import ccxt.async_support as ccxt
import logging

from .common_symbols_finder import CommonSymbolsFinder
from .exchange_instance import ExchangeInstance
from .market_processor import MarketProcessor

logger = logging.getLogger(__name__)

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
        latest_prices (dict): 存储最新价格数据
        exchange_status (dict): 存储交易所连接状态
    
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
        self.config = config
        # 存储最新价格数据
        self.latest_prices = {}
        # 存储交易所连接状态
        self.exchange_status = {}
        self.common_symbols_finder = CommonSymbolsFinder(exchange_instance, self.market_processor, config)
        self.running = True

    def get_latest_prices(self):
        """获取所有最新价格数据"""
        return self.latest_prices

    def get_exchange_status(self):
        """获取所有交易所连接状态"""
        return self.exchange_status

    async def initialize(self, exchanges: List[str], max_retries: int = 3, retry_delay: float = 5.0):
        """
        初始化所有配置的交易所连接
        
        此方法会为每个交易所创建REST和WebSocket连接。
        包含重试机制，在连接失败时会多次尝试重新连接。
        
        Args:
            exchanges (List[str]): 要初始化的交易所ID列表
            max_retries (int): 最大重试次数
            retry_delay (float): 重试间隔时间（秒）
            
        示例：
            await manager.initialize(['binance', 'okex'])
        """
        import asyncio
        
        for exchange_id in exchanges:
            retries = 0
            while retries < max_retries:
                try:
                    # 尝试初始化REST和WebSocket连接
                    await self.exchange_instance.get_rest_instance(exchange_id)
                    await self.exchange_instance.get_ws_instance(exchange_id)
                    print(f"✅ 成功初始化交易所 {exchange_id} 的连接")
                    break
                except Exception as e:
                    retries += 1
                    error_msg = f"初始化 {exchange_id} 时发生错误: {str(e)}"
                    if retries < max_retries:
                        print(f"❌ {error_msg}，{retry_delay}秒后进行第{retries + 1}次重试...")
                        await asyncio.sleep(retry_delay)
                    else:
                        print(f"❌ {error_msg}，已达到最大重试次数，跳过此交易所")

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
        exchange_config = self.config[exchange_id]
        enabled_types = self.market_processor.get_enabled_market_types(exchange_config['market_types'])

        while self.running:
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
        """
        exchange_config = self.config[exchange_id]
        for market_type in enabled_types:
            for quote in exchange_config['quote_currencies']:
                for symbol in self.common_symbols_finder.common_symbols[market_type][quote]:
                    await self._monitor_symbol(exchange_id, exchange, symbol, market_type, quote)

    async def _monitor_symbol(self, exchange_id: str, exchange,
                              symbol: str, market_type: str, quote: str):
        """
        监控单个交易对的价格
        
        此方法通过WebSocket获取单个交易对的实时价格数据，
        并在成功获取数据时打印价格信息。价格精度处理遵循CCXT规范。
        
        Args:
            exchange_id (str): 交易所ID
            exchange: 交易所WebSocket实例
            symbol (str): 交易对符号（如 'BTC/USDT'）
            market_type (str): 市场类型
            quote (str): 计价货币
            
        注意：
            - 价格精度根据交易所规则自动处理
            - 使用CCXT的price_to_precision方法确保精度正确
        """
        try:
            ticker = await exchange.watch_ticker(symbol)
            if ticker and ticker.get('last'):
                formatted_price = exchange.price_to_precision(symbol, ticker['last'])
                price_info = {
                    "exchange": exchange_id,
                    "type": market_type,
                    "symbol": symbol,
                    "quote": quote,
                    "price": formatted_price,
                    "timestamp": ticker.get('timestamp', None)
                }
                # 更新最新价格
                key = f"{exchange_id}:{market_type}:{symbol}"
                self.latest_prices[key] = price_info
        except Exception as e:
            error_msg = f"获取 {exchange_id} 的 {symbol} 数据时发生错误: {str(e)}"
            print(f"❌ {error_msg}")
            self.exchange_status[exchange_id] = {
                "status": "error",
                "error": error_msg,
                "timestamp": import_time.time()
            }

    def _print_ticker_info(self, exchange_id: str, market_type: str,
                           symbol: str, quote: str, price: str):
        """
        打印价格信息
        
        此方法将价格信息格式化为JSON并打印输出。价格已经通过CCXT的精度处理方法处理，
        确保符合交易所的精度要求。
        
        Args:
            exchange_id (str): 交易所ID
            market_type (str): 市场类型
            symbol (str): 交易对符号
            quote (str): 计价货币
            price (str): 已格式化的价格字符串
            
        输出格式示例：
            {
                "exchange": "binance",
                "type": "spot",
                "symbol": "BTC/USDT",
                "quote": "USDT",
                "price": "0.000009404"
            }
            
        注意：
            price参数应该已经是通过交易所的price_to_precision方法处理过的字符串
        """
        print(json.dumps({
            "exchange": exchange_id,
            "type": market_type,
            "symbol": symbol,
            "quote": quote,
            "price": price
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
        error_msg = f"监控 {exchange_id} 时发生错误: {str(error)}"
        print(f"❌ {error_msg}")
        self.exchange_status[exchange_id] = {
            "status": "error",
            "error": error_msg,
            "timestamp": import_time.time()
        }
        await exchange.close()
        try:
            await self.exchange_instance.get_ws_instance(exchange_id)
            self.exchange_status[exchange_id] = {
                "status": "connected",
                "error": None,
                "timestamp": import_time.time()
            }
        except Exception as reconnect_error:
            reconnect_error_msg = f"重新连接 {exchange_id} 失败: {str(reconnect_error)}"
            print(f"❌ {reconnect_error_msg}")
            self.exchange_status[exchange_id] = {
                "status": "reconnect_failed",
                "error": reconnect_error_msg,
                "timestamp": import_time.time()
            }

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
        self.running = True
        self.common_symbols_finder.find_common_symbols(exchanges)
        # 初始化交易所状态
        for exchange_id in exchanges:
            self.exchange_status[exchange_id] = {
                "status": "initializing",
                "error": None,
                "timestamp": import_time.time()
            }
        print("\n🔄 开始监控实时价格...")  # 保留重要的状态信息打印

    async def stop(self):
        """
        停止监控管理器
        
        此方法会：
        1. 设置运行标志为False以停止监控循环
        2. 关闭所有交易所连接
        3. 清理资源
        """
        self.running = False
        if hasattr(self, 'exchange_instance') and self.exchange_instance:
            try:
                await self.exchange_instance.close()
            except Exception as e:
                print(f"❌ 关闭交易所连接时发生错误: {str(e)}")

    async def fetch_exchange_tickers(self, exchange_id: str):
        """
        获取指定交易所的所有交易对价格数据
        
        Args:
            exchange_id (str): 交易所ID
            
        Returns:
            dict: 包含所有交易对价格信息的字典
        """
        exchange = None
        try:
            # 根据交易所ID创建对应的异步交易所实例
            if exchange_id == 'binance':
                from ccxt.async_support import binance
                exchange = binance()
            elif exchange_id == 'okx':
                from ccxt.async_support import okx
                exchange = okx()
            elif exchange_id == 'huobi':
                from ccxt.async_support import huobi
                exchange = huobi()
            elif exchange_id == 'bybit':
                from ccxt.async_support import bybit
                exchange = bybit()
            elif exchange_id == 'gateio':
                from ccxt.async_support import gateio
                exchange = gateio()
            else:
                raise Exception(f"不支持的交易所: {exchange_id}")
            
            # 设置配置
            exchange.options['defaultType'] = 'spot'
            exchange.enableRateLimit = True
            
            # 加载市场数据
            await exchange.load_markets()
            
            # 获取所有交易对的价格
            tickers = await exchange.fetch_tickers()
            return tickers
            
        except Exception as e:
            error_msg = f"获取 {exchange_id} 价格数据时发生错误: {str(e)}"
            print(f"❌ {error_msg}")
            self.exchange_status[exchange_id] = {
                "status": "error",
                "error": error_msg,
                "timestamp": import_time.time()
            }
            return None
        finally:
            # 确保在任何情况下都关闭交易所连接
            if exchange:
                try:
                    await exchange.close()
                except Exception as e:
                    print(f"❌ 关闭交易所 {exchange_id} 连接时发生错误: {str(e)}")
