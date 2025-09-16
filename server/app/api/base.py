from fastapi import APIRouter, UploadFile, File
from fastapi import Request
from fastapi.responses import JSONResponse
import shutil
import os
from ..kb.utils import KnowledgeBase
from fastapi.responses import FileResponse
import tempfile
import os
from docx import Document
from .schemas import DownloadRequest, DownloadReturn
import tempfile, logging
from starlette.background import BackgroundTask  # 修改这里

base_router = APIRouter()

KB_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../kb/data"))
KB_UPLOAD_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../kb/uploads")
)


# upload kb file
# if file with same name uploaded twice, later one will overcome the first
@base_router.post("/kb/upload")
async def upload_kb_file(file: UploadFile = File(...)):
    """
    上传知识库文件接口
    :param file: UploadFile (description="用户上传的文件")
    :return: JSONResponse (description="上传结果")
    """
    os.makedirs(KB_UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(KB_UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"success": True, "filename": file.filename}


# delete uploaded kb file
@base_router.post("/kb/delete")
async def delete_kb_file(request: Request):
    """
    删除知识库文件接口
    :param request: Request (description="用户请求")
    :return: JSONResponse (description="删除结果")
    """
    data = await request.json()
    filename = data.get("filename")
    file_path = os.path.join(KB_UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"success": True, "filename": filename}
    else:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "File not found", "filename": filename},
        )


# generate JSON of kb list, for front-end rendering
@base_router.get("/kb/list")
def router_get_kb_list():
    # print("get_kb_list 路由被调用")
    """
    Fintch scans the knowledge base directory and
    returns all knowledge base files by folder classification
    return format:
    [
      {
        "category": "分类名",
        "files": [
          { "name": "文件名.xml", "type": "file" }
        ]
      },
      ...
    ]


    获取知识库文件列表接口
    :return: JSONResponse (description="知识库文件列表")
    """
    return KnowledgeBase.get_kb_list()


@base_router.post("/kb/download")
async def router_download(req: DownloadRequest):
    """
    统一的大纲/全文下载接口
    :param req: DownloadOutlineRequest
                -> title: str (标题)
                -> outline: str (大纲JSON)
                -> policy: str (政策摘要)
                -> format: str (文件格式)
                -> download_type: str (下载类型：outline-仅大纲，full-全文)
    :return: FileResponse 或错误信息
    """
    logging.info(f"router_download,req:\n{req}")
    try:
        import json

        # 解析大纲JSON
        outline_data = json.loads(req.outline)
        while isinstance(outline_data, str):
            try:
                outline_data = json.loads(outline_data)
                logging.info(f"router_download,outline_data:\n{outline_data}")
            except json.JSONDecodeError:
                logging.error("大纲JSON解析失败，尝试去掉首尾空格")

        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{req.format}"
        ) as tmp_file:
            file_path = tmp_file.name

        if req.format == "docx":
            # 创建Word文档
            doc = Document()
            doc.add_heading(req.title, 0)

            # 添加政策摘要
            doc.add_heading("政策摘要", level=1)
            doc.add_paragraph(req.policy)

            # 根据下载类型添加内容
            if req.download_type == "outline":
                # 仅大纲模式
                doc.add_heading("详细大纲", level=1)
                add_outline_items(doc, outline_data)
            else:
                # 全文模式
                doc.add_heading("完整内容", level=1)
                outline_data = outline_data.get("content_outline", [])
                logging.info(f"router_download,content_outline:\n{outline_data}")
                add_full_content(doc, outline_data)

            doc.save(file_path)

        elif req.format == "txt":
            # 创建文本文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"标题: {req.title}\n\n")
                f.write(f"政策摘要:\n{req.policy}\n\n")

                if req.download_type == "outline":
                    f.write(f"详细大纲:\n")
                    write_outline_items(f, outline_data)
                else:
                    f.write(f"完整内容:\n")
                    write_full_content(f, outline_data)

        # 返回文件下载
        file_name = f"{req.title}_{req.download_type}.{req.format}"
        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type="application/octet-stream",
            background=BackgroundTask(
                lambda: (
                    os.unlink(file_path)
                    if file_path and os.path.exists(file_path)
                    else None
                )
            ),
        )

    except json.JSONDecodeError:
        # 如果JSON解析失败，返回错误响应
        logging.error(f"大纲JSON解析失败: {req.outline}")
        raise HTTPException(status_code=400, detail="大纲格式不正确，请检查大纲内容")
    except Exception as e:
        # 发生异常时清理文件
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
        # 添加详细的错误信息
        logging.error(f"文件生成失败详情: {str(e)}")
        logging.error(f"异常类型: {type(e).__name__}")
        import traceback

        logging.error(f"堆栈跟踪: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"文件生成失败: {str(e)}")


# 辅助函数：添加大纲项（仅标题）
def add_outline_items(doc, items, level=2):
    """递归添加大纲项（仅标题）"""
    for item in items:
        doc.add_heading(item.get("title", ""), level=level)
        if "children" in item and item["children"]:
            add_outline_items(doc, item["children"], level + 1)


# 辅助函数：添加完整内容（标题+内容）
def add_full_content(doc, items, level=2):
    """递归添加完整内容（标题+内容）"""
    for item in items:
        # 添加标题
        doc.add_heading(item.get("title", ""), level=level)

        # 添加内容（如果存在）
        if "content" in item and item["content"]:
            doc.add_paragraph(item["content"])

        # 递归处理子项
        if "children" in item and item["children"]:
            add_full_content(doc, item["children"], level + 1)


# 辅助函数：写入大纲项到文本文件
def write_outline_items(f, items, indent_level=0):
    """递归写入大纲项到文本文件（仅标题）"""
    for item in items:
        indent = "  " * indent_level
        f.write(f"{indent}- {item.get('title', '')}\n")
        if "children" in item and item["children"]:
            write_outline_items(f, item["children"], indent_level + 1)


# 辅助函数：写入完整内容到文本文件
def write_full_content(f, items, indent_level=0):
    """递归写入完整内容到文本文件（标题+内容）"""
    for item in items:
        indent = "  " * indent_level
        f.write(f"{indent}- {item.get('title', '')}\n")

        # 写入内容（如果存在）
        if "content" in item and item["content"]:
            content_indent = "  " * (indent_level + 1)
            f.write(f"{content_indent}  {item['content']}\n\n")

        # 递归处理子项
        if "children" in item and item["children"]:
            write_full_content(f, item["children"], indent_level + 1)
