import os
from .configs import *


"""项目根目录"""
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


"""安全警告: 不要在生产中打开调试运行!"""
DEBUG = False


"""项目配置"""
TITLE = "FastAPI Framework"
DESCRIPTION = "基于FastAPI的Web框架"
VERSION = "0.0.1"


"""
临时文件目录
TEMP_DIR：临时文件目录绝对路径
"""
TEMP_DIR = os.path.join(BASE_DIR, "temp")


"""
挂载静态目录，并添加路由访问，此路由不会在接口文档中显示
STATIC_ENABLE：是否启用静态目录访问
STATIC_URL：路由访问
STATIC_ROOT：静态文件目录绝对路径
官方文档：https://fastapi.tiangolo.com/tutorial/static-files/
"""
STATIC_ENABLE = True
STATIC_URL = "/static"
STATIC_DIR = "static"
STATIC_ROOT = os.path.join(BASE_DIR, STATIC_DIR)


"""
跨域解决
详细解释：https://cloud.tencent.com/developer/article/1886114
官方文档：https://fastapi.tiangolo.com/tutorial/cors/
"""
# 是否启用跨域
CORS_ORIGIN_ENABLE = True
# 只允许访问的域名列表，* 代表所有
ALLOW_ORIGINS = ["*"]
# 是否支持携带 cookie
ALLOW_CREDENTIALS = True
# 设置允许跨域的http方法，比如 get、post、put等。
ALLOW_METHODS = ["*"]
# 允许携带的headers，可以用来鉴别来源等作用。
ALLOW_HEADERS = ["*"]


"""
中间件配置
"""
MIDDLEWARES = [
    "middleware.request_log_middleware.register_request_log_middleware",
]


"""
全局事件配置
"""
EVENTS = [
    "extensions.mongodb.mongodb.connect_mongo" if MONGO_DB_ENABLE else None,
    "extensions.redis.redis.connect_redis" if REDIS_DB_ENABLE else None,
    "extensions.elasticsearch.elasticsearch.connect_elasticsearch" if ELASTICSEARCH_ENABLE else None,
]
