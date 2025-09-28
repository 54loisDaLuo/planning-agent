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
from fastapi.responses import StreamingResponse
import asyncio

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


@generate_router.post("/api/outline/stream")
async def router_generate_outline_stream(req: GenerateOutlineRequest):
    """
    修复后的流式大纲生成接口
    """
    logging.info(f"router_generate_outline_stream, req:\n{req}")

    async def generate_stream():
        try:
            # 初始状态设置
            initial_state = {
                "title": req.title,
                "selectedKbList": [kb.model_dump() for kb in req.selectedKbList],
                "policy": "",
            }

            # 执行知识库选择步骤
            from ..ai.graph.outline import node_select_kb, OutlineState

            state = OutlineState(**initial_state)
            updated_state = node_select_kb(state)

            # 获取选中的知识库内容
            from ..kb.utils import KnowledgeBase

            kb = KnowledgeBase()
            selected_bfs = updated_state.get("selectedKbList", [])
            selected_kb_contents = kb.get_all_kb_content(selected_bfs)

            # 生成摘要
            from ..ai.agent import KbAgent

            kb_agent = KbAgent()
            selected_kb_abstract = kb_agent.abstract_kb_lst(
                req.title, selected_kb_contents
            )

            # 先发送政策摘要（立即发送）
            if selected_kb_abstract:
                yield f"data: {json.dumps({'type': 'policy', 'content': selected_kb_abstract})}\n\n"
                # 重要：立即刷新
                await asyncio.sleep(0.01)

            # 修复：使用异步方式调用流式生成
            full_outline = ""

            # 方法1：直接使用异步生成器
            outline_stream = outline_agent.generate_outline_stream(
                req.title, selected_kb_abstract
            )

            # 关键修复：正确处理异步生成器
            async for token in outline_stream:
                full_outline += token
                # 立即发送每个token，不要累积
                yield f"data: {json.dumps({'token': token, 'type': 'outline'})}\n\n"
                # 小延迟让流式效果明显
                await asyncio.sleep(0.02)

            # 发送完整大纲和结束信号
            yield f"data: {json.dumps({'type': 'complete_outline', 'content': full_outline})}\n\n"
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            error_msg = f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"
            yield error_msg
            print(f"流式生成大纲异常: {e}")
            traceback.print_exc()

    # 修复响应头配置
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
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
