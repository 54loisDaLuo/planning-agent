# later can add more nodes as business expands

from langgraph.graph import StateGraph
from pydantic import BaseModel
from ...ai.agent import ContentAgent
import json


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

    if has_content_in_outline(outline):
        # 解析outline JSON
        outline_data = json.loads(outline)

        # 提取结构化内容（而不是原始JSON）
        original_full_content = extract_full_content_with_structure(outline_data)

        # 移除content信息得到纯净大纲
        new_outline = remove_content_from_outline(outline)

        # # 重写任务，传入结构化内容
        # content = content_agent.rewrite_content(
        #     title, new_outline, original_full_content, context
        # )
        # 重写任务，传入结构化内容
        content = content_agent.rewrite_content(
            title, new_outline, original_full_content, context
        )
    else:
        # 大纲生成全文
        content = content_agent.generate_content(title, outline, context)

    return {"content": content}


def has_content_in_outline(outline: str) -> bool:
    """
    判断outline中是否含有content字段
    Args:
        outline (str): JSON格式的outline字符串
    Returns:
        bool: 如果含有content字段返回True，否则返回False
    """
    try:
        outline_data = json.loads(outline)

        def check_content_recursive(obj):
            if isinstance(obj, dict):
                if "content" in obj:
                    return True
                for value in obj.values():
                    if check_content_recursive(value):
                        return True
            elif isinstance(obj, list):
                for item in obj:
                    if check_content_recursive(item):
                        return True
            return False

        return check_content_recursive(outline_data)
    except json.JSONDecodeError:
        return False


def node_has_content_in_outline(state: ContentState) -> bool:
    """
    判断outline中是否含有content字段
    Args:
        outline (str): JSON格式的outline字符串
    Returns:
        bool: 如果含有content字段返回True，否则返回False
    """
    return has_content_in_outline(state.outline)


def remove_content_from_outline(outline: str) -> str:
    """
    从outline中剔除content信息，形成新的数据
    Args:
        outline (str): JSON格式的outline字符串
    Returns:
        str: 剔除content信息后的JSON字符串
    """
    try:
        outline_data = json.loads(outline)

        def remove_content_recursive(obj):
            if isinstance(obj, dict):
                # 创建新字典，排除content字段
                new_dict = {}
                for key, value in obj.items():
                    if key != "content":
                        new_dict[key] = remove_content_recursive(value)
                return new_dict
            elif isinstance(obj, list):
                # 递归处理列表中的每个元素
                return [remove_content_recursive(item) for item in obj]
            else:
                # 基本类型直接返回
                return obj

        cleaned_outline = remove_content_recursive(outline_data)
        return json.dumps(cleaned_outline, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        return outline


# def extract_full_content_with_structure(outline_data):
#     """
#     从outline JSON数据中提取结构化内容，明确区分大纲和文本
#     Args:
#         outline_data: 解析后的JSON对象
#     Returns:
#         str: 结构化格式的完整内容
#     """

#     def build_structure_recursive(obj, level=0):
#         if isinstance(obj, dict):
#             result = []
#             if "title" in obj:
#                 indent = "  " * level
#                 result.append(f"{indent}# {obj['title']}")

#             if "content" in obj and obj["content"]:
#                 indent = "  " * (level + 1)
#                 result.append(f"{indent}【文本内容开始】")
#                 result.append(f"{obj['content']}")
#                 result.append(f"{indent}【文本内容结束】")

#             for key, value in obj.items():
#                 if key not in ["title", "content"]:
#                     result.extend(build_structure_recursive(value, level + 1))

#             if "children" in obj:
#                 for child in obj["children"]:
#                     result.extend(build_structure_recursive(child, level + 1))

#             return result
#         elif isinstance(obj, list):
#             result = []
#             for item in obj:
#                 result.extend(build_structure_recursive(item, level))
#             return result
#         else:
#             return []

#     structure_lines = build_structure_recursive(outline_data)
#     return "\n".join(structure_lines)


def extract_full_content_with_structure(outline_data):
    """
    从outline JSON数据中提取结构化内容，明确区分大纲和文本
    Args:
        outline_data: 解析后的JSON对象
    Returns:
        str: 结构化格式的完整内容
    """

    def build_structure_recursive(obj, level=1):
        if isinstance(obj, dict):
            result = []
            if "title" in obj:
                # 使用【大纲标题 X级】格式代替#标记
                result.append(f"【大纲标题 {level}级】{obj['title']}")

            if "content" in obj and obj["content"]:
                # 使用【具体文本开始】代替【文本内容开始】
                result.append(f"【具体文本开始】")
                result.append(f"{obj['content']}")
                result.append(f"【具体文本结束】")

            for key, value in obj.items():
                if key not in ["title", "content"]:
                    result.extend(build_structure_recursive(value, level + 1))

            if "children" in obj:
                for child in obj["children"]:
                    result.extend(build_structure_recursive(child, level + 1))

            return result
        elif isinstance(obj, list):
            result = []
            for item in obj:
                result.extend(build_structure_recursive(item, level))
            return result
        else:
            return []

    structure_lines = build_structure_recursive(outline_data)
    return "\n".join(structure_lines)


# Construct the graph
wf = StateGraph(ContentState)

wf.add_node("generate_content", node_generate_content)
wf.set_entry_point("generate_content")
wf.add_edge("generate_content", "__end__")

app = wf.compile()
