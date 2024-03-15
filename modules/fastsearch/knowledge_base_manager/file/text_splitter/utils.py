import importlib
from langchain_text_splitters import MarkdownHeaderTextSplitter
from application.settings import TEXT_SPLITTER_DICT, CHUNK_SIZE, OVERLAP_SIZE

DEFAULT_TEXT_SPLITTER_NAME = "ChineseRecursiveTextSplitter"

# 分词器匹配， 如果未配置默认为DEFAULT_TEXT_SPLITTER_NAME
SPLITTER_DICT = {
    "None": ['.csv'],  # 无需使用分词器的格式
    "MarkdownHeaderTextSplitter": ['.md'],

}


def get_splitter_name(file_extension):
    for splitter_name, extensions in SPLITTER_DICT.items():
        if file_extension in extensions:
            return splitter_name


def make_text_splitter(
        splitter_name: str,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = OVERLAP_SIZE,
):
    """
    根据参数获取特定的分词器
    """
    if splitter_name == "None":
        return None

    splitter_name = splitter_name or "SpacyTextSplitter"
    try:
        if splitter_name == "MarkdownHeaderTextSplitter":  # MarkdownHeaderTextSplitter特殊判定
            headers_to_split_on = TEXT_SPLITTER_DICT[splitter_name]['headers_to_split_on']
            text_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on)
        else:

            try:
                # 优先使用用户自定义的text_splitter
                text_splitter_module = importlib.import_module(
                    'modules.fastsearch.knowledge_base_manager.file.text_splitter'
                )
                TextSplitter = getattr(text_splitter_module, splitter_name)
            except:
                # 否则使用langchain的text_splitter
                text_splitter_module = importlib.import_module('langchain_text_splitters')
                TextSplitter = getattr(text_splitter_module, splitter_name)

            if TEXT_SPLITTER_DICT[splitter_name]["source"] == "tiktoken":  ## 从tiktoken加载
                try:
                    text_splitter = TextSplitter.from_tiktoken_encoder(
                        encoding_name=TEXT_SPLITTER_DICT[splitter_name]["tokenizer_name_or_path"],
                        pipeline="zh_core_web_sm",
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
                except:
                    text_splitter = TextSplitter.from_tiktoken_encoder(
                        encoding_name=TEXT_SPLITTER_DICT[splitter_name]["tokenizer_name_or_path"],
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
            elif TEXT_SPLITTER_DICT[splitter_name]["source"] == "huggingface":  ## 从huggingface加载
                # if text_splitter_dict[splitter_name]["tokenizer_name_or_path"] == "":
                #     config = get_model_worker_config(llm_model)
                #     text_splitter_dict[splitter_name]["tokenizer_name_or_path"] = \
                #         config.get("model_path")

                if TEXT_SPLITTER_DICT[splitter_name]["tokenizer_name_or_path"] == "gpt2":
                    from transformers import GPT2TokenizerFast
                    from langchain.text_splitter import CharacterTextSplitter
                    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
                else:  ## 字符长度加载
                    from transformers import AutoTokenizer
                    tokenizer = AutoTokenizer.from_pretrained(
                        TEXT_SPLITTER_DICT[splitter_name]["tokenizer_name_or_path"],
                        trust_remote_code=True)
                text_splitter = TextSplitter.from_huggingface_tokenizer(
                    tokenizer=tokenizer,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
            else:
                try:
                    text_splitter = TextSplitter(
                        pipeline="zh_core_web_sm",
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
                except:
                    text_splitter = TextSplitter(
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
    except Exception as e:
        print(e)
        text_splitter_module = importlib.import_module('langchain_text_splitters')
        TextSplitter = getattr(text_splitter_module, "RecursiveCharacterTextSplitter")
        text_splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # If you use SpacyTextSplitter you can use GPU to do split likes Issue #1287
    # text_splitter._tokenizer.max_length = 37016792
    # text_splitter._tokenizer.prefer_gpu()
    return text_splitter
