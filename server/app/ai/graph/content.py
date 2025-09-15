# later can add more nodes as business expands

from langgraph.graph import StateGraph
from pydantic import BaseModel
from ...ai.agent import ContentAgent


content_agent = ContentAgent()


class ContentState(BaseModel):
    title: str
    outline: str
    context: str
    content: str = ""


def node_generate_content(state: ContentState):
    """
    生成整篇文本内容（基于标题、大纲和上下文）
    Args:
        state (ContentState): 包含标题、大纲和上下文的状态对象

    Returns:
        dict: 包含生成的文本内容的字典
    """
    title = state.title
    outline = state.outline
    context = state.context

    # 生成整篇文本内容（基于标题、大纲和上下文）
    content = content_agent.generate_content(title, outline, context)

    return {"content": content}


# Construct the graph
wf = StateGraph(ContentState)

wf.add_node("generate_content", node_generate_content)
wf.set_entry_point("generate_content")
wf.add_edge("generate_content", "__end__")

app = wf.compile()
