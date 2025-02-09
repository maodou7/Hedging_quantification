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
import uvicorn
import sys
import platform
from multiprocessing import Process, Event

# Windows系统特殊处理
if platform.system() == 'Windows':
    import asyncio
    import aiohttp.resolver
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from src.exchange.exchange_instance import ExchangeInstance
from src.exchange.market_structure_fetcher import MarketStructureFetcher
from src.exchange.price_monitor import PriceMonitor
from src.core.cache_manager import CacheManager
from src.core.redis_manager import RedisManager
from src.Config.exchange_config import (
    EXCHANGES,
    QUOTE_CURRENCIES,
    MARKET_TYPES,
    CACHE_MODE,
    MONITOR_CONFIG,
    REDIS_CONFIG,
    MARKET_STRUCTURE_CONFIG,
    COMMON_SYMBOLS,
    EXCHANGE_CONFIGS,
    SYMBOLS
)
from src.utils.system_adapter import SystemAdapter
from src.exchange.exchange_factory import ExchangeFactory
from src.strategies.spread_arbitrage_strategy import SpreadArbitrageStrategy
from src.utils.logger import ArbitrageLogger
from src.api.api_server import app
from src.core.communication_manager import create_communication_manager

class MonitorSystem:
    """价格监控系统"""
    def __init__(self):
        # 初始化系统适配器
        self.system_adapter = SystemAdapter()
        
        # 初始化基础组件
        self.exchange_instance = ExchangeInstance()
        self.exchange_factory = ExchangeFactory()
        self.logger = ArbitrageLogger()
        
        # 初始化依赖组件
        self.market_structure_fetcher = MarketStructureFetcher(self.exchange_instance)
        self.cache_manager = CacheManager()
        
        # 初始化价格监控器
        self.price_monitor = None
        
        # 初始化通信管理器
        self.comm_manager = create_communication_manager()
        
    async def _init_exchange(self, exchange_id: str):
        """初始化单个交易所"""
        print(f"[监控进程] 初始化交易所 {exchange_id}...")
        try:
            config = EXCHANGE_CONFIGS.get(exchange_id, {})
            exchange = await self.exchange_instance.get_exchange(exchange_id, config)
            if not exchange:
                print(f"[监控进程] 初始化 {exchange_id} 失败: 无法创建交易所实例")
                return False
            return True
        except Exception as e:
            print(f"[监控进程] 初始化 {exchange_id} 失败: {str(e)}")
            return False
            
    async def _fetch_market_structure(self, exchange_id: str):
        """获取市场结构"""
        print(f"[监控进程] 获取 {exchange_id} 市场结构...")
        try:
            await self.market_structure_fetcher.fetch_market_structure(exchange_id)
            print(f"[监控进程] {exchange_id} 市场结构获取成功")
            return True
        except Exception as e:
            print(f"[监控进程] 获取 {exchange_id} 市场结构失败: {str(e)}")
            return False
            
    async def initialize(self):
        """初始化系统"""
        print("\n[监控进程] 正在初始化监控系统...")
        
        # 初始化交易所连接
        for exchange_id in EXCHANGES:
            await self._init_exchange(exchange_id)
            await self._fetch_market_structure(exchange_id)
        
        try:
            # 初始化价格监控器
            self.price_monitor = PriceMonitor(
                exchange_instance=self.exchange_instance,
                cache_manager=self.cache_manager
            )
            
            # 设置价格更新回调
            self.price_monitor.set_price_update_callback(self._on_price_update)
            
            # 订阅系统命令
            self.comm_manager.subscribe_command(self._handle_command)
            
            return True
        except Exception as e:
            print(f"[监控进程] 系统启动失败: {str(e)}")
            return False
            
    async def _on_price_update(self, price_data: Dict[str, Any]):
        """价格更新回调"""
        try:
            # 通过通信管理器发布价格数据
            self.comm_manager.publish_price(price_data)
        except Exception as e:
            self.logger.error(f"[监控进程] 处理价格更新失败: {str(e)}")
            
    def _handle_command(self, command: str, data: Dict[str, Any]):
        """处理系统命令"""
        print(f"[监控进程] 收到命令: {command}, 数据: {data}")
        if command == "stop":
            self.stop_event.set()
            
    async def start(self):
        """启动系统"""
        if await self.initialize():
            print("\n[监控进程] 系统初始化完成，开始运行...")
            # 启动通信管理器监听
            asyncio.create_task(self.comm_manager.start_listening())
            # 启动价格监控
            await self.price_monitor.start_monitoring()
        else:
            print("\n[监控进程] 系统初始化失败，无法启动")
            
    async def stop(self):
        """停止系统"""
        if self.price_monitor:
            await self.price_monitor.stop_monitoring()
        await self.exchange_instance.close_all()
        self.comm_manager.stop_listening()
        print("\n[监控进程] 系统已停止")

