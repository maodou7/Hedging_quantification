"""
日志配置模块
"""
import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, log_file: str = None, level=logging.INFO) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 防止日志传播到父记录器
    logger.propagate = False
    
    # 如果已经有处理器，不再添加
    if logger.handlers:
        return logger
        
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'  # 添加统一的时间格式
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)  # 设置处理器级别
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，创建文件处理器
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)  # 设置处理器级别
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name) 