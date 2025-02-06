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
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
from rich.progress import Progress
from rich.markdown import Markdown
import threading
import queue
import subprocess
from pathlib import Path

# 创建logger实例
logger = setup_logger(__name__)
# 创建rich console实例
console = Console()

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
        
        # 初始化语音合成队列和播放队列
        self.synthesis_queue = queue.Queue()  # 待合成的文本队列
        self.playback_queue = queue.Queue()   # 待播放的音频文件队列
        
        # 创建临时文件目录
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        
        # 启动语音合成线程
        self.synthesis_thread = threading.Thread(target=self._synthesis_worker, daemon=True)
        self.synthesis_thread.start()
        
        # 启动语音播放线程
        self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self.playback_thread.start()
        
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
                model = GeminiAI()
                # 设置语音合成回调
                model.set_tts_callback(self.speak)
                return model
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
        console.print(Panel(message, style="bold green"))
        logger.info("Jarvis 已启动并发送问候")
    
    def _clean_markdown(self, text: str) -> str:
        """
        清理文本中的 Markdown 标记
        
        Args:
            text: 包含 Markdown 标记的文本
            
        Returns:
            str: 清理后的纯文本
        """
        # 移除粗体标记
        text = text.replace('**', '')
        # 移除斜体标记
        text = text.replace('*', '')
        # 移除代码块标记
        text = text.replace('`', '')
        # 移除列表标记
        text = text.replace('- ', '')
        return text
    
    def _synthesis_worker(self):
        """语音合成工作线程"""
        while True:
            try:
                text = self.synthesis_queue.get()
                if text is None:  # 停止信号
                    break
                    
                # 清理 Markdown 标记
                clean_text = self._clean_markdown(text)
                
                # 生成唯一的音频文件名
                audio_file = self.temp_dir / f"response_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}.mp3"
                
                # 生成语音文件
                self.speech_synthesizer.text_to_speech(clean_text, str(audio_file))
                
                # 将音频文件加入播放队列
                self.playback_queue.put(audio_file)
                
            except Exception as e:
                logger.error(f"语音合成失败: {str(e)}")
            finally:
                self.synthesis_queue.task_done()
    
    def _playback_worker(self):
        """语音播放工作线程"""
        while True:
            try:
                audio_file = self.playback_queue.get()
                if audio_file is None:  # 停止信号
                    break
                
                if not audio_file.exists():
                    logger.error(f"音频文件不存在: {audio_file}")
                    continue
                
                try:
                    # 使用 subprocess 播放音频（不阻塞主线程）
                    if os.name == 'posix':  # Mac/Linux
                        subprocess.run(['afplay', str(audio_file)], check=True)
                    else:  # Windows
                        subprocess.run(['start', str(audio_file)], shell=True, check=True)
                finally:
                    # 播放完成后删除临时文件
                    try:
                        audio_file.unlink()
                    except Exception as e:
                        logger.warning(f"删除临时文件失败: {str(e)}")
                    
            except Exception as e:
                logger.error(f"语音播放失败: {str(e)}")
            finally:
                self.playback_queue.task_done()
    
    def speak(self, text: str):
        """
        将文字加入语音合成队列
        
        Args:
            text: 要说出的文字
        """
        try:
            self.synthesis_queue.put(text)
        except Exception as e:
            logger.error(f"添加语音合成任务失败: {str(e)}")
    
    def stop_speaking(self):
        """停止语音合成和播放线程"""
        # 发送停止信号
        self.synthesis_queue.put(None)
        self.playback_queue.put(None)
        
        # 等待线程结束
        self.synthesis_thread.join()
        self.playback_thread.join()
    
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
            
            # 生成响应（AI模型内部会处理流式输出和语音合成）
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
                console.print("\n[yellow]暂无对话记录[/yellow]")
                return
            
            console.print("\n[bold cyan]最近对话记录[/bold cyan]")
            
            for record in history:
                console.print(f"\n[dim]{record['timestamp']}[/dim] ([magenta]{record['input_type']}[/magenta])")
                console.print(f"[green]用户:[/green] {record['user_input']}")
                console.print("[blue]Jarvis:[/blue]")
                console.print(Markdown(record['ai_response']))
                console.print(f"[yellow]响应时间: {record['response_time']:.2f}秒[/yellow]")
                console.print("─" * 50)

        except Exception as e:
            logger.error(f"显示对话记录失败: {str(e)}")
            console.print(f"\n[red]获取对话记录失败: {str(e)}[/red]")

    def show_stats(self):
        """显示统计信息"""
        try:
            stats = self.db.get_session_stats()
            
            table = Table(title="统计信息")
            table.add_column("类别", style="cyan")
            table.add_column("数值", style="yellow")
            
            table.add_row("总对话数", str(stats['total']))
            table.add_row("平均响应时间", f"{stats['avg_response_time']:.2f}秒")
            
            console.print(table)
            
            # 输入类型分布
            type_table = Table(title="输入类型分布")
            type_table.add_column("类型", style="magenta")
            type_table.add_column("数量", style="green")
            
            for type_, count in stats['input_types'].items():
                type_table.add_row(type_, str(count))
            
            console.print(type_table)
            
            # 模型使用统计
            model_table = Table(title="模型使用统计")
            model_table.add_column("模型", style="blue")
            model_table.add_column("使用次数", style="green")
            
            for model, count in stats['models'].items():
                model_table.add_row(model, str(count))
            
            console.print(model_table)
            
        except Exception as e:
            logger.error(f"显示统计信息失败: {str(e)}")
            console.print(f"\n[red]获取统计信息失败: {str(e)}[/red]")

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
                    
                except KeyboardInterrupt:
                    print("\n\n退出持续对话模式")
                    break
                    
        except Exception as e:
            logger.error(f"持续对话模式出错: {str(e)}")
            print(f"\n持续对话模式出错: {str(e)}")

    def cleanup(self):
        """清理资源"""
        try:
            # 停止语音线程
            self.stop_speaking()
            
            # 清理临时文件
            for file in self.temp_dir.glob("response_*.mp3"):
                try:
                    file.unlink()
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {str(e)}")
        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")

