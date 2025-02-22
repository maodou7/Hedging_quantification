# 网格交易策略

## 策略原理

网格交易策略是一种在预设价格区间内，通过设置多个等距价格网格，在不同价格点位自动执行买入和卖出操作的交易策略。当价格下跌时买入，上涨时卖出，通过高抛低吸获取收益。

### 核心特点

1. 预设交易区间
2. 等距网格划分
3. 自动双向交易
4. 风险可控

## 参数配置

### 基础参数

- `symbol`: 交易对，如 "BTC/USDT"
- `exchange`: 交易所，如 "binance"

### 网格参数

- `grid_num`: 网格数量，建议10-50之间
- `upper_price`: 网格上限价格
- `lower_price`: 网格下限价格
- `grid_invest_amount`: 每格投资金额(USDT)

### 风控参数

- `max_position`: 最大持仓量
- `stop_loss_pct`: 止损百分比
- `take_profit_pct`: 止盈百分比

### 执行参数

- `order_type`: 订单类型(market/limit)
- `price_precision`: 价格精度
- `amount_precision`: 数量精度
- `min_amount`: 最小交易量
- `min_notional`: 最小交易金额

## 使用方法

1. 导入策略类：
```python
from strategies.grid_trading.strategy import GridTradingStrategy
```

2. 创建策略实例：
```python
config = {
    'symbol': 'BTC/USDT',
    'exchange': 'binance',
    'grid_num': 20,
    'upper_price': 50000.0,
    'lower_price': 40000.0,
    'grid_invest_amount': 1000
}

strategy = GridTradingStrategy(config)
```

3. 注册市场数据回调：
```python
def on_market_data(tick_data):
    strategy.on_tick(tick_data)
```

## 风险提示

1. 网格策略适合震荡行情，不适合单边趋势市场
2. 建议在波动率较大的币种上使用
3. 合理设置网格参数，避免资金过度分散
4. 注意设置止损，控制风险

## 策略优化建议

1. 根据市场波动动态调整网格间距
2. 结合技术指标优化入场时机
3. 考虑加入趋势判断，避免逆势交易
4. 实现资金管理，控制单网格风险