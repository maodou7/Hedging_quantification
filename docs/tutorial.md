\_\_# 量化交易系统使用教程

## 1. 系统安装

### 1.1 环境要求

- Python 3.8+
- Redis 服务器
- 交易所 API 密钥

### 1.2 安装步骤

```bash
# 1. 克隆代码库
git clone [repository_url]

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的配置信息
```

## 2. 策略配置

### 2.1 选择运行模式

#### 单一策略模式

```python
# 在 src/config/exchange.py 中设置
FEATURE_FLAGS = {
    "strategies": {
        "mode": "single",  # 设置为单一策略模式
        "triangular_arbitrage": {
            "enabled": True,  # 启用三角套利
            ...
        },
        "statistical_arbitrage": {
            "enabled": False,  # 禁用其他策略
            ...
        },
        ...
    }
}
```

#### 混合策略模式

```python
FEATURE_FLAGS = {
    "strategies": {
        "mode": "mixed",  # 设置为混合策略模式
        "mixed_strategy": {
            "enabled": True,
            "strategy_weights": {
                "triangular_arbitrage": 0.3,
                "statistical_arbitrage": 0.2,
                ...
            }
        }
    }
}
```

### 2.2 配置具体策略

#### 三角套利策略配置

```python
"triangular_arbitrage": {
    "enabled": True,
    "min_profit_threshold": 0.001,  # 设置最小利润率
    "pairs": ["BTC/USDT", "ETH/USDT", "ETH/BTC"],  # 设置交易对
    ...
}
```

#### 统计套利策略配置

```python
"statistical_arbitrage": {
    "enabled": True,
    "window_size": 3600,  # 设置观察窗口
    "z_score_threshold": 2.0,  # 设置z分数阈值
    ...
}
```

## 3. 风险管理配置

### 3.1 全局风险控制

```python
"risk_management": {
    "max_position_size": 1000,  # 设置最大持仓
    "max_daily_loss": 100,      # 设置最大日亏损
    "max_drawdown": 0.1         # 设置最大回撤
}
```

### 3.2 策略级别风险控制

```python
"risk_limits": {
    "max_total_position": 50000,
    "max_single_strategy_loss": 1000,
    ...
}
```

## 4. 启动和监控

### 4.1 启动系统

```bash
# 启动主程序
python main.py
```

### 4.2 监控系统运行

```python
# 检查日志
tail -f logs/system.log

# 查看性能指标
python tools/monitor_performance.py
```

## 5. 策略优化

### 5.1 参数优化

1. 分析历史数据
2. 进行回测验证
3. 小资金实盘测试
4. 根据结果调整参数

### 5.2 机器学习模型训练

```python
# 配置模型参数
"machine_learning": {
    "enabled": True,
    "min_data_points": 1000,
    "models": {
        "lstm": {
            "enabled": True,
            "sequence_length": 60
        }
    }
}
```

## 6. 常见问题处理

### 6.1 连接问题

- 检查网络连接
- 验证 API 密钥
- 确认交易所服务状态

### 6.2 订单问题

- 检查资金是否充足
- 验证交易对是否可用
- 确认价格精度设置

### 6.3 性能问题

- 监控系统资源使用
- 优化数据处理流程
- 调整更新频率

## 7. 维护和更新

### 7.1 日常维护

- 检查日志文件
- 备份重要数据
- 更新市场参数

### 7.2 系统更新

- 定期更新依赖
- 同步最新代码
- 测试新功能

## 8. 应急处理

### 8.1 风险控制触发

1. 立即检查持仓状态
2. 确认触发原因
3. 采取必要措施

### 8.2 系统异常

1. 停止策略运行
2. 保存现场数据
3. 分析错误日志
4. 修复并重启

## 9. 性能优化

### 9.1 数据处理优化

- 使用缓存
- 优化查询
- 清理历史数据

### 9.2 策略优化

- 调整更新频率
- 优化计算逻辑
- 改进执行流程
