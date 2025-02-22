"""
交易所数据监控主程序

此模块实现了一个高性能的异步交易所数据监控系统。该系统能够同时监控多个交易所的市场数据，
并通过异步IO和并发处理来实现最大性能。

主要功能：
- 多交易所并发监控
- 自动错误恢复和重连机制
- 无限制的性能优化
- 实时数据处理和状态更新
- 自动系统识别和优化
  * Linux: 使用uvloop实现最高性能
  * Windows: 使用原生事件循环

依赖项：
- asyncio: 用于异步IO操作
- concurrent.futures: 用于线程池管理
- Config.exchange_config: 交易所配置信息
- ExchangeModules: 交易所接口实现
- uvloop (Linux): 用于提供更高性能的事件循环
- fastapi: 用于提供Web API接口

使用方法：
1. 确保已正确配置 Config/exchange_config.py 中的交易所参数
2. 直接运行此文件即可启动监控系统和API服务器
3. 使用 Ctrl+C 可以安全地停止程序

示例：
    python main.py

注意事项：
- 运行前请确保网络连接稳定
- 建议在高性能服务器上运行以获得最佳性能
- 程序会自动处理断线重连，无需手动干预
- Linux系统下会自动使用uvloop优化性能
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import sys
import os
from dotenv import load_dotenv
import uvicorn
from src.api.api_server import app
from src.api.monitor.monitor_api import set_monitor_manager, update_price
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

from Config.exchange_config import (
    EXCHANGES, EXCHANGE_CONFIGS, MARKET_TYPES, 
    QUOTE_CURRENCIES, MARKET_STRUCTURE_CONFIG
)

from ExchangeModules import ExchangeInstance, MonitorManager
from ExchangeModules.market_processor import MarketProcessor

async def process_price_updates(exchange_id: str, monitor_manager: MonitorManager):
    """处理价格更新的异步任务"""
    try:
        while True:
            try:
                tickers = await monitor_manager.fetch_exchange_tickers(exchange_id)
                if tickers:
                    for symbol, ticker in tickers.items():
                        if isinstance(ticker, dict) and 'last' in ticker:
                            price = ticker['last']
                            await update_price(symbol, exchange_id, price)
            except Exception as e:
                if not hasattr(process_price_updates, f'error_logged_{exchange_id}'):
                    logger.error(f"❌ 处理价格更新出错 ({exchange_id}): {str(e)}")
                    setattr(process_price_updates, f'error_logged_{exchange_id}', True)
            await asyncio.sleep(1)
    except Exception as e:
        if not hasattr(process_price_updates, f'conn_error_logged_{exchange_id}'):
            logger.error(f"❌ 价格订阅连接出错 ({exchange_id}): {str(e)}")
            setattr(process_price_updates, f'conn_error_logged_{exchange_id}', True)
        await asyncio.sleep(5)
        return

async def main():
    """主程序入口函数"""
    try:
        print("\n🚀 正在启动量化交易系统...")
        
        # 初始化系统组件
        exchange_instance = ExchangeInstance()
        market_processor = MarketProcessor(exchange_instance)
        
        # 初始化交易所配置
        exchange_configs = {}
        for exchange_id in EXCHANGES:
            exchange_configs[exchange_id] = {
                **EXCHANGE_CONFIGS.get(exchange_id, {}),
                'market_types': MARKET_TYPES,
                'quote_currencies': QUOTE_CURRENCIES
            }
        
        # 创建监控管理器
        monitor_manager = MonitorManager(exchange_instance, exchange_configs)
        set_monitor_manager(monitor_manager)
        
        # 初始化所有交易所连接
        await monitor_manager.initialize(EXCHANGES)
        
        # 创建价格订阅任务，包含自动重连机制
        async def run_price_subscription(exchange_id):
            error_count = 0
            while True:
                try:
                    await process_price_updates(exchange_id, monitor_manager)
                    error_count = 0
                except Exception as e:
                    error_count += 1
                    if error_count >= 5:
                        logger.error(f"❌ {exchange_id} 价格订阅任务异常，已重试{error_count}次")
                        error_count = 0
                await asyncio.sleep(5)
        
        # 创建价格更新任务
        price_tasks = [
            asyncio.create_task(run_price_subscription(exchange_id))
            for exchange_id in EXCHANGES
        ]
        
        print("✅ 系统初始化完成")
        
        # 启动FastAPI服务器和价格更新任务
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info"
        )
        server = uvicorn.Server(config)
        server_task = asyncio.create_task(server.serve())
        
        # 等待所有任务完成
        all_tasks = price_tasks + [server_task]
        await asyncio.gather(*all_tasks)
        
    except Exception as e:
        print(f"\n❌ 系统运行出错: {str(e)}")
        if 'monitor_manager' in locals():
            await monitor_manager.stop()
        if 'exchange_instance' in locals():
            await exchange_instance.close()
        for task in all_tasks:
            if not task.done():
                task.cancel()
        raise

if __name__ == "__main__":
    # 在Windows系统上使用SelectorEventLoop
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        # 运行主程序
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 正在关闭系统...")
    finally:
        print("✅ 系统已安全关闭")
