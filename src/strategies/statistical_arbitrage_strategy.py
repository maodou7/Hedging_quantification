"""
统计套利策略

基于价格统计特性的套利策略:
1. 均值回归
2. 协整性
3. 标准差突破
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import coint
from src.strategies.base_strategy import BaseStrategy
from src.core.order_manager import OrderManager, Order
from src.core.strategy_monitor import StrategyMonitor
from src.risk_management.risk_manager import RiskManager
from src.utils.logger import ArbitrageLogger
from src.Config.exchange_config import STRATEGY_CONFIG

class StatisticalArbitrageStrategy(BaseStrategy):
    def __init__(self, exchange_instance, config: Dict[str, Any] = None):
        super().__init__()
        self.exchange_instance = exchange_instance
        self.config = config or STRATEGY_CONFIG['statistical_arbitrage']
        
        # 初始化组件
        self.order_manager = OrderManager()
        self.risk_manager = RiskManager()
        self.strategy_monitor = StrategyMonitor()
        self.logger = ArbitrageLogger()
        
        # 策略参数
        self.window_size = self.config['window_size']
        self.z_score_threshold = self.config['z_score_threshold']
        self.mean_reversion_threshold = self.config['mean_reversion_threshold']
        self.trade_amount = self.config['trade_amount']
        self.max_open_orders = self.config['max_open_orders']
        
        # 价格历史数据
        self.price_history: Dict[str, pd.DataFrame] = {}
        self.pairs: List[Tuple[str, str]] = []
        
    async def start(self):
        """启动策略"""
        self.is_running = True
        # 初始化交易对
        await self._initialize_pairs()
        self.logger.info("统计套利策略已启动")
        
    async def stop(self):
        """停止策略"""
        self.is_running = False
        # 取消所有未完成订单
        active_orders = self.order_manager.get_active_orders()
        for order in active_orders:
            await self.order_manager.cancel_order(self.exchange_instance, order.order_id)
        self.logger.info("统计套利策略已停止")
        
    async def _initialize_pairs(self):
        """初始化交易对"""
        try:
            exchange = await self.exchange_instance.get_rest_instance(list(self.exchange_instance.exchanges.keys())[0])
            markets = await exchange.load_markets()
            
            # 获取所有USDT计价的交易对
            usdt_pairs = [symbol for symbol in markets.keys() if symbol.endswith('/USDT')]
            
            # 初始化价格历史数据
            for symbol in usdt_pairs:
                ohlcv = await exchange.fetch_ohlcv(symbol, '1m', limit=self.window_size)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                self.price_history[symbol] = df
                
            # 寻找协整对
            self.pairs = await self._find_cointegrated_pairs(usdt_pairs)
            self.logger.info(f"找到 {len(self.pairs)} 个协整对")
            
        except Exception as e:
            self.logger.error(f"初始化交易对时发生错误: {str(e)}")
            
    async def _find_cointegrated_pairs(self, symbols: List[str]) -> List[Tuple[str, str]]:
        """寻找协整对"""
        cointegrated_pairs = []
        
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                symbol1, symbol2 = symbols[i], symbols[j]
                
                # 获取收盘价序列
                price1 = self.price_history[symbol1]['close'].values
                price2 = self.price_history[symbol2]['close'].values
                
                # 计算协整性
                score, pvalue, _ = coint(price1, price2)
                
                # 如果p值小于0.05，认为存在协整关系
                if pvalue < 0.05:
                    cointegrated_pairs.append((symbol1, symbol2))
                    
        return cointegrated_pairs
        
    async def process_price_update(self, exchange_id: str, symbol: str, price_data: Dict[str, Any]):
        """处理价格更新"""
        if not self.is_running:
            return
            
        try:
            # 更新价格历史数据
            self._update_price_history(symbol, price_data)
            
            # 检查是否有套利机会
            for pair in self.pairs:
                if symbol in pair:
                    opportunity = self.calculate_opportunity(exchange_id, pair, price_data)
                    if opportunity:
                        await self.execute_trade(opportunity)
                        
        except Exception as e:
            self.logger.error(f"处理价格更新时发生错误: {str(e)}")
            
    def _update_price_history(self, symbol: str, price_data: Dict[str, Any]):
        """更新价格历史数据"""
        try:
            if symbol not in self.price_history:
                self.price_history[symbol] = pd.DataFrame(columns=['close'])
                
            df = self.price_history[symbol]
            
            # 添加新数据
            new_row = pd.DataFrame({
                'close': [price_data['close']]
            }, index=[pd.Timestamp.now()])
            
            df = pd.concat([df, new_row])
            
            # 保持固定窗口大小
            if len(df) > self.window_size:
                df = df.iloc[-self.window_size:]
                
            self.price_history[symbol] = df
            
        except Exception as e:
            self.logger.error(f"更新价格历史数据时发生错误: {str(e)}")
            
    def calculate_opportunity(self, exchange_id: str, pair: Tuple[str, str], 
                            price_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """计算统计套利机会"""
        try:
            symbol1, symbol2 = pair
            
            # 获取价格序列
            price1 = self.price_history[symbol1]['close']
            price2 = self.price_history[symbol2]['close']
            
            # 计算价格比率
            ratio = price1 / price2
            
            # 计算z分数
            z_score = (ratio - ratio.mean()) / ratio.std()
            
            # 计算均值回归概率
            mean_reversion_prob = self._calculate_mean_reversion_probability(ratio)
            
            # 判断交易信号
            if abs(z_score.iloc[-1]) > self.z_score_threshold and mean_reversion_prob > self.mean_reversion_threshold:
                return {
                    'type': 'statistical_arbitrage',
                    'exchange_id': exchange_id,
                    'pair': pair,
                    'z_score': z_score.iloc[-1],
                    'mean_reversion_prob': mean_reversion_prob,
                    'action': 'sell' if z_score.iloc[-1] > 0 else 'buy',
                    'timestamp': datetime.now()
                }
                
            return None
            
        except Exception as e:
            self.logger.error(f"计算统计套利机会时发生错误: {str(e)}")
            return None
            
    def _calculate_mean_reversion_probability(self, price_ratio: pd.Series) -> float:
        """计算均值回归概率"""
        try:
            # 计算价格比率的变化
            ratio_changes = price_ratio.diff().dropna()
            
            # 计算当前偏离均值的程度
            current_deviation = price_ratio.iloc[-1] - price_ratio.mean()
            
            # 计算向均值方向移动的概率
            if current_deviation > 0:
                prob = len(ratio_changes[ratio_changes < 0]) / len(ratio_changes)
            else:
                prob = len(ratio_changes[ratio_changes > 0]) / len(ratio_changes)
                
            return prob
            
        except Exception as e:
            self.logger.error(f"计算均值回归概率时发生错误: {str(e)}")
            return 0
            
    async def execute_trade(self, opportunity: Dict[str, Any]):
        """执行统计套利交易"""
        try:
            self.logger.info(f"执行统计套利交易: {opportunity}")
            
            exchange_id = opportunity['exchange_id']
            symbol1, symbol2 = opportunity['pair']
            action = opportunity['action']
            
            # 计算交易数量
            price1 = self.price_history[symbol1]['close'].iloc[-1]
            price2 = self.price_history[symbol2]['close'].iloc[-1]
            
            amount1 = round(self.trade_amount / price1, 8)
            amount2 = round(self.trade_amount / price2, 8)
            
            # 创建对冲订单
            orders = []
            if action == 'buy':
                # 买入symbol1，卖出symbol2
                orders.append(Order(
                    exchange_id=exchange_id,
                    symbol=symbol1,
                    order_type='limit',
                    side='buy',
                    amount=amount1,
                    price=price1
                ))
                orders.append(Order(
                    exchange_id=exchange_id,
                    symbol=symbol2,
                    order_type='limit',
                    side='sell',
                    amount=amount2,
                    price=price2
                ))
            else:
                # 卖出symbol1，买入symbol2
                orders.append(Order(
                    exchange_id=exchange_id,
                    symbol=symbol1,
                    order_type='limit',
                    side='sell',
                    amount=amount1,
                    price=price1
                ))
                orders.append(Order(
                    exchange_id=exchange_id,
                    symbol=symbol2,
                    order_type='limit',
                    side='buy',
                    amount=amount2,
                    price=price2
                ))
                
            # 执行订单
            order_ids = []
            for order in orders:
                order_id = await self.order_manager.create_order(self.exchange_instance, order)
                if not order_id:
                    # 如果有订单失败，取消所有已成功的订单
                    for completed_id in order_ids:
                        await self.order_manager.cancel_order(self.exchange_instance, completed_id)
                    return
                order_ids.append(order_id)
                
            # 记录交易
            trade_record = {
                'type': 'statistical_arbitrage',
                'exchange_id': exchange_id,
                'pair': opportunity['pair'],
                'orders': order_ids,
                'z_score': opportunity['z_score'],
                'mean_reversion_prob': opportunity['mean_reversion_prob'],
                'action': action,
                'timestamp': datetime.now()
            }
            
            self.strategy_monitor.record_trade(trade_record)
            
            # 监控订单状态
            await self._monitor_orders(order_ids)
            
        except Exception as e:
            self.logger.error(f"执行统计套利交易时发生错误: {str(e)}")
            
    async def _monitor_orders(self, order_ids: List[str]):
        """监控订单状态"""
        try:
            for order_id in order_ids:
                await self.order_manager.update_order_status(self.exchange_instance, order_id)
        except Exception as e:
            self.logger.error(f"监控订单状态时发生错误: {str(e)}")
            
    def get_strategy_status(self) -> Dict[str, Any]:
        """获取策略状态"""
        return {
            'is_running': self.is_running,
            'active_orders': len(self.order_manager.get_active_orders()),
            'completed_orders': len(self.order_manager.get_completed_orders()),
            'pairs_count': len(self.pairs),
            'performance_metrics': self.strategy_monitor.calculate_performance_metrics()
        } 