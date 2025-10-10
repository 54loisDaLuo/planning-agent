#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tavily WebSearch工具
基于Tavily API实现高质量的网络搜索功能
"""

import sys
import os
import time
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
import getpass

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

# 导入配置
import WEB_SEARCH_CONFIG


# 配置日志
log_dir = os.path.join(project_root, "logs")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "tavily_websearch_test.log")

# 创建日志格式
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 创建文件处理器
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# 配置根日志记录器
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

logger = logging.getLogger(__name__)
logger.info(f"Tavily WebSearch日志文件: {log_file}")


class TavilyWebSearch:
    """Tavily网络搜索引擎"""

    def __init__(self):
        # 优先从配置文件获取API Key
        self.api_key = WEB_SEARCH_CONFIG.get("tavily_api_key")
        self.max_results = WEB_SEARCH_CONFIG.get("max_web_results", 3)  # 默认5个结果
        # 如果配置文件中没有，则从环境变量获取
        if not self.api_key:
            self.api_key = os.environ.get("TAVILY_API_KEY")
        self.enabled = bool(
            self.api_key and self.api_key != "your_actual_tavily_api_key_here"
        )

        if self.enabled:
            logger.info(f"Tavily API密钥已设置: {self.api_key[:10]}...")
            logger.info("Tavily WebSearch已启用")
        else:
            logger.warning("Tavily WebSearch未启用 - API密钥未正确设置")

    def search(self, query: str, max_results: int) -> List[Dict]:
        """
        执行Tavily搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数量

        Returns:
            tuple: (ai_answer, results)
            ai_answer: AI生成的答案
            results: list[dict], 每一个dict包含排名、标题、URL、相关性分数等信息
        """
        if not self.enabled:
            logger.warning("Tavily未启用，返回空结果")
            return []

        try:
            logger.info(f"开始Tavily搜索，查询: {query}")
            start_time = time.time()

            # 使用langchain_tavily，传递API Key
            tool = TavilySearch(
                tavily_api_key=self.api_key,
                max_results=self.max_results,
                topic="general",
                include_answer=True,
                include_raw_content=False,
                include_images=False,
                include_image_descriptions=False,
                search_depth="basic",
            )

            # 执行搜索
            result = tool.invoke({"query": query})

            # 解析结果
            ai_answer, results = self._parse_results(result)

            search_time = time.time() - start_time
            logger.info(
                f"Tavily搜索完成，耗时: {search_time:.2f}秒，获得 {len(results)} 个结果"
            )

            return ai_answer, results

        except Exception as e:
            logger.error(f"Tavily搜索异常: {e}")
            return "", []

    def _parse_results(self, data: Dict) -> tuple:
        """解析Tavily搜索结果"""

        results = []
        ai_answer = ""

        # 提取搜索结果
        for i, item in enumerate(data.get("results", [])):
            result = {
                "rank": str(i + 1),  # 从1开始编号
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "score": item.get("score", 0.0),
            }
            results.append(result)

            # 记录详细信息
            logger.debug(f"搜索结果: {result['title']} - {result['url']}")

        # 提取AI生成的答案（如果有）
        if "answer" in data and data["answer"]:
            ai_answer = data["answer"]
            logger.info("找到AI生成的答案")

        logger.info(f"解析完成，共 {len(results)} 个结果")
        return ai_answer, results


# 全局Tavily搜索实例
tavily_searcher = TavilyWebSearch()


@tool
def tavily_websearch_tool(query: str) -> tuple:
    """
    使用Tavily执行高质量的网络搜索，获取最新的网络信息。

    Tavily是一个专门为AI应用设计的搜索API，提供高质量、结构化的搜索结果。
    该工具会返回相关的网页内容、AI生成的答案，以及详细的元数据。

    Args:
        query (str): 搜索查询字符串

    Returns:
        tuple: (ai_answer, results)
        ai_answer: AI生成的答案
        results: list[dict], 每一个dict包含排名、标题、URL、相关性分数等信息

    """
    try:
        logger.info(f"开始Tavily WebSearch，查询: {query}")

        # 执行搜索
        ai_answer, results = tavily_searcher.search(query, max_results=5)

        # 返回JSON格式结果
        result_json = json.dumps(results, ensure_ascii=False, indent=2)

        logger.info(f"Tavily WebSearch返回 {len(results)} 个结果")
        return ai_answer, result_json

    except Exception as e:
        logger.error(f"Tavily WebSearch工具执行失败: {e}")
        return json.dumps([], ensure_ascii=False)


def test_tavily_websearch():
    """测试Tavily WebSearch功能"""
    logger.info("=" * 60)
    logger.info("测试Tavily WebSearch功能")
    logger.info("=" * 60)

    # 检查配置
    if not tavily_searcher.enabled:
        logger.error("Tavily未配置，请设置TAVILY_API_KEY环境变量")
        logger.info("获取API密钥: https://tavily.com/")
        return

    test_queries = [
        "知识图谱构建方法",
        # "人工智能最新发展2024",
        # "机器学习在医疗领域的应用"
    ]

    for i, query in enumerate(test_queries, 1):
        logger.info(f"测试 {i}: {query}")
        logger.info("-" * 40)

        try:
            ai_answer, result = tavily_websearch_tool.invoke(query)
            logger.info(f"ai_answer: {ai_answer}")
            logger.info(f"搜索结果: {result}")
        except Exception as e:
            logger.error(f"搜索失败: {e}")

        time.sleep(2)  # 避免请求过于频繁


if __name__ == "__main__":
    test_tavily_websearch()
