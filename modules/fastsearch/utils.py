from langchain_core.documents import Document


def validate_kb_name(knowledge_base_id: str) -> bool:
    # 检查是否包含预期外的字符或路径攻击关键字
    if "../" in knowledge_base_id:
        return False
    return True


class DocumentWithVSId(Document):
    """
    矢量化后的文档
    """
    id: str = None
    score: float = 3.0
