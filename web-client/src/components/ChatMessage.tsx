import React from 'react';
import { Avatar } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import MermaidDiagram from './MermaidDiagram';
import EChartDiagram from './EChartDiagram';

interface ChatMessageProps {
  content: string;
  isUser: boolean;
  timestamp?: string;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ content, isUser, timestamp }) => {
  // 处理内容
  const renderContent = () => {
    // 分割内容以处理特殊代码块
    const parts = content.split(/(```(?:mermaid|echart|[a-z]*)\n[\s\S]*?```)/);
    
    return parts.map((part, index) => {
      // 处理 Mermaid 图表
      if (part.startsWith('```mermaid\n')) {
        const chartContent = part.replace(/```mermaid\n([\s\S]*?)```/, '$1').trim();
        return <MermaidDiagram key={index} chart={chartContent} />;
      }
      
      // 处理 ECharts 图表
      if (part.startsWith('```echart\n')) {
        try {
          const chartContent = part.replace(/```echart\n([\s\S]*?)```/, '$1').trim();
          // 验证是否为有效的 JSON
          const config = JSON.parse(chartContent);
          return <EChartDiagram key={index} config={chartContent} />;
        } catch (e: Error | unknown) {
          console.error('Invalid EChart config:', e);
          const errorMessage = e instanceof Error ? e.message : '未知错误';
          return (
            <div key={index} style={{ color: 'red', padding: '10px', margin: '10px 0', backgroundColor: '#ffebee' }}>
              图表配置无效：{errorMessage}
              <pre style={{ marginTop: '10px' }}>{part}</pre>
            </div>
          );
        }
      }
      
      // 处理其他代码块
      if (part.startsWith('```')) {
        const match = part.match(/```(\w*)\n([\s\S]*?)```/);
        if (match) {
          const [, language, code] = match;
          return (
            <SyntaxHighlighter
              key={index}
              language={language || 'text'}
              style={tomorrow}
            >
              {code.trim()}
            </SyntaxHighlighter>
          );
        }
      }

      // 处理普通文本
      if (part.trim()) {
        return (
          <ReactMarkdown
            key={index}
            remarkPlugins={[remarkGfm]}
            components={{
              code({className, children}) {
                const match = /language-(\w+)/.exec(className || '');
                return match ? (
                  <SyntaxHighlighter
                    language={match[1]}
                    style={tomorrow}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={className}>
                    {children}
                  </code>
                );
              },
              table({children}) {
                return (
                  <div className="table-container">
                    <table>{children}</table>
                  </div>
                );
              }
            }}
          >
            {part}
          </ReactMarkdown>
        );
      }
      
      return null;
    }).filter(Boolean);
  };

  return (
    <div className={`chat-message ${isUser ? 'user' : ''}`}>
      <Avatar
        className="avatar"
        icon={isUser ? <UserOutlined /> : <RobotOutlined />}
        style={{ backgroundColor: isUser ? '#1890ff' : '#52c41a' }}
      />
      <div className="content">
        {renderContent()}
        {timestamp && (
          <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
            {timestamp}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage; 