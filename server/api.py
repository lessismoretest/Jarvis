import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from server.jarvis import Jarvis
import json
from typing import Dict
import asyncio
from utils.logger import setup_logger

# 配置日志
logger = setup_logger(__name__)

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储每个会话的Jarvis实例
jarvis_instances: Dict[str, Jarvis] = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("New WebSocket connection accepted")
    
    try:
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message_data = json.loads(data)
                session_id = message_data.get('sessionId')
                logger.info(f"Received message from session {session_id}: {message_data}")
                
                # 提取消息内容和配置
                content = message_data.get('content', '')
                model = message_data.get('model', 'gemini')
                whisper_model = message_data.get('whisperModel', 'small')
                tts_voice = message_data.get('ttsVoice', 'zh-CN-XiaoxiaoNeural')
                
                # 检查是否已存在相同会话的Jarvis实例
                if session_id not in jarvis_instances:
                    logger.info(f"Creating new Jarvis instance for session {session_id}")
                    jarvis = Jarvis(ai_model=model)
                    jarvis_instances[session_id] = jarvis
                else:
                    jarvis = jarvis_instances[session_id]
                    # 如果AI模型与当前不同,重新初始化
                    if model != jarvis.ai_model.__class__.__name__.lower().replace('ai', ''):
                        logger.info(f"Switching AI model to {model} for session {session_id}")
                        jarvis = Jarvis(ai_model=model)
                        jarvis_instances[session_id] = jarvis
                
                # 生成响应
                response = jarvis.chat(content)
                logger.info(f"Generated response for session {session_id}")
                
                # 发送响应
                await websocket.send_json({
                    'content': response
                })
                logger.info(f"Sent response to session {session_id}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {str(e)}")
                await websocket.send_json({
                    'error': '无效的消息格式'
                })
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                await websocket.send_json({
                    'error': f'处理消息时出错: {str(e)}'
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # 不要立即清理资源,保留实例以便重连时复用
        pass

# 定期清理长时间未使用的实例
@app.on_event("startup")
async def startup_event():
    async def cleanup_instances():
        while True:
            await asyncio.sleep(3600)  # 每小时检查一次
            # TODO: 添加实例使用时间戳,清理超过一定时间未使用的实例
            
    asyncio.create_task(cleanup_instances())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001) 