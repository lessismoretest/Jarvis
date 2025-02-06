#!/usr/bin/env python3

"""
Jarvis - 个人智能助手系统
基于钢铁侠电影中的 J.A.R.V.I.S. (Just A Rather Very Intelligent System)
"""
from config import DEFAULT_AI_MODEL
from ai_models import DeepseekAI, GeminiAI
from speech.recognizer import WhisperRecognizer
from utils.logger import setup_logger

# 创建logger实例
logger = setup_logger(__name__)

class Jarvis:
    def __init__(self, ai_model: str = DEFAULT_AI_MODEL):
        """
        初始化 Jarvis 系统
        
        Args:
            ai_model: 选择使用的AI模型 ('deepseek' 或 'gemini')
        """
        self.name = "Jarvis"
        logger.info(f"正在初始化 Jarvis，使用 {ai_model} 模型")
        self.ai_model = self._initialize_ai_model(ai_model)
        self.speech_recognizer = WhisperRecognizer()
        logger.info("Jarvis 初始化完成")
    
    def _initialize_ai_model(self, model_name: str):
        """
        初始化选择的AI模型
        
        Args:
            model_name: AI模型名称
            
        Returns:
            BaseAIModel: AI模型实例
        """
        try:
            if model_name == "deepseek":
                return DeepseekAI()
            elif model_name == "gemini":
                return GeminiAI()
            else:
                error_msg = f"不支持的AI模型: {model_name}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        except Exception as e:
            logger.error(f"初始化AI模型时出错: {str(e)}")
            raise
    
    def greet(self):
        """Jarvis 的问候语"""
        message = f"Hello world! 我是 {self.name}, 很高兴为您服务。"
        print(message)
        logger.info("Jarvis 已启动并发送问候")
    
    def chat(self, message: str) -> str:
        """
        与AI模型对话
        
        Args:
            message: 用户输入的消息
            
        Returns:
            str: AI的回复
        """
        try:
            logger.info(f"收到用户输入: {message}")
            response = self.ai_model.generate_response(message)
            logger.info(f"AI响应: {response}")
            return response
        except Exception as e:
            error_msg = f"处理请求时出错: {str(e)}"
            logger.error(error_msg)
            return f"抱歉，{error_msg}"

    def listen(self, duration: int = 5) -> str:
        """
        监听用户语音输入
        
        Args:
            duration: 录音时长（秒）
            
        Returns:
            str: 识别出的文字
        """
        try:
            audio_path = self.speech_recognizer.record_audio(duration)
            text = self.speech_recognizer.transcribe_audio(audio_path)
            return text
        except Exception as e:
            logger.error(f"语音识别失败: {str(e)}")
            return ""

def main():
    """主程序入口"""
    try:
        logger.info("启动 Jarvis 系统")
        jarvis = Jarvis()
        jarvis.greet()
        
        while True:
            choice = input("\n选择输入方式 (1: 文字, 2: 语音, q: 退出): ")
            
            if choice.lower() == 'q':
                logger.info("用户请求退出")
                print("再见！")
                break
            
            if choice == '1':
                user_input = input("\n请输入您的问题: ")
            elif choice == '2':
                print("\n请说话（5秒）...")
                user_input = jarvis.listen()
                print(f"识别结果: {user_input}")
            else:
                print("无效的选择，请重试")
                continue
            
            if user_input:
                response = jarvis.chat(user_input)
                print(f"\nJarvis: {response}")
            
    except Exception as e:
        logger.error(f"系统运行时出错: {str(e)}")
        raise
    finally:
        logger.info("Jarvis 系统已关闭")

if __name__ == "__main__":
    main() 