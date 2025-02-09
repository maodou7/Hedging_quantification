"""
价格预测器模块
"""
import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
from sklearn.preprocessing import MinMaxScaler
from src.config.exchange import INDICATOR_CONFIG

logger = logging.getLogger(__name__)

class LSTM(nn.Module):
    """LSTM模型"""
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, output_size: int, dropout: float = 0.2):
        super(LSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout
        )
        
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        # 初始化隐藏状态
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        # LSTM前向传播
        out, _ = self.lstm(x, (h0, c0))
        
        # 只取最后一个时间步的输出
        out = self.fc(out[:, -1, :])
        return out

class PricePredictor:
    """价格预测器类"""
    
    def __init__(self, config: dict = None):
        """初始化价格预测器"""
        self.config = config or INDICATOR_CONFIG
        self.model = None
        self.scaler = MinMaxScaler()
        self.sequence_length = self.config.get("sequence_length", 60)
        self.prediction_length = self.config.get("prediction_length", 10)
        self.features = self.config.get("features", ["close", "volume", "rsi", "macd"])
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    def prepare_data(self, data: pd.DataFrame) -> Tuple[torch.Tensor, torch.Tensor]:
        """准备训练数据"""
        try:
            # 确保数据包含所需特征
            missing_features = [f for f in self.features if f not in data.columns]
            if missing_features:
                raise ValueError(f"数据缺少以下特征: {missing_features}")
                
            # 选择特征并标准化
            feature_data = data[self.features].values
            scaled_data = self.scaler.fit_transform(feature_data)
            
            # 创建序列
            X, y = [], []
            for i in range(len(scaled_data) - self.sequence_length - self.prediction_length + 1):
                X.append(scaled_data[i:(i + self.sequence_length)])
                y.append(scaled_data[i + self.sequence_length:i + self.sequence_length + self.prediction_length, 0])
                
            # 转换为PyTorch张量
            X = torch.FloatTensor(np.array(X)).to(self.device)
            y = torch.FloatTensor(np.array(y)).to(self.device)
            
            return X, y
            
        except Exception as e:
            logger.error(f"准备训练数据失败: {e}")
            raise
            
    def build_model(self):
        """构建LSTM模型"""
        try:
            self.model = LSTM(
                input_size=len(self.features),
                hidden_size=50,
                num_layers=2,
                output_size=self.prediction_length,
                dropout=0.2
            ).to(self.device)
            
            self.optimizer = torch.optim.Adam(self.model.parameters())
            self.criterion = nn.MSELoss()
            
            logger.info("成功构建LSTM模型")
            
        except Exception as e:
            logger.error(f"构建LSTM模型失败: {e}")
            raise
            
    def train(self, data: pd.DataFrame, epochs: int = 100, batch_size: int = 32, validation_split: float = 0.2):
        """训练模型"""
        try:
            # 准备数据
            X, y = self.prepare_data(data)
            
            # 构建模型
            if self.model is None:
                self.build_model()
                
            # 分割训练集和验证集
            train_size = int(len(X) * (1 - validation_split))
            X_train, X_val = X[:train_size], X[train_size:]
            y_train, y_val = y[:train_size], y[train_size:]
            
            # 训练模型
            self.model.train()
            for epoch in range(epochs):
                # 批量训练
                for i in range(0, len(X_train), batch_size):
                    batch_X = X_train[i:i+batch_size]
                    batch_y = y_train[i:i+batch_size]
                    
                    # 前向传播
                    self.optimizer.zero_grad()
                    outputs = self.model(batch_X)
                    loss = self.criterion(outputs, batch_y)
                    
                    # 反向传播
                    loss.backward()
                    self.optimizer.step()
                
                # 验证
                if epoch % 10 == 0:
                    self.model.eval()
                    with torch.no_grad():
                        val_outputs = self.model(X_val)
                        val_loss = self.criterion(val_outputs, y_val)
                        logger.info(f"Epoch [{epoch}/{epochs}], Loss: {loss.item():.4f}, Val Loss: {val_loss.item():.4f}")
                    self.model.train()
            
            logger.info("模型训练完成")
            
        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            raise
            
    def predict(self, data: pd.DataFrame) -> Optional[np.ndarray]:
        """预测未来价格"""
        try:
            if self.model is None:
                raise ValueError("模型尚未训练")
                
            self.model.eval()
            with torch.no_grad():
                # 准备预测数据
                feature_data = data[self.features].values[-self.sequence_length:]
                scaled_data = self.scaler.transform(feature_data)
                X = torch.FloatTensor(scaled_data).unsqueeze(0).to(self.device)
                
                # 预测
                scaled_prediction = self.model(X).cpu().numpy()
                
                # 反标准化
                prediction = self.scaler.inverse_transform(
                    np.concatenate([scaled_prediction, np.zeros((self.prediction_length, len(self.features)-1))], axis=1)
                )[:, 0]
                
                logger.debug(f"预测结果: {prediction}")
                return prediction
            
        except Exception as e:
            logger.error(f"预测失败: {e}")
            return None
            
    def evaluate(self, test_data: pd.DataFrame) -> Dict[str, float]:
        """评估模型性能"""
        try:
            if self.model is None:
                raise ValueError("模型尚未训练")
                
            self.model.eval()
            with torch.no_grad():
                # 准备测试数据
                X_test, y_test = self.prepare_data(test_data)
                
                # 评估模型
                outputs = self.model(X_test)
                loss = self.criterion(outputs, y_test)
                mae = torch.mean(torch.abs(outputs - y_test))
                
                metrics = {
                    "loss": loss.item(),
                    "mae": mae.item()
                }
                
                logger.info(f"模型评估结果: {metrics}")
                return metrics
            
        except Exception as e:
            logger.error(f"模型评估失败: {e}")
            raise
            
    def save_model(self, path: str):
        """保存模型"""
        try:
            if self.model is None:
                raise ValueError("模型尚未训练")
                
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'scaler': self.scaler
            }, path)
            
            logger.info(f"模型已保存到: {path}")
            
        except Exception as e:
            logger.error(f"保存模型失败: {e}")
            raise
            
    def load_model(self, path: str):
        """加载模型"""
        try:
            if self.model is None:
                self.build_model()
                
            checkpoint = torch.load(path)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.scaler = checkpoint['scaler']
            
            logger.info(f"成功加载模型: {path}")
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            raise 