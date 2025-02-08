"""
测试运行脚本
"""

from ExchangeModules.test_arbitrage import ArbitrageTest

def main():
    print("开始套利系统测试...")
    print("测试将持续5分钟，每秒检查一次市场价格")
    print("按Ctrl+C可以随时终止测试")
    
    tester = ArbitrageTest()
    tester.run_test(duration=300, interval=1)

if __name__ == "__main__":
    main() 