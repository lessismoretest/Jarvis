class WebSocketService {
  private ws: WebSocket | null = null;
  private messageHandlers: ((message: any) => void)[] = [];
  private statusHandlers: ((status: boolean) => void)[] = [];
  private offlineMode: boolean = false;
  private reconnectTimer: number | null = null;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectInterval: number = 3000;
  private sessionId: string = '';

  constructor() {
    // 从localStorage获取或生成新的会话ID
    this.sessionId = localStorage.getItem('sessionId') || Date.now().toString();
    localStorage.setItem('sessionId', this.sessionId);
    
    if (!this.offlineMode) {
      this.connect();
    } else {
      setTimeout(() => {
        this.notifyStatusHandlers(true);
      }, 0);
    }

    // 监听页面可见性变化
    document.addEventListener('visibilitychange', this.handleVisibilityChange);
    // 监听在线状态变化
    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);
  }

  private handleVisibilityChange = () => {
    if (document.visibilityState === 'visible') {
      // 页面变为可见时，检查连接状态
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        this.connect();
      }
    }
  };

  private handleOnline = () => {
    console.log('网络已连接，尝试重新连接WebSocket');
    this.connect();
  };

  private handleOffline = () => {
    console.log('网络已断开');
    this.notifyStatusHandlers(false);
  };

  private connect() {
    try {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        console.log('WebSocket已连接');
        return;
      }

      this.ws = new WebSocket('ws://localhost:5001/ws');

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.notifyStatusHandlers(true);
        this.reconnectAttempts = 0;
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.notifyStatusHandlers(false);
        
        // 如果不是主动关闭，则尝试重连
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          console.log(`尝试重连 (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
          this.reconnectTimer = window.setTimeout(() => {
            this.reconnectAttempts++;
            this.connect();
          }, this.reconnectInterval);
        } else {
          console.log('达到最大重连次数');
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('Received message:', message);
          this.notifyMessageHandlers(message);
        } catch (e) {
          console.error('Failed to parse message:', e);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (e) {
      console.error('Failed to create WebSocket:', e);
    }
  }

  public sendMessage(message: string, options: {
    model: string;
    whisperModel: string;
    ttsVoice: string;
  }) {
    if (this.offlineMode) {
      setTimeout(() => {
        this.notifyMessageHandlers({
          content: `[离线模式] 收到消息：${message}\n\n当前选择的配置：\n- 模型：${options.model}\n- 语音识别：${options.whisperModel}\n- 声音：${options.ttsVoice}`,
        });
      }, 500);
      return;
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        const data = JSON.stringify({
          content: message,
          sessionId: this.sessionId,
          ...options,
        });
        console.log('Sending message:', data);
        this.ws.send(data);
      } catch (e) {
        console.error('Failed to send message:', e);
      }
    } else {
      console.error('WebSocket is not connected');
      // 保存消息到本地存储，等待重连后发送
      this.saveMessageToLocal(message, options);
    }
  }

  private saveMessageToLocal(message: string, options: any) {
    const pendingMessages = JSON.parse(localStorage.getItem('pendingMessages') || '[]');
    pendingMessages.push({ message, options, timestamp: Date.now() });
    localStorage.setItem('pendingMessages', JSON.stringify(pendingMessages));
  }

  private sendPendingMessages() {
    const pendingMessages = JSON.parse(localStorage.getItem('pendingMessages') || '[]');
    if (pendingMessages.length > 0) {
      pendingMessages.forEach((item: any) => {
        this.sendMessage(item.message, item.options);
      });
      localStorage.removeItem('pendingMessages');
    }
  }

  public onMessage(handler: (message: any) => void) {
    this.messageHandlers.push(handler);
    return () => {
      this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
    };
  }

  public onStatusChange(handler: (status: boolean) => void) {
    this.statusHandlers.push(handler);
    return () => {
      this.statusHandlers = this.statusHandlers.filter(h => h !== handler);
    };
  }

  private notifyMessageHandlers(message: any) {
    this.messageHandlers.forEach(handler => handler(message));
  }

  private notifyStatusHandlers(status: boolean) {
    this.statusHandlers.forEach(handler => handler(status));
  }

  public disconnect() {
    document.removeEventListener('visibilitychange', this.handleVisibilityChange);
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // 获取当前会话ID
  public getSessionId(): string {
    return this.sessionId;
  }

  // 创建新会话
  public createNewSession() {
    this.sessionId = Date.now().toString();
    localStorage.setItem('sessionId', this.sessionId);
    return this.sessionId;
  }
}

export const wsService = new WebSocketService(); 