def main():
    """主程序入口"""
    jarvis = None
    try:
        logger.info("启动 Jarvis 系统")
        jarvis = Jarvis()
        jarvis.greet()
        
        while True:
            menu = Panel("""
[cyan]1[/cyan]: 文字输入
[cyan]2[/cyan]: 语音输入
[cyan]3[/cyan]: 持续文字对话
[cyan]4[/cyan]: 持续语音对话
[cyan]h[/cyan]: 显示历史记录
[cyan]s[/cyan]: 显示统计信息
[cyan]c[/cyan]: 清除历史记录
[cyan]q[/cyan]: 退出
            """, title="Jarvis 命令菜单", border_style="green")
            
            console.print(menu)
            
            choice = Prompt.ask("\n请选择", default="1").lower()
            
            if choice == 'q':
                logger.info("用户请求退出")
                console.print("[yellow]再见！[/yellow]")
                break
            elif choice == 'h':
                jarvis.show_history()
                continue
            elif choice == 's':
                jarvis.show_stats()
                continue
            elif choice == 'c':
                confirm = Prompt.ask("确定要清除所有历史记录吗？", choices=["y", "n"], default="n")
                if confirm == 'y':
                    jarvis.db.clear_history()
                    console.print("[green]历史记录已清除[/green]")
                continue
            
            if choice == '1':
                user_input = Prompt.ask("\n请输入您的问题")
                input_type = "text"
                if user_input:
                    jarvis.chat(user_input, input_type)
            elif choice == '2':
                user_input = jarvis.listen()
                input_type = "voice"
                if user_input:
                    jarvis.chat(user_input, input_type)
                else:
                    console.print("[red]未能识别语音，请重试[/red]")
            elif choice == '3':
                jarvis.continuous_chat(mode="text")
            elif choice == '4':
                jarvis.continuous_chat(mode="voice")
            else:
                console.print("[red]无效的选择，请重试[/red]")
                continue
            
    except Exception as e:
        logger.error(f"系统运行时出错: {str(e)}")
        console.print(f"[red]系统错误: {str(e)}[/red]")
    finally:
        if jarvis:
            jarvis.cleanup()
        logger.info("Jarvis 系统已关闭")

if __name__ == "__main__":
    main() 