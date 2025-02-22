# 系统配置说明文档

## 简介

本文档详细说明了系统的各项配置参数及其使用方法，包括交易所配置、风险控制参数、性能监控设置等。

## 配置文件列表

### 1. exchange_config.py

交易所连接配置，包含API密钥、请求限制等设置。

```python
EXCHANGE_CONFIG = {
    "binance": {
        "api_key": "your_api_key",
        "secret_key": "your_secret_key",
        "rate_limit": 1200,  # 每分钟请求限制
        "timeout": 10000,   # 请求超时时间（毫秒）
    }
}
```

### 2. risk_config.py

风险控制参数配置。

```python
RISK_CONFIG = {
    "max_position_value": 100000,  # 最大持仓价值（USDT）
    "max_order_value": 10000,     # 单笔订单最大价值
    "max_leverage": 3,           # 最大杠杆倍数
    "stop_loss_rate": 0.05      # 止损比例
}
```

### 3. monitor_config.py

系统监控配置。

```python
MONITOR_CONFIG = {
    "performance_check_interval": 60,  # 性能检查间隔（秒）
    "log_level": "INFO",             # 日志级别
    "alert_threshold": {              # 告警阈值
        "cpu_usage": 80,             # CPU使用率阈值
        "memory_usage": 85,          # 内存使用率阈值
        "api_latency": 1000          # API延迟阈值（毫秒）
    }
}
```

### 4. trading_config.py

交易相关配置。

```python
TRADING_CONFIG = {
    "default_fee_rate": 0.001,     # 默认手续费率
    "min_profit_rate": 0.002,     # 最小利润率
    "order_timeout": 60,          # 订单超时时间（秒）
    "price_precision": {          # 价格精度设置
        "BTC/USDT": 2,
        "ETH/USDT": 2
    }
}
```

## 配置文件加载流程

1. 系统启动时首先加载默认配置
2. 检查环境变量中的配置覆盖
3. 加载用户自定义配置文件
4. 验证配置参数的有效性

## 配置更新方法

### 1. 直接修改配置文件

修改对应的配置文件内容，系统重启后生效。

### 2. 环境变量覆盖

通过设置环境变量覆盖默认配置：

```bash
export EXCHANGE_API_KEY="new_api_key"
export RISK_MAX_POSITION=200000
```

### 3. 运行时更新

部分配置支持运行时动态更新：

```python
from config import ConfigManager

ConfigManager.update_risk_config({
    "max_position_value": 150000
})
```

## 配置验证规则

系统会对配置参数进行验证，确保：

1. 必需参数不为空
2. 参数类型正确
3. 数值在合理范围内
4. 配置之间的依赖关系正确

## 最佳实践

1. 使用环境变量管理敏感信息
2. 定期备份配置文件
3. 在测试环境验证配置更改
4. 记录配置变更日志
5. 使用版本控制管理配置文件

## 常见问题

### 1. 配置未生效

- 检查配置文件格式是否正确
- 确认系统是否需要重启
- 验证环境变量是否正确设置

### 2. 参数验证失败

- 检查参数类型是否正确
- 确认参数值是否在允许范围内
- 查看日志获取详细错误信息

### 3. 配置冲突

- 检查多个配置文件之间的优先级
- 确认环境变量未意外覆盖配置
- 验证配置之间的依赖关系

## API接口请求示例

### 1. 市场数据接口

#### 获取交易对行情

```bash
# 请求URL
GET http://localhost:8000/api/v1/market/ticker?symbol=BTC/USDT

# curl示例
curl -X GET "http://localhost:8000/api/v1/market/ticker?symbol=BTC/USDT"

# 返回数据
{
    "code": 0,
    "data": {
        "symbol": "BTC/USDT",
        "price": "45000.00",
        "volume": "1000.5",
        "timestamp": 1645084800000
    }
}
```

#### 获取深度数据

```bash
# 请求URL
GET http://localhost:8000/api/v1/market/depth?symbol=BTC/USDT&limit=10

# curl示例
curl -X GET "http://localhost:8000/api/v1/market/depth?symbol=BTC/USDT&limit=10"
```

### 2. 系统监控接口

#### 获取系统状态

```bash
# 请求URL
GET http://localhost:8000/api/v1/monitor/status

# curl示例
curl -X GET "http://localhost:8000/api/v1/monitor/status"

# 返回数据
{
    "code": 0,
    "data": {
        "cpu_usage": 45.5,
        "memory_usage": 60.2,
        "api_latency": 150,
        "uptime": 86400
    }
}
```

#### 获取策略运行状态

```bash
# 请求URL
GET http://localhost:8000/api/v1/monitor/strategy?name=triangular_arbitrage

# curl示例
curl -X GET "http://localhost:8000/api/v1/monitor/strategy?name=triangular_arbitrage"
```

### 3. 交易接口

#### 下单接口

```bash
# 请求URL
POST http://localhost:8000/api/v1/trade/order

# curl示例
curl -X POST "http://localhost:8000/api/v1/trade/order" \
     -H "Content-Type: application/json" \
     -d '{
         "symbol": "BTC/USDT",
         "type": "limit",
         "side": "buy",
         "price": "45000",
         "amount": "0.1"
     }'
```