"""网格交易策略实现

此模块实现了基于网格交易的策略逻辑，通过在价格区间内设置多个网格来进行自动交易。
"""

from typing import Dict, List, Optional
from decimal import Decimal
from .config import DEFAULT_CONFIG, validate_config

class GridTradingStrategy:
    """网格交易策略类
    
    在指定价格区间内设置等距网格，当价格触及网格线时进行买入或卖出操作。
    """
    
    def __init__(self, config: Dict = None):
        """初始化网格交易策略
        
        Args:
            config: 策略配置，若未提供则使用默认配置
        """
        self.config = config or DEFAULT_CONFIG.copy()
        validate_config(self.config)
        
        # 初始化网格
        self.grid_prices = self._calculate_grid_prices()
        self.active_orders: Dict[str, Dict] = {}
        self.positions: Dict[str, Decimal] = {}
        
    def _calculate_grid_prices(self) -> List[Decimal]:
        """计算网格价格点
        
        Returns:
            List[Decimal]: 网格价格列表
        """
        upper_price = Decimal(str(self.config['upper_price']))
        lower_price = Decimal(str(self.config['lower_price']))
        grid_num = self.config['grid_num']
        
        # 计算网格间距
        grid_interval = (upper_price - lower_price) / Decimal(str(grid_num - 1))
        
        # 生成网格价格点
        return [lower_price + grid_interval * Decimal(str(i)) 
                for i in range(grid_num)]
    
    def on_tick(self, tick_data: Dict):
        """处理市场数据更新
        
        Args:
            tick_data: 市场数据字典
        """
        current_price = Decimal(str(tick_data['price']))
        self._check_grid_orders(current_price)
    
    def _check_grid_orders(self, current_price: Decimal):
        """检查并更新网格订单
        
        Args:
            current_price: 当前市场价格
        """
        for i, grid_price in enumerate(self.grid_prices):
            # 跳过已有活动订单的网格
            if str(grid_price) in self.active_orders:
                continue
                
            # 根据当前价格决定买入或卖出
            if i < len(self.grid_prices) - 1:
                next_price = self.grid_prices[i + 1]
                if current_price > grid_price and current_price < next_price:
                    self._place_grid_orders(grid_price, next_price)
    
    def _place_grid_orders(self, lower_price: Decimal, upper_price: Decimal):
        """在网格点位下单
        
        Args:
            lower_price: 下边界价格
            upper_price: 上边界价格
        """
        # 计算订单数量
        amount = Decimal(str(self.config['grid_invest_amount'])) / lower_price
        
        # 确保满足最小交易量
        min_amount = Decimal(str(self.config['min_amount']))
        if amount < min_amount:
            return
            
        # 创建买单和卖单
        buy_order = {
            'type': 'limit',
            'side': 'buy',
            'price': str(lower_price),
            'amount': str(amount)
        }
        
        sell_order = {
            'type': 'limit',
            'side': 'sell',
            'price': str(upper_price),
            'amount': str(amount)
        }
        
        # 记录订单
        self.active_orders[str(lower_price)] = buy_order
        self.active_orders[str(upper_price)] = sell_order
    
    def on_orderbook(self, orderbook: Dict):
        """处理订单簿数据
        
        Args:
            orderbook: 订单簿数据
        """
        # 可以根据订单簿深度调整网格策略
        pass
    
    def on_trade(self, trade: Dict):
        """处理成交信息
        
        Args:
            trade: 成交信息
        """
        # 更新持仓信息
        order_id = trade['order_id']
        if order_id in self.active_orders:
            del self.active_orders[order_id]
            
        # 更新策略状态
        self._update_position(trade)
    
    def _update_position(self, trade: Dict):
        """更新持仓信息
        
        Args:
            trade: 成交信息
        """
        symbol = trade['symbol']
        amount = Decimal(str(trade['amount']))
        
        if trade['side'] == 'buy':
            self.positions[symbol] = self.positions.get(symbol, Decimal('0')) + amount
        else:
            self.positions[symbol] = self.positions.get(symbol, Decimal('0')) - amount
    
    def on_position_update(self, position: Dict):
        """处理持仓更新
        
        Args:
            position: 持仓信息
        """
        # 可以根据持仓变化调整网格策略
        symbol = position['symbol']
        self.positions[symbol] = Decimal(str(position['amount']))