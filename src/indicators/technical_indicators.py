"""
技术指标

实现常用的技术分析指标:
1. 移动平均线
2. RSI
3. MACD
4. 布林带
5. KDJ
6. ATR
7. OBV
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Union
from src.utils.logger import ArbitrageLogger

class TechnicalIndicators:
    def __init__(self):
        self.logger = ArbitrageLogger()
        
    def sma(self, data: Union[pd.Series, List[float]], period: int) -> np.ndarray:
        """简单移动平均线"""
        try:
            if isinstance(data, list):
                data = pd.Series(data)
            return data.rolling(window=period).mean().values
        except Exception as e:
            self.logger.error(f"计算SMA时发生错误: {str(e)}")
            return np.array([])
            
    def ema(self, data: Union[pd.Series, List[float]], period: int) -> np.ndarray:
        """指数移动平均线"""
        try:
            if isinstance(data, list):
                data = pd.Series(data)
            return data.ewm(span=period, adjust=False).mean().values
        except Exception as e:
            self.logger.error(f"计算EMA时发生错误: {str(e)}")
            return np.array([])
            
    def rsi(self, data: Union[pd.Series, List[float]], period: int = 14) -> np.ndarray:
        """相对强弱指标"""
        try:
            if isinstance(data, list):
                data = pd.Series(data)
                
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.values
            
        except Exception as e:
            self.logger.error(f"计算RSI时发生错误: {str(e)}")
            return np.array([])
            
    def macd(self, data: Union[pd.Series, List[float]], fast_period: int = 12, 
            slow_period: int = 26, signal_period: int = 9) -> Dict[str, np.ndarray]:
        """MACD指标"""
        try:
            if isinstance(data, list):
                data = pd.Series(data)
                
            # 计算快线和慢线
            fast_ema = data.ewm(span=fast_period, adjust=False).mean()
            slow_ema = data.ewm(span=slow_period, adjust=False).mean()
            
            # 计算MACD线
            macd_line = fast_ema - slow_ema
            
            # 计算信号线
            signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
            
            # 计算MACD柱状图
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line.values,
                'signal': signal_line.values,
                'histogram': histogram.values
            }
            
        except Exception as e:
            self.logger.error(f"计算MACD时发生错误: {str(e)}")
            return {'macd': np.array([]), 'signal': np.array([]), 'histogram': np.array([])}
            
    def bollinger_bands(self, data: Union[pd.Series, List[float]], period: int = 20, 
                       num_std: float = 2.0) -> Dict[str, np.ndarray]:
        """布林带"""
        try:
            if isinstance(data, list):
                data = pd.Series(data)
                
            # 计算中轨（简单移动平均线）
            middle_band = data.rolling(window=period).mean()
            
            # 计算标准差
            std = data.rolling(window=period).std()
            
            # 计算上轨和下轨
            upper_band = middle_band + (std * num_std)
            lower_band = middle_band - (std * num_std)
            
            return {
                'upper': upper_band.values,
                'middle': middle_band.values,
                'lower': lower_band.values
            }
            
        except Exception as e:
            self.logger.error(f"计算布林带时发生错误: {str(e)}")
            return {'upper': np.array([]), 'middle': np.array([]), 'lower': np.array([])}
            
    def kdj(self, high: Union[pd.Series, List[float]], low: Union[pd.Series, List[float]], 
            close: Union[pd.Series, List[float]], period: int = 9) -> Dict[str, np.ndarray]:
        """KDJ指标"""
        try:
            if isinstance(high, list):
                high = pd.Series(high)
            if isinstance(low, list):
                low = pd.Series(low)
            if isinstance(close, list):
                close = pd.Series(close)
                
            # 计算RSV
            low_min = low.rolling(window=period).min()
            high_max = high.rolling(window=period).max()
            rsv = 100 * ((close - low_min) / (high_max - low_min))
            
            # 计算K值
            k = pd.Series(0.0, index=close.index)
            k = k.mask(k == 0, rsv.rolling(window=3).mean())
            
            # 计算D值
            d = k.rolling(window=3).mean()
            
            # 计算J值
            j = 3 * k - 2 * d
            
            return {
                'k': k.values,
                'd': d.values,
                'j': j.values
            }
            
        except Exception as e:
            self.logger.error(f"计算KDJ时发生错误: {str(e)}")
            return {'k': np.array([]), 'd': np.array([]), 'j': np.array([])}
            
    def atr(self, high: Union[pd.Series, List[float]], low: Union[pd.Series, List[float]], 
            close: Union[pd.Series, List[float]], period: int = 14) -> np.ndarray:
        """平均真实波幅"""
        try:
            if isinstance(high, list):
                high = pd.Series(high)
            if isinstance(low, list):
                low = pd.Series(low)
            if isinstance(close, list):
                close = pd.Series(close)
                
            # 计算真实波幅
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # 计算ATR
            atr = tr.rolling(window=period).mean()
            return atr.values
            
        except Exception as e:
            self.logger.error(f"计算ATR时发生错误: {str(e)}")
            return np.array([])
            
    def obv(self, close: Union[pd.Series, List[float]], 
            volume: Union[pd.Series, List[float]]) -> np.ndarray:
        """能量潮指标"""
        try:
            if isinstance(close, list):
                close = pd.Series(close)
            if isinstance(volume, list):
                volume = pd.Series(volume)
                
            # 计算价格变化方向
            price_change = close.diff()
            
            # 根据价格变化方向调整成交量
            volume_direction = pd.Series(0, index=close.index)
            volume_direction[price_change > 0] = volume[price_change > 0]
            volume_direction[price_change < 0] = -volume[price_change < 0]
            
            # 计算OBV
            obv = volume_direction.cumsum()
            return obv.values
            
        except Exception as e:
            self.logger.error(f"计算OBV时发生错误: {str(e)}")
            return np.array([])
            
    def stochastic(self, high: Union[pd.Series, List[float]], low: Union[pd.Series, List[float]], 
                   close: Union[pd.Series, List[float]], k_period: int = 14, 
                   d_period: int = 3) -> Dict[str, np.ndarray]:
        """随机指标"""
        try:
            if isinstance(high, list):
                high = pd.Series(high)
            if isinstance(low, list):
                low = pd.Series(low)
            if isinstance(close, list):
                close = pd.Series(close)
                
            # 计算%K
            low_min = low.rolling(window=k_period).min()
            high_max = high.rolling(window=k_period).max()
            k = 100 * ((close - low_min) / (high_max - low_min))
            
            # 计算%D
            d = k.rolling(window=d_period).mean()
            
            return {
                'k': k.values,
                'd': d.values
            }
            
        except Exception as e:
            self.logger.error(f"计算随机指标时发生错误: {str(e)}")
            return {'k': np.array([]), 'd': np.array([])}
            
    def momentum(self, data: Union[pd.Series, List[float]], period: int = 10) -> np.ndarray:
        """动量指标"""
        try:
            if isinstance(data, list):
                data = pd.Series(data)
                
            momentum = data.diff(period)
            return momentum.values
            
        except Exception as e:
            self.logger.error(f"计算动量指标时发生错误: {str(e)}")
            return np.array([])
            
    def cci(self, high: Union[pd.Series, List[float]], low: Union[pd.Series, List[float]], 
            close: Union[pd.Series, List[float]], period: int = 20) -> np.ndarray:
        """顺势指标"""
        try:
            if isinstance(high, list):
                high = pd.Series(high)
            if isinstance(low, list):
                low = pd.Series(low)
            if isinstance(close, list):
                close = pd.Series(close)
                
            # 计算典型价格
            tp = (high + low + close) / 3
            
            # 计算移动平均
            ma = tp.rolling(window=period).mean()
            
            # 计算平均偏差
            mean_dev = tp.rolling(window=period).apply(lambda x: abs(x - x.mean()).mean())
            
            # 计算CCI
            cci = (tp - ma) / (0.015 * mean_dev)
            return cci.values
            
        except Exception as e:
            self.logger.error(f"计算CCI时发生错误: {str(e)}")
            return np.array([])
            
    def williams_r(self, high: Union[pd.Series, List[float]], low: Union[pd.Series, List[float]], 
                   close: Union[pd.Series, List[float]], period: int = 14) -> np.ndarray:
        """威廉指标"""
        try:
            if isinstance(high, list):
                high = pd.Series(high)
            if isinstance(low, list):
                low = pd.Series(low)
            if isinstance(close, list):
                close = pd.Series(close)
                
            # 计算最高价和最低价
            highest_high = high.rolling(window=period).max()
            lowest_low = low.rolling(window=period).min()
            
            # 计算威廉指标
            wr = -100 * (highest_high - close) / (highest_high - lowest_low)
            return wr.values
            
        except Exception as e:
            self.logger.error(f"计算威廉指标时发生错误: {str(e)}")
            return np.array([]) 