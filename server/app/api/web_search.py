from fastapi import APIRouter, HTTPException
from ..ai.agent import WebSearchAgent
from .schemas import WebSearchParagraphRequest, WebSearchParagraphReturn
import traceback
import logging

web_search_router = APIRouter()
web_search_agent = WebSearchAgent()


@web_search_router.post("/web_search/paragraph")
async def web_search_content_paragraph(req: WebSearchParagraphRequest):
    """
    段落搜索接口
    :param req: WebSearchParagraphRequest -> plan_title: str(description="计划标题")
                                            ,section_title: str(description="章节标题")
                                            ,subtitle_title: str(description="子标题")
    :return: WebSearchParagraphReturn -> success: bool
                                            ,web_search_infos: dict | str(description="搜索到的段落信息")
    """
    logging.info(f"web_search_content_paragraph, req:\n{req}")
    try:
        result = web_search_agent.web_search_content_paragraph(
            plan_title=req.plan_title,
            section_title=req.section_title,
            subtitle_title=req.subtitle_title,
        )
        return WebSearchParagraphReturn(
            success=True,
            web_search_infos=result,
        )
    except Exception as e:
        print(
            f"(from web_search_content_paragraph, web_search.py) 段落文本【联网搜索】异常: {e}"
        )
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"段落文本【联网搜索】失败: {str(e)}, (from router_web_search, web_search.py)",
        )
