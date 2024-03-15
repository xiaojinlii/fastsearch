import json
import urllib
from fastapi import APIRouter, File, Form, UploadFile, Body, Query
from sse_starlette import EventSourceResponse
from starlette.responses import FileResponse
from typing import List

from application.settings import CHUNK_SIZE, OVERLAP_SIZE, ZH_TITLE_ENHANCE, VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD, \
    USE_RERANKER, RERANKER_MODEL_URL
from core.exception import CustomException
from utils.response import SuccessResponse, ErrorResponse
from core.logger import logger
from .utils import validate_kb_name, DocumentWithVSId
from .knowledge_base_manager.file import file_manager
from .knowledge_base_manager.file.knowledge_file import files2docs_in_thread, KnowledgeFile
from .knowledge_base_manager.kb_service import KBService
from modules.fastsearch.langchain.reranker import LangchainReranker


router = APIRouter()


@router.get("/list_knowledge_bases", summary="获取知识库列表")
async def list_knowledge_bases():
    names = KBService.get_all_kb_names()
    return SuccessResponse(data=names)


@router.get("/list_knowledge_base_details", summary="获取所有知识库信息")
async def list_knowledge_base_details():
    details = KBService.get_all_kb_details()
    return SuccessResponse(data=details)


@router.post("/create_knowledge_base", summary="创建知识库")
async def create_knowledge_base(
        knowledge_base_name: str = Body(..., examples=["samples"]),
        vector_store_type: str = Body("faiss"),
):
    if not validate_kb_name(knowledge_base_name):
        return ErrorResponse(msg="Don't attack me")
    if knowledge_base_name is None or knowledge_base_name.strip() == "":
        return ErrorResponse(msg="知识库名称不能为空，请重新填写知识库名称")
    if KBService.exist_kb(knowledge_base_name):
        return ErrorResponse(msg=f"已存在知识库{knowledge_base_name}")

    try:
        KBService.create_kb(knowledge_base_name, vector_store_type)
    except Exception as e:
        msg = f"创建知识库出错： {e}"
        logger.error(f'{e.__class__.__name__}: {msg}')
        return ErrorResponse(msg=msg)

    return SuccessResponse(msg=f"已新增知识库 {knowledge_base_name}")


@router.post("/delete_knowledge_base", summary="删除知识库")
async def delete_knowledge_base(
        knowledge_base_name: str = Body(..., examples=["samples"]),
):
    if not validate_kb_name(knowledge_base_name):
        return ErrorResponse(msg="Don't attack me")

    knowledge_base_name = urllib.parse.unquote(knowledge_base_name)
    if not KBService.exist_kb(knowledge_base_name):
        return ErrorResponse(msg=f"未找到知识库 {knowledge_base_name}")

    try:
        KBService.delete_kb(knowledge_base_name)
        return SuccessResponse(f"成功删除知识库 {knowledge_base_name}")
    except Exception as e:
        msg = f"删除知识库时出现意外： {e}"
        logger.error(f'{e.__class__.__name__}: {msg}')
        return ErrorResponse(msg=msg)


@router.post("/update_kb_info", summary="更新知识库介绍")
async def update_kb_info(
        knowledge_base_name: str = Body(..., description="知识库名称", examples=["samples"]),
        kb_info: str = Body(..., description="知识库介绍", examples=["这是一个知识库"])
):
    if not validate_kb_name(knowledge_base_name):
        return ErrorResponse(code=403, msg="Don't attack me")

    try:
        kb_service = KBService.get_kb_service(knowledge_base_name)
    except CustomException as e:
        return ErrorResponse(msg=e.msg)

    kb_service.update_kb_info(kb_info)
    return SuccessResponse(msg=f"知识库介绍修改完成", data={"kb_info": kb_info})


