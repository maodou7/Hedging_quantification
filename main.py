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
- Environment.exchange_config: 交易所配置信息
- ExchangeModules: 交易所接口实现
- uvloop (Linux): 用于提供更高性能的事件循环

使用方法：
1. 确保已正确配置 Environment/exchange_config.py 中的交易所参数
2. 直接运行此文件即可启动监控系统
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

from Environment.exchange_config import (
    EXCHANGES, EXCHANGE_CONFIGS, MARKET_TYPES, 
    QUOTE_CURRENCIES, MARKET_STRUCTURE_CONFIG
)
from ExchangeModules import ExchangeInstance, MonitorManager, CommonSymbolsFinder
from ExchangeModules.market_structure_fetcher import MarketStructureFetcher
from ExchangeModules.market_processor import MarketProcessor


async def process_exchange_data(exchange_id: str, monitor_manager: MonitorManager, queue: asyncio.Queue):
    """
    处理单个交易所的数据监控任务

    此函数在独立的异步任务中运行，负责监控单个交易所的数据。
    它会持续运行并在发生错误时自动尝试重连。

    参数：
        exchange_id (str): 交易所标识符，必须与配置文件中的定义匹配
        monitor_manager (MonitorManager): 监控管理器实例，负责具体的监控实现
        queue (asyncio.Queue): 异步队列，用于报告处理状态和错误

    异常处理：
        - 捕获所有异常并通过队列报告
        - 在发生错误时等待1秒后自动重试
        - 持续运行直到程序终止

    返回：
        无返回值，函数持续运行直到程序终止
    """
    while True:
        try:
            await monitor_manager.monitor_exchange(exchange_id)
            await queue.put((exchange_id, True))
        except Exception as e:
            print(f"交易所 {exchange_id} 处理出错: {str(e)}")
            await queue.put((exchange_id, False))
            await asyncio.sleep(1)  # 错误后短暂延迟


async def main():
    """
    主程序入口函数

    此函数实现了整个监控系统的核心逻辑，包括：
    1. 配置系统参数和性能优化
    2. 初始化交易所连接
    3. 启动监控任务
    4. 管理错误处理和恢复机制

    配置说明：
        - 使用 ThreadPoolExecutor 实现最大并发
        - 通过 TaskGroup 管理多个异步任务
        - 使用队列进行任务状态管理

    异常处理：
        - 优雅处理键盘中断（Ctrl+C）
        - 自动关闭所有交易所连接
        - 捕获并记录所有异常

    返回：
        无返回值
    """
    # 设置更大的并发限制
    asyncio.get_event_loop().set_default_executor(ThreadPoolExecutor(max_workers=None))
    
    # 构建配置字典
    config = {
        'exchanges': EXCHANGES,
        'market_types': MARKET_TYPES,
        'quote_currencies': QUOTE_CURRENCIES,
        'type_configs': {
            market_type: {'type': config['type_configs'][market_type]['type']}
            for exchange_id, config in EXCHANGE_CONFIGS.items()
            for market_type in MARKET_TYPES
            if market_type in config['type_configs']
        }
    }

    # 创建实例
    exchange_instance = ExchangeInstance()
    monitor_manager = MonitorManager(exchange_instance, config)
    queue = asyncio.Queue()

    try:
        # 初始化交易所
        print("\n正在初始化交易所连接...")
        await monitor_manager.initialize(config['exchanges'])

        # 查找共同交易对
        print("\n正在查找共同交易对...")
        market_processor = MarketProcessor(exchange_instance)  # 传入exchange_instance参数
        symbol_finder = CommonSymbolsFinder(exchange_instance, market_processor, config)
        symbol_finder.find_common_symbols(config['exchanges'])
        
        # 获取共同交易对列表
        common_symbols_by_type = {}
        enabled_market_types = market_processor.get_enabled_market_types(config['market_types'])
        for market_type in enabled_market_types:
            symbols = []
            for quote in config['quote_currencies']:
                symbols.extend(list(symbol_finder.common_symbols[market_type][quote]))
            if symbols:  # 只添加非空的市场类型
                common_symbols_by_type[market_type] = symbols
        
        # 获取市场结构
        print("\n正在获取市场结构...")
        market_structure_fetcher = MarketStructureFetcher(
            exchange_instance,
            output_dir=MARKET_STRUCTURE_CONFIG['output_dir']
        )
        market_structure_fetcher.set_common_symbols(common_symbols_by_type)
        market_structure_fetcher.fetch_and_save_market_structures(
            config['exchanges'],
            include_comments=MARKET_STRUCTURE_CONFIG['include_comments']
        )

        # 开始监控
        monitor_manager.start_monitoring(config['exchanges'])

        # 创建所有监控任务
        tasks = []
        
        # 为每个交易所创建独立的监控任务
        for exchange_id in config['exchanges']:
            task = asyncio.create_task(process_exchange_data(exchange_id, monitor_manager, queue))
            tasks.append(task)

        # 创建结果处理任务
        async def process_results():
            """
            内部异步函数：处理监控结果

            持续从队列中获取监控结果并进行处理：
            - 成功：静默处理
            - 失败：打印重连信息
            """
            while True:
                exchange_id, success = await queue.get()
                if not success:
                    print(f"交易所 {exchange_id} 需要重新连接")
                queue.task_done()

        tasks.append(asyncio.create_task(process_results()))

        # 等待所有任务完成
        await asyncio.gather(*tasks)

    except KeyboardInterrupt:
        print("\n正在关闭连接...")
        await exchange_instance.close_all()
    except Exception as e:
        print(f"发生错误: {str(e)}")
        await exchange_instance.close_all()


def setup_event_loop():
    """
    设置事件循环
    
    根据运行的操作系统自动选择最优的事件循环实现：
    - Linux: 使用uvloop获得最佳性能
    - Windows: 使用WindowsSelectorEventLoopPolicy
    - 其他系统: 使用默认事件循环
    
    注意：
        在Linux系统下，需要先安装uvloop包：
        pip install uvloop
    """
    if sys.platform == 'linux':
        try:
            import uvloop
            uvloop.install()
            print("已启用 uvloop 以获得最佳性能")
        except ImportError:
            print("警告: 未安装 uvloop，建议安装以获得更好的性能")
            print("可以使用以下命令安装: pip install uvloop")
    elif sys.platform == 'win32':
        # 仅在Windows系统下导入Windows特定的策略
        from asyncio import WindowsSelectorEventLoopPolicy, set_event_loop_policy
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
        print("已启用 Windows 事件循环策略")
    else:
        print("使用默认事件循环策略")


if __name__ == "__main__":
    # 设置事件循环
    setup_event_loop()

    print("交易所价格监控程序启动...")
    print(f"监控的交易所: {', '.join(EXCHANGES)}")
    print(f"监控的计价币种: {', '.join(QUOTE_CURRENCIES)}")
    print("市场类型:")
    for market_type, enabled in MARKET_TYPES.items():
        print(f"  - {market_type}: {'启用' if enabled else '禁用'}")
        
    print("\n市场结构保存配置:")
    print(f"  - 保存目录: {MARKET_STRUCTURE_CONFIG['output_dir']}")
    print(f"  - 包含中文注释: {'是' if MARKET_STRUCTURE_CONFIG['include_comments'] else '否'}")
    print(f"  - JSON缩进空格数: {MARKET_STRUCTURE_CONFIG['indent']}")
    print(f"  - 允许中文字符: {'是' if not MARKET_STRUCTURE_CONFIG['ensure_ascii'] else '否'}")
    print()

    # 运行主程序
    asyncio.run(main())
