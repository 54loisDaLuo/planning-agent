from pydantic import BaseModel
from typing import List, Optional


# For /api/classify_title
class ClassifyTitleRequest(BaseModel):
    title: str


class ClassifyTitleReturn(BaseModel):
    valid: bool


# For /api/outline
class KnowledgeBaseFile(BaseModel):
    name: str
    type: str
    category: Optional[str] = None


class GenerateOutlineRequest(BaseModel):
    title: str
    selectedKbList: List[KnowledgeBaseFile]


class GenerateOutlineReturn(BaseModel):
    success: bool
    title: str
    outline: str
    policy: str
    kb_list: List[KnowledgeBaseFile]


# For /api/content
class GenerateContentRequest(BaseModel):
    title: str
    outline: str
    context: str


class GenerateContentReturn(BaseModel):
    success: bool = True
    title: str
    content: dict | str  # accept dict for content_outline, or str for error message


# For /api/rewrite/outline
class RewriteOutlineRequest(BaseModel):
    title: str
    selectedKbList: List[KnowledgeBaseFile]
    outline: str


class RewriteOutlineReturn(BaseModel):
    success: bool
    title: str
    outline: str
    policy: str
    kb_list: List[KnowledgeBaseFile]


# For rewriting a subtitle
class RewriteSubtitleRequest(BaseModel):
    plan_title: str
    full_outline: list
    parent_title: str
    current_subtitle: str
    context: str
    user_requirement: Optional[str] = ""


class RewriteSubtitleReturn(BaseModel):
    success: bool = True
    new_title: str


# For rewriting a section
class RewriteSectionRequest(BaseModel):
    plan_title: str
    full_outline: list
    current_section: dict
    policy_context: str
    user_requirement: Optional[str] = ""


class RewriteSectionReturn(BaseModel):
    success: bool = True
    new_section: dict


# For rewriting a content paragraph
class RewriteContentParagraphRequest(BaseModel):
    plan_title: str
    section_title: str
    subtitle_title: str
    current_content: str
    context: str
    user_requirement: Optional[str] = ""


class RewriteContentParagraphReturn(BaseModel):
    success: bool = True
    new_content: str


# For /api/download
class DownloadRequest(BaseModel):
    title: str
    outline: str
    policy: str
    format: str = "docx"  # 支持 docx, txt, pdf
    download_type: str = "outline"  # (下载类型：outline-仅大纲，full-全文)


class DownloadReturn(BaseModel):
    success: bool
    message: str
    file_name: Optional[str] = None


class WebSearchParagraphRequest(BaseModel):
    plan_title: str
    section_title: str
    subtitle_title: str


class WebSearchParagraphReturn(BaseModel):
    success: bool = True
    web_search_infos: list[dict]


class QARequest(BaseModel):
    question: str
    use_web_search: bool = True
    use_llm_knowledge: bool = True
    context: Optional[str] = None


class WebSearchResult(BaseModel):
    url: str
    title: str
    content: str
    score: float


class LLMKnowledgeResult(BaseModel):
    knowledge: str
    confidence: float


class ContextAnalysisResult(BaseModel):
    analysis: str
    relevance: float


class QAResponse(BaseModel):
    final_answer: str
    web_search_results: Optional[List[WebSearchResult]] = None
    llm_knowledge_results: Optional[LLMKnowledgeResult] = None
    context_analysis_results: Optional[ContextAnalysisResult] = None
    confidence: float
    evidence_sources: List[str]
