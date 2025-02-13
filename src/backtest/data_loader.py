"""
数据加载器

负责:
1. 加载历史数据
2. 数据预处理
3. 数据格式转换
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import ccxt
import os
from src.utils.logger import ArbitrageLogger

# Add rate limit handling
from ccxt.base.errors import RateLimitExceeded

class DataLoader:
    def __init__(self):
        self.logger = ArbitrageLogger()
        
    async def load_exchange_data(self, exchange_id: str, symbols: List[str], 
                               start_time: datetime, end_time: datetime,
                               timeframe: str = '1m') -> Dict[str, pd.DataFrame]:
        """从交易所加载历史数据"""
        try:
            # 创建交易所实例
            exchange = getattr(ccxt, exchange_id)({
                'enableRateLimit': True
            })
            
            if not exchange.has['fetchOHLCV']:
                self.logger.error(f"{exchange_id} 不支持获取历史K线数据")
                return {}
                
            data = {}
            for symbol in symbols:
                self.logger.info(f"正在加载 {exchange_id} {symbol} 的历史数据...")
                
                # 获取K线数据
                ohlcv = []
                current_time = start_time
                while current_time < end_time:
                    try:
                        # 获取一批数据
                        batch = await exchange.fetch_ohlcv(
                            symbol,
                            timeframe,
                            int(current_time.timestamp() * 1000),
                            limit=1000
                        )
                        if not batch:
                            break
                            
                        ohlcv.extend(batch)
                        current_time = datetime.fromtimestamp(batch[-1][0] / 1000) + timedelta(minutes=1)
                        
                    except RateLimitExceeded as e:
                        self.logger.warning(f"达到速率限制，等待重试: {str(e)}")
                        await asyncio.sleep(exchange.rateLimit / 1000)
                        continue
                    except Exception as e:
                        self.logger.error(f"获取数据时发生错误: {str(e)}")
                        break
                        
                if ohlcv:
                    # 转换为DataFrame
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    
                    # 计算买卖价格
                    df['bid'] = df['close'] * 0.9999  # 模拟买价
                    df['ask'] = df['close'] * 1.0001  # 模拟卖价
                    
                    # 重采样到1分钟
                    if timeframe != '1m':
                        df = df.resample('1min').ffill()
                        
                    data[symbol] = df
                    
            return data
            
        except Exception as e:
            self.logger.error(f"加载交易所数据时发生错误: {str(e)}")
            return {}
            
    def load_csv_data(self, directory: str, symbols: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """从CSV文件加载数据"""
        try:
            data = {}
            
            # 获取目录下的所有CSV文件
            files = [f for f in os.listdir(directory) if f.endswith('.csv')]
            
            for file in files:
                symbol = file.replace('.csv', '')
                if symbols and symbol not in symbols:
                    continue
                    
                file_path = os.path.join(directory, file)
                df = pd.read_csv(file_path)
                
                # 确保时间列存在
                if 'timestamp' not in df.columns:
                    self.logger.error(f"{file} 缺少timestamp列")
                    continue
                    
                # 转换时间戳
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                
                # 确保必要的列存在
                required_columns = ['open', 'high', 'low', 'close', 'volume']
                if not all(col in df.columns for col in required_columns):
                    self.logger.error(f"{file} 缺少必要的列")
                    continue
                    
                # 计算买卖价格
                if 'bid' not in df.columns:
                    df['bid'] = df['close'] * 0.9999
                if 'ask' not in df.columns:
                    df['ask'] = df['close'] * 1.0001
                    
                data[symbol] = df
                
            return data
            
        except Exception as e:
            self.logger.error(f"加载CSV数据时发生错误: {str(e)}")
            return {}
            
    def preprocess_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """预处理数据"""
        try:
            processed_data = {}
            
            for symbol, df in data.items():
                # 删除重复数据
                df = df[~df.index.duplicated(keep='first')]
                
                # 按时间排序
                df.sort_index(inplace=True)
                
                # 处理缺失值
                df.fillna(method='ffill', inplace=True)
                
                # 删除异常值
                for col in ['open', 'high', 'low', 'close', 'bid', 'ask']:
                    if col in df.columns:
                        # 计算z分数
                        z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                        # 删除z分数大于3的数据点
                        df = df[z_scores <= 3]
                        
                processed_data[symbol] = df
                
            return processed_data
            
        except Exception as e:
            self.logger.error(f"预处理数据时发生错误: {str(e)}")
            return data
            
    def save_data(self, data: Dict[str, pd.DataFrame], directory: str):
        """保存数据到CSV文件"""
        try:
            os.makedirs(directory, exist_ok=True)
            
            for symbol, df in data.items():
                file_path = os.path.join(directory, f"{symbol}.csv")
                df.to_csv(file_path)
                self.logger.info(f"数据已保存至: {file_path}")
                
        except Exception as e:
            self.logger.error(f"保存数据时发生错误: {str(e)}")
            
    def merge_data(self, data_list: List[Dict[str, pd.DataFrame]]) -> Dict[str, pd.DataFrame]:
        """合并多个数据源的数据"""
        try:
            merged_data = {}
            
            # 获取所有交易对
            all_symbols = set()
            for data in data_list:
                all_symbols.update(data.keys())
                
            # 合并每个交易对的数据
            for symbol in all_symbols:
                dfs = []
                for data in data_list:
                    if symbol in data:
                        dfs.append(data[symbol])
                        
                if dfs:
                    # 合并数据框
                    merged_df = pd.concat(dfs)
                    # 删除重复数据
                    merged_df = merged_df[~merged_df.index.duplicated(keep='first')]
                    # 按时间排序
                    merged_df.sort_index(inplace=True)
                    
                    merged_data[symbol] = merged_df
                    
            return merged_data
            
        except Exception as e:
            self.logger.error(f"合并数据时发生错误: {str(e)}")
            return {}
