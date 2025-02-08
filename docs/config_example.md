# 配置示例

## 配置文件结构

配置文件采用 Python 字典格式，包含以下主要部分：

1. 模型训练配置
2. 模型评估配置
3. 特征工程配置
4. 日志配置

## 完整配置示例

```python
CONFIG = {
    'model_training': {
        'enabled': True,
        'config': {
            'default_model': 'lstm',
            'test_size': 0.2
        },
        'lstm': {
            'enabled': True,
            'units': 64,
            'dropout': 0.2,
            'batch_size': 32,
            'epochs': 100,
            'learning_rate': 0.001,
            'input_size': 33,
            'early_stopping': {
                'patience': 10
            },
            'checkpointing': {
                'enabled': True,
                'filepath': 'models/lstm_best.pth'
            }
        },
        'xgboost': {
            'enabled': True,
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1,
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'early_stopping_rounds': 10
        }
    },

    'model_evaluation': {
        'metrics': ['mse', 'rmse', 'mae', 'r2'],
        'cv_folds': 5,
        'test_size': 0.2
    },

    'feature_engineering': {
        'sequence_length': 10,
        'target_horizon': 1,
        'feature_selection': {
            'enabled': True,
            'method': 'correlation',
            'threshold': 0.1
        },
        'normalization': {
            'method': 'standard',
            'clip_outliers': True
        }
    },

    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(levelname)s - %(message)s',
        'file': {
            'enabled': True,
            'path': 'logs/training.log'
        }
    }
}
```

## 配置项说明

### 1. 模型训练配置

#### 通用配置

- `enabled`: 是否启用模型训练
- `default_model`: 默认使用的模型类型
- `test_size`: 测试集比例

#### LSTM 配置

- `units`: LSTM 隐藏层大小
- `dropout`: Dropout 比率
- `batch_size`: 批次大小
- `epochs`: 训练轮数
- `learning_rate`: 学习率
- `early_stopping`: 早停设置
  - `patience`: 早停等待轮数
- `checkpointing`: 模型检查点设置
  - `enabled`: 是否启用检查点
  - `filepath`: 检查点保存路径

#### XGBoost 配置

- `n_estimators`: 树的数量
- `max_depth`: 树的最大深度
- `learning_rate`: 学习率
- `objective`: 目标函数
- `eval_metric`: 评估指标
- `early_stopping_rounds`: 早停轮数

### 2. 模型评估配置

- `metrics`: 评估指标列表
- `cv_folds`: 交叉验证折数
- `test_size`: 测试集比例

### 3. 特征工程配置

- `sequence_length`: 序列长度
- `target_horizon`: 预测目标时间跨度
- `feature_selection`: 特征选择设置
  - `enabled`: 是否启用特征选择
  - `method`: 特征选择方法
  - `threshold`: 选择阈值
- `normalization`: 数据归一化设置
  - `method`: 归一化方法
  - `clip_outliers`: 是否裁剪异常值

### 4. 日志配置

- `level`: 日志级别
- `format`: 日志格式
- `file`: 文件日志设置
  - `enabled`: 是否启用文件日志
  - `path`: 日志文件路径

## 使用示例

```python
from src.core.exchange_config import get_ml_config
from src.ml.model_trainer import ModelTrainer

# 获取配置
config = get_ml_config()

# 创建训练器实例
trainer = ModelTrainer()

# 训练模型
model_id, metrics, history = trainer.train_model(X, y, model_type=config['model_training']['config']['default_model'])
```

## 配置最佳实践

1. 模型选择

   - 对于时序数据，优先使用 LSTM
   - 对于表格数据，优先使用 XGBoost
   - 可以同时训练多个模型进行对比

2. 超参数调优

   - LSTM
     - 序列长度根据数据特点选择
     - 隐藏层大小通常为特征维度的 1-2 倍
     - Dropout 率通常在 0.1-0.5 之间
   - XGBoost
     - 树的深度通常在 3-10 之间
     - 学习率通常在 0.01-0.3 之间

3. 早停策略

   - LSTM：patience 设置为 10-20 轮
   - XGBoost：early_stopping_rounds 设置为 10-50 轮

4. 数据划分

   - 时序数据推荐使用时间序列交叉验证
   - 测试集比例通常为 20%-30%

5. 特征工程
   - 启用特征选择以减少噪声
   - 使用标准化或最小最大缩放进行归一化
   - 考虑添加时间特征
