"""
滑点计算器模块
负责计算交易滑点
"""

from typing import Dict
from src.Config.exchange_config import RISK_CONFIG

class SlippageCalculator:
    """滑点计算器"""
    def __init__(self, max_slippage_percent: float = None):
        # 使用风险配置中的最大滑点参数
        self.max_slippage_percent = max_slippage_percent or 0.001  # 默认0.1%的最大滑点
    
    def calculate_slippage(self, order_book: Dict, side: str, amount: float, base_price: float) -> float:
        """
        计算给定交易量的滑点
        :param order_book: 订单簿数据
        :param side: 交易方向 ('buy' 或 'sell')
        :param amount: 交易数量
        :param base_price: 基准价格
        :return: 滑点成本
        """
        try:
            orders = order_book['asks'] if side == 'buy' else order_book['bids']
            remaining_amount = amount
            weighted_price = 0
            
            for price, size in orders:
                if remaining_amount <= 0:
                    break
                
                executed_amount = min(remaining_amount, size)
                weighted_price += price * executed_amount
                remaining_amount -= executed_amount
            
            if remaining_amount > 0:
                # 订单簿深度不足
                return float('inf')
            
            average_price = weighted_price / amount
            slippage = abs(average_price - base_price)
            
            # 检查滑点是否超过最大允许值
            if (slippage / base_price) > self.max_slippage_percent:
                return float('inf')
            
            return slippage
            
        except Exception as e:
            print(f"计算滑点时发生错误: {str(e)}")
            return float('inf') 