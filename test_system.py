"""
系统功能测试脚本
测试所有主要功能，包括：
1. 数据预处理和特征工程
2. 模型训练（LSTM和XGBoost）
3. 模型评估
4. 模型预测
5. 模型保存和加载
"""

import numpy as np
import pandas as pd
import logging
import traceback
import os
import pickle
from datetime import datetime, timedelta
from src.ml.feature_engineering import FeatureEngineering
from src.ml.model_trainer import ModelTrainer
from src.utils.logger import ArbitrageLogger
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
import xgboost as xgb
import uuid
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_system.log', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 检查点路径
CHECKPOINT_DIR = "checkpoints"
FEATURE_CHECKPOINT = os.path.join(CHECKPOINT_DIR, "feature_data.pkl")
MODEL_CHECKPOINT = os.path.join(CHECKPOINT_DIR, "model_data.pkl")

class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

def ensure_checkpoint_dir():
    """确保检查点目录存在"""
    if not os.path.exists(CHECKPOINT_DIR):
        os.makedirs(CHECKPOINT_DIR)

def save_checkpoint(data, checkpoint_path):
    """保存检查点数据"""
    ensure_checkpoint_dir()
    with open(checkpoint_path, 'wb') as f:
        pickle.dump(data, f)

def load_checkpoint(checkpoint_path):
    """加载检查点数据"""
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'rb') as f:
            return pickle.load(f)
    return None

def generate_test_data(n_samples=1000):
    """生成测试数据"""
    try:
        # 生成时间索引
        dates = pd.date_range(start='2023-01-01', periods=n_samples, freq='H')
        
        # 生成价格数据
        np.random.seed(42)
        close = np.random.normal(100, 10, n_samples).cumsum()
        high = close + np.random.uniform(0, 2, n_samples)
        low = close - np.random.uniform(0, 2, n_samples)
        volume = np.random.uniform(1000, 5000, n_samples)
        
        # 创建DataFrame
        df = pd.DataFrame({
            'open': close,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }, index=dates)
        
        return df
        
    except Exception as e:
        logger.error(f"生成测试数据时发生错误: {str(e)}\n{traceback.format_exc()}")
        return pd.DataFrame()

def test_feature_engineering():
    """测试特征工程"""
    try:
        # 检查是否有已保存的特征数据
        checkpoint_data = load_checkpoint(FEATURE_CHECKPOINT)
        if checkpoint_data is not None:
            logger.info("从检查点加载特征数据...")
            return checkpoint_data['X'], checkpoint_data['y']
            
        logger.info("开始测试特征工程...")
        
        # 生成测试数据
        df = generate_test_data()
        if df.empty:
            logger.error("生成测试数据失败")
            return None, None
            
        logger.info(f"生成测试数据成功，形状: {df.shape}")
        
        # 创建特征工程实例
        fe = FeatureEngineering()
        
        # 创建特征
        logger.info("开始创建特征...")
        features = fe.create_features(df)
        if features.empty:
            logger.error("创建特征失败")
            return None, None
            
        logger.info(f"生成特征数量: {features.shape[1]}")
        logger.info(f"特征列表: {features.columns.tolist()}")
        
        # 创建目标变量
        logger.info("开始创建目标变量...")
        target = fe.create_target(df, horizon=24, method='returns')
        if len(target) == 0:
            logger.error("创建目标变量失败")
            return None, None
            
        logger.info(f"目标变量长度: {len(target)}")
        
        # 特征选择
        logger.info("开始特征选择...")
        selected_features = fe.select_features(features, target)
        if selected_features.empty:
            logger.error("特征选择失败")
            return None, None
            
        logger.info(f"选择的特征数量: {selected_features.shape[1]}")
        
        # 创建序列数据
        logger.info("开始创建序列数据...")
        X, y = fe.create_sequences(selected_features, target, sequence_length=10)
        if X is None or y is None:
            logger.error("创建序列数据失败")
            return None, None
            
        logger.info(f"序列数据形状: X={X.shape}, y={y.shape}")
        
        # 保存特征数据到检查点
        save_checkpoint({'X': X, 'y': y}, FEATURE_CHECKPOINT)
        
        return X, y
        
    except Exception as e:
        logger.error(f"特征工程测试失败: {str(e)}\n{traceback.format_exc()}")
        return None, None

