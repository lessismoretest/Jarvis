"""
配置文件 - 存储各种API密钥和设置
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# AI模型配置
AI_CONFIG = {
    "deepseek": {
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "api_base": os.getenv("DEEPSEEK_API_BASE"),
    },
    "gemini": {
        "api_key": os.getenv("GEMINI_API_KEY"),
    }
}

# 默认使用的AI模型
DEFAULT_AI_MODEL = "gemini" 