@router.post("/recreate_vector_store", summary="根据content中文档重建向量库，流式输出处理进度。")
async def recreate_vector_store(
        knowledge_base_name: str = Body(..., examples=["samples"]),
        allow_empty_kb: bool = Body(True),
        chunk_size: int = Body(CHUNK_SIZE, description="知识库中单段文本最大长度"),
        chunk_overlap: int = Body(OVERLAP_SIZE, description="知识库中相邻文本重合长度"),
        zh_title_enhance: bool = Body(ZH_TITLE_ENHANCE, description="是否开启中文标题加强"),
):
    def output():
        try:
            kb_service = KBService.get_kb_service(knowledge_base_name)
        except CustomException as e:
            yield {"code": 404, "msg": f"未找到知识库 ‘{knowledge_base_name}’"}

        if not allow_empty_kb:
            yield {"code": 404, "msg": f"未找到知识库 ‘{knowledge_base_name}’"}

        kb_service.clear_kb()
        files = file_manager.list_files_from_folder(knowledge_base_name)
        kb_files = [(file, knowledge_base_name) for file in files]
        i = 0
        for status, result in files2docs_in_thread(
                kb_files,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                zh_title_enhance=zh_title_enhance
        ):
            if status:
                kb_name, file_name, docs = result
                kb_file = KnowledgeFile(filename=file_name, knowledge_base_name=kb_name)
                kb_file.splited_docs = docs
                yield json.dumps({
                    "code": 200,
                    "msg": f"({i + 1} / {len(files)}): {file_name}",
                    "total": len(files),
                    "finished": i + 1,
                    "doc": file_name,
                }, ensure_ascii=False)
                kb_service.add_file(kb_file)
            else:
                kb_name, file_name, error = result
                msg = f"添加文件‘{file_name}’到知识库‘{knowledge_base_name}’时出错：{error}。已跳过。"
                logger.error(msg)
                yield json.dumps({
                    "code": 500,
                    "msg": msg,
                })
            i += 1

    return EventSourceResponse(output())


@router.post("/search_docs", summary="搜索知识库")
async def search_docs(
        query: str = Body("", description="用户输入", examples=["你好"]),
        knowledge_base_name: str = Body(..., description="知识库名称", examples=["samples"]),
        top_k: int = Body(VECTOR_SEARCH_TOP_K, description="匹配向量数"),
        score_threshold: float = Body(SCORE_THRESHOLD,
                                      description="知识库匹配相关度阈值，取值范围在0-1之间，"
                                                  "SCORE越小，相关度越高，"
                                                  "取到1相当于不筛选，建议设置在0.5左右",
                                      ge=0, le=2),
):
    try:
        kb_service = KBService.get_kb_service(knowledge_base_name)
    except CustomException as e:
        return ErrorResponse(msg=e.msg)

    docs = kb_service.search_docs(query, top_k, score_threshold)
    data = [DocumentWithVSId(**x[0].dict(), score=x[1], id=x[0].metadata.get("id")) for x in docs]

    if USE_RERANKER:
        reranker_model = LangchainReranker(base_url=RERANKER_MODEL_URL, top_n=top_k, reranker_score=0.7)
        logger.debug("---------pre rerank------------------")
        logger.debug(data)
        data = reranker_model.compress_documents(documents=data, query=query)
        logger.debug("---------after rerank------------------")
        logger.debug(data)

    return data


@router.get("/list_kb_file_details", summary="获取某个知识库的所有文件信息")
async def list_kb_file_details(knowledge_base_name: str = Query(..., description="知识库名称", examples=["samples"]),):
    try:
        kb_service = KBService.get_kb_service(knowledge_base_name)
    except CustomException as e:
        return ErrorResponse(msg=e.msg)

    details = kb_service.list_kb_file_details()
    return SuccessResponse(data=details)


@router.post("/upload_files", summary="上传文件到知识库，并/或进行向量化")
async def upload_files(
        files: List[UploadFile] = File(..., description="上传文件，支持多文件"),
        knowledge_base_name: str = Form(..., description="知识库名称", examples=["samples"]),
        override: bool = Form(False, description="覆盖已有文件"),
        to_vector_store: bool = Form(True, description="上传文件后是否进行向量化"),
        chunk_size: int = Form(CHUNK_SIZE, description="知识库中单段文本最大长度"),
        chunk_overlap: int = Form(OVERLAP_SIZE, description="知识库中相邻文本重合长度"),
        zh_title_enhance: bool = Form(ZH_TITLE_ENHANCE, description="是否开启中文标题加强"),
):
    try:
        kb_service = KBService.get_kb_service(knowledge_base_name)
    except CustomException as e:
        return ErrorResponse(msg=e.msg)

    failed_files = {}

    success_files, failed = kb_service.upload_files(files, override=override)
    failed_files.update(failed)

    if to_vector_store:
        failed = kb_service.update_files(success_files, chunk_size=chunk_size, chunk_overlap=chunk_overlap,
                                         zh_title_enhance=zh_title_enhance)
        failed_files.update(failed)

    return SuccessResponse(msg="文件上传与向量化完成", data={"failed_files": failed_files})


