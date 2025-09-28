import {
  GenerateOutlineResponse,
  GenerateContentResponse,
} from '@/data/generateTypes';
import { PageMode, OutlineStruct } from '@/data/contentTypes';
import React from 'react';
import OutlineEditor from './internals/OutlineEditor';
import PolicyDisplay from './PolicyDisplay';
import RewriteOutlineBtn from './buttons/RewriteOutlineBtn';
import DownloadBtn from './buttons/DownloadBtn';
import WriteContentBtn from './buttons/WriteContentBtn';
import RewriteContentBtn from './buttons/RewriteContentBtn';
import FinishPlanningBtn from './buttons/FinishPlanningBtn';
import ContentEditor from './internals/ContentEditor';

interface LeftContentProps {
  loading: boolean;
  data: GenerateOutlineResponse | null;
  pageMode: PageMode;
  setPageMode: (mode: PageMode) => void;
  onGenerateContent: () => void;
  fullContent: GenerateContentResponse | null;
  onRewriteOutline: () => void;
  isRewriting: boolean;
  onRewriteContent: () => void;
  isRewritingContent: boolean;
  streamingData?: {
    policy: string;
    outline: string;
    isComplete: boolean;
  };
  isStreaming?: boolean;
  onOutlineUpdate: (newOutline: OutlineStruct) => void;
  onWebSearchResults?: (
    results: Array<{
      url: string;
      title: string;
      content: string;
      score: number;
    }>
  ) => void;
}

// 清理流式大纲显示，只保留中文、括号和标点
const cleanStreamingOutline = (text: string): string => {
  if (!text) return '';

  // 移除JSON格式的引号、冒号等符号，只保留中文、括号、数字和标点
  let cleanedText = text
    .replace(/"/g, '') // 移除双引号
    .replace(/title/g, '') // 移除title字段名
    .replace(/children/g, '') // 移除children字段名
    .replace(/:/g, '') // 移除冒号
    .replace(/{/g, '') // 移除左花括号
    .replace(/}/g, '') // 移除右花括号
    .replace(/\[/g, '') // 移除左方括号
    .replace(/\]/g, '') // 移除右方括号
    .replace(/,/g, '') // 移除逗号
    .replace(/\( /g, '(') // 清理括号内的空格
    .replace(/ \)/g, ')') // 清理括号内的空格
    .trim();

  // 按行处理，保留有意义的行
  const lines = cleanedText.split('\n');
  const meaningfulLines = lines.filter((line) => {
    const trimmedLine = line.trim();
    if (!trimmedLine) return false;

    // 检查是否包含中文或有效的标题结构
    const hasChinese = /[\u4e00-\u9fa5]/.test(trimmedLine);
    const hasValidStructure =
      /^[一二三四五六七八九十]+[、.]|^（[一二三四五六七八九十]+）/.test(
        trimmedLine
      );

    return hasChinese || hasValidStructure;
  });

  return meaningfulLines.join('\n');
};

const LeftContent = ({
  loading,
  data,
  pageMode,
  setPageMode,
  onGenerateContent,
  fullContent,
  onRewriteOutline,
  isRewriting,
  onRewriteContent,
  isRewritingContent,
  onOutlineUpdate,
  onWebSearchResults,
  streamingData,
  isStreaming,
}: LeftContentProps) => {
  const displayData =
    isStreaming && streamingData
      ? {
          title: data?.title || '',
          policy: streamingData.policy,
          outline: streamingData.outline,
          kb_list: data?.kb_list || [],
        }
      : data;

  // 清理后的流式大纲
  const cleanedStreamingOutline = streamingData?.outline
    ? cleanStreamingOutline(streamingData.outline)
    : '';

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Policy Display Section */}
      {displayData && displayData.policy && (
        <PolicyDisplay
          policy={displayData.policy}
          kb_list={displayData.kb_list}
        />
      )}

      {/* middle rollable */}
      <div className="flex-1 min-h-0 overflow-y-auto py-2">
        <div className="space-y-6">
          {/* 流式传输时显示大纲 */}
          {isStreaming ? (
            pageMode === 'outline' ? (
              <div className="whitespace-pre-wrap text-gray-800 leading-relaxed font-medium">
                {cleanedStreamingOutline || '正在生成大纲...'}
              </div>
            ) : (
              <div className="text-center text-gray-500 italic">
                流式内容生成暂不支持实时预览，请等待生成完成
              </div>
            )
          ) : loading ? (
            <div className="text-center text-gray-500">正在生成...</div>
          ) : data ? (
            pageMode === 'outline' ? (
              <OutlineEditor
                initialData={data}
                onOutlineUpdate={onOutlineUpdate}
              />
            ) : (
              fullContent &&
              data && (
                <ContentEditor
                  initialContentData={fullContent.content}
                  planTitle={data.title}
                  policyContext={data.policy}
                  onWebSearchResults={onWebSearchResults}
                />
              )
            )
          ) : (
            <div className="text-center text-gray-400">
              请先在首页输入标题以生成大纲
            </div>
          )}
        </div>
      </div>

      {/* button */}
      <div className="mt-auto flex flex-wrap gap-2 justify-between items-center pt-4">
        {pageMode === 'outline' ? (
          <>
            <RewriteOutlineBtn
              onClick={onRewriteOutline}
              isLoading={isRewriting}
            />
            <div className="flex flex-wrap gap-2">
              <WriteContentBtn onClick={onGenerateContent} />
              {data && !isStreaming && (
                <DownloadBtn
                  title={data.title}
                  outline={JSON.stringify(data.outline)}
                  policy={data.policy}
                  downloadType="outline"
                />
              )}
            </div>
          </>
        ) : (
          <>
            <RewriteContentBtn
              onClick={onRewriteContent}
              isLoading={isRewritingContent}
              disabled={!fullContent}
            />
            <div className="flex flex-wrap gap-2">
              <FinishPlanningBtn />
              {data && (
                <DownloadBtn
                  title={data.title}
                  outline={JSON.stringify(fullContent?.content || data.outline)}
                  policy={data.policy}
                  downloadType="full"
                />
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default LeftContent;
