"""
交易所实例管理模块（优化版）

此模块提供交易所连接的完整生命周期管理，支持连接池和健康检查。
主要优化点：
1. REST和WebSocket连接池管理
2. 异步连接健康检查
3. Redis连接池集成
4. 智能重连机制
5. 并发控制
"""

import os
import asyncio
import aiohttp
from typing import Dict, Optional, Any, List, Deque, Set
from collections import defaultdict, deque
import ccxt
import ccxt.pro as ccxtpro
import redis.asyncio as redis
from src.config.exchange import (
    EXCHANGE_CONFIGS, 
    MARKET_TYPES, 
    EXCHANGE_SYMBOLS, 
    QUOTE_CURRENCIES, 
    get_exchange_config
)
from src.utils.logger import ArbitrageLogger

class ExchangeInstance:
    """交易所实例管理类（优化版）"""
    
    def __init__(self, config: dict):
        """初始化交易所实例管理器"""
        self._config = config
        self._rest_instances: Dict[str, ccxt.Exchange] = {}
        self._ws_instances: Dict[str, ccxtpro.Exchange] = {}
        self.logger = ArbitrageLogger()
        self._redis_pool = None
        self._initialized = False
        self._rest_pools: Dict[str, Deque[ccxt.Exchange]] = defaultdict(deque)
        self._ws_pools: Dict[str, Deque[ccxtpro.Exchange]] = defaultdict(deque)
        self._pool_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._health_check_task: Optional[asyncio.Task] = None
        self._symbol_cache: Dict[str, Dict[str, bool]] = defaultdict(dict)

    def _convert_symbol_format(self, exchange_id: str, symbol: str) -> str:
        """转换交易对格式为交易所特定格式"""
        try:
            # 获取交易所支持的交易对格式
            exchange_format = EXCHANGE_SYMBOLS.get(exchange_id, [])
            if not exchange_format:
                return symbol

            # 解析基础货币和计价货币
            if '/' in symbol:
                base, quote = symbol.split('/')
            elif '-' in symbol:
                base, quote = symbol.split('-')
            elif '_' in symbol:
                base, quote = symbol.split('_')
            else:
                # 假设是无分隔符的格式
                for q in QUOTE_CURRENCIES:
                    if symbol.upper().endswith(q):
                        quote_len = len(q)
                        base = symbol[:-quote_len]
                        quote = symbol[-quote_len:]
                        break
                else:
                    return symbol

            # 根据交易所格式转换
            if exchange_id == 'huobi':
                return f"{base.lower()}{quote.lower()}"
            elif exchange_id == 'okx':
                return f"{base}-{quote}"
            elif exchange_id == 'gateio':
                return f"{base}_{quote}"
            else:  # binance, bybit等使用标准格式
                return f"{base}/{quote}"

        except Exception as e:
            self.logger.debug(f"交易对格式转换失败 {exchange_id} {symbol}: {str(e)}")
            return symbol

    def symbol_exists(self, exchange_id: str, symbol: str) -> bool:
        """检查交易对是否存在（支持自动格式转换）"""
        try:
            # 检查缓存
            cache_key = f"{exchange_id}:{symbol}"
            if cache_key in self._symbol_cache:
                return self._symbol_cache[cache_key]

            if not self._rest_pools.get(exchange_id):
                return False
            
            instance = self._rest_pools[exchange_id][0]
            
            # 转换为交易所特定格式
            exchange_symbol = self._convert_symbol_format(exchange_id, symbol)
            
            try:
                # 尝试直接获取市场信息
                market = instance.market(exchange_symbol)
                is_valid = (market.get('active', False) and 
                          market.get('quote') in QUOTE_CURRENCIES and
                          market.get('spot', False))
            except ccxt.BadSymbol:
                # 如果失败，尝试在所有市场中查找
                markets = instance.markets or {}
                market = None
                for m_symbol, m_info in markets.items():
                    if (m_symbol.replace('-', '/').replace('_', '/').upper() == 
                        symbol.replace('-', '/').replace('_', '/').upper()):
                        market = m_info
                        break
                is_valid = (market is not None and 
                          market.get('active', False) and
                          market.get('quote') in QUOTE_CURRENCIES and
                          market.get('spot', False))

            # 更新缓存
            self._symbol_cache[cache_key] = is_valid
            return is_valid
            
        except Exception as e:
            self.logger.error(f"交易对检查异常 {exchange_id} {symbol}: {str(e)}")
            return False

    async def initialize_all_connections(self) -> bool:
        """初始化所有交易所连接"""
        try:
            # 初始化Redis连接池
            if self._config.get('use_redis', True):
                self._redis_pool = await redis.from_url(
                    self._config['redis_url'],
                    encoding='utf-8',
                    decode_responses=True,
                    max_connections=20
                )
            
            # 初始化交易所连接
            for exchange_id in self._config['exchanges']:
                if not await self._create_exchange_connections(exchange_id):
                    return False
            
            self._initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"初始化连接失败: {str(e)}")
            return False
    
    async def _create_exchange_connections(self, exchange_id: str) -> bool:
        """创建交易所的REST和WebSocket连接"""
        try:
            # 创建REST实例
            rest_instance = await self._create_rest_instance(exchange_id, self._config)
            if not rest_instance:
                return False
            self._rest_instances[exchange_id] = rest_instance
            
            # 创建WebSocket实例
            ws_instance = await self._create_ws_instance(exchange_id, self._config)
            if not ws_instance:
                return False
            self._ws_instances[exchange_id] = ws_instance
            
            return True
            
        except Exception as e:
            self.logger.error(f"创建{exchange_id}连接失败: {str(e)}")
            return False
    
    async def _create_rest_instance(self, exchange_id: str, config: dict) -> Optional[ccxt.Exchange]:
        """创建REST API实例"""
        try:
            exchange_config = get_exchange_config(exchange_id)
            
            exchange_class = getattr(ccxt.async_support, exchange_id)
            instance = exchange_class({
                'enableRateLimit': True,
                'timeout': config.get('rest_timeout', 30000),
                **exchange_config
            })
            
            # 加载市场数据
            await instance.load_markets()
            
            # 验证配置中的交易对是否有效
            valid_symbols = []
            for symbol in instance.markets:
                market = instance.markets[symbol]
                if (market.get('active') and 
                    market.get('quote') in QUOTE_CURRENCIES and
                    market.get('spot', False)):  # 只验证现货交易对
                    valid_symbols.append(symbol)
            
            if not valid_symbols:
                self.logger.warning(f"{exchange_id} 配置中无有效交易对")
                return None
            
            return instance
            
        except Exception as e:
            self.logger.error(f"创建REST实例失败 {exchange_id}: {str(e)}")
            return None
    
    async def _create_ws_instance(self, exchange_id: str, config: dict) -> Optional[ccxtpro.Exchange]:
        """创建WebSocket实例"""
        try:
            exchange_config = get_exchange_config(exchange_id)
            
            exchange_class = getattr(ccxtpro, exchange_id)
            instance = exchange_class({
                'enableRateLimit': True,
                'timeout': config.get('ws_timeout', 30000),
                **exchange_config
            })
            
            await instance.load_markets()
            return instance
            
        except Exception as e:
            self.logger.error(f"创建WS实例失败 {exchange_id}: {str(e)}")
            return None
    
    async def get_rest_instance(self, exchange_id: str) -> Optional[ccxt.Exchange]:
        """获取REST API实例"""
        return self._rest_instances.get(exchange_id)
    
    async def get_ws_instance(self, exchange_id: str) -> Optional[ccxtpro.Exchange]:
        """获取WebSocket实例"""
        return self._ws_instances.get(exchange_id)
    
    async def reset_ws_connection(self, exchange_id: str):
        """重置WebSocket连接"""
        if exchange_id in self._ws_instances:
            try:
                await self._ws_instances[exchange_id].close()
            except Exception:
                pass
            self._ws_instances[exchange_id] = await self._create_ws_instance(exchange_id, self._config)
    
    async def close_all_connections(self):
        """关闭所有连接"""
        try:
            # 关闭健康检查任务
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
                
            # 关闭REST连接池
            for exchange_id in list(self._rest_pools.keys()):
                async with self._pool_locks[exchange_id]:
                    while self._rest_pools[exchange_id]:
                        instance = self._rest_pools[exchange_id].pop()
                        try:
                            # 关闭client session
                            if hasattr(instance, 'session') and instance.session:
                                await instance.session.close()
                            # 关闭exchange实例
                            await instance.close()
                        except Exception as e:
                            self.logger.warning(f"关闭REST连接失败 {exchange_id}: {str(e)}")
                    
            # 关闭WebSocket连接池
            for exchange_id in list(self._ws_pools.keys()):
                async with self._pool_locks[exchange_id]:
                    while self._ws_pools[exchange_id]:
                        instance = self._ws_pools[exchange_id].pop()
                        try:
                            # 关闭client session
                            if hasattr(instance, 'session') and instance.session:
                                await instance.session.close()
                            # 关闭exchange实例
                            await instance.close()
                        except Exception as e:
                            self.logger.warning(f"关闭WebSocket连接失败 {exchange_id}: {str(e)}")
                    
            # 关闭Redis连接池
            if self._redis_pool:
                try:
                    await self._redis_pool.close()
                    # 新版redis-py不再需要wait_closed
                except Exception as e:
                    self.logger.warning(f"关闭Redis连接池失败: {str(e)}")
            
            # 清理资源
            self._rest_pools.clear()
            self._ws_pools.clear()
            self._pool_locks.clear()
            self._symbol_cache.clear()
            self._initialized = False
            
            self.logger.info("所有连接已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭连接时发生错误: {str(e)}")
            raise

    async def cleanup(self):
        """清理所有资源（包括连接池和缓存）"""
        try:
            # 关闭所有连接
            await self.close_all_connections()
            
            # 清理其他资源
            for instance in self._rest_instances.values():
                try:
                    if hasattr(instance, 'session') and instance.session:
                        await instance.session.close()
                    await instance.close()
                except Exception:
                    pass
            self._rest_instances.clear()
            
            for instance in self._ws_instances.values():
                try:
                    if hasattr(instance, 'session') and instance.session:
                        await instance.session.close()
                    await instance.close()
                except Exception:
                    pass
            self._ws_instances.clear()
            
            self._redis_pool = None
            
            # 重置状态
            self._initialized = False
            self._health_check_task = None
            
            self.logger.info("资源清理完成")
            
        except Exception as e:
            self.logger.error(f"资源清理失败: {str(e)}")
            raise

    async def __aenter__(self):
        """异步上下文管理器入口"""
        if not self._initialized:
            await self.initialize_all_connections()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()

    async def check_connection(self, exchange_id: str) -> bool:
        """检查交易所连接状态"""
        try:
            instance = self._rest_instances.get(exchange_id)
            if not instance:
                return False
            
            # 尝试获取服务器时间来测试连接
            await instance.fetch_time()
            return True
            
        except Exception:
            return False

    async def initialize_exchange(self, exchange_id: str, config: dict) -> bool:
        """初始化指定交易所连接
        Args:
            exchange_id (str): 交易所ID (如binance, okx)
            config (dict): 交易所配置参数
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 验证基本配置
            if not config:
                self.logger.error(f"{exchange_id} 缺少配置信息")
                return False

            # 验证API配置
            if not self._validate_api_config(exchange_id, config):
                return False

            # 初始化连接池
            await self._init_exchange_pool(exchange_id)
            
            # 执行健康检查
            if not await self.check_connection(exchange_id):
                self.logger.error(f"{exchange_id} 初始化失败：健康检查未通过")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"初始化交易所 {exchange_id} 失败: {str(e)}")
            return False

    def _validate_api_config(self, exchange_id: str, config: dict) -> bool:
        """验证API配置
        Args:
            exchange_id (str): 交易所ID
            config (dict): 配置信息
        Returns:
            bool: 配置是否有效
        """
        # 检查必要的API配置
        required_keys = ['apiKey', 'secret']
        if exchange_id == 'okx':  # OKX需要额外的密码
            required_keys.append('password')
            
        missing_keys = [key for key in required_keys if not config.get(key)]
        if missing_keys:
            self.logger.error(f"{exchange_id} 缺少必要的API配置: {', '.join(missing_keys)}")
            return False
            
        # 验证API密钥格式
        if not self._validate_api_key_format(config['apiKey']):
            self.logger.error(f"{exchange_id} API密钥格式无效")
            return False
            
        if not self._validate_api_secret_format(config['secret']):
            self.logger.error(f"{exchange_id} API密钥密文格式无效")
            return False
            
        # 验证特定交易所的额外配置
        if exchange_id == 'okx' and not self._validate_api_password_format(config['password']):
            self.logger.error(f"{exchange_id} API密码格式无效")
            return False
            
        return True
        
    def _validate_api_key_format(self, api_key: str) -> bool:
        """验证API密钥格式"""
        if not api_key or not isinstance(api_key, str):
            return False
        # 大多数交易所的API密钥长度在32-64个字符之间
        return 32 <= len(api_key) <= 64 and api_key.strip() == api_key
        
    def _validate_api_secret_format(self, secret: str) -> bool:
        """验证API密钥密文格式"""
        if not secret or not isinstance(secret, str):
            return False
        # 大多数交易所的密钥密文长度在32-64个字符之间
        return 32 <= len(secret) <= 64 and secret.strip() == secret
        
    def _validate_api_password_format(self, password: str) -> bool:
        """验证API密码格式（仅OKX需要）"""
        if not password or not isinstance(password, str):
            return False
        # OKX的API密码通常是8-32个字符
        return 8 <= len(password) <= 32 and password.strip() == password

    async def _init_exchange_pool(self, exchange_id: str):
        """初始化交易所连接池"""
        config = EXCHANGE_CONFIGS.get(exchange_id, {})
        
        # 初始化REST连接池
        async with self._pool_locks[exchange_id]:
            for _ in range(self._config['max_rest_pool_size']):
                instance = await self._create_rest_instance(exchange_id, config)
                if instance:
                    self._rest_pools[exchange_id].append(instance)
                    
        # 初始化WebSocket连接池
        async with self._pool_locks[exchange_id]:
            for _ in range(self._config['max_ws_pool_size']):
                instance = await self._create_ws_instance(exchange_id, config)
                if instance:
                    self._ws_pools[exchange_id].append(instance)

    async def release_rest_instance(self, exchange_id: str, instance: ccxt.Exchange):
        """释放REST实例到连接池"""
        async with self._pool_locks[exchange_id]:
            if len(self._rest_pools[exchange_id]) < self._config['max_rest_pool_size']:
                self._rest_pools[exchange_id].append(instance)

    async def release_ws_instance(self, exchange_id: str, instance: ccxtpro.Exchange):
        """释放WebSocket实例到连接池"""
        async with self._pool_locks[exchange_id]:
            if len(self._ws_pools[exchange_id]) < self._config['max_ws_pool_size']:
                self._ws_pools[exchange_id].append(instance)

    async def _run_health_checks(self):
        """定期执行健康检查"""
        while True:
            self.logger.info("开始连接健康检查...")
            for exchange_id in EXCHANGE_CONFIGS:
                if not await self.check_connection(exchange_id):
                    self.logger.warning(f"{exchange_id} 连接异常，尝试重置...")
                    await self.reset_ws_connection(exchange_id)
            await asyncio.sleep(self._config['health_check_interval'])

    @property
    def redis_pool(self) -> Optional[redis.Redis]:
        """获取Redis连接池"""
        return self._redis_pool
