import { useState, useEffect, useRef } from 'react'
import { Layout, Menu, Button, Select, Input, theme, message } from 'antd'
import {
  PlusOutlined,
  MessageOutlined,
  SettingOutlined,
  SendOutlined,
  AudioOutlined,
} from '@ant-design/icons'
import ChatMessage from './components/ChatMessage'
import Settings from './components/Settings'
import { wsService } from './services/websocket'
import './App.css'

const { Header, Sider, Content } = Layout
const { Option } = Select

interface Message {
  content: string
  isUser: boolean
  timestamp: string
}

function App() {
  const [collapsed, setCollapsed] = useState(false)
  const [activeTab, setActiveTab] = useState('chat')
  const [inputMessage, setInputMessage] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [messages, setMessages] = useState<Message[]>(() => {
    // 从localStorage加载消息历史
    const savedMessages = localStorage.getItem('chatMessages');
    return savedMessages ? JSON.parse(savedMessages) : [];
  })
  const [selectedModel, setSelectedModel] = useState(() => 
    localStorage.getItem('selectedModel') || 'gemini'
  )
  const [selectedWhisper, setSelectedWhisper] = useState(() =>
    localStorage.getItem('selectedWhisper') || 'small'
  )
  const [selectedVoice, setSelectedVoice] = useState(() =>
    localStorage.getItem('selectedVoice') || 'zh-CN-XiaoxiaoNeural'
  )
  const [isConnected, setIsConnected] = useState(true)
  
  // 初始化主题
  useEffect(() => {
    // 检查系统主题偏好
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    // 从localStorage获取保存的主题设置，如果没有则使用系统主题
    const savedTheme = localStorage.getItem('theme') || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // 监听系统主题变化
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      const newTheme = e.matches ? 'dark' : 'light';
      // 只有在用户没有手动设置主题时才跟随系统
      if (!localStorage.getItem('theme')) {
        document.documentElement.setAttribute('data-theme', newTheme);
      }
    };
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // 保存消息历史到localStorage
  useEffect(() => {
    localStorage.setItem('chatMessages', JSON.stringify(messages));
  }, [messages]);

  // 保存设置到localStorage
  useEffect(() => {
    localStorage.setItem('selectedModel', selectedModel);
    localStorage.setItem('selectedWhisper', selectedWhisper);
    localStorage.setItem('selectedVoice', selectedVoice);
  }, [selectedModel, selectedWhisper, selectedVoice]);

  const {
    token: { colorBgContainer },
  } = theme.useToken()

  // 创建一个ref来引用聊天历史区域
  const chatHistoryRef = useRef<HTMLDivElement>(null);

  // 滚动到最新消息
  const scrollToBottom = () => {
    if (chatHistoryRef.current) {
      const scrollHeight = chatHistoryRef.current.scrollHeight;
      const height = chatHistoryRef.current.clientHeight;
      const maxScrollTop = scrollHeight - height;
      chatHistoryRef.current.scrollTop = maxScrollTop > 0 ? maxScrollTop : 0;
    }
  };

  useEffect(() => {
    console.log('Setting up WebSocket listeners')
    const unsubscribeMessage = wsService.onMessage((msg) => {
      console.log('Received message:', msg)
      const newMessage: Message = {
        content: msg.content,
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
      }
      setMessages(prev => [...prev, newMessage])
      // 消息更新后滚动到底部
      setTimeout(scrollToBottom, 100) // 添加小延迟确保内容已渲染
    })

    const unsubscribeStatus = wsService.onStatusChange((status) => {
      console.log('Connection status changed:', status)
      setIsConnected(status)
      if (!status) {
        message.error('连接已断开，正在尝试重新连接...')
      } else {
        message.success('已重新连接')
      }
    })

    // 组件挂载时滚动到底部
    scrollToBottom();

    return () => {
      unsubscribeMessage()
      unsubscribeStatus()
      wsService.disconnect()
    }
  }, [])

  const handleSend = () => {
    if (inputMessage.trim()) {
      const newMessage: Message = {
        content: inputMessage,
        isUser: true,
        timestamp: new Date().toLocaleTimeString(),
      }
      setMessages(prev => [...prev, newMessage])
      
      wsService.sendMessage(inputMessage, {
        model: selectedModel,
        whisperModel: selectedWhisper,
        ttsVoice: selectedVoice,
      })
      
      setInputMessage('')
      // 发送消息后也滚动到底部
      setTimeout(scrollToBottom, 100)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewChat = () => {
    if (messages.length > 0) {
      const confirmed = window.confirm('确定要开始新的对话吗？当前对话将被清空。');
      if (confirmed) {
        setMessages([]);
        wsService.createNewSession();
      }
    }
  }

  return (
    <Layout style={{ height: '100vh' }}>
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        width={250}
        style={{
          background: colorBgContainer,
          borderRight: '1px solid rgba(0, 0, 0, 0.06)'
        }}
      >
        <div style={{ padding: '16px' }}>
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            block
            onClick={handleNewChat}
          >
            新建会话
          </Button>
        </div>
        
        <div style={{ flex: 1, overflow: 'auto' }}>
          {/* 会话列表将在这里 */}
        </div>

        <Menu
          mode="inline"
          selectedKeys={[activeTab]}
          onClick={({ key }) => setActiveTab(key)}
          items={[
            {
              key: 'chat',
              icon: <MessageOutlined />,
              label: '聊天',
            },
            {
              key: 'settings',
              icon: <SettingOutlined />,
              label: '设置',
            },
          ]}
        />
      </Sider>
      
      <Layout>
        <Content style={{ background: colorBgContainer }}>
          {activeTab === 'chat' ? (
            <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              {/* 工具栏 */}
              <div style={{ padding: '16px', borderBottom: '1px solid rgba(0, 0, 0, 0.06)' }}>
                <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                  <div>
                    <span style={{ marginRight: '8px' }}>AI模型:</span>
                    <Select 
                      value={selectedModel} 
                      onChange={setSelectedModel}
                      style={{ width: 120 }}
                    >
                      <Option value="deepseek">Deepseek</Option>
                      <Option value="gemini">Gemini</Option>
                    </Select>
                  </div>
                  <div>
                    <span style={{ marginRight: '8px' }}>语音识别:</span>
                    <Select 
                      value={selectedWhisper}
                      onChange={setSelectedWhisper}
                      style={{ width: 120 }}
                    >
                      <Option value="tiny">Tiny (最快)</Option>
                      <Option value="base">Base (快速)</Option>
                      <Option value="small">Small (平衡)</Option>
                      <Option value="medium">Medium (较准)</Option>
                      <Option value="large">Large (最准)</Option>
                    </Select>
                  </div>
                  <div>
                    <span style={{ marginRight: '8px' }}>文字转语音:</span>
                    <Select 
                      value={selectedVoice}
                      onChange={setSelectedVoice}
                      style={{ width: 160 }}
                    >
                      <Option value="none">关闭</Option>
                      <Option value="zh-CN-XiaoxiaoNeural">晓晓 (女声)</Option>
                      <Option value="zh-CN-YunxiNeural">云希 (男声)</Option>
                      <Option value="zh-CN-YunyangNeural">云扬 (男声新闻)</Option>
                    </Select>
                  </div>
                </div>
              </div>

              {/* 聊天历史 */}
              <div 
                ref={chatHistoryRef} 
                className="chat-history"
              >
                {messages.map((msg, index) => (
                  <ChatMessage
                    key={index}
                    content={msg.content}
                    isUser={msg.isUser}
                    timestamp={msg.timestamp}
                  />
                ))}
              </div>

              {/* 输入区域 */}
              <div style={{ padding: '16px', borderTop: '1px solid rgba(0, 0, 0, 0.06)' }}>
                <Input.Group compact>
                  <Input
                    style={{ width: 'calc(100% - 120px)' }}
                    placeholder="输入您的问题..."
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                  />
                  <Button
                    icon={<AudioOutlined />}
                    onMouseDown={() => setIsRecording(true)}
                    onMouseUp={() => setIsRecording(false)}
                  />
                  <Button 
                    type="primary" 
                    icon={<SendOutlined />}
                    onClick={handleSend}
                  >
                    发送
                  </Button>
                </Input.Group>
                {isRecording && (
                  <div style={{ textAlign: 'center', color: '#ff4d4f', marginTop: '8px' }}>
                    正在录音...
                  </div>
                )}
              </div>
            </div>
          ) : (
            <Settings />
          )}
        </Content>
      </Layout>
    </Layout>
  )
}

export default App
