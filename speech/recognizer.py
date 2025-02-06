"""
语音识别模块 - 使用Whisper模型进行语音转文字
"""
import os
from pathlib import Path
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TimeRemainingColumn
)
from rich.console import Console
import sounddevice as sd
import soundfile as sf
import numpy as np
import whisper
from utils.logger import setup_logger
from rich.live import Live
from rich.text import Text
import time

logger = setup_logger(__name__)
console = Console()

class WhisperRecognizer:
    """Whisper语音识别器"""
    
    def __init__(self, model_name: str = "small", language: str = "zh"):
        """
        初始化Whisper模型
        
        Args:
            model_name: 模型名称 ("tiny", "base", "small", "medium", "large")
            language: 主要识别的语言 ("zh", "en", "ja" 等)
        """
        logger.info(f"正在加载Whisper {model_name}模型...")
        self.model = whisper.load_model(model_name)
        self.language = language
        
        # 录音设置
        self.sample_rate = 16000
        self.channels = 1
        
        # 识别设置
        self.decode_options = {
            "language": language,          # 主要语言
            "fp16": False,                # 使用FP16加速（如果GPU支持）
            "without_timestamps": True,    # 不需要时间戳信息
        }
        
        # VAD（语音活动检测）设置
        self.vad_threshold = 0.005       # 降低音量阈值
        self.silence_duration = 5.0      # 停顿检测时长（秒）
        self.min_speech_duration = 0.5   # 最短语音要求
        
        # 调试设置
        self.show_volume = True         # 显示音量
        
        # 实时识别设置
        self.segment_duration = 3.0    # 每个音频段的长度（秒）
        self.buffer = []               # 音频缓冲区
        self.last_text = ""           # 最后一段识别的文本
        
        logger.info(f"Whisper {model_name}模型加载完成，语言设置: {language}")
    
    def _get_volume(self, audio_chunk: np.ndarray) -> float:
        """计算音频块的音量"""
        return float(np.sqrt(np.mean(audio_chunk**2)))
    
    def _is_silent(self, audio_chunk: np.ndarray) -> bool:
        """检测音频片段是否为静音"""
        volume = self._get_volume(audio_chunk)
        return volume < self.vad_threshold
    
    def record_and_transcribe(self) -> str:
        """实时录音并识别"""
        logger.info("开始录音和实时识别...")
        console.print("[bold cyan]请说话[/bold cyan]（静音超过5秒或按Ctrl+C停止）...")
        console.print(f"音量阈值: [yellow]{self.vad_threshold:.4f}[/yellow]")
        
        audio_chunks = []
        silence_counter = 0
        speech_detected = False
        max_volume = 0.0
        segment_samples = int(self.segment_duration * self.sample_rate)
        accumulated_samples = 0
        
        def callback(indata, frames, time, status):
            if status:
                logger.warning(f"录音状态: {status}")
            audio_chunks.append(indata.copy())
            
            nonlocal accumulated_samples
            accumulated_samples += len(indata)
            
            if accumulated_samples >= segment_samples:
                self._process_audio_segment(audio_chunks)
                accumulated_samples = 0
        
        try:
            with Live(auto_refresh=True) as live:
                with sd.InputStream(samplerate=self.sample_rate,
                                  channels=self.channels,
                                  callback=callback,
                                  blocksize=int(self.sample_rate * 0.1)):
                    
                    while True:
                        sd.sleep(50)  # 减少刷新间隔
                        
                        if len(audio_chunks) > 0:
                            current_chunk = audio_chunks[-1]
                            volume = self._get_volume(current_chunk)
                            max_volume = max(max_volume, volume)
                            is_silent = volume < self.vad_threshold
                            
                            # 更新音量显示
                            if self.show_volume:
                                bar_length = 40
                                volume_ratio = volume/max(max_volume, self.vad_threshold)
                                volume_bar = "█" * int(volume_ratio * bar_length)
                                # 根据音量大小改变颜色
                                if volume_ratio > 0.8:
                                    color = "red"
                                elif volume_ratio > 0.4:
                                    color = "yellow"
                                else:
                                    color = "green"
                                
                                # 创建音量显示文本
                                display = Text()
                                display.append("音量: ", style="bold")
                                display.append(f"{volume:.4f}", style="bold")
                                display.append(" [")
                                display.append(volume_bar, style=color)
                                display.append(" " * (bar_length - len(volume_bar)))
                                display.append("] | ")
                                display.append("阈值: ", style="bold")
                                display.append(f"{self.vad_threshold:.4f}", style="cyan")
                                
                                # 更新显示
                                live.update(display)
                            
                            if is_silent:
                                silence_counter += 0.1
                                if speech_detected and silence_counter >= self.silence_duration:
                                    console.print("\n[yellow]检测到静音，停止录音[/yellow]")
                                    break
                            else:
                                silence_counter = 0
                                speech_detected = True
        
        except KeyboardInterrupt:
            logger.info("用户手动停止录音")
            console.print("\n[yellow]录音已停止[/yellow]")
        
        finally:
            console.print()
            if audio_chunks:
                self._process_audio_segment(audio_chunks)
        
        # 返回最后一段识别的文本
        logger.info(f"完整识别结果: {self.last_text}")
        console.print(f"\n[bold green]识别完成![/bold green]")
        return self.last_text  # 返回最后识别的文本
    
    def _process_audio_segment(self, audio_chunks: list):
        """处理音频段并进行识别"""
        if not audio_chunks:
            return
        
        # 合并音频块
        audio_data = np.concatenate(audio_chunks)
        
        # 保存临时文件
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        # 使用时间戳作为文件名，避免冲突
        temp_file = temp_dir / f"segment_{int(time.time() * 1000)}.wav"
        sf.write(str(temp_file), audio_data, self.sample_rate)
        
        try:
            # 识别当前段
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(complete_style="green", finished_style="bright_green"),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=console,
                transient=True
            ) as progress:
                
                task = progress.add_task("[cyan]识别中...", total=100)
                
                def progress_callback(value):
                    progress.update(task, completed=int(value * 100))
                
                result = self.model.transcribe(
                    str(temp_file),
                    **self.decode_options,
                    initial_prompt="这是一段中文对话。",
                    temperature=0.0
                )
                
                # 确保进度条完成
                progress.update(task, completed=100)
            
            text = result["text"].strip()
            if text:
                console.print(f"\n[green]当前识别:[/green] {text}")
                self.last_text = text  # 只保存最新的文本
        
        finally:
            # 清理临时文件
            try:
                os.remove(temp_file)
            except Exception as e:
                logger.warning(f"删除临时文件失败: {str(e)}")
    
    def transcribe_audio(self, audio_path: str) -> str:
        """将音频转换为文字"""
        try:
            logger.info(f"开始转写音频: {audio_path}")
            console.print("\n[bold cyan]正在进行语音识别...[/bold cyan]")
            
            # 使用简单的进度条
            with tqdm(total=100, desc="语音识别", ncols=80) as pbar:
                # 使用转写选项
                result = self.model.transcribe(
                    audio_path,
                    **self.decode_options,
                    initial_prompt="这是一段中文对话。",
                    temperature=0.0,
                )
                pbar.n = 100
                pbar.refresh()
            
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