class TradingSystem:
    """交易系统"""
    def __init__(self):
        # 初始化系统适配器
        self.system_adapter = SystemAdapter()
        print("[主进程] 系统信息:", self.system_adapter.get_system_info())
        
        # 设置事件循环
        self.system_adapter.setup_event_loop()
        
        # 初始化基础组件
        self.logger = ArbitrageLogger()
        self.exchange_instance = ExchangeInstance()
        self.exchange_factory = ExchangeFactory()
        
        # 初始化套利策略
        self.arbitrage_strategy = SpreadArbitrageStrategy(self.exchange_instance)
        
        # 初始化通信管理器
        self.comm_manager = create_communication_manager()
        
        # 运行标志
        self.running = True
        
    async def initialize(self):
        """初始化系统"""
        print("\n[主进程] 正在初始化交易系统...")
        try:
            # 初始化交易所连接
            for exchange_id in EXCHANGES:
                config = EXCHANGE_CONFIGS.get(exchange_id, {})
                exchange = await self.exchange_instance.get_exchange(exchange_id, config)
                if not exchange:
                    print(f"[主进程] 初始化 {exchange_id} 失败")
                    return False
                    
            # 订阅价格数据
            self.comm_manager.subscribe_price(self._handle_price_update)
            
            return True
        except Exception as e:
            print(f"[主进程] 系统初始化失败: {str(e)}")
            return False
            
    async def _handle_price_update(self, price_data: Dict[str, Any]):
        """处理价格数据"""
        try:
            await self.arbitrage_strategy.process_price_update(price_data)
        except Exception as e:
            self.logger.error(f"[主进程] 处理价格数据失败: {str(e)}")
                
    async def start(self):
        """启动系统"""
        if await self.initialize():
            print("\n[主进程] 系统初始化完成，开始运行...")
            # 启动通信管理器监听
            await self.comm_manager.start_listening()
        else:
            print("\n[主进程] 系统初始化失败，无法启动")
            
    async def stop(self):
        """停止系统"""
        self.running = False
        # 发送停止命令给监控进程
        self.comm_manager.publish_command("stop")
        await self.exchange_instance.close_all()
        self.comm_manager.stop_listening()
        print("\n[主进程] 系统已停止")

def setup_windows_event_loop():
    """设置Windows系统的事件循环"""
    if platform.system() == 'Windows':
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resolver = aiohttp.resolver.ThreadedResolver(loop=loop)
        aiohttp.resolver.DefaultResolver = lambda *args, **kwargs: resolver
        return loop
    return None

def run_monitor(stop_event: Event):
    """运行监控进程"""
    try:
        # 设置事件循环
        loop = setup_windows_event_loop()
        
        # 创建监控系统实例
        monitor_system = MonitorSystem()
        monitor_system.stop_event = stop_event
        
        async def run():
            try:
                # 启动监控系统
                await monitor_system.start()
                
                # 等待停止信号
                while not stop_event.is_set():
                    await asyncio.sleep(0.1)
                    
                # 停止监控系统
                await monitor_system.stop()
            except Exception as e:
                print(f"[监控进程] 运行时发生错误: {str(e)}")
                if monitor_system:
                    await monitor_system.stop()
                    
        # 运行监控系统
        if loop:
            loop.run_until_complete(run())
        else:
            asyncio.run(run())
    except KeyboardInterrupt:
        print("\n[监控进程] 收到终止信号")
    finally:
        stop_event.set()
        if loop:
            loop.close()

def run_api_server():
    """运行API服务"""
    print("[API进程] 启动API服务...")
    
    if platform.system() == 'Windows':
        # Windows系统使用同步方式运行
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            loop="asyncio",
            http="auto"
        )
    else:
        # 其他系统使用默认配置
        uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    """主程序"""
    try:
        # 设置事件循环
        loop = setup_windows_event_loop()
        
        # 创建停止事件
        stop_event = Event()
        
        # 启动监控进程
        monitor_process = Process(
            target=run_monitor,
            args=(stop_event,)
        )
        monitor_process.start()
        
        # 创建交易系统实例
        trading_system = TradingSystem()
        
        # 启动系统
        await trading_system.start()
            
    except Exception as e:
        print(f"[主进程] 系统运行时发生错误: {str(e)}")
        if 'trading_system' in locals():
            await trading_system.stop()
    finally:
        # 停止监控进程
        stop_event.set()
        monitor_process.join()
        if loop:
            loop.close()

if __name__ == "__main__":
    # 启动API服务进程
    api_process = Process(target=run_api_server)
    api_process.start()
    
    try:
        # 启动主系统
        if platform.system() == 'Windows':
            loop = setup_windows_event_loop()
            loop.run_until_complete(main())
        else:
            asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[主进程] 程序终止")
    finally:
        # 终止API服务进程
        api_process.terminate()
        api_process.join()
