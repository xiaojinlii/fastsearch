from abc import ABC, abstractmethod
from typing import Union, List
from langchain_core.documents import Document

from application.settings import EMBEDDINGS_MODEL_URL
from modules.fastsearch.langchain.embeddings import LangchainEmbeddings

embeddings_model = LangchainEmbeddings(base_url=EMBEDDINGS_MODEL_URL)


class VectorKB(ABC):
    def __init__(self, knowledge_base_name: str):
        self.kb_name = knowledge_base_name
        self.embeddings_model = embeddings_model

    @abstractmethod
    def add_docs(self, docs: List[Document], **kwargs):
        """添加文档到向量库"""
        raise NotImplemented

    @abstractmethod
    def delete_docs(self, kb_file, **kwargs):
        """从向量库中删除文档"""
        raise NotImplemented

    @abstractmethod
    def search(self, query: str, top_k: int, score_threshold: float):
        """从向量库中查询文档"""
        raise NotImplemented

    @abstractmethod
    def get_docs_by_ids(self, ids: List[str]) -> List[Document]:
        return []


class VectorDB(ABC):
    def __init__(self):
        self.kbs = {}

    def create_kb(self, kb_name: str):
        """创建一个知识库"""
        kb = self._create_kb(kb_name)
        self.kbs[kb_name] = kb
        return kb

    def delete_kb(self, kb_name: str):
        """删除一个知识库"""
        self._delete_kb(kb_name)
        self.kbs.pop(kb_name, None)

    def get_kb(self, kb_name: str):
        """获取知识库"""
        if kb_name in self.kbs:
            return self.kbs[kb_name]

        kb = self._get_kb(kb_name)
        if kb is not None:
            self.kbs[kb_name] = kb
        return kb

    # --- Custom methods ---

    @abstractmethod
    def exist_kb(self, kb_name: str):
        """知识库是否存在"""
        return False

    @abstractmethod
    def _create_kb(self, kb_name: str) -> VectorKB:
        raise NotImplemented

    @abstractmethod
    def _delete_kb(self, kb_name: str):
        raise NotImplemented

    @abstractmethod
    def _get_kb(self, kb_name: str) -> VectorKB:
        raise NotImplemented

    @abstractmethod
    def clear_kb(self, kb_name: str):
        """清空知识库"""
        raise NotImplemented


class SupportedVSType:
    ES = 'es'


class VectorDBFactory:
    dbs = {}

    @staticmethod
    def get_vector_db(vector_store_type: Union[str, SupportedVSType]) -> VectorDB:
        if vector_store_type in VectorDBFactory.dbs:
            return VectorDBFactory.dbs[vector_store_type]

        db = VectorDBFactory.create_db(vector_store_type)
        if db is not None:
            VectorDBFactory.dbs[vector_store_type] = db
        return db

    @staticmethod
    def create_db(vector_store_type: Union[str, SupportedVSType]) -> VectorDB:
        if isinstance(vector_store_type, str):
            vector_store_type = getattr(SupportedVSType, vector_store_type.upper())

        if vector_store_type == SupportedVSType.ES:
            from .elasticsearch_db import ElasticsearchDB
            return ElasticsearchDB()

        return None
