# fastsearch
基于 xiaoapi 的知识库系统


## 安装
```
pip install -r requirements.txt
```

## 配置
在 application/settings 中 修改以下配置：
```python
"""
向量数据库配置
"""
VECTOR_DB = {
    "faiss": {
    },
    "es": {
        "host": "127.0.0.1",
        "port": "9200",
        "user": "elastic",
        "password": "gv3Z0Nnti2gdApgzLmUN",
        "ca_certs": r"D:\kibana-8.11.0\data\ca_1703500158232.crt",
    },
}

# 是否启用reranker模型
USE_RERANKER = True
# 选用的reranker模型
RERANKER_MODEL_URL = "http://10.12.25.5:21021"
# 选用的embeddings模型
EMBEDDINGS_MODEL_URL = "http://10.12.25.5:21021"
```


## 初始化数据库
```
python manage.py sqlalchemy create-tables
```


## 启动
```
python manage.py run-server
```