# main_window.py

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget,
                             QLabel, QStatusBar, QMessageBox)
from PyQt6.QtCore import Qt
import logging

from bilibili_spider.utils.config import Config
from bilibili_spider.utils.db_handler import DatabaseHandler
from bilibili_spider.pages.home_page import HomePage
from bilibili_spider.pages.crawl_page import CrawlPage
from bilibili_spider.pages.search_page import SearchPage
from bilibili_spider.pages.settings_page import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('BilibiliSpider')
        self.init_backend()
        self.init_ui()

    def init_backend(self):
        try:
            self.config = Config()
            self.db_handler = DatabaseHandler('bilibili_comments.db')
            self.spider = None
            self.logger.info("后端组件初始化成功")
        except Exception as e:
            self.logger.error(f"后端组件初始化失败: {str(e)}")
            QMessageBox.critical(self, "错误", "程序初始化失败，请检查配置和数据库")
            raise

    def init_ui(self):
        self.setWindowTitle("B站评论爬虫")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 600)
        self.setup_style()

        try:
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)

            self.tab_widget = QTabWidget()
            self.setup_tab_style()

            # 初始化各页面
            self.home_page = HomePage(self.db_handler)
            self.crawl_page = CrawlPage(self.db_handler, self.config)
            self.search_page = SearchPage(self.db_handler)
            self.settings_page = SettingsPage(self.config, self.db_handler)

            self.tab_widget.addTab(self.home_page, "主页")
            self.tab_widget.addTab(self.crawl_page, "评论爬取")
            self.tab_widget.addTab(self.search_page, "评论查询")
            self.tab_widget.addTab(self.settings_page, "系统设置")

            main_layout.addWidget(self.tab_widget)

            self.home_page.connect_buttons(self.tab_widget)

            self.logger.info("界面初始化完成")

        except Exception as e:
            self.logger.error(f"界面初始化失败: {str(e)}")
            QMessageBox.critical(self, "错误", "界面初始化失败")
            raise

    def setup_tab_style(self):
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #1e1e1e;
            }
            QTabBar::tab {
                background: #2d2d2d;
                color: white;
                padding: 12px 25px;
                margin: 0px 2px 0px 0px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: #0078d4;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background: #3d3d3d;
            }
        """)

    def setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                color: white;
            }
            QScrollBar:vertical {
                background: #2d2d2d;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #404040;
                min-height: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #505050;
            }
        """)

    def closeEvent(self, event):
        try:
            self.logger.info("正在关闭应用程序...")
            # 在这里添加清理代码
            event.accept()
        except Exception as e:
            self.logger.error(f"程序关闭时发生错误: {str(e)}")
            event.accept()
