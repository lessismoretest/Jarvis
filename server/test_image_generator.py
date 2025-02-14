"""
测试图像生成模块
"""
from dotenv import load_dotenv
from image_generator import (
    ImageGenerator, 
    ModelType, 
    ImageGenerationParams,
    AspectRatio,
    OutputFormat
)

def test_model(
    generator: ImageGenerator,
    params: ImageGenerationParams
):
    """测试图像生成"""
    print(f"\n[测试] Stable Diffusion 3.5")
    print(f"提示词: {params.prompt}")
    print(f"参数: 宽高比={params.aspect_ratio}, 步数={params.steps}, CFG={params.cfg}")
    
    try:
        result = generator.generate(
            params=params,
            model_type="stable-diffusion-3.5",
            num_images=1
        )
        
        if params.save_to_local:
            print("\n本地保存路径:")
            for path in result.local_paths:
                print(f"- {path}")
                
        print("\n图像URI:")
        for uri in result.uris:
            print(f"- {uri}")
            
    except Exception as e:
        print(f"测试失败: {str(e)}")

def main():
    # 加载环境变量
    load_dotenv()
    
    # 创建图像生成器实例
    generator = ImageGenerator()
    
    # 测试不同的参数配置
    test_cases = [
        # 标准1:1比例的风景照（保存到本地）
        ImageGenerationParams(
            prompt="A girl in a red dress",
            aspect_ratio="1:1",
            steps=40,
            cfg=7.0,
            save_to_local=True
        ),
        # 16:9宽屏人像（只返回URI）
        ImageGenerationParams(
            prompt="A professional portrait of a young woman in business attire",
            aspect_ratio="16:9",
            steps=45,
            cfg=7.5,
            output_format="png",
            output_quality=100,
            save_to_local=False
        ),
        # 带有负面提示词的生成
        ImageGenerationParams(
            prompt="A beautiful cat in a garden",
            aspect_ratio="4:3",
            steps=40,
            cfg=7.0,
            negative_prompt="low quality, blurry, distorted"
        ),
        # 带有特定种子的生成
        ImageGenerationParams(
            prompt="A mystical forest with glowing mushrooms and fairies",
            aspect_ratio="3:2",
            seed=42,
            steps=40,
            cfg=7.0
        )
    ]
    
    # 运行测试
    for params in test_cases:
        test_model(generator, params)

if __name__ == "__main__":
    main() 