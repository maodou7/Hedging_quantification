"""
模型训练模块

负责:
1. 模型训练
2. 模型评估
3. 模型预测
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
from src.core.exchange_config import get_ml_config
import os
import uuid

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
        self.config = get_ml_config()['model_training']
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
