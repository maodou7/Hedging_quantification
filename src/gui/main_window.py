"""
主窗口界面

实现:
1. 策略监控
2. 实时行情
3. 配置管理
4. 性能分析
"""

import sys
import os
import aiohttp
import asyncio
from PyQt6.QtWidgets import (QMainWindow, QApplication, QTabWidget, 
                           QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QTableWidget, QTableWidgetItem, QFrame,
                           QDialog, QLineEdit, QFormLayout, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QColor, QIcon, QMouseEvent
import pyqtgraph as pg
from datetime import datetime
from typing import Dict, Any
import json
import qtawesome as qta

class SettingsDialog(QDialog):
    """设置对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(400, 250)
        
        # 加载当前设置
        self.settings = self.load_settings()
        
        # 创建表单布局
        layout = QFormLayout(self)
        
        # 主题选择
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["暗色主题", "明亮主题", "跟随系统"])
        current_theme = self.settings.get("theme", "暗色主题")
        self.theme_combo.setCurrentText(current_theme)
        layout.addRow("主题:", self.theme_combo)
        
        # 服务器地址
        self.host_edit = QLineEdit(self.settings.get("host", "localhost"))
        layout.addRow("服务器地址:", self.host_edit)
        
        # 端口
        self.port_edit = QLineEdit(str(self.settings.get("port", 8000)))
        layout.addRow("端口:", self.port_edit)
        
        # 保存按钮
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_settings)
        layout.addRow(self.save_button)
        
    def load_settings(self) -> Dict[str, Any]:
        """加载设置"""
        settings_file = os.path.join(os.path.dirname(__file__), "settings.json")
        if os.path.exists(settings_file):
            with open(settings_file, "r") as f:
                return json.load(f)
        return {
            "host": "localhost", 
            "port": 8000,
            "theme": "暗色主题"
        }
        
    def save_settings(self):
        """保存设置"""
        settings = {
            "host": self.host_edit.text(),
            "port": int(self.port_edit.text()),
            "theme": self.theme_combo.currentText()
        }
        
        settings_file = os.path.join(os.path.dirname(__file__), "settings.json")
        with open(settings_file, "w") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
            
        # 应用主题
        self.parent().apply_theme(settings["theme"])
        self.accept()

class APIClient:
    """API客户端"""
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get_strategy_status(self) -> Dict[str, Any]:
        """获取策略状态"""
        async with self.session.get(f"{self.base_url}/api/strategy/status") as response:
            return await response.json()
            
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """获取市场数据"""
        async with self.session.get(f"{self.base_url}/api/market/data/{symbol}") as response:
            return await response.json()
            
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        async with self.session.get(f"{self.base_url}/api/performance/metrics") as response:
            return await response.json()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("量化交易系统")
        self.resize(1200, 800)
        
        # 设置窗口样式
        self._init_window_style()
        
        # 创建API客户端
        self.settings = SettingsDialog.load_settings(None)
        self.api_client = APIClient(f"http://{self.settings['host']}:{self.settings['port']}")
        self.api_task = None
        
        # 创建事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # 创建中心部件
        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralwidget")
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 创建标题栏
        self._init_title_bar()
        
        # 创建内容区
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(0)
        self.main_layout.addWidget(content_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("")
        content_layout.addWidget(self.tab_widget)
        
        # 初始化各个标签页
        self._init_monitor_tab()
        self._init_market_tab()
        self._init_config_tab()
        self._init_performance_tab()
        
        # 设置定时器更新数据
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_data)
        self.update_timer.start(1000)  # 每秒更新一次
        
        # 用于窗口拖动
        self.dragging = False
        self.drag_position = QPoint()
        
        # 应用主题
        self.apply_theme(self.settings.get("theme", "暗色主题"))
        
    def _init_window_style(self):
        """初始化窗口样式"""
        # 加载样式表
        style_file = os.path.join(os.path.dirname(__file__), "themes/py_dracula_dark.qss")
        with open(style_file, "r", encoding='utf-8') as f:
            self.setStyleSheet(f.read())
            
        # 设置窗口属性
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.api_task:
            self.api_task.cancel()
        event.accept()
        
    def _init_title_bar(self):
        """初始化标题栏"""
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(35)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(10, 0, 10, 0)
        
        # 标题
        title_label = QLabel("量化交易系统")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # 设置按钮
        settings_button = QPushButton("⚙")
        settings_button.setObjectName("settingsButton")
        settings_button.setFixedSize(30, 30)
        settings_button.clicked.connect(self.show_settings)
        layout.addWidget(settings_button)
        
        # 最小化按钮
        min_button = QPushButton("─")
        min_button.setObjectName("minButton")
        min_button.setFixedSize(30, 30)
        min_button.clicked.connect(self.showMinimized)
        layout.addWidget(min_button)
        
        # 最大化按钮
        self.max_button = QPushButton("□")
        self.max_button.setObjectName("maxButton")
        self.max_button.setFixedSize(30, 30)
        self.max_button.clicked.connect(self.toggle_maximize)
        layout.addWidget(self.max_button)
        
        # 关闭按钮
        close_button = QPushButton("×")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        
        self.main_layout.addWidget(title_bar)
        
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        # 应用当前主题到对话框
        dialog.setStyleSheet(self.styleSheet())
        dialog.exec()
        
    def toggle_maximize(self):
        """切换最大化状态"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
            
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否在标题栏区域
            if event.position().y() <= 35:
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件"""
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

    def _init_monitor_tab(self):
        """初始化策略监控标签页"""
        monitor_tab = QWidget()
        layout = QVBoxLayout(monitor_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加策略状态表格
        self.strategy_table = QTableWidget()
        self.strategy_table.setColumnCount(6)
        self.strategy_table.setHorizontalHeaderLabels([
            "策略", "状态", "持仓", "盈亏", "订单数", "更新时间"
        ])
        self.strategy_table.horizontalHeader().setStretchLastSection(True)
        self.strategy_table.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self.strategy_table)
        
        # 添加控制按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.start_button = QPushButton("启动策略")
        self.start_button.setMinimumSize(120, 30)
        self.stop_button = QPushButton("停止策略")
        self.stop_button.setMinimumSize(120, 30)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(monitor_tab, "策略监控")
        
    def _init_market_tab(self):
        """初始化市场行情标签页"""
        market_tab = QWidget()
        layout = QVBoxLayout(market_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加选择区域
        select_layout = QHBoxLayout()
        
        # 交易所选择
        exchange_layout = QHBoxLayout()
        exchange_layout.addWidget(QLabel("交易所:"))
        self.exchange_combo = QComboBox()
        self.exchange_combo.setObjectName("exchangeCombo")
        self.exchange_combo.addItems(["Binance", "OKX", "Bybit"])
        self.exchange_combo.currentTextChanged.connect(self._on_exchange_changed)
        exchange_layout.addWidget(self.exchange_combo)
        select_layout.addLayout(exchange_layout)
        
        # 交易对选择
        pair_layout = QHBoxLayout()
        pair_layout.addWidget(QLabel("交易对:"))
        self.pair_combo = QComboBox()
        self.pair_combo.setObjectName("pairCombo")
        self.pair_combo.currentTextChanged.connect(self._on_pair_changed)
        pair_layout.addWidget(self.pair_combo)
        select_layout.addLayout(pair_layout)
        
        select_layout.addStretch()
        layout.addLayout(select_layout)
        
        # 添加K线图
        self.price_plot = pg.PlotWidget()
        self.price_plot.setBackground('transparent')
        self.price_plot.getAxis('bottom').setPen(pg.mkPen(color=(221, 221, 221)))
        self.price_plot.getAxis('left').setPen(pg.mkPen(color=(221, 221, 221)))
        layout.addWidget(self.price_plot)
        
        # 添加深度图
        self.depth_plot = pg.PlotWidget()
        self.depth_plot.setBackground('transparent')
        self.depth_plot.getAxis('bottom').setPen(pg.mkPen(color=(221, 221, 221)))
        self.depth_plot.getAxis('left').setPen(pg.mkPen(color=(221, 221, 221)))
        layout.addWidget(self.depth_plot)
        
        self.tab_widget.addTab(market_tab, "市场行情")
        
        # 初始化第一个交易所的交易对
        self._on_exchange_changed(self.exchange_combo.currentText())
        
    def _on_exchange_changed(self, exchange: str):
        """交易所改变时更新交易对列表"""
        self.pair_combo.clear()
        # 这里应该从API获取交易对列表，这里暂时使用模拟数据
        pairs = {
            "Binance": ["BTC/USDT", "ETH/USDT", "BNB/USDT"],
            "OKX": ["BTC/USDT", "ETH/USDT", "OKB/USDT"],
            "Bybit": ["BTC/USDT", "ETH/USDT", "BIT/USDT"]
        }
        self.pair_combo.addItems(pairs.get(exchange, []))
        
    def _on_pair_changed(self, pair: str):
        """交易对改变时更新图表"""
        if not pair:
            return
        # 这里应该从API获取数据，这里暂时使用空数据
        self.update_market_data(pair, {"time": [], "close": []}, 
                              {"bids_price": [], "bids_volume": [],
                               "asks_price": [], "asks_volume": []})
        
    def _init_config_tab(self):
        """初始化配置管理标签页"""
        config_tab = QWidget()
        layout = QVBoxLayout(config_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加配置表格
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(4)
        self.config_table.setHorizontalHeaderLabels([
            "参数", "值", "说明", "类型"
        ])
        self.config_table.horizontalHeader().setStretchLastSection(True)
        self.config_table.setFrameShape(QFrame.Shape.NoFrame)
        self.config_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.config_table.itemChanged.connect(self._on_config_changed)
        layout.addWidget(self.config_table)
        
        # 添加按钮区域
        button_layout = QHBoxLayout()
        
        # 添加参数按钮
        self.add_config_button = QPushButton("添加参数")
        self.add_config_button.clicked.connect(self._add_config)
        button_layout.addWidget(self.add_config_button)
        
        # 删除参数按钮
        self.delete_config_button = QPushButton("删除参数")
        self.delete_config_button.clicked.connect(self._delete_config)
        button_layout.addWidget(self.delete_config_button)
        
        button_layout.addStretch()
        
        # 保存配置按钮
        self.save_config_button = QPushButton("保存配置")
        self.save_config_button.clicked.connect(self._save_config)
        button_layout.addWidget(self.save_config_button)
        
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(config_tab, "配置管理")
        
        # 加载默认配置
        self._load_default_config()
        
    def _load_default_config(self):
        """加载默认配置"""
        default_config = [
            ("api_key", "", "交易所API密钥", "string"),
            ("api_secret", "", "交易所API密钥", "password"),
            ("trade_amount", "0.01", "每次交易数量", "float"),
            ("min_spread", "0.001", "最小价差", "float"),
            ("max_position", "1.0", "最大持仓", "float"),
            ("stop_loss", "0.02", "止损比例", "float")
        ]
        
        self.config_table.setRowCount(len(default_config))
        for i, (param, value, desc, type_) in enumerate(default_config):
            # 参数名
            param_item = QTableWidgetItem(param)
            param_item.setFlags(param_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.config_table.setItem(i, 0, param_item)
            
            # 参数值
            value_item = QTableWidgetItem(value)
            if type_ == "password":
                value_item.setFlags(value_item.flags() | Qt.ItemFlag.ItemIsEditable)
                value_item.setText("********")
            self.config_table.setItem(i, 1, value_item)
            
            # 说明
            desc_item = QTableWidgetItem(desc)
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.config_table.setItem(i, 2, desc_item)
            
            # 类型
            type_item = QTableWidgetItem(type_)
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.config_table.setItem(i, 3, type_item)
            
    def _on_config_changed(self, item):
        """配置项改变时的处理"""
        if item.column() != 1:  # 只处理值列的改变
            return
            
        row = item.row()
        type_item = self.config_table.item(row, 3)
        if not type_item:  # 检查类型单元格是否存在
            return
            
        type_ = type_item.text()
        value = item.text()
        
        try:
            # 根据类型验证值
            if type_ == "float":
                float(value)
            elif type_ == "int":
                int(value)
            elif type_ == "password":
                if value != "********":
                    # 这里应该保存新的密码
                    pass
        except ValueError:
            # 如果验证失败，恢复原值
            QMessageBox.warning(self, "输入错误", 
                              f"请输入正确的{type_}类型值")
            item.setText("")
            
    def _add_config(self):
        """添加新的配置项"""
        row = self.config_table.rowCount()
        self.config_table.insertRow(row)
        
        # 设置新行的默认值
        param_item = QTableWidgetItem("new_param")
        self.config_table.setItem(row, 0, param_item)
        
        value_item = QTableWidgetItem("")
        self.config_table.setItem(row, 1, value_item)
        
        desc_item = QTableWidgetItem("新参数说明")
        self.config_table.setItem(row, 2, desc_item)
        
        type_item = QTableWidgetItem("string")
        self.config_table.setItem(row, 3, type_item)
        
    def _delete_config(self):
        """删除选中的配置项"""
        current_row = self.config_table.currentRow()
        if current_row >= 0:
            self.config_table.removeRow(current_row)
            
    def _save_config(self):
        """保存配置"""
        config = {}
        for row in range(self.config_table.rowCount()):
            param = self.config_table.item(row, 0).text()
            value = self.config_table.item(row, 1).text()
            type_ = self.config_table.item(row, 3).text()
            
            # 根据类型转换值
            if type_ == "float":
                value = float(value)
            elif type_ == "int":
                value = int(value)
            elif type_ == "password" and value == "********":
                continue  # 跳过未修改的密码
                
            config[param] = value
            
        # 保存配置到文件
        config_file = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
            
        QMessageBox.information(self, "成功", "配置已保存")
        
    def _init_performance_tab(self):
        """初始化性能分析标签页"""
        performance_tab = QWidget()
        layout = QVBoxLayout(performance_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加收益曲线
        self.returns_plot = pg.PlotWidget()
        self.returns_plot.setBackground('transparent')
        self.returns_plot.getAxis('bottom').setPen(pg.mkPen(color=(221, 221, 221)))
        self.returns_plot.getAxis('left').setPen(pg.mkPen(color=(221, 221, 221)))
        layout.addWidget(self.returns_plot)
        
        # 添加性能指标
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(20)
        
        # 总收益
        returns_frame = QFrame()
        returns_frame.setFrameShape(QFrame.Shape.StyledPanel)
        returns_layout = QVBoxLayout(returns_frame)
        returns_layout.addWidget(QLabel("总收益"))
        self.total_returns_label = QLabel("0.00%")
        self.total_returns_label.setStyleSheet("font-size: 24px; color: #00ff00;")
        returns_layout.addWidget(self.total_returns_label)
        metrics_layout.addWidget(returns_frame)
        
        # 胜率
        win_rate_frame = QFrame()
        win_rate_frame.setFrameShape(QFrame.Shape.StyledPanel)
        win_rate_layout = QVBoxLayout(win_rate_frame)
        win_rate_layout.addWidget(QLabel("胜率"))
        self.win_rate_label = QLabel("0.00%")
        self.win_rate_label.setStyleSheet("font-size: 24px; color: #00ff00;")
        win_rate_layout.addWidget(self.win_rate_label)
        metrics_layout.addWidget(win_rate_frame)
        
        # 夏普比率
        sharpe_frame = QFrame()
        sharpe_frame.setFrameShape(QFrame.Shape.StyledPanel)
        sharpe_layout = QVBoxLayout(sharpe_frame)
        sharpe_layout.addWidget(QLabel("夏普比率"))
        self.sharpe_label = QLabel("0.00")
        self.sharpe_label.setStyleSheet("font-size: 24px; color: #00ff00;")
        sharpe_layout.addWidget(self.sharpe_label)
        metrics_layout.addWidget(sharpe_frame)
        
        metrics_layout.addStretch()
        layout.addLayout(metrics_layout)
        
        self.tab_widget.addTab(performance_tab, "性能分析")
        
    async def _fetch_data(self):
        """从API获取数据"""
        try:
            async with self.api_client as client:
                # 获取策略状态
                strategy_status = await client.get_strategy_status()
                self.update_strategy_status(strategy_status)
                
                # 获取市场数据
                market_data = await client.get_market_data("BTC/USDT")
                self.update_market_data("BTC/USDT", market_data["price_data"], market_data["depth_data"])
                
                # 获取性能指标
                metrics = await client.get_performance_metrics()
                self.update_performance_metrics(metrics)
                
        except Exception as e:
            print(f"获取数据时发生错误: {str(e)}")
            
    def _update_data(self):
        """更新界面数据"""
        if self.api_task and not self.api_task.done():
            return
            
        self.api_task = asyncio.run_coroutine_threadsafe(
            self._fetch_data(),
            self.loop
        )
            
    def update_strategy_status(self, status: Dict[str, Any]):
        """更新策略状态表格"""
        self.strategy_table.setRowCount(len(status))
        for i, (strategy_name, strategy_data) in enumerate(status.items()):
            # 设置单元格内容
            self.strategy_table.setItem(i, 0, QTableWidgetItem(strategy_name))
            
            status_item = QTableWidgetItem(strategy_data['status'])
            if strategy_data['status'] == "运行中":
                status_item.setForeground(QColor("#00ff00"))
            elif strategy_data['status'] == "错误":
                status_item.setForeground(QColor("#ff0000"))
            self.strategy_table.setItem(i, 1, status_item)
            
            self.strategy_table.setItem(i, 2, QTableWidgetItem(f"{strategy_data['position']:.2f}"))
            
            pnl_item = QTableWidgetItem(f"{strategy_data['pnl']:.2f}")
            if strategy_data['pnl'] > 0:
                pnl_item.setForeground(QColor("#00ff00"))
            elif strategy_data['pnl'] < 0:
                pnl_item.setForeground(QColor("#ff0000"))
            self.strategy_table.setItem(i, 3, pnl_item)
            
            self.strategy_table.setItem(i, 4, QTableWidgetItem(str(strategy_data['orders'])))
            self.strategy_table.setItem(i, 5, QTableWidgetItem(strategy_data['update_time']))
            
    def update_market_data(self, symbol: str, price_data: Dict[str, Any], depth_data: Dict[str, Any]):
        """更新市场行情图表"""
        # 更新K线图
        self.price_plot.clear()
        self.price_plot.plot(price_data['time'], price_data['close'], pen=pg.mkPen(color='w', width=2))
        
        # 更新深度图
        self.depth_plot.clear()
        self.depth_plot.plot(depth_data['bids_price'], depth_data['bids_volume'], 
                           pen=pg.mkPen(color='g', width=2))
        self.depth_plot.plot(depth_data['asks_price'], depth_data['asks_volume'], 
                           pen=pg.mkPen(color='r', width=2))
        
    def update_performance_metrics(self, metrics: Dict[str, Any]):
        """更新性能指标"""
        # 更新标签
        total_returns = metrics['total_returns']
        self.total_returns_label.setText(f"{total_returns:.2f}%")
        if total_returns > 0:
            self.total_returns_label.setStyleSheet("font-size: 24px; color: #00ff00;")
        else:
            self.total_returns_label.setStyleSheet("font-size: 24px; color: #ff0000;")
            
        self.win_rate_label.setText(f"{metrics['win_rate']:.2f}%")
        self.sharpe_label.setText(f"{metrics['sharpe_ratio']:.2f}")
        
        # 更新收益曲线
        self.returns_plot.clear()
        self.returns_plot.plot(range(len(metrics['time'])), metrics['cumulative_returns'], 
                             pen=pg.mkPen(color='w', width=2))

    def apply_theme(self, theme: str):
        """应用主题"""
        if theme == "暗色主题":
            style_file = os.path.join(os.path.dirname(__file__), "themes/py_dracula_dark.qss")
        elif theme == "明亮主题":
            style_file = os.path.join(os.path.dirname(__file__), "themes/py_light.qss")
        else:  # 跟随系统
            # 获取系统主题
            if self._is_system_dark_theme():
                style_file = os.path.join(os.path.dirname(__file__), "themes/py_dracula_dark.qss")
            else:
                style_file = os.path.join(os.path.dirname(__file__), "themes/py_light.qss")
        
        # 加载样式表
        with open(style_file, "r", encoding='utf-8') as f:
            self.setStyleSheet(f.read())
            
    def _is_system_dark_theme(self) -> bool:
        """检查系统是否使用暗色主题"""
        if sys.platform == "win32":
            try:
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return value == 0
            except:
                return False
        elif sys.platform == "darwin":  # macOS
            try:
                import subprocess
                cmd = 'defaults read -g AppleInterfaceStyle'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return result.stdout.strip() == 'Dark'
            except:
                return False
        else:  # Linux 或其他系统
            return False  # 默认返回 False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 