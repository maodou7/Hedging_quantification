"""
交易所连接测试脚本
"""

import time
from datetime import datetime
from ExchangeModules.connection_manager import ConnectionManager
from Config.exchange_config import EXCHANGES, SYMBOLS, COMMON_SYMBOLS

def test_connections():
    """测试交易所连接"""
    
    # 创建连接管理器
    manager = ConnectionManager()
    test_duration = 300  # 测试持续时间（秒）
    check_interval = 10  # 检查间隔（秒）
    start_time = time.time()
    
    try:
        # 初始化所有交易所连接
        print("\n=== 测试交易所连接初始化 ===")
        results = manager.initialize_all()
        
        for exchange_id, success in results.items():
            print(f"{exchange_id}: {'成功' if success else '失败'}")
        
        print(f"\n开始持续测试，持续时间: {test_duration}秒")
        
        while time.time() - start_time < test_duration:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n当前时间: {current_time}")
            
            # 检查连接状态
            print("\n=== 测试连接状态 ===")
            status = manager.check_all_connections()
            
            for exchange_id, is_connected in status.items():
                print(f"{exchange_id}: {'连接正常' if is_connected else '连接异常'}")
            
            # 获取账户余额
            print("\n=== 测试获取账户余额 ===")
            balances = manager.get_all_balances()
            
            for exchange_id, balance in balances.items():
                if balance:
                    print(f"\n{exchange_id} 余额:")
                    # 只显示有余额的币种
                    for currency, amount in balance.get('total', {}).items():
                        if amount and float(amount) > 0:
                            print(f"  {currency}: {amount}")
                else:
                    print(f"{exchange_id}: 获取余额失败")
            
            # 测试现货市场
            print("\n=== 测试现货市场信息 ===")
            for symbol in COMMON_SYMBOLS['spot'][:3]:  # 测试前三个现货交易对
                print(f"\n{symbol} 市场信息:")
                market_info = manager.get_market_info(symbol)
                
                for exchange_id, info in market_info.items():
                    if info:
                        print(f"\n{exchange_id}:")
                        print(f"  最小交易量: {info.get('limits', {}).get('amount', {}).get('min', 'N/A')}")
                        print(f"  价格精度: {info.get('precision', {}).get('price', 'N/A')}")
                        print(f"  数量精度: {info.get('precision', {}).get('amount', 'N/A')}")
                        
                        # 获取实时行情
                        try:
                            ticker = manager.get_connection(exchange_id).exchange.fetch_ticker(symbol)
                            print(f"  最新价格: {ticker.get('last', 'N/A')}")
                            print(f"  24h成交量: {ticker.get('baseVolume', 'N/A')}")
                        except Exception as e:
                            print(f"  获取行情失败: {str(e)}")
                    else:
                        print(f"{exchange_id}: 获取市场信息失败")
            
            # 测试永续合约市场
            print("\n=== 测试永续合约市场信息 ===")
            for symbol in COMMON_SYMBOLS['swap'][:3]:  # 测试前三个永续合约
                print(f"\n{symbol} 市场信息:")
                market_info = manager.get_market_info(symbol)
                
                for exchange_id, info in market_info.items():
                    if info:
                        print(f"\n{exchange_id}:")
                        print(f"  合约类型: {info.get('type', 'N/A')}")
                        print(f"  最小交易量: {info.get('limits', {}).get('amount', {}).get('min', 'N/A')}")
                        print(f"  价格精度: {info.get('precision', {}).get('price', 'N/A')}")
                        
                        # 获取实时行情
                        try:
                            ticker = manager.get_connection(exchange_id).exchange.fetch_ticker(symbol)
                            print(f"  最新价格: {ticker.get('last', 'N/A')}")
                            print(f"  资金费率: {ticker.get('fundingRate', 'N/A')}")
                        except Exception as e:
                            print(f"  获取行情失败: {str(e)}")
                    else:
                        print(f"{exchange_id}: 获取市场信息失败")
            
            # 测试订单簿深度
            print("\n=== 测试订单簿深度 ===")
            test_symbol = SYMBOLS[0]  # 使用第一个交易对测试
            print(f"\n{test_symbol} 订单簿信息:")
            
            for exchange_id in EXCHANGES:
                connection = manager.get_connection(exchange_id)
                if connection and connection.initialized:
                    try:
                        order_book = connection.exchange.fetch_order_book(test_symbol)
                        print(f"\n{exchange_id}:")
                        print(f"  买单数量: {len(order_book['bids'])}")
                        print(f"  卖单数量: {len(order_book['asks'])}")
                        if order_book['bids']:
                            print(f"  最高买价: {order_book['bids'][0][0]}")
                        if order_book['asks']:
                            print(f"  最低卖价: {order_book['asks'][0][0]}")
                    except Exception as e:
                        print(f"  获取订单簿失败: {str(e)}")
            
            print(f"\n等待 {check_interval} 秒后进行下一轮测试...")
            time.sleep(check_interval)
    
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
    
    finally:
        # 关闭所有连接
        print("\n=== 关闭所有连接 ===")
        manager.close_all()
        
        # 打印测试总结
        end_time = time.time()
        total_time = end_time - start_time
        print(f"\n测试总结:")
        print(f"总测试时间: {total_time:.2f} 秒")
        print(f"测试轮次: {int(total_time / check_interval)}")

if __name__ == "__main__":
    print("开始交易所连接测试...")
    print("测试将持续5分钟，每10秒检查一次所有交易所的连接状态")
    print("按Ctrl+C可以随时终止测试")
    test_connections() 