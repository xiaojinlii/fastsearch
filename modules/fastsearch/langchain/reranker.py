import os
import sys

import httpx

from typing import Optional, Sequence
from langchain_core.documents import Document
from langchain.callbacks.manager import Callbacks
from langchain.retrievers.document_compressors.base import BaseDocumentCompressor
from langchain_core.pydantic_v1 import Field

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class LangchainReranker(BaseDocumentCompressor):
    """Document compressor that uses `Cohere Rerank API`."""
    base_url: str = Field()
    top_n: int = Field()
    reranker_score: float = Field()

    def __init__(self, base_url: str, top_n: int = 3, reranker_score: float = 0):
        super().__init__(base_url=base_url, top_n=top_n, reranker_score=reranker_score)

    def compress_documents(
            self,
            documents: Sequence[Document],
            query: str,
            callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        """
        Compress documents using Cohere's rerank API.

        Args:
            documents: A sequence of documents to compress.
            query: The query to use for compressing the documents.
            callbacks: Callbacks to run during the compression process.

        Returns:
            A sequence of compressed documents.
        """
        if len(documents) == 0:  # to avoid empty api call
            return []

        doc_list = list(documents)
        texts = [d.page_content for d in doc_list]

        data = {
            "query": query,
            "texts": texts
        }
        url = f"{self.base_url}/worker_compute_score_by_query"
        response = httpx.post(url, json=data)
        results = response.json()

        for index, value in enumerate(results):
            doc = doc_list[index]
            doc.metadata["relevance_score"] = value
        doc_list.sort(key=lambda _doc: _doc.metadata["relevance_score"], reverse=True)
        ret_docs = [d for d in doc_list if d.metadata["relevance_score"] > self.reranker_score]

        top_k = self.top_n if self.top_n < len(ret_docs) else len(ret_docs)
        return ret_docs[:top_k]

    async def acompress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        """Compress retrieved documents given the query context."""
        if len(documents) == 0:  # to avoid empty api call
            return []

        doc_list = list(documents)
        texts = [d.page_content for d in doc_list]

        data = {
            "query": query,
            "texts": texts
        }
        url = f"{self.base_url}/worker_compute_score_by_query"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
        results = response.json()

        for index, value in enumerate(results):
            doc = doc_list[index]
            doc.metadata["relevance_score"] = value
        doc_list.sort(key=lambda _doc: _doc.metadata["relevance_score"], reverse=True)
        ret_docs = [d for d in doc_list if d.metadata["relevance_score"] > self.reranker_score]

        top_k = self.top_n if self.top_n < len(ret_docs) else len(ret_docs)
        return ret_docs[:top_k]


if __name__ == "__main__":
    reranker_model = LangchainReranker(base_url="http://127.0.0.1:21021", top_n=3, reranker_score=0.7)
    docs = [
        Document(page_content="早上好"),
        Document(page_content="哈喽"),
        Document(page_content="嗨"),
        Document(page_content="你好"),
    ]
    result = reranker_model.compress_documents(docs, "哈喽")
    print(result)
