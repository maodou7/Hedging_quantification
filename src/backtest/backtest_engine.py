"""
回测引擎

负责:
1. 策略回测
2. 模拟交易
3. 性能评估
"""

from typing import Dict, List, Any, Type, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from src.strategies.base_strategy import BaseStrategy
from src.utils.logger import ArbitrageLogger

class BacktestEngine:
    def __init__(self):
        self.logger = ArbitrageLogger()
        self.data: Dict[str, pd.DataFrame] = {}
        self.strategy: Optional[BaseStrategy] = None
        self.config: Dict[str, Any] = {}
        
        # 回测结果
        self.trades: List[Dict[str, Any]] = []
        self.positions: Dict[str, float] = {}
        self.balance = 0.0
        self.equity = 0.0
        
        # 性能指标
        self.metrics: Dict[str, Any] = {}
        
    def load_data(self, data: Dict[str, pd.DataFrame]):
        """加载回测数据"""
        self.data = data
        self.logger.info(f"已加载 {len(data)} 个交易对的数据")
        
    def set_strategy(self, strategy_class: Type[BaseStrategy], config: Dict[str, Any]):
        """设置回测策略"""
        self.strategy = strategy_class(None, config)  # 传入None作为exchange_instance
        self.config = config
        self.logger.info(f"已设置策略: {strategy_class.__name__}")
        
    async def run(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """运行回测"""
        try:
            if not self.strategy or not self.data:
                raise ValueError("策略或数据未设置")
                
            self.logger.info(f"开始回测: {start_time} - {end_time}")
            
            # 初始化账户
            self.balance = self.config.get('initial_balance', 10000)
            self.equity = self.balance
            
            # 遍历每个时间点
            timestamps = self._get_common_timestamps(start_time, end_time)
            for timestamp in timestamps:
                # 更新市场数据
                market_data = self._get_market_data(timestamp)
                
                # 更新策略
                await self._update_strategy(timestamp, market_data)
                
                # 更新账户状态
                self._update_account(timestamp)
                
            # 计算性能指标
            self._calculate_metrics(start_time, end_time)
            
            return {
                'backtest_start': start_time,
                'backtest_end': end_time,
                'total_days': (end_time - start_time).days,
                'initial_balance': self.config.get('initial_balance', 10000),
                'final_balance': self.balance,
                'total_trades': len(self.trades),
                'total_profit': self.equity - self.config.get('initial_balance', 10000),
                'metrics': self.metrics
            }
            
        except Exception as e:
            self.logger.error(f"回测过程中发生错误: {str(e)}")
            return {}
            
    def _get_common_timestamps(self, start_time: datetime, end_time: datetime) -> List[datetime]:
        """获取所有数据共同的时间戳"""
        try:
            # 获取每个数据集的时间戳
            all_timestamps = []
            for df in self.data.values():
                timestamps = df.index[(df.index >= start_time) & (df.index <= end_time)]
                all_timestamps.append(set(timestamps))
                
            # 取交集
            common_timestamps = set.intersection(*all_timestamps)
            
            # 排序
            return sorted(list(common_timestamps))
            
        except Exception as e:
            self.logger.error(f"获取时间戳时发生错误: {str(e)}")
            return []
            
    def _get_market_data(self, timestamp: datetime) -> Dict[str, Any]:
        """获取指定时间点的市场数据"""
        try:
            market_data = {}
            for symbol, df in self.data.items():
                if timestamp in df.index:
                    market_data[symbol] = {
                        'timestamp': timestamp,
                        'open': df.loc[timestamp, 'open'],
                        'high': df.loc[timestamp, 'high'],
                        'low': df.loc[timestamp, 'low'],
                        'close': df.loc[timestamp, 'close'],
                        'volume': df.loc[timestamp, 'volume'],
                        'bid': df.loc[timestamp, 'bid'] if 'bid' in df.columns else df.loc[timestamp, 'close'] * 0.9999,
                        'ask': df.loc[timestamp, 'ask'] if 'ask' in df.columns else df.loc[timestamp, 'close'] * 1.0001
                    }
            return market_data
            
        except Exception as e:
            self.logger.error(f"获取市场数据时发生错误: {str(e)}")
            return {}
            
    async def _update_strategy(self, timestamp: datetime, market_data: Dict[str, Any]):
        """更新策略状态"""
        try:
            # 模拟市场数据更新
            for symbol, data in market_data.items():
                await self.strategy.process_price_update('backtest', symbol, data)
                
            # 检查是否有新的交易信号
            if hasattr(self.strategy, 'strategy_monitor'):
                trades = self.strategy.strategy_monitor.trades
                if trades and trades[-1]['timestamp'] == timestamp:
                    self._process_trade(trades[-1])
                    
        except Exception as e:
            self.logger.error(f"更新策略时发生错误: {str(e)}")
            
    def _process_trade(self, trade: Dict[str, Any]):
        """处理交易记录"""
        try:
            # 计算交易成本
            commission = self.config.get('commission_rate', 0.001)
            cost = trade['amount'] * trade['price'] * (1 + commission)
            
            # 更新持仓
            symbol = trade['symbol']
            if trade['side'] == 'buy':
                self.positions[symbol] = self.positions.get(symbol, 0) + trade['amount']
                self.balance -= cost
            else:
                self.positions[symbol] = self.positions.get(symbol, 0) - trade['amount']
                self.balance += cost
                
            # 记录交易
            self.trades.append({
                'timestamp': trade['timestamp'],
                'symbol': symbol,
                'side': trade['side'],
                'amount': trade['amount'],
                'price': trade['price'],
                'cost': cost,
                'balance': self.balance
            })
            
        except Exception as e:
            self.logger.error(f"处理交易时发生错误: {str(e)}")
            
    def _update_account(self, timestamp: datetime):
        """更新账户状态"""
        try:
            # 计算当前持仓市值
            position_value = 0
            for symbol, amount in self.positions.items():
                if symbol in self.data:
                    price = self.data[symbol].loc[timestamp, 'close']
                    position_value += amount * price
                    
            # 更新账户权益
            self.equity = self.balance + position_value
            
        except Exception as e:
            self.logger.error(f"更新账户状态时发生错误: {str(e)}")
            
    def _calculate_metrics(self, start_time: datetime, end_time: datetime):
        """计算性能指标"""
        try:
            if not self.trades:
                return
                
            # 创建每日权益数据
            daily_equity = pd.Series(index=pd.date_range(start_time, end_time, freq='D'))
            for trade in self.trades:
                daily_equity[trade['timestamp'].date()] = trade['balance']
                
            # 填充空值
            daily_equity.fillna(method='ffill', inplace=True)
            daily_equity.fillna(self.config.get('initial_balance', 10000), inplace=True)
            
            # 计算每日收益率
            daily_returns = daily_equity.pct_change().dropna()
            
            # 计算性能指标
            total_days = (end_time - start_time).days
            total_return = (self.equity - self.config.get('initial_balance', 10000)) / self.config.get('initial_balance', 10000)
            
            self.metrics = {
                'total_return': total_return,
                'annual_return': total_return * (365 / total_days),
                'sharpe_ratio': self._calculate_sharpe_ratio(daily_returns),
                'max_drawdown': self._calculate_max_drawdown(daily_equity),
                'win_rate': self._calculate_win_rate(),
                'profit_factor': self._calculate_profit_factor(),
                'daily_returns': daily_returns.tolist(),
                'equity_curve': daily_equity.tolist()
            }
            
        except Exception as e:
            self.logger.error(f"计算性能指标时发生错误: {str(e)}")
            
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """计算夏普比率"""
        try:
            risk_free_rate = self.config.get('risk_free_rate', 0.02)
            daily_rf = (1 + risk_free_rate) ** (1/365) - 1
            excess_returns = returns - daily_rf
            if len(excess_returns) > 0:
                return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
            return 0
        except Exception as e:
            self.logger.error(f"计算夏普比率时发生错误: {str(e)}")
            return 0
            
    def _calculate_max_drawdown(self, equity: pd.Series) -> float:
        """计算最大回撤"""
        try:
            rolling_max = equity.expanding().max()
            drawdowns = (equity - rolling_max) / rolling_max
            return abs(drawdowns.min())
        except Exception as e:
            self.logger.error(f"计算最大回撤时发生错误: {str(e)}")
            return 0
            
    def _calculate_win_rate(self) -> float:
        """计算胜率"""
        try:
            if not self.trades:
                return 0
            profitable_trades = sum(1 for trade in self.trades if trade['cost'] > 0)
            return profitable_trades / len(self.trades)
        except Exception as e:
            self.logger.error(f"计算胜率时发生错误: {str(e)}")
            return 0
            
    def _calculate_profit_factor(self) -> float:
        """计算盈亏比"""
        try:
            if not self.trades:
                return 0
            gross_profit = sum(trade['cost'] for trade in self.trades if trade['cost'] > 0)
            gross_loss = abs(sum(trade['cost'] for trade in self.trades if trade['cost'] < 0))
            return gross_profit / gross_loss if gross_loss != 0 else 0
        except Exception as e:
            self.logger.error(f"计算盈亏比时发生错误: {str(e)}")
            return 0 