"""
API服务器

提供:
1. 策略状态数据
2. 市场行情数据
3. 性能指标数据
4. 系统状态
5. 套利机会
6. 日志查看
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from typing import Dict, List, Any, Optional
from datetime import datetime
import uvicorn
import random
import numpy as np
import pandas as pd
import os
from pydantic import BaseModel

app = FastAPI(
    title="量化交易系统API",
    description="提供系统状态、市场数据、交易记录等查询接口",
    version="1.0.0"
)

# 启用CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class StrategyStatus(BaseModel):
    strategy_name: str
    status: str
    position: float
    pnl: float
    orders: int
    update_time: str

class MarketData(BaseModel):
    symbol: str
    price_data: Dict[str, List[float]]
    depth_data: Dict[str, List[float]]

class PerformanceMetrics(BaseModel):
    total_returns: float
    win_rate: float
    sharpe_ratio: float
    time: List[str]
    cumulative_returns: List[float]

class SystemStatus(BaseModel):
    """系统状态"""
    monitor_status: str
    trading_status: str
    api_status: str
    active_exchanges: List[str]
    monitored_symbols: List[str]
    last_update: str

class ArbitrageOpportunity(BaseModel):
    """套利机会"""
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
    """交易记录"""
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

# 模拟数据生成函数
def generate_mock_strategy_status() -> Dict[str, Any]:
    strategies = ["网格交易", "马丁策略", "三角套利", "统计套利"]
    status = {}
    
    for strategy in strategies:
        status[strategy] = {
            "status": random.choice(["运行中", "已停止", "错误"]),
            "position": random.uniform(-10, 10),
            "pnl": random.uniform(-1000, 1000),
            "orders": random.randint(0, 100),
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    return status

def generate_mock_market_data(symbol: str) -> Dict[str, Any]:
    # 生成K线数据
    n_points = 100
    time = list(range(n_points))
    close = np.cumsum(np.random.normal(0, 1, n_points)) + 100
    
    # 生成深度数据
    n_depth = 10
    bids_price = np.linspace(close[-1]-10, close[-1]-1, n_depth)
    asks_price = np.linspace(close[-1]+1, close[-1]+10, n_depth)
    bids_volume = np.random.uniform(1, 10, n_depth)
    asks_volume = np.random.uniform(1, 10, n_depth)
    
    return {
        "price_data": {
            "time": time,
            "close": close.tolist()
        },
        "depth_data": {
            "bids_price": bids_price.tolist(),
            "bids_volume": bids_volume.tolist(),
            "asks_price": asks_price.tolist(),
            "asks_volume": asks_volume.tolist()
        }
    }

def generate_mock_performance_metrics() -> Dict[str, Any]:
    n_points = 100
    time = [
        (datetime.now() - pd.Timedelta(days=x)).strftime("%Y-%m-%d")
        for x in range(n_points-1, -1, -1)
    ]
    returns = np.cumsum(np.random.normal(0.001, 0.02, n_points))
    
    return {
        "total_returns": returns[-1] * 100,
        "win_rate": random.uniform(40, 60),
        "sharpe_ratio": random.uniform(0.5, 2.5),
        "time": time,
        "cumulative_returns": returns.tolist()
    }

# API路由
@app.get("/api/strategy/status")
async def get_strategy_status() -> Dict[str, Any]:
    """获取策略状态数据"""
    return generate_mock_strategy_status()

@app.get("/api/market/data/{symbol}")
async def get_market_data(symbol: str) -> Dict[str, Any]:
    """获取市场行情数据"""
    return generate_mock_market_data(symbol)

@app.get("/api/performance/metrics")
async def get_performance_metrics() -> Dict[str, Any]:
    """获取性能指标数据"""
    return generate_mock_performance_metrics()

@app.get("/status", response_model=SystemStatus, tags=["系统"])
async def get_system_status() -> Dict[str, Any]:
    """获取系统状态"""
    try:
        return {
            "monitor_status": "运行中",
            "trading_status": "运行中",
            "api_status": "运行中",
            "active_exchanges": ["binance", "okx", "bybit", "huobi", "gateio"],
            "monitored_symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT"],
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/opportunities", response_model=List[ArbitrageOpportunity], tags=["交易"])
async def get_arbitrage_opportunities() -> List[Dict[str, Any]]:
    """获取当前套利机会"""
    try:
        # 这里应该从实际系统获取数据
        opportunities = []
        for i in range(3):
            opportunities.append({
                "type": "spread_arbitrage",
                "symbol": "BTC/USDT",
                "buy_exchange": "binance",
                "sell_exchange": "okx",
                "buy_price": 40000 + random.uniform(-100, 100),
                "sell_price": 40100 + random.uniform(-100, 100),
                "profit_usdt": random.uniform(5, 20),
                "profit_percent": random.uniform(0.1, 0.5),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        return opportunities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs", tags=["系统"])
async def get_system_logs(lines: Optional[int] = 100) -> Dict[str, Any]:
    """获取系统日志"""
    try:
        log_file = "logs/arbitrage.log"
        if not os.path.exists(log_file):
            return {"logs": [], "message": "日志文件不存在"}
            
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            return {
                "logs": all_lines[-lines:],
                "total_lines": len(all_lines)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trades", response_model=List[TradeRecord], tags=["交易"])
async def get_trade_records(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: Optional[int] = 100
) -> List[Dict[str, Any]]:
    """获取交易记录"""
    try:
        trade_file = "data/trade_data/trades.csv"
        if not os.path.exists(trade_file):
            return []
            
        df = pd.read_csv(trade_file)
        if start_time:
            df = df[df["timestamp"] >= start_time]
        if end_time:
            df = df[df["timestamp"] <= end_time]
            
        return df.tail(limit).to_dict("records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prices/{symbol}", tags=["市场数据"])
async def get_price_history(
    symbol: str,
    exchange: Optional[str] = None,
    interval: Optional[str] = "1m",
    limit: Optional[int] = 1000
) -> Dict[str, Any]:
    """获取价格历史数据"""
    try:
        price_file = f"data/price_data/{symbol.replace('/', '_')}_{interval}.csv"
        if not os.path.exists(price_file):
            return {"prices": [], "message": "价格数据不存在"}
            
        df = pd.read_csv(price_file)
        if exchange:
            df = df[df["exchange"] == exchange]
            
        return {
            "symbol": symbol,
            "interval": interval,
            "prices": df.tail(limit).to_dict("records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True) 