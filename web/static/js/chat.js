// 初始化Socket.IO连接
const socket = io();

// DOM元素
const chatHistory = document.getElementById('chat-history');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-btn');
const modelSelect = document.getElementById('model-select');
const voiceSelect = document.getElementById('voice-select');
const whisperSelect = document.getElementById('whisper-select');
const voiceButton = document.getElementById('voice-btn');
const recordingIndicator = document.getElementById('recording-indicator');

// 页面切换相关
const menuButtons = document.querySelectorAll('.menu-btn');
const chatPage = document.getElementById('chat-page');
const settingsPage = document.getElementById('settings-page');

// 设置页面相关
const settingsMenuButtons = document.querySelectorAll('.settings-menu-btn');
const settingsContents = document.querySelectorAll('.settings-content');

// 会话管理相关
const newChatBtn = document.getElementById('new-chat-btn');
const chatList = document.getElementById('chat-list');
let currentChatId = null;

// 页面切换处理
menuButtons.forEach(button => {
    button.addEventListener('click', () => {
        const target = button.dataset.target;
        
        // 更新按钮状态
        menuButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        
        // 切换页面
        if (target === 'chat') {
            chatPage.classList.remove('hidden');
            settingsPage.classList.add('hidden');
        } else if (target === 'settings') {
            chatPage.classList.add('hidden');
            settingsPage.classList.remove('hidden');
        }
    });
});

// 设置菜单切换
settingsMenuButtons.forEach(button => {
    button.addEventListener('click', () => {
        const target = button.dataset.target;
        
        // 更新按钮状态
        settingsMenuButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        
        // 切换内容
        settingsContents.forEach(content => {
            if (content.id === target) {
                content.classList.remove('hidden');
            } else {
                content.classList.add('hidden');
            }
        });
    });
});

// 语音相关变量
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let voiceEnabled = true;  // 添加语音开关状态

// 初始化语音录制
async function initVoiceRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                channelCount: 1,
                sampleRate: 16000,
                sampleSize: 16,
                echoCancellation: true,
                noiseSuppression: true
            } 
        });
        
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm;codecs=opus',
            audioBitsPerSecond: 128000
        });
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            // 转换为WAV格式
            const arrayBuffer = await audioBlob.arrayBuffer();
            const audioContext = new AudioContext();
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            
            // 创建WAV
            const wavBuffer = audioBufferToWav(audioBuffer);
            const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' });
            
            await sendAudioToServer(wavBlob);
            audioChunks = [];
            audioContext.close();
        };
        
        return true;
    } catch (error) {
        console.error('初始化录音失败:', error);
        addMessage('错误: 无法访问麦克风，请检查权限设置', false);
        return false;
    }
}

