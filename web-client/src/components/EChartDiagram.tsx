import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { theme } from 'antd';

interface EChartDiagramProps {
  config: string;
}

const EChartDiagram: React.FC<EChartDiagramProps> = ({ config }) => {
  const [option, setOption] = useState<any>(null);
  const { token } = theme.useToken();
  
  useEffect(() => {
    try {
      // 解析配置字符串为对象
      const parsedOption = JSON.parse(config);
      
      // 根据当前主题调整图表颜色
      const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
      
      // 深拷贝配置以避免修改原始对象
      const themedOption = JSON.parse(JSON.stringify(parsedOption));
      
      // 设置主题相关的默认值
      if (!themedOption.backgroundColor) {
        themedOption.backgroundColor = 'transparent';
      }
      
      // 设置文本颜色
      const textColor = isDarkMode ? '#fff' : '#333';
      if (themedOption.title && !themedOption.title.textStyle) {
        themedOption.title.textStyle = { color: textColor };
      }
      
      // 设置坐标轴颜色
      ['xAxis', 'yAxis'].forEach(axis => {
        if (themedOption[axis]) {
          if (Array.isArray(themedOption[axis])) {
            themedOption[axis].forEach((item: any) => {
              if (!item.axisLine) item.axisLine = { lineStyle: { color: textColor } };
              if (!item.axisLabel) item.axisLabel = { color: textColor };
            });
          } else {
            if (!themedOption[axis].axisLine) themedOption[axis].axisLine = { lineStyle: { color: textColor } };
            if (!themedOption[axis].axisLabel) themedOption[axis].axisLabel = { color: textColor };
          }
        }
      });
      
      // 设置图例颜色
      if (themedOption.legend && !themedOption.legend.textStyle) {
        themedOption.legend.textStyle = { color: textColor };
      }
      
      // 设置默认的主题色
      if (themedOption.color === undefined) {
        themedOption.color = [
          token.colorPrimary,
          token.colorSuccess,
          token.colorWarning,
          token.colorError,
          token.colorInfo,
        ];
      }
      
      setOption(themedOption);
    } catch (error) {
      console.error('Failed to parse ECharts config:', error);
      setOption(null);
    }
  }, [config, token]);
  
  if (!option) {
    return <div>图表配置无效</div>;
  }
  
  return (
    <div className="echart-diagram">
      <ReactECharts
        option={option}
        style={{ height: '400px' }}
        theme={document.documentElement.getAttribute('data-theme') || 'light'}
      />
    </div>
  );
}

export default EChartDiagram; 