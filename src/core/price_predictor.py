"""
价格预测器
使用技术指标和机器学习模型预测价格走势
"""

import numpy as np
from collections import deque
from typing import Dict, List, Optional
from datetime import datetime

from src.Config.exchange_config import INDICATOR_CONFIG

class PricePredictor:
    """价格预测器"""
    def __init__(self, window_size: int = None):
        self.window_size = window_size or INDICATOR_CONFIG['price_history_size']
        self.price_history = {}  # 每个交易所的价格历史
        self.spread_history = deque(maxlen=self.window_size)  # 价差历史
        
        # 设置技术指标参数
        self.sma_short_period = INDICATOR_CONFIG['sma_periods'][0]  # 使用最短周期
        self.sma_long_period = INDICATOR_CONFIG['sma_periods'][-1]  # 使用最长周期
        self.rsi_period = INDICATOR_CONFIG['rsi_period']
        self.rsi_overbought = INDICATOR_CONFIG['rsi_overbought']
        self.rsi_oversold = INDICATOR_CONFIG['rsi_oversold']
        
    def add_price_data(self, exchange_id: str, price_data: Dict):
        """添加价格数据到历史记录"""
        if exchange_id not in self.price_history:
            self.price_history[exchange_id] = deque(maxlen=self.window_size)
        self.price_history[exchange_id].append(price_data)
    
    def add_spread_data(self, spread: float):
        """添加价差数据到历史记录"""
        self.spread_history.append(spread)
    
    def calculate_sma(self, data: List[float], period: int) -> float:
        """计算简单移动平均线"""
        if len(data) < period:
            return data[-1] if data else 0
        return np.mean(data[-period:])
    
    def calculate_rsi(self, data: List[float], period: int = None) -> float:
        """计算RSI指标"""
        period = period or INDICATOR_CONFIG['rsi_period']
        if len(data) <= period:
            return 50  # 默认中性值
        
        # 计算价格变化
        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # 计算平均涨跌幅
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def predict_trend(self, data: List[float]) -> str:
        """使用技术指标预测趋势"""
        if len(data) < self.window_size:
            return "neutral"
        
        # 计算技术指标
        sma_short = self.calculate_sma(data, self.sma_short_period)
        sma_long = self.calculate_sma(data, self.sma_long_period)
        rsi = self.calculate_rsi(data)
        
        # 趋势判断
        trend = "neutral"
        if sma_short > sma_long and rsi < self.rsi_overbought:
            trend = "up"
        elif sma_short < sma_long and rsi > self.rsi_oversold:
            trend = "down"
        
        return trend
    
    def predict_spread_trend(self) -> str:
        """预测价差趋势"""
        if len(self.spread_history) < self.window_size:
            return "neutral"
        
        return self.predict_trend(list(self.spread_history))
    
    def calculate_volatility(self, data: List[float]) -> float:
        """计算波动率"""
        if len(data) < 2:
            return 0.0
        
        returns = np.diff(data) / data[:-1]
        return np.std(returns) * np.sqrt(len(data)) 