"""监控模块API接口

提供系统监控相关的API接口，包括：
1. 交易对状态监控
2. 程序交易状态监控
3. 系统性能监控
4. 日志查询
"""

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Set
from datetime import datetime
from decimal import Decimal
import asyncio
import json
from src.core.exchange_manager import exchange_manager

# 创建路由
router = APIRouter(
    prefix="/api/v1/monitor",
    tags=["监控接口"]
)

# 交易对状态数据模型
class MarketStatus(BaseModel):
    """交易对市场状态数据模型"""
    symbol: str = Field(..., description="交易对，例如：BTC/USDT")
    exchange: str = Field(..., description="交易所名称")
    price: Decimal = Field(..., description="当前价格")
    bid_price: Decimal = Field(..., description="买一价")
    ask_price: Decimal = Field(..., description="卖一价")
    volume_24h: Decimal = Field(..., description="24小时成交量")
    price_change_24h: Decimal = Field(..., description="24小时价格变化百分比")
    high_24h: Decimal = Field(..., description="24小时最高价")
    low_24h: Decimal = Field(..., description="24小时最低价")
    last_update: str = Field(..., description="最后更新时间，ISO格式的UTC时间")

class OrderBookStatus(BaseModel):
    """交易对深度数据模型"""
    symbol: str
    exchange: str
    bids: List[List[Decimal]]
    asks: List[List[Decimal]]
    last_update: str

# 程序交易状态数据模型
class TradingStatus(BaseModel):
    """程序交易状态数据模型"""
    strategy_name: str = Field(..., description="策略名称")
    status: str = Field(..., description="策略状态：running/stopped/error")
    active_orders: int = Field(..., description="当前活跃订单数量")
    total_positions: int = Field(..., description="当前持仓数量")
    realized_pnl: Decimal = Field(..., description="已实现盈亏")
    unrealized_pnl: Decimal = Field(..., description="未实现盈亏")
    trading_volume_24h: Decimal = Field(..., description="24小时交易量")
    last_trade_time: str = Field(..., description="最后交易时间，ISO格式的UTC时间")
    error_message: Optional[str] = None

class SystemStatus(BaseModel):
    """系统状态数据模型"""
    monitor_status: str = Field(..., description="监控系统状态：running/stopped")
    trading_status: str = Field(..., description="交易系统状态：active/inactive")
    api_status: str = Field(..., description="API服务状态：healthy/unhealthy")
    active_exchanges: List[str] = Field(..., description="当前活跃的交易所列表")
    active_strategies: List[str] = Field(..., description="当前运行的策略列表")
    monitored_symbols: List[str] = Field(..., description="监控中的交易对列表")
    last_update: str = Field(..., description="最后更新时间，ISO格式的UTC时间")

class ExchangeStatus(BaseModel):
    """交易所连接状态数据模型"""
    exchange_name: str = Field(..., description="交易所名称")
    connection_status: str = Field(..., description="连接状态：connected/disconnected")
    api_latency: float = Field(..., description="API延迟（毫秒）")
    websocket_status: str = Field(..., description="WebSocket状态：connected/disconnected")
    error_count_1h: int = Field(..., description="最近1小时错误次数")
    last_update: str = Field(..., description="最后更新时间，ISO格式的UTC时间")

class PerformanceMetrics(BaseModel):
    """性能指标数据模型"""
    cpu_usage: float
    memory_usage: float
    network_latency: Dict[str, float]
    order_latency: Dict[str, float]
    websocket_latency: Dict[str, float]
    timestamp: str

class LogEntry(BaseModel):
    """日志条目数据模型"""
    timestamp: str
    level: str
    module: str
    message: str

@router.get("/market/status", response_model=List[MarketStatus])
async def get_market_status(
    symbol: Optional[str] = Query(None, description="交易对过滤"),
    exchange: Optional[str] = Query(None, description="交易所过滤")
):
    """获取交易对市场状态
    
    Args:
        symbol: 交易对名称
        exchange: 交易所名称
        
    Returns:
        List[MarketStatus]: 交易对状态列表
    """
    # TODO: 实现交易对状态获取逻辑
    return [
        MarketStatus(
            symbol="BTC/USDT",
            exchange="binance",
            price=Decimal("50000"),
            bid_price=Decimal("49999"),
            ask_price=Decimal("50001"),
            volume_24h=Decimal("1000"),
            price_change_24h=Decimal("2.5"),
            high_24h=Decimal("51000"),
            low_24h=Decimal("49000"),
            last_update=datetime.now().isoformat()
        )
    ]

@router.get("/market/orderbook", response_model=OrderBookStatus)
async def get_orderbook_status(
    symbol: str = Query(..., description="交易对名称"),
    exchange: str = Query(..., description="交易所名称")
):
    """获取交易对深度数据
    
    Args:
        symbol: 交易对名称
        exchange: 交易所名称
        
    Returns:
        OrderBookStatus: 深度数据
    """
    # TODO: 实现深度数据获取逻辑
    return OrderBookStatus(
        symbol=symbol,
        exchange=exchange,
        bids=[[Decimal("49999"), Decimal("1.5")], [Decimal("49998"), Decimal("2.0")]],
        asks=[[Decimal("50001"), Decimal("1.0")], [Decimal("50002"), Decimal("2.5")]],
        last_update=datetime.now().isoformat()
    )

