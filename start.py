#!/usr/bin/env python3
"""
智能启动脚本
自动检测系统环境并选择最佳启动方式
"""
import os
import sys
import psutil
import platform
import subprocess
from pathlib import Path
import multiprocessing
import logging
from typing import Optional

from src.config.startup import get_startup_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("启动器")

class SystemAdapter:
    def __init__(self):
        self.system = platform.system().lower()
        self.cpu_count = multiprocessing.cpu_count()
        self.total_memory = psutil.virtual_memory().total
        self.config = get_startup_config()
        self.env_config = self.config["environment"]
        self.sys_config = self.config["system"][self.system]
        self.res_config = self.config["resources"]
        
    def get_optimal_workers(self) -> int:
        """计算最优worker数量"""
        workers_by_cpu = self.cpu_count * self.res_config["cpu_multiplier"]
        memory_gb = self.total_memory / (1024 * 1024 * 1024)
        workers_by_memory = int(memory_gb / self.res_config["memory_per_worker"])
        
        optimal_workers = min(workers_by_cpu, workers_by_memory)
        return max(
            self.res_config["min_workers"],
            min(optimal_workers, self.res_config["max_workers"])
        )

    def get_startup_command(self) -> tuple[str, list[str]]:
        """获取最佳启动命令"""
        workers = self.get_optimal_workers()
        cmd = self.env_config["server"]
        
        if cmd == "gunicorn":
            args = [
                "-w", str(workers),
                "-k", self.sys_config["worker_class"],
                "--timeout", str(self.res_config["timeout"]),
                "--graceful-timeout", str(self.res_config["graceful_timeout"]),
                "--access-logfile", "-",
                "--error-logfile", "-",
                "--log-level", self.env_config["log_level"],
            ]
            
            if self.sys_config["worker_tmp_dir"]:
                args.extend(["--worker-tmp-dir", self.sys_config["worker_tmp_dir"]])
                
            if self.system == "linux":
                if self.sys_config["preload_app"]:
                    args.append("--preload")
                if self.sys_config["max_requests"] > 0:
                    args.extend([
                        "--max-requests", str(self.sys_config["max_requests"]),
                        "--max-requests-jitter", str(self.sys_config["max_requests_jitter"])
                    ])
            
            args.append("src.main:app")
            
        else:  # uvicorn
            args = [
                "src.main:app",
                "--workers", str(workers),
                "--loop", "uvloop",
                "--http", "httptools",
                "--log-level", self.env_config["log_level"],
            ]
            
            if self.env_config["reload"]:
                args.extend(["--reload", "--reload-dir", "src"])
                
            if self.system == "linux":
                args.append("--proxy-headers")
                
        return cmd, args

def check_dependencies() -> bool:
    """检查必要的依赖是否已安装"""
    try:
        import uvicorn
        import gunicorn
        import fastapi
        return True
    except ImportError as e:
        logger.error(f"缺少必要的依赖: {e}")
        return False

def setup_environment() -> None:
    """设置运行环境"""
    project_root = Path(__file__).parent.absolute()
    sys.path.insert(0, str(project_root))
    
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    if platform.system().lower() == "linux":
        import resource
        config = get_startup_config()
        fd_limit = config["system"]["linux"]["fd_limit"]
        if fd_limit:
            resource.setrlimit(resource.RLIMIT_NOFILE, (fd_limit, fd_limit))

def main():
    """主函数"""
    try:
        logger.info("正在初始化启动环境...")
        
        if not check_dependencies():
            sys.exit(1)
            
        setup_environment()
        
        adapter = SystemAdapter()
        cmd, args = adapter.get_startup_command()
        
        logger.info(f"系统信息: {platform.system()} {platform.release()}")
        logger.info(f"CPU核心数: {adapter.cpu_count}")
        logger.info(f"内存大小: {adapter.total_memory / (1024*1024*1024):.1f}GB")
        logger.info(f"运行模式: {adapter.env_config['description']}")
        logger.info(f"启动命令: {cmd} {' '.join(args)}")
        
        process = subprocess.Popen([cmd, *args])
        process.wait()
        
    except KeyboardInterrupt:
        logger.info("收到终止信号，正在关闭...")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 