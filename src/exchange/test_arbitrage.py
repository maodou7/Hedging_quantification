"""
套利系统测试脚本
测试套利系统的核心功能，包括：
1. 市场数据监控
2. 套利机会识别
3. 价差分析
4. 交易模拟
"""

import time
import sys
import os
from datetime import datetime
from typing import Dict, List
from .connection_manager import ConnectionManager
from ..Config.exchange_config import (
    EXCHANGES, SYMBOLS, COMMON_SYMBOLS,
    ARBITRAGE_CONFIG, RISK_CONFIG
)

class ArbitrageTest:
    """套利测试类"""
    
    def __init__(self):
        """初始化测试环境"""
        self.manager = ConnectionManager()
        self.price_data = {}  # 价格数据缓存
        self.opportunities = []  # 套利机会记录
        
    def initialize(self) -> bool:
        """初始化连接"""
        print("\n=== 初始化交易所连接 ===")
        results = self.manager.initialize_all()
        
        success = all(results.values())
        if success:
            print("所有交易所连接初始化成功")
        else:
            print("部分交易所连接失败:")
            for exchange_id, result in results.items():
                print(f"  {exchange_id}: {'成功' if result else '失败'}")
        
        return success
    
    def get_market_prices(self, symbol: str) -> Dict[str, Dict]:
        """获取所有交易所的市场价格"""
        prices = {}
        for exchange_id in EXCHANGES:
            connection = self.manager.get_connection(exchange_id)
            if not connection or not connection.initialized:
                continue
                
            try:
                ticker = connection.exchange.fetch_ticker(symbol)
                order_book = connection.exchange.fetch_order_book(symbol)
                
                prices[exchange_id] = {
                    'bid': order_book['bids'][0][0] if order_book['bids'] else None,
                    'ask': order_book['asks'][0][0] if order_book['asks'] else None,
                    'last': ticker.get('last'),
                    'volume': ticker.get('baseVolume'),
                    'timestamp': ticker.get('timestamp')
                }
            except Exception as e:
                print(f"获取{exchange_id} {symbol}价格失败: {str(e)}")
        
        return prices
    
    def analyze_opportunities(self, prices: Dict[str, Dict]) -> List[Dict]:
        """分析套利机会"""
        opportunities = []
        exchanges = list(prices.keys())
        
        for i in range(len(exchanges)):
            for j in range(i + 1, len(exchanges)):
                ex1, ex2 = exchanges[i], exchanges[j]
                
                if not prices[ex1].get('bid') or not prices[ex2].get('ask'):
                    continue
                
                # 计算价差
                spread = prices[ex1]['bid'] - prices[ex2]['ask']
                spread_percent = spread / prices[ex2]['ask'] * 100
                
                # 检查是否满足最小利润要求
                if spread_percent >= ARBITRAGE_CONFIG['min_profit_percent']:
                    opportunities.append({
                        'buy_exchange': ex2,
                        'sell_exchange': ex1,
                        'buy_price': prices[ex2]['ask'],
                        'sell_price': prices[ex1]['bid'],
                        'spread': spread,
                        'spread_percent': spread_percent,
                        'timestamp': datetime.now().isoformat()
                    })
        
        return opportunities
    
    def simulate_trade(self, opportunity: Dict) -> Dict:
        """模拟交易执行"""
        # 计算交易量（使用配置中的最小交易量）
        amount = RISK_CONFIG['max_order_amount'].get(
            'BTC/USDT', 0.01  # 默认使用0.01BTC作为测试量
        )
        
        # 计算预期收益
        profit = opportunity['spread'] * amount
        
        # 模拟交易结果
        return {
            'timestamp': datetime.now().isoformat(),
            'buy_exchange': opportunity['buy_exchange'],
            'sell_exchange': opportunity['sell_exchange'],
            'symbol': 'BTC/USDT',
            'amount': amount,
            'buy_price': opportunity['buy_price'],
            'sell_price': opportunity['sell_price'],
            'profit': profit,
            'profit_percent': opportunity['spread_percent'],
            'status': 'simulated'
        }
    
    def run_test(self, duration: int = 300, interval: int = 1):
        """
        运行测试
        :param duration: 测试持续时间（秒）
        :param interval: 检查间隔（秒）
        """
        if not self.initialize():
            print("初始化失败，测试终止")
            return
        
        print(f"\n开始套利测试，持续时间: {duration}秒，检查间隔: {interval}秒")
        start_time = time.time()
        trades = []
        total_opportunities = 0
        
        try:
            while time.time() - start_time < duration:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n当前时间: {current_time}")
                
                # 测试现货市场
                for symbol in SYMBOLS:
                    print(f"\n检查 {symbol} 市场...")
                    
                    # 获取市场价格
                    prices = self.get_market_prices(symbol)
                    if not prices:
                        continue
                    
                    # 打印当前价格
                    print("\n当前市场价格:")
                    for exchange_id, price_info in prices.items():
                        print(f"{exchange_id}:")
                        print(f"  买一价: {price_info['bid']}")
                        print(f"  卖一价: {price_info['ask']}")
                        print(f"  成交量: {price_info['volume']}")
                    
                    # 分析套利机会
                    opportunities = self.analyze_opportunities(prices)
                    total_opportunities += len(opportunities)
                    
                    # 打印套利机会
                    if opportunities:
                        print("\n发现套利机会:")
                        for opp in opportunities:
                            print(f"\n{opp['buy_exchange']} -> {opp['sell_exchange']}:")
                            print(f"  买入价: {opp['buy_price']}")
                            print(f"  卖出价: {opp['sell_price']}")
                            print(f"  价差: {opp['spread']:.2f}")
                            print(f"  价差百分比: {opp['spread_percent']:.4f}%")
                            
                            # 模拟交易
                            trade = self.simulate_trade(opp)
                            trades.append(trade)
                            
                            print("\n模拟交易结果:")
                            print(f"  交易量: {trade['amount']} BTC")
                            print(f"  预期收益: {trade['profit']:.8f} USDT")
                            print(f"  收益率: {trade['profit_percent']:.4f}%")
                    else:
                        print("\n未发现套利机会")
                
                print(f"\n等待 {interval} 秒后进行下一轮检查...")
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n用户中断测试")
        except Exception as e:
            print(f"\n测试过程中发生错误: {str(e)}")
        finally:
            # 打印测试总结
            print("\n=== 测试总结 ===")
            total_time = time.time() - start_time
            print(f"测试持续时间: {total_time:.2f} 秒")
            print(f"检查次数: {int(total_time / interval)}")
            print(f"发现套利机会: {total_opportunities} 次")
            print(f"模拟交易次数: {len(trades)} 次")
            
            if trades:
                total_profit = sum(t['profit'] for t in trades)
                avg_profit = total_profit / len(trades)
                print(f"总预期收益: {total_profit:.8f} USDT")
                print(f"平均每次收益: {avg_profit:.8f} USDT")
            
            # 关闭连接
            print("\n关闭所有连接...")
            self.manager.close_all()

if __name__ == "__main__":
    print("开始套利系统测试...")
    print("测试将持续5分钟，每秒检查一次市场价格")
    print("按Ctrl+C可以随时终止测试")
    
    tester = ArbitrageTest()
    tester.run_test(duration=300, interval=1) 