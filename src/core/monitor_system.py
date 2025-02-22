"""
监控系统

负责管理和协调各个交易所的价格监控、数据处理和套利策略执行
"""

import asyncio
import logging
import aiohttp
from typing import Dict, List, Any
from src.exchange.exchange_instance import ExchangeInstance
from src.exchange.market_structure_fetcher import MarketStructureFetcher
from src.exchange.price_monitor import PriceMonitor
from src.core.cache_manager import CacheManager
from src.core.redis_manager import RedisManager
from src.config.exchange import EXCHANGES, SYMBOLS, EXCHANGE_CONFIGS
from src.utils.system_adapter import SystemAdapter

logger = logging.getLogger(__name__)

class MonitorSystem:
    """价格监控系统"""
    def __init__(self):
        # 导入初始化状态监控器
        from src.api.monitor.init_status import init_status_monitor
        
        # 初始化系统适配器
        self.system_adapter = SystemAdapter()
        self.logger = logging.getLogger('monitor')
        system_info = self.system_adapter.get_system_info()
        init_status_monitor.add_event("system_init", "系统初始化开始", {"system_info": system_info})
        self.logger.info("[监控进程] 系统初始化开始，请通过API接口查看详细状态")
        
        # 初始化连接池
        self.redis_manager = RedisManager()
        self.http_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=20),
            timeout=aiohttp.ClientTimeout(total=30)
        )
        self.ws_conn_pool = {}
        init_status_monitor.add_event("connection_init", "连接池初始化完成")
        
        # 初始化基础组件
        exchange_config = {
            'exchanges': EXCHANGES,
            'configs': EXCHANGE_CONFIGS,
            'use_redis': True,
            'redis_url': self.redis_manager.get_redis_url(),
            'rest_timeout': 30000,
            'ws_timeout': 30000,
            'max_rest_pool_size': 10,
            'max_ws_pool_size': 5,
            'health_check_interval': 60
        }
        self.exchange_instance = ExchangeInstance(exchange_config)
        self.exchange_factory = None
        self.market_structure_fetcher = None
        self.cache_manager = None
        self.price_monitor = None
        init_status_monitor.add_event("component_init", "基础组件初始化完成", {"exchange_config": exchange_config})
        
        # 设置要监控的交易所
        self.exchanges = EXCHANGES
        init_status_monitor.add_event("exchange_config", "交易所配置加载完成", {"exchanges": EXCHANGES})
        
        # 运行标志
        self.running = True
        
    async def initialize(self):
        """初始化监控系统"""
        try:
            # 初始化Redis连接
            if not await self.redis_manager.initialize():
                self.logger.error("[监控进程] Redis连接失败，请检查Redis服务状态")
                return False
            
            # 构建交易所实例配置
            exchange_config = {
                'exchanges': EXCHANGES,
                'configs': EXCHANGE_CONFIGS,
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
            await self.exchange_instance.initialize_all_connections()
            
            # 检查交易所连接状态
            for exchange_id in self.exchanges:
                if not await self.exchange_instance.is_connected(exchange_id):
                    self.logger.error(f"交易所 {exchange_id} 连接失败")
                    return False
            
            # 初始化其他组件
            self.exchange_factory = ExchangeFactory()
            self.market_structure_fetcher = MarketStructureFetcher(self.exchange_instance)
            self.cache_manager = CacheManager()
            self.price_monitor = PriceMonitor(exchange_instance=self.exchange_instance)
            
            # 添加监控的交易对
            for exchange_id in EXCHANGES:
                self.price_monitor.add_symbols(exchange_id, SYMBOLS)
                
            return True
            
        except Exception as e:
            self.logger.error(f"[监控进程] 初始化系统时发生错误: {str(e)}")
            return False

    async def start_monitoring(self):
        """启动监控"""
        if not self.running:
            return
            
        try:
            await self.price_monitor.start_monitoring()
        except Exception as e:
            logger.error(f"[监控进程] 启动监控时发生错误: {str(e)}")

    async def stop(self):
        """停止监控系统"""
        if self.running:
            self.running = False
        try:
            # 并行关闭所有资源
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
            # 确保所有资源都被清理
            if hasattr(self, 'exchange_instance') and self.exchange_instance:
                try:
                    await self.exchange_instance.close_all_connections()
                except Exception as e:
                    logger.error(f"[监控进程] 关闭交易所实例时发生错误: {str(e)}")
                    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop()