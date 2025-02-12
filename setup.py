from setuptools import setup, find_packages
import platform
import sys

# 根据操作系统确定依赖项
SYSTEM = platform.system().lower()

# 基础依赖
INSTALL_REQUIRES = [
    # 核心依赖
    "python-dotenv>=0.19.0",
    "ccxt>=4.0.0",
    "numpy>=1.21.0",
    "pandas>=1.3.0",
    "watchdog>=2.1.0",  # 文件系统监控
    
    # 系统和进程管理
    "setproctitle>=1.2.2",  # 进程标题设置
    "psutil>=5.8.0",  # 系统和进程监控
    
    # Web服务和API
    "fastapi>=0.68.0",
    "uvicorn[standard]>=0.24.0",  # 更新到较新的稳定版本
    "python-multipart>=0.0.9",
    "websockets>=12.0",
    "httptools>=0.6.0",  # HTTP协议工具
    "httpx>=0.26.0",  # 异步HTTP客户端
    
    # 机器学习依赖
    "tensorflow>=2.10.0",  # 添加TensorFlow
    "torch>=2.0.0",
    "torchvision>=0.15.0",
    "torchaudio>=2.0.0",
    "scikit-learn>=1.0.0",
    "xgboost>=2.1.4",
    "tensorboard>=2.10.0",  # PyTorch可视化工具
    "pytorch-lightning>=2.0.0",  # PyTorch高级训练框架
    "optuna>=3.0.0",  # 超参数优化
    
    # 数据库
    "influxdb-client>=1.24.0",
    "redis>=4.0.0",
    "aiomysql>=0.2.0",
    "aiosqlite>=0.20.0",
    "tortoise-orm>=0.22.1",
    
    # 工具库
    "aiohttp>=3.8.0",
    "python-telegram-bot>=13.7",
    "requests>=2.26.0",
    "pydantic>=1.8.2",
    "loguru>=0.5.3",
    "PyYAML>=5.4.1",
    "aiodns>=3.2.0",
    "aiohappyeyeballs>=2.4.4",
    "aiosignal>=1.3.2",
    "async-timeout>=5.0.1",
    "attrs>=25.1.0",
    "black>=25.1.0",
    "cachetools>=5.5.1",
    "ccxtpro>=1.0.1",
    "cryptography>=44.0.0",
    "filelock>=3.17.0",
    "flatbuffers>=25.1.24",
    "frozenlist>=1.5.0",
    "fsspec>=2025.2.0",
    "h11>=0.14.0",
    "idna>=3.10",
    "iniconfig>=2.0.0",
    "iso8601>=2.1.0",
    "Jinja2>=3.1.5",
    "joblib>=1.4.2",
    "libclang>=18.1.1",
    "MarkupSafe>=3.0.2",
    "mpmath>=1.3.0",
    "multidict>=6.1.0",
    "mypy-extensions>=1.0.0",
    "namex>=0.0.8",
    "networkx>=3.4.2",
    "packaging>=24.2",
    "pathspec>=0.12.1",
    "patsy>=1.0.1",
    "platformdirs>=4.3.6",
    "pluggy>=1.5.0",
    "propcache>=0.2.1",
    "pycares>=4.5.0",
    "pycparser>=2.22",
    "pydantic_core>=2.27.1",
    "PyMySQL>=1.1.1",
    "pypika-tortoise>=0.3.0",
    
    # 监控和性能
    "prometheus-client>=0.11.0",
    
    # GUI依赖
    "PyQt6>=6.8.1",
    "pyqtgraph>=0.13.3",
    
    # 其他工具
    "python-dateutil>=2.8.2",
    "pytz>=2024.2",
    "scipy>=1.15.1",
    "statsmodels>=0.14.4",
    "sympy>=1.13.1",
    "networkx>=3.4.2",
    "redis-cli>=1.0.1",
    "sniffio>=1.3.1",
    "starlette>=0.41.3",
    "termcolor>=2.5.0",
    "threadpoolctl>=3.5.0",
    "typing_extensions>=4.12.2",
    "urllib3>=2.3.0",
    "wrapt>=1.17.2",
]

# Linux特定依赖
if SYSTEM == "linux":
    INSTALL_REQUIRES.extend([
        "uvloop>=0.19.0",  # 异步事件循环优化（仅Linux）
        "python-daemon>=3.0.1",  # Linux守护进程支持
        "gunicorn>=21.2.0",  # 生产环境WSGI服务器
        "psycopg2-binary>=2.9.1",  # PostgreSQL驱动
    ])
# Windows特定依赖
elif SYSTEM == "windows":
    INSTALL_REQUIRES.extend([
        "psycopg2-binary>=2.9.1",  # PostgreSQL驱动（Windows二进制版本）
        "pywin32>=306",  # Windows系统API支持
        "wmi>=1.5.1",  # Windows管理规范
    ])

setup(
    name="crypto_arbitrage",
    version="1.0.0",
    description="加密货币套利交易系统",
    author="maodou7",
    author_email="",  # 请填写您的邮箱
    url="https://github.com/maodou7/Hedging_quantification",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "dev": [
            "pytest>=6.2.5",
            "pytest-asyncio>=0.15.1",
            "coverage>=7.6.11",
        ],
        "docs": [
            "Sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "crypto-arbitrage=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    package_data={
        "": ["*.json", "*.yaml", "*.yml"],
    },
    include_package_data=True,
    zip_safe=False,
) 