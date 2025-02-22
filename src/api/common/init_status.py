"""系统初始化状态监控模块

负责记录和返回系统启动过程中的各个阶段状态
"""

from typing import Dict, List
from datetime import datetime
from pydantic import BaseModel

class InitializationStatus(BaseModel):
    """系统初始化状态数据模型"""
    event_time: str
    event_type: str
    event_message: str
    event_details: Dict = {}

class InitStatusMonitor:
    """系统初始化状态监控器"""
    
    def __init__(self):
        self.init_events: List[InitializationStatus] = []
        self.current_stage = "未开始"
        
    def add_event(self, event_type: str, message: str, details: Dict = {}):
        """添加初始化事件
        
        Args:
            event_type: 事件类型
            message: 事件消息
            details: 事件详细信息
        """
        event = InitializationStatus(
            event_time=datetime.now().isoformat(),
            event_type=event_type,
            event_message=message,
            event_details=details
        )
        self.init_events.append(event)
        self.current_stage = message
        
    def get_init_status(self) -> List[InitializationStatus]:
        """获取所有初始化事件
        
        Returns:
            List[InitializationStatus]: 初始化事件列表
        """
        return self.init_events
    
    def get_current_stage(self) -> str:
        """获取当前初始化阶段
        
        Returns:
            str: 当前初始化阶段描述
        """
        return self.current_stage

# 创建全局实例
init_status_monitor = InitStatusMonitor()