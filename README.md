# 对冲量化交易系统

## 项目简介

这是一个基于深度学习和机器学习的对冲量化交易系统，支持多种模型（LSTM 和 XGBoost）进行市场预测。

## 主要特性

- 支持多种深度学习和机器学习模型
  - LSTM 用于时序预测
  - XGBoost 用于特征驱动预测
- 完整的模型生命周期管理
  - 模型训练
  - 模型评估
  - 模型保存/加载
  - 模型预测
- 特征工程和数据预处理
- 模型性能评估和监控
- 特征重要性分析

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
