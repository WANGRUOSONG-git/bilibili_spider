from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont


class UpdateStatsWorker(QThread):
    stats_updated = pyqtSignal(dict)

    def __init__(self, db_handler):
        super().__init__()
        self.db_handler = db_handler
        self.is_running = False

    def run(self):
        self.is_running = True
        try:
            stats = self.db_handler.get_statistics()
            if self.is_running:
                self.stats_updated.emit(stats)
        except Exception as e:
            print(f"更新统计数据失败: {str(e)}")
        finally:
            self.is_running = False

    def stop(self):
        self.is_running = False


class StyledCard(QFrame):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
           StyledCard {
               background-color: #2d2d2d;
               border-radius: 10px;
               padding: 15px;
               margin: 5px;
           }
           QLabel {
               color: white;
           }
       """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078d4;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 内容
        content_label = QLabel(content)
        content_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(content_label)

    def update_content(self, content):
        """更新卡片内容"""
        for widget in self.findChildren(QLabel):
            if widget.styleSheet().find("color: white") != -1:
                widget.setText(content)
                break


class HomePage(QWidget):
    def __init__(self, db_handler):
        super().__init__()
        self.db_handler = db_handler
        self.stats_worker = None
        self.init_ui()

        # 创建定时器
        self.update_timer = QTimer()
        self.update_timer.setInterval(1000)  # 1秒
        self.update_timer.timeout.connect(self.start_update_stats)
        self.update_timer.start()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题区域
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)

        welcome_label = QLabel("欢迎使用B站评论爬虫")
        welcome_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("color: #0078d4; margin: 20px;")

        subtitle_label = QLabel("一个强大的B站评论数据采集工具")
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #cccccc; margin-bottom: 20px;")

        title_layout.addWidget(welcome_label)
        title_layout.addWidget(subtitle_label)

        layout.addWidget(title_widget)

        # 统计信息区域
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)

        # 加载实时统计数据
        stats = self.db_handler.get_statistics()

        self.total_comments = StyledCard("总评论数", str(stats['total_comments']))
        self.total_videos = StyledCard("视频数", str(stats['total_videos']))
        self.total_users = StyledCard("评论用户数", str(stats['total_users']))

        stats_layout.addWidget(self.total_comments)
        stats_layout.addWidget(self.total_videos)
        stats_layout.addWidget(self.total_users)

        layout.addWidget(stats_widget)

        # 功能区域
        feature_label = QLabel("快速入口")
        feature_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        feature_label.setStyleSheet("color: white; margin: 20px 0;")
        feature_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(feature_label)

        # 功能按钮区域
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setSpacing(20)

        self.start_crawl_btn = self.create_feature_button("开始爬取", "立即开始爬取B站视频评论")
        self.search_btn = self.create_feature_button("评论查询", "搜索和查看已爬取的评论")
        self.settings_btn = self.create_feature_button("系统设置", "配置Cookie和系统参数")

        buttons_layout.addWidget(self.start_crawl_btn)
        buttons_layout.addWidget(self.search_btn)
        buttons_layout.addWidget(self.settings_btn)

        layout.addWidget(buttons_widget)
        layout.addStretch()

        # 添加作者信息
        author_label = QLabel("版本: 1.0.0")
        author_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        author_label.setStyleSheet("color: #666666; margin: 0px;")
        layout.addWidget(author_label)

    def create_feature_button(self, title, description):
        button = QPushButton()
        button.setMinimumSize(QSize(300, 140))
        button.setStyleSheet("""
           QPushButton {
               background-color: #2d2d2d;
               border: none;
               border-radius: 10px;
               transition: background-color 0.2s;
           }
           QPushButton:hover {
               background-color: #3d3d3d;
           }
           QPushButton:pressed {
               background-color: #404040;
           }
       """)

        content_widget = QWidget(button)
        content_widget.setGeometry(button.rect())
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #0078d4;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #cccccc;")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        content_layout.addStretch()
        content_layout.addWidget(title_label)
        content_layout.addWidget(desc_label)
        content_layout.addStretch()

        # 确保内容跟随按钮大小变化
        button.resizeEvent = lambda e: content_widget.setGeometry(button.rect())

        return button

    def connect_buttons(self, tab_widget):
        """连接按钮信号到对应的标签页"""
        self.start_crawl_btn.clicked.connect(lambda: tab_widget.setCurrentIndex(1))
        self.search_btn.clicked.connect(lambda: tab_widget.setCurrentIndex(2))
        self.settings_btn.clicked.connect(lambda: tab_widget.setCurrentIndex(3))

    def start_update_stats(self):
        """启动异步统计更新"""
        if self.stats_worker and self.stats_worker.isRunning():
            self.stats_worker.stop()
            self.stats_worker.wait()

        self.stats_worker = UpdateStatsWorker(self.db_handler)
        self.stats_worker.stats_updated.connect(self.handle_stats_updated)
        self.stats_worker.start()

    def handle_stats_updated(self, stats):
        """处理统计更新结果"""
        self.total_comments.update_content(str(stats['total_comments']))
        self.total_videos.update_content(str(stats['total_videos']))
        self.total_users.update_content(str(stats['total_users']))