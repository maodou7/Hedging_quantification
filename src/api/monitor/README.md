# 监控模块API接口文档

## 简介

监控模块提供了一系列API接口，用于查询和监控系统运行状态、交易所连接状态、性能指标以及系统日志等信息。

## 接口列表

### 1. 获取系统状态

```
GET /monitor/system
```

**请求URL示例：**
```
http://localhost:8000/api/v1/monitor/system
```

**curl示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/monitor/system"
```

获取当前系统的运行状态，包括监控状态、交易状态、API状态等信息。

**响应示例：**
```json
{
    "monitor_status": "running",
    "trading_status": "active",
    "api_status": "healthy",
    "active_exchanges": ["binance", "huobi"],
    "monitored_symbols": ["BTC/USDT", "ETH/USDT"],
    "last_update": "2024-01-01T12:00:00.000Z"
}
```

### 2. 获取交易所连接状态

```
GET /monitor/exchanges
```

**请求URL示例：**
```
http://localhost:8000/api/v1/monitor/exchanges
```

**curl示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/monitor/exchanges"
```

获取所有交易所的连接状态信息，包括连接状态、API延迟等。

**响应示例：**
```json
[
    {
        "exchange_name": "binance",
        "connection_status": "connected",
        "api_latency": 50.5,
        "last_update": "2024-01-01T12:00:00.000Z"
    }
]
```

### 3. 获取性能指标

```
GET /monitor/performance
```

**请求URL示例：**
```
http://localhost:8000/api/v1/monitor/performance
```

**curl示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/monitor/performance"
```

获取系统性能指标，包括CPU使用率、内存使用率、网络延迟等。

**响应示例：**
```json
{
    "cpu_usage": 45.5,
    "memory_usage": 60.2,
    "network_latency": {
        "binance": 50.5,
        "huobi": 65.3
    },
    "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### 4. 获取系统日志

```
GET /monitor/logs
```

**请求URL示例：**
```
http://localhost:8000/api/v1/monitor/logs?level=INFO&module=monitor&limit=100
```

**curl示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/monitor/logs?level=INFO&module=monitor&limit=100"
```

查询系统日志信息，支持按日志级别、模块、时间范围等条件过滤。

**查询参数：**

- `level`: 日志级别过滤（可选）
- `module`: 模块名称过滤（可选）
- `start_time`: 开始时间（可选）
- `end_time`: 结束时间（可选）
- `limit`: 返回条数限制，默认100条

**响应示例：**
```json
[
    {
        "timestamp": "2024-01-01T12:00:00.000Z",
        "level": "INFO",
        "module": "monitor",
        "message": "系统运行正常"
    }
]
```

## 错误处理

所有接口在发生错误时会返回相应的HTTP状态码和错误信息：

- 404: 请求的资源不存在
- 500: 服务器内部错误

**错误响应示例：**
```json
{
    "detail": "错误信息描述"
}
```

## 注意事项

1. 所有时间相关的字段均使用ISO 8601格式的UTC时间
2. 性能指标的采样周期为1分钟
3. 日志查询默认返回最近100条记录，可通过limit参数调整