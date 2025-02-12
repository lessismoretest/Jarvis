"""
AI模型模块 - 处理与不同AI模型的交互
"""
from abc import ABC, abstractmethod
import google.generativeai as genai 
from openai import OpenAI
from config import AI_CONFIG
from utils.logger import setup_logger

# 创建logger实例
logger = setup_logger(__name__)

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
            logger.error("缺少Deepseek API配置")
            raise ValueError("请在 .env 文件中设置 DEEPSEEK_API_KEY 和 DEEPSEEK_API_BASE")
        
        logger.info("初始化 Deepseek 客户端")
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )
        # 初始化对话消息列表
        self.messages = [
            {"role": "system", "content": "你是一个智能助手，请用简洁友好的方式回答问题。"}
        ]
    
    def generate_response(self, prompt: str) -> str:
        """使用Deepseek生成回复"""
        try:
            logger.debug(f"向Deepseek发送请求: {prompt}")
            
            # 添加用户消息
            self.messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=self.messages,
                temperature=0.7,
                max_tokens=2000,
                stream=False
            )
            
            # 添加错误处理和日志
            if not response or not response.choices:
                raise ValueError("API返回空响应")
            
            result = response.choices[0].message.content.strip()
            
            # 添加助手回复到消息历史
            self.messages.append({"role": "assistant", "content": result})
            
            logger.debug(f"Deepseek响应: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Deepseek API调用失败: {str(e)}")
            raise

class GeminiAI(BaseAIModel):
    """Gemini AI模型实现"""
    
    def __init__(self):
        """初始化Gemini客户端"""
        api_key = AI_CONFIG["gemini"]["api_key"]
        
        if not api_key:
            logger.error("缺少Gemini API配置")
            raise ValueError("请在 .env 文件中设置 GEMINI_API_KEY")
        
        logger.info("初始化 Gemini 客户端")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        # 创建持久化的聊天会话
        self.chat = self.model.start_chat(history=[])
        
        # 用于语音合成的回调函数
        self.tts_callback = None
    
    def set_tts_callback(self, callback):
        """设置语音合成回调函数"""
        self.tts_callback = callback
    
    def _split_into_sentences(self, text: str) -> list:
        """
        将文本分割成句子
        
        Args:
            text: 要分割的文本
            
        Returns:
            list: 句子列表
        """
        # 使用常见的中文和英文标点符号作为分隔符
        delimiters = ['。', '！', '？', '；', '.', '!', '?', ';']
        sentences = []
        current = []
        
        for char in text:
            current.append(char)
            if char in delimiters:
                sentences.append(''.join(current))
                current = []
        
        # 处理最后一个不完整的句子
        if current:
            sentences.append(''.join(current))
        
        return sentences
    
    def generate_response(self, prompt: str) -> str:
        """使用Gemini生成回复（流式输出）"""
        try:
            logger.debug(f"向Gemini发送请求: {prompt}")
            
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE",
                },
            ]
            
            # 使用聊天会话发送消息并获取流式响应
            response = self.chat.send_message(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
                stream=True
            )
            
            # 收集并显示流式响应
            full_response = []
            current_sentence = []
            
            # 创建一个 Live 上下文用于动态更新 Markdown
            from rich.live import Live
            from rich.markdown import Markdown
            from rich.console import Console
            
            console = Console()
            console.print("\nJarvis:")
            
            with Live(console=console, refresh_per_second=4) as live:
                for chunk in response:
                    if chunk.text:
                        full_response.append(chunk.text)
                        current_sentence.append(chunk.text)
                        
                        # 检查是否有完整的句子
                        current_text = ''.join(current_sentence)
                        sentences = self._split_into_sentences(current_text)
                        
                        if len(sentences) > 1:  # 有完整的句子
                            # 保留最后一个不完整的句子
                            current_sentence = [sentences[-1]]
                            
                            # 对完整的句子进行语音合成
                            if self.tts_callback:
                                for sentence in sentences[:-1]:
                                    self.tts_callback(sentence)
                        
                        # 实时更新 Markdown 渲染
                        current_response = "".join(full_response)
                        live.update(Markdown(current_response))
            
            # 处理最后一个句子
            if current_sentence and self.tts_callback:
                last_sentence = ''.join(current_sentence)
                if last_sentence.strip():
                    self.tts_callback(last_sentence)
            
            # 合并所有响应
            result = "".join(full_response).strip()
            logger.debug(f"Gemini响应: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Gemini API调用失败: {str(e)}")
            raise 