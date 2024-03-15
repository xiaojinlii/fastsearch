"""
数据库配置文件
"""

import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


"""
数据库配置项
连接引擎官方文档：https://docs.sqlalchemy.org/en/20/core/engines.html
mysql配置说明：mysql+asyncmy://数据库用户名:数据库密码@数据库地址:数据库端口/数据库名称，需安装asyncmy
sqlite配置说明：sqlite+aiosqlite:///数据库路径，需安装aiosqlite
"""
SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{BASE_DIR}/info.db"


"""
数据库迁移
会将MIGRATE_MODELS里所有的model迁移到数据库表结构
"""
MIGRATE_MODELS = [
    "modules.quickstart.models.*"
]


"""
Redis 数据库配置
格式："redis://:密码@地址:端口/数据库名称"
"""
REDIS_DB_ENABLE = False
REDIS_DB_URL = "redis://:123456@177.8.0.5:6379/1"

"""
MongoDB 数据库配置
格式：mongodb://用户名:密码@地址:端口/?authSource=数据库名称
"""
MONGO_DB_ENABLE = False
MONGO_DB_NAME = "fastapi"
MONGO_DB_URL = f"mongodb://admin:123456@177.8.0.6:27017/?authSource={MONGO_DB_NAME}"


"""
Elasticsearch 配置
"""
ELASTICSEARCH_ENABLE = False
ELASTICSEARCH_USER = "elastic"
ELASTICSEARCH_PASSWORD = "gv3Z0Nnti2gdApgzLmUN"
ELASTICSEARCH_URL = "http://127.0.0.1:9200"
