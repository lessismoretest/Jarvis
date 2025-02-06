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

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger 