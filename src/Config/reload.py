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
import traceback
from typing import Dict, Set, Optional, Callable

logger = logging.getLogger("arbitrage")

# 尝试导入 watchdog
WATCHDOG_AVAILABLE = False
try:
    import watchdog
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
    logger.info("成功导入 watchdog 模块")
except ImportError as e:
    logger.error(f"导入 watchdog 模块失败: {str(e)}")
    logger.error(f"Python 路径: {sys.executable}")
    logger.error(f"sys.path: {sys.path}")
    logger.error(f"堆栈跟踪: {traceback.format_exc()}")
    print(f"警告: watchdog 模块导入失败: {str(e)}")

class ConfigReloadError(Exception):
    """配置重载错误异常"""
    pass

class ConfigFileHandler(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    """配置文件变更处理器"""
    
    def __init__(self, manager: 'ConfigReloadManager'):
        if not WATCHDOG_AVAILABLE:
            logger.warning("watchdog 模块未安装，配置文件监控功能已禁用")
            return
        super().__init__()
        self.manager = manager
        self.last_reload_time: Dict[str, float] = {}
        self.min_reload_interval = 1.0  # 最小重载间隔（秒）
        logger.info("ConfigFileHandler 初始化成功")
    
    def on_modified(self, event):
        """文件修改事件处理"""
        if not WATCHDOG_AVAILABLE:
            return
            
        try:
            if not isinstance(event, FileModifiedEvent):
                return
                
            file_path = event.src_path
            file_name = os.path.basename(file_path)
            logger.debug(f"检测到文件变更: {file_path}")
            
            # 根据文件名判断配置类型
            config_type = None
            if "trading" in file_name:
                config_type = "trading"
            elif "risk" in file_name:
                config_type = "risk"
                
            if not config_type:
                return
                
            # 检查重载间隔
            current_time = time.time()
            last_time = self.last_reload_time.get(config_type, 0)
            if current_time - last_time < self.min_reload_interval:
                logger.debug(f"重载间隔过短，跳过: {config_type}")
                return
                
            self.last_reload_time[config_type] = current_time
            self.manager.handle_config_change(config_type)
            
        except Exception as e:
            logger.error(f"处理文件变更事件时发生错误: {str(e)}")
            logger.error(f"堆栈跟踪: {traceback.format_exc()}")

class ConfigReloadManager:
    """配置重载管理器"""
    
    def __init__(self):
        self._callbacks: Dict[str, Callable] = {}
        self._observer: Optional[Observer] = None
        self._handler: Optional['ConfigFileHandler'] = None
        logger.info("ConfigReloadManager 初始化成功")
        
    def register_callback(self, config_type: str, callback: Callable) -> None:
        """注册配置变更回调函数"""
        self._callbacks[config_type] = callback
        logger.info(f"注册配置回调: {config_type}")
        
    def start_monitoring(self, config_dir: str) -> None:
        """启动配置文件监控"""
        if not WATCHDOG_AVAILABLE:
            logger.warning("watchdog 模块未安装，配置文件监控功能已禁用")
            return
            
        if not os.path.exists(config_dir):
            logger.error(f"配置目录不存在: {config_dir}")
            return
            
        try:
            self._observer = Observer()
            self._handler = ConfigFileHandler(self)
            self._observer.schedule(self._handler, config_dir, recursive=False)
            self._observer.start()
            logger.info(f"配置文件监控已启动，监控目录: {config_dir}")
        except Exception as e:
            logger.error(f"启动配置文件监控失败: {str(e)}")
            logger.error(f"堆栈跟踪: {traceback.format_exc()}")
            
    def stop_monitoring(self) -> None:
        """停止配置文件监控"""
        if self._observer:
            try:
                self._observer.stop()
                self._observer.join()
                logger.info("配置文件监控已停止")
            except Exception as e:
                logger.error(f"停止配置文件监控失败: {str(e)}")
                logger.error(f"堆栈跟踪: {traceback.format_exc()}")
                
    def handle_config_change(self, config_type: str) -> None:
        """处理配置文件变更"""
        callback = self._callbacks.get(config_type)
        if callback:
            try:
                callback()
                logger.info(f"配置 {config_type} 已重新加载")
            except Exception as e:
                logger.error(f"重新加载配置 {config_type} 失败: {str(e)}")
                logger.error(f"堆栈跟踪: {traceback.format_exc()}")

def on_trading_config_changed():
    """交易配置变更处理"""
    from .exchange import update_common_symbols
    from src.utils.system_adapter import SystemAdapter
    
    system_adapter = SystemAdapter()
    try:
        loop = system_adapter.get_event_loop()
        loop.run_until_complete(update_common_symbols())
        logger.info("交易配置更新成功")
    except Exception as e:
        logger.error(f"更新交易配置失败: {str(e)}")
        logger.error(f"堆栈跟踪: {traceback.format_exc()}")
    finally:
        try:
            if loop and not loop.is_closed():
                loop.stop()
        except Exception as e:
            logger.error(f"停止事件循环失败: {str(e)}")

def on_risk_config_changed():
    """风控配置变更处理"""
    try:
        # 在这里添加风控配置重载逻辑
        logger.info("风控配置更新成功")
    except Exception as e:
        logger.error(f"更新风控配置失败: {str(e)}")
        logger.error(f"堆栈跟踪: {traceback.format_exc()}")

# 注册配置变更回调
config_reload = ConfigReloadManager()
config_reload.register_callback("trading", on_trading_config_changed)
config_reload.register_callback("risk", on_risk_config_changed)

def start_config_file_monitoring(config_dir: str, callback) -> None:
    """启动配置文件监控"""
    if not WATCHDOG_AVAILABLE:
        logger.warning("watchdog 模块未安装，配置文件监控功能已禁用")
        return
    
    try:
        observer = Observer()
        handler = ConfigFileHandler(callback)
        observer.schedule(handler, config_dir, recursive=False)
        observer.start()
        logger.info(f"配置文件监控已启动: {config_dir}")
    except Exception as e:
        logger.error(f"启动配置文件监控失败: {str(e)}")
        logger.error(f"堆栈跟踪: {traceback.format_exc()}") 