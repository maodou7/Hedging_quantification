"""市场数据API接口

提供市场数据相关的API接口，包括：
1. 实时行情数据
2. K线数据
3. 深度数据
4. 交易对信息
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal

# 创建路由
router = APIRouter(
    prefix="/market",
    tags=["市场数据"],
    responses={404: {"description": "Not found"}},
)

# 数据模型
class TickerData(BaseModel):
    """实时行情数据模型"""
    symbol: str = Field(..., description="交易对，例如：BTC/USDT")
    exchange: str = Field(..., description="交易所名称，例如：binance")
    last_price: Decimal = Field(..., description="最新成交价")
    bid_price: Decimal = Field(..., description="买一价")
    ask_price: Decimal = Field(..., description="卖一价")
    volume_24h: Decimal = Field(..., description="24小时成交量")
    price_change_24h: Decimal = Field(..., description="24小时价格变化百分比")
    high_24h: Decimal = Field(..., description="24小时最高价")
    low_24h: Decimal = Field(..., description="24小时最低价")
    timestamp: str = Field(..., description="数据时间戳，ISO格式的UTC时间")

class KlineData(BaseModel):
    """K线数据模型"""
    symbol: str = Field(..., description="交易对，例如：BTC/USDT")
    exchange: str = Field(..., description="交易所名称，例如：binance")
    timestamp: str = Field(..., description="K线时间戳，ISO格式的UTC时间")
    open: Decimal = Field(..., description="开盘价")
    high: Decimal = Field(..., description="最高价")
    low: Decimal = Field(..., description="最低价")
    close: Decimal = Field(..., description="收盘价")
    volume: Decimal = Field(..., description="成交量")

class OrderBookData(BaseModel):
    """深度数据模型"""
    symbol: str = Field(..., description="交易对，例如：BTC/USDT")
    exchange: str = Field(..., description="交易所名称，例如：binance")
    bids: List[List[Decimal]] = Field(..., description="买单列表，格式：[[价格, 数量], ...]")
    asks: List[List[Decimal]] = Field(..., description="卖单列表，格式：[[价格, 数量], ...]")
    timestamp: str = Field(..., description="数据时间戳，ISO格式的UTC时间")

# API路由
@router.get("/ticker/{base_currency}/{quote_currency}", 
    response_model=TickerData,
    summary="获取实时行情",
    description="""
    获取指定交易对的实时行情数据
    
    参数说明：
    * base_currency: 基础货币，例如：BTC
    * quote_currency: 计价货币，例如：USDT
    * exchange: 交易所名称（可选），不指定则使用默认交易所
    
    返回数据包括：
    * 最新成交价
    * 买一价/卖一价
    * 24小时成交量
    * 24小时价格变化
    * 24小时最高/最低价
    * 数据时间戳
    """
)
async def get_ticker(
    base_currency: str,
    quote_currency: str,
    exchange: Optional[str] = None
) -> Dict:
    """获取实时行情数据"""
    try:
        symbol = f"{base_currency}/{quote_currency}"
        # TODO: 实现实际的数据获取逻辑
        return {
            "symbol": symbol,
            "exchange": exchange or "binance",
            "last_price": Decimal("50000"),
            "bid_price": Decimal("49999"),
            "ask_price": Decimal("50001"),
            "volume_24h": Decimal("1000"),
            "price_change_24h": Decimal("2.5"),
            "high_24h": Decimal("51000"),
            "low_24h": Decimal("49000"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/klines/{base_currency}/{quote_currency}",
    response_model=List[KlineData],
    summary="获取K线数据",
    description="""
    获取指定交易对的K线数据
    
    参数说明：
    * base_currency: 基础货币，例如：BTC
    * quote_currency: 计价货币，例如：USDT
    * interval: K线间隔，支持：1m（1分钟）, 5m, 15m, 30m, 1h, 4h, 1d
    * limit: 返回K线数量，最大1000条
    * exchange: 交易所名称（可选），不指定则使用默认交易所
    
    返回数据包括：
    * 开盘价/收盘价
    * 最高价/最低价
    * 成交量
    * K线时间戳
    """
)
async def get_klines(
    base_currency: str,
    quote_currency: str,
    interval: str = Query("1m", description="K线间隔，如1m, 5m, 1h, 1d"),
    limit: int = Query(100, le=1000),
    exchange: Optional[str] = None
) -> List[Dict]:
    """获取K线数据"""
    try:
        symbol = f"{base_currency}/{quote_currency}"
        # TODO: 实现实际的数据获取逻辑
        klines = []
        current_time = datetime.now()
        for i in range(limit):
            klines.append({
                "symbol": symbol,
                "exchange": exchange or "binance",
                "timestamp": current_time.isoformat(),
                "open": Decimal("50000"),
                "high": Decimal("50100"),
                "low": Decimal("49900"),
                "close": Decimal("50050"),
                "volume": Decimal("100")
            })
        return klines
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/depth/{base_currency}/{quote_currency}",
    response_model=OrderBookData,
    summary="获取深度数据",
    description="""
    获取指定交易对的订单簿深度数据
    
    参数说明：
    * base_currency: 基础货币，例如：BTC
    * quote_currency: 计价货币，例如：USDT
    * limit: 返回深度档数，最大100档
    * exchange: 交易所名称（可选），不指定则使用默认交易所
    
    返回数据包括：
    * 买单列表：按价格降序排列的[价格, 数量]列表
    * 卖单列表：按价格升序排列的[价格, 数量]列表
    * 数据时间戳
    """
)
async def get_order_book(
    base_currency: str,
    quote_currency: str,
    limit: int = Query(20, le=100),
    exchange: Optional[str] = None
) -> Dict:
    """获取深度数据"""
    try:
        symbol = f"{base_currency}/{quote_currency}"
        # TODO: 实现实际的数据获取逻辑
        return {
            "symbol": symbol,
            "exchange": exchange or "binance",
            "bids": [[Decimal("49999"), Decimal("1.5")], [Decimal("49998"), Decimal("2.0")]],
            "asks": [[Decimal("50001"), Decimal("1.0")], [Decimal("50002"), Decimal("2.5")]],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/status")
async def get_market_status():
    """获取市场状态"""
    return {
        "status": "running",
        "message": "市场数据服务正常运行"
    }