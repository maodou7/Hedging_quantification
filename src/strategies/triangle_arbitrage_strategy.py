"""
三角套利策略

实现同一交易所内的三角套利:
A/B -> B/C -> C/A 或 A/C -> C/B -> B/A
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from src.strategies.base_strategy import BaseStrategy
from src.core.order_manager import OrderManager, Order
from src.core.strategy_monitor import StrategyMonitor
from src.risk_management.risk_manager import RiskManager
from src.utils.logger import ArbitrageLogger
from src.Config.exchange_config import STRATEGY_CONFIG

class TriangleArbitrageStrategy(BaseStrategy):
    def __init__(self, exchange_instance, config: Dict[str, Any] = None):
        super().__init__()
        self.exchange_instance = exchange_instance
        self.config = config or STRATEGY_CONFIG['triangle_arbitrage']
        
        # 初始化组件
        self.order_manager = OrderManager()
        self.risk_manager = RiskManager()
        self.strategy_monitor = StrategyMonitor()
        self.logger = ArbitrageLogger()
        
        # 策略参数
        self.min_profit_threshold = self.config['min_profit_threshold']
        self.trade_amount = self.config['trade_amount']
        self.max_open_orders = self.config['max_open_orders']
        
        # 三角组合
        self.triangles = []
        
    async def start(self):
        """启动策略"""
        self.is_running = True
        # 获取并初始化所有可能的三角组合
        await self._initialize_triangles()
        self.logger.info("三角套利策略已启动")
        
    async def stop(self):
        """停止策略"""
        self.is_running = False
        # 取消所有未完成订单
        active_orders = self.order_manager.get_active_orders()
        for order in active_orders:
            await self.order_manager.cancel_order(self.exchange_instance, order.order_id)
        self.logger.info("三角套利策略已停止")
        
    async def _initialize_triangles(self):
        """初始化所有可能的三角组合"""
        try:
            exchange = await self.exchange_instance.get_rest_instance(list(self.exchange_instance.exchanges.keys())[0])
            markets = await exchange.load_markets()
            
            # 构建货币对关系图
            pairs_graph = {}
            for symbol in markets:
                base, quote = symbol.split('/')
                if base not in pairs_graph:
                    pairs_graph[base] = set()
                if quote not in pairs_graph:
                    pairs_graph[quote] = set()
                pairs_graph[base].add(quote)
                pairs_graph[quote].add(base)
            
            # 寻找所有可能的三角组合
            for base in pairs_graph:
                for quote in pairs_graph[base]:
                    for third in pairs_graph[quote]:
                        if third in pairs_graph[base]:
                            triangle = {
                                'symbols': [f"{base}/{quote}", f"{quote}/{third}", f"{third}/{base}"],
                                'currencies': [base, quote, third]
                            }
                            self.triangles.append(triangle)
                            
            self.logger.info(f"找到 {len(self.triangles)} 个三角组合")
            
        except Exception as e:
            self.logger.error(f"初始化三角组合时发生错误: {str(e)}")
            
    async def process_price_update(self, exchange_id: str, symbol: str, price_data: Dict[str, Any]):
        """处理价格更新"""
        if not self.is_running:
            return
            
        try:
            # 对每个三角组合计算套利机会
            for triangle in self.triangles:
                if symbol in triangle['symbols']:
                    opportunity = await self.calculate_opportunity(exchange_id, triangle, price_data)
                    if opportunity:
                        await self.execute_trade(opportunity)
                        
        except Exception as e:
            self.logger.error(f"处理价格更新时发生错误: {str(e)}")
            
    async def calculate_opportunity(self, exchange_id: str, triangle: Dict[str, Any], 
                                 price_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """计算三角套利机会"""
        try:
            exchange = await self.exchange_instance.get_rest_instance(exchange_id)
            
            # 获取三个交易对的订单簿
            orderbooks = {}
            for symbol in triangle['symbols']:
                orderbook = await exchange.fetch_order_book(symbol)
                orderbooks[symbol] = {
                    'bid': orderbook['bids'][0][0] if orderbook['bids'] else 0,
                    'ask': orderbook['asks'][0][0] if orderbook['asks'] else float('inf')
                }
            
            # 计算正向和反向套利路径的利润
            forward_profit = self._calculate_triangular_profit(orderbooks, triangle['symbols'], False)
            reverse_profit = self._calculate_triangular_profit(orderbooks, triangle['symbols'], True)
            
            # 选择最优路径
            if forward_profit > reverse_profit:
                profit_ratio = forward_profit
                is_reverse = False
            else:
                profit_ratio = reverse_profit
                is_reverse = True
                
            # 检查是否超过最小利润阈值
            if profit_ratio > self.min_profit_threshold:
                return {
                    'type': 'triangle_arbitrage',
                    'exchange_id': exchange_id,
                    'triangle': triangle,
                    'orderbooks': orderbooks,
                    'profit_ratio': profit_ratio,
                    'is_reverse': is_reverse,
                    'timestamp': datetime.now()
                }
                
            return None
            
        except Exception as e:
            self.logger.error(f"计算三角套利机会时发生错误: {str(e)}")
            return None
            
    def _calculate_triangular_profit(self, orderbooks: Dict[str, Dict[float, float]], 
                                   symbols: List[str], is_reverse: bool) -> float:
        """计算三角套利利润率"""
        try:
            # 考虑交易手续费
            fee_rate = 0.001  # 0.1% 手续费
            
            if is_reverse:
                # 反向路径: A->C->B->A
                rate1 = 1 / orderbooks[symbols[0]]['ask']  # A/B -> B/A
                rate2 = 1 / orderbooks[symbols[1]]['ask']  # B/C -> C/B
                rate3 = orderbooks[symbols[2]]['bid']      # C/A
            else:
                # 正向路径: A->B->C->A
                rate1 = orderbooks[symbols[0]]['bid']      # A/B
                rate2 = orderbooks[symbols[1]]['bid']      # B/C
                rate3 = orderbooks[symbols[2]]['bid']      # C/A
                
            # 计算总收益率(考虑手续费)
            profit_ratio = (rate1 * rate2 * rate3) * ((1 - fee_rate) ** 3) - 1
            
            return profit_ratio
            
        except Exception as e:
            self.logger.error(f"计算三角套利利润率时发生错误: {str(e)}")
            return 0
            
    async def execute_trade(self, opportunity: Dict[str, Any]):
        """执行三角套利交易"""
        try:
            self.logger.info(f"执行三角套利交易: {opportunity}")
            
            exchange_id = opportunity['exchange_id']
            triangle = opportunity['triangle']
            is_reverse = opportunity['is_reverse']
            
            # 计算交易数量
            trade_amount = self.trade_amount
            orders = []
            
            # 创建订单序列
            if is_reverse:
                # 反向路径: A->C->B->A
                symbols = triangle['symbols'][::-1]
                sides = ['sell', 'sell', 'buy']
            else:
                # 正向路径: A->B->C->A
                symbols = triangle['symbols']
                sides = ['buy', 'buy', 'sell']
                
            # 创建订单
            for i, (symbol, side) in enumerate(zip(symbols, sides)):
                order = Order(
                    exchange_id=exchange_id,
                    symbol=symbol,
                    order_type='limit',
                    side=side,
                    amount=trade_amount,
                    price=opportunity['orderbooks'][symbol]['ask' if side == 'buy' else 'bid']
                )
                orders.append(order)
                
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
                'type': 'triangle_arbitrage',
                'exchange_id': exchange_id,
                'triangle': triangle,
                'orders': order_ids,
                'profit_ratio': opportunity['profit_ratio'],
                'is_reverse': is_reverse,
                'timestamp': datetime.now()
            }
            
            self.strategy_monitor.record_trade(trade_record)
            
            # 监控订单状态
            await self._monitor_orders(order_ids)
            
        except Exception as e:
            self.logger.error(f"执行三角套利交易时发生错误: {str(e)}")
            
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
            'triangles_count': len(self.triangles),
            'performance_metrics': self.strategy_monitor.calculate_performance_metrics()
        } 