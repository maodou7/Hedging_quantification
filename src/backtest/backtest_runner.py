"""
回测运行器

负责:
1. 运行回测
2. 生成报告
3. 可视化结果
"""

from typing import Dict, List, Any, Type, Optional
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from src.backtest.backtest_engine import BacktestEngine
from src.backtest.data_loader import DataLoader
from src.strategies.base_strategy import BaseStrategy
from src.utils.logger import ArbitrageLogger

class BacktestRunner:
    def __init__(self):
        self.logger = ArbitrageLogger()
        self.engine = BacktestEngine()
        self.data_loader = DataLoader()
        self.results: Dict[str, Any] = {}
        
    async def run_backtest(self, strategy_class: Type[BaseStrategy], config: Dict[str, Any],
                          start_time: datetime, end_time: datetime,
                          exchange_id: str, symbols: List[str]) -> Dict[str, Any]:
        """运行回测"""
        try:
            # 加载数据
            data = await self.data_loader.load_exchange_data(
                exchange_id,
                symbols,
                start_time,
                end_time
            )
            
            if not data:
                self.logger.error("没有加载到数据")
                return {}
                
            # 预处理数据
            data = self.data_loader.preprocess_data(data)
            
            # 设置回测引擎
            self.engine.load_data(data)
            self.engine.set_strategy(strategy_class, config)
            
            # 运行回测
            self.results = await self.engine.run(start_time, end_time)
            
            # 生成报告
            self._generate_report()
            
            return self.results
            
        except Exception as e:
            self.logger.error(f"运行回测时发生错误: {str(e)}")
            return {}
            
    def _generate_report(self):
        """生成详细报告"""
        try:
            if not self.results:
                return
                
            report_dir = Path("backtest_reports")
            report_dir.mkdir(exist_ok=True)
            
            # 生成报告时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存结果数据
            results_file = report_dir / f"results_{timestamp}.json"
            with open(results_file, 'w') as f:
                json.dump(self.results, f, default=str, indent=2)
                
            # 生成图表
            self._generate_plots(report_dir, timestamp)
            
            # 生成HTML报告
            self._generate_html_report(report_dir, timestamp)
            
        except Exception as e:
            self.logger.error(f"生成报告时发生错误: {str(e)}")
            
    def _generate_plots(self, report_dir: Path, timestamp: str):
        """生成可视化图表"""
        try:
            if not hasattr(self.engine.strategy, 'strategy_monitor'):
                return
                
            trades_df = pd.DataFrame(self.engine.strategy.strategy_monitor.trades)
            if trades_df.empty:
                return
                
            # 设置图表风格
            plt.style.use('seaborn')
            
            # 1. 收益曲线
            plt.figure(figsize=(12, 6))
            cumulative_returns = trades_df['profit'].cumsum()
            plt.plot(trades_df['timestamp'], cumulative_returns)
            plt.title('Cumulative Returns')
            plt.xlabel('Time')
            plt.ylabel('Returns')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(report_dir / f"returns_{timestamp}.png")
            plt.close()
            
            # 2. 回撤曲线
            plt.figure(figsize=(12, 6))
            running_max = cumulative_returns.expanding().max()
            drawdowns = (cumulative_returns - running_max) / running_max
            plt.plot(trades_df['timestamp'], drawdowns)
            plt.title('Drawdown')
            plt.xlabel('Time')
            plt.ylabel('Drawdown')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(report_dir / f"drawdown_{timestamp}.png")
            plt.close()
            
            # 3. 每日收益分布
            plt.figure(figsize=(10, 6))
            daily_returns = trades_df.groupby(trades_df['timestamp'].dt.date)['profit'].sum()
            sns.histplot(daily_returns, kde=True)
            plt.title('Daily Returns Distribution')
            plt.xlabel('Returns')
            plt.ylabel('Frequency')
            plt.tight_layout()
            plt.savefig(report_dir / f"returns_dist_{timestamp}.png")
            plt.close()
            
            # 4. 交易量热图
            plt.figure(figsize=(12, 6))
            trades_by_hour = trades_df.groupby([
                trades_df['timestamp'].dt.dayofweek,
                trades_df['timestamp'].dt.hour
            ]).size().unstack()
            sns.heatmap(trades_by_hour, cmap='YlOrRd')
            plt.title('Trading Activity Heatmap')
            plt.xlabel('Hour')
            plt.ylabel('Day of Week')
            plt.tight_layout()
            plt.savefig(report_dir / f"activity_heatmap_{timestamp}.png")
            plt.close()
            
        except Exception as e:
            self.logger.error(f"生成图表时发生错误: {str(e)}")
            
    def _generate_html_report(self, report_dir: Path, timestamp: str):
        """生成HTML报告"""
        try:
            template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Backtest Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .section { margin-bottom: 30px; }
                    .metric { margin: 10px 0; }
                    .plot { margin: 20px 0; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f5f5f5; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>回测报告</h1>
                    <div class="section">
                        <h2>基本信息</h2>
                        <div class="metric">回测开始时间: {start_time}</div>
                        <div class="metric">回测结束时间: {end_time}</div>
                        <div class="metric">回测天数: {total_days}</div>
                    </div>
                    
                    <div class="section">
                        <h2>性能指标</h2>
                        <table>
                            <tr>
                                <th>指标</th>
                                <th>值</th>
                            </tr>
                            <tr>
                                <td>总收益</td>
                                <td>{total_profit:.2f}</td>
                            </tr>
                            <tr>
                                <td>年化收益率</td>
                                <td>{annual_return:.2%}</td>
                            </tr>
                            <tr>
                                <td>夏普比率</td>
                                <td>{sharpe_ratio:.2f}</td>
                            </tr>
                            <tr>
                                <td>最大回撤</td>
                                <td>{max_drawdown:.2%}</td>
                            </tr>
                            <tr>
                                <td>总交易次数</td>
                                <td>{total_trades}</td>
                            </tr>
                            <tr>
                                <td>胜率</td>
                                <td>{win_rate:.2%}</td>
                            </tr>
                            <tr>
                                <td>盈亏比</td>
                                <td>{profit_factor:.2f}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="section">
                        <h2>图表</h2>
                        <div class="plot">
                            <h3>收益曲线</h3>
                            <img src="returns_{timestamp}.png" width="100%">
                        </div>
                        <div class="plot">
                            <h3>回撤曲线</h3>
                            <img src="drawdown_{timestamp}.png" width="100%">
                        </div>
                        <div class="plot">
                            <h3>收益分布</h3>
                            <img src="returns_dist_{timestamp}.png" width="100%">
                        </div>
                        <div class="plot">
                            <h3>交易活动热图</h3>
                            <img src="activity_heatmap_{timestamp}.png" width="100%">
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 填充模板
            html_content = template.format(
                start_time=self.results.get('backtest_start'),
                end_time=self.results.get('backtest_end'),
                total_days=self.results.get('total_days'),
                total_profit=self.results.get('total_profit', 0),
                annual_return=self.results.get('annual_return', 0),
                sharpe_ratio=self.results.get('sharpe_ratio', 0),
                max_drawdown=self.results.get('max_drawdown', 0),
                total_trades=self.results.get('total_trades', 0),
                win_rate=self.results.get('win_rate', 0),
                profit_factor=self.results.get('profit_factor', 0),
                timestamp=timestamp
            )
            
            # 保存HTML报告
            report_file = report_dir / f"report_{timestamp}.html"
            with open(report_file, 'w') as f:
                f.write(html_content)
                
        except Exception as e:
            self.logger.error(f"生成HTML报告时发生错误: {str(e)}")
            
    def save_results(self, filepath: str):
        """保存回测结果"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.results, f, default=str, indent=2)
            self.logger.info(f"回测结果已保存至: {filepath}")
        except Exception as e:
            self.logger.error(f"保存回测结果时发生错误: {str(e)}")
            
    def load_results(self, filepath: str):
        """加载回测结果"""
        try:
            with open(filepath, 'r') as f:
                self.results = json.load(f)
            self.logger.info(f"已加载回测结果: {filepath}")
        except Exception as e:
            self.logger.error(f"加载回测结果时发生错误: {str(e)}") 