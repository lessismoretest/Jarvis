"""
数据库模块 - 处理与MySQL数据库的交互
"""
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger(__name__)

class Database:
    def __init__(self):
        """初始化数据库连接"""
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '88888888',
            'database': 'jarvis_chat'
        }
        self.connection = None
        self.create_database()
        self.create_tables()
    
    def create_database(self):
        """创建数据库"""
        try:
            conn = mysql.connector.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_config['database']}")
            logger.info(f"数据库 {self.db_config['database']} 创建成功")
        except Error as e:
            logger.error(f"创建数据库失败: {str(e)}")
            raise
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def create_tables(self):
        """创建必要的表"""
        try:
            self.connect()
            cursor = self.connection.cursor()
            
            # 创建对话历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(50),
                    timestamp DATETIME,
                    input_type ENUM('text', 'voice'),
                    user_input TEXT,
                    ai_response TEXT,
                    model_used VARCHAR(50),
                    response_time FLOAT
                )
            """)
            
            self.connection.commit()
            logger.info("数据表创建成功")
            
        except Error as e:
            logger.error(f"创建表失败: {str(e)}")
            raise
        finally:
            self.disconnect()
    
    def connect(self):
        """连接到数据库"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**self.db_config)
                logger.debug("数据库连接成功")
        except Error as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.debug("数据库连接已关闭")
    
    def save_chat(self, session_id: str, input_type: str, user_input: str, 
                 ai_response: str, model_used: str, response_time: float):
        """
        保存对话记录
        
        Args:
            session_id: 会话ID
            input_type: 输入类型 ('text' 或 'voice')
            user_input: 用户输入
            ai_response: AI响应
            model_used: 使用的AI模型
            response_time: 响应时间（秒）
        """
        try:
            self.connect()
            cursor = self.connection.cursor()
            
            query = """
                INSERT INTO chat_history 
                (session_id, timestamp, input_type, user_input, ai_response, model_used, response_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                session_id,
                datetime.now(),
                input_type,
                user_input,
                ai_response,
                model_used,
                response_time
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            logger.info(f"对话记录已保存，ID: {cursor.lastrowid}")
            
        except Error as e:
            logger.error(f"保存对话记录失败: {str(e)}")
            raise
        finally:
            self.disconnect()

    def get_chat_history(self, session_id: str = None, limit: int = 10) -> list:
        """
        获取对话历史记录
        
        Args:
            session_id: 可选的会话ID过滤
            limit: 返回的记录数量限制
            
        Returns:
            list: 对话记录列表
        """
        try:
            self.connect()
            cursor = self.connection.cursor(dictionary=True)
            
            if session_id:
                query = """
                    SELECT * FROM chat_history 
                    WHERE session_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """
                cursor.execute(query, (session_id, limit))
            else:
                query = """
                    SELECT * FROM chat_history 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
            
            results = cursor.fetchall()
            logger.debug(f"获取到 {len(results)} 条对话记录")
            return results
            
        except Error as e:
            logger.error(f"获取对话记录失败: {str(e)}")
            raise
        finally:
            self.disconnect()

    def get_session_stats(self) -> dict:
        """
        获取会话统计信息
        
        Returns:
            dict: 包含统计信息的字典
        """
        try:
            self.connect()
            cursor = self.connection.cursor(dictionary=True)
            
            # 获取总体统计
            stats = {}
            
            # 总对话数
            cursor.execute("SELECT COUNT(*) as total FROM chat_history")
            stats.update(cursor.fetchone())
            
            # 按输入类型统计
            cursor.execute("""
                SELECT input_type, COUNT(*) as count 
                FROM chat_history 
                GROUP BY input_type
            """)
            stats['input_types'] = {row['input_type']: row['count'] 
                                  for row in cursor.fetchall()}
            
            # 平均响应时间
            cursor.execute("""
                SELECT AVG(response_time) as avg_response_time 
                FROM chat_history
            """)
            stats.update(cursor.fetchone())
            
            # 使用的模型统计
            cursor.execute("""
                SELECT model_used, COUNT(*) as count 
                FROM chat_history 
                GROUP BY model_used
            """)
            stats['models'] = {row['model_used']: row['count'] 
                             for row in cursor.fetchall()}
            
            logger.debug("统计信息获取成功")
            return stats
            
        except Error as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            raise
        finally:
            self.disconnect()

    def clear_history(self, session_id: str = None):
        """
        清除对话历史
        
        Args:
            session_id: 可选的会话ID，如果提供则只清除该会话的记录
        """
        try:
            self.connect()
            cursor = self.connection.cursor()
            
            if session_id:
                query = "DELETE FROM chat_history WHERE session_id = %s"
                cursor.execute(query, (session_id,))
            else:
                cursor.execute("DELETE FROM chat_history")
            
            self.connection.commit()
            logger.info(f"已清除{'指定会话' if session_id else '所有'}的对话记录")
            
        except Error as e:
            logger.error(f"清除对话记录失败: {str(e)}")
            raise
        finally:
            self.disconnect() 