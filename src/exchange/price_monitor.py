"""
价格监控模块
负责从各个交易所获取价格数据
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import ccxt.async_support as ccxt
import ccxt.pro as ccxtpro
from decimal import Decimal
from collections import deque
import logging

from src.core.cache_manager import CacheManager
from src.config.monitoring import MONITOR_CONFIG
from src.config.exchange import EXCHANGES, MARKET_TYPES, SYMBOLS
from src.config.cache import CACHE_CONFIG, CacheStrategy
from src.utils.logger_config import setup_logger

class PriceMonitor:
    def __init__(self, exchange_instance, cache_manager: CacheManager):
        self.exchange_instance = exchange_instance
        self.cache_manager = cache_manager
        self.price_queue = deque(maxlen=MONITOR_CONFIG["max_queue_size"])
        self.is_running = False
        self.error_retry_delay = MONITOR_CONFIG["error_retry_delay"]
        self.print_price = MONITOR_CONFIG["print_price"]
        self.ws_clients = {}
        self.ws_reconnect_attempts = {}  # 记录每个交易所的重连次数
        self.price_update_callback = None
        self.monitor_task = None
        self.max_reconnect_attempts = MONITOR_CONFIG.get("max_reconnect_attempts", 5)
        self.reconnect_delay = MONITOR_CONFIG.get("reconnect_delay", 5)
        self.exponential_backoff = MONITOR_CONFIG.get("exponential_backoff", True)
        self.logger = setup_logger('price_monitor', 'logs/price_monitor.log')
        
    def set_price_update_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """设置价格更新回调函数"""
        self.price_update_callback = callback
        
    def _generate_cache_key(self, exchange: str, market_type: str, symbol: str) -> str:
        """生成缓存键名"""
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"market_structure:price:{timestamp}:{exchange}:{market_type}:{symbol}"
    
    async def _store_price_data(self, price_data: Dict):
        """根据缓存策略存储价格数据"""
        try:
            if self.cache_manager.strategy == CacheStrategy.REDIS:
                # 生成缓存键
                cache_key = self._generate_cache_key(
                    price_data["exchange"],
                    price_data["type"],
                    price_data["symbol"]
                )
                
                # 使用pipeline批量执行命令
                pipe = self.cache_manager.redis_client.pipeline()
                pipe.set(cache_key, json.dumps(price_data))
                pipe.expire(cache_key, 60)
                await pipe.execute()
                
            elif self.cache_manager.strategy == CacheStrategy.LOCAL:
                self.price_queue.append(price_data)
            
            # 调用价格更新回调函数
            if self.price_update_callback:
                await self.price_update_callback(price_data)
            
            # 打印价格数据
            if self.print_price:
                self.logger.info(f"价格更新: {json.dumps(price_data, ensure_ascii=False)}")
                
        except Exception as e:
            self.logger.error(f"存储价格数据时发生错误: {str(e)}")

    async def _init_ws_client(self, exchange_id: str) -> bool:
        """初始化WebSocket客户端"""
        try:
            if exchange_id not in self.ws_clients:
                self.ws_clients[exchange_id] = await self.exchange_instance.get_ws_instance(exchange_id)
                self.ws_reconnect_attempts[exchange_id] = 0
            return True
        except Exception as e:
            self.logger.error(f"初始化{exchange_id} WebSocket客户端失败: {str(e)}")
            return False
            
    async def _handle_ws_error(self, exchange_id: str) -> bool:
        """处理WebSocket错误并尝试重连"""
        self.ws_reconnect_attempts[exchange_id] += 1
        
        if self.ws_reconnect_attempts[exchange_id] >= self.max_reconnect_attempts:
            self.logger.error(f"{exchange_id} WebSocket重连次数超过限制({self.max_reconnect_attempts}次)，停止重连")
            return False
            
        # 计算重连延迟时间
        delay = self.reconnect_delay
        if self.exponential_backoff:
            delay = self.reconnect_delay * (2 ** (self.ws_reconnect_attempts[exchange_id] - 1))
            
        self.logger.info(f"{exchange_id} WebSocket连接断开，{delay}秒后尝试重连...")
        await asyncio.sleep(delay)
        
        # 重置WebSocket连接
        try:
            await self._reset_ws_connection(exchange_id)
            success = await self._init_ws_client(exchange_id)
            if success:
                self.ws_reconnect_attempts[exchange_id] = 0
                self.logger.info(f"{exchange_id} WebSocket重连成功")
                return True
        except Exception as e:
            self.logger.error(f"{exchange_id} WebSocket重连失败: {str(e)}")
            
        return False

    async def watch_ticker(self, exchange_id: str, market_type: str, symbol: str):
        """使用WebSocket监控单个交易对的价格"""
        while self.is_running:
            try:
                # 获取WebSocket实例
                ws_client = await self.exchange_instance.get_ws_instance(exchange_id)
                if not ws_client:
                    self.logger.error(f"无法获取{exchange_id} WebSocket实例")
                    await asyncio.sleep(self.error_retry_delay)
                    continue

                # 使用WebSocket监控价格
                while self.is_running:
                    try:
                        # 使用watch_ticker方法获取实时价格
                        ticker = await ws_client.watch_ticker(symbol)
                        
                        if ticker and ticker.get('last'):
                            price_data = {
                                "exchange": exchange_id,
                                "type": market_type,
                                "symbol": symbol,
                                "quote": symbol.split('/')[1],
                                "price": str(ticker['last']),
                                "bid": str(ticker.get('bid', 0)),
                                "ask": str(ticker.get('ask', 0)),
                                "volume": str(ticker.get('baseVolume', 0)),
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            await self._store_price_data(price_data)
                            
                    except Exception as e:
                        self.logger.error(f"WebSocket监控{exchange_id} {symbol}价格时发生错误: {str(e)}")
                        # 如果发生错误，尝试重新连接
                        success = await self._handle_ws_error(exchange_id)
                        if not success:
                            break
                        
            except Exception as e:
                self.logger.error(f"监控{exchange_id} {symbol}价格时发生错误: {str(e)}")
                await asyncio.sleep(self.error_retry_delay)

    async def _reset_ws_connection(self, exchange_id: str):
        """重置WebSocket连接"""
        try:
            if exchange_id in self.ws_clients:
                await self.ws_clients[exchange_id].close()
                del self.ws_clients[exchange_id]
        except Exception as e:
            self.logger.error(f"重置{exchange_id} WebSocket连接时发生错误: {str(e)}")

    async def monitor_realtime(self, symbols_by_type: Dict[str, List[str]], exchanges: List[str]):
        """实时模式监控"""
        self.is_running = True
        watch_tasks = []
        
        try:
            # 为每个交易对创建监控任务
            for exchange_id in exchanges:
                for market_type, symbols_dict in symbols_by_type.items():
                    exchange_symbols = symbols_dict.get(exchange_id, [])
                    
                    for symbol in exchange_symbols:
                        if not self.is_running:
                            return
                        watch_tasks.append(
                            asyncio.create_task(
                                self.watch_ticker(exchange_id, market_type, symbol)
                            )
                        )
            
            # 等待所有监控任务
            await asyncio.gather(*watch_tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"实时监控发生错误: {str(e)}")
            raise
        finally:
            # 关闭所有WebSocket连接
            await self._cleanup_resources()

    async def monitor_ratelimited(self, symbols_by_type: Dict[str, List[str]], exchanges: List[str]):
        """
        限流模式监控
        按固定频率获取价格更新
        """
        self.is_running = True
        interval_ms = MONITOR_CONFIG["interval_ms"]
        watch_tasks = []
        
        try:
            # 为每个交易对创建监控任务
            for exchange_id in exchanges:
                for market_type, symbols in symbols_by_type.items():
                    # 只监控启用的市场类型
                    if not MARKET_TYPES.get(market_type, False):
                        continue
                        
                    # 跳过空的交易对列表
                    if not symbols:
                        continue
                        
                    for symbol in symbols:
                        if not self.is_running:
                            return
                        watch_tasks.append(
                            asyncio.create_task(
                                self.watch_ticker(exchange_id, market_type, symbol)
                            )
                        )
            
            # 等待所有监控任务
            while self.is_running:
                await asyncio.sleep(interval_ms / 1000)
            
            # 取消所有任务
            for task in watch_tasks:
                task.cancel()
            
            await asyncio.gather(*watch_tasks, return_exceptions=True)
            
        except Exception as e:
            print(f"限流监控发生错误: {str(e)}")
        finally:
            # 关闭所有WebSocket连接
            for exchange_id, ws_client in self.ws_clients.items():
                try:
                    await ws_client.close()
                except Exception as e:
                    print(f"关闭{exchange_id} WebSocket连接时发生错误: {str(e)}")

    async def start_monitoring(self):
        """启动价格监控"""
        self.logger.info("开始价格监控...")
        
        try:
            # 准备监控的交易对
            symbols_by_type = {"spot": SYMBOLS}  # 使用固定的spot类型
            
            # 使用实时模式监控
            self.monitor_task = asyncio.create_task(
                self.monitor_realtime(symbols_by_type, EXCHANGES)
            )
            
            await self.monitor_task
            
        except asyncio.CancelledError:
            self.logger.info("监控任务被取消")
        except Exception as e:
            self.logger.error(f"启动监控时发生错误: {str(e)}")
            raise
        finally:
            await self._cleanup_resources()

    async def _cleanup_resources(self):
        """清理资源"""
        try:
            # 关闭所有WebSocket连接
            for exchange_id in list(self.ws_clients.keys()):
                try:
                    ws_client = await self.exchange_instance.get_ws_instance(exchange_id)
                    if ws_client:
                        await ws_client.close()
                    del self.ws_clients[exchange_id]
                except Exception as e:
                    self.logger.error(f"关闭{exchange_id} WebSocket连接时发生错误: {str(e)}")
                        
        except Exception as e:
            self.logger.error(f"清理资源时发生错误: {str(e)}")

    async def stop_monitoring(self):
        """停止价格监控"""
        self.logger.info("正在停止价格监控...")
        self.is_running = False
        
        try:
            if self.monitor_task and not self.monitor_task.done():
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    self.logger.error(f"取消监控任务时发生错误: {str(e)}")
            
            await self._cleanup_resources()
            self.logger.info("价格监控已停止")
            
        except Exception as e:
            self.logger.error(f"停止监控时发生错误: {str(e)}")
            raise
    
    def get_cached_prices(self) -> List[Dict]:
        """获取缓存的价格数据"""
        if self.cache_manager.strategy == CacheStrategy.LOCAL:
            return list(self.price_queue)
        return [] 