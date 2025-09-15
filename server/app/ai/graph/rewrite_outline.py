from langgraph.graph import StateGraph
from pydantic import BaseModel
from typing import List
from ...api.schemas import KnowledgeBaseFile
from ...kb.utils import KnowledgeBase
from ...kb.query_chroma import Query
from ...ai.agent import KbAgent, OutlineAgent
import json

kb = KnowledgeBase()
qry = Query()
kb_agent = KbAgent()
outline_agent = OutlineAgent()

AI_MAX_SELECT_NUM = 3
VEC_SELECT_NUM = 7

"""
outline knowledge base reference:
- user maximum select 3;
- ai maximum select 3 based on title only; out of vector selection of 7,
  but if not really relavant, ai can select less than 3 or 0

so the maximum reference knowledge base num is 6; minimun is 0.
"""


class RewriteOutlineState(BaseModel):
    title: str
    selectedKbList: List[KnowledgeBaseFile]
    policy: str  # TODO: change it later
    outline: str = ""


# 节点：根据标题选择知识库
def node_select_kb(state: RewriteOutlineState):
    """
    根据标题选择知识库
    :param state: title、selectedKbList（用户选择的知识库）
    :return: 所有选中的知识库文件列表，包括用户上传和AI选择的

    returns:
    all the kbs in selectedKbList, including user uploaded and ai selected.
    the returned data structure is like:
        “09_城建环保/青岛市加快推动“专精特新”中小企业高质量发展行动方案（2022—2025年）.xml”
    """
    title = state.title
    user_selected_bfs = state.selectedKbList

    # Overall: get the id of both user select + upload, and ai select
    # get the ai select kb in id format
    # 从向量数据库中查询与标题相关的知识库文件ID
    vec_relevant_ids = qry.query_relevant(title, VEC_SELECT_NUM)
    # 利用AI模型选择与标题相关的知识库文件ID
    ai_selected_ids = kb_agent.select_kb(title, vec_relevant_ids, AI_MAX_SELECT_NUM)
    # convert [id] format of ai choice into [bf] format
    # 从知识库中根据ID获取文件路径
    ai_selected_bfs = kb.id_to_bf_lst(ai_selected_ids)

    # TODO: test only, delete later
    print("--- 向量数据库检索到的相关ID (vec_relevant_ids): ---")
    print(vec_relevant_ids)
    print("----------------------------------------------------")

    print("--- AI从上述列表中筛选出的ID (ai_selected_ids): ---")
    print(ai_selected_ids)
    print("----------------------------------------------------")

    # integrate user choices and ai choices, delete overlaps
    # Pydantic models are not hashable, so can't use a set of objects directly.
    # We'll use a dictionary to ensure uniqueness based on a unique identifier (the ID).
    # 将用户选择的知识库ID-文件路径的映射
    unique_bfs = {kb.bf_to_id(bf): bf for bf in user_selected_bfs}
    # 合并用户选择和AI选择的知识库文件
    for bf in ai_selected_bfs:
        unique_bfs[kb.bf_to_id(bf)] = bf

    total_selected_bfs = list(unique_bfs.values())

    # Return a dictionary to update the state
    return {"selectedKbList": total_selected_bfs}


def node_rewrite_outline(state: RewriteOutlineState):
    """
    Reads content from the selected knowledge base files,
    constructs a RAG prompt, and generates the final outline.

    根据标题、选中的知识库文件列表生成大纲
    :param state: 包括title、selectedKbList
    :return: policy（生成的摘要）, outline（生成的大纲）
    """
    title = state.title
    selected_bfs = state.selectedKbList

    # get contents of all selected kb, and use it to generate ai abstract
    # 读取所有选中的知识库文件内容
    selected_kb_contents = kb.get_all_kb_content(selected_bfs)
    # 生成摘要
    selected_kb_abstract = kb_agent.abstract_kb_lst(title, selected_kb_contents)
    # 重新生成大纲
    final_outline = outline_agent.get_rewrite_outline_prompt(
        title, selected_kb_abstract, state.outline
    )

    return {"policy": selected_kb_abstract, "outline": final_outline}


# Construct the graph
wf = StateGraph(RewriteOutlineState)
# 添加节点
wf.add_node("select_kb", node_select_kb)
wf.add_node("rewrite_outline", node_rewrite_outline)

# 添加边
# 从入口节点到选择知识库节点
wf.set_entry_point("select_kb")
# 从选择知识库节点到生成大纲节点
wf.add_edge("select_kb", "rewrite_outline")
# 从生成大纲节点到结束
wf.add_edge("rewrite_outline", "__end__")
# 编译工作流
app = wf.compile()


# code below is not needed:
# # extract selected db/file in bf format
# user_selected_bfs_db = kb.bf_get_db(user_selected_bfs)
# user_selected_bfs_file = kb.bf_get_file(user_selected_bfs)
# # convert selected db, from bf format in id format, and integrate with ai choice
# selected_db_ids = kb.bf_to_id_lst(user_selected_bfs)
# final_unique_list = list(set(ai_selected_ids + selected_db_ids))
