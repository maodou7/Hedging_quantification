# 三角套利策略

## 策略原理

三角套利是一种利用同一资产在不同交易对之间的价格差异进行套利的策略。通过在三个或更多交易对之间进行一系列交易，最终回到初始货币，从而获取无风险收益。

### 核心特点

1. 无风险套利
2. 高频交易
3. 多市场监控
4. 实时价格追踪

## 参数配置

### 基础参数

- `base_currency`: 基础货币，如 "USDT"
- `exchanges`: 交易所列表
- `min_profit_rate`: 最小利润率

### 交易参数

- `max_trade_amount`: 最大交易金额
- `min_trade_amount`: 最小交易金额
- `execution_timeout`: 执行超时时间(秒)

### 风控参数

- `max_position`: 最大持仓量
- `max_order_count`: 最大订单数量
- `stop_loss_rate`: 止损率

## 使用方法

1. 导入策略类：
```python
from strategies.triangular_arbitrage.strategy import TriangularArbitrageStrategy
```

2. 创建策略实例：
```python
config = {
    'base_currency': 'USDT',
    'exchanges': ['binance', 'huobi'],
    'min_profit_rate': 0.001,
    'max_trade_amount': 1000,
    'min_trade_amount': 10
}

strategy = TriangularArbitrageStrategy(config)
```

3. 启动策略：
```python
strategy.start()
```

## 风险提示

1. 交易延迟风险
2. 流动性风险
3. 交易成本影响
4. 市场价格波动风险

## 策略优化建议

1. 优化路径搜索算法
2. 实现智能订单分配
3. 添加市场深度分析
4. 优化执行时机判断