// 添加WAV转换函数
function audioBufferToWav(buffer) {
    const numOfChan = buffer.numberOfChannels;
    const length = buffer.length * numOfChan * 2;
    const buffer32 = new Float32Array(buffer.length * numOfChan);
    const view = new DataView(new ArrayBuffer(44 + length));
    let offset = 0;
    let pos = 0;

    // WAV头
    writeString(view, offset, 'RIFF'); offset += 4;
    view.setUint32(offset, 36 + length, true); offset += 4;
    writeString(view, offset, 'WAVE'); offset += 4;
    writeString(view, offset, 'fmt '); offset += 4;
    view.setUint32(offset, 16, true); offset += 4;
    view.setUint16(offset, 1, true); offset += 2;
    view.setUint16(offset, numOfChan, true); offset += 2;
    view.setUint32(offset, buffer.sampleRate, true); offset += 4;
    view.setUint32(offset, buffer.sampleRate * 2 * numOfChan, true); offset += 4;
    view.setUint16(offset, numOfChan * 2, true); offset += 2;
    view.setUint16(offset, 16, true); offset += 2;
    writeString(view, offset, 'data'); offset += 4;
    view.setUint32(offset, length, true); offset += 4;

    // 写入音频数据
    for (let i = 0; i < buffer.numberOfChannels; i++) {
        buffer32.set(buffer.getChannelData(i), buffer.length * i);
    }

    // 转换为16位整数
    for (let i = 0; i < buffer32.length; i++) {
        let s = Math.max(-1, Math.min(1, buffer32[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        offset += 2;
    }

    return view.buffer;
}

// 辅助函数：写入字符串
function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

// 发送音频到服务器进行识别
async function sendAudioToServer(audioBlob) {
    try {
        showTypingIndicator();
        
        const formData = new FormData();
        formData.append('audio', audioBlob);
        
        const response = await fetch('/api/speech-to-text', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.text) {
            messageInput.value = data.text;
            // 自动发送识别的文本
            sendMessage();
        } else {
            addMessage(`错误: ${data.error || '语音识别失败'}`, false);
        }
    } catch (error) {
        console.error('发送音频失败:', error);
        addMessage('错误: 语音识别请求失败', false);
    } finally {
        hideTypingIndicator();
    }
}

// 开始录音
function startRecording() {
    if (!mediaRecorder) {
        initVoiceRecording().then((success) => {
            if (success) {
                startRecording();
            }
        });
        return;
    }
    
    if (!isRecording) {
        isRecording = true;
        audioChunks = [];
        mediaRecorder.start();
        recordingIndicator.classList.remove('hidden');
        voiceButton.classList.add('bg-red-500', 'text-white');
        voiceButton.classList.remove('bg-gray-100', 'text-gray-700');
    }
}

// 停止录音
function stopRecording() {
    if (isRecording) {
        isRecording = false;
        mediaRecorder.stop();
        recordingIndicator.classList.add('hidden');
        voiceButton.classList.remove('bg-red-500', 'text-white');
        voiceButton.classList.add('bg-gray-100', 'text-gray-700');
    }
}

// 语音按钮事件监听
voiceButton.addEventListener('mousedown', startRecording);
voiceButton.addEventListener('mouseup', stopRecording);
voiceButton.addEventListener('mouseleave', stopRecording);

// 触摸设备支持
voiceButton.addEventListener('touchstart', (e) => {
    e.preventDefault();
    startRecording();
});

voiceButton.addEventListener('touchend', (e) => {
    e.preventDefault();
    stopRecording();
});

// 模型切换处理
async function switchModel(model) {
    try {
        // 显示加载指示器
        showTypingIndicator();
        
        const response = await fetch('/api/switch-model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ model }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // 添加系统消息
            addMessage(`系统: ${data.message}`, false);
        } else {
            // 显示错误消息
            addMessage(`错误: ${data.error}`, false);
        }
    } catch (error) {
        console.error('切换模型失败:', error);
        addMessage(`错误: 切换模型失败 - ${error.message}`, false);
    } finally {
        hideTypingIndicator();
    }
}

// 语音切换处理
async function switchVoice(voice) {
    try {
        const response = await fetch('/api/switch-voice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ voice }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // 更新语音状态
            voiceEnabled = voice !== 'none';
            // 添加系统消息
            addMessage(`系统: ${data.message}`, false);
        } else {
            // 显示错误消息
            addMessage(`错误: ${data.error}`, false);
        }
    } catch (error) {
        console.error('切换语音失败:', error);
        addMessage(`错误: 切换语音失败 - ${error.message}`, false);
    }
}

// 切换Whisper模型
async function switchWhisperModel(model) {
    try {
        const response = await fetch('/api/switch-whisper', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model })
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message);
        }

        // 显示成功消息
        showMessage('系统', data.message, 'system');
    } catch (error) {
        console.error('切换Whisper模型失败:', error);
        showMessage('系统', `切换Whisper模型失败: ${error.message}`, 'error');
    }
}

// 监听模型选择变化
modelSelect.addEventListener('change', (e) => {
    switchModel(e.target.value);
});

// 监听语音选择变化
voiceSelect.addEventListener('change', (e) => {
    switchVoice(e.target.value);
});

// 监听Whisper模型切换
whisperSelect.addEventListener('change', (e) => {
    switchWhisperModel(e.target.value);
});

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
    // 隐藏加载指示器
    hideTypingIndicator();
    
    // 创建消息容器
    const messageContainer = document.createElement('div');
    messageContainer.className = `message-container ${isUser ? 'user-message-container' : 'bot-message-container'}`;
    
    // 创建头像
    const avatar = document.createElement('div');
    avatar.className = `avatar ${isUser ? 'user-avatar' : 'bot-avatar'}`;
    
    // 创建消息气泡
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    // 消息内容区域
    const content = document.createElement('div');
    content.className = 'markdown-content';
    
    if (!isUser) {
        // 处理Mermaid图表
        const mermaidRegex = /```mermaid([\s\S]*?)```/g;
        let lastIndex = 0;
        let match;
        let messageHTML = '';
        
        while ((match = mermaidRegex.exec(message)) !== null) {
            // 添加Mermaid图表前的文本
            messageHTML += parseMarkdown(message.slice(lastIndex, match.index));
            
            // 创建Mermaid图表容器
            const mermaidId = 'mermaid-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            messageHTML += `<div class="mermaid-container"><div class="mermaid" id="${mermaidId}">${match[1].trim()}</div></div>`;
            
            lastIndex = match.index + match[0].length;
        }
        
        // 添加剩余的文本
        messageHTML += parseMarkdown(message.slice(lastIndex));
        content.innerHTML = messageHTML;
        
        // 渲染所有新的Mermaid图表
        setTimeout(() => {
            content.querySelectorAll('.mermaid').forEach(element => {
                try {
                    mermaid.init(undefined, element);
                } catch (error) {
                    console.error('Mermaid渲染失败:', error);
                    element.innerHTML = '图表渲染失败: ' + error.message;
                }
            });
        }, 0);
    } else {
        content.innerHTML = parseMarkdown(message);
    }
    
    // 消息工具区域
    const toolsDiv = document.createElement('div');
    toolsDiv.className = 'message-tools mt-2 flex items-center justify-end space-x-2';
    
    // 复制按钮
    const copyBtn = document.createElement('button');
    copyBtn.className = 'text-gray-500 hover:text-gray-700 text-sm flex items-center space-x-1 px-2 py-1 rounded hover:bg-gray-100';
    copyBtn.innerHTML = '<i class="fas fa-copy mr-1"></i>复制';
    copyBtn.onclick = async () => {
        try {
            await navigator.clipboard.writeText(message);
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fas fa-check mr-1"></i>已复制';
            copyBtn.classList.add('text-green-500');
            
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
                copyBtn.classList.remove('text-green-500');
            }, 2000);
        } catch (err) {
            console.error('复制失败:', err);
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fas fa-times mr-1"></i>复制失败';
            copyBtn.classList.add('text-red-500');
            
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
                copyBtn.classList.remove('text-red-500');
            }, 2000);
        }
    };
    
    toolsDiv.appendChild(copyBtn);
    messageDiv.appendChild(content);
    messageDiv.appendChild(toolsDiv);
    
    // 组装消息容器
    messageContainer.appendChild(avatar);
    messageContainer.appendChild(messageDiv);
    
    chatHistory.appendChild(messageContainer);
    
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

