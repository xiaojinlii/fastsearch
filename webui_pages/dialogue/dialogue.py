from urllib.parse import urlencode

import streamlit as st

from application.settings import VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD
from streamlit_chatbox import *
import os

from webui_pages.api_request import ApiRequest, DEFAULT_BASE_URL

chat_box = ChatBox(
    assistant_avatar=os.path.join(
        "static/system",
        "chat_icon.png"
    )
)


def dialogue_page(api: ApiRequest):
    chat_input_placeholder = "请输入查询内容，换行请使用Shift+Enter。"

    def on_kb_change():
        st.toast(f"已加载知识库： {st.session_state.selected_kb}")

    with st.sidebar:
        kb_list = api.list_knowledge_bases()
        index = 0
        selected_kb = st.selectbox(
            "请选择知识库：",
            kb_list,
            index=index,
            on_change=on_kb_change,
            key="selected_kb",
        )
        kb_top_k = st.number_input("匹配知识条数：", 1, 20, VECTOR_SEARCH_TOP_K)

        ## Bge 模型会超过1
        score_threshold = st.slider("知识匹配分数阈值：", 0.0, 2.0, float(SCORE_THRESHOLD), 0.01)

    chat_box.output_messages()

    if prompt := st.chat_input(chat_input_placeholder, key="prompt"):
        chat_box.user_say(prompt)

        chat_box.ai_say([
            f"正在查询知识库 `{selected_kb}` ...",
            Markdown("...", in_expander=True, title="知识库匹配结果", state="complete"),
        ])

        docs = api.search_kb_docs(knowledge_base_name=selected_kb, query=prompt, top_k=kb_top_k, score_threshold=score_threshold)

        source_documents = []
        for inum, doc in enumerate(docs):
            filename = doc["metadata"]["source"]
            parameters = urlencode({"knowledge_base_name": selected_kb, "file_name": filename})
            url = f"{DEFAULT_BASE_URL}/knowledge_base/download_file?" + parameters
            text = f"""出处 [{inum + 1}] [{filename}]({url}) \n\n{doc["page_content"]}\n\n"""
            source_documents.append(text)

        if len(source_documents) == 0:
            chat_box.update_msg(f"<span style='color:red'>未找到相关文档！</span>", element_index=0, streaming=False)
        else:
            chat_box.update_msg(f"<span style='color:green'>查询结果如下：</span>", element_index=0, streaming=False)
        chat_box.update_msg("\n\n".join(source_documents), element_index=1, streaming=False)
