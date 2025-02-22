# 期现套利策略

## 策略原理

期现套利是利用同一资产在现货市场和期货市场之间的价格差异进行套利的策略。通过同时在现货和期货市场建立相反方向的头寸，赚取价差收益，同时对冲市场风险。

### 核心特点

1. 市场中性
2. 低风险收益
3. 双向交易
4. 基差交易

## 参数配置

### 基础参数

- `symbol`: 交易对，如 "BTC/USDT"
- `futures_symbol`: 期货合约，如 "BTC-PERP"
- `min_spread`: 最小价差率

### 交易参数

- `position_size`: 单次开仓数量
- `max_leverage`: 最大杠杆倍数
- `funding_threshold`: 资金费率阈值

### 风控参数

- `max_position`: 最大持仓量
- `stop_loss_pct`: 止损百分比
- `margin_ratio`: 保证金率

## 使用方法

1. 导入策略类：
```python
from strategies.spot_futures_arbitrage.strategy import SpotFuturesArbitrageStrategy
```

2. 创建策略实例：
```python
config = {
    'symbol': 'BTC/USDT',
    'futures_symbol': 'BTC-PERP',
    'min_spread': 0.002,
    'position_size': 0.1,
    'max_leverage': 3
}

strategy = SpotFuturesArbitrageStrategy(config)
```

3. 启动策略：
```python
strategy.start()
```

## 风险提示

1. 基差收敛风险
2. 资金费率影响
3. 交易成本损耗
4. 流动性风险

## 策略优化建议

1. 优化基差预测模型
2. 引入资金费率策略
3. 动态调整持仓比例
4. 优化交易时机选择