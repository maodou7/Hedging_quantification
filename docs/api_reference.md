# API 参考文档

## 策略接口

### 1. 三角套利策略 (TriangularArbitrageStrategy)

#### 配置参数

```python
{
    "enabled": bool,                    # 是否启用策略
    "min_profit_threshold": float,      # 最小利润率
    "max_trade_amount": float,          # 最大交易金额
    "pairs": List[str],                 # 三角套利对
    "update_interval": int,             # 更新间隔(秒)
    "execution_timeout": int,           # 执行超时时间(秒)
    "risk_control": {
        "max_slippage": float,          # 最大滑点
        "min_volume_threshold": float    # 最小交易量阈值
    }
}
```

#### 主要方法

```python
async def start()                       # 启动策略
async def stop()                        # 停止策略
async def process_price_update()        # 处理价格更新
async def calculate_opportunity()       # 计算套利机会
async def execute_trade()               # 执行交易
```

### 2. 统计套利策略 (StatisticalArbitrageStrategy)

#### 配置参数

```python
{
    "enabled": bool,                    # 是否启用策略
    "window_size": int,                 # 观察窗口大小(秒)
    "z_score_threshold": float,         # z分数阈值
    "pairs": List[List[str]],          # 配对交易对
    "position_holding_time": int,       # 持仓时间(秒)
    "max_position_value": float,        # 最大持仓价值
    "correlation_threshold": float      # 相关性阈值
}
```

#### 主要方法

```python
async def start()                       # 启动策略
async def stop()                        # 停止策略
async def calculate_z_score()           # 计算z分数
async def check_correlation()           # 检查相关性
async def execute_pair_trade()          # 执行配对交易
```

### 3. 期现套利策略 (SpotFutureArbitrageStrategy)

#### 配置参数

```python
{
    "enabled": bool,                    # 是否启用策略
    "min_spread_threshold": float,      # 最小价差阈值
    "max_leverage": int,                # 最大杠杆倍数
    "funding_rate_threshold": float,    # 资金费率阈值
    "pairs": List[str],                # 交易对
    "position_limit": Dict[str, float], # 各币种最大持仓量
    "hedge_ratio": float,              # 对冲比例
    "margin_ratio": float              # 保证金比例
}
```

#### 主要方法

```python
async def start()                       # 启动策略
async def stop()                        # 停止策略
async def calculate_basis()             # 计算基差
async def check_funding_rate()          # 检查资金费率
async def execute_hedge()               # 执行对冲交易
```

### 4. 价差套利策略 (SpreadArbitrageStrategy)

#### 配置参数

```python
{
    "enabled": bool,                    # 是否启用策略
    "min_profit_threshold": float,      # 最小利润阈值
    "trade_amount": float,             # 交易金额
    "max_open_orders": int,            # 最大挂单数
    "price_decimal": int,              # 价格小数位
    "amount_decimal": int,             # 数量小数位
    "update_interval": int,            # 更新间隔(秒)
    "execution_timeout": int           # 执行超时时间(秒)
}
```

#### 主要方法

```python
async def start()                       # 启动策略
async def stop()                        # 停止策略
async def process_price_update()        # 处理价格更新
async def calculate_opportunity()       # 计算套利机会
async def execute_trade()               # 执行交易
```

## 机器学习接口

### 1. 模型训练器 (ModelTrainer)

#### 配置参数

```python
{
    "enabled": bool,                    # 是否启用
    "min_data_points": int,            # 最小数据点数
    "update_interval": int,            # 更新间隔(秒)
    "models": {
        "lstm": {
            "enabled": bool,           # 是否启用LSTM
            "batch_size": int,         # 批次大小
            "epochs": int,             # 训练轮数
            "sequence_length": int     # 序列长度
        },
        "xgboost": {
            "enabled": bool           # 是否启用XGBoost
        }
    }
}
```

#### 主要方法

```python
def train_model()                      # 训练模型
def evaluate_model()                   # 评估模型
def predict()                          # 预测
def save_model()                       # 保存模型
def load_model()                       # 加载模型
```

