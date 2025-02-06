"""
AI模型模块 - 处理与不同AI模型的交互
"""
from abc import ABC, abstractmethod
import google.generativeai as genai
from openai import OpenAI
from config import AI_CONFIG

class BaseAIModel(ABC):
    """AI模型的基类"""
    
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """生成回复的抽象方法"""
        pass

class DeepseekAI(BaseAIModel):
    """Deepseek AI模型实现"""
    
    def __init__(self):
        """初始化Deepseek客户端"""
        api_key = AI_CONFIG["deepseek"]["api_key"]
        api_base = AI_CONFIG["deepseek"]["api_base"]
        
        if not api_key or not api_base:
            raise ValueError("请在 .env 文件中设置 DEEPSEEK_API_KEY 和 DEEPSEEK_API_BASE")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )
    
    def generate_response(self, prompt: str) -> str:
        """
        使用Deepseek生成回复
        
        Args:
            prompt: 用户输入的提示
            
        Returns:
            str: AI的回复
        """
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

class GeminiAI(BaseAIModel):
    """Gemini AI模型实现"""
    
    def __init__(self):
        """初始化Gemini客户端"""
        api_key = AI_CONFIG["gemini"]["api_key"]
        
        if not api_key:
            raise ValueError("请在 .env 文件中设置 GEMINI_API_KEY")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_response(self, prompt: str) -> str:
        """
        使用Gemini生成回复
        
        Args:
            prompt: 用户输入的提示
            
        Returns:
            str: AI的回复
        """
        response = self.model.generate_content(prompt)
        return response.text 