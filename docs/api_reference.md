# API 参考文档

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