@router.post("/update_files", summary="更新现有文件到知识库")
async def update_files(
        knowledge_base_name: str = Body(..., description="知识库名称", examples=["samples"]),
        file_names: List[str] = Body(..., description="文件名称，支持多文件", examples=[["file_name1", "text.txt"]]),
        chunk_size: int = Body(CHUNK_SIZE, description="知识库中单段文本最大长度"),
        chunk_overlap: int = Body(OVERLAP_SIZE, description="知识库中相邻文本重合长度"),
        zh_title_enhance: bool = Body(ZH_TITLE_ENHANCE, description="是否开启中文标题加强"),
):
    try:
        kb_service = KBService.get_kb_service(knowledge_base_name)
    except CustomException as e:
        return ErrorResponse(msg=e.msg)

    failed_files = {}
    failed = kb_service.update_files(file_names, chunk_size=chunk_size, chunk_overlap=chunk_overlap,
                                     zh_title_enhance=zh_title_enhance)
    failed_files.update(failed)
    return SuccessResponse(msg="更新文档完成", data={"failed_files": failed_files})


@router.post("/delete_files", summary="删除知识库内指定文件")
def delete_files(
        knowledge_base_name: str = Body(..., examples=["samples"]),
        file_names: List[str] = Body(..., examples=[["file_name.md", "test.txt"]]),
        delete_content: bool = Body(False),
):
    if not validate_kb_name(knowledge_base_name):
        return ErrorResponse(msg="Don't attack me")

    knowledge_base_name = urllib.parse.unquote(knowledge_base_name)
    try:
        kb_service = KBService.get_kb_service(knowledge_base_name)
    except CustomException as e:
        return ErrorResponse(msg=e.msg)

    failed_files = {}
    for file_name in file_names:
        if not kb_service.exist_file(file_name):
            failed_files[file_name] = f"未找到文件 {file_name}"

        try:
            kb_file = KnowledgeFile(filename=file_name, knowledge_base_name=knowledge_base_name)
            kb_service.delete_file(kb_file, delete_content)
        except Exception as e:
            msg = f"{file_name} 文件删除失败，错误信息：{e}"
            logger.error(f'{e.__class__.__name__}: {msg}')
            failed_files[file_name] = msg

    return SuccessResponse(msg="文件删除完成", data={"failed_files": failed_files})


@router.post("/download_file", summary="下载对应的知识文件")
async def download_file(
        knowledge_base_name: str = Query(..., description="知识库名称", examples=["samples"]),
        file_name: str = Query(..., description="文件名称", examples=["test.txt"]),
        preview: bool = Query(False, description="是：浏览器内预览；否：下载"),
):
    if not validate_kb_name(knowledge_base_name):
        return ErrorResponse(msg="Don't attack me")

    if preview:
        content_disposition_type = "inline"
    else:
        content_disposition_type = None

    try:
        kb_file = KnowledgeFile(filename=file_name, knowledge_base_name=knowledge_base_name)
        if file_manager.exist_file(kb_file.kb_name, kb_file.filename):
            return FileResponse(
                path=kb_file.filepath,
                filename=kb_file.filename,
                media_type="multipart/form-data",
                content_disposition_type=content_disposition_type
            )
    except Exception as e:
        msg = f"{kb_file.filename} 读取文件失败，错误信息是：{e}"
        logger.error(f'{e.__class__.__name__}: {msg}')
        return ErrorResponse(msg=msg)

    return ErrorResponse(msg=f"{kb_file.filename} 读取文件失败")


@router.post("/list_file_docs", summary="列出某个文件的全部文档")
async def list_file_docs(
        knowledge_base_name: str = Body(..., description="知识库名称", examples=["samples"]),
        file_name: str = Body("", description="文件名称，支持 sql 通配符"),
        metadata: dict = Body({}, description="根据 metadata 进行过滤，仅支持一级键"),
):
    try:
        kb_service = KBService.get_kb_service(knowledge_base_name)
    except CustomException as e:
        return ErrorResponse(msg=e.msg)

    data = kb_service.list_file_docs(file_name=file_name, metadata=metadata)
    return data
