from asyncio import WindowsSelectorEventLoopPolicy, gather, run, set_event_loop_policy

from Environment.exchange_config import EXCHANGES, EXCHANGE_CONFIGS, MARKET_TYPES, QUOTE_CURRENCIES
from ExchangeModules import ExchangeInstance, MonitorManager


async def main():
    """主程序入口"""
    # 构建配置字典
    config = {
        'exchanges'       : EXCHANGES,
        'market_types'    : MARKET_TYPES,
        'quote_currencies': QUOTE_CURRENCIES,
        'type_configs'    : {
            market_type: {'type': config['type_configs'][market_type]['type']}
            for exchange_id, config in EXCHANGE_CONFIGS.items()
            for market_type in MARKET_TYPES
            if market_type in config['type_configs']
        }
    }

    # 创建实例
    exchange_instance = ExchangeInstance()
    monitor_manager = MonitorManager(exchange_instance, config)

    try:
        # 初始化交易所
        print("\n正在初始化交易所连接...")
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

    print("交易所价格监控程序启动...")
    print(f"监控的交易所: {', '.join(EXCHANGES)}")
    print(f"监控的计价币种: {', '.join(QUOTE_CURRENCIES)}")
    print("市场类型:")
    for market_type, enabled in MARKET_TYPES.items():
        print(f"  - {market_type}: {'启用' if enabled else '禁用'}")

    # 运行主程序
    run(main())
