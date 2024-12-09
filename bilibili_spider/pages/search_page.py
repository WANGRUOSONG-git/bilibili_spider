from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QFrame, QComboBox, QLineEdit, QApplication,
                             QHeaderView, QMessageBox, QToolTip, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation
from PyQt6.QtGui import QColor, QCursor
import json


class SearchWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, db_handler, query_type, search_text='', sort_field='publish_time', sort_order='DESC'):
        super().__init__()
        self.db_handler = db_handler
        self.query_type = query_type
        self.search_text = search_text
        self.sort_field = sort_field
        self.sort_order = sort_order

    def run(self):
        try:
            results = self.db_handler.query_comments_batch(
                self.query_type,
                self.search_text,
                batch_size=1000,
                offset=0,
                sort_by=self.sort_field,
                sort_order=self.sort_order
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

class StyledFrame(QFrame):
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


class SearchPage(QWidget):
    def __init__(self, db_handler):
        super().__init__()
        self.db_handler = db_handler
        self.search_worker = None
        self.sort_field = 'publish_time'
        self.sort_order = 'DESC'
        self.floating_tip = FloatingTip(self)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 搜索控制区域
        search_frame = StyledFrame("搜索控制")
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        search_layout.setContentsMargins(10, 5, 10, 5)

        # 搜索类型选择
        self.search_type = QComboBox()
        self.search_type.addItems([
            "查看全部评论",
            "按视频ID搜索",
            "按视频标题搜索",
            "按用户名搜索",
            "按评论内容搜索"
        ])
        self.search_type.setStyleSheet("""
           QComboBox {
               padding: 8px;
               border: 1px solid #3d3d3d;
               border-radius: 4px;
               background-color: #1e1e1e;
               color: white;
               min-width: 150px;
               font-size: 14px;
           }
           QComboBox::drop-down {
               border: none;
               width: 30px;
           }
           QComboBox::down-arrow {
               image: url(resources/down_arrow.png);
               width: 12px;
               height: 12px;
           }
           QComboBox QAbstractItemView {
               background-color: #1e1e1e;
               border: 1px solid #3d3d3d;
               selection-background-color: #0078d4;
               color: white;
           }
       """)

        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setEnabled(False)
        self.search_input.setPlaceholderText("查看全部评论无需输入搜索内容")
        self.search_input.setStyleSheet("""
           QLineEdit {
               padding: 8px;
               border: 1px solid #3d3d3d;
               border-radius: 4px;
               background-color: #1e1e1e;
               color: white;
               font-size: 14px;
           }
           QLineEdit:focus {
               border: 1px solid #0078d4;
           }
           QLineEdit:disabled {
               background-color: #2d2d2d;
               color: #888888;
           }
       """)

        # 搜索按钮
        self.search_button = QPushButton("搜索")
        self.search_button.setStyleSheet("""
           QPushButton {
               padding: 8px 20px;
               background-color: #0078d4;
               color: white;
               border: none;
               border-radius: 4px;
               font-weight: bold;
               font-size: 14px;
               min-width: 100px;
           }
           QPushButton:hover {
               background-color: #1184db;
           }
           QPushButton:pressed {
               background-color: #006abc;
           }
           QPushButton:disabled {
               background-color: #666666;
           }
       """)

        search_layout.addWidget(self.search_type)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        search_frame.layout.addLayout(search_layout)
        layout.addWidget(search_frame)

        # 结果表格
        results_frame = StyledFrame("搜索结果")
        results_frame.layout.setContentsMargins(10, 5, 10, 5)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(8)
        self.result_table.setHorizontalHeaderLabels([
            '视频ID', '视频标题', '用户名', '评论内容', '发布时间',
            '点赞数', '回复数', '更新时间'
        ])

        self.setup_table_style()
        results_frame.layout.addWidget(self.result_table)
        layout.addWidget(results_frame)

        # 连接信号
        self.search_button.clicked.connect(self.start_search)
        self.search_type.currentIndexChanged.connect(self.on_search_type_changed)
        self.result_table.horizontalHeader().sectionClicked.connect(self.handle_sort_click)
        self.result_table.cellDoubleClicked.connect(self.copy_cell_content)

    def setup_table_style(self):
        self.result_table.setStyleSheet("""
           QTableWidget {
               background-color: #1e1e1e;
               border: 1px solid #3d3d3d;
               gridline-color: #3d3d3d;
               color: white;
           }
           QTableWidget::item {
               padding: 8px;
               border-bottom: 1px solid #3d3d3d;
               color: white;
           }
           QTableWidget::item:hover {
               background-color: #3d3d3d;
           }
           QTableWidget::item:selected {
               background-color: #404040;
               color: white;
           }
           QHeaderView::section {
               background-color: #2d2d2d;
               padding: 12px 8px;
               border: none;
               border-right: 1px solid #3d3d3d;
               border-bottom: 1px solid #3d3d3d;
               font-weight: bold;
               color: white;
               font-size: 14px;
           }
           QHeaderView::section:hover {
               background-color: #3d3d3d;
               cursor: pointer;
           }
           QToolTip {
               background-color: #2d2d2d;
               color: white;
               border: 1px solid #3d3d3d;
               padding: 5px;
           }
       """)

        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        column_widths = {
            0: 120,  # 视频ID
            1: 200,  # 视频标题
            2: 150,  # 用户名
            3: 305,  # 评论内容
            4: 150,  # 发布时间
            5: 80,  # 点赞数
            6: 80,  # 回复数
            7: 150  # 更新时间
        }

        for col, width in column_widths.items():
            self.result_table.setColumnWidth(col, width)

        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.result_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

    def copy_cell_content(self, row, col):
        try:
            content = ''
            cell_widget = self.result_table.cellWidget(row, col)
            if cell_widget and isinstance(cell_widget, QLabel):
                content = cell_widget.text()
                content = content.replace('<span style=\'color: #ff4444\'>', '').replace('</span>', '')
            else:
                item = self.result_table.item(row, col)
                if item:
                    content = item.text()

            if content:
                clipboard = QApplication.clipboard()
                clipboard.setText(content)

                # 获取鼠标位置
                cursor_pos = QCursor.pos()
                tip = FloatingTip(self)
                tip.showTip("已复制到剪贴板", cursor_pos, 2000)

        except Exception as e:
            print(f"复制内容失败: {str(e)}")

    def on_search_type_changed(self, index):
        self.search_input.setEnabled(index != 0)
        if index == 0:
            self.search_input.clear()
            self.search_input.setPlaceholderText("查看全部评论无需输入搜索内容")
        else:
            self.search_input.setPlaceholderText("请输入搜索内容...")

    def handle_sort_click(self, column_index):
        sort_mapping = {
            4: 'publish_time',  # 发布时间列
            5: 'like_count',  # 点赞数列
            6: 'replies'  # 回复数列
        }

        if column_index in sort_mapping:
            if self.sort_field == sort_mapping[column_index]:
                self.sort_order = 'ASC' if self.sort_order == 'DESC' else 'DESC'
            else:
                self.sort_field = sort_mapping[column_index]
                self.sort_order = 'DESC'

            self.start_search()

    def start_search(self):
        if hasattr(self, 'search_worker') and self.search_worker:
            self.search_worker.wait()
            self.search_worker.deleteLater()
            self.search_worker = None

        query_type = str(self.search_type.currentIndex() + 1)
        search_text = self.search_input.text().strip()

        if query_type != '1' and not search_text:
            return

        self.result_table.setRowCount(0)
        self.search_button.setEnabled(False)
        self.search_button.setText("正在查询...")

        self.search_worker = SearchWorker(
            self.db_handler,
            query_type,
            search_text,
            self.sort_field,
            self.sort_order
        )
        self.search_worker.finished.connect(self.handle_search_results)
        self.search_worker.error.connect(self.handle_search_error)
        self.search_worker.start()

    def highlight_text(self, text, search_text):
        if not search_text or search_text.lower() not in text.lower():
            return text

        label = QLabel()
        index = text.lower().find(search_text.lower())
        before = text[:index]
        matched = text[index:index + len(search_text)]
        after = text[index + len(search_text):]

        label.setText(f"{before}<span style='color: #ff4444'>{matched}</span>{after}")
        label.setTextFormat(Qt.TextFormat.RichText)
        return label

    def handle_search_results(self, results):
        try:
            self.result_table.setRowCount(0)
            query_type = str(self.search_type.currentIndex() + 1)
            search_text = self.search_input.text().strip()

            for row_data in results:
                row = self.result_table.rowCount()
                self.result_table.insertRow(row)

                for col, data in enumerate(row_data):
                    text = str(data)
                    if len(text) > 100 and col == 3:
                        text = text[:97] + "..."

                    if search_text and (
                            (query_type == '2' and col == 0) or  # 视频ID
                            (query_type == '3' and col == 1) or  # 视频标题
                            (query_type == '4' and col == 2) or  # 用户名
                            (query_type == '5' and col == 3)  # 评论内容
                    ):
                        highlighted = self.highlight_text(text, search_text)
                        if isinstance(highlighted, QLabel):
                            self.result_table.setCellWidget(row, col, highlighted)
                            continue

                    item = QTableWidgetItem(text)
                    if col == 6:
                        replies = json.loads(data) if data else []
                        item.setText(str(len(replies)))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.result_table.setItem(row, col, item)

                self.result_table.setRowHeight(row, 40)

        except Exception as e:
            self.handle_search_error(str(e))
        finally:
            self.search_button.setEnabled(True)
            self.search_button.setText("搜索")

    def handle_search_error(self, error_message):
        self.search_button.setEnabled(True)
        self.search_button.setText("搜索")
        QMessageBox.critical(self, "错误", f"搜索失败: {error_message}")


class FloatingTip(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
           background-color: rgba(45, 45, 45, 0.95);
           color: white;
           border: 1px solid #3d3d3d;
           padding: 8px 12px;
           border-radius: 4px;
       """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()

        # 动画效果
        self.opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        self.anim = QPropertyAnimation(self.opacity, b"opacity")
        self.anim.setDuration(200)  # 200ms渐变

        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self.start_fade)

    def showTip(self, text, pos, duration=3000):
        self.setText(text)
        self.adjustSize()

        self.move(pos.x() - 250, pos.y() - 90)

        # 重置并显示
        self.opacity.setOpacity(1)
        self.show()

        # 设置定时器
        self.fade_timer.start(duration)

    def start_fade(self):
        self.fade_timer.stop()
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.start()
        self.anim.finished.connect(self.hide)