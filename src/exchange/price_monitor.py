"""
价格监控模块（优化版）

此模块负责监控交易所的价格数据，使用WebSocket连接池和批量处理优化性能
主要优化点：
1. WebSocket连接池管理
2. 异步信号量控制并发
3. 批量处理队列使用asyncio.Queue
4. 心跳保持和智能重连机制
"""

import asyncio
import time
import json
import traceback
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime
from collections import deque, defaultdict
import logging
import ccxt.async_support as ccxt
import ccxt.pro as ccxtpro

from src.core.cache_manager import CacheManager
from src.config.monitoring import MONITOR_CONFIG
from src.config.exchange import EXCHANGES, MARKET_TYPES, SYMBOLS
from src.config.cache import CACHE_CONFIG, CacheStrategy
from src.utils.logger import ArbitrageLogger
from src.exchange.exchange_instance import ExchangeInstance

class PriceMonitor:
    """价格监控类（优化版）"""
    
    def __init__(self, exchange_instance: ExchangeInstance):
        """初始化价格监控器"""
        self.exchange_instance = exchange_instance
        self.logger = ArbitrageLogger()
        self._running = False
        self._tasks = set()
        self._symbols_by_exchange: Dict[str, Set[str]] = {}

        # 连接池配置
        self.ws_pool_size = MONITOR_CONFIG.get("ws_pool_size", 10)
        self.ws_pool: Dict[str, deque] = defaultdict(deque)
        self.pool_lock = asyncio.Lock()
        self.semaphore = asyncio.Semaphore(MONITOR_CONFIG.get("max_concurrent", 100))

        # 队列优化配置
        self.price_queue = deque(maxlen=MONITOR_CONFIG["max_queue_size"])
        self.batch_queue = asyncio.Queue(maxsize=MONITOR_CONFIG.get("batch_queue_size", 1000))
        self.batch_interval = MONITOR_CONFIG.get("batch_interval", 0.5)
        self.batch_size = MONITOR_CONFIG.get("batch_size", 200)

        # 运行状态控制
        self.is_running = False
        self.error_retry_delay = MONITOR_CONFIG["error_retry_delay"]
        self.print_price = MONITOR_CONFIG.get("debug_mode", False)

        # 熔断机制
        self.circuit_breaker_threshold = MONITOR_CONFIG.get("circuit_breaker_threshold", 50)
        self.circuit_breaker_interval = MONITOR_CONFIG.get("circuit_breaker_interval", 60)
        self.error_count = 0
        self.circuit_opened = False

        # 异步初始化控制
        self._init_done = asyncio.Event()
        self.cache_manager = CacheManager()
        
        # 后台任务
        self.batch_task = None
        self.health_check_task = None

    def add_symbols(self, exchange_id: str, symbols: List[str]):
        """添加需要监控的交易对"""
        if isinstance(symbols, str):
            symbols = [symbols]
        elif not isinstance(symbols, (list, set)):
            self.logger.error(f"[监控] 交易对格式错误: {type(symbols)}")
            return

        valid_symbols = []
        for symbol in symbols:
            if not self._validate_symbol_format(symbol):
                continue
            
            if self.exchange_instance.symbol_exists(exchange_id, symbol):
                valid_symbols.append(symbol)
                self.logger.debug(f"[监控] 交易所 {exchange_id} 的交易对 {symbol} 验证通过")
            else:
                self.logger.warning(f"[监控] 交易所 {exchange_id} 的交易对 {symbol} 验证失败")

        if valid_symbols:
            if exchange_id not in self._symbols_by_exchange:
                self._symbols_by_exchange[exchange_id] = set()
            self._symbols_by_exchange[exchange_id].update(valid_symbols)
            self.logger.info(f"[监控] 交易所 {exchange_id} 添加了 {len(valid_symbols)} 个有效交易对")
        else:
            self.logger.warning(f"[监控] 交易所 {exchange_id} 没有有效的交易对")

    def _validate_symbol_format(self, symbol: str) -> bool:
        """验证交易对格式"""
        if not isinstance(symbol, str):
            self.logger.warning(f"[监控] 跳过非字符串交易对: {symbol}")
            return False
        if '/' not in symbol:
            self.logger.warning(f"[监控] 交易对格式错误: {symbol}")
            return False
        return True

    async def _get_ws_connection(self, exchange_id: str) -> Optional[ccxtpro.Exchange]:
        """从连接池获取WebSocket连接"""
        async with self.pool_lock:
            if self.ws_pool[exchange_id]:
                return self.ws_pool[exchange_id].popleft()
        try:
            return await self.exchange_instance.get_ws_instance(exchange_id)
        except Exception as e:
            self.logger.error(f"创建{exchange_id} WS连接失败: {str(e)}")
            return None

    async def _release_ws_connection(self, exchange_id: str, ws: ccxtpro.Exchange):
        """释放WebSocket连接到连接池"""
        async with self.pool_lock:
            if len(self.ws_pool[exchange_id]) < self.ws_pool_size:
                self.ws_pool[exchange_id].append(ws)

    async def watch_ticker(self, exchange_id: str, market_type: str, symbol: str):
        """使用连接池监控交易对价格"""
        await self._init_done.wait()
        self.logger.debug(f"开始监控 {exchange_id} {symbol}")

        async with self.semaphore:
            ws = await self._get_ws_connection(exchange_id)
            if not ws:
                return

            try:
                while self.is_running:
                    try:
                        ticker = await ws.watch_ticker(symbol)
                        if ticker and ticker.get('last'):
                            await self._process_ticker_data(exchange_id, market_type, symbol, ticker)
                            
                            # 心跳保持
                            if hasattr(ws, '_last_heartbeat') and ws._last_heartbeat % 100 == 0:
                                await ws.keep_alive()
                                
                    except (ccxt.NetworkError, ccxt.ExchangeError) as e:
                        await self._handle_reconnect(exchange_id, ws, str(e))
                        break
            finally:
                await self._release_ws_connection(exchange_id, ws)

    async def _process_ticker_data(self, exchange_id: str, market_type: str, symbol: str, ticker: dict):
        """处理并存储ticker数据"""
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
        
        await self.batch_queue.put(price_data)
        
        if self.print_price:
            self.logger.debug(f"价格更新: {exchange_id} {symbol}")

    async def _handle_reconnect(self, exchange_id: str, ws: ccxtpro.Exchange, error_msg: str):
        """处理重连逻辑"""
        self.logger.warning(f"{exchange_id} 连接异常: {error_msg}")
        try:
            await ws.close()
        except Exception as e:
            self.logger.error(f"关闭{exchange_id}连接失败: {str(e)}")
            
        await asyncio.sleep(MONITOR_CONFIG.get("reconnect_delay", 5))
        await self.exchange_instance.reset_ws_connection(exchange_id)

    async def _batch_processor(self):
        """优化后的批量数据处理循环"""
        while self.is_running:
            try:
                await asyncio.sleep(self.batch_interval)
                await self._flush_batch()
            except Exception as e:
                self.logger.error(f"批量处理错误: {str(e)}")
                await self._handle_batch_error()

    async def _flush_batch(self):
        """批量处理队列数据"""
        batch = []
        while not self.batch_queue.empty() and len(batch) < self.batch_size:
            batch.append(await self.batch_queue.get())
        
        if batch:
            await self._batch_store_data(batch)
            self.logger.debug(f"批量存储完成: {len(batch)} 条记录")

    async def _batch_store_data(self, tickers: List[Dict]):
        """批量存储到缓存系统"""
        try:
            if self.cache_manager.strategy == CacheStrategy.REDIS:
                await self._store_to_redis(tickers)
            else:
                await self._store_to_local(tickers)
                
            if self.print_price:
                self.logger.debug(f"批量存储 {len(tickers)} 条价格数据")
        except Exception as e:
            self.logger.error(f"批量存储失败: {str(e)}")
            raise

    async def _store_to_redis(self, tickers: List[Dict]):
        """存储到Redis"""
        async with self.exchange_instance.redis_pool as redis:
            pipe = redis.pipeline()
            for ticker in tickers:
                cache_key = self._generate_cache_key(ticker)
                pipe.setex(cache_key, 60, json.dumps(ticker))
            await pipe.execute()

    async def _store_to_local(self, tickers: List[Dict]):
        """存储到本地队列"""
        for ticker in tickers:
            self.price_queue.append(ticker)

    def _generate_cache_key(self, ticker: Dict) -> str:
        """生成缓存键"""
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"price:{timestamp}:{ticker['exchange']}:{ticker['symbol']}"

    async def _health_check(self):
        """连接健康检查"""
        while self.is_running:
            try:
                # 检查交易所连接
                for exchange_id in self._symbols_by_exchange:
                    if not await self.exchange_instance.check_connection(exchange_id):
                        self.logger.warning(f"{exchange_id} 连接异常")
                        
                # 检查Redis连接
                if self.cache_manager.strategy == CacheStrategy.REDIS:
                    async with self.exchange_instance.redis_pool as redis:
                        if not await redis.ping():
                            self.logger.error("Redis连接异常")
                
                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"健康检查失败: {str(e)}")
                await asyncio.sleep(10)

    async def start_monitoring(self):
        """启动监控系统"""
        if not await self._initialize():
            self.logger.error("监控系统初始化失败")
            return

        self.logger.info("启动价格监控...")
        self.is_running = True
        
        try:
            # 启动后台任务
            self.batch_task = asyncio.create_task(self._batch_processor())
            self.health_check_task = asyncio.create_task(self._health_check())
            
            # 创建监控任务
            tasks = []
            for exchange_id, symbols in self._symbols_by_exchange.items():
                if symbols:
                    tasks.append(self._monitor_exchange(exchange_id, symbols))
            
            await asyncio.gather(*tasks)
            
        except Exception as e:
            self.logger.error(f"监控启动失败: {str(e)}")
        finally:
            await self.stop_monitoring()

    async def _initialize(self) -> bool:
        """初始化系统组件"""
        try:
            # 初始化缓存连接
            if self.cache_manager.strategy == CacheStrategy.REDIS:
                await self.cache_manager.initialize()
            
            # 预创建交易所连接
            await self.exchange_instance.initialize_all_connections()
            
            # 启动后台任务
            self._init_done.set()
            return True
        except Exception as e:
            self.logger.error(f"初始化失败: {str(e)}")
            return False

    async def _monitor_exchange(self, exchange_id: str, symbols: Set[str]):
        """监控单个交易所"""
        self.logger.info(f"开始监控 {exchange_id}")
        
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(
                self.watch_ticker(exchange_id, 'spot', symbol)
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop_monitoring(self):
        """停止监控"""
        self.logger.info("停止价格监控...")
        self.is_running = False
        
        # 取消后台任务
        if self.batch_task:
            self.batch_task.cancel()
        if self.health_check_task:
            self.health_check_task.cancel()
        
        # 关闭所有连接
        await self.exchange_instance.close_all_connections()
        
        # 清理队列
        self.price_queue.clear()
        while not self.batch_queue.empty():
            self.batch_queue.get_nowait()
        
        self.logger.info("价格监控已停止")

    def get_cached_prices(self) -> List[Dict]:
        """获取缓存价格"""
        return list(self.price_queue)
