"""API服务器数据模型

此模块定义了API服务器使用的所有数据模型
"""

from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

class StrategyStatus(BaseModel):
    """策略状态数据模型"""
    strategy_name: str
    status: str
    position: float
    pnl: float
    orders: int
    update_time: str

class MarketData(BaseModel):
    """市场数据模型"""
    symbol: str
    price_data: Dict[str, List[float]]
    depth_data: Dict[str, List[float]]

class PerformanceMetrics(BaseModel):
    """性能指标数据模型"""
    total_returns: float
    win_rate: float
    sharpe_ratio: float
    time: List[str]
    cumulative_returns: List[float]

class SystemStatus(BaseModel):
    """系统状态数据模型"""
    monitor_status: str
    trading_status: str
    api_status: str
    active_exchanges: List[str]
    monitored_symbols: List[str]
    last_update: str

class ArbitrageOpportunity(BaseModel):
    """套利机会数据模型"""
    type: str
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    profit_usdt: float
    profit_percent: float
    timestamp: str

class TradeRecord(BaseModel):
    """交易记录数据模型"""
    trade_id: str
    type: str
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    amount: float
    profit_usdt: float
    timestamp: str
    status: str