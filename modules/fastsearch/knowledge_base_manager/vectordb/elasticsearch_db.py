import operator
from enum import Enum
from typing import List, Dict

from elasticsearch import Elasticsearch
from langchain_community.vectorstores.elasticsearch import ElasticsearchStore
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_core.documents import Document

from application.settings import VECTOR_DB
from core.logger import logger
from .base import VectorDB, VectorKB


def weighted_reciprocal_rank(
        doc_lists: List[List[Document]], weights: List[float]
) -> List[Document]:
    """
    Perform weighted Reciprocal Rank Fusion on multiple rank lists.
    You can find more details about RRF here:
    https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf

    Args:
        doc_lists: A list of rank lists, where each rank list contains unique items.

    Returns:
        list: The final aggregated list of items sorted by their weighted RRF
                scores in descending order.
    """
    if len(doc_lists) != len(weights):
        raise ValueError(
            "Number of rank lists must be equal to the number of weights."
        )

    # Create a union of all unique documents in the input doc_lists
    all_documents = set()
    for doc_list in doc_lists:
        for doc in doc_list:
            # logger.info(f"doc:{doc} tyep:{type(doc)}")
            all_documents.add(doc[0].page_content)

    # Initialize the RRF score dictionary for each document
    rrf_score_dic = {doc: 0.0 for doc in all_documents}

    # A constant added to the rank, controlling the balance between the importance
    # of high-ranked items and the consideration given to lower-ranked items.
    # Default is 60.
    c = 60

    # Calculate RRF scores for each document
    for doc_list, weight in zip(doc_lists, weights):
        for rank, doc in enumerate(doc_list, start=1):
            rrf_score = weight * (1 / (rank + c))
            rrf_score_dic[doc[0].page_content] += rrf_score

    # Sort documents by their RRF scores in descending order
    sorted_documents = sorted(
        rrf_score_dic.keys(), key=lambda x: rrf_score_dic[x], reverse=True
    )

    # Map the sorted page_content back to the original document objects
    page_content_to_doc_map = {
        doc[0].page_content: doc for doc_list in doc_lists for doc in doc_list
    }
    sorted_docs = [
        page_content_to_doc_map[page_content] for page_content in sorted_documents
    ]

    return sorted_docs


def handle_score_threshold(score_threshold, k, docs):
    if score_threshold is not None:
        cmp = (
            operator.ge
        )
        docs = [
            (doc, similarity)
            for doc, similarity in docs
            if cmp(similarity, score_threshold)
        ]
    return docs[:k]


class Properties(Enum):
    CONTEXT = "context"
    DENSE_VECTOR = "dense_vector"


