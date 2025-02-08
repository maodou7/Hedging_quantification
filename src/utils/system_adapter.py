"""
系统适配器模块
负责处理不同操作系统的兼容性问题
"""

import sys
import platform
import asyncio
from typing import Dict, Any

class SystemAdapter:
    """系统适配器类"""
    
    def __init__(self):
        """初始化系统适配器"""
        self.system_info = self._get_system_info()
        
    def _get_system_info(self) -> Dict[str, str]:
        """获取系统信息"""
        return {
            'system': platform.system(),
            'python_version': sys.version,
            'platform': platform.platform(),
            'machine': platform.machine()
        }
        
    def get_system_info(self) -> Dict[str, str]:
        """获取系统信息"""
        return self.system_info
        
    def setup_event_loop(self):
        """设置事件循环"""
        if sys.platform == 'win32':
            # Windows系统使用SelectorEventLoop
            loop = asyncio.SelectorEventLoop()
            asyncio.set_event_loop(loop)
        else:
            # 其他系统使用默认事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
    def get_ccxt_config(self) -> Dict[str, Any]:
        """获取CCXT配置"""
        config = {
            'async_mode': True,
            'timeout': 30000,
            'enableRateLimit': True
        }
        
        # Windows系统特殊处理
        if sys.platform == 'win32':
            config.update({
                'asyncio_loop': asyncio.get_event_loop()
            })
            
        return config
    
    def is_windows(self) -> bool:
        """是否是Windows系统"""
        return self.system_info['system'] == 'Windows'
        
    def is_linux(self) -> bool:
        """是否是Linux系统"""
        return self.system_info['system'] == 'Linux'
        
    def is_mac(self) -> bool:
        """是否是Mac系统"""
        return self.system_info['system'] == 'Darwin'

    def get_event_loop_policy(self):
        """获取事件循环策略"""
        if self.is_linux():
            import asyncio
            return asyncio.DefaultEventLoopPolicy()
        elif self.is_windows():
            import asyncio
            return asyncio.WindowsSelectorEventLoopPolicy()
        return None
    
    def get_optimal_thread_count(self) -> int:
        """获取最优线程数"""
        import multiprocessing
        if self.is_linux():
            return multiprocessing.cpu_count() * 2
        return multiprocessing.cpu_count()
    
    def get_io_config(self):
        """获取IO配置"""
        if self.is_linux():
            return {
                'use_uvloop': True,
                'use_threading': True,
                'max_workers': self.get_optimal_thread_count(),
                'buffer_size': 8192
            }
        return {
            'use_uvloop': False,
            'use_threading': True,
            'max_workers': self.get_optimal_thread_count(),
            'buffer_size': 4096
        } 