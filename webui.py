import streamlit as st
from streamlit_option_menu import option_menu

from webui_pages.api_request import ApiRequest
from webui_pages.dialogue.dialogue import dialogue_page
from webui_pages.knowledge_base.knowledge_base import knowledge_base_page
import os
from application.settings import VERSION, TITLE

api = ApiRequest()

if __name__ == "__main__":
    st.set_page_config(
        f"{TITLE} WebUI",
        os.path.join("static/system", "favicon.png"),
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/xiaojinlii/fastsearch',
            'Report a bug': "https://github.com/xiaojinlii/fastsearch/issues",
            'About': f"""欢迎使用 {TITLE} WebUI {VERSION}！"""
        }
    )

    pages = {
        "知识库查询": {
            "icon": "chat",
            "func": dialogue_page,
        },
        "知识库管理": {
            "icon": "hdd-stack",
            "func": knowledge_base_page,
        },
    }

    with st.sidebar:

        st.image(
            os.path.join(
                "static/system",
                "facebook_cover_photo_1.png"
            ),
            use_column_width=True
        )
        st.caption(
            f"""<p align="right">当前版本：{VERSION}</p>""",
            unsafe_allow_html=True,
        )
        options = list(pages)
        icons = [x["icon"] for x in pages.values()]

        default_index = 0
        selected_page = option_menu(
            "",
            options=options,
            icons=icons,
            # menu_icon="chat-quote",
            default_index=default_index,
        )

    if selected_page in pages:
        pages[selected_page]["func"](api=api)
