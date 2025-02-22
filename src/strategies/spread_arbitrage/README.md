# 价差套利策略

## 策略原理

价差套利是一种利用同一资产在不同交易所或不同交易对之间的价格差异进行套利的策略。通过在价格较低的市场买入，同时在价格较高的市场卖出，赚取价差收益。

### 核心特点

1. 多市场监控
2. 实时套利
3. 价格差异捕捉
4. 快速执行

## 参数配置

### 基础参数

- `symbol`: 交易对，如 "BTC/USDT"
- `exchanges`: 交易所列表
- `min_spread_rate`: 最小价差率

### 交易参数

- `trade_amount`: 单次交易金额
- `max_slippage`: 最大滑点容忍度
- `execution_timeout`: 执行超时时间(秒)

### 风控参数

- `max_exposure`: 最大敞口
- `max_order_count`: 最大订单数量
- `stop_loss_rate`: 止损率

## 使用方法

1. 导入策略类：
```python
from strategies.spread_arbitrage.strategy import SpreadArbitrageStrategy
```

2. 创建策略实例：
```python
config = {
    'symbol': 'BTC/USDT',
    'exchanges': ['binance', 'huobi'],
    'min_spread_rate': 0.001,
    'trade_amount': 1000,
    'max_slippage': 0.0005
}

strategy = SpreadArbitrageStrategy(config)
```

3. 启动策略：
```python
strategy.start()
```

## 风险提示

1. 价格同步风险
2. 交易延迟风险
3. 流动性风险
4. 交易成本影响

## 策略优化建议

1. 优化价格监控机制
2. 实现智能路由系统
3. 优化订单执行策略
4. 加入深度分析模块