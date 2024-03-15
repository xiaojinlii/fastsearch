from modules.fastsearch.knowledge_base_manager.db.models.knowledge_base_model import KnowledgeBaseModel
from modules.fastsearch.knowledge_base_manager.db.session import with_session


@with_session
def add_kb_to_db(session, kb_name, kb_info, vs_type):
    # 创建知识库实例
    kb = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()
    if not kb:
        kb = KnowledgeBaseModel(kb_name=kb_name, kb_info=kb_info, vs_type=vs_type)
        session.add(kb)
    else:  # update kb with new vs_type
        kb.kb_info = kb_info
        kb.vs_type = vs_type
    return True


@with_session
def list_kbs_from_db(session, min_file_count: int = -1):
    kbs = session.query(KnowledgeBaseModel.kb_name).filter(KnowledgeBaseModel.file_count > min_file_count).all()
    kbs = [kb[0] for kb in kbs]
    return kbs


@with_session
def kb_exists(session, kb_name):
    kb = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()
    status = True if kb else False
    return status


@with_session
def load_kb_from_db(session, kb_name):
    kb = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()
    if kb:
        kb_name, vs_type = kb.kb_name, kb.vs_type
    else:
        kb_name, vs_type = None, None
    return kb_name, vs_type


@with_session
def delete_kb_from_db(session, kb_name):
    kb = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()
    if kb:
        session.delete(kb)
    return True


@with_session
def get_kb_detail(session, kb_name: str) -> dict:
    kb: KnowledgeBaseModel = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()
    if kb:
        return {
            "kb_name": kb.kb_name,
            "kb_info": kb.kb_info,
            "vs_type": kb.vs_type,
            "file_count": kb.file_count,
            "create_time": kb.create_time,
        }
    else:
        return {}
