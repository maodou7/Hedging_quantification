"""
数据存储模块
负责管理和存储交易数据
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

class DataStore:
    """数据存储管理器"""
    
    def __init__(self):
        # 设置数据存储目录
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 创建子目录
        self.market_data_dir = os.path.join(self.data_dir, 'market_data')
        self.trades_dir = os.path.join(self.data_dir, 'trades')
        self.opportunities_dir = os.path.join(self.data_dir, 'opportunities')
        
        # 创建所需的目录
        for directory in [self.market_data_dir, self.trades_dir, self.opportunities_dir]:
            os.makedirs(directory, exist_ok=True)
            
        # 初始化价格缓存
        self.price_cache = {}

    def update_price(self, exchange_id: str, symbol: str, price_data: Dict[str, Any]):
        """更新价格数据"""
        if exchange_id not in self.price_cache:
            self.price_cache[exchange_id] = {}
        self.price_cache[exchange_id][symbol] = price_data
        
    def get_all_prices(self, symbol: str) -> Dict[str, Dict[str, Any]]:
        """获取所有交易所的价格数据"""
        result = {}
        for exchange_id, prices in self.price_cache.items():
            if symbol in prices:
                result[exchange_id] = prices[symbol]
        return result

    def _get_current_date(self) -> str:
        """获取当前日期字符串"""
        return datetime.now().strftime('%Y-%m-%d')
        
    def save_market_data(self, exchange: str, symbol: str, data: Dict[str, Any]):
        """保存市场数据"""
        current_date = self._get_current_date()
        filename = f"{exchange}_{symbol}_{current_date}.csv"
        filepath = os.path.join(self.market_data_dir, filename)
        
        # 添加时间戳
        data['timestamp'] = datetime.now().isoformat()
        
        # 将数据转换为DataFrame并保存
        df = pd.DataFrame([data])
        if os.path.exists(filepath):
            df.to_csv(filepath, mode='a', header=False, index=False)
        else:
            df.to_csv(filepath, index=False)
            
    def save_trade(self, trade_data: Dict[str, Any]):
        """保存交易记录"""
        current_date = self._get_current_date()
        filename = f"trades_{current_date}.json"
        filepath = os.path.join(self.trades_dir, filename)
        
        # 添加时间戳
        trade_data['timestamp'] = datetime.now().isoformat()
        
        # 保存为JSON格式
        trades = []
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                trades = json.load(f)
        
        trades.append(trade_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(trades, f, ensure_ascii=False, indent=2)
            
    def save_opportunity(self, opportunity_data: Dict[str, Any]):
        """保存套利机会记录"""
        current_date = self._get_current_date()
        filename = f"opportunities_{current_date}.json"
        filepath = os.path.join(self.opportunities_dir, filename)
        
        # 添加时间戳
        opportunity_data['timestamp'] = datetime.now().isoformat()
        
        # 保存为JSON格式
        opportunities = []
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                opportunities = json.load(f)
        
        opportunities.append(opportunity_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(opportunities, f, ensure_ascii=False, indent=2)
            
    def load_market_data(self, exchange: str, symbol: str,
                        start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """加载市场数据"""
        if start_date is None:
            start_date = self._get_current_date()
        if end_date is None:
            end_date = start_date
            
        dfs = []
        for date in pd.date_range(start_date, end_date):
            date_str = date.strftime('%Y-%m-%d')
            filename = f"{exchange}_{symbol}_{date_str}.csv"
            filepath = os.path.join(self.market_data_dir, filename)
            
            if os.path.exists(filepath):
                df = pd.read_csv(filepath)
                dfs.append(df)
                
        return pd.concat(dfs) if dfs else pd.DataFrame()
        
    def load_trades(self, date: str = None) -> List[Dict[str, Any]]:
        """加载交易记录"""
        if date is None:
            date = self._get_current_date()
            
        filename = f"trades_{date}.json"
        filepath = os.path.join(self.trades_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
        
    def load_opportunities(self, date: str = None) -> List[Dict[str, Any]]:
        """加载套利机会记录"""
        if date is None:
            date = self._get_current_date()
            
        filename = f"opportunities_{date}.json"
        filepath = os.path.join(self.opportunities_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return [] 