@router.get("/trading/status", response_model=List[TradingStatus])
async def get_trading_status(
    strategy: Optional[str] = Query(None, description="策略名称过滤")
):
    """获取程序交易状态
    
    Args:
        strategy: 策略名称
        
    Returns:
        List[TradingStatus]: 交易状态列表
    """
    # TODO: 实现交易状态获取逻辑
    return [
        TradingStatus(
            strategy_name="grid_trading",
            status="running",
            active_orders=5,
            total_positions=3,
            realized_pnl=Decimal("100.5"),
            unrealized_pnl=Decimal("50.2"),
            trading_volume_24h=Decimal("1000000"),
            last_trade_time=datetime.now().isoformat()
        )
    ]

from src.core.base_monitor import BaseMonitor

class MonitorAPI(BaseMonitor):
    def __init__(self):
        super().__init__()

    def _get_cpu_usage(self) -> float:
        # TODO: 实现CPU使用率获取逻辑
        return 45.5
    
    def _get_memory_usage(self) -> float:
        # TODO: 实现内存使用率获取逻辑
        return 60.2
    
    def _check_connection_status(self, exchange: str) -> str:
        # TODO: 实现连接状态检查逻辑
        return "connected"
    
    def _get_api_latency(self, exchange: str) -> float:
        # TODO: 实现API延迟获取逻辑
        return 50.5
    
    def _check_websocket_status(self, exchange: str) -> str:
        # TODO: 实现WebSocket状态检查逻辑
        return "connected"
    
    def _get_error_count(self, exchange: str) -> int:
        # TODO: 实现错误计数获取逻辑
        return 0

@router.get("/system",
    response_model=SystemStatus,
    summary="获取系统状态",
    description="""
    获取整个系统的运行状态信息
    
    返回数据包括：
    * 监控系统状态
    * 交易系统状态
    * API服务状态
    * 活跃交易所列表
    * 运行中的策略列表
    * 监控中的交易对
    * 最后更新时间
    """
)
async def get_system_status():
    """获取系统状态
    
    Returns:
        SystemStatus: 系统状态信息
    """
    monitor = MonitorAPI()
    metrics = monitor.get_system_metrics()
    return SystemStatus(
        monitor_status="running",
        trading_status="active",
        api_status="healthy",
        active_exchanges=["binance", "huobi"],
        active_strategies=["grid_trading", "arbitrage"],
        monitored_symbols=["BTC/USDT", "ETH/USDT"],
        last_update=metrics["timestamp"]
    )

@router.get("/exchanges", response_model=List[ExchangeStatus])
async def get_exchange_status():
    """获取所有交易所连接状态
    
    Returns:
        List[ExchangeStatus]: 交易所状态列表
    """
    # TODO: 实现交易所状态获取逻辑
    return [
        ExchangeStatus(
            exchange_name="binance",
            connection_status="connected",
            api_latency=50.5,
            websocket_status="connected",
            error_count_1h=0,
            last_update=datetime.now().isoformat()
        )
    ]

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics():
    """获取系统性能指标
    
    Returns:
        PerformanceMetrics: 性能指标数据
    """
    monitor = MonitorAPI()
    metrics = monitor.get_system_metrics()
    return PerformanceMetrics(
        cpu_usage=metrics["cpu_usage"],
        memory_usage=metrics["memory_usage"],
        network_latency={"binance": 50.5, "huobi": 65.3},
        order_latency={"binance": 100, "huobi": 120},
        websocket_latency={"binance": 30, "huobi": 40},
        timestamp=metrics["timestamp"]
    )

