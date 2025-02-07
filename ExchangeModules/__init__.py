"""
交易所模块包 (Exchange Modules Package)
此包提供了一套完整的加密货币交易所接口管理工具，包含以下主要功能：

1. 交易所实例管理 (ExchangeInstance):
   - REST和WebSocket连接的统一管理
   - 实例的创建、获取和关闭

2. 市场数据处理 (MarketProcessor):
   - 处理不同类型的市场数据
   - 支持多种市场类型的配置管理

3. 共同交易对查找 (CommonSymbolsFinder):
   - 在多个交易所间查找共同的交易对
   - 支持不同市场类型和计价货币

4. 监控管理 (MonitorManager):
   - 实时监控多个交易所的价格数据
   - 自动错误处理和重连机制

Version: 1.0.0
"""

from .common_symbols_finder import CommonSymbolsFinder
from .exchange_instance import ExchangeInstance
from .market_processor import MarketProcessor
from .monitor_manager import MonitorManager

__version__ = '1.0.0'
__author__ = 'Your Name'

__all__ = [
    'ExchangeInstance',
    'MarketProcessor',
    'CommonSymbolsFinder',
    'MonitorManager'
]
