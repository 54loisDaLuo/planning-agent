from ast import Dict
import json
import re
from langgraph.graph import StateGraph
from openai import OpenAI, api_key
from typing import Any, TypedDict, List, Optional, Tuple
import os
from dotenv import load_dotenv
from regex import P
from .prompt import Prompt
from ..api.schemas import KnowledgeBaseFile
import logging
import asyncio

from ..api.schemas import (
    QARequest,
    QAResponse,
    WebSearchResult,
    LLMKnowledgeResult,
    ContextAnalysisResult,
)

from tavily import TavilyClient

load_dotenv()
DEFAULT_MODEL_NAME = "moonshot-v1-8k"

EXAMPLE_TITLE_1 = "杭州市政府关于十五五的专项规划"
EXAMPLE_TITLE_2 = "杭州市城市轨道交通网络‘十五五’发展专项规划（2021-2025年）"

# config kimi api client, globally
# client = OpenAI(
#     api_key=os.getenv("API_KEY"),
#     base_url=os.getenv("BASE_URL"),
# )

# define state struct for langgraph
# class PlanningState(TypedDict):
#     title: str
#     # policy_research: str
#     outline: str
#     content: str


# class for embedding
class EmbeddingAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("EBD_API_KEY"),
            base_url=os.getenv("EBD_BASE_URL"),
        )
        self.model_name = os.getenv("EBD_MODEL_NAME")

    def get_embedding(self, text: str):
        """
        generate embedding for text

        生成文本的embedding
        :param text: 输入文本
        :return: 嵌入向量
        """
        try:
            response = self.client.embeddings.create(
                model=self.model_name, input=[text], encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[错误] 获取 embedding 失败: {e}")
            return None


# AI operates knowledge base
class KbAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
        )
        self.model_name = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)

    def select_kb(self, title: str, lst: List[str], num: int) -> List[str]:
        """
        从知识库中选择与标题相关的知识库ID
        :param title: 专项规划标题
        :param lst: 知识库列表
        :param num: 选择数量
        :return: 知识库ID列表
        """
        messages = Prompt.get_kb_selection_prompt(title, lst, num)
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
            )
            selection_str = completion.choices[0].message.content
            # parse JSON
            selection_obj = json.loads(selection_str)
            # from 'selected_ids' keys, safely extract array
            selected_ids = selection_obj.get("selected_ids", [])
            # remove duplicates and preserve order
            unique_ids = list(dict.fromkeys(selected_ids))
            return unique_ids
        except json.JSONDecodeError:
            print(f"[错误] AI返回的知识库选择不是有效的JSON格式: {selection_str}")
            return []
        except Exception as e:
            print(f"[错误] 调用AI选择知识库时出错: {e}")
            return []

    def abstract_kb_lst(self, title: str, content_lst: List[str]) -> str:
        """
        Summarizes a list of knowledge base content based on a title.
        """
        if not content_lst:
            return ""

        messages = Prompt.get_abstract_prompt(title, content_lst)
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            abstract = completion.choices[0].message.content
            print(f"----AI整理出来的知识库大纲---- \n{abstract}")
            return abstract.strip()
        except Exception as e:
            print(f"[错误] 调用AI生成摘要时出错: {e}")
            return ""


# check if the title is valid
class ClassificationAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
        )
        self.model_name = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)

    def classify_title(self, title: str):
        messages = Prompt.get_classification_prompt(title)
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
        )
        classification = completion.choices[0].message.content
        return classification


