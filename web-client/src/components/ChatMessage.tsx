import React from 'react';
import { Avatar } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import MermaidDiagram from './MermaidDiagram';

interface ChatMessageProps {
  content: string;
  isUser: boolean;
  timestamp?: string;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ content, isUser, timestamp }) => {
  // 检查内容是否包含Mermaid图表
  const hasMermaid = content.includes('```mermaid');

  // 处理Mermaid图表
  const renderContent = () => {
    if (hasMermaid) {
      const parts = content.split('```');
      return parts.map((part, index) => {
        if (part.startsWith('mermaid\n')) {
          // 提取Mermaid图表内容
          const chartContent = part.replace('mermaid\n', '');
          return <MermaidDiagram key={index} chart={chartContent} />;
        } else if (part.trim()) {
          // 渲染普通Markdown内容
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
                      <table style={{borderCollapse: 'collapse', width: '100%'}}>
                        {children}
                      </table>
                    </div>
                  );
                },
                th({children}) {
                  return (
                    <th 
                      style={{
                        border: '1px solid #ddd', 
                        padding: '8px', 
                        backgroundColor: '#f5f5f5'
                      }}
                    >
                      {children}
                    </th>
                  );
                },
                td({children}) {
                  return (
                    <td 
                      style={{
                        border: '1px solid #ddd', 
                        padding: '8px'
                      }}
                    >
                      {children}
                    </td>
                  );
                }
              }}
            >
              {part}
            </ReactMarkdown>
          );
        }
        return null;
      });
    } else {
      // 如果没有Mermaid图表，直接渲染Markdown
      return (
        <ReactMarkdown
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
                  <table style={{borderCollapse: 'collapse', width: '100%'}}>
                    {children}
                  </table>
                </div>
              );
            },
            th({children}) {
              return (
                <th 
                  style={{
                    border: '1px solid #ddd', 
                    padding: '8px', 
                    backgroundColor: '#f5f5f5'
                  }}
                >
                  {children}
                </th>
              );
            },
            td({children}) {
              return (
                <td 
                  style={{
                    border: '1px solid #ddd', 
                    padding: '8px'
                  }}
                >
                  {children}
                </td>
              );
            }
          }}
        >
          {content}
        </ReactMarkdown>
      );
    }
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