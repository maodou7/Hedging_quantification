"""
系统适配器模块
负责处理不同操作系统的兼容性问题
"""

import sys
import platform
import asyncio
import logging
from typing import Dict, Any
import aiohttp.resolver

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
            'machine': self.machine
        }
        
    def setup_event_loop(self):
        """设置事件循环"""
        try:
            if self.is_windows():
                # Windows系统使用SelectorEventLoop
                loop = asyncio.SelectorEventLoop()
                asyncio.set_event_loop(loop)
                logging.info("[系统适配器] Windows系统使用SelectorEventLoop")
            elif self.is_linux():
                # Linux系统使用uvloop
                try:
                    import uvloop
                    uvloop.install()
                    logging.info("[系统适配器] Linux系统使用uvloop")
                except ImportError:
                    logging.warning("[系统适配器] uvloop不可用，使用默认事件循环")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            else:
                # 其他系统使用默认事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                logging.info(f"[系统适配器] {self.system}系统使用默认事件循环")
        except Exception as e:
            logging.error(f"[系统适配器] 设置事件循环失败: {str(e)}")
            # 使用默认事件循环作为后备方案
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