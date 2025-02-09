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

import os
import asyncio
import aiohttp
from typing import Dict, Optional, Any, List
import ccxt
import ccxt.pro as ccxtpro
from src.config.exchange import EXCHANGE_CONFIGS
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
        _sessions (Dict[str, aiohttp.ClientSession]): 存储HTTP会话的字典
        _max_retries (int): 最大重试次数
        _retry_delay (int): 重试延迟时间（秒）
        _ws_timeout (int): WebSocket超时时间（秒）
        _rest_timeout (int): REST API超时时间（秒）
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
        self._sessions: Dict[str, aiohttp.ClientSession] = {}
        self._max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self._retry_delay = int(os.getenv('RETRY_DELAY', '5'))
        self._ws_timeout = int(os.getenv('WEBSOCKET_TIMEOUT', '30'))
        self._rest_timeout = int(os.getenv('REST_TIMEOUT', '10'))

    async def initialize_exchange(self, exchange_id: str, config: Optional[dict] = None) -> bool:
        """初始化交易所连接"""
        try:
            # 获取或创建初始化锁
            if exchange_id not in self._init_locks:
                self._init_locks[exchange_id] = asyncio.Lock()
            
            async with self._init_locks[exchange_id]:
                # 获取REST API实例
                rest_instance = await self.get_exchange(exchange_id, config)
                if not rest_instance:
                    self.logger.error(f"[交易所] 初始化REST API失败: {exchange_id}")
                    return False
                    
                # 加载市场数据
                for retry in range(self._max_retries):
                    try:
                        self.logger.info(f"[交易所] {exchange_id} 正在加载市场数据 (尝试 {retry + 1}/{self._max_retries})")
                        await rest_instance.load_markets(reload=True)  # 强制重新加载
                        self.logger.info(f"[交易所] {exchange_id} REST API初始化成功")
                        break
                    except Exception as e:
                        error_msg = str(e)
                        if any(msg in error_msg.lower() for msg in ["api", "key", "auth", "permission"]):
                            self.logger.warning(f"[交易所] {exchange_id} API认证相关错误，将使用公共API模式")
                            # 重置实例配置为公共模式
                            rest_instance.apiKey = None
                            rest_instance.secret = None
                            rest_instance.password = None
                            try:
                                await rest_instance.load_markets(reload=True)
                                self.logger.info(f"[交易所] {exchange_id} 使用公共API模式初始化成功")
                                break
                            except Exception as e2:
                                if retry == self._max_retries - 1:
                                    self.logger.error(f"[交易所] {exchange_id} 公共API模式加载失败: {str(e2)}")
                                    return False
                        elif retry == self._max_retries - 1:
                            self.logger.error(f"[交易所] {exchange_id} 加载市场数据失败: {error_msg}")
                            return False
                        self.logger.warning(f"[交易所] {exchange_id} 加载市场数据失败，将在 {self._retry_delay} 秒后重试: {error_msg}")
                        await asyncio.sleep(self._retry_delay)
                
                # 获取WebSocket实例（可选）
                try:
                    ws_instance = await self.get_ws_instance(exchange_id, config)
                    if ws_instance:
                        self.logger.info(f"[交易所] {exchange_id} WebSocket初始化成功")
                except Exception as e:
                    self.logger.warning(f"[交易所] {exchange_id} WebSocket初始化失败: {str(e)}")
                    # WebSocket失败不影响整体初始化
                
                return True
        except Exception as e:
            self.logger.error(f"[交易所] 初始化失败 {exchange_id}: {str(e)}")
            return False
        finally:
            # 清理不需要的锁
            if exchange_id in self._init_locks:
                del self._init_locks[exchange_id]

    async def _create_rest_instance(self, exchange_id: str, config: Optional[dict] = None) -> ccxt.Exchange:
        """异步创建REST API实例"""
        try:
            default_config = {
                'enableRateLimit': True,
                'timeout': self._rest_timeout * 1000,  # 转换为毫秒
                'options': {
                    'defaultType': 'spot',
                    'test': True,
                    'adjustForTimeDifference': True,
                    'createMarketBuyOrderRequiresPrice': False
                }
            }

            if config:
                # 深度合并配置
                default_config = self._deep_merge(default_config, config)

            # 创建HTTP会话
            if exchange_id not in self._sessions:
                connector = aiohttp.TCPConnector(ssl=False, force_close=True)
                self._sessions[exchange_id] = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self._rest_timeout),
                    connector=connector,
                    trust_env=True
                )

            exchange_class = getattr(ccxt.async_support, exchange_id)
            instance = exchange_class({
                **default_config,
                'session': self._sessions[exchange_id]
            })
            
            # 设置属性
            instance.enableRateLimit = True
            instance.timeout = self._rest_timeout * 1000
            instance.options['test'] = True
            
            return instance
            
        except Exception as e:
            self.logger.error(f"创建REST实例失败 {exchange_id}: {str(e)}")
            return None

    def _deep_merge(self, dict1: dict, dict2: dict) -> dict:
        """深度合并两个字典"""
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    async def get_exchange(self, exchange_id: str, config: Optional[dict] = None) -> Optional[ccxt.Exchange]:
        """获取交易所实例"""
        try:
            if exchange_id not in self._rest_instances:
                instance = await self._create_rest_instance(exchange_id, config)
                self._rest_instances[exchange_id] = instance
            return self._rest_instances[exchange_id]
        except Exception as e:
            self.logger.error(f"获取交易所实例失败 {exchange_id}: {str(e)}")
            return None

    async def get_ws_instance(self, exchange_id: str, config: Optional[dict] = None) -> Optional[ccxtpro.Exchange]:
        """异步获取或创建WebSocket实例"""
        try:
            if exchange_id not in self._ws_instances:
                default_config = {
                    'enableRateLimit': True,
                    'timeout': self._ws_timeout * 1000,  # 转换为毫秒
                    'options': {
                        'defaultType': 'spot',
                        'ws': {
                            'timeout': self._ws_timeout * 1000
                        }
                    }
                }

                if config:
                    default_config = self._deep_merge(default_config, config)

                ws_exchange_class = getattr(ccxtpro, exchange_id)
                ws_instance = ws_exchange_class(default_config)
                
                # 加载市场数据
                for retry in range(self._max_retries):
                    try:
                        await ws_instance.load_markets()
                        break
                    except Exception as e:
                        if retry == self._max_retries - 1:
                            raise Exception(f"加载WebSocket市场数据失败: {str(e)}")
                        await asyncio.sleep(self._retry_delay)
                
                self._ws_instances[exchange_id] = ws_instance

            return self._ws_instances[exchange_id]
        except Exception as e:
            self.logger.error(f"创建WebSocket实例失败 {exchange_id}: {str(e)}")
            return None

    async def close_ws_instances(self):
        """关闭所有WebSocket连接"""
        close_tasks = []
        for exchange_id, instance in self._ws_instances.items():
            try:
                close_tasks.append(instance.close())
            except Exception as e:
                self.logger.error(f"关闭WebSocket连接失败 {exchange_id}: {str(e)}")
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        self._ws_instances.clear()

    async def close_rest_instances(self):
        """关闭所有REST API实例"""
        for exchange_id, instance in self._rest_instances.items():
            try:
                await instance.close()
            except Exception as e:
                self.logger.error(f"关闭REST API实例失败 {exchange_id}: {str(e)}")
        
        # 关闭HTTP会话
        for session in self._sessions.values():
            try:
                await session.close()
            except Exception as e:
                self.logger.error(f"关闭HTTP会话失败: {str(e)}")
        
        self._rest_instances.clear()
        self._sessions.clear()
        self._init_locks.clear()

    async def close_all(self):
        """关闭所有连接"""
        await self.close_ws_instances()
        await self.close_rest_instances()

    async def get_exchange_info(self, exchange_id: str) -> Dict[str, Any]:
        """获取交易所信息"""
        try:
            exchange = await self.get_exchange(exchange_id)
            if not exchange:
                return {}
                
            return {
                'id': exchange.id,
                'name': exchange.name,
                'timeframes': exchange.timeframes,
                'has': exchange.has,
                'urls': exchange.urls,
                'version': exchange.version,
                'has_fetch_ohlcv': exchange.has.get('fetchOHLCV', False),
                'has_fetch_order_book': exchange.has.get('fetchOrderBook', False),
                'has_fetch_trades': exchange.has.get('fetchTrades', False),
                'test_mode': exchange.options.get('test', False)
            }
        except Exception as e:
            self.logger.error(f"获取交易所信息失败 {exchange_id}: {str(e)}")
            return {}
