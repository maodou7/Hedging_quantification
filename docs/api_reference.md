# API 参考文档

## 核心模块 API

### ModelTrainer

模型训练器类，负责模型的训练、评估和预测。

```python
class ModelTrainer:
    def train_model(self, X: np.ndarray, y: np.ndarray, model_type: str = 'lstm',
                   **kwargs) -> Tuple[str, Dict, Dict]:
        """
        训练模型并返回模型ID和训练指标。

        参数:
            X (np.ndarray): 输入特征数据，shape=(n_samples, seq_len, n_features)
            y (np.ndarray): 目标变量，shape=(n_samples,)
            model_type (str): 模型类型，可选 'lstm' 或 'xgboost'
            **kwargs: 其他模型参数

        返回:
            Tuple[str, Dict, Dict]: (模型ID, 评估指标, 训练历史)
        """
        pass

    def predict(self, model_id: str, X: np.ndarray) -> np.ndarray:
        """
        使用指定模型进行预测。

        参数:
            model_id (str): 模型ID
            X (np.ndarray): 输入特征数据

        返回:
            np.ndarray: 预测结果
        """
        pass
```

### PriceMonitor

价格监控器，负责实时市场数据的获取和处理。

```python
class PriceMonitor:
    def start_monitoring(self, symbols: List[str], callback: Callable):
        """
        开始监控指定交易对的价格。

        参数:
            symbols (List[str]): 交易对列表
            callback (Callable): 价格更新回调函数
        """
        pass

    def get_latest_price(self, symbol: str) -> Dict:
        """
        获取最新价格数据。

        参数:
            symbol (str): 交易对

        返回:
            Dict: 价格信息字典
        """
        pass
```

### ExchangeFactory

交易所工厂类，负责创建和管理交易所连接。

```python
class ExchangeFactory:
    def create_exchange(self, exchange_name: str, config: Dict) -> Exchange:
        """
        创建交易所实例。

        参数:
            exchange_name (str): 交易所名称
            config (Dict): 配置信息

        返回:
            Exchange: 交易所实例
        """
        pass
```

## 数据处理 API

### FeatureEngineering

特征工程类，负责数据预处理和特征提取。

```python
class FeatureEngineering:
    def process_raw_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        处理原始数据并生成特征。

        参数:
            data (pd.DataFrame): 原始数据

        返回:
            pd.DataFrame: 处理后的特征数据
        """
        pass

    def extract_features(self, data: pd.DataFrame, feature_config: Dict) -> pd.DataFrame:
        """
        根据配置提取特征。

        参数:
            data (pd.DataFrame): 输入数据
            feature_config (Dict): 特征配置

        返回:
            pd.DataFrame: 提取的特征
        """
        pass
```

## 策略模块 API

### TradingStrategy

交易策略基类，定义了策略接口。

```python
class TradingStrategy:
    def generate_signals(self, market_data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号。

        参数:
            market_data (pd.DataFrame): 市场数据

        返回:
            pd.Series: 交易信号
        """
        pass

    def calculate_position_size(self, signal: float,
                              account_info: Dict) -> float:
        """
        计算仓位大小。

        参数:
            signal (float): 交易信号
            account_info (Dict): 账户信息

        返回:
            float: 仓位大小
        """
        pass
```

## 风险管理 API

### RiskManager

风险管理器，负责风险控制和仓位管理。

```python
class RiskManager:
    def check_risk_limits(self, order: Dict) -> bool:
        """
        检查订单是否符合风险限制。

        参数:
            order (Dict): 订单信息

        返回:
            bool: 是否通过风险检查
        """
        pass

    def calculate_stop_loss(self, position: Dict) -> float:
        """
        计算止损价格。

        参数:
            position (Dict): 持仓信息

        返回:
            float: 止损价格
        """
        pass
```

## 使用示例

### 模型训练和预测

