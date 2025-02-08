"""
预测模型模块

负责:
1. 模型预测
2. 模型管理
3. 预测结果处理
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from src.utils.logger import ArbitrageLogger
from src.core.exchange_config import get_ml_config
from src.ml.feature_engineering import FeatureEngineering
from src.ml.model_trainer import ModelTrainer

class PredictionModel:
    def __init__(self):
        self.logger = ArbitrageLogger()
        self.config = get_ml_config()['prediction']
        self.feature_engineering = FeatureEngineering()
        self.model_trainer = ModelTrainer()
        self.active_models = {}
        
    def train_new_model(self, data: pd.DataFrame, model_type: Optional[str] = None,
                       feature_config: Optional[Dict[str, Any]] = None) -> str:
        """训练新模型"""
        try:
            if not self.config['enabled']:
                self.logger.warning("预测功能已禁用")
                return ""
                
            if model_type is None:
                model_type = self.config['config']['default_model']
                
            # 创建特征
            features = self.feature_engineering.create_features(data)
            if features.empty:
                self.logger.error("特征创建失败")
                return ""
                
            # 创建目标变量
            target = self.feature_engineering.create_target(
                data,
                horizon=self.config['config']['prediction_horizon'],
                method=self.config['config']['target_method']
            )
            if target.empty:
                self.logger.error("目标变量创建失败")
                return ""
                
            # 特征选择
            if self.config['feature_selection']['enabled']:
                features = self.feature_engineering.select_features(
                    features,
                    target
                )
                
            # 创建序列数据
            X, y = self.feature_engineering.create_sequences(
                features,
                target,
                sequence_length=self.config['config']['sequence_length']
            )
            if len(X) == 0 or len(y) == 0:
                self.logger.error("序列数据创建失败")
                return ""
                
            # 训练模型
            model_id, metrics, history = self.model_trainer.train_model(X, y, model_type)
            if not model_id:
                self.logger.error("模型训练失败")
                return ""
                
            # 保存模型信息
            self.active_models[model_id] = {
                'type': model_type,
                'features': features.columns.tolist(),
                'metrics': metrics,
                'history': history,
                'created_at': datetime.now().isoformat()
            }
            
            # 自动保存
            if self.config['auto_save']['enabled']:
                self.model_trainer.save_model(model_id)
                
            # 清理旧模型
            self._cleanup_old_models()
            
            return model_id
            
        except Exception as e:
            self.logger.error(f"训练新模型时发生错误: {str(e)}")
            return ""
            
    def predict(self, model_id: str, data: pd.DataFrame) -> np.ndarray:
        """使用模型进行预测"""
        try:
            if not self.config['enabled']:
                self.logger.warning("预测功能已禁用")
                return np.array([])
                
            if model_id not in self.active_models:
                self.logger.error(f"模型ID不存在: {model_id}")
                return np.array([])
                
            # 创建特征
            features = self.feature_engineering.create_features(data)
            if features.empty:
                self.logger.error("特征创建失败")
                return np.array([])
                
            # 特征选择
            if self.config['feature_selection']['enabled']:
                features = features[self.active_models[model_id]['features']]
                
            # 创建序列数据
            X = np.array([features.values[-self.config['config']['sequence_length']:]])
            
            # 预测
            predictions = self.model_trainer.predict(model_id, X)
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"预测时发生错误: {str(e)}")
            return np.array([])
            
    def evaluate_model(self, model_id: str, test_data: pd.DataFrame) -> Dict[str, float]:
        """评估模型"""
        try:
            if not self.config['enabled']:
                self.logger.warning("预测功能已禁用")
                return {}
                
            if model_id not in self.active_models:
                self.logger.error(f"模型ID不存在: {model_id}")
                return {}
                
            # 创建特征和目标变量
            features = self.feature_engineering.create_features(test_data)
            target = self.feature_engineering.create_target(
                test_data,
                horizon=self.config['config']['prediction_horizon'],
                method=self.config['config']['target_method']
            )
            
            if features.empty or target.empty:
                self.logger.error("特征或目标变量创建失败")
                return {}
                
            # 特征选择
            if self.config['feature_selection']['enabled']:
                features = features[self.active_models[model_id]['features']]
                
            # 创建序列数据
            X, y = self.feature_engineering.create_sequences(
                features,
                target,
                sequence_length=self.config['config']['sequence_length']
            )
            
            if len(X) == 0 or len(y) == 0:
                self.logger.error("序列数据创建失败")
                return {}
                
            # 评估模型
            metrics = self.model_trainer._evaluate_model(
                self.model_trainer.models[model_id],
                X,
                y,
                self.active_models[model_id]['type']
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"评估模型时发生错误: {str(e)}")
            return {}
            
    def get_model_info(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """获取模型信息"""
        try:
            if not self.config['enabled']:
                self.logger.warning("预测功能已禁用")
                return {}
                
            if model_id is None:
                return self.active_models
                
            if model_id not in self.active_models:
                self.logger.error(f"模型ID不存在: {model_id}")
                return {}
                
            return self.active_models[model_id]
            
        except Exception as e:
            self.logger.error(f"获取模型信息时发生错误: {str(e)}")
            return {}
            
    def save_model(self, model_id: str) -> bool:
        """保存模型"""
        try:
            if not self.config['enabled']:
                self.logger.warning("预测功能已禁用")
                return False
                
            if model_id not in self.active_models:
                self.logger.error(f"模型ID不存在: {model_id}")
                return False
                
            return self.model_trainer.save_model(model_id)
            
        except Exception as e:
            self.logger.error(f"保存模型时发生错误: {str(e)}")
            return False
            
    def load_model(self, model_id: str) -> bool:
        """加载模型"""
        try:
            if not self.config['enabled']:
                self.logger.warning("预测功能已禁用")
                return False
                
            success = self.model_trainer.load_model(model_id)
            if success:
                model_info = {
                    'type': model_id.split('_')[0],
                    'loaded_at': datetime.now().isoformat()
                }
                self.active_models[model_id] = model_info
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"加载模型时发生错误: {str(e)}")
            return False
            
    def delete_model(self, model_id: str) -> bool:
        """删除模型"""
        try:
            if not self.config['enabled']:
                self.logger.warning("预测功能已禁用")
                return False
                
            if model_id not in self.active_models:
                self.logger.error(f"模型ID不存在: {model_id}")
                return False
                
            # 从模型训练器中删除
            success = self.model_trainer.delete_model(model_id)
            if success:
                # 从活动模型中删除
                del self.active_models[model_id]
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"删除模型时发生错误: {str(e)}")
            return False
            
    def get_feature_importance(self, model_id: str) -> Dict[str, float]:
        """获取特征重要性"""
        try:
            if not self.config['enabled']:
                self.logger.warning("预测功能已禁用")
                return {}
                
            if model_id not in self.active_models:
                self.logger.error(f"模型ID不存在: {model_id}")
                return {}
                
            if not self.config['feature_importance']['enabled']:
                self.logger.warning("特征重要性分析已禁用")
                return {}
                
            feature_names = self.active_models[model_id]['features']
            importance = self.model_trainer.get_feature_importance(model_id, feature_names)
            
            # 获取前N个重要特征
            n = self.config['feature_importance']['top_n']
            sorted_importance = dict(sorted(importance.items(), 
                                         key=lambda x: x[1], 
                                         reverse=True)[:n])
            
            return sorted_importance
            
        except Exception as e:
            self.logger.error(f"获取特征重要性时发生错误: {str(e)}")
            return {}
            
    def _cleanup_old_models(self):
        """清理旧模型"""
        try:
            if not self.config['auto_save']['cleanup_enabled']:
                return
                
            max_models = self.config['auto_save']['max_models']
            if len(self.active_models) <= max_models:
                return
                
            # 按创建时间排序
            sorted_models = sorted(
                self.active_models.items(),
                key=lambda x: x[1]['created_at']
            )
            
            # 删除最旧的模型
            for model_id, _ in sorted_models[:-max_models]:
                self.delete_model(model_id)
                
        except Exception as e:
            self.logger.error(f"清理旧模型时发生错误: {str(e)}") 