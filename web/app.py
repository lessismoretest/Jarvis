"""
Flask Web应用 - Jarvis Web界面
"""
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import sys
import os
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

def run_web_app():
    """启动Web应用"""
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)

if __name__ == '__main__':
    run_web_app() 