from fastapi import APIRouter, HTTPException
from .schemas import QARequest, QAResponse
from ..ai.agent import QAAgent

qa_router = APIRouter(tags=["问答"])

# 全局问答Agent实例
qa_agent = QAAgent()


@qa_router.post("/ask", response_model=QAResponse)
async def ask_question(request: QARequest):
    """问答接口 - 三路并行架构"""
    # TODO:整理prompt代码
    try:
        response = await qa_agent.ask_question(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答服务异常: {str(e)}")


@qa_router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "qa", "architecture": "三路并行"}