def test_model_training(X, y):
    """测试模型训练"""
    try:
        logger.info("开始测试模型训练...")
        
        # 创建模型训练器
        trainer = ModelTrainer()
        
        # 数据分割
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        logger.info(f"数据分割完成: X_train={X_train.shape}, X_val={X_val.shape}")
        
        # 训练LSTM模型
        logger.info("训练LSTM模型...")
        try:
            lstm_model, lstm_history = trainer._train_lstm(X_train, y_train, X_val, y_val)
            if lstm_model is None:
                logger.error("LSTM模型训练失败")
                return False
                
            # 评估LSTM模型
            lstm_metrics = trainer._evaluate_model(lstm_model, X_val, y_val, 'lstm')
            logger.info(f"LSTM模型指标: {lstm_metrics}")
        except Exception as e:
            logger.error(f"LSTM模型训练失败: {str(e)}")
            return False
            
        # 训练XGBoost模型
        logger.info("训练XGBoost模型...")
        try:
            xgb_model, xgb_history = trainer._train_xgboost(X_train, y_train, X_val, y_val)
            if xgb_model is None:
                logger.error("XGBoost模型训练失败")
                return False
                
            # 评估XGBoost模型
            xgb_metrics = trainer._evaluate_model(xgb_model, X_val, y_val, 'xgboost')
            logger.info(f"XGBoost模型指标: {xgb_metrics}")
        except Exception as e:
            logger.error(f"XGBoost模型训练失败: {str(e)}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"模型训练测试失败: {str(e)}")
        return False

def test_model_save_load():
    """测试模型保存和加载功能"""
    try:
        logger.info("开始测试模型保存和加载功能...")
        
        # 创建一些示例数据
        X = np.random.randn(1000, 10, 33)  # (样本数, 序列长度, 特征数)
        y = np.random.randn(1000)  # 目标变量
        
        # 创建并训练模型
        trainer = ModelTrainer()
        model_id, metrics, history = trainer.train_model(X, y, model_type='lstm')
        
        if not model_id:
            logger.error("模型训练失败")
            return False
            
        # 保存模型
        logger.info("保存模型...")
        if not trainer.save_model(model_id):
            logger.error("模型保存失败")
            return False
            
        # 创建新的训练器实例
        new_trainer = ModelTrainer()
        
        # 加载模型
        logger.info("加载模型...")
        if not new_trainer.load_model(model_id):
            logger.error("模型加载失败")
            return False
            
        # 使用加载的模型进行预测
        logger.info("测试加载的模型...")
        predictions = new_trainer.predict(model_id, X[:5])
        if len(predictions) == 0:
            logger.error("模型预测失败")
            return False
            
        logger.info("模型保存和加载测试成功")
        return True
        
    except Exception as e:
        logger.error(f"模型保存和加载测试失败: {str(e)}")
        return False

def test_feature_importance():
    """测试特征重要性分析功能"""
    try:
        logger.info("开始测试特征重要性分析...")
        
        # 创建一些示例数据
        X = np.random.randn(1000, 10, 33)
        y = np.random.randn(1000)
        
        # 创建特征名称
        feature_names = [f'feature_{i}' for i in range(X.shape[2] * X.shape[1])]
        
        # 训练XGBoost模型
        trainer = ModelTrainer()
        model_id, metrics, history = trainer.train_model(X, y, model_type='xgboost')
        
        if not model_id:
            logger.error("模型训练失败")
            return False
            
        # 获取特征重要性
        importance = trainer.get_feature_importance(model_id, feature_names)
        if not importance:
            logger.error("获取特征重要性失败")
            return False
            
        # 显示前10个最重要的特征
        sorted_importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10])
        logger.info(f"前10个最重要的特征: {sorted_importance}")
        
        logger.info("特征重要性分析测试成功")
        return True
        
    except Exception as e:
        logger.error(f"特征重要性分析测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    try:
        logger.info("开始系统功能测试...")
        
        # 测试特征工程
        X, y = test_feature_engineering()
        if X is None or y is None:
            logger.error("特征工程测试失败，终止测试")
            return False
            
        # 测试模型训练
        success = test_model_training(X, y)
        if not success:
            logger.error("模型训练测试失败")
            return False
            
        # 测试模型保存和加载
        if not test_model_save_load():
            logger.error("模型保存和加载测试失败")
            return False
            
        # 测试特征重要性分析
        if not test_feature_importance():
            logger.error("特征重要性分析测试失败")
            return False
            
        logger.info("系统功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"系统测试过程中发生错误: {str(e)}\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    main() 