// 创建新会话
async function createNewChat() {
    try {
        // 调用新建会话API
        const response = await fetch('/api/chat/new', {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('创建新会话失败');
        }
        
        // 创建新的会话项
        const chatId = Date.now().toString();
        const chatItem = createChatItem(chatId, '新的对话');
        chatList.insertBefore(chatItem, chatList.firstChild);
        switchToChat(chatId);
        saveChatList();
        
        // 清空聊天历史
        chatHistory.innerHTML = '';
        
    } catch (error) {
        console.error('创建新会话失败:', error);
        addMessage('错误: 创建新会话失败', false);
    }
}

// 创建会话项
function createChatItem(id, title) {
    const div = document.createElement('div');
    div.className = 'chat-item';
    div.dataset.id = id;
    div.innerHTML = `
        <i class="fas fa-comments"></i>
        <span class="title">${title}</span>
        <button class="delete-btn" onclick="deleteChat('${id}')">
            <i class="fas fa-trash"></i>
        </button>
    `;
    div.onclick = (e) => {
        if (!e.target.closest('.delete-btn')) {
            switchToChat(id);
        }
    };
    return div;
}

// 切换到指定会话
function switchToChat(chatId) {
    // 移除之前的活动状态
    const activeItem = chatList.querySelector('.chat-item.active');
    if (activeItem) {
        activeItem.classList.remove('active');
    }
    
    // 设置新的活动状态
    const newActiveItem = chatList.querySelector(`.chat-item[data-id="${chatId}"]`);
    if (newActiveItem) {
        newActiveItem.classList.add('active');
        currentChatId = chatId;
        
        // 清空聊天历史
        chatHistory.innerHTML = '';
        
        // 加载会话历史
        loadChatHistory(chatId);
    }
}

// 删除会话
function deleteChat(chatId) {
    const chatItem = chatList.querySelector(`.chat-item[data-id="${chatId}"]`);
    if (chatItem) {
        chatItem.remove();
        
        // 如果删除的是当前会话，创建新会话
        if (currentChatId === chatId) {
            createNewChat();
        }
        
        // 删除会话历史
        deleteChatHistory(chatId);
        saveChatList();
    }
}

// 保存会话列表
function saveChatList() {
    const chats = [];
    chatList.querySelectorAll('.chat-item').forEach(item => {
        chats.push({
            id: item.dataset.id,
            title: item.querySelector('.title').textContent
        });
    });
    localStorage.setItem('chatList', JSON.stringify(chats));
}

// 加载会话列表
function loadChatList() {
    const chats = JSON.parse(localStorage.getItem('chatList') || '[]');
    chatList.innerHTML = '';
    chats.forEach(chat => {
        chatList.appendChild(createChatItem(chat.id, chat.title));
    });
    
    // 如果没有会话，创建新会话
    if (chats.length === 0) {
        createNewChat();
    } else {
        // 切换到第一个会话
        switchToChat(chats[0].id);
    }
}

// 加载会话历史
async function loadChatHistory(chatId) {
    try {
        const response = await fetch(`/api/history/${chatId}`);
        const data = await response.json();
        
        if (data.history) {
            data.history.reverse().forEach(record => {
                addMessage(record.user_input, true);
                addMessage(record.ai_response);
            });
        }
    } catch (error) {
        console.error('加载会话历史失败:', error);
    }
}

// 删除会话历史
async function deleteChatHistory(chatId) {
    try {
        await fetch(`/api/history/${chatId}`, {
            method: 'DELETE'
        });
    } catch (error) {
        console.error('删除会话历史失败:', error);
    }
}

// 事件监听
newChatBtn.addEventListener('click', createNewChat);

// 修改发送消息函数，添加会话ID
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
    socket.emit('message', { 
        message,
        chatId: currentChatId  // 添加会话ID
    });
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
    const message = data.message;
    addMessage(message, false);
    
    // 只有在语音功能开启时才播放音频
    if (voiceEnabled) {
        // 播放音频响应
        const audio = new Audio('/temp/response.mp3');
        audio.play().catch(error => {
            console.error('播放音频失败:', error);
        });
    }
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

// 页面加载完成后加载会话列表
document.addEventListener('DOMContentLoaded', loadChatList); 