# Hedging Quantification - 对冲量化系统

[English](README.md) | [简体中文](README_CN.md)

一个高性能的加密货币交易所监控系统，支持多交易所实时价格追踪。

> **注意**：这是一个私有仓库，请确保您有必要的访问权限。

## 特性

- **多交易所支持**：同时监控多个加密货币交易所
- **实时价格监控**：基于 WebSocket 的实时价格更新
- **市场类型支持**：支持现货、期货和杠杆交易市场
- **高精度处理**：遵循 CCXT 标准的高级价格精度处理
- **市场参数**：全面的市场信息，包括：
  - 最小购买金额
  - 杠杆范围
  - 交易手续费（maker/taker）
  - 价格和数量精度
- **错误处理**：强大的错误处理和自动重连机制
- **跨平台**：针对 Windows 和 Linux 系统优化

## 系统要求

- Python 3.12.8
- ccxt
- asyncio

## 安装

1. 克隆仓库：

```bash
git clone https://github.com/maodou7/Hedging_quantification.git
cd Hedging_quantification
```

2. 创建并激活环境：

方式一 - 使用 Anaconda（推荐）：

```bash
# 列出所有环境
conda env list

# 创建新的 Python 3.12.8 环境
conda create -n hedging python=3.12.8

# 激活环境
conda activate hedging

# 使用完毕后退出环境
conda deactivate

# 如需删除环境
conda remove -n hedging --all
```

方式二 - 使用 venv：

Linux/macOS 系统：

```bash
python -m venv venv
source venv/bin/activate
```

Windows 系统：

```bash
python -m venv venv
.\venv\Scripts\activate
```

3. 安装依赖：

Linux/macOS 系统：

```bash
# 安装系统依赖
sudo apt-get update
sudo apt-get install python3-dev build-essential

# 安装Python依赖
pip install --upgrade pip
pip install -r requirements.txt

# 安装uvloop以提升性能（仅Linux系统）
pip install uvloop
```

Windows 系统：

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 配置

编辑 `Config/exchange_config.py` 进行配置：

- 需要监控的交易所
- 市场类型（现货/期货/杠杆）
- 计价货币
- 市场结构设置

配置示例：

```python
EXCHANGES = ['binance', 'bybit', 'okx']
MARKET_TYPES = {
    'spot': True,
    'future': True,
    'margin': False
}
QUOTE_CURRENCIES = ['USDT', 'BTC']
```

## 使用方法

运行主程序：

```bash
python main.py
```

程序将：

1. 初始化交易所连接
2. 查找共同交易对
3. 开始实时价格监控
4. 输出格式化的 JSON 价格数据

输出示例：

```json
{
  "exchange": "binance",
  "type": "spot",
  "symbol": "BTC/USDT",
  "quote": "USDT",
  "price": "45123.45",
  "min_cost": "5.0",
  "leverage": "1-100",
  "fees": {
    "taker": "0.001",
    "maker": "0.001"
  },
  "precision": {
    "price": 2,
    "amount": 6
  }
}
```

## 架构

- `main.py`: 主程序入口
- `ExchangeModules/`:
  - `exchange_instance.py`: 交易所连接管理
  - `monitor_manager.py`: 价格监控系统
  - `market_processor.py`: 市场数据处理
  - `common_symbols_finder.py`: 共同交易对检测
  - `market_structure_fetcher.py`: 市场结构处理

## 性能优化

- 自动事件循环优化：
  - Linux: 使用 `uvloop` 获得最佳性能
  - Windows: 使用 `WindowsSelectorEventLoopPolicy`
- 高效的 WebSocket 连接
- 优化的数据结构，实现快速查找

## 错误处理

- 全面的错误检测
- 自动重连机制
- 详细的错误报告
- 数据验证检查
