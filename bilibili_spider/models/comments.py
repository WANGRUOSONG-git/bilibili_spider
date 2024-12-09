"""
评论数据模型
"""
from datetime import datetime


class Comment:
    """
    评论数据模型类
    """

    def __init__(self, video_id, video_title, comment_id, user_name, content,
                 publish_time, like_count, replies=None):
        """初始化评论对象"""
        self.video_id = video_id
        self.video_title = video_title
        self.comment_id = comment_id
        self.user_name = user_name
        self.content = content
        self.publish_time = publish_time
        self.like_count = like_count
        self.replies = replies or []