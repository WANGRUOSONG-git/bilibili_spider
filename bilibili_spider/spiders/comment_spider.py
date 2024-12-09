# bilibili_spider/spiders/comment_spider.py

import re
import time
import random
import logging
import requests
from datetime import datetime
import json


class BilibiliSpider:
    """B站评论爬虫实现类"""

    def __init__(self, config):
        """初始化爬虫实例

        @param {Config} config - 配置对象
        """
        self.headers = config.get_headers()
        self.config = config

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def extract_video_id(self, url):
        """从URL中提取视频ID

        @param {string} url - 视频URL
        @return {string} - 视频ID
        """
        patterns = [
            r'BV\w{10}',  # BV号格式
            r'av\d+'  # av号格式
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group()
        return None

    def get_api_url(self, video_id, page=1):
        """获取评论API的URL

        @param {string} video_id - 视频ID
        @param {int} page - 页码
        @return {string} - API URL
        """
        if video_id.startswith('BV'):
            self.logger.info(f"正在处理BV号: {video_id}")
            try:
                view_url = f'https://api.bilibili.com/x/web-interface/view?bvid={video_id}'
                response = requests.get(view_url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                if data['code'] == 0:
                    aid = data['data']['aid']
                    self.logger.info(f"获取到aid: {aid}")
                else:
                    self.logger.error(f"获取aid失败: {data['message']}")
                    return None
            except Exception as e:
                self.logger.error(f"转换BV号失败: {str(e)}")
                return None
        elif video_id.startswith('av'):
            aid = video_id[2:]
        else:
            aid = video_id

        return f'http://api.bilibili.com/x/v2/reply?pn={page}&type=1&oid={aid}&sort=2'

    def crawl_video_comments(self, url, max_pages=10):
        """爬取视频评论"""
        self.logger.info(f"开始爬取视频评论: {url}")
        video_id = self.extract_video_id(url)
        if not video_id:
            self.logger.error("无法从URL中提取视频ID")
            return []

        # 获取视频标题
        video_title = ""
        try:
            if video_id.startswith('BV'):
                view_url = f'https://api.bilibili.com/x/web-interface/view?bvid={video_id}'
            else:
                view_url = f'https://api.bilibili.com/x/web-interface/view?aid={video_id.lstrip("av")}'

            response = requests.get(view_url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            if data['code'] == 0:
                video_title = data['data']['title']
                self.logger.info(f"获取到视频标题: {video_title}")
        except Exception as e:
            self.logger.error(f"获取视频标题失败: {str(e)}")
            video_title = "未知标题"

        all_comments = []
        current_page = 1

        while current_page <= max_pages:
            try:
                self.logger.info(f"正在爬取第 {current_page} 页")

                api_url = self.get_api_url(video_id, current_page)
                if not api_url:
                    break

                response = requests.get(api_url, headers=self.headers)
                response.raise_for_status()
                data = response.json()

                if data['code'] != 0:
                    self.logger.error(f"API返回错误: {data.get('message', '未知错误')}")
                    break

                replies = data['data'].get('replies', [])
                if not replies:
                    self.logger.info("没有更多评论了")
                    break

                for reply in replies:
                    try:
                        comment_data = {
                            'comment_id': str(reply['rpid']),
                            'video_id': video_id,
                            'video_title': video_title,
                            'user_name': reply['member']['uname'],
                            'content': reply['content']['message'],
                            'publish_time': datetime.fromtimestamp(
                                reply['ctime']
                            ).strftime('%Y-%m-%d %H:%M:%S'),
                            'like_count': reply['like'],
                            'replies': []
                        }

                        # 处理子回复
                        if reply.get('replies'):
                            for sub_reply in reply['replies']:
                                reply_data = {
                                    'user_name': sub_reply['member']['uname'],
                                    'content': sub_reply['content']['message'],
                                    'time': datetime.fromtimestamp(
                                        sub_reply['ctime']
                                    ).strftime('%Y-%m-%d %H:%M:%S')
                                }
                                comment_data['replies'].append(reply_data)

                        all_comments.append(comment_data)
                    except Exception as e:
                        self.logger.error(f"处理评论数据失败: {str(e)}")
                        continue

                self.logger.info(f"第 {current_page} 页爬取完成，获取到 {len(replies)} 条评论")

                delay = random.uniform(self.config.DELAY_MIN, self.config.DELAY_MAX)
                self.logger.debug(f"等待 {delay:.2f} 秒后继续...")
                time.sleep(delay)

                current_page += 1

            except requests.exceptions.RequestException as e:
                self.logger.error(f"网络请求失败: {str(e)}")
                break
            except json.JSONDecodeError as e:
                self.logger.error(f"解析响应数据失败: {str(e)}")
                break
            except Exception as e:
                self.logger.error(f"爬取过程出错: {str(e)}")
                break

        self.logger.info(f"爬取完成，共获取 {len(all_comments)} 条评论")
        return all_comments

    def test_cookie(self):
        """测试Cookie是否有效

        @return {bool} - Cookie是否有效
        """
        try:
            test_url = 'http://api.bilibili.com/x/web-interface/nav'
            response = requests.get(test_url, headers=self.headers)
            data = response.json()

            if data['code'] == 0:
                user_name = data['data'].get('uname', '')
                self.logger.info(f"Cookie有效，当前用户: {user_name}")
                return True
            else:
                self.logger.warning(f"Cookie无效: {data.get('message', '未知错误')}")
                return False

        except Exception as e:
            self.logger.error(f"测试Cookie失败: {str(e)}")
            return False