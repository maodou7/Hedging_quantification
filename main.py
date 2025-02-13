"""
交易所价格监控与套利主程序

此程序负责：
1. 监控多个交易所的价格数据（监控进程）
2. 实时分析套利机会（主进程）
3. 执行套利交易（主进程）
4. 提供API服务（API进程）
"""
# TODO: 将监控系统放在另一个进程运行，主进程运行价差套利系统，买卖逻辑优先
import os
import asyncio
import signal
import sys
import platform
from typing import Dict, List, Any
from datetime import datetime
import multiprocessing
from multiprocessing import Process, Event, shared_memory
import uvicorn
import sys
import platform
import logging
import aiohttp
import aiohttp.resolver
import redis.asyncio as redis
from src.core.redis_manager import RedisManager
from src.utils.system_adapter import SystemAdapter
import selectors
from src.utils.logger_config import setup_logger

# Windows系统下使用selector事件循环
if platform.system() == 'Windows':
    import asyncio
    import selectors
    selector = selectors.SelectSelector()
    loop = asyncio.SelectorEventLoop(selector)
    asyncio.set_event_loop(loop)

from src.exchange.exchange_instance import ExchangeInstance
from src.exchange.market_structure_fetcher import MarketStructureFetcher
from src.exchange.price_monitor import PriceMonitor
from src.core.cache_manager import CacheManager
from src.config.exchange import (
    EXCHANGES,
    QUOTE_CURRENCIES,
    MARKET_TYPES,
    COMMON_SYMBOLS,
    EXCHANGE_CONFIGS,
    SYMBOLS
)
from src.config.monitoring import MONITOR_CONFIG, MARKET_STRUCTURE_CONFIG
from src.config.cache import CACHE_CONFIG
from src.utils.system_adapter import SystemAdapter
from src.exchange.exchange_factory import ExchangeFactory
from src.strategies.spread_arbitrage_strategy import SpreadArbitrageStrategy
from src.utils.logger import ArbitrageLogger
from src.api.api_server import app
from src.core.communication_manager import create_communication_manager

# 配置日志
os.makedirs('logs', exist_ok=True)
logger = setup_logger('main', 'logs/arbitrage.log')

# 禁用所有第三方库的默认日志
for log_name in ['uvicorn', 'asyncio', 'aiohttp', 'multiprocessing', 'concurrent', 'urllib3']:
    third_party_logger = logging.getLogger(log_name)
    third_party_logger.handlers = []
    third_party_logger.propagate = False
    if log_name == 'uvicorn.error':
        third_party_logger.addHandler(logging.NullHandler())

def setup_event_loop():
    """设置事件循环（跨平台兼容版）"""
    try:
        if platform.system() != 'Windows':
            import uvloop
            uvloop.install()
    except ImportError:
        pass  # 非Windows系统但未安装uvloop时继续使用默认循环
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Loop is closed")
    except (RuntimeError, AttributeError):
        if platform.system() == 'Windows':
            loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
        else:
            try:
                import uvloop
                loop = uvloop.new_event_loop()
            except ImportError:
                loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    # Windows平台优化配置
    if platform.system() == 'Windows':
        # 设置aiohttp的DNS解析器
        async def setup_resolver():
            aiohttp.ClientSession._resolver = aiohttp.resolver.ThreadedResolver()
        loop.run_until_complete(setup_resolver())
        
    return loop

class MonitorSystem:
    """价格监控系统"""
    def __init__(self):
        # 初始化系统适配器
        self.system_adapter = SystemAdapter()
        self.logger = setup_logger('monitor', 'logs/monitor.log')
        self.logger.info(f"[监控进程] 系统信息: {self.system_adapter.get_system_info()}")
        
        # 初始化连接池
        self.redis_manager = RedisManager()
        self.http_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=20),
            timeout=aiohttp.ClientTimeout(total=30)
        )
        self.ws_conn_pool = {}
        
        # 初始化基础组件
        self.exchange_instance = None
        self.exchange_factory = None
        self.market_structure_fetcher = None
        self.cache_manager = None
        self.price_monitor = None
        
        # 运行标志
        self.running = True
        
    async def initialize(self):
        """初始化系统"""
        try:
            # 初始化Redis连接
            if not await self.redis_manager.initialize():
                logger.error("[监控进程] Redis连接失败")
                return False
            
            # 构建交易所实例配置
            exchange_config = {
                'exchanges': EXCHANGES,
                'use_redis': True,
                'redis_url': self.redis_manager.get_redis_url(),
                'rest_timeout': 30000,
                'ws_timeout': 30000,
                'max_rest_pool_size': 10,
                'max_ws_pool_size': 5,
                'health_check_interval': 60
            }
                
            # 初始化其他组件
            self.exchange_instance = ExchangeInstance(exchange_config)
            try:
                await self.exchange_instance.initialize_all_connections()
                if not self.exchange_instance.is_connected():
                    logger.error("[监控进程] 交易所连接初始化失败")
                    return False
                if not await self.redis_manager.initialize():
                    logger.error("[监控进程] Redis连接失败")
                    return False
            except Exception as e:
                logger.error(f"[监控进程] 初始化过程发生错误: {str(e)}")
                return False

            self.exchange_factory = ExchangeFactory()
            self.market_structure_fetcher = MarketStructureFetcher(self.exchange_instance)
            self.cache_manager = CacheManager()
            self.price_monitor = PriceMonitor(exchange_instance=self.exchange_instance)
            for exchange_id in EXCHANGES:
                self.price_monitor.add_symbols(exchange_id, SYMBOLS)
            return True
        except Exception as e:
            logger.error(f"[监控进程] 初始化系统时发生错误: {str(e)}")
            return False

    async def stop(self):
        if self.running:
            self.running = False
        try:
            # Parallelly close all resources
            close_tasks = []
            if self.price_monitor:
                close_tasks.append(self.price_monitor.stop_monitoring())
            if self.exchange_instance:
                close_tasks.append(self.exchange_instance.close_all_connections())
            if close_tasks:
                await asyncio.gather(*close_tasks)
        except Exception as e:
            logger.error(f"[监控进程] 停止时发生错误: {str(e)}")
        finally:
            # Ensure all resources are cleared
            if hasattr(self, 'exchange_instance') and self.exchange_instance:
                try:
                    await self.exchange_instance.close_all_connections()
                except Exception as e:
                    logger.error(f"[监控进程] 关闭交易所实例时发生错误: {str(e)}")
