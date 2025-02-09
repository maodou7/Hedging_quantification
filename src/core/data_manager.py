"""
数据管理器

负责:
1. 数据缓存
2. 异步数据更新
3. 数据预处理
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import deque
import aiohttp
import redis
import json
import os
from pathlib import Path
from src.utils.logger import ArbitrageLogger
from src.core.exchange_config import get_ml_config

class DataManager:
    def __init__(self, cache_size: int = 1000):
        self.logger = ArbitrageLogger()
        self.cache_size = cache_size
        self.config = get_ml_config()
        
        # 缓存模式
        self.cache_mode = self.config['cache']['mode']  # 'redis', 'local', 'none'
        
        # Redis客户端
        self.redis_client = None
        if self.cache_mode == 'redis':
            self.redis_client = redis.Redis(
                host=self.config['redis']['host'],
                port=self.config['redis']['port'],
                db=self.config['redis']['db'],
                password=self.config['redis']['password']
            )
            
        # 本地缓存
        elif self.cache_mode == 'local':
            self.price_cache: Dict[str, deque] = {}
            self.orderbook_cache: Dict[str, Dict] = {}
            self.kline_cache: Dict[str, pd.DataFrame] = {}
            
        # 文件存储路径
        self.data_dir = Path(self.config['storage']['data_dir'])
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 更新时间记录
        self.last_update: Dict[str, datetime] = {}
        
        # 会话管理
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def start(self):
        """启动数据管理器"""
        self.session = aiohttp.ClientSession()
        self.logger.info(f"数据管理器已启动 (缓存模式: {self.cache_mode})")
        
    async def stop(self):
        """停止数据管理器"""
        if self.session:
            await self.session.close()
        if self.redis_client:
            self.redis_client.close()
        self.logger.info("数据管理器已停止")
        
    async def update_price(self, exchange_id: str, symbol: str, price: float):
        """更新价格数据"""
        try:
            key = f"{exchange_id}_{symbol}"
            data = {
                'timestamp': datetime.now().isoformat(),
                'price': price
            }
            
            if self.cache_mode == 'redis':
                # Redis存储
                self.redis_client.lpush(f"price:{key}", json.dumps(data))
                self.redis_client.ltrim(f"price:{key}", 0, self.cache_size - 1)
                
            elif self.cache_mode == 'local':
                # 本地缓存
                if key not in self.price_cache:
                    self.price_cache[key] = deque(maxlen=self.cache_size)
                self.price_cache[key].append(data)
                
            else:
                # 文件存储
                file_path = self.data_dir / f"price_{key}.csv"
                df = pd.DataFrame([data])
                df.to_csv(file_path, mode='a', header=not file_path.exists(), index=False)
                
            self.last_update[key] = datetime.now()
            
        except Exception as e:
            self.logger.error(f"更新价格数据时发生错误: {str(e)}")
            
    async def update_orderbook(self, exchange_id: str, symbol: str, orderbook: Dict[str, Any]):
        """更新订单簿数据"""
        try:
            key = f"{exchange_id}_{symbol}"
            data = {
                'timestamp': datetime.now().isoformat(),
                'bids': orderbook['bids'],
                'asks': orderbook['asks']
            }
            
            if self.cache_mode == 'redis':
                # Redis存储
                self.redis_client.set(f"orderbook:{key}", json.dumps(data))
                
            elif self.cache_mode == 'local':
                # 本地缓存
                self.orderbook_cache[key] = data
                
            else:
                # 文件存储
                file_path = self.data_dir / f"orderbook_{key}.csv"
                df = pd.DataFrame([{
                    'timestamp': data['timestamp'],
                    'bids': json.dumps(data['bids']),
                    'asks': json.dumps(data['asks'])
                }])
                df.to_csv(file_path, mode='a', header=not file_path.exists(), index=False)
                
            self.last_update[key] = datetime.now()
            
        except Exception as e:
            self.logger.error(f"更新订单簿数据时发生错误: {str(e)}")
            
    async def update_kline(self, exchange_id: str, symbol: str, kline_data: List[List]):
        """更新K线数据"""
        try:
            key = f"{exchange_id}_{symbol}"
            df = pd.DataFrame(kline_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            if self.cache_mode == 'redis':
                # Redis存储
                for _, row in df.iterrows():
                    data = row.to_dict()
                    data['timestamp'] = data['timestamp'].isoformat()
                    self.redis_client.lpush(f"kline:{key}", json.dumps(data))
                self.redis_client.ltrim(f"kline:{key}", 0, self.cache_size - 1)
                
            elif self.cache_mode == 'local':
                # 本地缓存
                if key not in self.kline_cache:
                    self.kline_cache[key] = df
                else:
                    self.kline_cache[key] = pd.concat([self.kline_cache[key], df])
                    self.kline_cache[key] = self.kline_cache[key].iloc[-self.cache_size:]
                    
            else:
                # 文件存储
                file_path = self.data_dir / f"kline_{key}.csv"
                df.to_csv(file_path, mode='a', header=not file_path.exists(), index=False)
                
            self.last_update[key] = datetime.now()
            
        except Exception as e:
            self.logger.error(f"更新K线数据时发生错误: {str(e)}")
            
    def get_latest_price(self, exchange_id: str, symbol: str) -> Optional[float]:
        """获取最新价格"""
        try:
            key = f"{exchange_id}_{symbol}"
            
            if self.cache_mode == 'redis':
                # Redis读取
                data = self.redis_client.lindex(f"price:{key}", 0)
                if data:
                    return json.loads(data)['price']
                    
            elif self.cache_mode == 'local':
                # 本地缓存读取
                if key in self.price_cache and self.price_cache[key]:
                    return self.price_cache[key][-1]['price']
                    
            else:
                # 文件读取
                file_path = self.data_dir / f"price_{key}.csv"
                if file_path.exists():
                    df = pd.read_csv(file_path)
                    if not df.empty:
                        return df.iloc[-1]['price']
                        
            return None
            
        except Exception as e:
            self.logger.error(f"获取最新价格时发生错误: {str(e)}")
            return None
            
    def get_orderbook(self, exchange_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """获取订单簿数据"""
        try:
            key = f"{exchange_id}_{symbol}"
            
            if self.cache_mode == 'redis':
                # Redis读取
                data = self.redis_client.get(f"orderbook:{key}")
                if data:
                    return json.loads(data)
                    
            elif self.cache_mode == 'local':
                # 本地缓存读取
                return self.orderbook_cache.get(key)
                
            else:
                # 文件读取
                file_path = self.data_dir / f"orderbook_{key}.csv"
                if file_path.exists():
                    df = pd.read_csv(file_path)
                    if not df.empty:
                        latest = df.iloc[-1]
                        return {
                            'timestamp': latest['timestamp'],
                            'bids': json.loads(latest['bids']),
                            'asks': json.loads(latest['asks'])
                        }
                        
            return None
            
        except Exception as e:
            self.logger.error(f"获取订单簿数据时发生错误: {str(e)}")
            return None
            
    def get_kline_data(self, exchange_id: str, symbol: str,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """获取K线数据"""
        try:
            key = f"{exchange_id}_{symbol}"
            
            if self.cache_mode == 'redis':
                # Redis读取
                data = self.redis_client.lrange(f"kline:{key}", 0, -1)
                if data:
                    df = pd.DataFrame([json.loads(d) for d in data])
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    
            elif self.cache_mode == 'local':
                # 本地缓存读取
                if key not in self.kline_cache:
                    return None
                df = self.kline_cache[key]
                
            else:
                # 文件读取
                file_path = self.data_dir / f"kline_{key}.csv"
                if not file_path.exists():
                    return None
                df = pd.read_csv(file_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                
            # 时间过滤
            if start_time:
                df = df[df.index >= start_time]
            if end_time:
                df = df[df.index <= end_time]
                
            return df
            
        except Exception as e:
            self.logger.error(f"获取K线数据时发生错误: {str(e)}")
            return None
            
    async def fetch_historical_data(self, exchange_id: str, symbol: str,
                                  start_time: datetime, end_time: datetime,
                                  timeframe: str = '1m') -> Optional[pd.DataFrame]:
        """获取历史数据"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            # 构建API请求URL (这里以Binance为例)
            url = f"https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol.replace('/', ''),
                'interval': timeframe,
                'startTime': int(start_time.timestamp() * 1000),
                'endTime': int(end_time.timestamp() * 1000),
                'limit': 1000
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                                   'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                                                   'taker_buy_quote', 'ignore'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    
                    # 更新缓存
                    key = f"{exchange_id}_{symbol}"
                    self.kline_cache[key] = df
                    
                    return df
                    
                else:
                    self.logger.error(f"获取历史数据失败: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"获取历史数据时发生错误: {str(e)}")
            return None
            
    def is_data_fresh(self, exchange_id: str, symbol: str, max_age_seconds: int = 60) -> bool:
        """检查数据是否过期"""
        try:
            key = f"{exchange_id}_{symbol}"
            if key not in self.last_update:
                return False
                
            age = datetime.now() - self.last_update[key]
            return age.total_seconds() <= max_age_seconds
            
        except Exception as e:
            self.logger.error(f"检查数据是否过期时发生错误: {str(e)}")
            return False
            
    def clear_cache(self, exchange_id: Optional[str] = None, symbol: Optional[str] = None):
        """清除缓存数据"""
        try:
            if exchange_id and symbol:
                key = f"{exchange_id}_{symbol}"
                if self.cache_mode == 'redis':
                    # 清除Redis缓存
                    self.redis_client.delete(f"price:{key}")
                    self.redis_client.delete(f"orderbook:{key}")
                    self.redis_client.delete(f"kline:{key}")
                    
                elif self.cache_mode == 'local':
                    # 清除本地缓存
                    self.price_cache.pop(key, None)
                    self.orderbook_cache.pop(key, None)
                    self.kline_cache.pop(key, None)
                    
                else:
                    # 删除文件
                    for prefix in ['price', 'orderbook', 'kline']:
                        file_path = self.data_dir / f"{prefix}_{key}.csv"
                        if file_path.exists():
                            file_path.unlink()
                            
            else:
                if self.cache_mode == 'redis':
                    # 清除所有Redis缓存
                    self.redis_client.flushdb()
                    
                elif self.cache_mode == 'local':
                    # 清除所有本地缓存
                    self.price_cache.clear()
                    self.orderbook_cache.clear()
                    self.kline_cache.clear()
                    
                else:
                    # 删除所有文件
                    for file_path in self.data_dir.glob("*.csv"):
                        file_path.unlink()
                        
            self.last_update.clear()
            self.logger.info("缓存已清除")
            
        except Exception as e:
            self.logger.error(f"清除缓存时发生错误: {str(e)}")
            
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            stats = {
                'cache_mode': self.cache_mode,
                'total_symbols': len(set(key.split('_')[1] for key in self.last_update.keys())),
                'total_exchanges': len(set(key.split('_')[0] for key in self.last_update.keys()))
            }
            
            if self.cache_mode == 'redis':
                # Redis统计
                stats.update({
                    'price_cache_size': sum(self.redis_client.llen(key) for key in self.redis_client.keys('price:*')),
                    'orderbook_cache_size': len(self.redis_client.keys('orderbook:*')),
                    'kline_cache_size': sum(self.redis_client.llen(key) for key in self.redis_client.keys('kline:*'))
                })
                
            elif self.cache_mode == 'local':
                # 本地缓存统计
                stats.update({
                    'price_cache_size': sum(len(cache) for cache in self.price_cache.values()),
                    'orderbook_cache_size': len(self.orderbook_cache),
                    'kline_cache_size': sum(len(df) for df in self.kline_cache.values())
                })
                
            else:
                # 文件统计
                stats.update({
                    'price_cache_size': len(list(self.data_dir.glob("price_*.csv"))),
                    'orderbook_cache_size': len(list(self.data_dir.glob("orderbook_*.csv"))),
                    'kline_cache_size': len(list(self.data_dir.glob("kline_*.csv")))
                })
                
            return stats
            
        except Exception as e:
            self.logger.error(f"获取缓存统计信息时发生错误: {str(e)}")
            return {} 