# class solving outline
class OutlineAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
        )
        self.model_name = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)

    def generate_outline(self, title: str, kb_abstract: str):
        """
        Generates an outline based on a title and knowledge base abstract.

        生成基于标题和知识库摘要的大纲
        :param title: 专项规划标题
        :param kb_abstract: 知识库摘要
        :return: 提示列表
        """
        messages = Prompt.get_outline_prompt(title, kb_abstract)
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            # timeout=30,  # 添加超时参数
            # response_format={"type": "json_object"},
        )
        outline = completion.choices[0].message.content
        return outline

    def get_rewrite_outline_prompt(
        self, title: str, kb_abstract: str, original_outline: str
    ):
        """
        Generates a prompt to rewrite an outline with reference to the original outline.

        重写大纲
        :param title: 专项规划标题
        :param kb_abstract: 知识库摘要
        :param original_outline: 原始大纲
        :return: 解析后的JSON对象
        """
        messages = Prompt.get_rewrite_outline_prompt(
            title, kb_abstract, original_outline
        )
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            # response_format={"type": "json_object"},
        )
        outline = completion.choices[0].message.content
        return outline

    # def rewrite_subtitle(
    #     self,
    #     plan_title: str,
    #     full_outline: list,
    #     parent_title: str,
    #     current_subtitle: str,
    #     context: str,
    #     user_requirement: str = "",
    # ):
    #     """
    #     Rewrites a single second-level title.

    #     重写单个二级标题
    #     :param plan_title: 专项规划标题
    #     :param full_outline: 完整大纲
    #     :param parent_title: 父标题
    #     :param current_subtitle: 当前二级标题
    #     :param context: 政策背景
    #     :param user_requirement: 用户要求
    #     :return: 提示列表
    #     """
    #     messages = Prompt.get_rewrite_subtitle_prompt(
    #         plan_title,
    #         full_outline,
    #         parent_title,
    #         current_subtitle,
    #         context,
    #         user_requirement,
    #     )
    #     logging.info(f"rewrite_subtitle prompt: {messages}")
    #     try:
    #         completion = self.client.chat.completions.create(
    #             model=self.model_name,
    #             messages=messages,
    #         )
    #         new_title = completion.choices[0].message.content
    #         logging.info(f"rewrite_subtitle response: {new_title}")
    #         # Clear out possible quotation marks
    #         return new_title.strip().strip('"')
    #     except Exception as e:
    #         print(f"[错误] 调用AI重写二级标题时出错: {e}")
    #         # Return to the original title to avoid front-end errors
    #         return current_subtitle

    # search 工具的具体实现，这里我们只需要返回参数即可
    def rewrite_subtitle(
        self,
        plan_title: str,
        full_outline: list,
        parent_title: str,
        current_subtitle: str,
        context: str,
        user_requirement: str = "",
    ):
        """
        Rewrites a single second-level title.

        重写单个二级标题
        :param plan_title: 专项规划标题
        :param full_outline: 完整大纲
        :param parent_title: 父标题
        :param current_subtitle: 当前二级标题
        :param context: 政策背景
        :param user_requirement: 用户要求
        :return: 提示列表
        """
        messages = Prompt.get_rewrite_subtitle_prompt(
            plan_title,
            full_outline,
            parent_title,
            current_subtitle,
            context,
            user_requirement,
        )
        logging.info(f"rewrite_subtitle prompt: {messages}")
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name, messages=messages
            )
            new_title = completion.choices[0].message.content
            logging.info(f"rewrite_subtitle response: {new_title}")
            # Clear out possible quotation marks
            return new_title.strip().strip('"')
        except Exception as e:
            print(f"[错误] 调用AI重写二级标题时出错: {e}")
            # Return to the original title to avoid front-end errors
            return current_subtitle

    def rewrite_section(
        self,
        plan_title: str,
        full_outline: list,
        current_section: dict,
        policy_context: str,
        user_requirement: str = "",
    ):
        """
        Rewrites an entire section, expecting a JSON object as return.

        重写一整段章节内容
        :param plan_title: 专项规划标题
        :param full_outline: 完整大纲
        :param current_section: 当前章节
        :param policy_context: 政策背景
        :param user_requirement: 用户要求
        :return: 提示列表
        """
        messages = Prompt.get_rewrite_section_prompt(
            plan_title, full_outline, current_section, policy_context, user_requirement
        )
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
            )
            response_str = completion.choices[0].message.content

            # 解析AI返回的JSON字符串
            parsed_json = json.loads(response_str)
            return parsed_json

        except json.JSONDecodeError:
            print(f"[错误] AI返回的章节不是有效的JSON格式: {response_str}")
            return {"error": "JSON Decode Error", "raw_content": response_str}
        except Exception as e:
            print(f"[错误] 调用AI重写章节时出错: {e}")
            return {"error": str(e)}

    def generate_outline(self, title: str, kb_abstract: str):
        messages = Prompt.get_outline_prompt(title, kb_abstract)
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
            )
            outline_str = completion.choices[0].message.content

            parsed_json = json.loads(outline_str)
            print("--- AI返回并解析后的JSON对象 ---")
            print(parsed_json)

            # Robustness fix: If the AI returns a single object instead of a list, wrap it in a list.
            if isinstance(parsed_json, dict):
                return [parsed_json]

            return parsed_json

        except json.JSONDecodeError:
            print(f"[错误] AI返回的大纲不是有效的JSON格式: {outline_str}")
            return []
        except Exception as e:
            print(f"[错误] 调用AI生成大纲时出错: {e}")
            return []

    async def generate_outline_stream(
        self, title: str, kb_abstract: str
    ):  # 缩进与上面方法一致
        """
        Generates an outline with streaming support.
        流式生成基于标题和知识库摘要的大纲
        :param title: 专项规划标题
        :param kb_abstract: 知识库摘要
        :return: 生成器，逐token返回大纲内容
        """
        messages = Prompt.get_outline_prompt(title, kb_abstract)
        try:
            # 使用正确的异步流式调用
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=1000,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    # 添加小延迟让流式效果明显
                    await asyncio.sleep(0.02)

        except Exception as e:
            print(f"[错误] 流式生成大纲时出错: {e}")
            yield f"[错误] 生成大纲时发生错误: {str(e)}"


class ContentAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("FORMAL_API_KEY"),
            base_url=os.getenv("FORMAL_BASE_URL"),
        )
        self.model_name = os.getenv("FORMAL_MODEL_NAME", DEFAULT_MODEL_NAME)

    def generate_content(self, title: str, outline: str, context: str):
        """
        Generates content based on a title, outline, and context.

        生成整篇文本内容（基于标题、大纲和上下文）
        :param title: 专项规划标题
        :param outline: 完整大纲
        :param context: 政策背景
        :return: 提示列表
        """
        try:
            messages = Prompt.get_content_prompt(title, outline, context)
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=8192,
            )
            content_str = completion.choices[0].message.content

            parsed_json = json.loads(content_str)
            print("--- AI返回的content JSON ---")
            print(parsed_json)

            return parsed_json

        except json.JSONDecodeError:
            print(f"[错误] AI返回的内容不是有效的JSON格式: {content_str}")
            return {"error": "JSON Decode Error", "raw_content": content_str}
        except Exception as e:
            print(f"[错误] 调用AI生成内容时出错: {e}")
            return {"error": str(e)}

    def rewrite_content(
        self, title: str, outline: str, original_full_content: str, context: str = ""
    ) -> list[dict]:
        # def rewrite_content(
        #     self, title: str, outline: str, original_full_content: str, context: str = ""
        # ) -> list[dict]:
        """
        Rewrites the full content of a document.

        重写整篇文档的内容
        :param title: 专项规划标题
        :param outline: 完整大纲
        :param original_full_content: 原始全文内容
        :param context: 政策背景
        :return: 提示列表
        """
        try:
            messages = Prompt.get_rewrite_content_prompt(
                title, outline, original_full_content, context
            )
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=8192,
            )
            content_str = completion.choices[0].message.content

            parsed_json = json.loads(content_str)
            print("--- AI返回的content JSON ---")
            print(parsed_json)

            return parsed_json

        except json.JSONDecodeError:
            print(f"[错误] AI返回的内容不是有效的JSON格式: {content_str}")
            return {"error": "JSON Decode Error", "raw_content": content_str}
        except Exception as e:
            print(f"[错误] 调用AI生成内容时出错: {e}")
            return {"error": str(e)}

    def rewrite_content_paragraph(
        self,
        plan_title: str,
        section_title: str,
        subtitle_title: str,
        current_content: str,
        context: str,
        user_requirement: str = "",
    ):
        """
        Rewrites a single paragraph of content.

        重写单个段落内容
        :param plan_title: 专项规划标题
        :param section_title: 章节标题
        :param subtitle_title: 二级标题
        :param current_content: 当前段落内容
        :param context: 政策背景
        :param user_requirement: 用户要求

        :return: 提示列表
        """
        messages = Prompt.get_rewrite_paragraph_prompt(
            plan_title,
            section_title,
            subtitle_title,
            current_content,
            context,
            user_requirement,
        )
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=4096,  # leave sufficient space for rewriting the content
            )
            new_content = completion.choices[0].message.content
            # Return plain text directly
            return new_content.strip()
        except Exception as e:
            print(f"[错误] 调用AI重写段落内容时出错: {e}")
            # Return the original content when an error occurs to prevent front-end errors
            return current_content


