# 市场数据API接口文档

## 简介

市场数据模块提供了一系列API接口，用于获取实时行情、K线数据、深度数据等市场信息。支持多个交易所的数据查询和订阅。

## 接口列表

### 1. 获取实时行情

```
GET /market/ticker/{symbol}
```

**请求URL示例：**
```
http://localhost:8000/api/v1/market/ticker?symbol=BTC/USDT&exchange=binance
```

**curl示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/market/ticker?symbol=BTC/USDT&exchange=binance"
```

获取指定交易对的实时行情数据。

**查询参数：**
- `symbol`: 交易对名称（必需）
- `exchange`: 交易所名称（可选）

**响应示例：**
```json
{
    "symbol": "BTC/USDT",
    "exchange": "binance",
    "last_price": "50000",
    "bid_price": "49999",
    "ask_price": "50001",
    "volume_24h": "1000",
    "price_change_24h": "2.5%",
    "high_24h": "51000",
    "low_24h": "49000",
    "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### 2. 获取K线数据

```
GET /market/klines/{symbol}
```

**请求URL示例：**
```
http://localhost:8000/api/v1/market/klines?symbol=BTC/USDT&interval=1h&limit=100
```

**curl示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/market/klines?symbol=BTC/USDT&interval=1h&limit=100"
```

获取指定交易对的K线历史数据。

**查询参数：**
- `symbol`: 交易对名称（必需）
- `exchange`: 交易所名称（可选）
- `interval`: K线间隔，如1m、5m、1h、1d等（必需）
- `start_time`: 开始时间（可选）
- `end_time`: 结束时间（可选）
- `limit`: 返回条数限制，默认500条

**响应示例：**
```json
[
    {
        "timestamp": "2024-01-01T12:00:00.000Z",
        "open": "50000",
        "high": "50100",
        "low": "49900",
        "close": "50050",
        "volume": "100"
    }
]
```

### 3. 获取深度数据

```
GET /market/depth/{symbol}
```

**请求URL示例：**
```
http://localhost:8000/api/v1/market/depth?symbol=BTC/USDT&limit=20
```

**curl示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/market/depth?symbol=BTC/USDT&limit=20"
```

获取指定交易对的订单簿深度数据。

**查询参数：**
- `symbol`: 交易对名称（必需）
- `exchange`: 交易所名称（可选）
- `limit`: 深度级别，默认20档

**响应示例：**
```json
{
    "symbol": "BTC/USDT",
    "exchange": "binance",
    "bids": [
        ["49999", "1.5"],
        ["49998", "2.0"]
    ],
    "asks": [
        ["50001", "1.0"],
        ["50002", "2.5"]
    ],
    "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### 4. 获取最新成交

```
GET /market/trades/{symbol}
```

**请求URL示例：**
```
http://localhost:8000/api/v1/market/trades?symbol=BTC/USDT&limit=50
```

**curl示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/market/trades?symbol=BTC/USDT&limit=50"
```

获取指定交易对的最新成交记录。

**查询参数：**
- `symbol`: 交易对名称（必需）
- `exchange`: 交易所名称（可选）
- `limit`: 返回条数限制，默认100条

**响应示例：**
```json
[
    {
        "id": "trade123",
        "symbol": "BTC/USDT",
        "exchange": "binance",
        "price": "50000",
        "amount": "0.1",
        "side": "buy",
        "timestamp": "2024-01-01T12:00:00.000Z"
    }
]
```

## 错误处理

所有接口在发生错误时会返回相应的HTTP状态码和错误信息：

- 400: 请求参数错误
- 404: 请求的资源不存在
- 429: 请求频率超限
- 500: 服务器内部错误

**错误响应示例：**
```json
{
    "code": 400,
    "message": "无效的交易对"
}
```

## 使用建议

1. 建议使用WebSocket接口订阅实时数据
2. 合理设置请求频率，避免触发限制
3. 对接收到的数据进行本地缓存
4. 实现错误重试机制
5. 注意处理数据延迟和断线重连