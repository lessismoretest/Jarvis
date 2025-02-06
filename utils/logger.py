"""
日志配置模块
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 创建logs目录
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 生成日志文件名，包含日期
LOG_FILE = os.path.join(LOG_DIR, f"jarvis_{datetime.now().strftime('%Y%m%d')}.log")

class ConsoleLogFilter(logging.Filter):
    """控制台日志过滤器"""
    def filter(self, record):
        # 过滤语音合成相关的日志
        if record.name == "speech.synthesizer" and (
            "开始转换文字为语音" in record.msg or 
            "语音生成完成" in record.msg
        ):
            return False
            
        # 过滤AI响应的重复显示
        if record.name == "__main__" and (
            "AI响应:" in record.msg or
            "收到用户输入:" in record.msg
        ):
            return False
            
        # 过滤数据库的一些日志
        if record.name == "utils.database" and (
            "数据库连接成功" in record.msg or
            "数据库连接已关闭" in record.msg or
            "对话记录已保存" in record.msg
        ):
            return False
            
        # 过滤语音识别的一些日志
        if record.name == "speech.recognizer" and (
            "删除临时文件" in record.msg
        ):
            return False
            
        return True

def setup_logger(name: str) -> logging.Logger:
    """
    配置并返回logger实例
    
    Args:
        name: logger名称
        
    Returns:
        logging.Logger: 配置好的logger实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 配置文件处理器 - 10MB大小，保留5个备份
    file_handler = RotatingFileHandler(
        LOG_FILE, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 添加过滤器
    console_filter = ConsoleLogFilter()
    console_handler.addFilter(console_filter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger 