"""
语音合成模块 - 使用Edge-TTS进行文字转语音
"""
import asyncio
from pathlib import Path
import edge_tts
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EdgeTTSSynthesizer:
    """Edge TTS语音合成器"""
    
    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural"):
        """
        初始化Edge TTS
        
        Args:
            voice: 声音选项，默认使用中文女声
        """
        self.voice = voice
        self.enabled = True  # 添加enabled标志
        self.output_dir = Path("temp")
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"初始化Edge TTS，使用声音: {voice}")
    
    async def _generate_speech(self, text: str, output_file: str):
        """
        生成语音文件
        
        Args:
            text: 要转换的文本
            output_file: 输出文件路径
        """
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_file)
    
    def text_to_speech(self, text: str, output_file: str = None) -> str:
        """
        将文字转换为语音
        
        Args:
            text: 要转换的文本
            output_file: 可选的输出文件路径，如果不指定则自动生成
            
        Returns:
            str: 生成的音频文件路径，如果语音功能关闭则返回None
        """
        if not self.enabled:
            logger.info("语音功能已关闭，跳过语音生成")
            return None
            
        try:
            logger.info(f"开始转换文字为语音: {text}")
            
            if output_file is None:
                output_file = str(self.output_dir / "response.mp3")
            
            # 运行异步任务
            asyncio.run(self._generate_speech(text, output_file))
            
            logger.info(f"语音生成完成: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"语音生成失败: {str(e)}")
            raise 