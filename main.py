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
    """设置事件循环"""
    if platform.system() == 'Windows':
        selector = selectors.SelectSelector()
        loop = asyncio.SelectorEventLoop(selector)
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    # 设置aiohttp的DNS解析器
    if platform.system() == 'Windows':
        async def setup_resolver():
            resolver = aiohttp.resolver.ThreadedResolver()
            aiohttp.ClientSession._resolver = resolver
        loop.run_until_complete(setup_resolver())
        
    return loop

class MonitorSystem:
    """价格监控系统"""
    def __init__(self):
        # 初始化系统适配器
        self.system_adapter = SystemAdapter()
        self.logger = setup_logger('monitor', 'logs/monitor.log')
        self.logger.info(f"[监控进程] 系统信息: {self.system_adapter.get_system_info()}")
        
        # 初始化Redis管理器
        self.redis_manager = RedisManager()
        
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
                
            # 初始化其他组件
            self.exchange_instance = ExchangeInstance()
            self.exchange_factory = ExchangeFactory()
            self.market_structure_fetcher = MarketStructureFetcher(self.exchange_instance)
            self.cache_manager = CacheManager()
            
            # 初始化价格监控器
            self.price_monitor = PriceMonitor(
                exchange_instance=self.exchange_instance,
                cache_manager=self.cache_manager
            )
            
            # 初始化交易所连接
            for exchange_id in EXCHANGES:
                config = EXCHANGE_CONFIGS.get(exchange_id, {})
                if not await self.exchange_instance.initialize_exchange(exchange_id, config):
                    logger.error(f"[监控进程] 初始化交易所 {exchange_id} 失败")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"[监控进程] 初始化失败: {str(e)}")
            return False
            
    async def start(self):
        """启动系统"""
        if await self.initialize():
            logger.info("[监控进程] 系统初始化完成，开始运行...")
            try:
                # 启动价格监控
                await self.price_monitor.start_monitoring()
            except Exception as e:
                logger.error(f"[监控进程] 运行时错误: {str(e)}")
                await self.stop()
        else:
            logger.error("[监控进程] 系统初始化失败，无法启动")
            
    async def stop(self):
        """停止系统"""
        self.running = False
        try:
            if self.price_monitor:
                await self.price_monitor.stop_monitoring()
            if self.exchange_instance:
                await self.exchange_instance.close_all()
            if self.redis_manager:
                await self.redis_manager.cleanup()
            logger.info("[监控进程] 系统已停止")
        except Exception as e:
            logger.error(f"[监控进程] 停止时发生错误: {str(e)}")

def run_monitor(stop_event: Event):
    """运行监控进程"""
    monitor_logger = setup_logger('monitor', 'logs/monitor.log')
    try:
        # 设置事件循环
        loop = setup_event_loop()
        
        async def run():
            monitor = MonitorSystem()
            try:
                await monitor.start()
                while not stop_event.is_set() and monitor.running:
                    await asyncio.sleep(1)
            except Exception as e:
                monitor_logger.error(f"[监控进程] 运行时错误: {str(e)}")
            finally:
                try:
                    await monitor.stop()
                except Exception as e:
                    monitor_logger.error(f"[监控进程] 停止时发生错误: {str(e)}")
                finally:
                    # 确保所有资源都被清理
                    if hasattr(monitor, 'exchange_instance') and monitor.exchange_instance:
                        try:
                            await monitor.exchange_instance.close_all()
                        except Exception as e:
                            monitor_logger.error(f"[监控进程] 关闭交易所实例时发生错误: {str(e)}")
                    
                    if hasattr(monitor, 'redis_manager') and monitor.redis_manager:
                        try:
                            await monitor.redis_manager.cleanup()
                        except Exception as e:
                            monitor_logger.error(f"[监控进程] 关闭Redis连接时发生错误: {str(e)}")
                
        loop.run_until_complete(run())
    except Exception as e:
        monitor_logger.error(f"[监控进程] 致命错误: {str(e)}")
    finally:
        try:
            pending = asyncio.all_tasks(loop)
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception as e:
            monitor_logger.error(f"[监控进程] 清理事件循环时发生错误: {str(e)}")
        finally:
            loop.close()

def run_api_server():
    """运行API服务器"""
    api_logger = setup_logger('api', 'logs/api.log')
    try:
        uvicorn.run(
            "src.api.api_server:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_config=None,  # 禁用uvicorn的默认日志配置
            access_log=False  # 禁用访问日志
        )
    except Exception as e:
        api_logger.error(f"[API进程] 运行时错误: {str(e)}")

async def main():
    """主函数"""
    try:
        # 创建停止事件
        stop_event = Event()
        
        # 启动监控进程
        monitor_process = Process(target=run_monitor, args=(stop_event,))
        monitor_process.start()
        logger.info("[主进程] 监控进程已启动")
        
        # 启动API服务器进程
        api_process = Process(target=run_api_server)
        api_process.start()
        logger.info("[主进程] API服务器进程已启动")
        
        # 等待中断信号
        def signal_handler(signum, frame):
            logger.info("\n[主进程] 收到停止信号，正在关闭系统...")
            stop_event.set()
            monitor_process.join(timeout=5)
            api_process.terminate()
            api_process.join(timeout=5)
            
            # 强制终止未能正常退出的进程
            if monitor_process.is_alive():
                monitor_process.terminate()
            if api_process.is_alive():
                api_process.kill()
                
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 保持主进程运行并监控子进程状态
        while True:
            if not monitor_process.is_alive():
                logger.error("[主进程] 监控进程异常退出")
                api_process.terminate()
                sys.exit(1)
            if not api_process.is_alive():
                logger.error("[主进程] API服务器进程异常退出")
                stop_event.set()
                monitor_process.join()
                sys.exit(1)
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"[主进程] 运行时错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # 设置事件循环
    loop = setup_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("\n程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {str(e)}")
    finally:
        loop.close()
