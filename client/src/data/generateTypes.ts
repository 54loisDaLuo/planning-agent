import { OutlineStruct } from './contentTypes';
import { KnowledgeBaseFile } from './contentTypes';
import { generateContent } from '../api/generateApi';

// this is used for getting api response, not in the ui
export interface GenerateOutlineResponse {
  success: boolean;
  title: string;
  outline: string;
  policy: string;
  kb_list: KnowledgeBaseFile[];
}

// content
export interface ContentOutlineItem {
  title: string;
  children: {
    title: string;
    content: string;
  }[];
}

export interface GenerateContentResponse {
  success: boolean;
  title: string;
  content: {
    content_outline: ContentOutlineItem[];
  };
}

// 新增流式数据接口
export interface StreamingOutlineData {
  type: 'policy' | 'outline' | 'complete_outline' | 'complete' | 'error';
  content?: string;
  token?: string;
}

export interface StreamingOutlineResponse {
  success: boolean;
  title: string;
  outline: string;
  policy: string;
  kb_list: KnowledgeBaseFile[];
}

// 实时问答类型定义
export interface LLMKnowledgeResult {
  knowledge: string;
  confidence: number;
}

export interface ContextAnalysisResult {
  analysis: string;
  relevance: number;
}

export interface QAResult {
  final_answer: string;
  web_search_results?: Array<{
    url: string;
    title: string;
    content: string;
    score: number;
  }>;
  llm_knowledge_results?: LLMKnowledgeResult; // 改为对象类型
  context_analysis_results?: ContextAnalysisResult; // 改为对象类型
  confidence: number;
  evidence_sources: string[]; // 添加缺失的字段
}

export interface QARequest {
  question: string;
}
