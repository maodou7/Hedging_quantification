"""
交易所实例管理模块

此模块提供了统一的交易所实例管理接口，支持REST API和WebSocket连接。
它封装了ccxt和ccxt.pro库的功能，提供了更简单和统一的接口来管理不同交易所的连接。

主要功能：
1. REST API实例管理
   - 创建和获取REST API连接
   - 自动进行配置管理
   - 支持自定义配置选项

2. WebSocket实例管理
   - 创建和获取WebSocket连接
   - 自动加载市场数据
   - 支持实时数据流

3. 连接生命周期管理
   - 自动管理连接的创建和销毁
   - 提供统一的清理接口
   - 错误处理和异常管理

使用示例：
    # 创建实例
    exchange_instance = ExchangeInstance()
    
    # 获取REST API连接
    rest_api = await exchange_instance.get_rest_instance('binance')
    
    # 获取WebSocket连接
    ws_api = await exchange_instance.get_ws_instance('binance')
    
    # 使用完毕后清理
    await exchange_instance.close_all()

依赖：
- ccxt: 用于REST API连接
- ccxt.pro: 用于WebSocket连接

注意：
- WebSocket连接需要在使用完毕后手动关闭
- REST API实例可以被重用
- 所有方法都提供了适当的错误处理
"""

from typing import Dict, Optional, Any
import asyncio
import ccxt
import ccxt.pro as ccxtpro
from src.Config.exchange_config import EXCHANGE_CONFIGS
from src.utils.logger import ArbitrageLogger


class ExchangeInstance:
    """
    交易所实例管理类
    
    此类负责管理所有交易所的连接实例，包括REST API和WebSocket连接。
    它提供了一个统一的接口来创建、获取和管理这些连接。
    
    属性：
        _rest_instances (Dict[str, ccxt.Exchange]): 存储REST API实例的字典
        _ws_instances (Dict[str, ccxtpro.Exchange]): 存储WebSocket实例的字典
        _init_locks (Dict[str, asyncio.Lock]): 存储初始化锁的字典
    """
    
    def __init__(self):
        """
        初始化交易所实例管理器
        
        创建用于存储REST和WebSocket实例的字典
        """
        self.logger = ArbitrageLogger()
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self._rest_instances: Dict[str, ccxt.Exchange] = {}
        self._ws_instances: Dict[str, ccxtpro.Exchange] = {}
        self._init_locks: Dict[str, asyncio.Lock] = {}

    async def _create_rest_instance(self, exchange_id: str, config: Optional[dict] = None) -> ccxt.Exchange:
        """异步创建REST API实例"""
        try:
            default_config = {
                'enableRateLimit': True,
                'timeout': 30000,
                'options': {
                    'defaultType': 'spot'
                }
            }

            if config:
                default_config.update(config)

            exchange_class = getattr(ccxt.async_support, exchange_id)
            instance = exchange_class(default_config)
            
            # 使用异步方式加载市场数据
            await instance.load_markets()
            return instance
            
        except Exception as e:
            self.logger.error(f"获取交易所实例失败 {exchange_id}: {str(e)}")
            raise Exception(f"创建 REST 实例失败 {exchange_id}: {str(e)}")

    async def get_exchange(self, exchange_id: str, config: Optional[dict] = None) -> ccxt.Exchange:
        """获取交易所实例"""
        try:
            if exchange_id not in self._rest_instances:
                instance = await self._create_rest_instance(exchange_id, config)
                self._rest_instances[exchange_id] = instance
            return self._rest_instances[exchange_id]
        except Exception as e:
            self.logger.error(f"获取交易所实例失败 {exchange_id}: {str(e)}")
            return None

    async def get_ws_instance(self, exchange_id: str, config: Optional[dict] = None) -> ccxtpro.Exchange:
        """异步获取或创建WebSocket实例"""
        if exchange_id not in self._ws_instances:
            default_config = {
                'enableRateLimit': True,
                'timeout': 30000,
                'options': {
                    'defaultType': 'spot'
                }
            }

            if config:
                default_config.update(config)

            try:
                ws_exchange_class = getattr(ccxtpro, exchange_id)
                ws_instance = ws_exchange_class(default_config)
                await ws_instance.load_markets()
                self._ws_instances[exchange_id] = ws_instance
            except Exception as e:
                raise Exception(f"创建 WebSocket 实例失败 {exchange_id}: {str(e)}")

        return self._ws_instances[exchange_id]

    async def close_ws_instances(self):
        """关闭所有WebSocket连接"""
        close_tasks = []
        for exchange_id, instance in self._ws_instances.items():
            try:
                close_tasks.append(instance.close())
            except Exception as e:
                print(f"关闭 WebSocket 连接失败 {exchange_id}: {str(e)}")
        
        if close_tasks:
            await asyncio.gather(*close_tasks)
        self._ws_instances.clear()

    def clear_rest_instances(self):
        """清除所有REST API实例"""
        self._rest_instances.clear()
        self._init_locks.clear()

    async def close_all(self):
        """关闭所有交易所连接"""
        for exchange in self._rest_instances.values():
            try:
                await exchange.close()
            except Exception as e:
                self.logger.error(f"关闭交易所连接失败: {str(e)}")
        self._rest_instances.clear()
        self._ws_instances.clear()

    async def get_exchange_info(self, exchange_id: str) -> Dict[str, Any]:
        """获取交易所信息"""
        try:
            exchange = await self.get_exchange(exchange_id)
            return {
                'id': exchange.id,
                'name': exchange.name,
                'timeframes': exchange.timeframes,
                'has': exchange.has,
                'urls': exchange.urls,
                'version': exchange.version,
                'has_fetch_ohlcv': exchange.has['fetchOHLCV'],
                'has_fetch_order_book': exchange.has['fetchOrderBook'],
                'has_fetch_trades': exchange.has['fetchTrades']
            }
        except Exception as e:
            self.logger.error(f"获取交易所信息失败 {exchange_id}: {str(e)}")
            return {}
