"""
配置热重载模块
用于在运行时动态重新加载配置
"""
import os
import sys
import time
import logging
import threading
import importlib
from typing import Dict, Set, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

logger = logging.getLogger(__name__)

class ConfigReloadError(Exception):
    """配置重载错误异常"""
    pass

class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变更处理器"""
    
    def __init__(self, reload_manager: 'ConfigReloadManager'):
        self.manager = reload_manager
        self.last_reload_time: Dict[str, float] = {}
        self.min_reload_interval = 1.0  # 最小重载间隔（秒）
    
    def on_modified(self, event):
        if not isinstance(event, FileModifiedEvent):
            return
            
        file_path = event.src_path
        if not file_path.endswith('.py'):
            return
            
        # 检查是否是配置文件
        file_name = os.path.basename(file_path)
        module_name = os.path.splitext(file_name)[0]
        if not self.manager.is_config_module(module_name):
            return
            
        # 检查重载间隔
        current_time = time.time()
        last_time = self.last_reload_time.get(file_path, 0)
        if current_time - last_time < self.min_reload_interval:
            return
            
        self.last_reload_time[file_path] = current_time
        
        try:
            self.manager.reload_config(module_name)
        except Exception as e:
            logger.error(f"重载配置文件失败 {file_path}: {e}")

class ConfigReloadManager:
    """配置重载管理器"""
    
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.config_modules: Set[str] = set()
        self.callbacks: Dict[str, Set[Callable]] = {}
        self.observer: Optional[Observer] = None
        self._lock = threading.Lock()
    
    def register_config(self, module_name: str):
        """注册需要监控的配置模块"""
        with self._lock:
            self.config_modules.add(module_name)
    
    def register_callback(self, module_name: str, callback: Callable):
        """注册配置变更回调函数"""
        with self._lock:
            if module_name not in self.callbacks:
                self.callbacks[module_name] = set()
            self.callbacks[module_name].add(callback)
    
    def unregister_callback(self, module_name: str, callback: Callable):
        """取消注册配置变更回调函数"""
        with self._lock:
            if module_name in self.callbacks:
                self.callbacks[module_name].discard(callback)
    
    def is_config_module(self, module_name: str) -> bool:
        """检查是否是已注册的配置模块"""
        return module_name in self.config_modules
    
    def start(self):
        """启动配置文件监控"""
        if self.observer is not None:
            return
            
        try:
            self.observer = Observer()
            handler = ConfigFileHandler(self)
            self.observer.schedule(handler, self.config_dir, recursive=False)
            self.observer.start()
            logger.info("配置文件监控已启动")
        except Exception as e:
            logger.error(f"启动配置文件监控失败: {e}")
            raise ConfigReloadError(f"启动配置文件监控失败: {e}")
    
    def stop(self):
        """停止配置文件监控"""
        if self.observer is None:
            return
            
        try:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("配置文件监控已停止")
        except Exception as e:
            logger.error(f"停止配置文件监控失败: {e}")
    
    def reload_config(self, module_name: str):
        """重新加载指定的配置模块"""
        with self._lock:
            try:
                # 获取模块完整路径
                module_path = f"src.config.{module_name}"
                
                # 重新加载模块
                if module_path in sys.modules:
                    module = sys.modules[module_path]
                    importlib.reload(module)
                    logger.info(f"已重新加载配置模块: {module_name}")
                    
                    # 调用回调函数
                    if module_name in self.callbacks:
                        for callback in self.callbacks[module_name]:
                            try:
                                callback()
                            except Exception as e:
                                logger.error(f"执行配置变更回调失败: {e}")
                
            except Exception as e:
                logger.error(f"重载配置模块失败 {module_name}: {e}")
                raise ConfigReloadError(f"重载配置模块失败 {module_name}: {e}")
    
    def reload_all(self):
        """重新加载所有配置模块"""
        with self._lock:
            for module_name in self.config_modules:
                try:
                    self.reload_config(module_name)
                except Exception as e:
                    logger.error(f"重载配置模块失败 {module_name}: {e}")

# 创建重载管理器实例
config_reload = ConfigReloadManager(config_dir="src/config")

# 注册配置模块
config_reload.register_config("trading")
config_reload.register_config("risk")
config_reload.register_config("monitoring")
config_reload.register_config("database")
config_reload.register_config("notification")

# 示例：注册回调函数
def on_trading_config_changed():
    """交易配置变更处理"""
    logger.info("交易配置已更新，重新初始化交易策略...")

def on_risk_config_changed():
    """风险配置变更处理"""
    logger.info("风险配置已更新，重新计算风险限额...")

config_reload.register_callback("trading", on_trading_config_changed)
config_reload.register_callback("risk", on_risk_config_changed) 