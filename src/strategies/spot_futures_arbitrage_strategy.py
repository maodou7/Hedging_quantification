"""
期现套利策略

实现现货和永续合约之间的套利:
1. 基差套利
2. 资金费率套利
3. 期限结构套利
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

class SpotFuturesArbitrageStrategy(BaseStrategy):
    def __init__(self, exchange_instance, config: Dict[str, Any] = None):
        super().__init__()
        self.exchange_instance = exchange_instance
        self.config = config or STRATEGY_CONFIG['spot_futures_arbitrage']
        
        # 初始化组件
        self.order_manager = OrderManager()
        self.risk_manager = RiskManager()
        self.strategy_monitor = StrategyMonitor()
        self.logger = ArbitrageLogger()
        
        # 策略参数
        self.min_spread_ratio = self.config['min_spread_ratio']
        self.funding_rate_threshold = self.config['funding_rate_threshold']
        self.trade_amount = self.config['trade_amount']
        self.max_open_orders = self.config['max_open_orders']
        
        # 交易对映射
        self.symbol_mapping = {}  # 现货到合约的映射
        
    async def start(self):
        """启动策略"""
        self.is_running = True
        # 初始化交易对
        await self._initialize_symbols()
        self.logger.info("期现套利策略已启动")
        
    async def stop(self):
        """停止策略"""
        self.is_running = False
        # 取消所有未完成订单
        active_orders = self.order_manager.get_active_orders()
        for order in active_orders:
            await self.order_manager.cancel_order(self.exchange_instance, order.order_id)
        self.logger.info("期现套利策略已停止")
        
    async def _initialize_symbols(self):
        """初始化交易对映射"""
        try:
            exchange = await self.exchange_instance.get_rest_instance(list(self.exchange_instance.exchanges.keys())[0])
            markets = await exchange.load_markets()
            
            # 构建现货和永续合约的映射
            for symbol in markets:
                if symbol.endswith('/USDT'):  # 现货交易对
                    futures_symbol = f"{symbol.replace('/USDT', '')}/USDT:USDT"  # 永续合约交易对
                    if futures_symbol in markets:
                        self.symbol_mapping[symbol] = futures_symbol
                        
            self.logger.info(f"找到 {len(self.symbol_mapping)} 个可交易的期现对")
            
        except Exception as e:
            self.logger.error(f"初始化交易对时发生错误: {str(e)}")
            
    async def process_price_update(self, exchange_id: str, symbol: str, price_data: Dict[str, Any]):
        """处理价格更新"""
        if not self.is_running:
            return
            
        try:
            # 检查是否是可交易的交易对
            if symbol in self.symbol_mapping or symbol in self.symbol_mapping.values():
                opportunity = await self.calculate_opportunity(exchange_id, symbol, price_data)
                if opportunity:
                    await self.execute_trade(opportunity)
                    
        except Exception as e:
            self.logger.error(f"处理价格更新时发生错误: {str(e)}")
            
    async def calculate_opportunity(self, exchange_id: str, symbol: str, 
                                 price_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """计算期现套利机会"""
        try:
            exchange = await self.exchange_instance.get_rest_instance(exchange_id)
            
            # 获取现货和合约价格
            spot_symbol = symbol if symbol in self.symbol_mapping else list(self.symbol_mapping.keys())[list(self.symbol_mapping.values()).index(symbol)]
            futures_symbol = self.symbol_mapping.get(spot_symbol)
            
            spot_ticker = await exchange.fetch_ticker(spot_symbol)
            futures_ticker = await exchange.fetch_ticker(futures_symbol)
            
            # 计算基差率
            basis_ratio = (futures_ticker['last'] - spot_ticker['last']) / spot_ticker['last']
            
            # 获取资金费率
            funding_rate = await self._get_funding_rate(exchange, futures_symbol)
            
            # 判断交易信号
            if abs(basis_ratio) > self.min_spread_ratio or abs(funding_rate) > self.funding_rate_threshold:
                return {
                    'type': 'spot_futures_arbitrage',
                    'exchange_id': exchange_id,
                    'spot_symbol': spot_symbol,
                    'futures_symbol': futures_symbol,
                    'spot_price': spot_ticker['last'],
                    'futures_price': futures_ticker['last'],
                    'basis_ratio': basis_ratio,
                    'funding_rate': funding_rate,
                    'action': 'long_basis' if basis_ratio < -self.min_spread_ratio else 'short_basis',
                    'timestamp': datetime.now()
                }
                
            return None
            
        except Exception as e:
            self.logger.error(f"计算期现套利机会时发生错误: {str(e)}")
            return None
            
    async def _get_funding_rate(self, exchange, futures_symbol: str) -> float:
        """获取资金费率"""
        try:
            # 不同交易所的资金费率接口可能不同
            if hasattr(exchange, 'fetch_funding_rate'):
                funding_info = await exchange.fetch_funding_rate(futures_symbol)
                return funding_info['fundingRate']
            return 0
        except Exception as e:
            self.logger.error(f"获取资金费率时发生错误: {str(e)}")
            return 0
            
    async def execute_trade(self, opportunity: Dict[str, Any]):
        """执行期现套利交易"""
        try:
            self.logger.info(f"执行期现套利交易: {opportunity}")
            
            exchange_id = opportunity['exchange_id']
            spot_symbol = opportunity['spot_symbol']
            futures_symbol = opportunity['futures_symbol']
            action = opportunity['action']
            
            # 计算交易数量
            spot_amount = round(self.trade_amount / opportunity['spot_price'], 8)
            futures_amount = round(self.trade_amount / opportunity['futures_price'], 8)
            
            # 创建对冲订单
            orders = []
            if action == 'long_basis':
                # 现货做多，期货做空
                orders.append(Order(
                    exchange_id=exchange_id,
                    symbol=spot_symbol,
                    order_type='limit',
                    side='buy',
                    amount=spot_amount,
                    price=opportunity['spot_price']
                ))
                orders.append(Order(
                    exchange_id=exchange_id,
                    symbol=futures_symbol,
                    order_type='limit',
                    side='sell',
                    amount=futures_amount,
                    price=opportunity['futures_price']
                ))
            else:
                # 现货做空，期货做多
                orders.append(Order(
                    exchange_id=exchange_id,
                    symbol=spot_symbol,
                    order_type='limit',
                    side='sell',
                    amount=spot_amount,
                    price=opportunity['spot_price']
                ))
                orders.append(Order(
                    exchange_id=exchange_id,
                    symbol=futures_symbol,
                    order_type='limit',
                    side='buy',
                    amount=futures_amount,
                    price=opportunity['futures_price']
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
                'type': 'spot_futures_arbitrage',
                'exchange_id': exchange_id,
                'spot_symbol': spot_symbol,
                'futures_symbol': futures_symbol,
                'orders': order_ids,
                'basis_ratio': opportunity['basis_ratio'],
                'funding_rate': opportunity['funding_rate'],
                'action': action,
                'timestamp': datetime.now()
            }
            
            self.strategy_monitor.record_trade(trade_record)
            
            # 监控订单状态
            await self._monitor_orders(order_ids)
            
        except Exception as e:
            self.logger.error(f"执行期现套利交易时发生错误: {str(e)}")
            
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
            'pairs_count': len(self.symbol_mapping),
            'performance_metrics': self.strategy_monitor.calculate_performance_metrics()
        } 