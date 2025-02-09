"""
价格监控模块
负责实时监控多个交易所的价格数据
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from src.exchange.exchange_instance import ExchangeInstance
from src.cache.cache_manager import CacheManager
from src.logger.arbitrage_logger import ArbitrageLogger
from src.core.exchange_config import EXCHANGES, SYMBOLS, MONITOR_CONFIG

class PriceMonitor:
    """价格监控器"""
    
    def __init__(self, exchange_instance: ExchangeInstance, cache_manager: CacheManager):
        """
        初始化价格监控器
        :param exchange_instance: 交易所实例
        :param cache_manager: 缓存管理器
        """
        self.exchange_instance = exchange_instance
        self.cache_manager = cache_manager
        self.logger = ArbitrageLogger()
        
        # 使用默认配置
        self.config = {
            "mode": "realtime",
            "interval_ms": 100,
            "max_queue_size": 1000,
            "print_price": True,
            "error_retry_delay": 1,
            "update_interval": 1.0,
            "health_check_interval": 60.0,
            "retry_interval": 5.0,
            "max_retries": 3
        }
        
        # 更新配置
        try:
            if MONITOR_CONFIG:
                self.config.update(MONITOR_CONFIG)
        except Exception as e:
            self.logger.warning(f"无法加载监控配置: {str(e)}")
            
        # 初始化队列和回调
        try:
            self.price_queue = asyncio.Queue(maxsize=self.config.get("max_queue_size", 1000))
            self.price_update_callback = None
            self.is_running = False
        except Exception as e:
            self.logger.error(f"初始化价格队列失败: {str(e)}")
            raise
        
    def set_price_update_callback(self, callback: Callable):
        """设置价格更新回调"""
        self.price_update_callback = callback
        
    async def _fetch_price(self, exchange_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """获取价格数据"""
        try:
            exchange = await self.exchange_instance.get_exchange(exchange_id)
            if not exchange:
                return None
                
            ticker = await exchange.fetch_ticker(symbol)
            return {
                'exchange': exchange_id,
                'symbol': symbol,
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'timestamp': ticker['timestamp']
            }
        except Exception as e:
            self.logger.error(f"获取价格失败 {exchange_id} {symbol}: {str(e)}")
            return None
            
    async def _process_price_queue(self):
        """处理价格队列"""
        while self.is_running:
            try:
                price_data = await self.price_queue.get()
                if self.price_update_callback:
                    await self.price_update_callback(price_data)
                self.price_queue.task_done()
            except Exception as e:
                self.logger.error(f"处理价格队列时发生错误: {str(e)}")
                await asyncio.sleep(self.config["error_retry_delay"])
                
    async def _monitor_prices(self):
        """监控价格"""
        while self.is_running:
            try:
                for exchange_id in EXCHANGES:
                    for symbol in SYMBOLS:
                        price_data = await self._fetch_price(exchange_id, symbol)
                        if price_data:
                            await self.price_queue.put(price_data)
                            if self.config["print_price"]:
                                print(f"价格更新: {exchange_id} {symbol} - Bid: {price_data['bid']}, Ask: {price_data['ask']}")
                                
                await asyncio.sleep(self.config["update_interval"])
            except Exception as e:
                self.logger.error(f"监控价格时发生错误: {str(e)}")
                await asyncio.sleep(self.config["error_retry_delay"])
                
    async def start_monitoring(self):
        """开始监控"""
        self.is_running = True
        asyncio.create_task(self._process_price_queue())
        asyncio.create_task(self._monitor_prices())
        self.logger.info("价格监控已启动")
        
    async def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        self.logger.info("价格监控已停止") 