## 风险管理接口

### 1. 风险管理器 (RiskManager)

#### 配置参数

```python
{
    "max_position_size": float,        # 最大持仓量
    "max_daily_loss": float,           # 最大日亏损
    "max_drawdown": float,             # 最大回撤
    "risk_limits": {
        "max_total_position": float,   # 最大总持仓
        "max_single_strategy_loss": float,  # 单策略最大亏损
        "max_total_loss": float        # 总体最大亏损
    }
}
```

#### 主要方法

```python
def check_risk()                       # 检查风险
def update_position()                  # 更新持仓
def calculate_drawdown()               # 计算回撤
def check_daily_loss()                # 检查日亏损
```

## 数据监控接口

### 1. 市场监控器 (MarketMonitor)

#### 配置参数

```python
{
    "enabled": bool,                   # 是否启用
    "price_update_interval": int,      # 价格更新间隔
    "depth_update_interval": int,      # 深度更新间隔
    "trade_update_interval": int       # 成交更新间隔
}
```

#### 主要方法

```python
async def start_monitoring()           # 启动监控
async def stop_monitoring()            # 停止监控
async def process_market_data()        # 处理市场数据
async def update_orderbook()           # 更新订单簿
```

## 性能监控接口

### 1. 性能监控器 (PerformanceMonitor)

#### 配置参数

```python
{
    "performance_threshold": {
        "min_sharpe_ratio": float,     # 最小夏普比率
        "min_win_rate": float          # 最小胜率
    }
}
```

#### 主要方法

```python
def calculate_sharpe_ratio()           # 计算夏普比率
def calculate_win_rate()               # 计算胜率
def calculate_returns()                # 计算收益率
def generate_report()                  # 生成报告
```

## 1. 核心模块 API

### 1.1 ModelTrainer（模型训练器）

模型训练器类负责机器学习模型的训练、评估和预测。支持 LSTM 和 XGBoost 两种模型类型，可用于价格预测和套利机会识别。

主要功能：

- 模型训练和验证
- 模型保存和加载
- 预测和评估
- 特征重要性分析

使用场景：

- 价格趋势预测
- 套利机会识别
- 风险评估
- 交易策略优化

````python
class ModelTrainer:
    def train_model(self, X: np.ndarray, y: np.ndarray, model_type: str = 'lstm',
                   **kwargs) -> Tuple[str, Dict, Dict]:
        """
        训练模型并返回模型ID和训练指标。

        参数:
            X (np.ndarray): 输入特征数据，shape=(样本数, 序列长度, 特征数)
            y (np.ndarray): 目标变量，shape=(样本数,)
            model_type (str): 模型类型，可选 'lstm' 或 'xgboost'
            **kwargs: 其他模型参数，如:
                - learning_rate: 学习率
                - batch_size: 批次大小
                - epochs: 训练轮数
                - early_stopping: 早停轮数

        返回:
            Tuple[str, Dict, Dict]:
            - 模型ID
            - 评估指标（准确率、损失等）
            - 训练历史记录
        """
        pass

    def predict(self, model_id: str, X: np.ndarray) -> np.ndarray:
        """
        使用指定模型进行预测。

        参数:
            model_id (str): 模型ID，由train_model返回
            X (np.ndarray): 输入特征数据，需与训练数据格式一致

        返回:
            np.ndarray: 预测结果，对于回归任务返回预测值，分类任务返回概率
        """
        pass

### 1.2 PriceMonitor（价格监控器）

价格监控器负责实时获取和处理市场数据，支持多交易所、多交易对的价格监控。

主要功能：

- 实时价格数据获取
- 价格异常检测
- 数据清洗和预处理
- 价格更新回调处理

使用场景：

- 实时价格监控
- 套利机会发现
- 市场异常检测
- 交易信号生成

