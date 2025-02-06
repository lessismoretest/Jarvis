# Jarvis AI 助手

基于钢铁侠电影中的 J.A.R.V.I.S. (Just A Rather Very Intelligent System) 打造的智能助手系统。

## 功能特点

- 多AI模型支持（Deepseek和Gemini）
- 模块化设计
- 完整的日志系统
- 安全的配置管理

## 安装步骤

1. 克隆项目：
~~~bash
git clone <repository_url>
cd jarvis
~~~

2. 创建并激活虚拟环境：
~~~bash
# Linux/Mac
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
~~~

3. 安装依赖：
~~~bash
pip install -r requirements.txt
~~~

4. 配置环境变量：
   - 复制 `.env.example` 为 `.env`
   - 在 `.env` 中填入你的API密钥：
~~~ini
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_BASE=your_deepseek_api_base_url_here
GEMINI_API_KEY=your_gemini_api_key_here
~~~

## 使用方法

1. 运行Jarvis：
~~~bash
python jarvis.py
~~~

2. 与Jarvis交互：
   - 输入问题进行对话
   - 输入 'quit' 退出程序

3. 切换AI模型：
~~~python
# 在代码中指定模型
jarvis = Jarvis(ai_model="gemini")  # 或 "deepseek"
~~~

## 项目结构

~~~
jarvis/
├── logs/           # 日志文件目录
├── utils/
│   ├── __init__.py
│   └── logger.py   # 日志配置
├── ai_models.py    # AI模型实现
├── config.py       # 配置管理
├── jarvis.py       # 主程序
├── requirements.txt
└── README.md
~~~

## 日志系统

- 日志存储在 `logs` 目录
- 按日期命名：`jarvis_YYYYMMDD.log`
- 自动分割：每个文件最大10MB
- 保留最近5个备份文件
- 同时输出到控制台和文件

## 开发说明

1. 添加新的AI模型：
   - 在 `ai_models.py` 中继承 `BaseAIModel`
   - 实现 `generate_response` 方法
   - 在 `config.py` 中添加相应配置

2. 日志级别：
   - DEBUG: 详细调试信息
   - INFO: 一般信息
   - WARNING: 警告信息
   - ERROR: 错误信息
   - CRITICAL: 严重错误

## 注意事项

- 请勿将 `.env` 文件提交到版本控制系统
- 建议定期检查和清理日志文件
- API密钥请妥善保管，不要泄露

## 依赖列表

- openai: Deepseek API 客户端
- google-generativeai: Gemini API 客户端
- python-dotenv: 环境变量管理
- python-json-logger: JSON格式日志支持

## 许可证

[添加你的许可证信息]

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 联系方式

[添加你的联系方式] 