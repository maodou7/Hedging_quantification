# 交易模块API接口文档

## 简介

交易模块提供了一系列API接口，用于管理交易订单、查询持仓和交易记录等功能。支持多交易所、多币种的交易操作。

## 接口列表

### 1. 创建订单

```
POST /trading/orders
```

**请求URL示例：**
```
http://localhost:8000/api/v1/trading/orders
```

**curl示例：**
```bash
curl -X POST "http://localhost:8000/api/v1/trading/orders" \
     -H "Content-Type: application/json" \
     -d '{
         "symbol": "BTC/USDT",
         "exchange": "binance",
         "order_type": "limit",
         "side": "buy",
         "amount": "0.1",
         "price": "50000"
     }'
```

创建新的交易订单。

**请求参数：**
```json
{
    "symbol": "BTC/USDT",
    "exchange": "binance",
    "order_type": "limit",
    "side": "buy",
    "amount": "0.1",
    "price": "50000",
    "stop_price": null
}
```

**响应示例：**
```json
{
    "order_id": "test_order_001",
    "symbol": "BTC/USDT",
    "exchange": "binance",
    "order_type": "limit",
    "side": "buy",
    "amount": "0.1",
    "price": "50000",
    "status": "created",
    "create_time": "2024-01-01T12:00:00.000Z"
}
```

### 2. 取消订单

```
DELETE /trading/orders/{order_id}
```

**请求URL示例：**
```
http://localhost:8000/api/v1/trading/orders/test_order_001
```

**curl示例：**
```bash
curl -X DELETE "http://localhost:8000/api/v1/trading/orders/test_order_001"
```

取消指定ID的订单。

**响应示例：**
```json
{
    "status": "success",
    "message": "订单 test_order_001 已取消"
}
```

### 3. 查询订单

```
GET /trading/orders/{order_id}
```

**请求URL示例：**
```
http://localhost:8000/api/v1/trading/orders/test_order_001
```

**curl示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/trading/orders/test_order_001"
```

查询指定ID的订单详情。

**响应示例：**
```json
{
    "order_id": "test_order_001",
    "symbol": "BTC/USDT",
    "exchange": "binance",
    "order_type": "limit",
    "side": "buy",
    "amount": "0.1",
    "price": "50000",
    "status": "filled",
    "create_time": "2024-01-01T12:00:00.000Z"
}
```

### 4. 查询持仓

```
GET /trading/positions
```

**请求URL示例：**
```
http://localhost:8000/api/v1/trading/positions?symbol=BTC/USDT&exchange=binance
```

**curl示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/trading/positions?symbol=BTC/USDT&exchange=binance"
```

查询当前持仓情况，支持按交易对和交易所过滤。

**查询参数：**
- `symbol`: 交易对过滤（可选）
- `exchange`: 交易所过滤（可选）

**响应示例：**
```json
[
    {
        "symbol": "BTC/USDT",
        "exchange": "binance",
        "amount": "0.1",
        "avg_price": "50000",
        "unrealized_pnl": "100",
        "realized_pnl": "200",
        "update_time": "2024-01-01T12:00:00.000Z"
    }
]
```

### 5. 查询交易记录

```
GET /trading/trades
```

**请求URL示例：**
```
http://localhost:8000/api/v1/trading/trades?symbol=BTC/USDT&exchange=binance&limit=100
```

**curl示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/trading/trades?symbol=BTC/USDT&exchange=binance&limit=100"
```

查询历史交易记录，支持多种过滤条件。

**查询参数：**
- `symbol`: 交易对过滤（可选）
- `exchange`: 交易所过滤（可选）
- `start_time`: 开始时间（可选）
- `end_time`: 结束时间（可选）
- `limit`: 返回条数限制，默认100条

**响应示例：**
```json
[
    {
        "trade_id": "test_trade_001",
        "order_id": "test_order_001",
        "symbol": "BTC/USDT",
        "exchange": "binance",
        "side": "buy",
        "amount": "0.1",
        "price": "50000",
        "fee": "0.1",
        "pnl": "100",
        "trade_time": "2024-01-01T12:00:00.000Z"
    }
]
```

## 错误处理

所有接口在发生错误时会返回相应的HTTP状态码和错误信息：

- 400: 请求参数错误
- 404: 请求的资源不存在
- 500: 服务器内部错误

**错误响应示例：**
```json
{
    "detail": "错误信息描述"
}
```

## 注意事项

1. 所有金额相关的字段均使用字符串格式，避免浮点数精度问题
2. 时间相关的字段均使用ISO 8601格式的UTC时间
3. 订单状态包括：created（已创建）、filled（已成交）、canceled（已取消）、rejected（已拒绝）
4. 交易方向（side）只能是buy或sell