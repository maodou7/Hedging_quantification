"""
价差套利策略

实现交易所间的价差套利逻辑，集成机器学习预测
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from src.strategies.base_strategy import BaseStrategy
from src.ml.model_trainer import RealTimeModelTrainer
from src.risk_management.slippage_calculator import SlippageCalculator
from src.risk_management.risk_manager import RiskManager
from src.utils.logger import ArbitrageLogger
from src.core.data_store import DataStore
from src.core.order_manager import OrderManager, Order
from src.core.strategy_monitor import StrategyMonitor
from src.config.trading import STRATEGY_CONFIG
from src.config.exchange import FEATURE_FLAGS

class SpreadArbitrageStrategy(BaseStrategy):
    def __init__(self, exchange_instance, config: Dict[str, Any] = None):
        super().__init__()
        self.exchange_instance = exchange_instance
        self.config = config or STRATEGY_CONFIG['spread_arbitrage']
        self.feature_flags = FEATURE_FLAGS
        
        # 初始化组件
        self.logger = ArbitrageLogger()
        self.data_store = DataStore()
        
        # 根据功能开关初始化组件
        if self.feature_flags['machine_learning']['enabled']:
            self.model_trainer = RealTimeModelTrainer(
                update_interval=self.feature_flags['machine_learning']['update_interval']
            )
            self.prediction_threshold = self.feature_flags['machine_learning']['prediction_threshold']
        
        if self.feature_flags['trading']['enabled']:
            self.slippage_calculator = SlippageCalculator()
            self.risk_manager = RiskManager()
            self.order_manager = OrderManager()
            self.strategy_monitor = StrategyMonitor()
            
            # 策略参数
            self.min_profit_threshold = self.feature_flags['trading']['min_profit_threshold']
            self.trade_amount = self.config['trade_amount']
            self.max_open_orders = self.feature_flags['trading']['max_open_orders']
            self.price_decimal = self.config['price_decimal']
            self.amount_decimal = self.config['amount_decimal']

    async def start(self):
        """启动策略"""
        self.is_running = True
        
        # 根据功能开关启动相应组件
        if self.feature_flags['machine_learning']['enabled']:
            self.model_trainer.start()
            self.logger.info("机器学习模型训练器已启动")
            
        if self.feature_flags['monitoring']['enabled']:
            self.logger.info("市场监控已启动")
            
        if self.feature_flags['trading']['enabled']:
            self.logger.info("交易功能已启动")
            
        self.logger.info("价差套利策略已启动")

    async def stop(self):
        """停止策略"""
        self.is_running = False
        
        if self.feature_flags['machine_learning']['enabled']:
            self.model_trainer.stop()
            
        if self.feature_flags['trading']['enabled']:
            # 取消所有未完成的订单
            active_orders = self.order_manager.get_active_orders()
            for order in active_orders:
                await self.order_manager.cancel_order(self.exchange_instance, order.order_id)
                
        self.logger.info("价差套利策略已停止")

    async def process_price_update(self, exchange_id: str, symbol: str, price_data: Dict[str, Any]):
        """处理价格更新"""
        if not self.is_running:
            return

        try:
            # 1. 存储价格数据
            if self.feature_flags['monitoring']['enabled']:
                self.data_store.update_price(exchange_id, symbol, price_data)
            
            # 2. 机器学习相关处理
            price_prediction = None
            if self.feature_flags['machine_learning']['enabled']:
                # 更新模型训练数据
                self.model_trainer.add_price_data(exchange_id, symbol, price_data)
                
                # 检查是否有足够的数据点进行预测
                if len(self.data_store.get_price_history(exchange_id, symbol)) >= self.feature_flags['machine_learning']['min_data_points']:
                    price_prediction = self.model_trainer.get_prediction(exchange_id, symbol)

            # 3. 交易相关处理
            if self.feature_flags['trading']['enabled']:
                # 计算预期滑点
                slippage = self.slippage_calculator.calculate(exchange_id, symbol, price_data)

                # 风险评估
                if not self.risk_manager.check_risk(exchange_id, symbol, price_data, slippage):
                    return

                # 检查是否有太多未完成订单
                if len(self.order_manager.get_active_orders()) >= self.max_open_orders:
                    return

                # 寻找套利机会
                opportunity = self.calculate_opportunity(exchange_id, symbol, price_data, price_prediction)
                if opportunity:
                    await self.execute_trade(opportunity)

        except Exception as e:
            self.logger.error(f"处理价格更新时发生错误: {str(e)}")

    def calculate_opportunity(self, exchange_id: str, symbol: str, 
                            price_data: Dict[str, Any], 
                            price_prediction: Optional[float]) -> Optional[Dict[str, Any]]:
        """计算套利机会"""
        try:
            # 获取所有交易所的价格数据
            all_prices = self.data_store.get_all_prices(symbol)
            
            # 找出最高买价和最低卖价
            best_bid = {'price': 0, 'exchange': None}
            best_ask = {'price': float('inf'), 'exchange': None}
            
            for ex_id, ex_data in all_prices.items():
                if ex_data['bid'] > best_bid['price']:
                    best_bid = {'price': ex_data['bid'], 'exchange': ex_id}
                if ex_data['ask'] < best_ask['price']:
                    best_ask = {'price': ex_data['ask'], 'exchange': ex_id}
            
            # 计算价差
            spread = best_bid['price'] - best_ask['price']
            
            # 如果有价格预测，考虑预测因素
            if price_prediction is not None:
                current_price = float(price_data['price'])
                predicted_change = (price_prediction - current_price) / current_price
                
                # 根据预测调整交易方向
                if predicted_change > self.prediction_threshold:
                    # 预测价格上涨，增加买入意愿
                    spread *= (1 + predicted_change)
                elif predicted_change < -self.prediction_threshold:
                    # 预测价格下跌，减少买入意愿
                    spread *= (1 + predicted_change)
            
            # 如果价差超过最小利润阈值
            if spread > self.min_profit_threshold:
                return {
                    'type': 'spread_arbitrage',
                    'symbol': symbol,
                    'buy_exchange': best_ask['exchange'],
                    'buy_price': best_ask['price'],
                    'sell_exchange': best_bid['exchange'],
                    'sell_price': best_bid['price'],
                    'spread': spread,
                    'timestamp': price_data.get('timestamp'),
                    'trade_amount': self.trade_amount,
                    'prediction': price_prediction
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"计算套利机会时发生错误: {str(e)}")
            return None

    async def execute_trade(self, opportunity: Dict[str, Any]):
        """执行套利交易"""
        try:
            self.logger.info(f"执行套利交易: {opportunity}")
            
            # 1. 计算交易数量
            amount = round(self.trade_amount / opportunity['buy_price'], self.amount_decimal)
            
            # 2. 创建买单
            buy_order = Order(
                exchange_id=opportunity['buy_exchange'],
                symbol=opportunity['symbol'],
                order_type='limit',
                side='buy',
                amount=amount,
                price=round(opportunity['buy_price'], self.price_decimal)
            )
            
            # 3. 创建卖单
            sell_order = Order(
                exchange_id=opportunity['sell_exchange'],
                symbol=opportunity['symbol'],
                order_type='limit',
                side='sell',
                amount=amount,
                price=round(opportunity['sell_price'], self.price_decimal)
            )
            
            # 4. 同时发送订单
            buy_order_id = await self.order_manager.create_order(self.exchange_instance, buy_order)
            sell_order_id = await self.order_manager.create_order(self.exchange_instance, sell_order)
            
            if not buy_order_id or not sell_order_id:
                # 如果其中一个订单失败，取消另一个订单
                if buy_order_id:
                    await self.order_manager.cancel_order(self.exchange_instance, buy_order_id)
                if sell_order_id:
                    await self.order_manager.cancel_order(self.exchange_instance, sell_order_id)
                return
            
            # 5. 记录交易
            trade_record = {
                'type': 'spread_arbitrage',
                'buy_order_id': buy_order_id,
                'sell_order_id': sell_order_id,
                'symbol': opportunity['symbol'],
                'buy_exchange': opportunity['buy_exchange'],
                'sell_exchange': opportunity['sell_exchange'],
                'buy_price': opportunity['buy_price'],
                'sell_price': opportunity['sell_price'],
                'amount': amount,
                'spread': opportunity['spread'],
                'profit': (opportunity['sell_price'] - opportunity['buy_price']) * amount,
                'timestamp': datetime.now()
            }
            
            self.strategy_monitor.record_trade(trade_record)
            
            # 6. 更新风险管理器
            self.risk_manager.update_position(opportunity['symbol'], amount)
            self.risk_manager.update_pnl(trade_record['profit'])
            
            # 7. 启动订单状态监控
            await self._monitor_orders(buy_order_id, sell_order_id)
            
        except Exception as e:
            self.logger.error(f"执行套利交易时发生错误: {str(e)}")
            
    async def _monitor_orders(self, buy_order_id: str, sell_order_id: str):
        """监控订单状态"""
        try:
            # 更新买单状态
            await self.order_manager.update_order_status(self.exchange_instance, buy_order_id)
            # 更新卖单状态
            await self.order_manager.update_order_status(self.exchange_instance, sell_order_id)
            
        except Exception as e:
            self.logger.error(f"监控订单状态时发生错误: {str(e)}")
            
    def get_strategy_status(self) -> Dict[str, Any]:
        """获取策略状态"""
        return {
            'is_running': self.is_running,
            'active_orders': len(self.order_manager.get_active_orders()),
            'completed_orders': len(self.order_manager.get_completed_orders()),
            'risk_metrics': self.risk_manager.get_risk_metrics(),
            'performance_metrics': self.strategy_monitor.calculate_performance_metrics()
        } 