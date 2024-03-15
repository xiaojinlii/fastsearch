"""
elasticsearch连接

Python Elasticsearch 文档：https://elasticsearch-py.readthedocs.io/en/latest/async.html
Elasticsearch 官网：https://www.elastic.co/guide/en/elasticsearch/reference/current/async-search.html

需要安装：
pip install elasticsearch[async]==8.11.0
"""

from fastapi import FastAPI, Request

from application.settings import ELASTICSEARCH_ENABLE, ELASTICSEARCH_URL, \
    ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD

from core.exception import CustomException

from elasticsearch import AsyncElasticsearch, AuthenticationException
from elastic_transport import ConnectionError


async def connect_elasticsearch(app: FastAPI, status: bool):
    """
    把 elasticsearch 挂载到 app 对象上面

    :param app:
    :param status:
    :return:
    """
    if status:
        try:
            connection = AsyncElasticsearch(
                ELASTICSEARCH_URL,
                basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD),
            )
            app.state.es = connection

            response = await connection.info()
            if response:
                print("Elasticsearch 连接成功")
            else:
                print("Elasticsearch 连接失败")
        except AuthenticationException as e:
            raise AuthenticationException(f"Elasticsearch 连接认证失败: {e}")
        except ConnectionError as e:
            raise ConnectionError(f"Elasticsearch 连接失败: {e}")
    else:
        print("Elasticsearch 连接关闭")
        await app.state.es.close()


def elasticsearch_getter(request: Request) -> AsyncElasticsearch:
    """
    获取 elasticsearch 连接对象

    全局挂载，使用一个数据库对象
    """
    if not ELASTICSEARCH_ENABLE:
        raise CustomException("请先配置Elasticsearch链接并启用！",
                              desc="请启用 application/settings.py: ELASTICSEARCH_ENABLE")
    return request.app.state.es
