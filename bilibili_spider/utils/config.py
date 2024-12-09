# bilibili_spider/utils/config.py

import logging
from datetime import datetime


class Config:
    """配置类,管理爬虫所需的各项配置"""

    def __init__(self):
        """初始化配置"""
        # 基础请求头
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'cache-control': 'no-cache',
            'pragma': 'no-cache'
        }

        # 当前使用的headers
        self.headers = self.base_headers.copy()

        # 爬虫配置
        self.DELAY_MIN = 3  # 最小延迟秒数
        self.DELAY_MAX = 7  # 最大延迟秒数
        self.MAX_RETRIES = 3  # 最大重试次数
        self.MAX_PAGES = 10  # 默认最大爬取页数

        # Cookie配置
        self.cookie = None
        self._cookie_valid = False

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def validate_cookie(self, cookie):
        """验证Cookie是否包含必要字段和格式是否正确

        @param {string} cookie - 要验证的Cookie字符串
        @return {bool} - Cookie是否有效
        """
        if not cookie:
            self.logger.info("Cookie为空")
            return False

        try:
            # 解析Cookie字符串为字典
            cookie_dict = {}
            for item in cookie.split(';'):
                if '=' in item:
                    name, value = item.strip().split('=', 1)
                    cookie_dict[name.strip()] = value.strip()

            # 检查必要字段
            required_fields = ['SESSDATA', 'bili_jct', 'DedeUserID']
            for field in required_fields:
                if field not in cookie_dict:
                    self.logger.info(f"缺少必要字段: {field}")
                    return False
                if not cookie_dict[field]:
                    self.logger.info(f"字段值为空: {field}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Cookie验证失败: {str(e)}")
            return False

    def set_cookie(self, cookie):
        """设置Cookie并更新请求头

        @param {string} cookie - Cookie字符串
        @return {bool} - 是否设置成功
        """
        # 如果传入空Cookie，则清除
        if not cookie:
            self.clear_cookie()
            return False

        # 先验证Cookie
        if not self.validate_cookie(cookie):
            return False

        try:
            # 重置headers
            self.headers = self.base_headers.copy()

            # 设置新的Cookie相关字段
            self.cookie = cookie
            self.headers['Cookie'] = cookie
            self.headers['Origin'] = 'https://www.bilibili.com'
            self.headers['Host'] = 'api.bilibili.com'
            self.headers['Referer'] = 'https://www.bilibili.com'

            self._cookie_valid = True
            self.logger.info("Cookie设置成功")
            return True

        except Exception as e:
            self.logger.error(f"设置Cookie失败: {str(e)}")
            self.clear_cookie()
            return False

    def clear_cookie(self):
        """清除Cookie相关的所有信息"""
        self.cookie = None
        self._cookie_valid = False
        self.headers = self.base_headers.copy()
        self.logger.info("Cookie已清除")

    def has_valid_cookie(self):
        """检查是否有有效的Cookie

        @return {bool} - 是否有有效的Cookie
        """
        return bool(self.cookie and self._cookie_valid)

    def get_headers(self):
        """获取请求头

        @return {dict} - 完整的请求头字典
        """
        if not self.has_valid_cookie():
            self.logger.warning("当前没有有效的Cookie")
        return self.headers.copy()