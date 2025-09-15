import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List
from ..api.schemas import KnowledgeBaseFile
import chromadb
from .import_to_chromadb import CHROMA_PERSIST_DIR, COLLECTION_NAME
import docx


load_dotenv()

API_KEY = os.getenv("EBD_API_KEY")
BASE_URL = os.getenv("EBD_BASE_URL")
MODEL_NAME = os.getenv("EBD_MODEL_NAME")

MAX_KB_NUM = 6  # max 6 kb each generation # 每次生成最多使用6个知识库
USER_MAX_KB_NUM = 5  # max 5 kb for user to select # 用户最多可选择5个知识库

KB_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../kb/data")
)  # 预定义知识库数据目录
KB_UPLOADS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../kb/uploads")
)  # 用户上传文件目录

MAX_CHAR_NUM = 950  # 最大字符数限制


class KnowledgeBase:
    @staticmethod
    def get_kb_list():
        """
        获取知识库文件列表
        扫描知识库数据目录，按文件夹分类返回所有知识库XML文件
        :return: 按分类组织的知识库文件列表
        """
        kb_list = []
        for category in os.listdir(KB_DATA_DIR):
            category_path = os.path.join(KB_DATA_DIR, category)
            if os.path.isdir(category_path):
                files = []
                for fname in os.listdir(category_path):
                    if fname.endswith(".xml"):
                        files.append({"name": fname, "type": "db"})
                kb_list.append({"category": category, "files": files})
        return kb_list

    @staticmethod
    def bf_to_id(bf: KnowledgeBaseFile) -> str:
        """
        Converts a KnowledgeBaseFile object to a string ID if its type is 'db'.
        Format: "category/name"
        Returns an empty string if the type is not 'db'.

        单个知识库文件转ID
        :param bf: KnowledgeBaseFile (description="知识库文件对象")
        :return: str (description="知识库文件ID")
        """
        if bf.type == "db":
            return f"{bf.category}/{bf.name}"
        return ""

    @staticmethod
    def bf_to_id_lst(bf_lst: List[KnowledgeBaseFile]) -> List[str]:
        """
        Converts a list of KnowledgeBaseFile objects to a list of string IDs,
        only including items where type is 'db'.
        Format: "category/name"

        知识库文件列表转ID列表
        :param bf_lst: List[KnowledgeBaseFile] (description="知识库文件对象列表")
        :return: List[str] (description="知识库文件ID列表")
        """
        return [f"{bf.category}/{bf.name}" for bf in bf_lst if bf.type == "db"]

    @staticmethod
    def bf_get_file(bf_lst: List[KnowledgeBaseFile]) -> List[KnowledgeBaseFile]:
        """
        Extracts items with type 'file' from a list of KnowledgeBaseFile objects.

        从知识库文件对象列表中提取类型为'file'的文件
        :param bf_lst: List[KnowledgeBaseFile] (description="知识库文件对象列表")
        :return: List[KnowledgeBaseFile] (description="知识库文件对象列表，类型为'file'的文件对象列表")
        """
        return [bf for bf in bf_lst if bf.type == "file"]

    @staticmethod
    def bf_get_db(bf_lst: List[KnowledgeBaseFile]) -> List[KnowledgeBaseFile]:
        """
        Extracts items with type 'db' from a list of KnowledgeBaseFile objects.

        从知识库文件对象列表中提取类型为'db'的文件
        :param bf_lst: List[KnowledgeBaseFile] (description="知识库文件对象列表")
        :return: List[KnowledgeBaseFile] (description="知识库文件对象列表，类型为'db'的文件对象列表")
        """
        return [bf for bf in bf_lst if bf.type == "db"]

    @staticmethod
    def get_ai_kb_num(selected_kb):
        """
        this function says: how many kb should ai gonna find

        计算AI需要选择的知识库数量
        根据用户已选知识库数量，计算AI还需要选择多少个知识库（最多6个）
        :param selected_kb: List[KnowledgeBaseFile] (description="用户已选知识库文件对象列表")
        :return: int (description="AI需要选择的知识库数量")
        """
        # calculate the number of selected knowledge bases (including user uploads)
        used_num = len(selected_kb)
        remain_num = MAX_KB_NUM - used_num
        return remain_num

    @staticmethod
    def exclude_kb_list(lst, selected_kb):
        """
        this function is used for re-getting all the kbs but except user-selected

        从完整知识库列表中排除用户已选择的知识库
        仅过滤类型为'db'的文件
        :param lst: List[KnowledgeBaseFile] (description="完整知识库文件对象列表")
        :param selected_kb: List[KnowledgeBaseFile] (description="用户已选知识库文件对象列表")
        :return: List[KnowledgeBaseFile] (description="知识库文件对象列表，排除用户已选择的知识库文件对象列表")
        """
        # build the selected collection {(category, name)} for items with type 'db'
        # 构建已选择的知识库集合{(分类, 文件名)}，仅包含db类型
        selected_set = set(
            (kb["category"], kb["name"]) for kb in selected_kb if kb.get("type") == "db"
        )
        new_lst = []
        for cat in lst:
            # Filter out the selected files
            # 过滤掉已选择的文件
            new_files = [
                f
                for f in cat["files"]
                if (cat["category"], f["name"]) not in selected_set
            ]
            # Only the categories with remaining files are retained
            # 只保留还有剩余文件的分类
            if new_files:
                new_lst.append({"category": cat["category"], "files": new_files})
        return new_lst

    @staticmethod
    def id_to_bf(id_str: str) -> KnowledgeBaseFile:
        """
        Converts a string ID back to a KnowledgeBaseFile object.
        ID Format: "category/name"

        将知识库文件ID转换为知识库文件对象
        :param id_str: str (description="知识库文件ID")
        :return: KnowledgeBaseFile (description="知识库文件对象")
        """
        parts = id_str.split("/", 1)
        category = parts[0]
        name = parts[1]
        return KnowledgeBaseFile(name=name, type="db", category=category)

    @staticmethod
    def id_to_bf_lst(id_lst: List[str]) -> List[KnowledgeBaseFile]:
        """
        Converts a list of string IDs back to a list of KnowledgeBaseFile objects.

        批量将ID字符串列表转换回知识库文件对象列表
        :param id_lst: List[str] (description="知识库文件ID列表")
        :return: List[KnowledgeBaseFile] (description="知识库文件对象列表")
        """
        return [KnowledgeBase.id_to_bf(id_str) for id_str in id_lst]

    @staticmethod
    def get_all_kb_content(bf_lst: List[KnowledgeBaseFile]) -> List[str]:
        """
        Retrieves the content for a list of KnowledgeBaseFile objects.
        - For 'db' type, it fetches content from ChromaDB by ID.
        - For 'file' type, it reads the content from the local file system.
        - All content is truncated to MAX_CHAR_NUM characters.

        获取知识库文件列表的内容（核心方法）
        对于'db'类型：从ChromaDB向量数据库获取内容
        对于'file'类型：从本地文件系统读取内容
        所有内容截断至最大字符数限制
        :param bf_lst: List[KnowledgeBaseFile] (description="知识库文件对象列表")
        :return: List[str] (description="知识库文件内容列表")
        """
        contents = []

        # Initialize ChromaDB client
        try:
            db_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
            collection = db_client.get_collection(name=COLLECTION_NAME)
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            # Return empty content for all if DB fails
            # 如果数据库初始化失败，返回空内容列表
            return [""] * len(bf_lst)

        for bf in bf_lst:
            content = ""
            try:
                if bf.type == "db":
                    # 从ChromaDB获取预定义知识库内容
                    doc_id = KnowledgeBase.bf_to_id(bf)
                    if doc_id:
                        # Fetch from ChromaDB
                        # 从ChromaDB获取文档内容
                        result = collection.get(ids=[doc_id], include=["documents"])
                        if result and result.get("documents"):
                            content = result["documents"][0]
                        else:
                            print(
                                f"Warning: Document with ID '{doc_id}' not found in ChromaDB."
                            )

                elif bf.type == "file":
                    # User upload files has no category
                    # 用户上传的文件没有分类目录
                    file_path = os.path.join(KB_UPLOADS_DIR, bf.name)
                    if os.path.exists(file_path):
                        # --- File classify starts ---
                        # --- 文件分类处理开始 ---
                        if bf.name.endswith(".docx"):
                            # 如果是.docx文件，使用python-docx读取
                            try:
                                doc = docx.Document(file_path)
                                full_text = [para.text for para in doc.paragraphs]
                                content = "\n".join(full_text)
                            except Exception as e:
                                print(f"Error reading .docx file '{bf.name}': {e}")
                                content = ""
                        else:
                            try:
                                with open(file_path, "r", encoding="utf-8") as f:
                                    content = f.read()
                            except UnicodeDecodeError:
                                print(
                                    f"Warning: Could not decode file '{bf.name}' as utf-8."
                                )
                                content = f"Non-text file content for {bf.name} is not displayed."
                        # --- File classify ends ---
                        # --- 文件分类处理结束 ---
                    else:
                        print(f"Warning: File not found at '{file_path}'.")

            except Exception as e:
                print(f"Error processing '{bf.name}': {e}")
                content = ""  # Ensure content is empty on error （确保出错时内容为空）

            # Truncate content if it exceeds the maximum length
            # 截断内容如果超过最大长度
            if len(content) > MAX_CHAR_NUM:
                content = content[:MAX_CHAR_NUM]

            contents.append(content)

        return contents


# test functionality
if __name__ == "__main__":
    all_kb_list = [
        {
            "category": "组织机构",
            "files": [
                {"name": "A.xml", "type": "db"},
                {"name": "B.xml", "type": "db"},
            ],
        },
        {
            "category": "国土能源",
            "files": [
                {"name": "C.xml", "type": "db"},
                {"name": "D.xml", "type": "db"},
            ],
        },
    ]
    # mock selected kb
    selected_kb = [
        # This item has type 'db', so it should be excluded from the list.
        {"name": "A.xml", "type": "db", "category": "组织机构"},
        # This item also has type 'db', so it should also be excluded.
        {"name": "C.xml", "type": "db", "category": "国土能源"},
    ]
    # test exclude_kb_list
    print("Testing exclude_kb_list function...")
    filtered_kb_list = KnowledgeBase.exclude_kb_list(all_kb_list, selected_kb)
    print("Filtered list:")
    print(filtered_kb_list)
    # ...
    print("\nExpected output:")
    print(
        "[{'category': '组织机构', 'files': [{'name': 'B.xml', 'type': 'db'}]}, {'category': '国土能源', 'files': [{'name': 'D.xml', 'type': 'db'}]}]"
    )