```python
class PriceMonitor:
    def start_monitoring(self, symbols: List[str], callback: Callable):
        """
        开始监控指定交易对的价格。

        参数:
            symbols (List[str]): 交易对列表，如 ["BTC/USDT", "ETH/USDT"]
            callback (Callable): 价格更新回调函数，当收到新价格时调用
                回调函数格式: callback(price_data: Dict)
                price_data包含：
                - symbol: 交易对
                - exchange: 交易所
                - price: 最新价格
                - timestamp: 时间戳
        """
        pass

    def get_latest_price(self, symbol: str) -> Dict:
        """
        获取最新价格数据。

        参数:
            symbol (str): 交易对名称，如 "BTC/USDT"

        返回:
            Dict: 价格信息字典，包含：
            - price: 最新价格
            - bid: 买一价
            - ask: 卖一价
            - volume: 24小时成交量
            - timestamp: 时间戳
        """
        pass

### 1.3 ExchangeFactory（交易所工厂）

交易所工厂类负责创建和管理各个交易所的连接实例，支持统一的接口访问不同交易所。

主要功能：

- 交易所实例创建
- 连接管理
- 接口统一化
- 错误处理

使用场景：

- 多交易所管理
- 统一接口调用
- 连接状态监控
- 错误恢复处理

```python
class ExchangeFactory:
    def create_exchange(self, exchange_name: str, config: Dict) -> Exchange:
        """
        创建交易所实例。

        参数:
            exchange_name (str): 交易所名称，如 "binance", "okx"
            config (Dict): 配置信息，包含：
                - api_key: API密钥
                - secret: 密钥
                - password: 密码（如果需要）
                - test_mode: 是否使用测试网络
                - timeout: 超时设置

        返回:
            Exchange: 交易所实例，提供统一的交易接口
        """
        pass
````

## 2. 数据处理 API

### 2.1 FeatureEngineering（特征工程）

特征工程类负责数据预处理和特征提取，为机器学习模型提供高质量的训练数据。

主要功能：

- 原始数据处理
- 特征提取和选择
- 数据标准化
- 时序特征生成

使用场景：

- 数据预处理
- 特征创建
- 数据清洗
- 特征选择

```python
class FeatureEngineering:
    def process_raw_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        处理原始数据并生成特征。

        参数:
            data (pd.DataFrame): 原始数据，包含：
                - timestamp: 时间戳
                - price: 价格
                - volume: 成交量
                - trades: 成交笔数等

        返回:
            pd.DataFrame: 处理后的特征数据，包含：
                - 技术指标
                - 统计特征
                - 时间特征
                - 市场特征
        """
        pass

    def extract_features(self, data: pd.DataFrame, feature_config: Dict) -> pd.DataFrame:
        """
        根据配置提取特征。

        参数:
            data (pd.DataFrame): 输入数据
            feature_config (Dict): 特征配置，如：
                - technical_indicators: 技术指标列表
                - time_features: 时间特征列表
                - market_features: 市场特征列表

        返回:
            pd.DataFrame: 提取的特征数据
        """
        pass
```

## 3. 策略模块 API

### 3.1 TradingStrategy（交易策略）

交易策略基类，定义了策略的基本接口和通用功能。所有具体的策略实现都应继承此类。

主要功能：

- 交易信号生成
- 仓位管理
- 风险控制
- 策略回测

使用场景：

- 策略开发
- 信号生成
- 交易执行
- 性能评估

```python
class TradingStrategy:
    def generate_signals(self, market_data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号。

        参数:
            market_data (pd.DataFrame): 市场数据，包含：
                - price: 价格数据
                - volume: 成交量
                - indicators: 技术指标
                - features: 其他特征

        返回:
            pd.Series: 交易信号，其中：
                1: 买入信号
                0: 持仓不变
                -1: 卖出信号
        """
        pass

    def calculate_position_size(self, signal: float,
                              account_info: Dict) -> float:
        """
        计算仓位大小。

        参数:
            signal (float): 交易信号强度，范围[-1, 1]
            account_info (Dict): 账户信息，包含：
                - balance: 账户余额
                - positions: 当前持仓
                - risk_limit: 风险限额

        返回:
            float: 建议的仓位大小（按基础货币计算）
        """
        pass
```

## 4. 风险管理 API

### 4.1 RiskManager（风险管理器）

