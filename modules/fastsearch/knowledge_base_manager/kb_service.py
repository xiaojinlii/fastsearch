import os
from typing import Any, Dict, List, ClassVar

from fastapi import UploadFile
from langchain_core.documents import Document
from pydantic.v1 import root_validator, BaseModel, Field

from application.settings import CHUNK_SIZE, OVERLAP_SIZE, ZH_TITLE_ENHANCE, VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD
from core.logger import logger
from core.exception import CustomException
from .file.knowledge_file import KnowledgeFile, files2docs_in_thread
from .vectordb.base import VectorDBFactory, VectorDB, VectorKB

from .db import repository as db
from .file import file_manager
from modules.fastsearch.utils import DocumentWithVSId


class KBService(BaseModel):
    services: ClassVar[dict] = {}

    kb_name: str = Field()
    vs_type: str = Field(default=None)
    vector_db: Any = Field(default=None, exclude=True)
    vector_kb: Any = Field(default=None, exclude=True)

    def __repr__(self) -> str:
        return f"{self.kb_name} @ {self.vs_type}"

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        kb_name, vs_type = db.load_kb_from_db(values["kb_name"])
        if kb_name is None:
            raise CustomException(f"数据库中不存在知识库：{values['kb_name']}.")

        values["vs_type"] = vs_type

        vector_db = VectorDBFactory.get_vector_db(vs_type)
        if vector_db is None:
            raise CustomException(f"不存在向量库：{vs_type}.")
        values["vector_db"] = vector_db

        vector_kb = vector_db.get_kb(values['kb_name'])
        if vector_kb is None:
            raise CustomException(f"不存在向量数据库：{values['kb_name']}.")
        values["vector_kb"] = vector_kb

        if not file_manager.exist_kb(values['kb_name']):
            raise CustomException(f"文件管理中不存在知识库目录：{values['kb_name']}.")

        return values

    @staticmethod
    def exist_kb(kb_name: str):
        """
        知识库是否存在
        """
        if kb_name in KBService.services:
            return True

        try:
            KBService.get_kb_service(kb_name)
            return True
        except CustomException as e:
            return False

    @staticmethod
    def create_kb(kb_name: str, vector_store_type: str):
        """
        创建知识库
        """
        file_manager.create_kb(kb_name)

        vector_db = VectorDBFactory.get_vector_db(vector_store_type)
        if vector_db is None:
            raise CustomException(f"不存在向量库：{vector_store_type}.")
        vector_db.create_kb(kb_name)

        kb_info = f"关于{kb_name}的知识库"
        db.add_kb_to_db(kb_name, kb_info, vector_store_type)

    @staticmethod
    def delete_kb(kb_name: str):
        """
        删除知识库
        """
        kb_service = KBService.get_kb_service(kb_name)

        kb_service.vector_db.delete_kb(kb_name)
        db.delete_files_from_db(kb_name)
        db.delete_kb_from_db(kb_name)
        file_manager.delete_kb(kb_name)
        KBService.services.pop(kb_name, None)

    @staticmethod
    def get_kb_service(kb_name: str):
        if kb_name in KBService.services:
            return KBService.services[kb_name]

        kb_service = KBService(kb_name=kb_name)  # 知识库不存在这里会抛异常
        KBService.services[kb_name] = kb_service
        return kb_service

    @staticmethod
    def get_all_kb_names():
        return db.list_kbs_from_db()

    @staticmethod
    def get_all_kb_details():
        kbs_in_folder = file_manager.list_kbs_from_folder()
        kbs_in_db = db.list_kbs_from_db()
        result = {}

        for kb in kbs_in_folder:
            result[kb] = {
                "kb_name": kb,
                "vs_type": "",
                "kb_info": "",
                "file_count": 0,
                "create_time": None,
                "in_folder": True,
                "in_db": False,
            }

        for kb in kbs_in_db:
            kb_detail = db.get_kb_detail(kb)
            if kb_detail:
                kb_detail["in_db"] = True
                if kb in result:
                    result[kb].update(kb_detail)
                else:
                    kb_detail["in_folder"] = False
                    result[kb] = kb_detail

        data = []
        for i, v in enumerate(result.values()):
            v['No'] = i + 1
            data.append(v)

        return data

    def update_kb_info(self, kb_info: str):
        status = db.add_kb_to_db(self.kb_name, kb_info, self.vs_type)
        return status

    def clear_kb(self):
        self.vector_db.clear_kb(self.kb_name)
        db.delete_files_from_db(self.kb_name)

    def search_docs(self,
                    query: str,
                    top_k: int = VECTOR_SEARCH_TOP_K,
                    score_threshold: float = SCORE_THRESHOLD,
                    ) -> List[Document]:
        docs = self.vector_kb.search(query, top_k, score_threshold)
        return docs

    def list_file_docs(self, file_name: str = None, metadata: Dict = {}) -> List[DocumentWithVSId]:
        """
        通过file_name或metadata检索Document
        """
        doc_infos = db.list_docs_from_db(kb_name=self.kb_name, file_name=file_name, metadata=metadata)
        docs = []
        for x in doc_infos:
            doc_list = self.vector_kb.get_docs_by_ids([x["id"]])
            if len(doc_list) > 0:
                # 处理非空的情况
                doc_info = doc_list[0]
                doc_with_id = DocumentWithVSId(**doc_info.dict(), id=x["id"])
                docs.append(doc_with_id)
            else:
                # 处理空的情况
                # 可以选择跳过当前循环迭代或执行其他操作
                pass
        return docs

    def list_kb_file_details(self) -> List[Dict]:
        files_in_folder = file_manager.list_files_from_folder(self.kb_name)
        files_in_db = db.list_files_from_db(self.kb_name)
        result = {}

        for doc in files_in_folder:
            result[doc] = {
                "kb_name": self.kb_name,
                "file_name": doc,
                "file_ext": os.path.splitext(doc)[-1],
                "file_version": 0,
                "document_loader": "",
                "docs_count": 0,
                "text_splitter": "",
                "create_time": None,
                "in_folder": True,
                "in_db": False,
            }
        lower_names = {x.lower(): x for x in result}
        for doc in files_in_db:
            doc_detail = db.get_file_detail(self.kb_name, doc)
            if doc_detail:
                doc_detail["in_db"] = True
                if doc.lower() in lower_names:
                    result[lower_names[doc.lower()]].update(doc_detail)
                else:
                    doc_detail["in_folder"] = False
                    result[doc] = doc_detail

        data = []
        for i, v in enumerate(result.values()):
            v['No'] = i + 1
            data.append(v)
        return data

    def upload_files(self, files: List[UploadFile], override: bool = False):
        success_files = []
        failed_files = {}
        for result in file_manager.save_files_in_thread(files, knowledge_base_name=self.kb_name, override=override):
            filename = result["data"]["file_name"]
            if result["code"] == 200:
                success_files.append(filename)
            else:
                failed_files[filename] = result["msg"]

        return success_files, failed_files

    def handle_doc_source(self, docs: List[Document], file_name):
        for doc in docs:
            doc.metadata["source"] = file_name
        return docs

    def exist_file(self, file_name: str):
        return db.file_exists_in_db(KnowledgeFile(knowledge_base_name=self.kb_name, filename=file_name))

    def add_file(self, kb_file: KnowledgeFile):
        docs = kb_file.file2text()
        docs = self.handle_doc_source(docs, kb_file.filename)
        doc_infos = self.vector_kb.add_docs(docs)
        db.add_file_to_db(kb_file, custom_docs=False, docs_count=len(docs), doc_infos=doc_infos)

    def delete_file(self, kb_file: KnowledgeFile, delete_content: bool = False, **kwargs):
        self.vector_kb.delete_docs(kb_file)
        db.delete_file_from_db(kb_file)
        if delete_content:
            file_manager.delete_file(kb_file.filepath)

    def update_files(self, filenames: List[str], chunk_size=CHUNK_SIZE, chunk_overlap=OVERLAP_SIZE,
                     zh_title_enhance=ZH_TITLE_ENHANCE):
        failed_files = {}
        kb_files = []

        for file_name in filenames:
            try:
                kb_files.append(KnowledgeFile(filename=file_name, knowledge_base_name=self.kb_name))
            except Exception as e:
                msg = f"加载文档 {file_name} 时出错：{e}"
                logger.error(f'{e.__class__.__name__}: {msg}')
                failed_files[file_name] = msg

        # 从文件生成docs，并进行向量化。
        # 这里利用了KnowledgeFile的缓存功能，在多线程中加载Document，然后传给KnowledgeFile
        for status, result in files2docs_in_thread(
                kb_files,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                zh_title_enhance=zh_title_enhance
        ):
            if status:
                kb_name, file_name, splited_docs = result
                kb_file = KnowledgeFile(filename=file_name, knowledge_base_name=self.kb_name)
                kb_file.splited_docs = splited_docs

                self.delete_file(kb_file, delete_content=False)
                self.add_file(kb_file)
            else:
                kb_name, file_name, error = result
                failed_files[file_name] = error

        return failed_files






