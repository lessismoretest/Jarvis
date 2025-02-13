import React, { useState, useEffect } from 'react';
import { Tabs, Form, Select, Card, Radio } from 'antd';
import type { TabsProps } from 'antd';

const { Option } = Select;

const Settings: React.FC = () => {
  const [form] = Form.useForm();
  const [theme, setTheme] = useState(() => {
    return document.documentElement.getAttribute('data-theme') || 'light';
  });

  const handleThemeChange = (value: string) => {
    setTheme(value);
    document.documentElement.setAttribute('data-theme', value);
    localStorage.setItem('theme', value);
  };

  const items: TabsProps['items'] = [
    {
      key: 'ai',
      label: 'AI设置',
      children: (
        <Card>
          <Form form={form} layout="vertical">
            <Form.Item
              label="默认AI模型"
              name="defaultModel"
              initialValue="gemini"
            >
              <Select>
                <Option value="deepseek">Deepseek</Option>
                <Option value="gemini">Gemini</Option>
              </Select>
            </Form.Item>
            <Form.Item
              label="语音识别模型"
              name="whisperModel"
              initialValue="small"
            >
              <Select>
                <Option value="tiny">Tiny (最快)</Option>
                <Option value="base">Base (快速)</Option>
                <Option value="small">Small (平衡)</Option>
                <Option value="medium">Medium (较准)</Option>
                <Option value="large">Large (最准)</Option>
              </Select>
            </Form.Item>
            <Form.Item
              label="文字转语音声音"
              name="ttsVoice"
              initialValue="zh-CN-XiaoxiaoNeural"
            >
              <Select>
                <Option value="none">关闭</Option>
                <Option value="zh-CN-XiaoxiaoNeural">晓晓 (女声)</Option>
                <Option value="zh-CN-YunxiNeural">云希 (男声)</Option>
                <Option value="zh-CN-YunyangNeural">云扬 (男声新闻)</Option>
                <Option value="zh-CN-XiaochenNeural">晓辰 (女声温柔)</Option>
                <Option value="zh-CN-XiaohanNeural">晓涵 (女声自然)</Option>
                <Option value="zh-CN-XiaomoNeural">晓墨 (女声活力)</Option>
                <Option value="zh-CN-XiaoruiNeural">晓睿 (女声感性)</Option>
                <Option value="zh-CN-XiaoshuangNeural">晓双 (女声可爱)</Option>
              </Select>
            </Form.Item>
          </Form>
        </Card>
      ),
    },
    {
      key: 'appearance',
      label: '外观设置',
      children: (
        <Card>
          <Form layout="vertical">
            <Form.Item label="主题模式">
              <Radio.Group value={theme} onChange={e => handleThemeChange(e.target.value)}>
                <Radio.Button value="light">浅色</Radio.Button>
                <Radio.Button value="dark">深色</Radio.Button>
                <Radio.Button value="system">跟随系统</Radio.Button>
              </Radio.Group>
            </Form.Item>
          </Form>
        </Card>
      ),
    },
  ];

  // 监听系统主题变化
  useEffect(() => {
    if (theme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    }
  }, [theme]);

  return (
    <div style={{ padding: '24px' }}>
      <h2 style={{ marginBottom: '24px' }}>设置</h2>
      <Tabs items={items} />
    </div>
  );
};

export default Settings; 