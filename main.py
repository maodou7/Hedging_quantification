"""
交易所价格监控与套利主程序

此程序负责：
1. 监控多个交易所的价格数据
2. 实时分析套利机会
3. 执行套利交易
"""

import os
import asyncio
import signal
from typing import Dict, List, Any
from datetime import datetime

from src.exchange.exchange_instance import ExchangeInstance
from src.exchange.market_structure_fetcher import MarketStructureFetcher
from src.exchange.price_monitor import PriceMonitor
from src.core.cache_manager import CacheManager
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

class GracefulExit:
    """优雅退出处理类"""
    
    def __init__(self):
        self.shutdown = False
        self.tasks = set()
        
    def signal_handler(self, signum, frame):
        """处理退出信号"""
        print("\n收到退出信号，正在安全停止...")
        self.shutdown = True
        
    async def shutdown_handler(self, monitor: PriceMonitor, arbitrage_strategy: SpreadArbitrageStrategy, exchange_instance: ExchangeInstance):
        """处理关闭操作"""
        try:
            # 停止套利策略
            if arbitrage_strategy:
                await arbitrage_strategy.stop()
                print("已停止套利策略")

            # 停止价格监控
            if monitor:
                await monitor.stop_monitoring()
                print("已停止价格监控")
            
            # 取消所有运行中的任务
            tasks = [t for t in self.tasks if not t.done()]
            if tasks:
                print(f"正在取消 {len(tasks)} 个运行中的任务...")
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # 关闭交易所连接
            if exchange_instance:
                print("正在关闭交易所连接...")
                await exchange_instance.close_all()
                print("已关闭所有交易所连接")
            
        except Exception as e:
            print(f"清理资源时发生错误: {str(e)}")
        finally:
            print("所有资源已清理完毕")

class TradingSystem:
    """交易系统主类"""
    
    def __init__(self):
        # 初始化系统适配器
        self.system_adapter = SystemAdapter()
        print("系统信息:", self.system_adapter.get_system_info())
        
        # 设置事件循环
        self.system_adapter.setup_event_loop()
        
        # 初始化基础组件
        self.logger = ArbitrageLogger()
        self.exchange_instance = ExchangeInstance()
        self.exchange_factory = ExchangeFactory()
        
        # 初始化依赖组件
        self.market_structure_fetcher = MarketStructureFetcher(self.exchange_instance)
        self.cache_manager = CacheManager()
        
        # 初始化套利策略
        self.arbitrage_strategy = SpreadArbitrageStrategy(self.exchange_instance)
        
        # 初始化价格监控器
        self.price_monitor = None
        
    async def _init_exchange(self, exchange_id: str):
        """初始化单个交易所"""
        print(f"初始化交易所 {exchange_id}...")
        try:
            config = EXCHANGE_CONFIGS.get(exchange_id, {})
            exchange = await self.exchange_instance.get_exchange(exchange_id, config)
            if not exchange:
                print(f"初始化 {exchange_id} 失败: 无法创建交易所实例")
                return False
            return True
        except Exception as e:
            print(f"初始化 {exchange_id} 失败: {str(e)}")
            return False
            
    async def _fetch_market_structure(self, exchange_id: str):
        """获取市场结构"""
        print(f"获取 {exchange_id} 市场结构...")
        try:
            await self.market_structure_fetcher.fetch_market_structure(exchange_id)
            print(f"{exchange_id} 市场结构获取成功")
            return True
        except Exception as e:
            print(f"获取 {exchange_id} 市场结构失败: {str(e)}")
            return False
            
    async def initialize(self):
        """初始化系统"""
        print("\n正在初始化交易系统...")
        
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
            return True
        except Exception as e:
            print(f"系统启动失败: {str(e)}")
            return False
            
    async def _on_price_update(self, price_data: Dict[str, Any]):
        """价格更新回调"""
        try:
            # 处理价格更新
            await self.arbitrage_strategy.process_price_update(price_data)
        except Exception as e:
            self.logger.error(f"处理价格更新失败: {str(e)}")
            
    async def start(self):
        """启动系统"""
        if await self.initialize():
            print("\n系统初始化完成，开始运行...")
            await self.price_monitor.start_monitoring()
        else:
            print("\n系统初始化失败，无法启动")
            
    async def stop(self):
        """停止系统"""
        if self.price_monitor:
            await self.price_monitor.stop_monitoring()
        await self.exchange_instance.close_all()
        print("\n系统已停止")

if __name__ == "__main__":
    try:
        # 创建交易系统实例
        trading_system = TradingSystem()
        
        # 获取事件循环
        loop = asyncio.get_event_loop()
        
        # 启动系统
        loop.run_until_complete(trading_system.start())
        
        # 保持系统运行
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print("\n接收到停止信号，正在关闭系统...")
            loop.run_until_complete(trading_system.stop())
        finally:
            loop.close()
            
    except Exception as e:
        print(f"系统运行时发生错误: {str(e)}")
        if 'trading_system' in locals():
            loop.run_until_complete(trading_system.stop())
