from ast import Dict
import json
import re
from langgraph.graph import StateGraph
from openai import OpenAI, api_key
from typing import Any, TypedDict, List
import os
from dotenv import load_dotenv
from .prompt import Prompt
from ..api.schemas import KnowledgeBaseFile
import logging
import asyncio

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

    """
    [{'url': 'https://www.moa.gov.cn:10443/ztzl/nylsfz/xwbd_lsfz/201705/t20170511_5603586.htm', 'title': '大力推进农业绿色发展', 'content': '推进农业绿色发展，就是要大力推广绿色生产技术，加快农业环境突出问题治理，重显农业绿色的本色。 更加注重生态保育。这是农业绿色发展的根本要求。', 'score': 0.66308063, 'raw_content': None}, {'url': 'https://www.moa.gov.cn/ztzl/ymksn/xhsbd/202507/t20250721_6475841.htm', 'title': '报告显示我国农业绿色发展水平稳步提升', 'content': '**中文**English 2025年8月20日 星期三 农历 后天是处暑 中国农业农村信息网 * 首页 * 机构 * 新闻 * 公开 * 政务服务 * 专题 * 互动 * 数据 * 业务管理 当前位置：首页\xa0>\xa0央媒看三农\xa0>\xa0新华社报道 # 报告显示我国农业绿色发展水平稳步提升 日期：2025-07-21 10:56 作者：古一平 李令仪 来源：新华社 字号：大 中 小 【字号：大 中 小】 打印本页 由中国农业绿色发展研究会和中国农业科学院农业资源与农业区划研究所编著的《中国农业绿色发展报告2024》日前发布，报告显示，我国农业绿色发展水平稳步提升。 报告显示，2023年全国农业绿色发展指数为78.23，较上年提高0.33，比2015年提高了3.04。 据介绍，农业绿色发展指数是评价我国绿色农业发展总体状况的指标，由资源节约保育、生态环境安全、绿色产品供给、生活富裕美好等4个一级指标组成。 报告从2019年起已连续7年发布。今年的报告以数据为支撑，从生产、生活和生态等多角度系统反映2023年至2024年我国农业绿色发展的总体水平、重大行动和主要成就。 “推进农业绿色发展是系统工程，涉及农业各领域各方面。”中国农业科学院院长、中国科学院院士黄三文表示，中国农业科学院将持续聚焦耕地保护修复、绿色循环发展、绿色产品供给等方面，加强耕地质量提升、绿色投入品创制等领域布局，为我国农业农村发展全面绿色转型贡献力量。（古一平、李令仪） 附件下载： * 机关子站 * 直属单位网站 * 国务院各部门网站 * 地方农业管理部门网站 1. 办公厅（对台湾农业事务办公室） 2. 人事司（党组巡视工作领导小组办公室） 3. 法规司 4. 政策与改革司 5. 发展规划司 6. 计划财务司 7. 种植业管理司（农药管理司） 8. 畜牧兽医局 9. 渔业渔政管理局 乡村产业发展司（农产品加工指导司） 乡村建设促进司 "乡村建设促进司") 农村社会事业促进司 农村合作经济指导司 帮扶司 区域协作促进司（革命老区工作办公室） 监督检查司 市场与信息化司 国际合作司 科学技术司（农业转基因生物安全管理办公室） 农产品质量安全监管司 农垦局 种业管理司 农业机械化管理司 农田建设管理司 机关党委 离退休干部局 长江流域渔政监督管理办公室 1. 农业农村部机关服务中心( 农业农村部机关服务局 )") 2. 中国农业科学院 3. 中国水产科学研究院 4. 中国热带农业科学院 5. 全国农业展览馆（中国农业博物馆） 6. 中国农业电影电视中心 7. 农民日报社 8. 中国农业出版社有限公司（农村读物出版社） 9. 中国农村杂志社 全国乡村振兴宣传教育中心 中央农业干部教育培训中心（农业农村部管理干部学院、中国共产党农业农村部党校） 农业农村部人力资源开发中心、中国农学会 农业农村部农村经济研究中心 农业农村部信息中心 农业农村部农产品质量安全中心', 'score': 0.6399392, 'raw_content': None}, {'url': 'https://www.gov.cn/zhengce/202402/content_6931903.htm', 'title': '农业绿色底色更鲜明 - 中国政府网', 'content': '农业绿色底色更鲜明_政策解读_中国政府网 Image 1) Image 2Image 3 *   首页 *   简 *   繁 *   EN *   登录;) *   个人中心;) *   退出;) *   邮箱 *   无障碍 Image 4Image 5ENImage 6Image 7 https://www.gov.cn/ 首页>政策>解读 农业绿色底色更鲜明 2024-02-19 10:52 来源： 经济日报  字号：默认 大 超大|打印| 绿色兴农是今年中央一号文件的热词。文件提出，加强农村生态文明建设。持续打好农业农村污染治理攻坚战，一体化推进乡村生态保护修复。扎实推进化肥农药减量增效，推广种养循环模式。整县推进农业面源污染综合防治。 2023年，农业绿色发展步伐加快，农业生态环境持续改善。农业农村部副部长邓小刚介绍，2023年全国化肥农药施用持续减量增效，畜禽粪污综合利用率、秸秆综合利用率、农膜处置率保持较高水平。长江十年禁渔取得重要阶段性成效，长江水生生物资源和多样性呈现恢复向好态势。农业生产和农产品“三品一标”再获新成效，全国农产品质量安全监测总体合格率保持高水平。 农业产地环境明显改善。农业农村部数据显示，主要农作物病虫害绿色防控面积覆盖率达54.1%，水稻、小麦、玉米三大粮食作物统防统治面积覆盖率达45.2%，化肥、农药利用率均超过41%。实施畜禽粪污资源化利用整县推进项目，畜禽粪污综合利用率达78.3%。整建制建设秸秆综合利用重点县，秸秆综合利用率达88%以上。农膜回收处置率稳定在80%以上。新批准创建80个国家农业绿色发展先行区，遴选29个先行区开展整建制全要素全链条推进农业面源污染综合防治。 农业绿色产业链条加快打造。全国累计认定绿色、有机农产品超过6.8万个，近5年全国农产品质量安全监测合格率保持在97.4%以上。统筹农产品初加工、精深加工和副产物综合利用，农产品及加工副产物综合利用水平稳步提升。推进加工减损，粮食加工损耗率为3.7%，比2015年降低约1个百分点，实现粮食年均减损100多亿斤。实施休闲农业精品工程，拓展丰富农事体验、观光采摘、特色乡宿、研学科普等新业态。目前，已建设120个全国休闲农业重点县，推介一批乡村休闲旅游精品线路。 农业农村部农村经济研究中心副主任金书秦表示，在推进农业绿色发展过程中将产生三方面红利：一是化肥、农药、农膜等化学投入品减量和作物秸秆、畜禽粪便资源化利用带来的减排红利；二是产品质量提升带来的产品红利；三是产地环境改善带来的生态红利。要以“产品、服务、功能”的眼光来重新衡量农业价值，通过生态补偿、发展绿色农产品、有机农产品和地理标志农产品、农业产业链延伸等手段将以上红利变成农业产值和农民收入，实现“绿水青山”向“金山银山”的转化。 “我们以发展绿色生态农业为抓手，全力打造绿色有机农产品示范基地。”江西省芦溪县农业农村局副局长杨学红介绍，县里专门出台有关农药和化肥减量增效方案，建立科学用药施肥管理和技术体系，2023年农药、化肥施用量同比分别减少1.18%、3%，农药化肥利用率普遍提高。实施粪污资源化利用整县推进，2023年全县粪污资源化利用率达到91.76%。积极引导新型农业经营主体开展绿色有机农产品认证申报，全县现有18个产品获绿色食品认证，8个产品获有机食品认证，全国绿色食品原料标准化生产基地达26万亩。 随着气温逐渐回暖，综合种养基地开始忙碌起来。在浙江省湖州市南浔区双林镇稻虾种养示范基地，农户曹雪杰说，前期已用羊粪对田块肥水，并陆续开始将小龙虾苗投放到稻田，预计4月底就可以上市。往年，基地的小龙虾一上市就被抢购一空；稻米绿色生态，煮后软糯甘甜，价格是普通稻米的两倍多。双林镇副镇长张开荣说，过去纯种粮亩均纯收益约800元，如今实施稻虾综合种养后能提高到2000多元。从全镇来看，综合种养实现了“粮食安全+食品安全+生态安全+农民增收+企业增效”多赢局面。 金书秦认为，农业绿色发展具有阶段性特点，可划分为“去污、提质、增效”三个阶段：去污就是生产生活过程清洁化，实现增产增收不增污；提质就是实现产地绿色化和产品优质化，通过完善市场实现优质优价；增效就是绿色成为发展的内生动力，农业农村多功能性逐步凸显，成为满足人们对美好生活向往的重要载体，绿色和发展相得益彰。（记者 乔金亮） 绿色兴农是今年中央一号文件的热词。文件提出，加强农村生态文明建设。持续打好农业农村污染治理攻坚战，一体化推进乡村生态保护修复。扎实推进化肥农药减量增效，推广种养循环模式。整县推进农业面源污染综合防治。 2023年，农业绿色发展步伐加快，农业生态环境持续改善。农业农村部副部长邓小刚介绍，2023年全国化肥农药施用持续减量增效，畜禽粪污综合利用率、秸秆综合利用率、农膜处置率保持较高水平。长江十年禁渔取得重要阶段性成效，长江水生生物资源和多样性呈现恢复向好态势。农业生产和农产品“三品一标”再获新成效，全国农产品质量安全监测总体合格率保持高水平。 农业产地环境明显改善。农业农村部数据显示，主要农作物病虫害绿色防控面积覆盖率达54.1%，水稻、小麦、玉米三大粮食作物统防统治面积覆盖率达45.2%，化肥、农药利用率均超过41%。实施畜禽粪污资源化利用整县推进项目，畜禽粪污综合利用率达78.3%。整建制建设秸秆综合利用重点县，秸秆综合利用率达88%以上。农膜回收处置率稳定在80%以上。新批准创建80个国家农业绿色发展先行区，遴选29个先行区开展整建制全要素全链条推进农业面源污染综合防治。 农业绿色产业链条加快打造。全国累计认定绿色、有机农产品超过6.8万个，近5年全国农产品质量安全监测合格率保持在97.4%以上。统筹农产品初加工、精深加工和副产物综合利用，农产品及加工副产物综合利用水平稳步提升。推进加工减损，粮食加工损耗率为3.7%，比2015年降低约1个百分点，实现粮食年均减损100多亿斤。实施休闲农业精品工程，拓展丰富农事体验、观光采摘、特色乡宿、研学科普等新业态。目前，已建设120个全国休闲农业重点县，推介一批乡村休闲旅游精品线路。 农业农村部农村经济研究中心副主任金书秦表示，在推进农业绿色发展过程中将产生三方面红利：一是化肥、农药、农膜等化学投入品减量和作物秸秆、畜禽粪便资源化利用带来的减排红利；二是产品质量提升带来的产品红利；三是产地环境改善带来的生态红利。要以“产品、服务、功能”的眼光来重新衡量农业价值，通过生态补偿、发展绿色农产品、有机农产品和地理标志农产品、农业产业链延伸等手段将以上红利变成农业产值和农民收入，实现“绿水青山”向“金山银山”的转化。 “我们以发展绿色生态农业为抓手，全力打造绿色有机农产品示范基地。”江西省芦溪县农业农村局副局长杨学红介绍，县里专门出台有关农药和化肥减量增效方案，建立科学用药施肥管理和技术体系，2023年农药、化肥施用量同比分别减少1.18%、3%，农药化肥利用率普遍提高。实施粪污资源化利用整县推进，2023年全县粪污资源化利用率达到91.76%。积极引导新型农业经营主体开展绿色有机农产品认证申报，全县现有18个产品获绿色食品认证，8个产品获有机食品认证，全国绿色食品原料标准化生产基地达26万亩。 随着气温逐渐回暖，综合种养基地开始忙碌起来。在浙江省湖州市南浔区双林镇稻虾种养示范基地，农户曹雪杰说，前期已用羊粪对田块肥水，并陆续开始将小龙虾苗投放到稻田，预计4月底就可以上市。往年，基地的小龙虾一上市就被抢购一空；稻米绿色生态，煮后软糯甘甜，价格是普通稻米的两倍多。双林镇副镇长张开荣说，过去纯种粮亩均纯收益约800元，如今实施稻虾综合种养后能提高到2000多元。从全镇来看，综合种养实现了“粮食安全+食品安全+生态安全+农民增收+企业增效”多赢局面。 金书秦认为，农业绿色发展具有阶段性特点，可划分为“去污、提质、增效”三个阶段：去污就是生产生活过程清洁化，实现增产增收不增污；提质就是实现产地绿色化和产品优质化，通过完善市场实现优质优价；增效就是绿色成为发展的内生动力，农业农村多功能性逐步凸显，成为满足人们对美好生活向往的重要载体，绿色和发展相得益彰。（记者 乔金亮） 【我要纠错】责任编辑：马文华 相关稿件 *   链接： *   全国人大 *   全国政协 *   国家监察委员会 *   最高人民法院 *   最高人民检察院 *   国务院部门网站 *   地方政府网站 *   驻港澳机构网站 *   驻外机构 Image 8Image 9 中国政府网|关于本网|网站声明|联系我们|网站纠错 主办单位：国务院办公厅 运行维护单位：中国政府网运行中心 版权所有：中国政府网 中文域名：中国政府网.政务 网站标识码bm01000001 京ICP备05070218号Image 10京公网安备11010202000001号 Image 11国务院客户端 Image 12国务院客户端小程序 Image 13Image 14 中国政府网微博、微信 *   电脑版 *   客户端 *   小程序 *   微博 *   微信 *   Image 15 *   网站纠错 Image 16 网站标识码bm01000001 京ICP备05070218号 京公网安备11010202000001号 农业绿色底色更鲜明 Image 17', 'score': 0.6152965, 'raw_content': None}, {'url': 'https://tjj.changzhi.gov.cn/sjfx/202311/t20231116_2822449.html', 'title': '绿色引领长治农业高质量发展', 'content': '农业绿色发展是新时期下农业可持续高质量发展的必然选择，是贯彻新发展理念、推进农业供给侧结构性改革的必然要求，是加快农业现代化、促进农业可持续发展', 'score': 0.5726516, 'raw_content': None}, {'url': 'http://www.reea.agri.cn/lsfzpj/202507/t20250718_8750669.htm', 'title': '农业农村部推介第三批农业绿色发展典型案例', 'content': '《通知》强调，加快农业发展全面绿色转型，是加快建设农业强国的重要任务，是促进人与自然和谐共生的客观要求。各级农业农村部门要提高政治站位，细化工作举措', 'score': 0.529337, 'raw_content': None}]
    """


# test
if __name__ == "__main__":
    tested_agent = ClassificationAgent()
    answer = tested_agent.classify_title("杭州市政府‘十五五’建设的专项规划（2025）")
    print(answer)