# test if api works
class TestAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
        )
        self.model_name = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)

    def test_api(self):
        messages = Prompt.get_test_prompt()
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
        )
        answer = completion.choices[0].message.content

        return answer


class WebSearchAgent:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")

    def web_search_content_paragraph(
        self,
        plan_title: str,
        section_title: str,
        subtitle_title: str,
    ):
        """
        Web search for a single paragraph of content.

        搜索单个段落的内容
        :param plan_title: 专项规划标题
        :param section_title: 章节标题
        :param subtitle_title: 二级标题
        :return: 搜索结果列表
        """
        tavily_client = TavilyClient(api_key=self.api_key)
        query = Prompt.web_search_content_paragraph_prompt(
            plan_title, section_title, subtitle_title
        )
        response = tavily_client.search(query)
        print(response["results"])

        return response["results"]


class QAAgent:
    """问答Agent - 三路并行架构"""

    def __init__(self):
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        self.client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
        )
        self.model_name = os.getenv("MODEL_NAME")

    async def ask_question(self, request: QARequest) -> QAResponse:
        """处理问答请求 - 三路并行处理"""

        # 并行执行三路搜索
        tasks = []
        # 路线1（Web搜索）：
        if request.use_web_search:
            tasks.append(self.qa_web_search(request.question))

        # 路线2（LLM知识）：
        if request.use_llm_knowledge:
            tasks.append(self.qa_llm_knowledge(request.question))

        # # 路线3（上下文分析）：
        # if request.context:
        #     tasks.append(
        #         self.real_qa_context_analysis(request.question, request.context)
        #     )

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        web_search_results = None
        llm_knowledge_results = None
        context_analysis_results = None

        for result in results:
            if isinstance(result, Exception):
                continue
            if isinstance(result, list):  # Web搜索返回列表
                web_search_results = (
                    [WebSearchResult(**r) for r in result] if result else None
                )
            elif isinstance(result, dict) and "knowledge" in result:  # LLM知识
                llm_knowledge_results = LLMKnowledgeResult(**result)
            elif isinstance(result, dict) and "analysis" in result:  # 上下文分析
                context_analysis_results = ContextAnalysisResult(**result)

        # 整合分析生成最终答案
        final_answer, confidence, evidence_sources = (
            await self.qa_integrate_and_analyze(
                request.question,
                web_search_results,
                llm_knowledge_results,
                context_analysis_results,
            )
        )

        return QAResponse(
            final_answer=final_answer,
            web_search_results=web_search_results,
            llm_knowledge_results=llm_knowledge_results,
            context_analysis_results=context_analysis_results,
            confidence=confidence,
            evidence_sources=evidence_sources,
        )

    async def qa_web_search(self, question: str) -> List[Dict]:
        """路线1: Tavily Web搜索"""
        try:
            response = self.tavily_client.search(
                query=question, search_depth="advanced", max_results=5
            )
            results = response.get("results", [])
            # 转换为标准格式
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "url": result.get("url", ""),
                        "title": result.get("title", ""),
                        "content": result.get("content", ""),
                        "score": result.get("score", 0.0),
                    }
                )
            return formatted_results
        except Exception as e:
            print(f"Web搜索错误: {e}")
            return []

    async def qa_llm_knowledge(self, question: str) -> Dict:
        """路线2: LLM知识搜索"""
        try:
            prompt = Prompt.qa_llm_knowledge_prompt(question)

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=prompt,
                temperature=0.3,
                max_tokens=800,
            )

            knowledge = response.choices[0].message.content
            # 基于回答质量评估置信度
            confidence = min(len(knowledge) / 1000, 0.95) if knowledge else 0.5

            return {"knowledge": knowledge, "confidence": confidence}

        except Exception as e:
            print(f"LLM知识搜索错误: {e}")
            return {"knowledge": "无法获取相关知识", "confidence": 0.1}

    async def qa_context_analysis(self, question: str, context: str) -> Dict:
        """路线3: 上下文分析"""
        try:
            prompt = Prompt.qa_context_analysis_prompt(context, question)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=prompt,
                temperature=0.3,
                max_tokens=600,
            )

            analysis = response.choices[0].message.content
            # 基于分析深度评估相关性
            relevance = min(len(analysis) / 800, 0.95) if analysis else 0.3

            return {"analysis": analysis, "relevance": relevance}

        except Exception as e:
            print(f"上下文分析错误: {e}")
            return {"analysis": "上下文分析失败", "relevance": 0.1}

    async def qa_integrate_and_analyze(
        self,
        question: str,
        web_results: Optional[List[WebSearchResult]],
        llm_results: Optional[LLMKnowledgeResult],
        context_results: Optional[ContextAnalysisResult],
    ) -> Tuple[str, float, List[str]]:
        """整合三路结果并生成最终答案"""
        try:
            # 构建整合提示词
            messages = Prompt.qa_build_integration_prompt(
                question, web_results, llm_results, context_results
            )

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
                max_tokens=1200,
            )

            final_answer = response.choices[0].message.content

            # 计算综合置信度
            confidence_sources = []
            if web_results:
                avg_web_score = (
                    sum(r.score for r in web_results) / len(web_results)
                    if web_results
                    else 0
                )
                confidence_sources.append(avg_web_score * 0.4)  # Web搜索权重40%

            if llm_results:
                confidence_sources.append(
                    llm_results.confidence * 0.35
                )  # LLM知识权重35%

            if context_results:
                confidence_sources.append(
                    context_results.relevance * 0.25
                )  # 上下文分析权重25%

            final_confidence = (
                sum(confidence_sources) / len(confidence_sources)
                if confidence_sources
                else 0.5
            )

            # 提取证据来源
            evidence_sources = self.qa_extract_evidence_sources(
                web_results, llm_results, context_results
            )

            return final_answer, final_confidence, evidence_sources

        except Exception as e:
            print(f"整合分析错误: {e}")
            return "抱歉，暂时无法生成完整答案。", 0.3, ["系统错误"]

    #     def _build_integration_prompt(
    #         self,
    #         question: str,
    #         web_results: Optional[List[WebSearchResult]],
    #         llm_results: Optional[LLMKnowledgeResult],
    #         context_results: Optional[ContextAnalysisResult],
    #     ) -> str:
    #         """构建整合分析提示词"""
    #         prompt = f"""请基于以下三路信息源，为用户问题生成最准确、最全面的答案。

    # 用户问题：{question}

    # """

    #         # Web搜索结果
    #         if web_results:
    #             prompt += "【网络搜索结果】\n"
    #             for i, result in enumerate(web_results[:3], 1):
    #                 prompt += f"{i}. {result.title}\n"
    #                 prompt += f"   内容：{result.content[:150]}...\n"
    #                 prompt += f"   相关度：{result.score:.2f}\n\n"

    #         # LLM知识结果
    #         if llm_results:
    #             prompt += "【专业知识库】\n"
    #             prompt += f"{llm_results.knowledge}\n"
    #             prompt += f"置信度：{llm_results.confidence:.2f}\n\n"

    #         # 上下文分析结果
    #         if context_results:
    #             prompt += "【上下文分析】\n"
    #             prompt += f"{context_results.analysis}\n"
    #             prompt += f"相关性：{context_results.relevance:.2f}\n\n"

    #         prompt += """请生成最终答案，要求：
    # 1. 综合所有可用信息
    # 2. 优先采用高置信度的信息源
    # 3. 明确标注信息来源
    # 4. 如果信息冲突，说明不同观点
    # 5. 给出最合理的结论

    # 请开始生成最终答案："""

    #         return prompt

    def qa_extract_evidence_sources(
        self,
        web_results: Optional[List[WebSearchResult]],
        llm_results: Optional[LLMKnowledgeResult],
        context_results: Optional[ContextAnalysisResult],
    ) -> List[str]:
        """提取证据来源"""
        sources = []

        if web_results:
            sources.append(f"网络搜索结果：{len(web_results)}条")

        if llm_results and llm_results.confidence > 0.3:
            sources.append("专业知识库")

        if context_results and context_results.relevance > 0.3:
            sources.append("上下文分析")

        return sources if sources else ["信息不足"]


# test
if __name__ == "__main__":
    tested_agent = ClassificationAgent()
    answer = tested_agent.classify_title("杭州市政府‘十五五’建设的专项规划（2025）")
    print(answer)