风险管理器负责交易风险控制和仓位管理，确保交易在可控范围内进行。

主要功能：

- 风险限额控制
- 仓位规模管理
- 止损止盈管理
- 风险指标监控

使用场景：

- 交易风险控制
- 仓位管理
- 资金管理
- 风险预警

```python
class RiskManager:
    def check_risk_limits(self, order: Dict) -> bool:
        """
        检查订单是否符合风险限制。

        参数:
            order (Dict): 订单信息，包含：
                - symbol: 交易对
                - type: 订单类型
                - side: 买卖方向
                - amount: 数量
                - price: 价格
                - leverage: 杠杆倍数

        返回:
            bool: 是否通过风险检查
        """
        pass

    def calculate_stop_loss(self, position: Dict) -> float:
        """
        计算止损价格。

        参数:
            position (Dict): 持仓信息，包含：
                - entry_price: 开仓价格
                - current_price: 当前价格
                - size: 持仓大小
                - unrealized_pnl: 未实现盈亏
                - risk_ratio: 风险系数

        返回:
            float: 建议的止损价格
        """
        pass
```

## 5. 系统模块 API

### 5.1 SystemAdapter（系统适配器）

系统适配器负责处理不同操作系统平台的兼容性问题，提供统一的系统接口。

主要功能：

- 系统环境检测
- 平台兼容性处理
- 系统资源管理
- 性能监控

使用场景：

- 跨平台部署
- 系统资源监控
- 性能优化
- 错误处理

```python
class SystemAdapter:
    def get_system_info(self) -> Dict:
        """
        获取系统信息。

        返回:
            Dict: 系统信息，包含：
                - os_type: 操作系统类型
                - python_version: Python版本
                - cpu_count: CPU核心数
                - memory_info: 内存信息
                - disk_info: 磁盘信息
        """
        pass

    def monitor_resources(self) -> Dict:
        """
        监控系统资源使用情况。

        返回:
            Dict: 资源使用情况，包含：
                - cpu_usage: CPU使用率
                - memory_usage: 内存使用率
                - disk_usage: 磁盘使用率
                - network_traffic: 网络流量
        """
        pass
```

### 5.2 CacheManager（缓存管理器）

缓存管理器负责系统数据的缓存处理，支持多种缓存策略和存储方式。

主要功能：

- 数据缓存管理
- 缓存策略实现
- 缓存同步
- 过期处理

使用场景：

- 行情数据缓存
- 订单数据缓存
- 配置信息缓存
- 临时数据存储

```python
class CacheManager:
    def set_cache(self, key: str, value: Any,
                 expire: Optional[int] = None) -> bool:
        """
        设置缓存数据。

        参数:
            key (str): 缓存键名
            value (Any): 缓存数据
            expire (Optional[int]): 过期时间（秒）

        返回:
            bool: 是否设置成功
        """
        pass

    def get_cache(self, key: str) -> Optional[Any]:
        """
        获取缓存数据。

        参数:
            key (str): 缓存键名

        返回:
            Optional[Any]: 缓存数据，不存在返回None
        """
        pass

    def clear_expired(self) -> int:
        """
        清理过期缓存。

        返回:
            int: 清理的缓存数量
        """
        pass
```

### 5.3 Logger（日志记录器）

日志记录器负责系统运行日志、交易记录、错误信息的记录和管理。

主要功能：

- 日志记录
- 日志分类管理
- 日志文件轮转
- 日志查询

使用场景：

- 系统运行日志
- 交易记录
- 错误追踪
- 性能分析

```python
class Logger:
    def log_trade(self, trade_info: Dict):
        """
        记录交易信息。

        参数:
            trade_info (Dict): 交易信息，包含：
                - trade_id: 交易ID
                - symbol: 交易对
                - type: 交易类型
                - amount: 交易数量
                - price: 交易价格
                - timestamp: 交易时间
        """
        pass

    def log_error(self, error_info: Dict):
        """
        记录错误信息。

        参数:
            error_info (Dict): 错误信息，包含：
                - error_type: 错误类型
                - message: 错误消息
                - stack_trace: 堆栈跟踪
                - timestamp: 发生时间
        """
        pass

    def query_logs(self,
                  start_time: datetime,
                  end_time: datetime,
                  log_type: str) -> List[Dict]:
        """
        查询日志记录。

        参数:
            start_time (datetime): 开始时间
            end_time (datetime): 结束时间
            log_type (str): 日志类型，如 'trade', 'error', 'system'

        返回:
            List[Dict]: 日志记录列表
        """
        pass
```

