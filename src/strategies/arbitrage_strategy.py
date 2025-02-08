"""
套利策略核心类

负责：
1. 接收价格监控数据
2. 计算套利机会
3. 执行套利交易
4. 风险控制
"""

from typing import Dict, List, Any
from src.core.price_predictor import PricePredictor
from src.risk_management.slippage_calculator import SlippageCalculator
from src.risk_management.risk_manager import RiskManager
from src.utils.logger import ArbitrageLogger
from src.core.data_store import DataStore

class ArbitrageStrategy:
    def __init__(self):
        self.price_predictor = PricePredictor()
        self.slippage_calculator = SlippageCalculator()
        self.risk_manager = RiskManager()
        self.logger = ArbitrageLogger()
        self.data_store = DataStore()
        self.is_running = False

    async def start(self):
        """启动套利策略"""
        self.is_running = True
        print("套利策略系统已启动")

    async def stop(self):
        """停止套利策略"""
        self.is_running = False
        print("套利策略系统已停止")

    async def process_price_update(self, exchange_id: str, symbol: str, price_data: Dict[str, Any]):
        """处理价格更新
        
        Args:
            exchange_id: 交易所ID
            symbol: 交易对
            price_data: 价格数据
        """
        if not self.is_running:
            return

        try:
            # 1. 存储价格数据
            self.data_store.update_price(exchange_id, symbol, price_data)

            # 2. 预测价格走势
            prediction = self.price_predictor.predict(exchange_id, symbol, price_data)

            # 3. 计算预期滑点
            slippage = self.slippage_calculator.calculate(exchange_id, symbol, price_data)

            # 4. 风险评估
            if not self.risk_manager.check_risk(exchange_id, symbol, price_data, slippage):
                return

            # 5. 寻找套利机会
            arbitrage_opportunity = self._find_arbitrage_opportunity(exchange_id, symbol, price_data)
            if arbitrage_opportunity:
                await self._execute_arbitrage(arbitrage_opportunity)

        except Exception as e:
            self.logger.error(f"处理价格更新时发生错误: {str(e)}")

    def _find_arbitrage_opportunity(self, exchange_id: str, symbol: str, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """寻找套利机会"""
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
            
            # 如果有套利机会
            if spread > 0:
                return {
                    'symbol': symbol,
                    'buy_exchange': best_ask['exchange'],
                    'buy_price': best_ask['price'],
                    'sell_exchange': best_bid['exchange'],
                    'sell_price': best_bid['price'],
                    'spread': spread
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"寻找套利机会时发生错误: {str(e)}")
            return None

    async def _execute_arbitrage(self, opportunity: Dict[str, Any]):
        """执行套利交易"""
        try:
            self.logger.info(f"发现套利机会: {opportunity}")
            # TODO: 实现实际的套利交易逻辑
            
        except Exception as e:
            self.logger.error(f"执行套利交易时发生错误: {str(e)}") 