"""
主窗口界面

实现:
1. 策略监控
2. 实时行情
3. 配置管理
4. 性能分析
"""

import sys
from PyQt6.QtWidgets import (QMainWindow, QApplication, QTabWidget, 
                           QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg
from datetime import datetime
from typing import Dict, Any

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("量化交易系统")
        self.resize(1200, 800)
        
        # 创建中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # 初始化各个标签页
        self._init_monitor_tab()
        self._init_market_tab()
        self._init_config_tab()
        self._init_performance_tab()
        
        # 设置定时器更新数据
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_data)
        self.update_timer.start(1000)  # 每秒更新一次
        
    def _init_monitor_tab(self):
        """初始化策略监控标签页"""
        monitor_tab = QWidget()
        layout = QVBoxLayout(monitor_tab)
        
        # 添加策略状态表格
        self.strategy_table = QTableWidget()
        self.strategy_table.setColumnCount(6)
        self.strategy_table.setHorizontalHeaderLabels([
            "策略", "状态", "持仓", "盈亏", "订单数", "更新时间"
        ])
        layout.addWidget(self.strategy_table)
        
        # 添加控制按钮
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("启动策略")
        self.stop_button = QPushButton("停止策略")
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(monitor_tab, "策略监控")
        
    def _init_market_tab(self):
        """初始化市场行情标签页"""
        market_tab = QWidget()
        layout = QVBoxLayout(market_tab)
        
        # 添加K线图
        self.price_plot = pg.PlotWidget()
        self.price_plot.setBackground('w')
        layout.addWidget(self.price_plot)
        
        # 添加深度图
        self.depth_plot = pg.PlotWidget()
        self.depth_plot.setBackground('w')
        layout.addWidget(self.depth_plot)
        
        # 添加交易对选择
        symbol_layout = QHBoxLayout()
        symbol_layout.addWidget(QLabel("交易对:"))
        self.symbol_label = QLabel("BTC/USDT")
        symbol_layout.addWidget(self.symbol_label)
        layout.addLayout(symbol_layout)
        
        self.tab_widget.addTab(market_tab, "市场行情")
        
    def _init_config_tab(self):
        """初始化配置管理标签页"""
        config_tab = QWidget()
        layout = QVBoxLayout(config_tab)
        
        # 添加配置表格
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(3)
        self.config_table.setHorizontalHeaderLabels([
            "参数", "值", "说明"
        ])
        layout.addWidget(self.config_table)
        
        # 添加保存按钮
        self.save_config_button = QPushButton("保存配置")
        layout.addWidget(self.save_config_button)
        
        self.tab_widget.addTab(config_tab, "配置管理")
        
    def _init_performance_tab(self):
        """初始化性能分析标签页"""
        performance_tab = QWidget()
        layout = QVBoxLayout(performance_tab)
        
        # 添加收益曲线
        self.returns_plot = pg.PlotWidget()
        self.returns_plot.setBackground('w')
        layout.addWidget(self.returns_plot)
        
        # 添加性能指标
        metrics_layout = QHBoxLayout()
        metrics_layout.addWidget(QLabel("总收益:"))
        self.total_returns_label = QLabel("0.00%")
        metrics_layout.addWidget(self.total_returns_label)
        
        metrics_layout.addWidget(QLabel("胜率:"))
        self.win_rate_label = QLabel("0.00%")
        metrics_layout.addWidget(self.win_rate_label)
        
        metrics_layout.addWidget(QLabel("夏普比率:"))
        self.sharpe_label = QLabel("0.00")
        metrics_layout.addWidget(self.sharpe_label)
        
        layout.addLayout(metrics_layout)
        
        self.tab_widget.addTab(performance_tab, "性能分析")
        
    def _update_data(self):
        """更新界面数据"""
        try:
            # 更新策略状态
            self._update_strategy_status()
            
            # 更新市场行情
            self._update_market_data()
            
            # 更新性能指标
            self._update_performance_metrics()
            
        except Exception as e:
            print(f"更新数据时发生错误: {str(e)}")
            
    def _update_strategy_status(self):
        """更新策略状态"""
        # TODO: 从策略管理器获取状态数据
        pass
        
    def _update_market_data(self):
        """更新市场行情"""
        # TODO: 从行情模块获取数据
        pass
        
    def _update_performance_metrics(self):
        """更新性能指标"""
        # TODO: 从性能监控模块获取数据
        pass
        
    def update_strategy_status(self, status: Dict[str, Any]):
        """更新策略状态表格"""
        self.strategy_table.setRowCount(len(status))
        for i, (strategy_name, strategy_data) in enumerate(status.items()):
            self.strategy_table.setItem(i, 0, QTableWidgetItem(strategy_name))
            self.strategy_table.setItem(i, 1, QTableWidgetItem(strategy_data['status']))
            self.strategy_table.setItem(i, 2, QTableWidgetItem(str(strategy_data['position'])))
            self.strategy_table.setItem(i, 3, QTableWidgetItem(f"{strategy_data['pnl']:.2f}"))
            self.strategy_table.setItem(i, 4, QTableWidgetItem(str(strategy_data['orders'])))
            self.strategy_table.setItem(i, 5, QTableWidgetItem(strategy_data['update_time']))
            
    def update_market_data(self, symbol: str, price_data: Dict[str, Any], depth_data: Dict[str, Any]):
        """更新市场行情图表"""
        # 更新K线图
        self.price_plot.clear()
        self.price_plot.plot(price_data['time'], price_data['close'])
        
        # 更新深度图
        self.depth_plot.clear()
        self.depth_plot.plot(depth_data['bids_price'], depth_data['bids_volume'], pen='g')
        self.depth_plot.plot(depth_data['asks_price'], depth_data['asks_volume'], pen='r')
        
    def update_performance_metrics(self, metrics: Dict[str, Any]):
        """更新性能指标"""
        self.total_returns_label.setText(f"{metrics['total_returns']:.2f}%")
        self.win_rate_label.setText(f"{metrics['win_rate']:.2f}%")
        self.sharpe_label.setText(f"{metrics['sharpe_ratio']:.2f}")
        
        # 更新收益曲线
        self.returns_plot.clear()
        self.returns_plot.plot(metrics['time'], metrics['cumulative_returns'])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 