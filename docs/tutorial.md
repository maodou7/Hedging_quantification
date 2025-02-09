# 使用教程

## 快速入门

本教程将指导您如何使用对冲量化交易系统进行模型训练、回测和实盘交易。

### 环境准备

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 配置环境变量

创建 `.env` 文件并设置以下环境变量：

```bash
EXCHANGE_API_KEY=your_api_key
EXCHANGE_SECRET_KEY=your_secret_key
MODEL_CHECKPOINT_DIR=./checkpoints
DATA_CACHE_DIR=./cache
LOG_LEVEL=INFO
```

3. 配置交易所

在 `src/Config/exchange_config.yaml` 中配置交易所参数：

```yaml
exchange:
  name: binance
  test_mode: true # 设置为 false 进行实盘交易
  symbols:
    - BTC/USDT
    - ETH/USDT
  timeframes:
    - 1m
    - 5m
    - 15m
```

## 数据收集和预处理

### 1. 获取历史数据

```python
from src.exchange.market_structure_fetcher import MarketStructureFetcher
from datetime import datetime, timedelta

# 初始化数据获取器
fetcher = MarketStructureFetcher()

# 设置时间范围
end_time = datetime.now()
start_time = end_time - timedelta(days=30)

# 获取历史数据
data = fetcher.fetch_historical_data(
    symbol='BTC/USDT',
    timeframe='1h',
    start_time=start_time,
    end_time=end_time
)
```

### 2. 数据预处理

```python
from src.ml.feature_engineering import FeatureEngineering

# 初始化特征工程器
fe = FeatureEngineering()

# 配置特征
feature_config = {
    'technical_indicators': ['RSI', 'MACD', 'BB'],
    'time_features': ['hour', 'day_of_week'],
    'market_features': ['volume', 'trades']
}

# 生成特征
features = fe.extract_features(data, feature_config)

# 数据清洗和标准化
processed_data = fe.process_raw_data(features)
```

## 模型训练

### 1. 准备训练数据

```python
from src.ml.model_trainer import ModelTrainer
import numpy as np

# 准备特征和标签
X = processed_data.drop('target', axis=1).values
y = processed_data['target'].values

# 重塑数据为 LSTM 格式
sequence_length = 10
X_reshaped = np.array([X[i:i+sequence_length]
                       for i in range(len(X)-sequence_length)])
y_reshaped = y[sequence_length:]
```

### 2. 训练模型

```python
# 初始化训练器
trainer = ModelTrainer()

# 训练 LSTM 模型
model_id, metrics, history = trainer.train_model(
    X_reshaped,
    y_reshaped,
    model_type='lstm',
    learning_rate=0.001,
    batch_size=32,
    epochs=100,
    validation_split=0.2
)

print(f"训练完成，模型ID: {model_id}")
print(f"验证集性能: {metrics}")
```

## 回测

### 1. 设置回测参数

```python
from src.core.backtester import Backtester

# 初始化回测器
backtester = Backtester(
    initial_capital=10000,
    commission_rate=0.001,
    risk_free_rate=0.02
)

# 配置回测参数
backtest_config = {
    'start_date': '2024-01-01',
    'end_date': '2024-02-01',
    'symbol': 'BTC/USDT',
    'timeframe': '1h',
    'position_size': 0.1  # 每次交易使用 10% 的资金
}
```

### 2. 运行回测

```python
# 运行回测
results = backtester.run(
    model_id=model_id,
    config=backtest_config
)

# 分析结果
print(f"夏普比率: {results['sharpe_ratio']}")
print(f"最大回撤: {results['max_drawdown']}")
print(f"年化收益率: {results['annual_return']}")
```

## 实盘交易

### 1. 配置交易参数

```python
from src.core.trader import Trader
from src.core.risk_manager import RiskManager

# 初始化风险管理器
risk_manager = RiskManager(
    max_position_size=0.1,
    stop_loss_pct=0.02,
    take_profit_pct=0.05
)

# 初始化交易器
trader = Trader(
    exchange_name='binance',
    model_id=model_id,
    risk_manager=risk_manager
)
```

### 2. 启动交易

```python
# 配置交易参数
trading_config = {
    'symbols': ['BTC/USDT'],
    'timeframe': '1h',
    'update_interval': 60  # 每60秒更新一次
}

# 启动交易
trader.start_trading(config=trading_config)
```

## 监控和日志

### 1. 查看交易日志

```python
from src.utils.logger import get_logger

logger = get_logger('trading')

# 查看最近的交易日志
logger.get_recent_logs(n=10)
```

### 2. 监控性能指标

```python
from src.utils.monitor import PerformanceMonitor

monitor = PerformanceMonitor()

# 获取实时性能指标
metrics = monitor.get_current_metrics()
print(f"当前收益率: {metrics['current_return']}")
print(f"持仓成本: {metrics['position_cost']}")
print(f"未实现盈亏: {metrics['unrealized_pnl']}")
```

## 高级功能

### 1. 自定义策略

```python
from src.core.strategy import TradingStrategy

class CustomStrategy(TradingStrategy):
    def generate_signals(self, market_data):
        # 实现自定义信号生成逻辑
        pass

    def calculate_position_size(self, signal, account_info):
        # 实现自定义仓位计算逻辑
        pass
```

### 2. 多模型集成

```python
from src.ml.model_ensemble import ModelEnsemble

# 创建模型集成
ensemble = ModelEnsemble([
    ('lstm', model_id_1, 0.4),
    ('xgboost', model_id_2, 0.3),
    ('lightgbm', model_id_3, 0.3)
])

# 使用集成模型进行预测
predictions = ensemble.predict(X_test)
```

## 故障排除

### 1. 常见问题

- 数据延迟：检查网络连接和 API 限制
- 订单执行失败：验证账户余额和交易限制
- 模型性能不佳：检查特征工程和超参数

### 2. 错误处理

```python
try:
    trader.place_order(order)
except InsufficientFundsError:
    logger.error("账户余额不足")
    risk_manager.reduce_position_size()
except APIError as e:
    logger.error(f"API 错误: {e}")
    trader.retry_order(order)
```

## 最佳实践

1. 定期备份模型和配置
2. 使用测试网进行验证
3. 实施严格的风险控制
4. 监控系统性能
5. 保持日志更新
