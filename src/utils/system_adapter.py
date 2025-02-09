"""
系统适配器模块
负责处理不同操作系统的兼容性问题
"""

import sys
import platform
import asyncio
import logging
import psutil
import os
from typing import Dict, Any
import aiohttp.resolver

logger = logging.getLogger(__name__)

class SystemAdapter:
    """系统适配器类"""
    
    def __init__(self):
        """初始化系统适配器"""
        self.system = platform.system()
        self.python_version = sys.version
        self.platform = platform.platform()
        self.machine = platform.machine()
        
        # 设置事件循环策略
        if self.is_windows():
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            # 禁用aiodns
            try:
                aiohttp.resolver.DefaultResolver = aiohttp.resolver.ThreadedResolver
                logging.info("[系统适配器] Windows系统已禁用aiodns")
            except ImportError:
                logging.warning("[系统适配器] 无法加载aiohttp.resolver")
        
    def get_system_info(self) -> dict:
        """获取系统信息"""
        return {
            'system': self.system,
            'python_version': self.python_version,
            'platform': self.platform,
            'machine': self.machine,
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_interfaces': len(psutil.net_if_addrs())
        }
        
    def setup_event_loop(self):
        """设置事件循环"""
        if self.is_windows():
            import selectors
            selector = selectors.SelectSelector()
            loop = asyncio.SelectorEventLoop(selector)
            asyncio.set_event_loop(loop)
            logger.info("已设置Windows系统的事件循环")
        else:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info(f"已设置{self.system}系统的事件循环")
    
    def get_ccxt_config(self) -> Dict[str, Any]:
        """获取CCXT配置"""
        config = {
            'async_mode': True,
            'timeout': 30000,
            'enableRateLimit': True
        }
        
        # Windows系统特殊处理
        if self.is_windows():
            config.update({
                'asyncio_loop': asyncio.get_event_loop(),
                'aiohttp_trust_env': False,  # 禁用aiohttp的环境变量
                'aiohttp_kwargs': {
                    'resolver_cache': None,  # 禁用DNS缓存
                    'use_dns_cache': False   # 禁用DNS缓存
                }
            })
            
        return config
    
    def is_windows(self) -> bool:
        """是否是Windows系统"""
        return self.system == 'Windows'
        
    def is_linux(self) -> bool:
        """是否是Linux系统"""
        return self.system == 'Linux'
        
    def is_mac(self) -> bool:
        """是否是Mac系统"""
        return self.system == 'Darwin'

    def get_event_loop_policy(self):
        """获取事件循环策略"""
        if self.is_windows():
            return asyncio.WindowsSelectorEventLoopPolicy()
        return asyncio.DefaultEventLoopPolicy()
    
    def get_optimal_thread_count(self) -> int:
        """获取最优线程数"""
        import multiprocessing
        if self.is_linux():
            return multiprocessing.cpu_count() * 2
        return multiprocessing.cpu_count()
    
    def get_io_config(self):
        """获取IO配置"""
        config = {
            'use_threading': True,
            'max_workers': self.get_optimal_thread_count(),
            'buffer_size': 4096
        }
        
        # Linux系统特殊配置
        if self.is_linux():
            config.update({
                'use_uvloop': True,
                'buffer_size': 8192
            })
        else:
            config.update({
                'use_uvloop': False
            })
            
        return config
    
    def setup_process(self):
        """设置进程"""
        if self.is_windows():
            # Windows系统特定的进程设置
            import win32api
            import win32con
            win32api.SetPriorityClass(win32api.GetCurrentProcess(), win32con.HIGH_PRIORITY_CLASS)
        else:
            # Unix系统特定的进程设置
            os.nice(10)
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        if not self.is_windows():
            # Unix系统支持的信号
            import signal
            signal.signal(signal.SIGTERM, self._handle_signal)
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGHUP, self._handle_signal)
        else:
            # Windows系统支持的信号
            import signal
            signal.signal(signal.SIGTERM, self._handle_signal)
            signal.signal(signal.SIGINT, self._handle_signal)
    
    def _handle_signal(self, signum, frame):
        """处理系统信号"""
        logger.info(f"收到系统信号: {signum}")
        sys.exit(0)
    
    def setup_logging(self):
        """设置日志"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(os.path.join(log_dir, 'system.log'))
            ]
        )
    
    def cleanup(self):
        """清理系统资源"""
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.close()
        except Exception as e:
            logger.error(f"清理事件循环时发生错误: {str(e)}")
        
        logger.info("系统资源已清理") 