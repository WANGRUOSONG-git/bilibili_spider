# pages/settings_page.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QTextEdit, QFrame,
                             QMessageBox, QSpinBox)
from PyQt6.QtCore import Qt
from datetime import datetime

from bilibili_spider.utils.cookie_helper import CookieHelper


class StyledFrame(QFrame):
    """自定义样式面板"""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            StyledFrame {
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)

        if title:
            label = QLabel(title)
            label.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: white;
                padding: 5px;
                margin-bottom: 10px;
            """)
            self.layout.addWidget(label)


class SettingsPage(QWidget):
    """设置页面"""

    def __init__(self, config, db_handler):
        super().__init__()
        self.config = config
        self.db_handler = db_handler
        self.cookie_helper = None
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Cookie设置区域
        cookie_frame = StyledFrame("Cookie 管理")
        cookie_frame.layout.setContentsMargins(10, 5, 10, 5)

        # Cookie状态显示
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 5, 0, 5)
        self.cookie_status_label = QLabel("当前状态: 未设置")
        self.cookie_status_label.setStyleSheet("""
            color: #ff9900;
            font-weight: bold;
            font-size: 14px;
            padding: 5px;
        """)
        status_layout.addWidget(self.cookie_status_label)
        cookie_frame.layout.addLayout(status_layout)

        # Cookie输入区域
        self.cookie_input = QTextEdit()
        self.cookie_input.setPlaceholderText(
            "请输入B站Cookie...\n"
            "提示：Cookie中必须包含以下字段：\n"
            "- SESSDATA\n"
            "- bili_jct\n"
            "- DedeUserID"
        )
        self.cookie_input.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        self.cookie_input.setMaximumHeight(150)
        cookie_frame.layout.addWidget(self.cookie_input)

        # Cookie操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        button_styles = """
            QPushButton {
                padding: 8px 20px;
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #1184db;
            }
            QPushButton:pressed {
                background-color: #006abc;
            }
        """

        # 创建并添加按钮
        for btn_text, btn_action in [
            ("快速获取Cookie", self.show_cookie_helper),
            ("验证Cookie", self.validate_cookie),
            ("保存Cookie", self.save_cookie),
            ("清除Cookie", self.clear_cookie)
        ]:
            btn = QPushButton(btn_text)
            btn.setStyleSheet(button_styles)
            btn.clicked.connect(btn_action)
            button_layout.addWidget(btn)

        cookie_frame.layout.addLayout(button_layout)
        layout.addWidget(cookie_frame)

        # 爬虫配置区域
        crawler_frame = StyledFrame("爬虫设置")
        crawler_frame.layout.setContentsMargins(10, 5, 10, 5)

        # 延迟设置
        delay_layout = QHBoxLayout()
        delay_layout.setContentsMargins(0, 5, 0, 5)

        delay_label = QLabel("请求延迟范围(秒):")
        delay_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                padding: 5px;
            }
        """)
        delay_layout.addWidget(delay_label)

        spinbox_style = """
            QSpinBox {
                padding: 8px;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                background-color: #2d2d2d;
                color: white;
                font-size: 14px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                background: #404040;
                border: none;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #505050;
            }
        """

        self.min_delay = QSpinBox()
        self.min_delay.setRange(0, 100)
        self.min_delay.setValue(self.config.DELAY_MIN)
        self.min_delay.setMinimumWidth(80)
        self.min_delay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.min_delay.setStyleSheet(spinbox_style)

        delay_layout.addWidget(self.min_delay)

        delay_to_label = QLabel("到")
        delay_to_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                padding: 5px;
            }
        """)
        delay_layout.addWidget(delay_to_label)

        self.max_delay = QSpinBox()
        self.max_delay.setRange(0, 100)
        self.max_delay.setValue(self.config.DELAY_MAX)
        self.max_delay.setMinimumWidth(80)
        self.max_delay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.max_delay.setStyleSheet(spinbox_style)

        delay_layout.addWidget(self.max_delay)
        delay_layout.addStretch()

        crawler_frame.layout.addLayout(delay_layout)

        # 重试设置
        retry_layout = QHBoxLayout()
        retry_layout.setContentsMargins(0, 5, 0, 5)

        retry_label = QLabel("最大重试次数:")
        retry_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                padding: 5px;
            }
        """)
        retry_layout.addWidget(retry_label)

        self.max_retries = QSpinBox()
        self.max_retries.setRange(0, 10)
        self.max_retries.setValue(self.config.MAX_RETRIES)
        self.max_retries.setMinimumWidth(80)
        self.max_retries.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.max_retries.setStyleSheet(spinbox_style)

        retry_layout.addWidget(self.max_retries)
        retry_layout.addStretch()

        crawler_frame.layout.addLayout(retry_layout)
        layout.addWidget(crawler_frame)

        # 数据库管理区域
        db_frame = StyledFrame("数据库管理")
        db_frame.layout.setContentsMargins(10, 5, 10, 5)

        # 数据库状态
        self.db_status_label = QLabel("数据库状态: 正常")
        self.db_status_label.setStyleSheet("""
            color: #00cc00;
            font-weight: bold;
            font-size: 14px;
            padding: 5px;
        """)
        db_frame.layout.addWidget(self.db_status_label)

        # 数据库操作按钮
        db_button_layout = QHBoxLayout()
        db_button_layout.setSpacing(10)

        self.clear_db_button = QPushButton("清空数据库")
        self.clear_db_button.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #d83b01;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #e9553e;
            }
            QPushButton:pressed {
                background-color: #c63502;
            }
        """)

        self.backup_db_button = QPushButton("备份数据库")
        self.backup_db_button.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #107c10;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #13981c;
            }
            QPushButton:pressed {
                background-color: #0e6a0e;
            }
        """)

        db_button_layout.addWidget(self.clear_db_button)
        db_button_layout.addWidget(self.backup_db_button)
        db_button_layout.addStretch()

        db_frame.layout.addLayout(db_button_layout)
        layout.addWidget(db_frame)

        # 连接信号
        self.clear_db_button.clicked.connect(self.clear_database)
        self.backup_db_button.clicked.connect(self.backup_database)

        layout.addStretch()

    def show_cookie_helper(self):
        """显示Cookie获取工具"""
        try:
            self.cookie_helper = CookieHelper(self.config, self.db_handler)
            self.cookie_helper.cookie_ready.connect(self.on_cookie_received)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动Cookie获取工具失败: {str(e)}")

    def on_cookie_received(self, cookie):
        """处理获取到的Cookie"""
        try:
            # 直接显示在输入框中
            self.cookie_input.setText(cookie)
            # 自动保存Cookie
            if self.config.set_cookie(cookie):
                self.db_handler.save_cookie(cookie)
                self.load_settings()
                QMessageBox.information(self, "成功", "Cookie已获取并保存！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理Cookie失败: {str(e)}")

    def load_settings(self):
        """加载当前设置"""
        try:
            cookie, need_update = self.db_handler.get_valid_cookie()
            if cookie:
                self.cookie_input.setText(cookie)
                if need_update:
                    self.cookie_status_label.setText("当前状态: Cookie即将过期")
                    self.cookie_status_label.setStyleSheet("""
                        color: #ff9900;
                        font-weight: bold;
                        font-size: 14px;
                        padding: 5px;
                    """)
                else:
                    self.cookie_status_label.setText("当前状态: Cookie有效")
                    self.cookie_status_label.setStyleSheet("""
                        color: #00cc00;
                        font-weight: bold;
                        font-size: 14px;
                        padding: 5px;
                    """)
            else:
                self.cookie_status_label.setText("当前状态: 未设置Cookie")
                self.cookie_status_label.setStyleSheet("""
                    color: #ff0000;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 5px;
                """)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载设置失败: {str(e)}")

    def validate_cookie(self):
        """验证Cookie"""
        cookie = self.cookie_input.toPlainText().strip()
        if not cookie:
            QMessageBox.warning(self, "提示", "请输入Cookie")
            return

        try:
            if self.config.validate_cookie(cookie):
                QMessageBox.information(self, "成功", "Cookie格式验证通过")
            else:
                QMessageBox.warning(self, "错误", "Cookie格式不正确或缺少必要字段")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"验证Cookie失败: {str(e)}")

    def save_cookie(self):
        """保存Cookie"""
        cookie = self.cookie_input.toPlainText().strip()
        if not cookie:
            QMessageBox.warning(self, "提示", "请输入Cookie")
            return

        try:
            # 先清除旧的Cookie
            self.config.clear_cookie()

            # 设置新的Cookie
            if self.config.set_cookie(cookie):
                self.db_handler.save_cookie(cookie)
                self.load_settings()  # 重新加载状态
                QMessageBox.information(self, "成功", "Cookie保存成功")
            else:
                QMessageBox.warning(self, "错误", "Cookie格式不正确或缺少必要字段")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存Cookie失败: {str(e)}")

    def clear_cookie(self):
        """清除Cookie"""
        reply = QMessageBox.question(
            self, "确认", "确定要清除Cookie吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cookie_input.clear()
                self.config.clear_cookie()
                self.db_handler.clear_cookies()
                self.load_settings()
                QMessageBox.information(self, "成功", "Cookie已清除")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清除Cookie失败: {str(e)}")

    def clear_database(self):
        """清空数据库"""
        reply = QMessageBox.question(
            self, "确认",
            "确定要清空数据库吗？此操作将删除所有已爬取的评论数据！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_handler.clear_database()
                QMessageBox.information(self, "成功", "数据库已清空")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清空数据库失败: {str(e)}")

    def backup_database(self):
        """备份数据库"""
        try:
            # 获取数据库中的所有评论数据
            comments = self.db_handler.get_all_comments()

            if not comments:
                QMessageBox.information(self, "提示", "数据库中没有评论数据")
                return

            # 提示用户选择保存路径
            from PyQt6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存CSV文件", "", "CSV文件 (*.csv)"
            )

            if not file_path:
                return  # 用户取消保存

            # 导出为CSV
            self.db_handler.export_comments_to_csv(file_path)

            QMessageBox.information(self, "成功", f"数据库备份成功，文件已保存到:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"备份数据库失败: {str(e)}")

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        if self.cookie_helper:
            self.cookie_helper.close()
            self.cookie_helper = None
        event.accept()

    def save_settings(self):
        """保存爬虫设置到配置类"""
        try:
            self.config.DELAY_MIN = self.min_delay.value()
            self.config.DELAY_MAX = self.max_delay.value()
            self.config.MAX_RETRIES = self.max_retries.value()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")
