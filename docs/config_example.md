# 配置示例文档

## 1. 环境配置 (.env)

```ini
# 基础配置
ENV=development                 # 运行环境：development/testing/production
DEBUG=true                     # 调试模式
LOG_LEVEL=INFO                 # 日志级别

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=crypto_arbitrage
DB_USER=postgres
DB_PASSWORD=

# GUI配置
GUI_ENABLED=true              # 是否启用GUI界面
GUI_THEME=dark               # GUI主题：light/dark
GUI_REFRESH_RATE=1000       # GUI刷新率（毫秒）

# 交易所API配置
## Binance
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_TESTNET=true

## Bybit
BYBIT_API_KEY=your_api_key
BYBIT_API_SECRET=your_api_secret
BYBIT_TESTNET=true

## OKX
OKX_API_KEY=your_api_key
OKX_API_SECRET=your_api_secret
OKX_PASSPHRASE=your_passphrase
OKX_TESTNET=true

# 交易所API配置
BINANCE_API_KEY=your_api_key
BINANCE_SECRET=your_secret
BYBIT_API_KEY=your_api_key
BYBIT_SECRET=your_secret
OKX_API_KEY=your_api_key
OKX_SECRET=your_secret
OKX_PASSWORD=your_password
HUOBI_API_KEY=your_api_key
HUOBI_SECRET=your_secret
GATEIO_API_KEY=your_api_key
GATEIO_SECRET=your_secret
```

## 2. 功能开关配置

```python
FEATURE_FLAGS = {
    # 市场监控配置
    "monitoring": {
        "enabled": True,
        "price_update_interval": 1,
        "depth_update_interval": 5,
        "trade_update_interval": 1
    },

    # 机器学习配置
    "machine_learning": {
        "enabled": True,
        "min_data_points": 1000,
        "update_interval": 3600,
        "models": {
            "lstm": {
                "enabled": True,
                "batch_size": 32,
                "epochs": 100,
                "sequence_length": 60
            },
            "xgboost": {
                "enabled": False
            }
        }
    },

    # 交易配置
    "trading": {
        "enabled": True,
        "max_open_orders": 5,
        "min_profit_threshold": 0.002,
        "risk_management": {
            "max_position_size": 1000,
            "max_daily_loss": 100,
            "max_drawdown": 0.1
        }
    }
}
```

## 3. 策略配置示例

### 3.1 三角套利配置

```python
"triangular_arbitrage": {
    "enabled": True,
    "min_profit_threshold": 0.001,
    "max_trade_amount": 1000,
    "pairs": [
        "BTC/USDT",
        "ETH/USDT",
        "ETH/BTC"
    ],
    "update_interval": 1,
    "execution_timeout": 5,
    "risk_control": {
        "max_slippage": 0.001,
        "min_volume_threshold": 1000
    }
}
```

### 3.2 统计套利配置

```python
"statistical_arbitrage": {
    "enabled": True,
    "window_size": 3600,
    "z_score_threshold": 2.0,
    "pairs": [
        ["BTC/USDT_binance", "BTC/USDT_okx"],
        ["ETH/USDT_binance", "ETH/USDT_okx"]
    ],
    "position_holding_time": 3600,
    "max_position_value": 10000,
    "correlation_threshold": 0.8
}
```

### 3.3 期现套利配置

```python
"spot_future_arbitrage": {
    "enabled": True,
    "min_spread_threshold": 0.002,
    "max_leverage": 5,
    "funding_rate_threshold": 0.001,
    "pairs": ["BTC/USDT", "ETH/USDT"],
    "position_limit": {
        "BTC": 1.0,
        "ETH": 10.0
    },
    "hedge_ratio": 1.0,
    "margin_ratio": 0.5
}
```

### 3.4 价差套利配置

```python
"spread_arbitrage": {
    "enabled": True,
    "min_profit_threshold": 0.002,
    "trade_amount": 1000,
    "max_open_orders": 5,
    "price_decimal": 8,
    "amount_decimal": 8,
    "update_interval": 1,
    "execution_timeout": 5
}
```

## 4. 混合策略配置

```python
"mixed_strategy": {
    "enabled": True,
    "strategy_weights": {
        "triangular_arbitrage": 0.3,
        "statistical_arbitrage": 0.2,
        "spot_future_arbitrage": 0.3,
        "spread_arbitrage": 0.2
    },
    "capital_allocation": {
        "triangular_arbitrage": 0.3,
        "statistical_arbitrage": 0.2,
        "spot_future_arbitrage": 0.3,
        "spread_arbitrage": 0.2
    },
    "risk_limits": {
        "max_total_position": 50000,
        "max_single_strategy_loss": 1000,
        "max_total_loss": 3000
    },
    "rebalance_interval": 3600,
    "performance_threshold": {
        "min_sharpe_ratio": 1.5,
        "min_win_rate": 0.6
    }
}
```

## 5. 市场配置

```python
# 交易所列表
EXCHANGES = ["binance", "bybit", "okx", "huobi", "gateio"]

# 市场类型
MARKET_TYPES = {
    "spot": True,      # 现货市场
    "futures": False,  # 期货市场
    "swap": True      # 永续合约市场
}

# 报价货币
QUOTE_CURRENCIES = ["USDT"]

# 默认手续费率
DEFAULT_FEES = {
    "maker": 0.001,  # 0.1%
    "taker": 0.002   # 0.2%
}
```

## 6. 指标配置

```python
INDICATOR_CONFIG = {
    # 序列长度
    "sequence_length": 60,
    "prediction_length": 10,

    # 特征列表
    "features": [
        "close",    # 收盘价
        "volume",   # 成交量
        "rsi",      # RSI指标
        "macd",     # MACD指标
        "bid",      # 买一价
        "ask",      # 卖一价
        "spread"    # 买卖价差
    ],

    # 模型参数
    "model_params": {
        "hidden_size": 50,
        "num_layers": 2,
        "dropout": 0.2,
        "learning_rate": 0.001
    },

    # 训练参数
    "train_params": {
        "batch_size": 32,
        "epochs": 100,
        "validation_split": 0.2
    }
}
```

## 7. 缓存配置

```python
# Redis配置
REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "password": "",
    "db": 0,
    "decode_responses": True
}

# 市场结构配置
MARKET_STRUCTURE_CONFIG = {
    "cache_prefix": "market",
    "cache_types": ["orderbook", "ticker", "trades"],
    "default_cache_ttl": 3600,
    "cache_ttl": {
        "orderbook": 60,
        "ticker": 30,
        "trades": 300
    }
}
```

## 8. 日志配置

```python
# 日志配置
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(message)s"
        }
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler"
        },
        "file": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": "logs/arbitrage.log"
        }
    },
    "loggers": {
        "": {
            "handlers": ["default", "file"],
            "level": "INFO",
            "propagate": True
        }
    }
}
```

## 监控配置 (monitoring.yaml)

```yaml
prometheus:
  enabled: true
  port: 9090
  path: /metrics

alerts:
  slack:
    enabled: true
    webhook_url: your_webhook_url
  email:
    enabled: true
    smtp_server: smtp.gmail.com
    smtp_port: 587
    sender: your_email@gmail.com
    recipients:
      - admin@example.com

metrics:
  system:
    cpu_usage: true
    memory_usage: true
    disk_usage: true
  trading:
    order_count: true
    trade_volume: true
    profit_loss: true
```
