"""
语音识别模块 - 使用Whisper模型进行语音转文字
"""
import os
import tempfile
from pathlib import Path
import sounddevice as sd
import soundfile as sf
import numpy as np
import whisper
from utils.logger import setup_logger

logger = setup_logger(__name__)

class WhisperRecognizer:
    """Whisper语音识别器"""
    
    def __init__(self, model_name: str = "base"):
        """
        初始化Whisper模型
        
        Args:
            model_name: 模型名称 ("tiny", "base", "small", "medium", "large")
        """
        logger.info(f"正在加载Whisper {model_name}模型...")
        self.model = whisper.load_model(model_name)
        logger.info("Whisper模型加载完成")
        
        # 录音设置
        self.sample_rate = 16000
        self.channels = 1
    
    def record_audio(self, duration: int = 5) -> str:
        """
        录制音频
        
        Args:
            duration: 录制时长（秒）
            
        Returns:
            str: 临时音频文件路径
        """
        logger.info(f"开始录音，持续{duration}秒...")
        
        # 录制音频
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.float32
        )
        sd.wait()
        
        # 保存到临时文件
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        temp_file = temp_dir / "temp_recording.wav"
        sf.write(str(temp_file), recording, self.sample_rate)
        
        logger.info(f"录音完成，保存至: {temp_file}")
        return str(temp_file)
    
    def transcribe_audio(self, audio_path: str) -> str:
        """
        将音频转换为文字
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            str: 识别出的文字
        """
        try:
            logger.info(f"开始转写音频: {audio_path}")
            result = self.model.transcribe(audio_path)
            text = result["text"].strip()
            logger.info(f"音频转写完成: {text}")
            return text
        except Exception as e:
            logger.error(f"音频转写失败: {str(e)}")
            raise
        finally:
            # 清理临时文件
            if audio_path.startswith(str(Path("temp"))):
                try:
                    os.remove(audio_path)
                    logger.debug(f"已删除临时音频文件: {audio_path}")
                except Exception as e:
                    logger.warning(f"删除临时文件失败: {str(e)}") 