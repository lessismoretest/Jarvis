"""
Flask Web应用 - Jarvis Web界面
"""
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jarvis import Jarvis

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis-secret-key'
socketio = SocketIO(app)

# 创建Jarvis实例
jarvis = Jarvis()

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@socketio.on('message')
def handle_message(data):
    """处理WebSocket消息"""
    try:
        user_message = data.get('message', '')
        if not user_message:
            return
            
        # 调用Jarvis处理消息
        response = jarvis.chat(user_message)
        
        # 发送响应回客户端
        emit('response', {'message': response})
        
    except Exception as e:
        emit('error', {'message': f'处理消息时出错: {str(e)}'})

@app.route('/api/chat', methods=['POST'])
def chat():
    """HTTP API端点用于聊天"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        if not message:
            return jsonify({'error': '消息不能为空'}), 400
            
        response = jarvis.chat(message)
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def get_history():
    """获取聊天历史"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = jarvis.db.get_chat_history(limit=limit)
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/switch-model', methods=['POST'])
def switch_model():
    """切换AI模型"""
    try:
        data = request.get_json()
        model = data.get('model', '')
        if not model or model not in ['deepseek', 'gemini']:
            return jsonify({'error': '无效的模型名称'}), 400
            
        # 重新初始化Jarvis实例
        global jarvis
        jarvis = Jarvis(ai_model=model)
        
        return jsonify({'message': f'已切换到 {model} 模型'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/switch-voice', methods=['POST'])
def switch_voice():
    """切换TTS语音"""
    try:
        data = request.get_json()
        voice = data.get('voice', '')
        if not voice:
            return jsonify({'error': '无效的语音选项'}), 400
            
        if voice == 'none':
            # 关闭语音功能
            jarvis.speech_synthesizer.enabled = False
            return jsonify({'message': '已关闭语音功能'})
            
        # 开启语音功能并更新语音
        jarvis.speech_synthesizer.enabled = True
        jarvis.speech_synthesizer.voice = voice
        
        return jsonify({'message': f'已切换到新的语音'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/switch-whisper', methods=['POST'])
def switch_whisper():
    """切换Whisper模型"""
    try:
        data = request.get_json()
        model_name = data.get('model')
        
        if not model_name or model_name not in ["tiny", "base", "small", "medium", "large"]:
            return jsonify({
                "success": False,
                "message": "无效的模型名称"
            }), 400
            
        # 重新初始化Whisper识别器
        jarvis.speech_recognizer = WhisperRecognizer(model_name=model_name)
        
        return jsonify({
            "success": True,
            "message": f"已切换到Whisper {model_name}模型"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"切换模型失败: {str(e)}"
        }), 500

@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    """语音识别API"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': '没有收到音频文件'}), 400
            
        audio_file = request.files['audio']
        if not audio_file:
            return jsonify({'error': '音频文件为空'}), 400
            
        # 保存临时文件
        temp_path = os.path.join('temp', f'speech_{int(time.time() * 1000)}.webm')
        audio_file.save(temp_path)
        
        try:
            # 使用Whisper进行语音识别
            text = jarvis.speech_recognizer.transcribe_audio(temp_path)
            return jsonify({'text': text})
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_web_app():
    """启动Web应用"""
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)

if __name__ == '__main__':
    run_web_app() 