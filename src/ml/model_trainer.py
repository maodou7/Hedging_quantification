"""
模型训练模块

负责:
1. 模型训练
2. 模型评估
3. 模型预测
4. 实时更新
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import joblib
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import xgboost as xgb
from src.utils.logger import ArbitrageLogger
from src.config.exchange import FEATURE_FLAGS, INDICATOR_CONFIG
import os
import uuid
from collections import defaultdict
import threading
import time

class TimeSeriesDataset(Dataset):
    """时间序列数据集"""
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
        
    def __len__(self):
        return len(self.X)
        
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

class LSTMModel(nn.Module):
    """LSTM模型"""
    def __init__(self, input_size, hidden_size, num_layers=2, dropout=0.2):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                           batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        # x shape: (batch_size, seq_len, input_size)
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])  # 只使用最后一个时间步的输出
        return out

class ModelTrainer:
    def __init__(self, model_dir="models"):
        self.logger = ArbitrageLogger()
        self.config = {
            'enabled': FEATURE_FLAGS['machine_learning']['enabled'],
            'config': {
                'default_model': 'lstm',
                'test_size': 0.2
            },
            'lstm': {
                'enabled': FEATURE_FLAGS['machine_learning']['models']['lstm']['enabled'],
                'batch_size': FEATURE_FLAGS['machine_learning']['models']['lstm']['batch_size'],
                'epochs': FEATURE_FLAGS['machine_learning']['models']['lstm']['epochs'],
                'sequence_length': FEATURE_FLAGS['machine_learning']['models']['lstm']['sequence_length'],
                'units': INDICATOR_CONFIG['model_params']['hidden_size'],
                'dropout': INDICATOR_CONFIG['model_params']['dropout'],
                'learning_rate': INDICATOR_CONFIG['model_params']['learning_rate'],
                'early_stopping': {
                    'patience': 10
                },
                'checkpointing': {
                    'enabled': True,
                    'filepath': 'models/best_lstm.pth'
                }
            },
            'xgboost': {
                'enabled': FEATURE_FLAGS['machine_learning']['models']['xgboost']['enabled'],
                'objective': 'reg:squarederror',
                'max_depth': 6,
                'learning_rate': 0.1,
                'n_estimators': 100,
                'early_stopping_rounds': 10
            }
        }
        self.models = {}
        self.histories = {}
        self.metrics = {}
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_dir = model_dir
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
    def train_model(self, X: np.ndarray, y: np.ndarray, model_type: Optional[str] = None) -> Tuple[str, Dict[str, float], Dict[str, Any]]:
        """训练模型"""
        try:
            if not self.config['enabled']:
                self.logger.warning("模型训练功能已禁用")
                return "", {}, {}
                
            if model_type is None:
                model_type = self.config['config']['default_model']
                
            # 数据分割
            X_train, X_test, y_train, y_test = self._split_data(X, y)
            
            # 训练模型
            if model_type == 'lstm':
                model, history = self._train_lstm(X_train, y_train, X_test, y_test)
            elif model_type == 'xgboost':
                model, history = self._train_xgboost(X_train, y_train, X_test, y_test)
            else:
                self.logger.error(f"未知的模型类型: {model_type}")
                return "", {}, {}
                
            # 评估模型
            metrics = self._evaluate_model(model, X_test, y_test, model_type)
            
            # 生成模型ID
            model_id = f"{model_type}_{len(self.models)}"
            
            # 保存模型信息
            self.models[model_id] = model
            self.histories[model_id] = history
            self.metrics[model_id] = metrics
            
            return model_id, metrics, history
            
        except Exception as e:
            self.logger.error(f"训练模型时发生错误: {str(e)}")
            return "", {}, {}
            
    def _split_data(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """分割数据"""
        try:
            test_size = self.config['config']['test_size']
            split_index = int(len(X) * (1 - test_size))
            
            X_train = X[:split_index]
            X_test = X[split_index:]
            y_train = y[:split_index]
            y_test = y[split_index:]
            
            return X_train, X_test, y_train, y_test
            
        except Exception as e:
            self.logger.error(f"分割数据时发生错误: {str(e)}")
            return np.array([]), np.array([]), np.array([]), np.array([])
            
    def _train_lstm(self, X_train: np.ndarray, y_train: np.ndarray, 
                    X_test: np.ndarray, y_test: np.ndarray) -> Tuple[nn.Module, Dict[str, Any]]:
        """训练LSTM模型"""
        try:
            if not self.config['lstm']['enabled']:
                self.logger.warning("LSTM模型已禁用")
                return None, {}
                
            config = self.config['lstm']
            
            # 创建数据加载器
            train_dataset = TimeSeriesDataset(X_train, y_train)
            test_dataset = TimeSeriesDataset(X_test, y_test)
            train_loader = DataLoader(train_dataset, batch_size=config['batch_size'], shuffle=True)
            test_loader = DataLoader(test_dataset, batch_size=config['batch_size'])
            
            # 构建模型
            input_size = X_train.shape[2]  # 特征维度
            model = LSTMModel(
                input_size=input_size,
                hidden_size=config['units'],
                num_layers=2,
                dropout=config['dropout']
            ).to(self.device)
            
            # 定义损失函数和优化器
            criterion = nn.MSELoss()
            optimizer = optim.Adam(model.parameters(), lr=config['learning_rate'])
            
            # 训练历史
            history = {
                'train_loss': [],
                'val_loss': []
            }
            
            # 早停设置
            best_val_loss = float('inf')
            patience = config['early_stopping']['patience']
            patience_counter = 0
            
            # 训练循环
            for epoch in range(config['epochs']):
                # 训练阶段
                model.train()
                train_loss = 0
                for batch_X, batch_y in train_loader:
                    batch_X = batch_X.to(self.device)
                    batch_y = batch_y.to(self.device)
                    
                    optimizer.zero_grad()
                    outputs = model(batch_X)
                    loss = criterion(outputs, batch_y.view(-1, 1))
                    loss.backward()
                    optimizer.step()
                    
                    train_loss += loss.item()
                
                # 验证阶段
                model.eval()
                val_loss = 0
                with torch.no_grad():
                    for batch_X, batch_y in test_loader:
                        batch_X = batch_X.to(self.device)
                        batch_y = batch_y.to(self.device)
                        
                        outputs = model(batch_X)
                        loss = criterion(outputs, batch_y.view(-1, 1))
                        val_loss += loss.item()
                
                # 记录损失
                train_loss = train_loss / len(train_loader)
                val_loss = val_loss / len(test_loader)
                history['train_loss'].append(train_loss)
                history['val_loss'].append(val_loss)
                
                # 早停检查
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    # 保存最佳模型
                    if config['checkpointing']['enabled']:
                        torch.save(model.state_dict(), config['checkpointing']['filepath'])
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        print(f'Early stopping at epoch {epoch}')
                        break
                
                if epoch % 10 == 0:
                    print(f'Epoch {epoch}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}')
            
            # 如果启用了checkpointing，加载最佳模型
            if config['checkpointing']['enabled']:
                model.load_state_dict(torch.load(config['checkpointing']['filepath']))
            
            return model, history
            
        except Exception as e:
            self.logger.error(f"训练LSTM模型时发生错误: {str(e)}")
            return None, {}
            
    def _train_xgboost(self, X_train: np.ndarray, y_train: np.ndarray,
                       X_test: np.ndarray, y_test: np.ndarray) -> Tuple[xgb.Booster, Dict[str, Any]]:
        """训练XGBoost模型"""
        try:
            if not self.config['xgboost']['enabled']:
                self.logger.warning("XGBoost模型已禁用")
                return None, {}
                
            config = self.config['xgboost']
            
            # 重塑输入数据
            # 从(samples, sequence_length, features)转换为(samples, sequence_length * features)
            X_train_reshaped = X_train.reshape(X_train.shape[0], -1)
            X_test_reshaped = X_test.reshape(X_test.shape[0], -1)
            
            # 创建DMatrix
            dtrain = xgb.DMatrix(X_train_reshaped, label=y_train)
            dtest = xgb.DMatrix(X_test_reshaped, label=y_test)
            
            # 模型参数
            params = {
                'objective': config['objective'],
                'max_depth': config['max_depth'],
                'learning_rate': config['learning_rate'],
                'n_estimators': config['n_estimators'],
                'eval_metric': 'rmse'
            }
            
            # 训练参数
            num_boost_round = config['n_estimators']
            early_stopping_rounds = config['early_stopping_rounds']
            
            # 训练模型
            evals_result = {}
            model = xgb.train(
                params,
                dtrain,
                num_boost_round=num_boost_round,
                evals=[(dtest, 'validation')],
                early_stopping_rounds=early_stopping_rounds,
                evals_result=evals_result,
                verbose_eval=False
            )
            
            # 获取训练历史
            history = {
                'train_score': evals_result['validation']['rmse'],
                'test_score': evals_result['validation']['rmse']
            }
            
            return model, history
            
        except Exception as e:
            self.logger.error(f"训练XGBoost模型时发生错误: {str(e)}")
            return None, {}
            
    def _evaluate_model(self, model, X_test: np.ndarray, y_test: np.ndarray, model_type: str) -> Dict[str, float]:
        """评估模型性能"""
        try:
            if model_type == 'lstm':
                return self._evaluate_lstm(model, X_test, y_test)
            elif model_type == 'xgboost':
                return self._evaluate_xgboost(model, X_test, y_test)
            else:
                self.logger.error(f"未知的模型类型: {model_type}")
                return {}
        except Exception as e:
            self.logger.error(f"评估模型时发生错误: {str(e)}")
            return {}

    def _evaluate_lstm(self, model: nn.Module, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """评估LSTM模型"""
        try:
            model.eval()
            test_dataset = TimeSeriesDataset(X_test, y_test)
            test_loader = DataLoader(test_dataset, batch_size=32)
            
            predictions = []
            actuals = []
            
            with torch.no_grad():
                for batch_X, batch_y in test_loader:
                    batch_X = batch_X.to(self.device)
                    outputs = model(batch_X)
                    predictions.extend(outputs.cpu().numpy())
                    actuals.extend(batch_y.numpy())
            
            predictions = np.array(predictions).reshape(-1)
            actuals = np.array(actuals)
            
            return {
                'mse': mean_squared_error(actuals, predictions),
                'rmse': np.sqrt(mean_squared_error(actuals, predictions)),
                'mae': mean_absolute_error(actuals, predictions),
                'r2': r2_score(actuals, predictions)
            }
            
        except Exception as e:
            self.logger.error(f"评估LSTM模型时发生错误: {str(e)}")
            return {}

    def _evaluate_xgboost(self, model: xgb.Booster, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """评估XGBoost模型"""
        try:
            # 重塑输入数据
            X_test_reshaped = X_test.reshape(X_test.shape[0], -1)
            predictions = model.predict(xgb.DMatrix(X_test_reshaped))
            return {
                'mse': mean_squared_error(y_test, predictions),
                'rmse': np.sqrt(mean_squared_error(y_test, predictions)),
                'mae': mean_absolute_error(y_test, predictions),
                'r2': r2_score(y_test, predictions)
            }
            
        except Exception as e:
            self.logger.error(f"评估XGBoost模型时发生错误: {str(e)}")
            return {}

    def predict(self, model_id: str, X: np.ndarray) -> np.ndarray:
        """使用模型进行预测"""
        try:
            if model_id not in self.models:
                self.logger.error(f"模型ID不存在: {model_id}")
                return np.array([])
                
            model = self.models[model_id]
            model_type = model_id.split('_')[0]
            
            if model_type == 'lstm':
                return self._predict_lstm(model, X)
            elif model_type == 'xgboost':
                X_reshaped = X.reshape(X.shape[0], -1)
                return model.predict(xgb.DMatrix(X_reshaped))
            else:
                self.logger.error(f"未知的模型类型: {model_type}")
                return np.array([])
                
        except Exception as e:
            self.logger.error(f"预测时发生错误: {str(e)}")
            return np.array([])

    def _predict_lstm(self, model: nn.Module, X: np.ndarray) -> np.ndarray:
        """使用LSTM模型进行预测"""
        try:
            model.eval()
            X_tensor = torch.FloatTensor(X).to(self.device)
            
            with torch.no_grad():
                predictions = model(X_tensor)
                
            return predictions.cpu().numpy().reshape(-1)
            
        except Exception as e:
            self.logger.error(f"LSTM预测时发生错误: {str(e)}")
            return np.array([])

    def save_model(self, model_id: str) -> bool:
        """保存模型"""
        try:
            if model_id not in self.models:
                self.logger.error(f"模型ID不存在: {model_id}")
                return False
                
            model = self.models[model_id]
            model_type = model_id.split('_')[0]
            
            # 创建保存目录
            os.makedirs('models', exist_ok=True)
            
            # 保存模型
            if model_type == 'lstm':
                torch.save(model.state_dict(), f'models/{model_id}.pth')
            elif model_type == 'xgboost':
                model.save_model(f'models/{model_id}.json')
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存模型时发生错误: {str(e)}")
            return False

    def load_model(self, model_id: str) -> bool:
        """加载模型"""
        try:
            model_type = model_id.split('_')[0]
            model_path = f'models/{model_id}'
            
            if model_type == 'lstm':
                if not os.path.exists(f'{model_path}.pth'):
                    self.logger.error(f"模型文件不存在: {model_path}.pth")
                    return False
                    
                # 创建新的LSTM模型实例
                config = self.config['lstm']
                model = LSTMModel(
                    input_size=config['input_size'],
                    hidden_size=config['units'],
                    num_layers=2,
                    dropout=config['dropout']
                ).to(self.device)
                
                # 加载模型参数
                model.load_state_dict(torch.load(f'{model_path}.pth'))
                self.models[model_id] = model
                
            elif model_type == 'xgboost':
                if not os.path.exists(f'{model_path}.json'):
                    self.logger.error(f"模型文件不存在: {model_path}.json")
                    return False
                    
                model = xgb.Booster()
                model.load_model(f'{model_path}.json')
                self.models[model_id] = model
                
            return True
            
        except Exception as e:
            self.logger.error(f"加载模型时发生错误: {str(e)}")
            return False

    def delete_model(self, model_id: str) -> bool:
        """删除模型"""
        try:
            if model_id not in self.models:
                self.logger.error(f"模型ID不存在: {model_id}")
                return False
                
            # 从内存中删除
            del self.models[model_id]
            if model_id in self.histories:
                del self.histories[model_id]
            if model_id in self.metrics:
                del self.metrics[model_id]
                
            # 从文件系统中删除
            model_type = model_id.split('_')[0]
            if model_type == 'lstm':
                if os.path.exists(f'models/{model_id}.pth'):
                    os.remove(f'models/{model_id}.pth')
            elif model_type == 'xgboost':
                if os.path.exists(f'models/{model_id}.json'):
                    os.remove(f'models/{model_id}.json')
                    
            return True
            
        except Exception as e:
            self.logger.error(f"删除模型时发生错误: {str(e)}")
            return False

    def get_feature_importance(self, model_id: str, feature_names: List[str]) -> Dict[str, float]:
        """获取特征重要性（仅支持XGBoost模型）"""
        try:
            if model_id not in self.models:
                self.logger.error(f"模型ID不存在: {model_id}")
                return {}
                
            model = self.models[model_id]
            model_type = model_id.split('_')[0]
            
            if model_type != 'xgboost':
                self.logger.error("特征重要性分析仅支持XGBoost模型")
                return {}
                
            # 获取特征重要性分数
            importance_scores = model.get_score(importance_type='gain')
            
            # 将特征索引（f0, f1, ...）映射到实际特征名称
            importance = {}
            for feat, score in importance_scores.items():
                idx = int(feat.replace('f', ''))
                if idx < len(feature_names):
                    importance[feature_names[idx]] = score
            
            return importance
            
        except Exception as e:
            self.logger.error(f"获取特征重要性时发生错误: {str(e)}")
            return {}

class RealTimeModelTrainer:
    """实时模型训练器"""
    def __init__(self, model_dir="models", update_interval=3600):
        self.model_trainer = ModelTrainer(model_dir)
        self.price_data = defaultdict(lambda: defaultdict(list))  # {exchange: {symbol: [price_data]}}
        self.models = {}  # {symbol: model}
        self.update_interval = update_interval  # 更新间隔（秒）
        self.is_running = False
        self.lock = threading.Lock()
        self.logger = ArbitrageLogger()

    def start(self):
        """启动实时训练"""
        self.is_running = True
        self.training_thread = threading.Thread(target=self._training_loop)
        self.training_thread.start()
        self.logger.info("实时模型训练器已启动")

    def stop(self):
        """停止实时训练"""
        self.is_running = False
        if hasattr(self, 'training_thread'):
            self.training_thread.join()
        self.logger.info("实时模型训练器已停止")

    def add_price_data(self, exchange: str, symbol: str, price_data: Dict):
        """添加新的价格数据"""
        with self.lock:
            self.price_data[exchange][symbol].append({
                'price': float(price_data['price']),
                'volume': float(price_data['volume']),
                'timestamp': price_data['timestamp'],
                'bid': float(price_data.get('bid', 0)),
                'ask': float(price_data.get('ask', 0))
            })

    def get_prediction(self, exchange: str, symbol: str) -> Optional[float]:
        """获取价格预测"""
        try:
            with self.lock:
                if symbol not in self.models:
                    return None
                
                # 获取最近的价格数据
                recent_data = self.price_data[exchange][symbol][-60:]  # 使用最近60个数据点
                if len(recent_data) < 60:
                    return None

                # 准备特征
                features = self._prepare_features(recent_data)
                
                # 使用模型预测
                model = self.models[symbol]
                if isinstance(model, nn.Module):
                    model.eval()
                    with torch.no_grad():
                        features_tensor = torch.FloatTensor(features).unsqueeze(0)
                        prediction = model(features_tensor)
                        return prediction.item()
                elif isinstance(model, xgb.Booster):
                    features_matrix = xgb.DMatrix(features.reshape(1, -1))
                    return model.predict(features_matrix)[0]
                
                return None

        except Exception as e:
            self.logger.error(f"获取预测时发生错误: {str(e)}")
            return None

    def _training_loop(self):
        """训练循环"""
        while self.is_running:
            try:
                with self.lock:
                    # 对每个交易对进行训练
                    for exchange in self.price_data:
                        for symbol in self.price_data[exchange]:
                            if len(self.price_data[exchange][symbol]) >= 1000:  # 确保有足够的数据
                                self._train_symbol_model(exchange, symbol)
                
                # 等待下一次更新
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"训练循环中发生错误: {str(e)}")
                time.sleep(60)  # 发生错误时等待一分钟

    def _train_symbol_model(self, exchange: str, symbol: str):
        """训练特定交易对的模型"""
        try:
            # 准备训练数据
            data = self.price_data[exchange][symbol]
            if len(data) < 1000:
                return

            # 准备特征和标签
            X, y = self._prepare_training_data(data)
            
            # 训练模型
            model_id, metrics, history = self.model_trainer.train_model(X, y, model_type='lstm')
            
            if model_id:
                self.models[symbol] = self.model_trainer.models[model_id]
                self.logger.info(f"完成{symbol}的模型训练, 指标: {metrics}")
            
        except Exception as e:
            self.logger.error(f"训练{symbol}模型时发生错误: {str(e)}")

    def _prepare_features(self, price_data: List[Dict]) -> np.ndarray:
        """准备特征数据"""
        try:
            # 提取基本特征
            prices = np.array([d['price'] for d in price_data])
            volumes = np.array([d['volume'] for d in price_data])
            bids = np.array([d['bid'] for d in price_data])
            asks = np.array([d['ask'] for d in price_data])
            
            # 计算技术指标
            rsi = self._calculate_rsi(prices)
            macd = self._calculate_macd(prices)
            
            # 组合特征
            features = np.column_stack((prices, volumes, bids, asks, rsi, macd))
            return features
            
        except Exception as e:
            self.logger.error(f"准备特征时发生错误: {str(e)}")
            return np.array([])

    def _prepare_training_data(self, price_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """准备训练数据"""
        try:
            sequence_length = 60
            features = self._prepare_features(price_data)
            
            X, y = [], []
            for i in range(len(features) - sequence_length):
                X.append(features[i:i+sequence_length])
                y.append(features[i+sequence_length, 0])  # 使用下一个时间点的价格作为标签
                
            return np.array(X), np.array(y)
            
        except Exception as e:
            self.logger.error(f"准备训练数据时发生错误: {str(e)}")
            return np.array([]), np.array([])

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """计算RSI指标"""
        try:
            deltas = np.diff(prices)
            seed = deltas[:period+1]
            up = seed[seed >= 0].sum()/period
            down = -seed[seed < 0].sum()/period
            rs = up/down
            rsi = np.zeros_like(prices)
            rsi[:period] = 100. - 100./(1. + rs)

            for i in range(period, len(prices)):
                delta = deltas[i-1]
                if delta > 0:
                    upval = delta
                    downval = 0.
                else:
                    upval = 0.
                    downval = -delta

                up = (up*(period-1) + upval)/period
                down = (down*(period-1) + downval)/period
                rs = up/down
                rsi[i] = 100. - 100./(1. + rs)

            return rsi
            
        except Exception as e:
            self.logger.error(f"计算RSI时发生错误: {str(e)}")
            return np.zeros_like(prices)

    def _calculate_macd(self, prices: np.ndarray, 
                       fast_period: int = 12, 
                       slow_period: int = 26, 
                       signal_period: int = 9) -> np.ndarray:
        """计算MACD指标"""
        try:
            # 计算EMA
            ema_fast = np.zeros_like(prices)
            ema_slow = np.zeros_like(prices)
            multiplier_fast = 2 / (fast_period + 1)
            multiplier_slow = 2 / (slow_period + 1)
            
            # 初始值
            ema_fast[0] = prices[0]
            ema_slow[0] = prices[0]
            
            # 计算EMA
            for i in range(1, len(prices)):
                ema_fast[i] = (prices[i] - ema_fast[i-1]) * multiplier_fast + ema_fast[i-1]
                ema_slow[i] = (prices[i] - ema_slow[i-1]) * multiplier_slow + ema_slow[i-1]
            
            # 计算MACD线
            macd_line = ema_fast - ema_slow
            
            return macd_line
            
        except Exception as e:
            self.logger.error(f"计算MACD时发生错误: {str(e)}")
            return np.zeros_like(prices)
