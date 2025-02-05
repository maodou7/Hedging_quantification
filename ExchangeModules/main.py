from asyncio import WindowsSelectorEventLoopPolicy, gather, run, set_event_loop_policy

from .exchange_instance import ExchangeInstance
from .monitor_manager import MonitorManager


async def main(config: dict):
    """
    主程序入口
    
    Args:
        config: 配置信息
    """
    exchange_instance = ExchangeInstance()
    monitor_manager = MonitorManager(exchange_instance, config)

    try:
        # 初始化交易所
        await monitor_manager.initialize(config['exchanges'])

        # 开始监控
        monitor_manager.start_monitoring(config['exchanges'])

        # 创建监控任务
        monitoring_tasks = [
            monitor_manager.monitor_exchange(exchange_id)
            for exchange_id in config['exchanges']
        ]

        # 等待所有任务完成
        await gather(*monitoring_tasks)

    except KeyboardInterrupt:
        print("\n正在关闭连接...")
        await exchange_instance.close_all()
    except Exception as e:
        print(f"发生错误: {str(e)}")
        await exchange_instance.close_all()


if __name__ == "__main__":
    # 在Windows下设置事件循环策略
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    # 配置信息
    config = {
        'exchanges'       : ['binance', 'okx', 'bybit'],  # 示例交易所列表
        'market_types'    : {
            'spot'  : True,
            'swap'  : True,
            'future': False
        },
        'quote_currencies': ['USDT', 'USD', 'BUSD'],
        'type_configs'    : {
            'spot': {'type': 'spot'},
            'swap': {'type': 'swap'}
        }
    }

    # 运行主程序
    run(main(config))
