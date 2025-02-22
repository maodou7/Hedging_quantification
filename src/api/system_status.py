from fastapi import APIRouter, WebSocket
from typing import Dict, List
import psutil
import asyncio
from datetime import datetime

router = APIRouter(prefix="/system", tags=["system"])

# 全局变量用于存储WebSocket连接
active_connections: List[WebSocket] = []

class SystemStatus:
    def __init__(self):
        self.api_service_running = True
        self.websocket_connected = False
        self.data_monitoring_active = True

    def get_status(self) -> Dict:
        return {
            "api_service_running": self.api_service_running,
            "websocket_connected": self.websocket_connected,
            "data_monitoring_active": self.data_monitoring_active
        }

system_status = SystemStatus()

@router.get("/status")
async def get_system_status():
    """获取系统状态"""
    return system_status.get_status()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    system_status.websocket_connected = True
    
    try:
        while True:
            # 每秒发送一次系统状态
            status_data = system_status.get_status()
            await websocket.send_json(status_data)
            await asyncio.sleep(1)
    except:
        active_connections.remove(websocket)
        if not active_connections:
            system_status.websocket_connected = False

@router.get("/metrics")
async def get_system_metrics():
    """获取系统指标"""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "timestamp": datetime.now().isoformat()
    } 