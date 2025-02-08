"""
交易所工厂类
负责创建和管理交易所实例
"""

import ccxt.async_support as ccxt
from typing import Dict, Any, Optional
from src.utils.system_adapter import SystemAdapter
from src.Config.exchange_config import EXCHANGE_CONFIGS

class ExchangeFactory:
    """交易所工厂类"""
    
    def __init__(self):
        self.system_adapter = SystemAdapter()
        self.ccxt_config = self.system_adapter.get_ccxt_config()
        self.exchanges = {}
        
    def create_exchange(self, exchange_id: str, config: Dict[str, Any]) -> Optional[Any]:
        """
        创建交易所实例
        :param exchange_id: 交易所ID
        :param config: 交易所配置
        :return: 交易所实例
        """
        try:
            # 合并系统配置和用户配置
            merged_config = {**config, **self.ccxt_config}
            
            if self.ccxt_config['async_mode']:
                # 异步模式（Linux）
                exchange_class = getattr(ccxt, exchange_id)
            else:
                # 同步模式（Windows）
                exchange_class = getattr(ccxt, exchange_id)
                
            exchange = exchange_class(merged_config)
            self.exchanges[exchange_id] = exchange
            return exchange
            
        except Exception as e:
            print(f"创建交易所{exchange_id}实例失败: {str(e)}")
            return None
    
    def get_exchange(self, exchange_id: str) -> Optional[Any]:
        """获取已创建的交易所实例"""
        return self.exchanges.get(exchange_id)
    
    def initialize_markets(self, exchange_id: str) -> bool:
        """
        初始化交易所市场数据
        :return: 是否成功
        """
        try:
            exchange = self.exchanges.get(exchange_id)
            if not exchange:
                return False
                
            if self.ccxt_config['async_mode']:
                # 异步模式需要在事件循环中运行
                import asyncio
                asyncio.get_event_loop().run_until_complete(exchange.load_markets())
            else:
                # 同步模式直接调用
                exchange.load_markets()
            return True
            
        except Exception as e:
            print(f"初始化{exchange_id}市场数据失败: {str(e)}")
            return False
    
    async def close_all_async(self):
        """关闭所有异步交易所连接"""
        if self.ccxt_config['async_mode']:
            for exchange in self.exchanges.values():
                try:
                    await exchange.close()
                except:
                    pass
    
    def close_all(self):
        """关闭所有交易所连接"""
        if self.ccxt_config['async_mode']:
            import asyncio
            asyncio.get_event_loop().run_until_complete(self.close_all_async())
        self.exchanges.clear() 