@router.get("/logs", response_model=List[LogEntry])
async def get_logs(
    level: Optional[str] = Query(None, description="日志级别过滤"),
    module: Optional[str] = Query(None, description="模块名称过滤"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    limit: int = Query(100, description="返回条数限制")
):
    """获取系统日志
    
    Args:
        level: 日志级别
        module: 模块名称
        start_time: 开始时间
        end_time: 结束时间
        limit: 返回条数限制
        
    Returns:
        List[LogEntry]: 日志条目列表
    """
    # TODO: 实现日志查询逻辑
    return [
        LogEntry(
            timestamp=datetime.now().isoformat(),
            level="INFO",
            module="monitor",
            message="系统运行正常"
        )
    ]

# 全局变量存储监控管理器实例
monitor_manager = None

def set_monitor_manager(manager):
    """设置监控管理器实例"""
    global monitor_manager
    monitor_manager = manager

class PriceInfo(BaseModel):
    """价格信息数据模型"""
    price: Decimal = Field(..., description="当前价格")
    exchange: str = Field(..., description="交易所名称")
    timestamp: str = Field(..., description="价格时间戳，ISO格式的UTC时间")

class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.latest_prices: Dict[str, Dict] = {}
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def broadcast_price(self, symbol: str, price_info: Dict):
        self.latest_prices[symbol] = price_info
        message = {
            "type": "price_update",
            "symbol": symbol,
            "data": price_info
        }
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                self.active_connections.remove(connection)
    
    def get_latest_prices(self) -> Dict[str, Dict]:
        return self.latest_prices

# 创建WebSocket管理器实例
websocket_manager = WebSocketManager()

@router.get("/prices",
    response_model=Dict[str, PriceInfo],
    summary="获取所有交易对的最新价格",
    description="""
    获取系统中所有监控交易对的最新价格信息。
    
    此API提供两种访问方式：
    1. HTTP GET请求：获取当前最新价格快照
    2. WebSocket连接：通过 /ws/prices 获取实时价格推送
    
    WebSocket示例：
    ```javascript
    const ws = new WebSocket('ws://127.0.0.1:8000/api/v1/monitor/ws/prices');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('收到价格更新:', data);
    };
    ```
    
    返回数据格式：
    {
        "BTC/USDT": {
            "price": "50000.00",
            "exchange": "binance",
            "timestamp": "2024-03-24T10:00:00Z"
        },
        ...
    }
    """
)
async def get_latest_prices():
    """获取所有交易对的最新价格"""
    if not monitor_manager:
        raise HTTPException(status_code=503, detail="监控系统未初始化")
    return websocket_manager.get_latest_prices()

# 在MonitorManager类中添加价格更新方法
async def update_price(symbol: str, exchange: str, price: Decimal):
    """更新交易对价格并通过WebSocket广播"""
    price_info = {
        "price": str(price),
        "exchange": exchange,
        "timestamp": datetime.now().isoformat()
    }
    await websocket_manager.broadcast_price(symbol, price_info)

@router.get("/prices/{exchange_id}", response_model=Dict[str, PriceInfo])
async def get_exchange_prices(exchange_id: str):
    """获取指定交易所的最新价格"""
    if not monitor_manager:
        raise HTTPException(status_code=503, detail="监控系统未初始化")
    prices = monitor_manager.get_latest_prices()
    exchange_prices = {
        key: value for key, value in prices.items()
        if value["exchange"] == exchange_id
    }
    if not exchange_prices:
        raise HTTPException(status_code=404, detail=f"未找到交易所 {exchange_id} 的价格数据")
    return exchange_prices

@router.get("/status",
    response_model=Dict[str, ExchangeStatus],
    summary="获取所有交易所的连接状态",
    description="""
    获取所有交易所的连接状态信息
    
    返回数据包括：
    * 连接状态
    * API延迟
    * WebSocket状态
    * 错误统计
    * 最后更新时间
    """
)
async def get_exchange_status():
    """获取所有交易所的连接状态"""
    if not monitor_manager:
        raise HTTPException(status_code=503, detail="监控系统未初始化")
    return monitor_manager.get_exchange_status()

@router.get("/status/{exchange_id}", response_model=ExchangeStatus)
async def get_single_exchange_status(exchange_id: str):
    """获取指定交易所的连接状态"""
    if not monitor_manager:
        raise HTTPException(status_code=503, detail="监控系统未初始化")
    status = monitor_manager.get_exchange_status().get(exchange_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"未找到交易所 {exchange_id} 的状态信息")
    return status

@router.get("/status")
async def get_monitor_status():
    """获取监控状态"""
    return {
        "status": "running",
        "message": "监控服务正常运行",
        "active_connections": len(websocket_manager.active_connections)
    }

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)
        
        # 移除断开的连接
        for conn in disconnected:
            self.active_connections.remove(conn)

# 创建全局连接管理器实例
manager = ConnectionManager()

async def get_exchange_status() -> Dict[str, bool]:
    """获取所有交易所的连接状态"""
    status = {}
    for exchange_id in exchange_manager.exchanges:
        try:
            exchange = exchange_manager.get_exchange(exchange_id)
            if exchange:
                # 测试连接
                await exchange_manager.test_connection(exchange)
                status[exchange_id] = True
            else:
                status[exchange_id] = False
        except:
            status[exchange_id] = False
    return status

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，用于实时推送系统状态"""
    await manager.connect(websocket)
    try:
        while True:
            # 获取交易所连接状态
            connection_status = await exchange_manager.get_connection_status()
            
            # 发送系统状态数据
            status_data = {
                "api_service_running": True,
                "websocket_connected": True,
                "data_monitoring_active": True,
                "exchange_status": connection_status,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_json(status_data)
            await asyncio.sleep(1)  # 每秒更新一次
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket错误: {str(e)}")
        manager.disconnect(websocket)

@router.get("/status")
async def get_monitor_status():
    """获取监控状态"""
    exchange_status = await get_exchange_status()
    return {
        "status": "running",
        "message": "监控服务正常运行",
        "active_connections": len(manager.active_connections),
        "exchange_status": exchange_status
    }