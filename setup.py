from setuptools import setup, find_packages

setup(
    name="crypto_arbitrage",
    version="1.0.0",
    packages=find_packages(include=['src', 'src.*']),
    package_dir={'': 'src'},
    install_requires=[
        "ccxt>=4.2.15",
        "pandas>=2.2.0",
        "numpy>=1.26.0",
        "aiohttp>=3.9.0",
        "python-dateutil>=2.8.2",
        "pytz>=2024.1",
        "requests>=2.31.0",
        "qtawesome>=1.3.0",
        "PyQt6>=6.4.0"
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="加密货币跨交易所套利系统",
    keywords="cryptocurrency,arbitrage,trading",
    python_requires=">=3.8",
) 