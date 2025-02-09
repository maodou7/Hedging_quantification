"""
CCXT功能测试脚本
测试交易所连接和基本功能
"""

import sys
import logging
from src.exchange.connection_manager import ConnectionManager
from src.Config.exchange_config import EXCHANGES, COMMON_SYMBOLS

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_exchange_connection():
    """测试交易所连接"""
    connection_manager = ConnectionManager()
    
    # 测试初始化所有交易所
    logger.info("开始测试交易所连接初始化...")
    results = connection_manager.initialize_all()
    for exchange_id, success in results.items():
        logger.info(f"交易所 {exchange_id} 初始化结果: {'成功' if success else '失败'}")
    
    # 测试连接状态
    logger.info("\n检查所有交易所连接状态...")
    connection_status = connection_manager.check_all_connections()
    for exchange_id, status in connection_status.items():
        logger.info(f"交易所 {exchange_id} 连接状态: {'正常' if status else '异常'}")
    
    # 测试市场数据获取
    logger.info("\n测试市场数据获取...")
    for symbol in COMMON_SYMBOLS[:2]:  # 只测试前两个交易对
        logger.info(f"\n获取 {symbol} 的市场信息:")
        market_info = connection_manager.get_market_info(symbol)
        for exchange_id, info in market_info.items():
            if info:
                logger.info(f"{exchange_id}: {info}")
            else:
                logger.warning(f"{exchange_id}: 未能获取市场信息")
    
    # 关闭所有连接
    connection_manager.close_all()

if __name__ == "__main__":
    try:
        test_exchange_connection()
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        sys.exit(1) 