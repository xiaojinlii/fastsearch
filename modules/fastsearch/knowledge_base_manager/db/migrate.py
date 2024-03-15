from .base import engine, Base

from .models.knowledge_base_model import KnowledgeBaseModel
from .models.knowledge_file_model import KnowledgeFileModel, FileDocModel


def create_tables():
    Base.metadata.create_all(bind=engine)


def reset_tables():
    Base.metadata.drop_all(bind=engine)
    create_tables()


if __name__ == "__main__":
    create_tables()
    # reset_tables()