### 5.4 DataAnalyzer（数据分析器）

数据分析器负责交易数据的分析和性能评估。

主要功能：

- 交易分析
- 性能评估
- 风险分析
- 报告生成

使用场景：

- 策略评估
- 绩效分析
- 风险评估
- 报告生成

```python
class DataAnalyzer:
    def analyze_performance(self,
                          trade_history: pd.DataFrame) -> Dict:
        """
        分析交易性能。

        参数:
            trade_history (pd.DataFrame): 交易历史数据，包含：
                - timestamp: 交易时间
                - type: 交易类型
                - price: 交易价格
                - amount: 交易数量
                - pnl: 盈亏

        返回:
            Dict: 性能指标，包含：
                - total_return: 总收益率
                - sharpe_ratio: 夏普比率
                - max_drawdown: 最大回撤
                - win_rate: 胜率
        """
        pass

    def generate_report(self,
                       analysis_results: Dict,
                       report_type: str = 'full') -> str:
        """
        生成分析报告。

        参数:
            analysis_results (Dict): 分析结果
            report_type (str): 报告类型，可选 'full', 'summary', 'risk'

        返回:
            str: 报告内容（HTML或Markdown格式）
        """
        pass
```

## 6. HTTP API 接口

### 6.1 系统状态

GET `/status`

- 描述：获取系统当前运行状态
- 返回：
  ```json
  {
    "monitor_status": "运行中",
    "trading_status": "运行中",
    "api_status": "运行中",
    "active_exchanges": ["binance", "okx", "bybit"],
    "monitored_symbols": ["BTC/USDT", "ETH/USDT"],
    "last_update": "2024-02-09 12:00:00"
  }
  ```

### 6.2 交易相关

GET `/trades`

- 描述：获取历史交易记录
- 参数：
  - start_time (可选): 开始时间
  - end_time (可选): 结束时间
  - limit (可选): 返回记录数量，默认 100
- 返回：
  ```json
  [
    {
      "trade_id": "T123456",
      "type": "spread_arbitrage",
      "symbol": "BTC/USDT",
      "buy_exchange": "binance",
      "sell_exchange": "okx",
      "buy_price": 40000.0,
      "sell_price": 40100.0,
      "amount": 0.1,
      "profit_usdt": 10.0,
      "timestamp": "2024-02-09 12:00:00",
      "status": "completed"
    }
  ]
  ```

### 6.3 市场数据

GET `/prices/{symbol}`

- 描述：获取交易对的历史价格数据
- 参数：
  - symbol: 交易对名称 (如 "BTC/USDT")
  - exchange (可选): 交易所名称
  - interval (可选): K 线间隔，默认"1m"
  - limit (可选): 返回记录数量，默认 1000
- 返回：
  ```json
  {
    "symbol": "BTC/USDT",
    "interval": "1m",
    "prices": [
      {
        "timestamp": "2024-02-09 12:00:00",
        "exchange": "binance",
        "open": 40000.0,
        "high": 40100.0,
        "low": 39900.0,
        "close": 40050.0,
        "volume": 100.0
      }
    ]
  }
  ```

### 6.4 策略管理

GET `/api/strategy/status`

- 描述：获取所有策略的运行状态
- 返回：
  ```json
  {
    "网格交易": {
      "status": "运行中",
      "position": 0.1,
      "pnl": 100.0,
      "orders": 50,
      "update_time": "2024-02-09 12:00:00"
    }
  }
  ```

## 7. 使用示例

### 7.1 模型训练和预测

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

### 7.2 实时价格监控

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

### 7.3 特征工程

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
