#!/usr/bin/env python3

"""
Jarvis - 个人智能助手系统
基于钢铁侠电影中的 J.A.R.V.I.S. (Just A Rather Very Intelligent System)
"""
from config import DEFAULT_AI_MODEL
from ai_models import DeepseekAI, GeminiAI

class Jarvis:
    def __init__(self, ai_model: str = DEFAULT_AI_MODEL):
        """
        初始化 Jarvis 系统
        
        Args:
            ai_model: 选择使用的AI模型 ('deepseek' 或 'gemini')
        """
        self.name = "Jarvis"
        self.ai_model = self._initialize_ai_model(ai_model)
    
    def _initialize_ai_model(self, model_name: str):
        """
        初始化选择的AI模型
        
        Args:
            model_name: AI模型名称
            
        Returns:
            BaseAIModel: AI模型实例
        """
        if model_name == "deepseek":
            return DeepseekAI()
        elif model_name == "gemini":
            return GeminiAI()
        else:
            raise ValueError(f"不支持的AI模型: {model_name}")
    
    def greet(self):
        """Jarvis 的问候语"""
        print(f"Hello world! 我是 {self.name}, 很高兴为您服务。")
    
    def chat(self, message: str) -> str:
        """
        与AI模型对话
        
        Args:
            message: 用户输入的消息
            
        Returns:
            str: AI的回复
        """
        try:
            response = self.ai_model.generate_response(message)
            return response
        except Exception as e:
            return f"抱歉，处理您的请求时出现错误: {str(e)}"

def main():
    """主程序入口"""
    # 默认使用 Deepseek
    jarvis = Jarvis()
    jarvis.greet()
    
    # 简单的对话循环
    while True:
        user_input = input("\n请输入您的问题 (输入 'quit' 退出): ")
        if user_input.lower() == 'quit':
            print("再见！")
            break
        
        response = jarvis.chat(user_input)
        print(f"\nJarvis: {response}")

if __name__ == "__main__":
    main() 