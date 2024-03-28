"""
FastAPI settings for project.
"""

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 注意：不要在生产中打开调试运行!
DEBUG = True

####################
# PROJECT SETTINGS #
####################
TITLE = "Fast Search"
DESCRIPTION = "基于 xiaoapi 的知识库系统"
VERSION = "0.0.1"


############
# UVICORN #
############
# 监听主机IP，默认开放给本网络所有主机
HOST = "0.0.0.0"
# 监听端口
PORT = 9000
# 工作进程数
WORKERS = 1


##############
# MIDDLEWARE #
##############
# List of middleware to use. Order is important; in the request phase, these
# middleware will be applied in the order given, and in the response
# phase the middleware will be applied in reverse order.
MIDDLEWARES = [
    "xiaoapi.middleware.register_request_log_middleware",
]


###############
# Fast Search #
###############
"""
知识库默认存储路径
"""
KB_ROOT_PATH = os.path.join(BASE_DIR, "knowledge_base")
if not os.path.exists(KB_ROOT_PATH):
    os.mkdir(KB_ROOT_PATH)
DB_ROOT_PATH = os.path.join(KB_ROOT_PATH, "info.db")

"""
数据库配置项
"""
SQLALCHEMY_DATABASE_URL_SYNC = f"sqlite:///{DB_ROOT_PATH}"

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

"""知识库配置"""
# 默认向量库/全文检索引擎类型。可选：faiss, milvus(离线) & zilliz(在线), pgvector,全文检索引擎es
DEFAULT_VS_TYPE = "es"

# 知识库匹配向量数量
VECTOR_SEARCH_TOP_K = 3

# 知识库匹配的距离阈值，一般取值范围在0-1之间，SCORE越小，距离越小从而相关度越高。
# 但有用户报告遇到过匹配分值超过1的情况，为了兼容性默认设为1，在WEBUI中调整范围为0-2
SCORE_THRESHOLD = 1.0

# 是否开启中文标题加强，以及标题增强的相关配置
# 通过增加标题判断，判断哪些文本为标题，并在metadata中进行标记；
# 然后将文本与往上一级的标题进行拼合，实现文本信息的增强。
ZH_TITLE_ENHANCE = False

# 是否启用reranker模型
USE_RERANKER = True
# 选用的reranker模型
RERANKER_MODEL_URL = "http://10.12.25.5:21021"
# 选用的embeddings模型
EMBEDDINGS_MODEL_URL = "http://10.12.25.5:21021"


"""
分词器
TextSplitter配置项，如果你不明白其中的含义，就不要修改。
"""
# 知识库中单段文本长度(不适用MarkdownHeaderTextSplitter)
CHUNK_SIZE = 250
# 知识库中相邻文本重合长度(不适用MarkdownHeaderTextSplitter)
OVERLAP_SIZE = 50

# 分词器配置
TEXT_SPLITTER_DICT = {
    "ChineseRecursiveTextSplitter": {
        "source": "huggingface",  # 选择tiktoken则使用openai的方法
        "tokenizer_name_or_path": "",
    },
    "SpacyTextSplitter": {
        "source": "huggingface",
        "tokenizer_name_or_path": "gpt2",
    },
    "RecursiveCharacterTextSplitter": {
        "source": "tiktoken",
        "tokenizer_name_or_path": "cl100k_base",
    },
    "MarkdownHeaderTextSplitter": {
        "headers_to_split_on":
            [
                ("#", "head1"),
                ("##", "head2"),
                ("###", "head3"),
                ("####", "head4"),
            ]
    },
}


"""
文档加载器
"""
# PDF OCR 控制：只对宽高超过页面一定比例（图片宽/页面宽，图片高/页面高）的图片进行 OCR。
# 这样可以避免 PDF 中一些小图片的干扰，提高非扫描版 PDF 处理速度
PDF_OCR_THRESHOLD = (0.6, 0.6)

# 不同文件类型对应的加载器
LOADER_DICT = {
    "UnstructuredHTMLLoader": ['.html'],
    "MHTMLLoader": ['.mhtml'],
    # "UnstructuredMarkdownLoader": ['.md'],
    "TextLoader": ['.md'],
    "JSONLoader": [".json"],
    "JSONLinesLoader": [".jsonl"],
    "CSVLoader": [".csv"],
    # "FilteredCSVLoader": [".csv"], 如果使用自定义分割csv
    "RapidOCRPDFLoader": [".pdf"],
    "RapidOCRDocLoader": ['.docx', '.doc'],
    "RapidOCRPPTLoader": ['.ppt', '.pptx', ],
    "RapidOCRLoader": ['.png', '.jpg', '.jpeg', '.bmp'],
    "UnstructuredFileLoader": ['.eml', '.msg', '.rst',
                               '.rtf', '.txt', '.xml',
                               '.epub', '.odt', '.tsv'],
    "UnstructuredEmailLoader": ['.eml', '.msg'],
    "UnstructuredEPubLoader": ['.epub'],
    "UnstructuredExcelLoader": ['.xlsx', '.xls', '.xlsd'],
    "NotebookLoader": ['.ipynb'],
    "UnstructuredODTLoader": ['.odt'],
    "PythonLoader": ['.py'],
    "UnstructuredRSTLoader": ['.rst'],
    "UnstructuredRTFLoader": ['.rtf'],
    "SRTLoader": ['.srt'],
    "TomlLoader": ['.toml'],
    "UnstructuredTSVLoader": ['.tsv'],
    "UnstructuredWordDocumentLoader": ['.docx', '.doc'],
    "UnstructuredXMLLoader": ['.xml'],
    "UnstructuredPowerPointLoader": ['.ppt', '.pptx'],
    "EverNoteLoader": ['.enex'],
}
