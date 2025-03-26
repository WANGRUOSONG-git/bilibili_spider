# bilibili_spider/utils/db_handler.py

"""数据库操作工具"""

import csv
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager


class DatabaseHandler:
    """数据库处理类，负责评论数据和Cookie管理"""

    def __init__(self, db_file):
        """初始化数据库处理器

        @param {string} db_file - 数据库文件路径
        """
        self.db_file = db_file
        self.logger = self._setup_logger()
        self.init_db()

    @contextmanager
    def get_connection(self):
        """安全获取数据库连接"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            yield conn
        finally:
            if conn:
                conn.close()

    def _setup_logger(self):
        """设置日志记录器

        @return {Logger} - 配置好的日志记录器
        """
        logger = logging.getLogger('BilibiliSpider')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def init_db(self):
        """初始化数据库结构"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 创建评论表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        video_id TEXT NOT NULL,
                        video_title TEXT NOT NULL,
                        comment_id TEXT NOT NULL UNIQUE,
                        user_name TEXT NOT NULL, 
                        content TEXT NOT NULL,
                        publish_time TEXT NOT NULL,
                        like_count INTEGER DEFAULT 0,
                        replies TEXT,
                        create_time TEXT NOT NULL,
                        update_time TEXT NOT NULL
                    )
                ''')

                # Cookie管理表保持不变
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cookie_manager (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cookie TEXT NOT NULL,
                        create_time TEXT NOT NULL,
                        expire_time TEXT NOT NULL,
                        last_check_time TEXT NOT NULL,
                        is_valid INTEGER DEFAULT 1,
                        UNIQUE(cookie)
                    )
                ''')

                conn.commit()
                self.logger.info("数据库表结构初始化成功")

        except Exception as e:
            self.logger.error(f"初始化数据库失败: {str(e)}")
            raise

    def save_cookie(self, cookie, expire_days=30):
        """保存Cookie信息

        @param {string} cookie - Cookie字符串
        @param {int} expire_days - Cookie有效期(天数)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 将所有已有Cookie标记为无效
                cursor.execute('UPDATE cookie_manager SET is_valid = 0')

                # 获取当前时间和过期时间
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                expire_time = (datetime.now() + timedelta(days=expire_days)).strftime('%Y-%m-%d %H:%M:%S')

                # 插入新Cookie
                cursor.execute('''
                    INSERT OR REPLACE INTO cookie_manager (
                        cookie, create_time, expire_time, last_check_time, is_valid
                    ) VALUES (?, ?, ?, ?, 1)
                ''', (cookie, current_time, expire_time, current_time))

                conn.commit()
                self.logger.info("Cookie已成功保存到数据库")

        except Exception as e:
            self.logger.error(f"保存Cookie失败: {str(e)}")
            raise

    def get_valid_cookie(self):
        """获取有效的Cookie信息

        @return {tuple} - (cookie字符串, 是否需要更新)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 查询最新的有效Cookie
                cursor.execute('''
                    SELECT cookie, expire_time, create_time 
                    FROM cookie_manager 
                    WHERE is_valid = 1 
                    ORDER BY create_time DESC 
                    LIMIT 1
                ''')

                result = cursor.fetchone()
                if not result:
                    self.logger.info("数据库中未找到有效的Cookie")
                    return None, True

                cookie, expire_time, create_time = result
                self.logger.info(f"找到Cookie记录，创建时间: {create_time}")

                # 转换时间并检查是否过期
                expire_time = datetime.strptime(expire_time, '%Y-%m-%d %H:%M:%S')
                current_time = datetime.now()
                need_update = current_time + timedelta(days=3) > expire_time

                if cookie:
                    self.logger.info("成功获取有效的Cookie")

                return cookie, need_update

        except Exception as e:
            self.logger.error(f"获取Cookie失败: {str(e)}")
            raise

    def clear_cookies(self):
        """清除所有Cookie记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('DELETE FROM cookie_manager')
                conn.commit()
                self.logger.info("已清除所有Cookie记录")

        except Exception as e:
            self.logger.error(f"清除Cookie失败: {str(e)}")
            raise

    def save_comment(self, comment):
        """保存或更新评论数据"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # 检查评论是否已存在
                cursor.execute('SELECT id FROM comments WHERE comment_id = ?', (comment.comment_id,))
                exists = cursor.fetchone()

                if exists:
                    # 更新已存在的评论
                    cursor.execute('''
                        UPDATE comments 
                        SET user_name = ?,
                            content = ?,
                            publish_time = ?,
                            like_count = ?,
                            replies = ?,
                            video_title = ?,
                            update_time = ?
                        WHERE comment_id = ?
                    ''', (
                        comment.user_name,
                        comment.content,
                        comment.publish_time,
                        comment.like_count,
                        json.dumps(comment.replies, ensure_ascii=False),
                        comment.video_title,
                        current_time,
                        comment.comment_id
                    ))
                    conn.commit()
                    return 2  # 更新成功
                else:
                    # 插入新评论
                    cursor.execute('''
                        INSERT INTO comments (
                            video_id, video_title, comment_id, user_name, content,
                            publish_time, like_count, replies, create_time, update_time
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        comment.video_id,
                        comment.video_title,
                        comment.comment_id,
                        comment.user_name,
                        comment.content,
                        comment.publish_time,
                        comment.like_count,
                        json.dumps(comment.replies, ensure_ascii=False),
                        current_time,
                        current_time
                    ))
                    conn.commit()
                    return 1  # 新增成功

        except Exception as e:
            self.logger.error(f"保存评论失败: {str(e)}")
            return 0  # 保存失败

    def query_comments_batch(self, query_type, search_text='', batch_size=100, offset=0, sort_by='publish_time',
                             sort_order='DESC'):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                base_sql = """
                   SELECT video_id, video_title, user_name, content, publish_time, 
                          like_count, replies, update_time 
                   FROM comments 
                   {where_clause}
                   ORDER BY {sort_field} {sort_order}
                   LIMIT ? OFFSET ?
               """

                valid_sort_fields = {
                    'publish_time': 'publish_time',
                    'like_count': 'like_count',
                    'replies': 'json_array_length(replies)'
                }

                sort_field = valid_sort_fields.get(sort_by, 'publish_time')
                sort_order = 'DESC' if sort_order.upper() == 'DESC' else 'ASC'

                where_clause = {
                    '2': "WHERE video_id LIKE ?",  # 按视频ID搜索
                    '3': "WHERE video_title LIKE ?",  # 按视频标题搜索
                    '4': "WHERE user_name LIKE ?",  # 按用户名搜索
                    '5': "WHERE content LIKE ?"  # 按评论内容搜索
                }.get(query_type, "")

                if where_clause:
                    params = (f'%{search_text}%', batch_size, offset)
                else:
                    params = (batch_size, offset)

                sql = base_sql.format(
                    where_clause=where_clause,
                    sort_field=sort_field,
                    sort_order=sort_order
                )

                cursor.execute(sql, params)
                results = cursor.fetchall()
                return results

        except Exception as e:
            self.logger.error(f"分批查询评论失败: {str(e)}")
            raise

    def clear_database(self):
        """清空数据库中的评论数据"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('DELETE FROM comments')
                cursor.execute('DELETE FROM sqlite_sequence WHERE name="comments"')

                conn.commit()
                self.logger.info("数据库评论数据已清空")

        except Exception as e:
            self.logger.error(f"清空数据库失败: {str(e)}")
            raise

    def get_statistics(self):
        """获取数据库统计信息

        @return {dict} - 包含统计信息的字典
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 获取总评论数
                cursor.execute('SELECT COUNT(*) FROM comments')
                total_comments = cursor.fetchone()[0]

                # 获取视频数量
                cursor.execute('SELECT COUNT(DISTINCT video_id) FROM comments')
                total_videos = cursor.fetchone()[0]

                # 获取用户数量
                cursor.execute('SELECT COUNT(DISTINCT user_name) FROM comments')
                total_users = cursor.fetchone()[0]

                # 获取最新评论时间
                cursor.execute('SELECT MAX(create_time) FROM comments')
                latest_comment = cursor.fetchone()[0]

                return {
                    'total_comments': total_comments,
                    'total_videos': total_videos,
                    'total_users': total_users,
                    'latest_comment': latest_comment
                }

        except Exception as e:
            self.logger.error(f"获取统计信息失败: {str(e)}")
            return {
                'total_comments': 0,
                'total_videos': 0,
                'total_users': 0,
                'latest_comment': None
            }

    def get_all_comments(self):
        """获取所有评论数据"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM comments ORDER BY publish_time DESC')
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"获取所有评论失败: {str(e)}")
            raise
    
    
    def export_comments_to_csv(self, file_path):
        """将评论数据导出为CSV文件

        @param {string} file_path - CSV文件的保存路径
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 查询所有评论数据
                cursor.execute('SELECT * FROM comments ORDER BY publish_time DESC')
                results = cursor.fetchall()

                if not results:
                    return

                # 获取表头
                columns = [description[0] for description in cursor.description]

                # 写入CSV文件
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(columns)  # 写入表头

                    for row in results:
                        writer.writerow(row)

        except Exception as e:
            self.logger.error(f"导出CSV文件失败: {str(e)}")
            raise