```python
from src.ml.model_trainer import ModelTrainer
import numpy as np

# 初始化训练器
trainer = ModelTrainer()

# 准备数据
X = np.random.randn(1000, 10, 33)  # (样本数, 序列长度, 特征数)
y = np.random.randn(1000)  # 目标变量

# 训练模型
model_id, metrics, history = trainer.train_model(
    X, y,
    model_type='lstm',
    learning_rate=0.001,
    batch_size=32,
    epochs=100
)

# 预测
predictions = trainer.predict(model_id, X[:5])
```

### 实时价格监控

```python
from src.exchange.price_monitor import PriceMonitor

def price_callback(price_data):
    print(f"New price: {price_data}")

# 初始化监控器
monitor = PriceMonitor()

# 开始监控
monitor.start_monitoring(
    symbols=['BTC/USDT', 'ETH/USDT'],
    callback=price_callback
)
```

### 特征工程

```python
from src.ml.feature_engineering import FeatureEngineering
import pandas as pd

# 初始化特征工程器
fe = FeatureEngineering()

# 准备数据
data = pd.DataFrame(...)

# 配置特征
feature_config = {
    'technical_indicators': ['RSI', 'MACD', 'BB'],
    'time_features': ['hour', 'day_of_week'],
    'market_features': ['volume', 'trades']
}

# 提取特征
features = fe.extract_features(data, feature_config)
```

## ModelTrainer 类

### 初始化

```python
trainer = ModelTrainer(model_dir="models")
```

参数：

- `model_dir` (str): 模型保存目录，默认为 "models"

### 主要方法

#### train_model

```python
model_id, metrics, history = trainer.train_model(X, y, model_type=None)
```

训练新模型。

参数：

- `X` (np.ndarray): 形状为 (samples, sequence_length, features) 的输入数据
- `y` (np.ndarray): 形状为 (samples,) 的目标变量
- `model_type` (str, 可选): 模型类型，可选 'lstm' 或 'xgboost'。如果为 None，将使用配置中的默认模型

返回：

- `model_id` (str): 模型 ID
- `metrics` (dict): 模型评估指标
- `history` (dict): 训练历史

#### predict

```python
predictions = trainer.predict(model_id, X)
```

使用指定模型进行预测。

参数：

- `model_id` (str): 模型 ID
- `X` (np.ndarray): 输入数据

返回：

- `predictions` (np.ndarray): 预测结果

#### save_model

```python
success = trainer.save_model(model_id)
```

保存模型到文件。

参数：

- `model_id` (str): 要保存的模型 ID

返回：

- `success` (bool): 是否保存成功

#### load_model

```python
success = trainer.load_model(model_id)
```

从文件加载模型。

参数：

- `model_id` (str): 要加载的模型 ID

返回：

- `success` (bool): 是否加载成功

#### delete_model

```python
success = trainer.delete_model(model_id)
```

删除指定模型。

参数：

- `model_id` (str): 要删除的模型 ID

返回：

- `success` (bool): 是否删除成功

#### get_feature_importance

```python
importance = trainer.get_feature_importance(model_id, feature_names)
```

获取特征重要性（仅支持 XGBoost 模型）。

参数：

- `model_id` (str): 模型 ID
- `feature_names` (List[str]): 特征名称列表

返回：

- `importance` (Dict[str, float]): 特征重要性得分字典

## LSTMModel 类

### 初始化

```python
model = LSTMModel(input_size, hidden_size, num_layers=2, dropout=0.2)
```

参数：

- `input_size` (int): 输入特征维度
- `hidden_size` (int): LSTM 隐藏层大小
- `num_layers` (int): LSTM 层数
- `dropout` (float): Dropout 比率

### 主要方法

#### forward

```python
output = model(x)
```

前向传播。

参数：

- `x` (torch.Tensor): 形状为 (batch_size, seq_len, input_size) 的输入数据

返回：

- `output` (torch.Tensor): 模型输出

## TimeSeriesDataset 类

### 初始化

```python
dataset = TimeSeriesDataset(X, y)
```

参数：

- `X` (np.ndarray): 输入数据
- `y` (np.ndarray): 目标变量

### 方法

#### **len**

返回数据集长度。

#### **getitem**

获取指定索引的数据样本。

参数：

- `idx` (int): 样本索引

返回：

- `(X[idx], y[idx])`: 数据样本对
