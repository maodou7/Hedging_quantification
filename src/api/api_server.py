"""
API服务器

提供:
1. 策略状态数据
2. 市场行情数据
3. 性能指标数据
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any
from datetime import datetime
import uvicorn
import random
import numpy as np
from pydantic import BaseModel

app = FastAPI(title="量化交易回测数据API")

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

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True) 