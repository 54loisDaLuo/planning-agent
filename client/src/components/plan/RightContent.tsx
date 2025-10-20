'use client';

import { useState } from 'react';
import { askQuestion } from '@/api/generateApi';
import { QAResult } from '@/data/generateTypes';

interface RightContentProps {
  webSearchResults?: Array<{
    url: string;
    title: string;
    content: string;
    score: number;
  }>;
}

const RightContent = ({ webSearchResults = [] }: RightContentProps) => {
  const [question, setQuestion] = useState('');
  const [qaResult, setQaResult] = useState<QAResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setIsLoading(true);
    try {
      console.log('发送问题:', question);
      const response = await askQuestion(question);
      console.log('API响应:', response);

      // 修正：后端直接返回QAResult对象，而不是{success, data}结构
      if (response) {
        console.log('问答结果数据:', response);
        setQaResult(response); // 直接设置响应数据
      } else {
        console.log('API响应为空');
      }
    } catch (error) {
      console.error('问答请求失败:', error);
      // 保持原有错误处理方式
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* 实时问答标题 */}
      <div className="text-center mb-4 flex-shrink-0">
        <h3 className="text-lg font-semibold text-blue-600">实时问答</h3>
      </div>

      {/* 主要内容区域 - 可滚动 */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        {/* 初始状态提示 */}
        {!qaResult && webSearchResults.length === 0 && (
          <div className="bg-gray-50 rounded-lg p-6 text-center">
            <div className="text-gray-500 text-sm">
              随时输入您想问的问题，包括查询资料、联系协调等......
            </div>
          </div>
        )}

        {/* 问答结果区域 - 按顺序显示所有内容 */}
        {qaResult && (
          <div className="space-y-4">
            {/* 调试信息 - 临时显示 */}
            {/* <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
              <strong>调试信息:</strong>
              <div>
                final_answer: {qaResult.final_answer ? '有数据' : '无数据'}
              </div>
              <div>
                web_search_results:{' '}
                {qaResult.web_search_results
                  ? `有${qaResult.web_search_results.length}条`
                  : '无数据'}
              </div>
              <div>confidence: {qaResult.confidence}</div>
            </div> */}

            {/* AI知识 - 显示在最上方 */}
            {qaResult.llm_knowledge_results &&
              qaResult.llm_knowledge_results.knowledge && (
                <div className="bg-white rounded-lg border p-4">
                  <div className="flex items-center mb-3">
                    <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                      AI知识库
                    </span>
                  </div>
                  <div className="space-y-3">
                    <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                      {qaResult.llm_knowledge_results.knowledge}
                    </p>
                    {/* <div className="flex items-center text-xs text-gray-500">
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        知识可信度:{' '}
                        {(
                          qaResult.llm_knowledge_results.confidence * 100
                        ).toFixed(1)}
                        %
                      </span>
                    </div> */}
                  </div>
                </div>
              )}

            {/* 网络搜索 - 显示在中间 */}
            {qaResult.web_search_results &&
              qaResult.web_search_results.length > 0 && (
                <div className="bg-white rounded-lg border p-4">
                  <div className="flex items-center mb-3">
                    <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                      网络搜索
                    </span>
                    <span className="ml-2 text-sm text-gray-500">
                      ({qaResult.web_search_results.length}条结果)
                    </span>
                  </div>
                  <div className="space-y-3">
                    {qaResult.web_search_results.map((result, index) => (
                      <div key={index} className="bg-gray-50 p-3 rounded">
                        <a
                          href={result.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline font-medium block mb-1"
                        >
                          {result.title}
                        </a>
                        <p className="text-sm text-gray-600">
                          {result.content.length > 150
                            ? `${result.content.substring(0, 150)}...`
                            : result.content}
                        </p>
                        <div className="text-xs text-gray-500 mt-2">
                          相关度: {result.score}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            {/* 上下文分析 */}
            {qaResult.context_analysis_results &&
              qaResult.context_analysis_results.analysis && (
                <div className="bg-white rounded-lg border p-4">
                  <div className="flex items-center mb-3">
                    <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium">
                      上下文分析
                    </span>
                  </div>
                  <div className="space-y-3">
                    <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                      {qaResult.context_analysis_results.analysis}
                    </p>
                    <div className="flex items-center text-xs text-gray-500">
                      <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded">
                        相关度:{' '}
                        {(
                          qaResult.context_analysis_results.relevance * 100
                        ).toFixed(1)}
                        %
                      </span>
                    </div>
                  </div>
                </div>
              )}

            {/* 综合回答 - 显示在最下方 */}
            {qaResult.final_answer && (
              <div className="bg-white rounded-lg border p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm font-medium">
                    综合回答
                  </span>
                  {/* <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                    可信度: {(qaResult.confidence * 100).toFixed(1)}%
                  </span> */}
                </div>
                <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                  {qaResult.final_answer}
                </p>
              </div>
            )}

            {/* 没有问答结果时的提示 */}
            {!qaResult && webSearchResults.length > 0 && (
              <div className="bg-gray-50 rounded-lg p-6 text-center">
                <div className="text-gray-500 text-sm">
                  请输入您的问题进行实时问答
                </div>
              </div>
            )}
          </div>
        )}

        {/* 只有联网搜索结果时的显示 */}
        {!qaResult && webSearchResults.length > 0 && (
          <div className="space-y-4">
            <div className="bg-white rounded-lg border p-4">
              <div className="flex items-center mb-3">
                <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                  联网搜索结果
                </span>
                <span className="ml-2 text-sm text-gray-500">
                  ({webSearchResults.length}条结果)
                </span>
              </div>
              <div className="space-y-3">
                {webSearchResults.map((result, index) => (
                  <div key={index} className="bg-gray-50 p-3 rounded">
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline font-medium block mb-1"
                    >
                      {result.title}
                    </a>
                    <p className="text-sm text-gray-600">
                      {result.content.length > 120
                        ? `${result.content.substring(0, 120)}...`
                        : result.content}
                    </p>
                    <div className="text-xs text-gray-500 mt-2">
                      相关度: {result.score}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 输入框区域 - 固定在底部 */}
      <div className="mt-auto flex-shrink-0 pt-4">
        <form onSubmit={handleSubmit} className="flex gap-2 w-full">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="输入您的问题..."
            className="flex-1 min-w-0 border border-gray-300 rounded px-3 py-2 focus:outline-none focus:border-blue-500 disabled:bg-gray-100"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !question.trim()}
            className="flex-shrink-0 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors min-w-[60px] disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center">
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                发送中
              </span>
            ) : (
              '发送'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default RightContent;
