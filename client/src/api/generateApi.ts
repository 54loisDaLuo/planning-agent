import {
  KnowledgeBaseFile,
  OutlineStruct,
  OutlineSection,
} from '@/data/contentTypes';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

export const classifyTitle = async (title: string) => {
  const res = await fetch(`${API_BASE_URL}/api/classify_title`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error('标题检测失败: generateApi.ts');
  return await res.json(); // { valid: boolean }
};

export const generateOutline = async (
  title: string,
  selectedKbList: KnowledgeBaseFile[]
) => {
  const res = await fetch(`${API_BASE_URL}/api/outline`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title,
      selectedKbList, // directy convey context select knowledgebase
    }),
  });
  if (!res.ok) throw new Error('生成大纲失败: generateApi.ts');
  return await res.json();
};

export const rewriteOutline = async (
  title: string,
  selectedKbList: KnowledgeBaseFile[],
  outline: string
) => {
  const res = await fetch(`${API_BASE_URL}/api/rewrite/outline`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title,
      selectedKbList,
      outline, // 使用传入的outline参数
    }),
  });
  if (!res.ok) {
    throw new Error('重写大纲失败: generateApi.ts');
  }
  return res.json();
};

export const generateContent = async (
  title: string,
  outline: string,
  context: string
) => {
  const res = await fetch(`${API_BASE_URL}/api/content`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title,
      outline,
      context,
    }),
  });
  if (!res.ok) throw new Error('生成内容失败: generateApi.ts');
  return await res.json();
};

// API for rewriting a single subtitle
export const rewriteSubtitle = async (
  plan_title: string,
  full_outline: OutlineStruct, // FIX: Changed from OutlineStruct[] to OutlineStruct
  parent_title: string,
  current_subtitle: string,
  context: string,
  user_requirement?: string
) => {
  const res = await fetch(`${API_BASE_URL}/api/rewrite/subtitle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      plan_title,
      full_outline,
      parent_title,
      current_subtitle,
      context,
      user_requirement,
    }),
  });
  if (!res.ok) throw new Error('重写二级标题失败: generateApi.ts');
  return await res.json(); // Returns { success: boolean, new_title: string }
};

// API for rewriting an entire section
export const rewriteSection = async (
  plan_title: string,
  full_outline: OutlineStruct, // FIX: Changed from OutlineStruct[] to OutlineStruct
  current_section: OutlineSection, // FIX: Changed from OutlineStruct to OutlineSection
  policy_context: string,
  user_requirement?: string
) => {
  const res = await fetch(`${API_BASE_URL}/api/rewrite/section`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      plan_title,
      full_outline,
      current_section,
      policy_context,
      user_requirement,
    }),
  });
  if (!res.ok) throw new Error('重写章节失败: generateApi.ts');
  return await res.json(); // Returns { success: boolean, new_section: OutlineStruct }
};

// API for rewriting a single paragraph of content
export const rewriteContentParagraph = async (
  plan_title: string,
  section_title: string,
  subtitle_title: string,
  current_content: string,
  context: string,
  user_requirement?: string
) => {
  const res = await fetch(`${API_BASE_URL}/api/rewrite/content_paragraph`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      plan_title,
      section_title,
      subtitle_title,
      current_content,
      context,
      user_requirement,
    }),
  });
  if (!res.ok) throw new Error('重写段落内容失败: generateApi.ts');
  return await res.json(); // Returns { success: boolean, new_content: string }
};

// 添加联网搜索接口
export const webSearchParagraph = async (
  plan_title: string,
  section_title: string,
  subtitle_title: string
) => {
  const res = await fetch(`${API_BASE_URL}/api/web_search/paragraph`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      plan_title,
      section_title,
      subtitle_title,
    }),
  });
  if (!res.ok) throw new Error('联网搜索失败: generateApi.ts');
  return await res.json(); // Returns { success: boolean, web_search_infos: list[dict] }
};
