# 加密货币交易所数据监控系统 / Cryptocurrency Exchange Data Monitoring System

## 项目简介 / Project Description

这是一个高性能的异步加密货币交易所数据监控系统。该系统能够同时监控多个交易所的市场数据，并通过异步 IO 和并发处理来实现最大性能。

This is a high-performance asynchronous cryptocurrency exchange data monitoring system. The system can simultaneously monitor market data from multiple exchanges and achieve maximum performance through asynchronous IO and concurrent processing.

## 主要特性 / Key Features

- 多交易所并发监控 / Multi-exchange concurrent monitoring
- 自动错误恢复和重连机制 / Automatic error recovery and reconnection mechanism
- 高性能优化 / High-performance optimization
- 实时数据处理和状态更新 / Real-time data processing and status updates
- 智能系统适配 / Intelligent system adaptation
  - Linux: 使用 uvloop 实现最高性能 / Uses uvloop for maximum performance on Linux
  - Windows: 使用原生事件循环 / Uses native event loop on Windows

## 系统要求 / System Requirements

### 操作系统 / Operating System

- Linux (推荐 / Recommended)
- Windows
- 其他类 Unix 系统 / Other Unix-like systems

### Python 版本 / Python Version

- Python 3.7+

## 安装指南 / Installation Guide

1. 克隆仓库 / Clone the repository:

```bash
git clone [repository-url]
```

2. 安装依赖 / Install dependencies:

对于 Windows 系统 / For Windows:

```bash
pip install -r requirement.txt
```

对于 Linux 系统 / For Linux:

```bash
pip install -r requirement_linux.txt
```

## 配置说明 / Configuration Guide

1. 在`Config/exchange_config.py`中配置以下参数 / Configure the following parameters in `Config/exchange_config.py`:
   - 交易所列表 / Exchange list
   - 市场类型 / Market types
   - 计价货币 / Quote currencies
   - 市场结构配置 / Market structure configuration

## 使用方法 / Usage

直接运行主程序 / Run the main program directly:

```bash
python main.py
```

使用 Ctrl+C 可以安全地停止程序 / Use Ctrl+C to safely stop the program

## 项目结构 / Project Structure

```
├── Config/                 # 配置文件目录 / Configuration directory
├── ExchangeModules/       # 交易所模块 / Exchange modules
├── market_structures/      # 市场结构数据 / Market structure data
├── main.py                # 主程序 / Main program
├── requirement.txt        # Windows依赖要求 / Windows dependencies
└── requirement_linux.txt  # Linux依赖要求 / Linux dependencies
```

## 注意事项 / Notes

- 运行前请确保网络连接稳定 / Ensure stable network connection before running
- 建议在高性能服务器上运行以获得最佳性能 / Recommended to run on high-performance servers for best results
- 程序会自动处理断线重连，无需手动干预 / Program automatically handles disconnections and reconnections
- Linux 系统下会自动使用 uvloop 优化性能 / Automatically uses uvloop for performance optimization on Linux

## 性能优化 / Performance Optimization

- 使用异步 IO 实现高并发 / Uses async IO for high concurrency
- 自动选择最优事件循环 / Automatically selects optimal event loop
- 线程池优化 / Thread pool optimization
- 智能内存管理 / Intelligent memory management

## 错误处理 / Error Handling

系统包含完整的错误处理机制 / The system includes comprehensive error handling:

- 自动重连机制 / Automatic reconnection mechanism
- 错误日志记录 / Error logging
- 状态监控 / Status monitoring
- 异常恢复 / Exception recovery
