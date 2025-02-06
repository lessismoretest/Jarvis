#!/usr/bin/env python3

"""
Jarvis - 个人智能助手系统
基于钢铁侠电影中的 J.A.R.V.I.S. (Just A Rather Very Intelligent System)
"""
import os
from config import DEFAULT_AI_MODEL
from ai_models import DeepseekAI, GeminiAI
from speech.recognizer import WhisperRecognizer
from speech.synthesizer import EdgeTTSSynthesizer
from utils.logger import setup_logger
from utils.database import Database
import uuid
import time

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
        self.speech_synthesizer = EdgeTTSSynthesizer()
        self.db = Database()
        self.session_id = str(uuid.uuid4())  # 为每次运行创建唯一会话ID
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
    
    def speak(self, text: str):
        """
        将文字转换为语音并播放
        
        Args:
            text: 要说出的文字
        """
        try:
            # 生成语音文件
            audio_file = self.speech_synthesizer.text_to_speech(text)
            
            # 使用系统命令播放音频
            if os.name == 'posix':  # Mac/Linux
                os.system(f"afplay {audio_file}")
            else:  # Windows
                os.system(f"start {audio_file}")
                
        except Exception as e:
            logger.error(f"语音播放失败: {str(e)}")
    
    def chat(self, message: str, input_type: str = "text") -> str:
        """
        与AI模型对话并保存记录
        
        Args:
            message: 用户输入的消息
            input_type: 输入类型 ('text' 或 'voice')
        """
        try:
            logger.info(f"收到用户输入: {message}")
            start_time = time.time()
            
            response = self.ai_model.generate_response(message)
            
            # 计算响应时间
            response_time = time.time() - start_time
            
            # 保存对话记录
            self.db.save_chat(
                session_id=self.session_id,
                input_type=input_type,
                user_input=message,
                ai_response=response,
                model_used=self.ai_model.__class__.__name__,
                response_time=response_time
            )
            
            logger.info(f"AI响应: {response}")
            # 添加语音输出
            self.speak(response)
            return response
            
        except Exception as e:
            error_msg = f"处理请求时出错: {str(e)}"
            logger.error(error_msg)
            return f"抱歉，{error_msg}"

    def listen(self) -> str:
        """
        监听用户语音输入并实时识别
        
        Returns:
            str: 完整的识别文字
        """
        try:
            print("\n=== 语音输入模式 ===")
            print("- 开始说话后自动检测")
            print("- 停顿5秒后自动结束")
            print("- 按Ctrl+C可手动结束")
            print("- 实时显示识别结果")
            print("========================")
            
            text = self.speech_recognizer.record_and_transcribe()
            if text:
                print("\n完整识别结果:", text)
                return text
            return ""
        except ValueError as e:
            logger.warning(str(e))
            return ""
        except Exception as e:
            logger.error(f"语音识别失败: {str(e)}")
            return ""

    def show_history(self, limit: int = 10):
        """显示最近的对话历史"""
        try:
            history = self.db.get_chat_history(limit=limit)
            if not history:
                print("\n暂无对话记录")
                return
            
            print("\n=== 最近对话记录 ===")
            for record in history:
                print(f"\n时间: {record['timestamp']}")
                print(f"输入类型: {record['input_type']}")
                print(f"用户: {record['user_input']}")
                print(f"Jarvis: {record['ai_response']}")
                print(f"响应时间: {record['response_time']:.2f}秒")
                print("-" * 50)
        
        except Exception as e:
            logger.error(f"显示对话记录失败: {str(e)}")
            print(f"\n获取对话记录失败: {str(e)}")

    def show_stats(self):
        """显示统计信息"""
        try:
            stats = self.db.get_session_stats()
            print("\n=== 统计信息 ===")
            print(f"总对话数: {stats['total']}")
            print("\n输入类型分布:")
            for type_, count in stats['input_types'].items():
                print(f"- {type_}: {count}")
            print(f"\n平均响应时间: {stats['avg_response_time']:.2f}秒")
            print("\n模型使用统计:")
            for model, count in stats['models'].items():
                print(f"- {model}: {count}")
        
        except Exception as e:
            logger.error(f"显示统计信息失败: {str(e)}")
            print(f"\n获取统计信息失败: {str(e)}")

    def continuous_chat(self, mode: str = "text"):
        """
        持续对话模式
        
        Args:
            mode: 对话模式 ('text' 或 'voice')
        """
        try:
            print("\n=== 持续对话模式 ===")
            print("- 随时按 Ctrl+C 结束对话")
            print("- 直接开始对话即可")
            print("=====================")
            
            while True:
                try:
                    if mode == "text":
                        user_input = input("\n您: ")
                    else:  # voice mode
                        print("\n正在听...")
                        user_input = self.listen()
                        
                    if not user_input:
                        continue
                        
                    response = self.chat(user_input, mode)
                    print(f"\nJarvis: {response}")
                    
                except KeyboardInterrupt:
                    print("\n\n退出持续对话模式")
                    break
                    
        except Exception as e:
            logger.error(f"持续对话模式出错: {str(e)}")
            print(f"\n持续对话模式出错: {str(e)}")

def main():
    """主程序入口"""
    try:
        logger.info("启动 Jarvis 系统")
        jarvis = Jarvis()
        jarvis.greet()
        
        while True:
            print("\n=== Jarvis 命令菜单 ===")
            print("1: 文字输入")
            print("2: 语音输入")
            print("3: 持续文字对话")
            print("4: 持续语音对话")
            print("h: 显示历史记录")
            print("s: 显示统计信息")
            print("c: 清除历史记录")
            print("q: 退出")
            print("=====================")
            
            choice = input("\n请选择: ").lower()
            
            if choice == 'q':
                logger.info("用户请求退出")
                print("再见！")
                break
            elif choice == 'h':
                jarvis.show_history()
                continue
            elif choice == 's':
                jarvis.show_stats()
                continue
            elif choice == 'c':
                confirm = input("确定要清除所有历史记录吗？(y/n): ").lower()
                if confirm == 'y':
                    jarvis.db.clear_history()
                    print("历史记录已清除")
                continue
            
            if choice == '1':
                user_input = input("\n请输入您的问题: ")
                input_type = "text"
                if user_input:
                    response = jarvis.chat(user_input, input_type)
                    print(f"\nJarvis: {response}")
            elif choice == '2':
                user_input = jarvis.listen()
                input_type = "voice"
                if user_input:
                    print("\n正在生成回复...")
                    response = jarvis.chat(user_input, input_type)
                    print(f"\nJarvis: {response}")
                else:
                    print("未能识别语音，请重试")
            elif choice == '3':
                jarvis.continuous_chat(mode="text")
            elif choice == '4':
                jarvis.continuous_chat(mode="voice")
            else:
                print("无效的选择，请重试")
                continue
            
    except Exception as e:
        logger.error(f"系统运行时出错: {str(e)}")
        raise
    finally:
        logger.info("Jarvis 系统已关闭")

if __name__ == "__main__":
    main() 