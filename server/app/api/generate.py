from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
from ..ai.agent import ClassificationAgent, OutlineAgent, ContentAgent
from typing import List, Optional
from .schemas import (
    ClassifyTitleRequest,
    ClassifyTitleReturn,
    GenerateOutlineRequest,
    GenerateOutlineReturn,
    GenerateContentRequest,
    GenerateContentReturn,
    RewriteOutlineRequest,
    RewriteOutlineReturn,
    RewriteSubtitleRequest,
    RewriteSubtitleReturn,
    RewriteSectionRequest,
    RewriteSectionReturn,
    RewriteSectionRequest,
    RewriteSectionReturn,
    RewriteContentParagraphRequest,
    RewriteContentParagraphReturn,
)
from ..ai.graph.outline import app as outline_graph_app
from ..ai.graph.content import app as content_graph_app
from ..ai.graph.rewrite_outline import app as rewrite_outline_graph_app
import traceback
import logging

generate_router = APIRouter()


classify_agent = ClassificationAgent()
outline_agent = OutlineAgent()
content_agent = ContentAgent()


@generate_router.post("/api/classify_title")
async def router_classify_title(req: ClassifyTitleRequest):
    """
    标题检测接口
    :param req: ClassifyTitleRequest -> title: str
    :return: ClassifyTitleReturn -> valid: bool
    """
    logging.info(f"router_classify_title, req:\n{req}")
    try:
        result = classify_agent.classify_title(req.title)
        return ClassifyTitleReturn(
            valid=(result.strip().lower() == "true")
        )  # return { valid: True/False }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"标题检测失败: {str(e)}  (from router_classify_title, generate.py)",
        )


@generate_router.post("/api/outline")
async def router_generate_outline(req: GenerateOutlineRequest):
    """
    大纲生成接口
    :param req: GenerateOutlineRequest
                -> title: str (description="用户输入的标题")
                    ,selectedKbList: List[KnowledgeBase](description="用户选择的知识库")
    :return: GenerateOutlineReturn
                -> success: bool
                    ,title: str(description="用户输入的标题")
                    ,outline: str(description="生成的大纲"),
                    ,policy: str(description="生成的政策总结"),
                    ,kb_list: List[KnowledgeBase](description="使用的知识库")
    """
    logging.info(f"router_generate_outline, req:\n{req}")
    try:
        # The initial state requires 'title' and 'selectedKbList'.
        # The 'policy' and 'outline' fields will be populated by the graph.
        initial_state = {
            "title": req.title,
            "selectedKbList": [kb.model_dump() for kb in req.selectedKbList],
            "policy": "",
            # outline is not needed for input
        }

        final_state = await outline_graph_app.ainvoke(initial_state)
        result_outline = final_state.get("outline", "生成大纲失败，未找到结果。")
        result_policy = final_state.get("policy", "未能生成政策总结。")
        result_kb_list = final_state.get("selectedKbList", [])

        return GenerateOutlineReturn(
            success=True,
            title=req.title,
            outline=result_outline,
            policy=result_policy,
            kb_list=result_kb_list,
        )

    except Exception as e:
        print(f"(from router_generate_outline, generate.py) 生成大纲异常: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"生成失败: {str(e)}, (from router_generate_outline, generate.py)",
        )


@generate_router.post("/api/rewrite/outline")
async def router_rewrite_outline(req: RewriteOutlineRequest):
    """
    大纲重写接口
    :param req: RewriteOutlineRequest
                -> title: str (description="用户输入的标题")
                    ,selectedKbList: List[KnowledgeBaseFile](description="用户选择的知识库")
                    ,outline: str(description="用户输入的大纲")
                    ,context: str(description="用户输入的上下文")
    :return: RewriteOutlineReturn
                -> success: bool
                    ,title: str(description="用户输入的标题")
                    ,outline: str(description="重写后的大纲")
                    ,policy: str(description="生成的政策总结")
                    ,kb_list: List[KnowledgeBaseFile](description="使用的知识库")
    """
    logging.info(f"router_rewrite_outline, req:\n{req}")
    try:
        # The initial state requires 'title' and 'selectedKbList'.
        # The 'policy' and 'outline' fields will be populated by the graph.
        initial_state = {
            "title": req.title,
            "selectedKbList": [kb.model_dump() for kb in req.selectedKbList],
            "policy": "",
            "outline": req.outline,
        }

        final_state = await rewrite_outline_graph_app.ainvoke(initial_state)

        result_outline = final_state.get("outline", "生成大纲失败，未找到结果。")
        result_policy = final_state.get("policy", "未能生成政策总结。")
        result_kb_list = final_state.get("selectedKbList", [])

        return RewriteOutlineReturn(
            success=True,
            title=req.title,
            outline=result_outline,
            policy=result_policy,
            kb_list=result_kb_list,
        )
    except Exception as e:
        print(f"(from router_generate_outline, generate.py) 生成大纲异常: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"生成失败: {str(e)}, (from router_generate_outline, generate.py)",
        )


