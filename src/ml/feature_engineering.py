"""
特征工程模块

负责:
1. 数据预处理
2. 特征提取
3. 特征选择
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Union
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from src.indicators.technical_indicators import TechnicalIndicators
from src.utils.logger import ArbitrageLogger
from src.core.exchange_config import get_ml_config

class FeatureEngineering:
    def __init__(self):
        self.logger = ArbitrageLogger()
        self.indicators = TechnicalIndicators()
        self.config = get_ml_config()['feature_engineering']
        
        # 根据配置初始化标准化器
        if self.config['config']['normalization']['method'] == 'standard':
            self.scaler = StandardScaler()
        else:
            self.scaler = MinMaxScaler()
            
        if self.config['config']['normalization']['price_method'] == 'standard':
            self.price_scaler = StandardScaler()
        else:
            self.price_scaler = MinMaxScaler()
        
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建特征"""
        try:
            if not self.config['enabled']:
                self.logger.warning("特征工程功能已禁用")
                return pd.DataFrame(index=df.index)
                
            features = pd.DataFrame(index=df.index)
            
            # 价格特征
            if self.config['config']['price_features_enabled']:
                features['price_normalized'] = self.price_scaler.fit_transform(df[['close']])
                features['returns'] = df['close'].pct_change()
                features['log_returns'] = np.log1p(features['returns'])
            
            # 波动率特征
            if self.config['config']['volatility_features_enabled']:
                window = self.config['config']['volatility_window']
                features['volatility'] = features['returns'].rolling(window=window).std()
                features['high_low_ratio'] = df['high'] / df['low']
            
            # 成交量特征
            if self.config['config']['volume_features_enabled']:
                features['volume_normalized'] = self.price_scaler.fit_transform(df[['volume']])
                features['volume_ma'] = df['volume'].rolling(window=20).mean()
                features['volume_std'] = df['volume'].rolling(window=20).std()
            
            # 技术指标特征
            if self.config['config']['technical_features_enabled']:
                window_sizes = self.config['config']['window_sizes']
                for window in window_sizes:
                    # 移动平均线
                    if 'sma' in self.config['config']['ma_types']:
                        features[f'sma_{window}'] = self.indicators.sma(df['close'], window)
                    if 'ema' in self.config['config']['ma_types']:
                        features[f'ema_{window}'] = self.indicators.ema(df['close'], window)
                    
                    # 相对位置
                    if 'sma' in self.config['config']['ma_types']:
                        features[f'price_sma_ratio_{window}'] = df['close'] / features[f'sma_{window}']
                    if 'ema' in self.config['config']['ma_types']:
                        features[f'price_ema_ratio_{window}'] = df['close'] / features[f'ema_{window}']
                
                # RSI
                features['rsi'] = self.indicators.rsi(df['close'])
                
                # MACD
                macd_data = self.indicators.macd(df['close'])
                features['macd'] = macd_data['macd']
                features['macd_signal'] = macd_data['signal']
                features['macd_hist'] = macd_data['histogram']
                
                # 布林带
                bb_data = self.indicators.bollinger_bands(df['close'])
                features['bb_upper'] = bb_data['upper']
                features['bb_middle'] = bb_data['middle']
                features['bb_lower'] = bb_data['lower']
                features['bb_width'] = (bb_data['upper'] - bb_data['lower']) / bb_data['middle']
                
                # KDJ
                kdj_data = self.indicators.kdj(df['high'], df['low'], df['close'])
                features['kdj_k'] = kdj_data['k']
                features['kdj_d'] = kdj_data['d']
                features['kdj_j'] = kdj_data['j']
                
                # ATR
                features['atr'] = self.indicators.atr(df['high'], df['low'], df['close'])
                
                # OBV
                features['obv'] = self.indicators.obv(df['close'], df['volume'])
                
                # 价格动量
                features['momentum'] = self.indicators.momentum(df['close'])
                
                # CCI
                features['cci'] = self.indicators.cci(df['high'], df['low'], df['close'])
                
                # 威廉指标
                features['williams_r'] = self.indicators.williams_r(df['high'], df['low'], df['close'])
            
            # 时间特征
            if self.config['config']['time_features_enabled']:
                features['hour'] = df.index.hour
                features['day_of_week'] = df.index.dayofweek
            
            # 删除包含NaN的行
            features = features.dropna()
            
            # 标准化特征
            numeric_columns = features.select_dtypes(include=[np.number]).columns
            features[numeric_columns] = self.scaler.fit_transform(features[numeric_columns])
            
            return features
            
        except Exception as e:
            self.logger.error(f"创建特征时发生错误: {str(e)}")
            return pd.DataFrame()
            
    def select_features(self, features: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
        """特征选择"""
        try:
            if not self.config['selection']['enabled']:
                return features
                
            method = self.config['selection']['method']
            threshold = self.config['selection']['threshold']
            
            if method == 'correlation':
                # 计算与目标变量的相关性
                correlations = features.corrwith(target).abs()
                selected_features = features[correlations[correlations > threshold].index]
                
            elif method == 'variance':
                # 计算方差
                variances = features.var()
                selected_features = features[variances[variances > threshold].index]
                
            else:
                self.logger.warning(f"未知的特征选择方法: {method}")
                return features
                
            return selected_features
            
        except Exception as e:
            self.logger.error(f"特征选择时发生错误: {str(e)}")
            return features
            
    def create_sequences(self, features: pd.DataFrame, target: pd.Series, 
                        sequence_length: Optional[int] = None) -> tuple:
        """创建序列数据"""
        try:
            if sequence_length is None:
                sequence_length = self.config['config'].get('sequence_length', 10)
                
            X, y = [], []
            
            for i in range(len(features) - sequence_length):
                X.append(features.iloc[i:(i + sequence_length)].values)
                y.append(target.iloc[i + sequence_length])
                
            return np.array(X), np.array(y)
            
        except Exception as e:
            self.logger.error(f"创建序列数据时发生错误: {str(e)}")
            return np.array([]), np.array([])
            
    def create_target(self, df: pd.DataFrame, horizon: Optional[int] = None, 
                     method: Optional[str] = None) -> pd.Series:
        """创建目标变量"""
        try:
            if horizon is None:
                horizon = self.config['config'].get('horizon', 1)
            if method is None:
                method = self.config['config'].get('target_method', 'returns')
                
            if method == 'returns':
                # 计算未来收益率
                target = df['close'].pct_change(horizon).shift(-horizon)
                
            elif method == 'direction':
                # 计算未来价格方向
                future_returns = df['close'].pct_change(horizon).shift(-horizon)
                target = (future_returns > 0).astype(int)
                
            elif method == 'volatility':
                # 计算未来波动率
                future_returns = df['close'].pct_change(horizon).shift(-horizon)
                target = future_returns.rolling(window=horizon).std().shift(-horizon)
                
            else:
                self.logger.warning(f"未知的目标变量方法: {method}")
                return pd.Series()
                
            return target.dropna()
            
        except Exception as e:
            self.logger.error(f"创建目标变量时发生错误: {str(e)}")
            return pd.Series()
            
    def add_market_features(self, features: pd.DataFrame, market_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """添加市场特征"""
        try:
            if not self.config['config']['market_features_enabled']:
                return features
                
            window = self.config['config']['correlation_window']
            
            # 添加市场指数
            for market_name, market_df in market_data.items():
                # 计算市场收益率
                market_returns = market_df['close'].pct_change()
                features[f'{market_name}_returns'] = market_returns
                
                # 计算相关性
                rolling_corr = features['returns'].rolling(window=window).corr(market_returns)
                features[f'{market_name}_correlation'] = rolling_corr
                
                # 计算Beta
                market_variance = market_returns.rolling(window=window).var()
                covariance = features['returns'].rolling(window=window).cov(market_returns)
                features[f'{market_name}_beta'] = covariance / market_variance
                
            return features
            
        except Exception as e:
            self.logger.error(f"添加市场特征时发生错误: {str(e)}")
            return features
            
    def add_sentiment_features(self, features: pd.DataFrame, sentiment_data: pd.Series) -> pd.DataFrame:
        """添加情感特征"""
        try:
            if not self.config['config']['sentiment_features_enabled']:
                return features
                
            features['sentiment_score'] = sentiment_data
            features['sentiment_ma'] = sentiment_data.rolling(window=20).mean()
            features['sentiment_std'] = sentiment_data.rolling(window=20).std()
            
            return features
            
        except Exception as e:
            self.logger.error(f"添加情感特征时发生错误: {str(e)}")
            return features 