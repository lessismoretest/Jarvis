"""
图像生成模块，使用Replicate API进行AI图像生成
"""
import os
import logging
from pathlib import Path
import replicate
from rich import print
from datetime import datetime
from typing import Literal, Optional, Union, List
from dataclasses import dataclass

# 配置日志
logger = logging.getLogger(__name__)

# 定义支持的模型
ModelType = Literal[
    "stable-diffusion-3.5"  # Stable Diffusion 3.5
]

# 定义支持的宽高比
AspectRatio = Literal[
    "1:1", "16:9", "21:9", "3:2", "2:3",
    "4:5", "5:4", "3:4", "4:3", "9:16", "9:21"
]

# 定义支持的输出格式
OutputFormat = Literal["webp", "jpg", "png"]

@dataclass
class ImageGenerationResult:
    """图像生成结果"""
    local_paths: List[str]  # 本地保存的图片路径
    uris: List[str]         # 原始的URI链接

@dataclass
class ImageGenerationParams:
    """图像生成参数"""
    prompt: str
    cfg: float = 4.5
    seed: Optional[int] = None
    image: Optional[str] = None
    steps: int = 40
    aspect_ratio: AspectRatio = "1:1"
    output_format: OutputFormat = "webp"
    output_quality: int = 90
    prompt_strength: float = 0.85
    negative_prompt: Optional[str] = None
    save_to_local: bool = True  # 是否保存到本地

# 模型映射
MODEL_MAPPING = {
    "stable-diffusion-3.5": "stability-ai/stable-diffusion-3.5-large"
}

# 宽高比映射
ASPECT_RATIO_DIMENSIONS = {
    "1:1": (1024, 1024),
    "16:9": (1024, 576),
    "21:9": (1024, 440),
    "3:2": (1024, 683),
    "2:3": (683, 1024),
    "4:5": (819, 1024),
    "5:4": (1024, 819),
    "3:4": (768, 1024),
    "4:3": (1024, 768),
    "9:16": (576, 1024),
    "9:21": (440, 1024)
}

class ImageGenerator:
    """
    图像生成器类，使用Replicate API生成图像
    """
    def __init__(self):
        """
        初始化图像生成器
        """
        self.output_dir = Path("outputs/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate(
        self, 
        params: Union[ImageGenerationParams, str],
        model_type: ModelType = "stable-diffusion-3.5",
        num_images: int = 1
    ) -> ImageGenerationResult:
        """
        生成图像

        Args:
            params: 图像生成参数，可以是ImageGenerationParams对象或字符串（作为prompt）
            model_type: 模型类型，默认为 "stable-diffusion-3.5"
            num_images: 生成图像数量，默认为 1

        Returns:
            ImageGenerationResult: 包含本地路径和URI的生成结果
        """
        try:
            # 如果params是字符串，将其转换为ImageGenerationParams对象
            if isinstance(params, str):
                params = ImageGenerationParams(prompt=params)
                
            logger.info(f"开始生成图像，使用模型: {model_type}，提示词: {params.prompt}")
            print(f"[bold green]开始生成图像...[/bold green]")
            print(f"[blue]使用模型:[/blue] {model_type}")
            
            # 获取宽高
            width, height = ASPECT_RATIO_DIMENSIONS[params.aspect_ratio]
            
            # 准备输入参数
            input_params = {
                "prompt": params.prompt,
                "num_outputs": num_images,
                "width": width,
                "height": height,
                "num_inference_steps": params.steps,
                "guidance_scale": params.cfg,
                "output_format": params.output_format,
                "quality": params.output_quality
            }
            
            # 添加可选参数
            if params.negative_prompt:
                input_params["negative_prompt"] = params.negative_prompt
            if params.seed is not None:
                input_params["seed"] = params.seed
            if params.image:
                input_params["image"] = params.image
                input_params["prompt_strength"] = params.prompt_strength
                
            # 获取模型ID
            model_id = MODEL_MAPPING[model_type]
            
            # 运行模型
            output = replicate.run(
                model_id,
                input=input_params
            )
            
            # 初始化结果
            image_paths = []
            image_uris = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 处理输出
            for index, item in enumerate(output):
                # 保存URI
                image_uris.append(item)
                
                # 如果需要保存到本地
                if params.save_to_local:
                    filename = f"image_{model_type}_{timestamp}_{index}.{params.output_format}"
                    filepath = self.output_dir / filename
                    
                    with open(filepath, "wb") as file:
                        file.write(item.read())
                        
                    image_paths.append(str(filepath))
                    logger.info(f"图像已保存: {filepath}")
                    print(f"[green]✓[/green] 已保存图像: {filepath}")
                
            return ImageGenerationResult(
                local_paths=image_paths,
                uris=image_uris
            )
            
        except Exception as e:
            error_msg = f"生成图像时发生错误: {str(e)}"
            logger.error(error_msg)
            print(f"[bold red]错误:[/bold red] {error_msg}")
            raise 