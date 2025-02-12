# 多策略加密货币套利系统

## 功能特点

- 支持多个主流交易所（Binance、Bybit、OKX、Huobi、Gate.io）
- 集成多种套利策略
- 支持机器学习预测
- 实时市场数据监控
- 灵活的策略配置
- 完整的风险管理

## 系统要求

### 基础环境

- Python >= 3.8
- Redis 服务器
- Linux（推荐）或 Windows 操作系统

### 硬件推荐配置

- CPU: 4 核心及以上
- 内存: 8GB 及以上
- 磁盘空间: 20GB 及以上
- 网络: 稳定的互联网连接

### 依赖组件

- CCXT: 用于交易所 API 集成
- FastAPI: Web 服务框架
- PyTorch/TensorFlow: 机器学习框架
- Redis: 缓存和消息队列
- PostgreSQL: 数据存储（可选）

## 文档导航

- [API 参考文档](docs/api_reference.md) - 详细的 API 接口说明和使用方法
- [使用教程](docs/tutorial.md) - 完整的安装、配置和使用步骤指南
- [配置示例](docs/config_example.md) - 所有配置项的详细说明和示例

## 系统概述

### 核心功能模块

1. 市场监控

   - 实时价格监控
   - 深度数据分析
   - 成交量跟踪

2. 机器学习预测

   - LSTM 模型支持
   - XGBoost 模型支持
   - 实时训练更新

3. 多策略支持

   - 三角套利
   - 统计套利
   - 期现套利
   - 价差套利

4. 风险管理
   - 全局风险控制
   - 策略级风险控制
   - 实时风险监控

## 快速开始

### 1. 安装

项目提供多种安装方式：

#### 基础安装

```bash
# 开发模式安装（推荐）
pip install -e .

# 或者直接安装
pip install .
```

#### 带开发工具安装

如果你需要进行开发或测试，可以安装开发依赖：

```bash
pip install -e .[dev]
```

#### 带文档工具安装

如果你需要构建文档，可以安装文档依赖：

```bash
pip install -e .[docs]
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的配置信息
```

### 3. 启动系统

```bash
python main.py
```

详细的配置和使用说明请参考[使用教程](docs/tutorial.md)。

## 注意事项

1. API 密钥安全

   - 确保 API 密钥安全保存
   - 避免密钥泄露

2. 风险控制

   - 建议先用小资金测试
   - 密切关注风险指标

3. 系统维护
   - 定期检查日志
   - 及时更新配置

## 更新日志

### v1.0.0 (2024-02-09)

- 初始版本发布
- 支持四种套利策略
- 集成机器学习预测
- 完整的风险管理系统

## 系统启动说明

### 环境配置

系统支持三种运行环境：

- 开发环境（development）：默认环境，支持热重载，适合开发调试
- 测试环境（testing）：用于测试部署
- 生产环境（production）：用于生产部署，性能优化

### 启动方式

1. 直接启动（推荐用于开发）：

```bash
# 开发环境
python start.py

# 测试环境
ENV=testing python start.py

# 生产环境
ENV=production python start.py
```

2. 使用系统服务（推荐用于生产）：

创建服务文件 `/etc/systemd/system/crypto-arbitrage.service`：

```ini
[Unit]
Description=Crypto Arbitrage Service
After=network.target

[Service]
Type=simple
User=root
Environment=ENV=production
WorkingDirectory=/root/Hedging_quantification
ExecStart=/usr/bin/python3 start.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

管理服务：

```bash
# 启用服务
systemctl enable crypto-arbitrage

# 启动服务
systemctl start crypto-arbitrage

# 查看状态
systemctl status crypto-arbitrage

# 停止服务
systemctl stop crypto-arbitrage

# 查看日志
journalctl -u crypto-arbitrage -f
```

### 配置说明

系统启动配置位于 `src/config/startup.py`，包含以下配置项：

1. 环境配置（environment）：

   - 开发/测试/生产环境配置
   - 服务器类型选择
   - 日志级别设置
   - 调试模式开关

2. 系统配置（system）：

   - Linux/Windows 系统适配
   - 进程管理参数
   - 系统资源限制

3. 资源配置（resources）：

   - worker 进程数量控制
   - 内存使用限制
   - 超时设置

4. 日志配置（logging）：

   - 日志格式
   - 文件日志设置
   - 日志轮转策略

5. 监控配置（monitoring）：

   - Prometheus 集成
   - 指标收集设置

6. 服务配置（service）：
   - 系统服务设置
   - 进程管理参数

### 性能优化

系统会根据硬件资源自动优化以下参数：

- Worker 进程数：根据 CPU 核心数和可用内存自动计算
- 文件描述符限制：Linux 系统下自动调整
- 临时文件存储：Linux 下使用内存文件系统
- 进程预加载：生产环境自动启用
- 请求限制：自动设置最大请求数和抖动值

### 故障处理

如果遇到启动问题：

1. 检查日志输出
2. 确认环境变量设置
3. 验证系统资源限制
4. 检查依赖包安装状态

## 许可证

MIT License

## 常见问题解决方案

### 1. 安装问题

#### pip 安装失败

```bash
# 尝试更新pip
python -m pip install --upgrade pip

# 如果安装特定包失败，可以尝试
pip install --no-cache-dir -e .

# 如果依赖冲突，可以创建新的虚拟环境
python -m venv venv
source venv/bin/activate  # Linux
venv\Scripts\activate     # Windows
pip install -e .
```

#### Linux 系统特定问题

- 如果遇到`uvicorn`相关的文件描述符错误，确保使用了正确的启动方式：
  ```bash
  # 生产环境使用gunicorn
  ENV=production python start.py
  ```
- 如果遇到权限问题，检查文件权限和用户权限：
  ```bash
  sudo chown -R $USER:$USER .
  chmod +x start.py
  ```

#### Windows 系统特定问题

- 如果安装`psycopg2`失败，可以尝试安装二进制版本：
  ```bash
  pip install psycopg2-binary
  ```
- 如果遇到`uvloop`相关错误，可以忽略，系统会自动使用替代方案

### 2. 运行问题

#### Redis 连接错误

- 检查 Redis 服务是否运行
- 验证 Redis 配置是否正确
- 确保防火墙允许 Redis 端口

#### 内存使用过高

- 调整`config/startup.py`中的 worker 数量
- 减少并发连接数
- 考虑增加系统内存

#### CPU 使用率过高

- 检查是否启用了过多的监控对
- 调整数据更新频率
- 优化机器学习模型参数

### 3. 性能优化

#### Linux 系统

- 使用`systemd`服务管理
- 启用`uvloop`
- 适当调整文件描述符限制
- 使用内存文件系统存储临时文件

#### Windows 系统

- 使用`Windows Terminal`而不是 cmd
- 关闭不必要的后台程序
- 调整 Windows 的性能选项

### 4. 开发相关

#### 测试

```bash
# 运行所有测试
pip install -e .[dev]
pytest

# 运行特定测试
pytest tests/test_exchange.py
```

#### 文档构建

```bash
# 安装文档工具
pip install -e .[docs]

# 构建文档
cd docs
make html
```

如果遇到其他问题，请查看详细的[使用教程](docs/tutorial.md)或提交 Issue。
