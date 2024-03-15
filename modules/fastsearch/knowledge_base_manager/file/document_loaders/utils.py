import importlib
from typing import Dict
import chardet
from langchain_community import document_loaders
from core.logger import logger


class JSONLinesLoader(document_loaders.JSONLoader):
    """
    行式 Json 加载器，要求文件扩展名为 .jsonl
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._json_lines = True


document_loaders.JSONLinesLoader = JSONLinesLoader


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

SUPPORTED_EXTS = [ext for sublist in LOADER_DICT.values() for ext in sublist]


def get_loader_name(file_extension):
    for loader_name, extensions in LOADER_DICT.items():
        if file_extension in extensions:
            return loader_name


def get_loader(loader_name: str, file_path: str, loader_kwargs: Dict = None):
    '''
    根据loader_name和文件路径或内容返回文档加载器。
    '''
    loader_kwargs = loader_kwargs or {}
    try:
        if loader_name in ["RapidOCRPDFLoader", "RapidOCRLoader", "FilteredCSVLoader",
                           "RapidOCRDocLoader", "RapidOCRPPTLoader"]:
            document_loaders_module = importlib.import_module('modules.fastsearch.knowledge_base_manager.file.document_loaders')
        else:
            document_loaders_module = importlib.import_module('langchain_community.document_loaders')
        DocumentLoader = getattr(document_loaders_module, loader_name)
    except Exception as e:
        msg = f"为文件{file_path}查找加载器{loader_name}时出错：{e}"
        logger.error(f'{e.__class__.__name__}: {msg}')
        document_loaders_module = importlib.import_module('langchain_community.document_loaders')
        DocumentLoader = getattr(document_loaders_module, "UnstructuredFileLoader")

    if loader_name == "UnstructuredFileLoader":
        loader_kwargs.setdefault("autodetect_encoding", True)
    elif loader_name == "CSVLoader":
        if not loader_kwargs.get("encoding"):
            # 如果未指定 encoding，自动识别文件编码类型，避免langchain loader 加载文件报编码错误
            with open(file_path, 'rb') as struct_file:
                encode_detect = chardet.detect(struct_file.read())
            if encode_detect is None:
                encode_detect = {"encoding": "utf-8"}
            loader_kwargs["encoding"] = encode_detect["encoding"]

    elif loader_name == "JSONLoader":
        loader_kwargs.setdefault("jq_schema", ".")
        loader_kwargs.setdefault("text_content", False)
    elif loader_name == "JSONLinesLoader":
        loader_kwargs.setdefault("jq_schema", ".")
        loader_kwargs.setdefault("text_content", False)
    elif loader_name == "TextLoader":
        loader_kwargs.setdefault("autodetect_encoding", True)

    loader = DocumentLoader(file_path, **loader_kwargs)
    return loader
