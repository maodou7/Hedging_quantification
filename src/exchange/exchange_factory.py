"""
交易所工厂模块
"""
import logging
from typing import Dict, Optional
from src.config.exchange import EXCHANGE_CONFIGS
from .exchange_instance import ExchangeInstance

logger = logging.getLogger(__name__)

class ExchangeFactory:
    """交易所工厂类"""
    
    _instances: Dict[str, ExchangeInstance] = {}
    
    @classmethod
    def create_exchange(cls, exchange_id: str) -> Optional[ExchangeInstance]:
        """创建交易所实例"""
        if exchange_id not in EXCHANGE_CONFIGS:
            logger.error(f"未知的交易所ID: {exchange_id}")
            return None
            
        if exchange_id not in cls._instances:
            try:
                cls._instances[exchange_id] = ExchangeInstance(exchange_id)
                logger.info(f"成功创建交易所实例: {exchange_id}")
            except Exception as e:
                logger.error(f"创建交易所实例失败: {exchange_id}, 错误: {e}")
                return None
                
        return cls._instances[exchange_id]
        
    @classmethod
    def get_exchange(cls, exchange_id: str) -> Optional[ExchangeInstance]:
        """获取交易所实例"""
        return cls._instances.get(exchange_id)
        
    @classmethod
    def remove_exchange(cls, exchange_id: str):
        """移除交易所实例"""
        if exchange_id in cls._instances:
            try:
                cls._instances[exchange_id].disconnect()
                del cls._instances[exchange_id]
                logger.info(f"成功移除交易所实例: {exchange_id}")
            except Exception as e:
                logger.error(f"移除交易所实例失败: {exchange_id}, 错误: {e}")
                
    @classmethod
    def get_all_exchanges(cls) -> Dict[str, ExchangeInstance]:
        """获取所有交易所实例"""
        return cls._instances
        
    @classmethod
    def close_all(cls):
        """关闭所有交易所连接"""
        for exchange_id in list(cls._instances.keys()):
            cls.remove_exchange(exchange_id)
        logger.info("已关闭所有交易所连接") 