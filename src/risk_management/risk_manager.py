"""
风险管理器模块
负责管理交易风险
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
from src.config.risk import RISK_CONFIG  # 修改导入路径
from src.utils.logger import ArbitrageLogger

logger = logging.getLogger(__name__)

class RiskManager:
    """风险管理器"""
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = ArbitrageLogger()
        self.config = config or {}
        
        # 从配置文件加载风险参数
        self.max_position_size = self.config.get('max_position_size', 10000.0)  # 最大持仓规模（USDT）
        self.max_daily_loss = self.config.get('max_daily_loss', 100.0)       # 每日最大亏损（USDT）
        self.max_trade_frequency = self.config.get('max_trade_frequency', 10)     # 每分钟最大交易次数
        self.min_profit_threshold = self.config.get('min_profit_threshold', 1.0)   # 最小利润阈值（USDT）
        
        # 初始化统计数据
        self.daily_pnl = 0.0
        self.trade_history = deque(maxlen=1000)
        self.last_reset_time = datetime.now()
        
        # 风险状态
        self.positions: Dict[str, float] = {}
        self.last_trade_time: Dict[str, datetime] = {}
        self.trade_count: Dict[str, int] = {}
        
        # 设置日志记录器
        self.logger = logging.getLogger('risk_manager')
        
    def reset_daily_stats(self):
        """重置每日统计数据"""
        current_time = datetime.now()
        if current_time.date() > self.last_reset_time.date():
            self.daily_pnl = 0
            self.last_reset_time = current_time
            self.logger.info("已重置每日统计数据")
            
    def check_trade_frequency(self) -> bool:
        """检查交易频率是否超限"""
        current_time = datetime.now()
        recent_trades = [trade for trade in self.trade_history 
                        if current_time - trade['timestamp'] < timedelta(minutes=1)]
        return len(recent_trades) < self.max_trade_frequency
        
    def check_position_size(self, amount: float, price: float) -> bool:
        """检查持仓规模是否超限"""
        position_value = amount * price
        return position_value <= self.max_position_size
        
    def update_pnl(self, profit: float):
        """更新收益统计"""
        self.daily_pnl += profit
        self.trade_history.append({
            'timestamp': datetime.now(),
            'profit': profit
        })
        self.logger.info(f"更新PnL: {profit:.2f} USDT, 当日累计: {self.daily_pnl:.2f} USDT")
        
    def can_trade(self, amount: float, price: float, expected_profit: float) -> Tuple[bool, Optional[str]]:
        """
        检查是否可以进行交易
        :return: (是否可以交易, 原因说明)
        """
        self.reset_daily_stats()
        
        # 检查交易频率
        if not self.check_trade_frequency():
            return False, "交易频率超过限制"
            
        # 检查持仓规模
        if not self.check_position_size(amount, price):
            return False, "交易规模超过限制"
            
        # 检查每日亏损限制
        if self.daily_pnl <= -self.max_daily_loss:
            return False, "达到每日最大亏损限制"
            
        # 检查最小利润要求
        if expected_profit < self.min_profit_threshold:
            return False, "预期利润低于最小阈值"
            
        return True, None
        
    def check_risk(self, exchange_id: str, symbol: str, price_data: Dict[str, Any], 
                  slippage: float) -> bool:
        """检查所有风险因素"""
        try:
            # 1. 检查价格有效性
            if not self._check_price_validity(price_data):
                return False
                
            # 2. 检查滑点是否可接受
            if not self._check_slippage(slippage):
                return False
                
            # 3. 检查交易频率
            if not self._check_trade_frequency(symbol):
                return False
                
            # 4. 检查持仓限制
            if not self._check_position_limit(symbol):
                return False
                
            # 5. 检查日内亏损限制
            if not self._check_daily_loss():
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"风险检查发生错误: {str(e)}")
            return False
            
    def _check_price_validity(self, price_data: Dict[str, Any]) -> bool:
        """检查价格有效性"""
        if not price_data.get('bid') or not price_data.get('ask'):
            self.logger.warning("价格数据无效")
            return False
            
        # 检查买卖价差是否异常
        spread_ratio = (price_data['ask'] - price_data['bid']) / price_data['bid']
        if spread_ratio > self.min_spread_ratio * 5:  # 价差超过正常的5倍
            self.logger.warning(f"价差异常: {spread_ratio}")
            return False
            
        return True
        
    def _check_slippage(self, slippage: float) -> bool:
        """检查滑点是否可接受"""
        if slippage > self.max_slippage:
            self.logger.warning(f"滑点过大: {slippage}")
            return False
        return True
        
    def _check_trade_frequency(self, symbol: str) -> bool:
        """检查交易频率"""
        now = datetime.now()
        if symbol in self.last_trade_time:
            time_diff = now - self.last_trade_time[symbol]
            if time_diff < timedelta(seconds=1):  # 限制每秒最多一次交易
                self.logger.warning(f"交易频率过高: {symbol}")
                return False
                
        # 更新最后交易时间
        self.last_trade_time[symbol] = now
        return True
        
    def _check_position_limit(self, symbol: str) -> bool:
        """检查持仓限制"""
        current_position = self.positions.get(symbol, 0)
        if abs(current_position) >= self.max_position_size:
            self.logger.warning(f"超出持仓限制: {symbol}")
            return False
        return True
        
    def _check_daily_loss(self) -> bool:
        """检查日内亏损限制"""
        if self.daily_pnl <= self.max_daily_loss:
            self.logger.warning(f"达到日内亏损限制: {self.daily_pnl}")
            return False
        return True
        
    def update_position(self, symbol: str, amount: float):
        """更新持仓"""
        self.positions[symbol] = self.positions.get(symbol, 0) + amount
        
    def get_risk_metrics(self) -> Dict[str, Any]:
        """获取风险指标"""
        return {
            'daily_pnl': self.daily_pnl,
            'positions': self.positions,
            'trade_count': self.trade_count
        } 