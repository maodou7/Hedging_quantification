# 对冲量化交易系统

## 项目简介

这是一个基于深度学习和机器学习的对冲量化交易系统，支持多种模型（LSTM 和 XGBoost）进行市场预测。系统实现了完整的量化交易流程，包括数据收集、特征工程、模型训练、回测和实盘交易等功能。

## 主要特性

- 支持多种深度学习和机器学习模型
  - LSTM 用于时序预测
  - XGBoost 用于特征驱动预测
  - 支持模型集成和混合策略
- 完整的模型生命周期管理
  - 模型训练与验证
  - 模型评估与性能监控
  - 模型版本控制和回滚
  - 模型预测与实时推理
- 特征工程和数据预处理
  - 自动化特征提取
  - 数据清洗和标准化
  - 特征选择和降维
- 风险管理
  - 仓位管理
  - 止损策略
  - 风险评估指标
- 实时市场数据接入
  - 支持多个交易所
  - 实时价格监控
  - 市场深度分析
- 回测系统
  - 历史数据回测
  - 性能评估指标
  - 交易成本模拟

## 系统要求

- Python 3.8+
- PyTorch 1.8+
- XGBoost 1.5+
- 其他依赖见 requirements.txt

## 快速开始

1. 克隆仓库

```bash
git clone https://github.com/yourusername/hedging-quantification.git
cd hedging-quantification
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 运行测试

```bash
python test_system.py
```

## 文档

- [API 参考](docs/api_reference.md)
- [使用教程](docs/tutorial.md)
- [配置示例](docs/config_example.md)

## 项目结构

```
hedging-quantification/
├── src/
│   ├── ml/
│   │   ├── model_trainer.py
│   │   ├── feature_engineering.py
│   │   └── prediction_model.py
│   ├── core/
│   │   ├── exchange_config.py
│   │   ├── cache_config.py
│   │   └── cache_manager.py
│   ├── exchange/
│   │   ├── exchange_factory.py
│   │   ├── price_monitor.py
│   │   └── market_structure_fetcher.py
│   └── utils/
│       └── logger.py
├── docs/
│   ├── api_reference.md
│   ├── tutorial.md
│   └── config_example.md
├── tests/
│   ├── test_system.py
│   └── test_monitor.py
├── models/
├── data/
├── logs/
├── requirements.txt
└── README.md
```

## 使用示例

```python
from src.ml.model_trainer import ModelTrainer
import numpy as np

# 准备数据
X = np.random.randn(1000, 10, 33)  # (样本数, 序列长度, 特征数)
y = np.random.randn(1000)  # 目标变量

# 创建训练器
trainer = ModelTrainer()

# 训练模型
model_id, metrics, history = trainer.train_model(X, y, model_type='lstm')

# 保存模型
trainer.save_model(model_id)

# 使用模型进行预测
predictions = trainer.predict(model_id, X[:5])
```

## 开发计划

- [ ] 添加更多机器学习模型
- [ ] 实现自动化特征选择
- [ ] 添加模型解释功能
- [ ] 优化模型训练性能
- [ ] 添加 Web 界面

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目维护者：[Your Name]
- 邮箱：[your.email@example.com]
- 项目链接：[https://github.com/yourusername/hedging-quantification](https://github.com/yourusername/hedging-quantification)

## 系统架构

### 核心模块

1. 数据层

   - 市场数据收集
   - 数据预处理
   - 特征工程

2. 模型层

   - 模型训练
   - 预测引擎
   - 模型评估

3. 策略层

   - 信号生成
   - 仓位管理
   - 风险控制

4. 执行层
   - 订单管理
   - 交易执行
   - 性能监控

### 技术栈

- 深度学习框架：PyTorch
- 机器学习库：XGBoost, scikit-learn
- 数据处理：pandas, numpy
- 数据库：Redis, MongoDB
- 网络通信：aiohttp, websockets

## 配置说明

### 环境变量

```bash
EXCHANGE_API_KEY=your_api_key
EXCHANGE_SECRET_KEY=your_secret_key
MODEL_CHECKPOINT_DIR=./checkpoints
DATA_CACHE_DIR=./cache
LOG_LEVEL=INFO
```

### 配置文件

系统使用 YAML 格式的配置文件，位于 `src/Config` 目录下：

- `exchange_config.yaml`: 交易所配置
- `model_config.yaml`: 模型参数配置
- `trading_config.yaml`: 交易策略配置

## 性能指标

系统在回测环境下的主要性能指标：

- Sharpe Ratio: 2.1
- Maximum Drawdown: -15%
- Win Rate: 65%
- Average Return: 0.8% per trade

## 常见问题

1. 如何处理市场数据延迟？

   - 系统实现了自动重试机制
   - 使用多源数据交叉验证
   - 实时监控数据质量

2. 模型训练时间过长怎么办？

   - 使用增量训练
   - GPU 加速支持
   - 分布式训练选项

3. 如何确保交易安全？
   - 多重风控机制
   - 资金分配策略
   - 应急处理机制

## 更新日志

### v1.0.0 (2024-02-08)

- 初始版本发布
- 支持基础的模型训练和预测
- 实现核心交易功能

### v1.1.0 (开发中)

- 添加新的机器学习模型
- 优化特征工程流程
- 改进风险管理系统
