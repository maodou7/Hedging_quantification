"""
策略监控模块

负责：
1. 策略性能统计
2. 交易分析
3. 风险指标计算
4. 性能报告生成
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
from src.utils.logger import ArbitrageLogger

class StrategyMonitor:
    def __init__(self):
        self.logger = ArbitrageLogger()
        self.trades: List[Dict[str, Any]] = []
        self.daily_stats: Dict[str, Dict[str, float]] = {}
        self.start_time = datetime.now()
        
    def record_trade(self, trade: Dict[str, Any]):
        """记录交易"""
        trade['timestamp'] = datetime.now()
        self.trades.append(trade)
        self._update_daily_stats(trade)
        
    def _update_daily_stats(self, trade: Dict[str, Any]):
        """更新每日统计"""
        date = trade['timestamp'].date().isoformat()
        if date not in self.daily_stats:
            self.daily_stats[date] = {
                'total_profit': 0.0,
                'trade_count': 0,
                'win_count': 0,
                'loss_count': 0,
                'max_profit': float('-inf'),
                'max_loss': float('inf'),
                'total_volume': 0.0
            }
            
        stats = self.daily_stats[date]
        profit = trade.get('profit', 0)
        
        stats['total_profit'] += profit
        stats['trade_count'] += 1
        stats['total_volume'] += trade.get('volume', 0)
        
        if profit > 0:
            stats['win_count'] += 1
            stats['max_profit'] = max(stats['max_profit'], profit)
        elif profit < 0:
            stats['loss_count'] += 1
            stats['max_loss'] = min(stats['max_loss'], profit)
            
    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """计算性能指标"""
        if not self.trades:
            return {}
            
        df = pd.DataFrame(self.trades)
        
        # 基础统计
        total_trades = len(df)
        winning_trades = len(df[df['profit'] > 0])
        losing_trades = len(df[df['profit'] < 0])
        
        # 盈利统计
        total_profit = df['profit'].sum()
        avg_profit = df['profit'].mean()
        max_profit = df['profit'].max()
        max_loss = df['profit'].min()
        
        # 胜率和盈亏比
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        profit_factor = abs(df[df['profit'] > 0]['profit'].sum() / df[df['profit'] < 0]['profit'].sum()) if losing_trades > 0 else float('inf')
        
        # 计算夏普比率
        daily_returns = df.groupby(df['timestamp'].dt.date)['profit'].sum()
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        
        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown(df)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_profit': total_profit,
            'average_profit': avg_profit,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'runtime': (datetime.now() - self.start_time).total_seconds() / 3600  # 运行时间(小时)
        }
        
    def _calculate_sharpe_ratio(self, daily_returns: pd.Series) -> float:
        """计算夏普比率"""
        if len(daily_returns) < 2:
            return 0
            
        # 假设无风险利率为0
        returns_mean = daily_returns.mean()
        returns_std = daily_returns.std()
        
        if returns_std == 0:
            return 0
            
        # 年化夏普比率
        return np.sqrt(252) * returns_mean / returns_std
        
    def _calculate_max_drawdown(self, df: pd.DataFrame) -> float:
        """计算最大回撤"""
        if df.empty:
            return 0
            
        # 计算累计收益
        cumulative = df['profit'].cumsum()
        
        # 计算运行中最大值
        running_max = cumulative.expanding().max()
        
        # 计算回撤
        drawdown = (cumulative - running_max) / running_max
        
        return abs(drawdown.min()) if len(drawdown) > 0 else 0
        
    def generate_report(self) -> str:
        """生成性能报告"""
        metrics = self.calculate_performance_metrics()
        
        report = [
            "策略性能报告",
            "=" * 50,
            f"报告生成时间: {datetime.now()}",
            f"策略运行时间: {metrics.get('runtime', 0):.2f} 小时",
            "",
            "交易统计",
            "-" * 30,
            f"总交易次数: {metrics.get('total_trades', 0)}",
            f"盈利交易: {metrics.get('winning_trades', 0)}",
            f"亏损交易: {metrics.get('losing_trades', 0)}",
            f"胜率: {metrics.get('win_rate', 0):.2%}",
            "",
            "盈利统计",
            "-" * 30,
            f"总盈利: {metrics.get('total_profit', 0):.2f}",
            f"平均盈利: {metrics.get('average_profit', 0):.2f}",
            f"最大单笔盈利: {metrics.get('max_profit', 0):.2f}",
            f"最大单笔亏损: {metrics.get('max_loss', 0):.2f}",
            f"盈亏比: {metrics.get('profit_factor', 0):.2f}",
            "",
            "风险指标",
            "-" * 30,
            f"夏普比率: {metrics.get('sharpe_ratio', 0):.2f}",
            f"最大回撤: {metrics.get('max_drawdown', 0):.2%}",
        ]
        
        return "\n".join(report)
        
    def save_trades(self, filepath: str):
        """保存交易记录"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.trades, f, default=str, indent=2)
            self.logger.info(f"交易记录已保存至: {filepath}")
        except Exception as e:
            self.logger.error(f"保存交易记录失败: {str(e)}")
            
    def load_trades(self, filepath: str):
        """加载交易记录"""
        try:
            with open(filepath, 'r') as f:
                self.trades = json.load(f)
            self.logger.info(f"已加载交易记录: {filepath}")
        except Exception as e:
            self.logger.error(f"加载交易记录失败: {str(e)}") 