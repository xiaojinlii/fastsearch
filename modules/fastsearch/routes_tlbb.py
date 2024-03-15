import random
from fastapi import APIRouter, File, Form, UploadFile, Body, Query
from langchain_core.documents import Document

from application.configs import DEFAULT_VS_TYPE
from application.settings import SCORE_THRESHOLD, DEFAULT_QA_KB, DEFAULT_QA_KB_MAX_NUM, DEFAULT_QA_KB_PER_NUM
from core.exception import CustomException
from utils.response import SuccessResponse, ErrorResponse
from core.logger import logger
from .utils import validate_kb_name, DocumentWithVSId
from .knowledge_base_manager.kb_service import KBService

router = APIRouter()


@router.post("/check_str_like", summary="检测问题相似度，并返回已加载的问题和答案")
def check_str_like(
        query: str = Body("", description="问题", examples=["你是谁"]),
        score_threshold: float = Body(SCORE_THRESHOLD, description="阈值", examples=["0.5"])
):
    logger.info(f"游戏服尝试使用缓存数据库中的答案")
    try:
        kb_service = KBService.get_kb_service(DEFAULT_QA_KB)
        docs = kb_service.search_docs(query, 1, score_threshold)

        answer = ""
        score = 0
        cached = False
        if len(docs) > 0:
            doc = [DocumentWithVSId(**x[0].dict(), score=x[1], id=x[0].metadata.get("id")) for x in docs][0]
            answers = doc.metadata.get("answers")
            if len(answers) > 0:
                answer = random.choice(answers)
                score = doc.score
                cached = True
        data = {"answer": answer, "score": score}

        return SuccessResponse(msg="success" if cached else "不存在相似的问题", data=data)
    except CustomException as e:
        return ErrorResponse(msg=e.msg)


@router.post("/set_qa_into_db", summary="将需要缓存的问题和答案加入到向量库")
def set_qa_into_db(
        query: str = Body("", description="问题", examples=["你是谁"]),
        answer: str = Body("", description="答案", examples=["我是xxx"]),
):
    logger.info(f"游戏服尝试向缓存数据库中添加qa")
    try:
        if not KBService.exist_kb(DEFAULT_QA_KB):
            KBService.create_kb(DEFAULT_QA_KB, DEFAULT_VS_TYPE)
        kb_service = KBService.get_kb_service(DEFAULT_QA_KB)

        now_num = kb_service.vector_kb.get_all_docs_num()
        if now_num >= DEFAULT_QA_KB_MAX_NUM:
            return SuccessResponse(
                msg=f"向qa问答库 {DEFAULT_QA_KB}添加文档失败！文档数量达到上限！")  # todo code!=200的话，游戏服会重新请求，这里先用SuccessResponse

        old_docs = kb_service.search_docs(query, 1, SCORE_THRESHOLD)
        answers = []
        if len(old_docs) > 0:
            answers = old_docs[0][0].metadata.get("answers")
            if len(answers) >= DEFAULT_QA_KB_PER_NUM:
                return SuccessResponse(msg="达到单个问题的答案最大缓存数量")  # todo 同上

            for a in answers:
                if a == answer:
                    return SuccessResponse(msg="此答案已被缓存过")  # todo 同上

            source = old_docs[0][0].metadata.get("source")
            kb_service.vector_kb.delete_docs(source)

        answers.append(answer)
        new_metadata = {"answers": answers, "source": query}
        new_docs = [Document(page_content=query, metadata=new_metadata)]
        kb_service.vector_kb.add_docs(new_docs, not_refresh_vs_cache=True)

        return SuccessResponse(
            msg=f"向缓存知识库{DEFAULT_QA_KB}中添加新缓存问答成功,当前问题:\'{query}\' 有{len(answers)}条缓存答案")
    except CustomException as e:
        return ErrorResponse(msg=e.msg)
