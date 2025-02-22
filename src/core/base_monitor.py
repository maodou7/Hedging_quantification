"""基础监控类

提供统一的监控状态查询基础功能，减少重复代码
"""

from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal

class BaseMonitor:
    """基础监控类，提供通用的监控状态查询功能"""
    
    def __init__(self):
        self.last_update = datetime.now()
    
    def get_system_metrics(self) -> Dict:
        """获取系统指标
        
        Returns:
            Dict: 系统指标数据
        """
        return {
            'cpu_usage': self._get_cpu_usage(),
            'memory_usage': self._get_memory_usage(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_exchange_metrics(self, exchange_name: str) -> Dict:
        """获取交易所连接指标
        
        Args:
            exchange_name: 交易所名称
            
        Returns:
            Dict: 交易所连接指标数据
        """
        return {
            'connection_status': self._check_connection_status(exchange_name),
            'api_latency': self._get_api_latency(exchange_name),
            'websocket_status': self._check_websocket_status(exchange_name),
            'error_count': self._get_error_count(exchange_name),
            'last_update': datetime.now().isoformat()
        }
    
    def get_trading_metrics(self, strategy_name: Optional[str] = None) -> Dict:
        """获取交易指标
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            Dict: 交易指标数据
        """
        return {
            'active_orders': self._get_active_orders(strategy_name),
            'total_positions': self._get_total_positions(strategy_name),
            'realized_pnl': self._get_realized_pnl(strategy_name),
            'unrealized_pnl': self._get_unrealized_pnl(strategy_name),
            'trading_volume': self._get_trading_volume(strategy_name),
            'last_trade_time': self._get_last_trade_time(strategy_name)
        }
    
    def get_market_metrics(self, symbol: str, exchange: str) -> Dict:
        """获取市场指标
        
        Args:
            symbol: 交易对名称
            exchange: 交易所名称
            
        Returns:
            Dict: 市场指标数据
        """
        return {
            'price': self._get_current_price(symbol, exchange),
            'volume': self._get_24h_volume(symbol, exchange),
            'price_change': self._get_24h_price_change(symbol, exchange),
            'high': self._get_24h_high(symbol, exchange),
            'low': self._get_24h_low(symbol, exchange),
            'last_update': datetime.now().isoformat()
        }
    
    # 以下为需要子类实现的protected方法
    def _get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        raise NotImplementedError
    
    def _get_memory_usage(self) -> float:
        """获取内存使用率"""
        raise NotImplementedError
    
    def _check_connection_status(self, exchange: str) -> str:
        """检查交易所连接状态"""
        raise NotImplementedError
    
    def _get_api_latency(self, exchange: str) -> float:
        """获取API延迟"""
        raise NotImplementedError
    
    def _check_websocket_status(self, exchange: str) -> str:
        """检查WebSocket连接状态"""
        raise NotImplementedError
    
    def _get_error_count(self, exchange: str) -> int:
        """获取错误计数"""
        raise NotImplementedError
    
    def _get_active_orders(self, strategy: Optional[str] = None) -> int:
        """获取活跃订单数量"""
        raise NotImplementedError
    
    def _get_total_positions(self, strategy: Optional[str] = None) -> int:
        """获取总持仓数量"""
        raise NotImplementedError
    
    def _get_realized_pnl(self, strategy: Optional[str] = None) -> Decimal:
        """获取已实现盈亏"""
        raise NotImplementedError
    
    def _get_unrealized_pnl(self, strategy: Optional[str] = None) -> Decimal:
        """获取未实现盈亏"""
        raise NotImplementedError
    
    def _get_trading_volume(self, strategy: Optional[str] = None) -> Decimal:
        """获取交易量"""
        raise NotImplementedError
    
    def _get_last_trade_time(self, strategy: Optional[str] = None) -> str:
        """获取最后交易时间"""
        raise NotImplementedError
    
    def _get_current_price(self, symbol: str, exchange: str) -> Decimal:
        """获取当前价格"""
        raise NotImplementedError
    
    def _get_24h_volume(self, symbol: str, exchange: str) -> Decimal:
        """获取24小时成交量"""
        raise NotImplementedError
    
    def _get_24h_price_change(self, symbol: str, exchange: str) -> Decimal:
        """获取24小时价格变化"""
        raise NotImplementedError
    
    def _get_24h_high(self, symbol: str, exchange: str) -> Decimal:
        """获取24小时最高价"""
        raise NotImplementedError
    
    def _get_24h_low(self, symbol: str, exchange: str) -> Decimal:
        """获取24小时最低价"""
        raise NotImplementedError