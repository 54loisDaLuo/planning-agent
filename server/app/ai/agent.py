import json
from langgraph.graph import StateGraph
from openai import OpenAI
from typing import TypedDict, List
import os
from dotenv import load_dotenv
from .prompt import Prompt
from ..api.schemas import KnowledgeBaseFile

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
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            new_title = completion.choices[0].message.content
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

    # def generate_outline(self, title: str, kb_abstract: str):
    #     messages = Prompt.get_outline_prompt(title, kb_abstract)
    #     try:
    #         completion = self.client.chat.completions.create(
    #             model=self.model_name,
    #             messages=messages,
    #             response_format={"type": "json_object"},
    #         )
    #         outline_str = completion.choices[0].message.content

    #         parsed_json = json.loads(outline_str)
    #         print("--- AI返回并解析后的JSON对象 ---")
    #         print(parsed_json)

    #         # Robustness fix: If the AI returns a single object instead of a list, wrap it in a list.
    #         if isinstance(parsed_json, dict):
    #             return [parsed_json]

    #         return parsed_json

    #     except json.JSONDecodeError:
    #         print(f"[错误] AI返回的大纲不是有效的JSON格式: {outline_str}")
    #         return []
    #     except Exception as e:
    #         print(f"[错误] 调用AI生成大纲时出错: {e}")
    #         return []


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
<<<<<<< HEAD
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
=======
>>>>>>> b4fa912... 新增注释、代码格式化、重写xx功能bug修复、prompt修改等
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


# test
if __name__ == "__main__":
    tested_agent = ClassificationAgent()
    answer = tested_agent.classify_title("杭州市政府‘十五五’建设的专项规划（2025）")
    print(answer)