class ElasticsearchKB(VectorKB):
    def __init__(self, knowledge_base_name: str,  es_connection: Elasticsearch, distance_strategy: DistanceStrategy):
        super().__init__(knowledge_base_name)

        self.index_name = knowledge_base_name
        self.es_connection = es_connection

        self.store = ElasticsearchStore(
            index_name=self.index_name,
            embedding=self.embeddings_model,
            es_connection=es_connection,
            query_field=Properties.CONTEXT.value,
            vector_query_field=Properties.DENSE_VECTOR.value,
            distance_strategy=distance_strategy
        )

    def add_docs(self, docs: List[Document], **kwargs):
        print(f"ElasticsearchKB.print 输入的docs参数长度为:{len(docs)}")
        print("*" * 100)
        self.store.add_documents(documents=docs)

        # 获取 id 和 source , 格式：[{"id": str, "metadata": dict}, ...]
        print("写入数据成功.")
        print("*" * 100)

        if self.es_connection.indices.exists(index=self.index_name):
            file_path = docs[0].metadata.get("source")
            query = {
                "query": {
                    "term": {
                        "metadata.source.keyword": file_path
                    }
                }
            }
            search_results = self.es_connection.search(index=self.index_name, body=query)
            if len(search_results["hits"]["hits"]) == 0:
                raise ValueError("召回元素个数为0")
        info_docs = [{"id": hit["_id"], "metadata": hit["_source"]["metadata"]} for hit in search_results["hits"]["hits"]]
        return info_docs

    def delete_docs(self, kb_file, **kwargs):
        # 从向量数据库中删除索引(文档名称是Keyword)
        query = {
            "query": {
                "term": {
                    "metadata.source.keyword": kb_file.filename
                }
            }
        }
        # 注意设置size，默认返回10个。
        search_results = self.es_connection.search(index=self.index_name, body=query, size=50)
        delete_list = [hit["_id"] for hit in search_results['hits']['hits']]

        if len(delete_list) == 0:
            return None
        else:
            for doc_id in delete_list:
                try:
                    self.es_connection.delete(index=self.index_name, id=doc_id, refresh=True)
                except Exception as e:
                    logger.error(f"ES Docs Delete Error! {e}")

    def search(self, query: str, top_k: int, score_threshold: float):
        knn_docs = self.search_knn(query, top_k, score_threshold)
        bm25_docs = self.search_bm25(query, top_k, score_threshold)

        logger.info(f"es_kb_service knn_docs:{knn_docs}")
        logger.info(f"es_kb_service bm25_docs:{bm25_docs}")

        # rrf 融合
        docs = weighted_reciprocal_rank([knn_docs, bm25_docs], [0.5, 0.5])

        return docs

    def search_knn(self, query: str, top_k: int, score_threshold: float):
        """向量搜索"""
        docs = self.store.similarity_search_with_score(query=query, k=top_k)
        # docs = handle_score_threshold(score_threshold, top_k, docs) # 这里的分数范围比较小，不适合做阈值筛选，放在后面的reranker里做阈值筛选
        return docs

    def search_bm25(self, query: str, top_k: int, score_threshold: float):
        query_dict = {
            "explain": False,
            "query": {
                # "match": {
                #     "context": query
                # },
                "multi_match": {
                    "query": query,
                    "type": "most_fields",
                    "fields": ["content", "metadata.head1", "metadata.head2", "metadata.head3"]
                }
            },
            "size": top_k
        }
        res = self.es_connection.search(index=self.index_name, body=query_dict)

        fields = []
        if "metadata" not in fields:
            fields.append("metadata")

        def default_doc_builder(hit: Dict) -> Document:
            return Document(
                page_content=hit["_source"].get("context", ""),
                metadata=hit["_source"]["metadata"],
            )

        doc_builder = default_doc_builder

        docs_and_scores = []
        for hit in res["hits"]["hits"]:
            for field in fields:
                if field in hit["_source"] and field not in [
                    "metadata",
                    "context",
                ]:
                    if "metadata" not in hit["_source"]:
                        hit["_source"]["metadata"] = {}
                    hit["_source"]["metadata"][field] = hit["_source"][field]

            docs_and_scores.append(
                (
                    doc_builder(hit),
                    hit["_score"],
                )
            )
        return docs_and_scores

    def get_docs_by_ids(self, ids: List[str]) -> List[Document]:
        results = []
        for doc_id in ids:
            try:
                res = self.es_connection.get(
                    index=self.index_name,
                    id=doc_id,
                    refresh=True
                )
                if "_source" in res:
                    source = res["_source"]
                    context = ""
                    metadata = ""
                    if "context" in source:
                        context = source["context"]
                    if "metadata" in source:
                        metadata = source["metadata"]
                    results.append(Document(page_content=context, metadata=metadata))
            except Exception as e:
                logger.error(f"ES Docs get_doc_by_ids Error! {e}")
        return results