@generate_router.post("/api/content")
async def router_generate_content(req: GenerateContentRequest):
    """
    整篇内容生成接口
    :param req: GenerateContentRequest
                -> title: str (description="用户输入的标题")
                    ,outline: str(description="用户输入的大纲")
                    ,context: str(description="用户输入的上下文")
    :return: GenerateContentReturn
                -> success: bool
                    ,title: str(description="用户输入的标题")
                    ,content: str(description="生成的内容")
    """
    logging.info(f"router_generate_content, req:\n{req}")
    try:
        initial_state = {
            "title": req.title,
            "outline": req.outline,
            "context": req.context,
        }

        final_state = await content_graph_app.ainvoke(initial_state)
        result_content = final_state.get("content", "生成内容失败，未找到结果。")

        return GenerateContentReturn(
            success=True,
            title=req.title,
            content=result_content,
        )

    except Exception as e:
        print(f"(from router_generate_content, generate.py) 生成内容异常: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"生成内容失败: {str(e)}, (from router_generate_content, generate.py)",
        )


@generate_router.post("/api/rewrite/subtitle")
async def router_rewrite_subtitle(req: RewriteSubtitleRequest):
    """
    单个二级标题重写接口
    :param req: RewriteSubtitleRequest
                -> plan_title: str (description="用户输入的标题")
                    ,full_outline: list(description="用户输入的大纲")
                    ,parent_title: str(description="用户输入的父标题")
                    ,current_subtitle: str(description="用户输入的当前二级标题")
                    ,context: str(description="用户输入的上下文")
                    ,user_requirement: Optional[str] = ""(description="用户输入的需求")
    :return: RewriteSubtitleReturn
                -> success: bool
                    ,new_title: str(description="重写后的二级标题")
    """
    logging.info(f"router_rewrite_subtitle, req:\n{req}")
    try:
        new_title = outline_agent.rewrite_subtitle(
            plan_title=req.plan_title,
            full_outline=req.full_outline,
            parent_title=req.parent_title,
            current_subtitle=req.current_subtitle,
            context=req.context,
            user_requirement=req.user_requirement,
        )
        return RewriteSubtitleReturn(new_title=new_title)
    except Exception as e:
        print(f"(from router_rewrite_subtitle, generate.py) 重写二级标题异常: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"重写二级标题失败: {str(e)}")


@generate_router.post("/api/rewrite/section")
async def router_rewrite_section(req: RewriteSectionRequest):
    """
    单个章节重写接口（仅有大纲重写单个一级标题及二级标题、）
    :param req: RewriteSectionRequest
                -> plan_title: str (description="用户输入的标题")
                    ,full_outline: list(description="用户输入的大纲")
                    ,current_section: dict(description="用户输入的当前章节")
                    ,policy_context: str(description="用户输入的政策上下文")
                    ,user_requirement: Optional[str] = ""(description="用户输入的需求")
    :return: RewriteSectionReturn
                -> success: bool
                    ,new_section: str(description="重写后的章节")
    """
    logging.info(f"router_rewrite_section, req:\n{req}")
    try:
        new_section = outline_agent.rewrite_section(
            plan_title=req.plan_title,
            full_outline=req.full_outline,
            current_section=req.current_section,
            policy_context=req.policy_context,
            user_requirement=req.user_requirement,
        )
        # 检查 agent 是否返回了错误字典
        if isinstance(new_section, dict) and "error" in new_section:
            raise Exception(
                f"AI Agent Error: {new_section.get('raw_content', new_section.get('error'))}"
            )

        return RewriteSectionReturn(new_section=new_section)
    except Exception as e:
        print(f"(from router_rewrite_section, generate.py) 重写章节异常: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"重写章节失败: {str(e)}")


@generate_router.post("/api/rewrite/content_paragraph")
async def router_rewrite_content_paragraph(req: RewriteContentParagraphRequest):
    """
    单个段落内容重写接口
    :param req: RewriteContentParagraphRequest
                -> plan_title: str (description="用户输入的标题")
                    ,section_title: str(description="用户输入的章节标题")
                    ,subtitle_title: str(description="用户输入的二级标题")
                    ,current_content: str(description="用户输入的当前段落内容")
                    ,context: str(description="用户输入的上下文")
                    ,user_requirement: Optional[str] = ""(description="用户输入的需求")
    :return: RewriteContentParagraphReturn
                -> success: bool
                    ,new_content: str(description="重写后的段落内容")
    """
    logging.info(f"router_rewrite_content_paragraph, req:\n{req}")
    try:
        new_content = content_agent.rewrite_content_paragraph(
            plan_title=req.plan_title,
            section_title=req.section_title,
            subtitle_title=req.subtitle_title,
            current_content=req.current_content,
            context=req.context,
            user_requirement=req.user_requirement,
        )
        return RewriteContentParagraphReturn(new_content=new_content)
    except Exception as e:
        print(
            f"(from router_rewrite_content_paragraph, generate.py) 重写段落内容异常: {e}"
        )
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"重写段落内容失败: {str(e)}")
