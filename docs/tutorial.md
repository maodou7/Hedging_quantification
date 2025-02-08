# 使用教程

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 基本用法

#### 训练新模型

```python
import numpy as np
from src.ml.model_trainer import ModelTrainer

# 准备数据
X = np.random.randn(1000, 10, 33)  # (样本数, 序列长度, 特征数)
y = np.random.randn(1000)  # 目标变量

# 创建训练器
trainer = ModelTrainer()

# 训练模型
model_id, metrics, history = trainer.train_model(X, y, model_type='lstm')

# 打印评估指标
print(f"模型评估指标: {metrics}")
```

#### 保存和加载模型

```python
# 保存模型
trainer.save_model(model_id)

# 创建新的训练器实例
new_trainer = ModelTrainer()

# 加载模型
new_trainer.load_model(model_id)

# 使用加载的模型进行预测
predictions = new_trainer.predict(model_id, X[:5])
```

#### 特征重要性分析（XGBoost）

```python
# 训练XGBoost模型
model_id, metrics, history = trainer.train_model(X, y, model_type='xgboost')

# 创建特征名称
feature_names = [f'feature_{i}' for i in range(X.shape[2] * X.shape[1])]

# 获取特征重要性
importance = trainer.get_feature_importance(model_id, feature_names)

# 显示前10个最重要的特征
sorted_importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10])
print(f"前10个最重要的特征: {sorted_importance}")
```

## 高级用法

### 1. 自定义 LSTM 模型

您可以通过继承 `LSTMModel` 类来创建自定义的 LSTM 模型：

```python
class CustomLSTMModel(LSTMModel):
    def __init__(self, input_size, hidden_size, num_layers=2):
        super().__init__(input_size, hidden_size, num_layers)
        # 添加自定义层
        self.additional_layer = nn.Linear(hidden_size, hidden_size)

    def forward(self, x):
        # 调用父类的forward方法
        out = super().forward(x)
        # 添加自定义处理
        out = self.additional_layer(out)
        return out
```

### 2. 自定义数据集

您可以通过继承 `TimeSeriesDataset` 类来创建自定义的数据集：

```python
class CustomDataset(TimeSeriesDataset):
    def __init__(self, X, y, transform=None):
        super().__init__(X, y)
        self.transform = transform

    def __getitem__(self, idx):
        X, y = super().__getitem__(idx)
        if self.transform:
            X = self.transform(X)
        return X, y
```

### 3. 批量预测

对于大量数据的预测，可以使用批处理来提高效率：

```python
def batch_predict(trainer, model_id, X, batch_size=32):
    predictions = []
    for i in range(0, len(X), batch_size):
        batch = X[i:i + batch_size]
        pred = trainer.predict(model_id, batch)
        predictions.extend(pred)
    return np.array(predictions)
```

## 最佳实践

1. 数据预处理

   - 确保输入数据已经正确归一化
   - 处理缺失值
   - 检查数据的时间序列特性

2. 模型选择

   - LSTM 适合捕捉长期依赖关系
   - XGBoost 适合处理非线性关系和特征交互

3. 模型训练

   - 使用早停来防止过拟合
   - 定期保存模型检查点
   - 监控训练和验证损失

4. 模型评估

   - 使用多个指标评估模型性能
   - 进行交叉验证
   - 分析预测误差的分布

5. 生产部署
   - 定期重新训练模型
   - 监控模型性能
   - 实现模型版本控制

## 常见问题

1. Q: 模型训练时内存不足怎么办？
   A: 可以减小批次大小或使用数据生成器

2. Q: 如何处理不同长度的序列？
   A: 可以使用填充（padding）或截断（truncation）

3. Q: 预测结果不稳定怎么办？
   A: 可以使用集成方法或增加训练数据量

4. Q: 如何选择最佳的序列长度？
   A: 可以通过网格搜索或基于业务领域知识来确定
