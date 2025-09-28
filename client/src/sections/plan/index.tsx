'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState, useRef } from 'react';
import {
  generateOutline,
  generateContent,
  generateOutlineStream,
  rewriteOutline,
} from '../../api/generateApi';
import {
  GenerateOutlineResponse,
  GenerateContentResponse,
} from '@/data/generateTypes';
import RightContent from '@/components/plan/RightContent';
import LeftContent from '@/components/plan/LeftContent';
import { useContext } from 'react';
import { useKnowledgeBase } from '@/contexts/KnowledgeBaseContext';
import { PageMode, OutlineStruct } from '@/data/contentTypes';

const Plan = () => {
  const searchParams = useSearchParams();
  const title = searchParams.get('title') || '';
  const [data, setData] = useState<GenerateOutlineResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const { selectedKbList } = useKnowledgeBase();
  const [pageMode, setPageMode] = useState<PageMode>('outline');
  // 在Plan组件中添加状态
  const [webSearchResults, setWebSearchResults] = useState<
    Array<{
      url: string;
      title: string;
      content: string;
      score: number;
    }>
  >([]);

  // Content part
  const [fullContent, setFullContent] =
    useState<GenerateContentResponse | null>(null);
  const [isContentLoading, setIsContentLoading] = useState(false);

  // General Rewrite
  const [isRewriting, setIsRewriting] = useState(false);
  // 新增：为“重写全部内容”功能创建独立的加载状态
  const [isRewritingContent, setIsRewritingContent] = useState(false);

  // Segmentation ratio status
  const [leftWidth, setLeftWidth] = useState(60); // default left 60%
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const [streamingData, setStreamingData] = useState<{
    policy: string;
    outline: string;
    isComplete: boolean;
  }>({
    policy: '',
    outline: '',
    isComplete: false,
  });
  const [isStreaming, setIsStreaming] = useState(false);

  useEffect(() => {
    if (title) {
      setLoading(true);
      // 使用流式接口替代原来的同步接口
      handleStreamOutline();
    }
  }, [title]);

  // 添加这个新的useEffect来处理流式数据的实时显示
  // 优化这个useEffect，避免过于频繁的更新
  // 优化这个useEffect，避免过于频繁的更新
  useEffect(() => {
    if (isStreaming && streamingData && streamingData.outline) {
      // 只有在outline有实际变化时才更新data
      setData((prevData) => {
        const currentOutline = prevData?.outline;
        const newOutline = streamingData.outline;

        // 只有当outline确实发生变化时才更新
        if (currentOutline !== newOutline && newOutline.length > 0) {
          console.log('更新data.outline，新长度:', newOutline.length);
          return {
            ...(prevData || { success: true, title, kb_list: selectedKbList }),
            outline: newOutline,
            policy: streamingData.policy,
          };
        }
        return prevData;
      });
    }
  }, [
    isStreaming,
    streamingData?.outline,
    streamingData?.policy,
    title,
    selectedKbList,
  ]);

  const handleStreamOutline = async () => {
    setLoading(true);
    setIsStreaming(true);
    setStreamingData({ policy: '', outline: '', isComplete: false });

    console.log('开始流式生成，标题:', title, '知识库:', selectedKbList);

    try {
      await generateOutlineStream(
        title,
        selectedKbList,
        (data) => {
          console.log('收到流式数据:', data);
          switch (data.type) {
            case 'policy':
              setStreamingData((prev) => {
                console.log(
                  '更新policy:',
                  data.content,
                  '当前policy长度:',
                  prev.policy.length
                );
                return { ...prev, policy: data.content };
              });
              break;
            case 'outline':
              if (data.token) {
                setStreamingData((prev) => {
                  const newOutline = prev.outline + data.token;
                  console.log(
                    '更新outline token:',
                    data.token,
                    '当前长度:',
                    newOutline.length
                  );
                  return { ...prev, outline: newOutline };
                });
              }
              break;
            case 'complete_outline':
              console.log('收到完整大纲');
              break;
            case 'complete':
              setStreamingData((prev) => {
                console.log('流式传输完成');
                return { ...prev, isComplete: true };
              });
              break;
          }
        },
        (completeData) => {
          // 使用函数式更新避免闭包问题
          setStreamingData((currentStreamingData) => {
            console.log('流式传输完成，最终数据:', currentStreamingData);
            setData({
              success: true,
              title,
              outline: currentStreamingData.outline,
              policy: currentStreamingData.policy,
              kb_list: selectedKbList,
            });
            setLoading(false);
            setIsStreaming(false);
            return currentStreamingData;
          });
        },
        (error) => {
          console.error('流式生成失败:', error);
          setLoading(false);
          setIsStreaming(false);
        }
      );
    } catch (error) {
      console.error('启动流式生成失败:', error);
      setLoading(false);
      setIsStreaming(false);
    }
  };
  // function rewrite outline
  const handleRewriteOutline = async () => {
    if (!data || !data.policy || !data.outline) {
      console.error('无法重写：缺少原始数据或 policy 或 outline');
      return;
    }
    setIsRewriting(true);
    try {
      const outlineString =
        typeof data.outline === 'string'
          ? data.outline
          : JSON.stringify(data.outline);
      const res = await rewriteOutline(title, selectedKbList, outlineString);

      // 处理后端返回的outline格式（包含```json标记的字符串）
      let parsedOutline = res.outline;
      if (
        typeof parsedOutline === 'string' &&
        parsedOutline.includes('```json')
      ) {
        // 提取JSON部分，去除```json标记
        const jsonMatch = parsedOutline.match(/```json\n([\s\S]*?)\n```/);
        if (jsonMatch && jsonMatch[1]) {
          parsedOutline = JSON.parse(jsonMatch[1]);
        }
      }

      setData((prevData) => ({
        ...prevData!,
        outline: parsedOutline,
        policy: res.policy,
        kb_list: res.kb_list,
      }));
    } catch (err) {
      console.error('(from Plan index.tsx) rewriteOutline API failed:', err);
    } finally {
      setIsRewriting(false);
    }
  };

  // function for adding content
  const handleGenerateContent = async () => {
    if (!data || !data.outline || !data.policy) return;

    setIsContentLoading(true);
    try {
      const outlineString =
        typeof data.outline === 'string'
          ? data.outline
          : JSON.stringify(data.outline);

      const res = await generateContent(title, outlineString, data.policy);
      setFullContent(res);
      setPageMode('content'); // Switch pages after success
    } catch (err) {
      console.error('(from Plan index.tsx) generateContent API failed:', err);
    } finally {
      setIsContentLoading(false);
    }
  };

  // 新增：处理“重写全部内容”的逻辑
  const handleRewriteAllContent = async () => {
    if (!data || !fullContent) {
      console.error('无法重写内容：缺少大纲或原始内容。');
      return;
    }
    setIsRewritingContent(true);
    try {
      // 复用 generateContent API
      const res = await generateContent(
        title,
        JSON.stringify(fullContent.content.content_outline),
        data.policy
      );
      setFullContent(res); // 更新内容状态
    } catch (err) {
      console.error(
        '(from Plan index.tsx) handleRewriteAllContent API failed:',
        err
      );
    } finally {
      setIsRewritingContent(false);
    }
  };

  // 在Plan页面中添加状态同步函数
  const handleOutlineUpdate = (newOutline: OutlineStruct) => {
    setData((prevData) => ({
      ...prevData!,
      outline: newOutline,
    }));
  };

  // dragging process function
  const handleMouseDown = () => setIsDragging(true);

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging || !containerRef.current) return;
    const containerRect = containerRef.current.getBoundingClientRect();
    const containerWidth = containerRect.width;
    const mouseX = e.clientX - containerRect.left;
    const newLeftWidth = Math.min(
      Math.max((mouseX / containerWidth) * 100, 20),
      80
    );
    setLeftWidth(newLeftWidth);
  };

  const handleMouseUp = () => setIsDragging(false);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isDragging]);

  return (
    <main className="h-screen flex flex-col bg-gray-50 p-6">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-gray-800">
          {title || '专项规划生成'}
        </h1>
      </div>
      {/* main content */}
      <div
        ref={containerRef}
        className="w-full px-4 mx-auto hidden lg:flex gap-1 flex-1 min-h-0"
      >
        {/* left box */}
        <div
          className="bg-white rounded-lg border border-plagt-blue-1 p-6 shadow-sm flex flex-col h-full min-h-0"
          style={{ width: `${leftWidth}%` }}
        >
          <LeftContent
            loading={loading || isContentLoading}
            data={data}
            pageMode={pageMode}
            setPageMode={setPageMode}
            onGenerateContent={handleGenerateContent}
            fullContent={fullContent}
            onRewriteOutline={handleRewriteOutline}
            isRewriting={isRewriting}
            onRewriteContent={handleRewriteAllContent}
            isRewritingContent={isRewritingContent}
            onOutlineUpdate={handleOutlineUpdate}
            onWebSearchResults={setWebSearchResults} // 添加这行
            // 新增：流式数据处理
            // 新增：流式数据处理
            streamingData={streamingData}
            isStreaming={isStreaming}
          />
        </div>
        {/* drag dividing line */}
        <div
          className={`w-2 bg-gray-300 hover:bg-blue-400 cursor-col-resize flex items-center justify-center rounded transition-colors ${
            isDragging ? 'bg-blue-500' : ''
          }`}
          onMouseDown={handleMouseDown}
        >
          <div className="w-1 h-8 bg-white rounded opacity-70"></div>
        </div>
        {/* right box */}
        <div
          className="bg-white rounded-lg border border-plagt-blue-1 p-6 shadow-sm flex flex-col h-full min-h-0"
          style={{ width: `${100 - leftWidth}%` }}
        >
          <RightContent webSearchResults={webSearchResults} />
        </div>
      </div>
      {/* modile layout */}
      <div className="max-w-4xl mx-auto lg:hidden space-y-6 flex-1 min-h-0">
        <div className="bg-white rounded-lg border border-plagt-blue-1 p-6 shadow-sm flex flex-col h-[80vh] min-h-0">
          <LeftContent
            loading={loading || isContentLoading}
            data={data}
            pageMode={pageMode}
            setPageMode={setPageMode}
            onGenerateContent={handleGenerateContent}
            fullContent={fullContent}
            onRewriteOutline={handleRewriteOutline}
            isRewriting={isRewriting}
            onRewriteContent={handleRewriteAllContent}
            isRewritingContent={isRewritingContent}
            onOutlineUpdate={handleOutlineUpdate}
            onWebSearchResults={setWebSearchResults} // 添加这行
            // 移动端也需要流式数据
            streamingData={streamingData}
            isStreaming={isStreaming}
          />
        </div>
        <div className="bg-white rounded-lg border border-plagt-blue-1 p-6 shadow-sm flex flex-col h-[80vh] min-h-0">
          <RightContent webSearchResults={webSearchResults} />
        </div>
      </div>
    </main>
  );
};

export default Plan;
