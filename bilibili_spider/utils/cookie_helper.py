# bilibili_spider/utils/cookie_helper.py

from PyQt6.QtCore import QObject, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import threading
import logging


class CookieHelper(QObject):
    """Cookie获取工具类"""
    cookie_ready = pyqtSignal(str)

    def __init__(self, config, db_handler):
        super().__init__()
        self.config = config
        self.db_handler = db_handler
        self.driver = None
        self.is_running = False

        # 检查浏览器环境并启动
        if self.check_browser_environment():
            self.start_browser_thread()

    def check_browser_environment(self):
        """检查浏览器环境"""
        try:
            # 先尝试Edge浏览器
            from selenium.webdriver.edge.options import Options as EdgeOptions
            self.browser_type = 'edge'
            return True
        except:
            try:
                # 再尝试Chrome浏览器
                from selenium.webdriver.chrome.options import Options as ChromeOptions
                self.browser_type = 'chrome'
                return True
            except:
                logging.error("未检测到可用的浏览器")
                return False

    def start_browser_thread(self):
        """在新线程中启动浏览器"""
        self.is_running = True
        threading.Thread(target=self.run_browser, daemon=True).start()

    def run_browser(self):
        """运行浏览器并监视Cookie"""
        try:
            # 根据检测结果创建对应的浏览器实例
            if self.browser_type == 'edge':
                from selenium.webdriver.edge.options import Options
                options = Options()
                options.add_argument('--start-maximized')
                self.driver = webdriver.Edge(options=options)
            else:
                from selenium.webdriver.chrome.options import Options
                options = Options()
                options.add_argument('--start-maximized')
                self.driver = webdriver.Chrome(options=options)

            # 访问B站首页
            self.driver.get('https://www.bilibili.com')

            try:
                # 等待并点击登录按钮
                wait = WebDriverWait(self.driver, 10)
                login_button = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "header-login-entry"))
                )
                login_button.click()

                # 开始检查Cookie
                while self.is_running:
                    cookies = self.driver.get_cookies()
                    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

                    required_fields = ['SESSDATA', 'bili_jct', 'DedeUserID']
                    if all(field in cookie_dict for field in required_fields):
                        cookie_str = '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])

                        if self.config.validate_cookie(cookie_str):
                            self.cookie_ready.emit(cookie_str)
                            break

                    import time
                    time.sleep(2)

            except TimeoutException:
                logging.error("加载登录页面失败")

        except Exception as e:
            logging.error(f"启动浏览器失败: {str(e)}")

        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        self.is_running = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None