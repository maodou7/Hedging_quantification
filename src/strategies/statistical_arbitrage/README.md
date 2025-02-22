# 统计套利策略

## 策略原理

统计套利是一种基于统计学原理，通过发现和利用金融市场中资产价格的统计规律进行交易的策略。该策略通常通过对历史数据进行分析，找出具有相关性的资产组合，在价格偏离统计均值时进行交易。

### 核心特点

1. 数据驱动
2. 均值回归
3. 多品种组合
4. 风险中性

## 参数配置

### 基础参数

- `symbol_pairs`: 交易对列表
- `lookback_period`: 回看周期
- `correlation_threshold`: 相关性阈值

### 统计参数

- `z_score_threshold`: Z分数阈值
- `mean_reversion_threshold`: 均值回归阈值
- `vol_window`: 波动率计算窗口

### 风控参数

- `max_position`: 最大持仓量
- `position_limit`: 单个交易对持仓限制
- `stop_loss_std`: 止损标准差倍数

## 使用方法

1. 导入策略类：
```python
from strategies.statistical_arbitrage.strategy import StatisticalArbitrageStrategy
```

2. 创建策略实例：
```python
config = {
    'symbol_pairs': [('BTC/USDT', 'ETH/USDT')],
    'lookback_period': 100,
    'correlation_threshold': 0.8,
    'z_score_threshold': 2.0
}

strategy = StatisticalArbitrageStrategy(config)
```

3. 启动策略：
```python
strategy.start()
```

## 风险提示

1. 相关性失效风险
2. 均值回归周期不确定
3. 市场结构性变化风险
4. 交易成本影响

## 策略优化建议

1. 引入机器学习模型
2. 优化配对选择算法
3. 动态调整阈值参数
4. 加入多因子分析