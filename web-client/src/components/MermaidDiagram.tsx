import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

// 初始化mermaid配置
mermaid.initialize({
  startOnLoad: true,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'monospace',
});

interface MermaidDiagramProps {
  chart: string;
}

const MermaidDiagram: React.FC<MermaidDiagramProps> = ({ chart }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      try {
        // 清空容器
        containerRef.current.innerHTML = '';
        
        // 生成唯一ID
        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
        
        // 渲染图表
        mermaid.render(id, chart).then(({ svg }) => {
          if (containerRef.current) {
            containerRef.current.innerHTML = svg;
          }
        });
      } catch (error) {
        console.error('Mermaid渲染失败:', error);
        if (containerRef.current) {
          containerRef.current.innerHTML = `<pre>${chart}</pre>`;
        }
      }
    }
  }, [chart]);

  return <div ref={containerRef} className="mermaid-diagram" />;
};

export default MermaidDiagram; 