class ElasticsearchDB(VectorDB):
    def __init__(self, distance_strategy: DistanceStrategy = DistanceStrategy.EUCLIDEAN_DISTANCE):
        super().__init__()
        self.distance_strategy = distance_strategy

        config = VECTOR_DB["es"]
        ip = config["host"]
        port = config["port"]
        user = config["user"]
        password = config["password"]
        ca_certs = config["ca_certs"]

        try:
            if user != "" and password != "":
                self.es_connection = Elasticsearch(
                    f"https://{ip}:{port}",
                    basic_auth=(user, password),
                    ca_certs=ca_certs,
                )
            else:
                self.es_connection = Elasticsearch(
                    f"https://{ip}:{port}",
                    ca_certs=ca_certs,
                )
        except ConnectionError:
            print("连接到 Elasticsearch 失败！")
        except Exception as e:
            print(f"Error 发生 : {e}")

    def exist_kb(self, kb_name: str):
        return self._exist_index(kb_name)

    def _create_kb(self, kb_name: str) -> VectorKB:
        if not self._exist_index(kb_name):
            self._create_index(kb_name, self.distance_strategy)
        kb = ElasticsearchKB(
            knowledge_base_name=kb_name,
            es_connection=self.es_connection,
            distance_strategy=self.distance_strategy
        )
        return kb

    def _delete_kb(self, kb_name: str):
        if self._exist_index(kb_name):
            self._delete_index(kb_name)

    def _get_kb(self, kb_name: str) -> VectorKB:
        if not self._exist_index(kb_name):
            return None
        kb = ElasticsearchKB(
            knowledge_base_name=kb_name,
            es_connection=self.es_connection,
            distance_strategy=self.distance_strategy
        )
        return kb

    def clear_kb(self, kb_name: str):
        self._delete_index(kb_name)
        self._create_index(kb_name, self.distance_strategy)

    def _exist_index(self, index_name: str):
        return self.es_connection.indices.exists(index=index_name)

    def _delete_index(self, index_name: str):
        self.es_connection.indices.delete(index=index_name)

    def _create_index(self,
                      index_name: str,
                      similarity: DistanceStrategy,
                      k1: float = 2.0,
                      b: float = 0.75,
                      dims: int = 1024
                      ):
        """
        使用BM25搜索时建议使用ik分词器， ik分词器需要额外安装， 参照 https://github.com/medcl/elasticsearch-analysis-ik
        ik分词器可以自定义词库以及设置停用词，参照 https://zq99299.github.io/note-book/elasticsearch-senior/ik/31-config.html#%E4%B8%BB%E8%A6%81%E9%85%8D%E7%BD%AE%E8%A7%A3%E8%AF%B4
        elasticsearch同义词库需放在 elasticsearch-8.11.0/config 路径下， 参照 https://www.elastic.co/guide/en/elasticsearch/reference/8.11/analysis-synonym-tokenfilter.html
        """
        if similarity is DistanceStrategy.COSINE:
            similarityAlgo = "cosine"
        elif similarity is DistanceStrategy.EUCLIDEAN_DISTANCE:
            similarityAlgo = "l2_norm"
        elif similarity is DistanceStrategy.DOT_PRODUCT:
            similarityAlgo = "dot_product"
        elif similarity is DistanceStrategy.MAX_INNER_PRODUCT:
            similarityAlgo = "max_inner_product"
        else:
            raise ValueError(f"Similarity {similarity} not supported.")

        # Define the index settings and mappings
        settings = {
            "analysis": {
                "filter": {
                    "custom_synonyms_filter": {
                        "type": "synonym",
                        "synonyms_path": "tlbb_synonym.dic"
                    }
                },
                "analyzer": {
                    "custom_analyzer": {
                        "tokenizer": "ik_smart",
                        "filter": [
                            "custom_synonyms_filter"
                        ]
                    }
                },
            },
            "similarity": {
                "custom_bm25": {
                    "type": "BM25",
                    "k1": k1,
                    "b": b,
                }
            },
        }
        mappings = {
            "properties": {
                Properties.CONTEXT.value: {
                    "type": "text",
                    "similarity": "custom_bm25",  # Use the custom BM25 similarity
                    "analyzer": "custom_analyzer"
                },
                Properties.DENSE_VECTOR.value: {
                    "type": "dense_vector",
                    "dims": dims,
                    "index": True,
                    "similarity": similarityAlgo
                },

                "metadata": {
                    "properties": {
                        "head1": {
                            "type": "text",
                            "similarity": "custom_bm25",
                            "analyzer": "custom_analyzer"
                        },
                        "head2": {
                            "type": "text",
                            "similarity": "custom_bm25",
                            "analyzer": "custom_analyzer"
                        },
                        "head3": {
                            "type": "text",
                            "similarity": "custom_bm25",
                            "analyzer": "custom_analyzer"
                        },
                        # "source": {
                        #     "type": "text",
                        #     "fields": {
                        #         "keyword": {
                        #             "type": "keyword",
                        #             "ignore_above": 256
                        #         }
                        #     }
                        # }
                    }
                }

            }
        }

        # Create the index with the specified settings and mappings
        try:
            self.es_connection.indices.create(index=index_name, mappings=mappings, settings=settings)
        except Exception as e:
            print(f"###create_index Error 发生 : {e}")


if __name__ == "__main__":
    db = ElasticsearchDB()
    db.es_connection.info()
    print(db.exist_kb("test"))
