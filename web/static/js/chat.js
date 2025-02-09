// 初始化Socket.IO连接
const socket = io();

// DOM元素
const chatHistory = document.getElementById('chat-history');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-btn');

// Markdown解析函数
function parseMarkdown(text) {
    // 这里可以使用更复杂的Markdown解析库，这里只做基本处理
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}

// 添加消息到聊天历史
function addMessage(message, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    const content = document.createElement('div');
    content.className = 'markdown-content';
    content.innerHTML = parseMarkdown(message);
    
    messageDiv.appendChild(content);
    chatHistory.appendChild(messageDiv);
    
    // 滚动到底部
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// 显示加载指示器
function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator message bot-message';
    indicator.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;
    indicator.id = 'typing-indicator';
    chatHistory.appendChild(indicator);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// 隐藏加载指示器
function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// 发送消息
function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    // 添加用户消息到聊天历史
    addMessage(message, true);
    
    // 清空输入框
    messageInput.value = '';
    
    // 显示加载指示器
    showTypingIndicator();
    
    // 发送消息到服务器
    socket.emit('message', { message });
}

// 事件监听器
sendButton.addEventListener('click', sendMessage);

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Socket.IO事件处理
socket.on('response', (data) => {
    hideTypingIndicator();
    addMessage(data.message);
});

socket.on('error', (data) => {
    hideTypingIndicator();
    addMessage(`错误: ${data.message}`);
});

// 加载历史记录
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.history) {
            // 清空现有历史
            chatHistory.innerHTML = '';
            
            // 添加历史消息
            data.history.reverse().forEach(record => {
                addMessage(record.user_input, true);
                addMessage(record.ai_response);
            });
        }
    } catch (error) {
        console.error('加载历史记录失败:', error);
    }
}

// 页面加载完成后加载历史记录
document.addEventListener('DOMContentLoaded', loadHistory); 