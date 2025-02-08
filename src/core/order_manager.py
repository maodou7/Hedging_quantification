"""
订单管理模块

负责：
1. 订单创建和发送
2. 订单状态跟踪
3. 订单执行分析
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from src.utils.logger import ArbitrageLogger

class OrderStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"

class Order:
    def __init__(self, exchange_id: str, symbol: str, order_type: str, 
                 side: str, amount: float, price: float):
        self.exchange_id = exchange_id
        self.symbol = symbol
        self.order_type = order_type
        self.side = side
        self.amount = amount
        self.price = price
        self.status = OrderStatus.PENDING
        self.filled_amount = 0.0
        self.average_price = 0.0
        self.order_id = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.error = None

class OrderManager:
    def __init__(self):
        self.logger = ArbitrageLogger()
        self.active_orders: Dict[str, Order] = {}
        self.completed_orders: List[Order] = []
        
    async def create_order(self, exchange_instance, order: Order) -> Optional[str]:
        """创建订单"""
        try:
            exchange = await exchange_instance.get_rest_instance(order.exchange_id)
            response = await exchange.create_order(
                symbol=order.symbol,
                type=order.order_type,
                side=order.side,
                amount=order.amount,
                price=order.price
            )
            
            order.order_id = response['id']
            order.status = OrderStatus.SENT
            order.updated_at = datetime.now()
            
            self.active_orders[order.order_id] = order
            self.logger.info(f"订单创建成功: {order.order_id}")
            
            return order.order_id
            
        except Exception as e:
            order.status = OrderStatus.FAILED
            order.error = str(e)
            self.logger.error(f"创建订单失败: {str(e)}")
            return None
            
    async def update_order_status(self, exchange_instance, order_id: str):
        """更新订单状态"""
        if order_id not in self.active_orders:
            return
            
        order = self.active_orders[order_id]
        try:
            exchange = await exchange_instance.get_rest_instance(order.exchange_id)
            order_info = await exchange.fetch_order(order_id, order.symbol)
            
            order.status = OrderStatus(order_info['status'])
            order.filled_amount = order_info['filled']
            order.average_price = order_info['average']
            order.updated_at = datetime.now()
            
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.FAILED]:
                self._move_to_completed(order_id)
                
        except Exception as e:
            self.logger.error(f"更新订单状态失败: {str(e)}")
            
    async def cancel_order(self, exchange_instance, order_id: str):
        """取消订单"""
        if order_id not in self.active_orders:
            return
            
        order = self.active_orders[order_id]
        try:
            exchange = await exchange_instance.get_rest_instance(order.exchange_id)
            await exchange.cancel_order(order_id, order.symbol)
            
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
            self._move_to_completed(order_id)
            
        except Exception as e:
            self.logger.error(f"取消订单失败: {str(e)}")
            
    def _move_to_completed(self, order_id: str):
        """将订单移至已完成列表"""
        if order_id in self.active_orders:
            order = self.active_orders.pop(order_id)
            self.completed_orders.append(order)
            
    def get_active_orders(self) -> List[Order]:
        """获取活跃订单列表"""
        return list(self.active_orders.values())
        
    def get_completed_orders(self) -> List[Order]:
        """获取已完成订单列表"""
        return self.completed_orders
        
    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """根据ID获取订单"""
        return self.active_orders.get(order_id) or next(
            (order for order in self.completed_orders if order.order_id == order_id), 
            None
        ) 