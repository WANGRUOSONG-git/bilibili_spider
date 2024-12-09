# main.py

import sys
import logging
from PyQt6.QtWidgets import QApplication
from bilibili_spider.main_window import MainWindow


def setup_logger():
    logger = logging.getLogger('BilibiliSpider')

    # 检查是否已经有处理器，如果有则不重复添加
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # 防止日志重复输出
    logger.propagate = False
    return logger


def main():
    try:
        logger = setup_logger()
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        logger.info("应用程序启动成功")
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"应用程序启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()