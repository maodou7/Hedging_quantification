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
from decimal import Decimal
from collections import deque

from src.core.cache_manager import CacheManager
from src.Config.exchange_config import MONITOR_CONFIG, EXCHANGES, MARKET_TYPES, SYMBOLS
from src.Environment.cache_config import CACHE_CONFIG, CacheStrategy

class PriceMonitor:
    def __init__(self, exchange_instance, cache_manager: CacheManager):
        self.exchange_instance = exchange_instance
        self.cache_manager = cache_manager
        self.price_queue = deque(maxlen=MONITOR_CONFIG["max_queue_size"])
        self.is_running = False
        self.error_retry_delay = MONITOR_CONFIG["error_retry_delay"]
        self.print_price = MONITOR_CONFIG["print_price"]
        self.ws_clients = {}
        self.price_update_callback = None
        self.monitor_task = None
        
    def set_price_update_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """设置价格更新回调函数"""
        self.price_update_callback = callback
        
    def _generate_cache_key(self, exchange: str, market_type: str, symbol: str) -> str:
        """生成缓存键名"""
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"market_structure:price:{timestamp}:{exchange}:{market_type}:{symbol}"
    
    def _store_price_data(self, price_data: Dict):
        """
        根据缓存策略存储价格数据
        使用Redis的EXPIRE命令设置过期时间，减少写入操作
        """
        if self.cache_manager.strategy == CacheStrategy.REDIS:
            try:
                # 生成缓存键
                cache_key = self._generate_cache_key(
                    price_data["exchange"],
                    price_data["type"],
                    price_data["symbol"]
                )
                
                # 使用pipeline批量执行命令，提高性能
                pipe = self.cache_manager.redis_client.pipeline()
                
                # 设置数据
                pipe.set(cache_key, json.dumps(price_data))
                # 设置过期时间为60秒
                pipe.expire(cache_key, 60)
                
                # 执行命令
                pipe.execute()
                
            except Exception as e:
                print(f"存储价格数据时发生错误: {str(e)}")
            
        elif self.cache_manager.strategy == CacheStrategy.LOCAL:
            # 本地缓存：存入队列
            self.price_queue.append(price_data)
            
        # 调用价格更新回调函数
        if self.price_update_callback:
            try:
                self.price_update_callback(price_data)
            except Exception as e:
                print(f"执行价格更新回调时发生错误: {str(e)}")
            
        # 根据配置决定是否打印价格数据
        if self.print_price:
            print(json.dumps(price_data, ensure_ascii=False))

    async def watch_ticker(self, exchange_id: str, market_type: str, symbol: str):
        """使用WebSocket监控单个交易对的价格"""
        try:
            # 获取WebSocket客户端
            if exchange_id not in self.ws_clients:
                self.ws_clients[exchange_id] = await self.exchange_instance.get_ws_instance(exchange_id)
            
            exchange = self.ws_clients[exchange_id]
            
            while self.is_running:
                try:
                    # 使用watchTicker方法获取实时价格
                    ticker = await exchange.watch_ticker(symbol)
                    
                    price_data = {
                        "exchange": exchange_id,
                        "type": market_type,
                        "symbol": symbol,
                        "quote": symbol.split('/')[1].split(':')[0],
                        "price": str(ticker['last']) if ticker['last'] else None,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    if price_data["price"]:
                        self._store_price_data(price_data)
                        
                except Exception as e:
                    print(f"监控{exchange_id} {symbol}价格时发生错误: {str(e)}")
                    await asyncio.sleep(self.error_retry_delay)
                    
        except Exception as e:
            print(f"创建{exchange_id} WebSocket连接时发生错误: {str(e)}")
    
    async def monitor_realtime(self, symbols_by_type: Dict[str, List[str]], exchanges: List[str]):
        """
        实时模式监控
        使用WebSocket实时获取价格更新
        """
        self.is_running = True
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
            await asyncio.gather(*watch_tasks, return_exceptions=True)
            
        except Exception as e:
            print(f"实时监控发生错误: {str(e)}")
        finally:
            # 关闭所有WebSocket连接
            for exchange_id, ws_client in self.ws_clients.items():
                try:
                    await ws_client.close()
                except Exception as e:
                    print(f"关闭{exchange_id} WebSocket连接时发生错误: {str(e)}")
    
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
        print("开始价格监控...")
        
        # 准备监控的交易对
        symbols_by_type = {market_type: SYMBOLS[market_type] for market_type in MARKET_TYPES if MARKET_TYPES[market_type]}
        
        # 根据配置选择监控模式
        if MONITOR_CONFIG.get("realtime_mode", True):
            self.monitor_task = asyncio.create_task(
                self.monitor_realtime(symbols_by_type, EXCHANGES)
            )
        else:
            self.monitor_task = asyncio.create_task(
                self.monitor_ratelimited(symbols_by_type, EXCHANGES)
            )
    
    async def stop_monitoring(self):
        """停止价格监控"""
        print("正在停止价格监控...")
        self.is_running = False
        
        if self.monitor_task:
            try:
                self.monitor_task.cancel()
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            
        # 关闭所有WebSocket连接
        for exchange_id, ws_client in self.ws_clients.items():
            try:
                await ws_client.close()
            except Exception as e:
                print(f"关闭{exchange_id} WebSocket连接时发生错误: {str(e)}")
        
        print("价格监控已停止")
    
    def get_cached_prices(self) -> List[Dict]:
        """获取缓存的价格数据"""
        if self.cache_manager.strategy == CacheStrategy.LOCAL:
            return list(self.price_queue)
        return [] 