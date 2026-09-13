from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge_base import KnowledgeBaseCreate


class KnowledgeBaseNotFoundError(Exception):
    pass


class DuplicateKnowledgeBaseError(Exception):
    pass

# 创建知识库
def create_knowledge_base(
    db: Session,
    owner_id: int,  # 这个owner_id是由路由端的current_user.id传递过来的
    data: KnowledgeBaseCreate,
) -> KnowledgeBase:
    existing_knowledge_base = db.scalar(
        select(KnowledgeBase).where(
            KnowledgeBase.owner_id == owner_id,  # 检查用户是否存在
            KnowledgeBase.name == data.name,  # 检查名称是否已存在（这里再查一次重复名称，确保唯一性，防止并发请求绕过代码检查）
        )
    )
    
    # 检查知识库是否存在重复名称，存在就抛出异常
    if existing_knowledge_base is not None:
        raise DuplicateKnowledgeBaseError

    # 创建知识库对象
    knowledge_base = KnowledgeBase(
        owner_id=owner_id,
        name=data.name,
        description=data.description,
    )

    db.add(knowledge_base)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateKnowledgeBaseError

    db.refresh(knowledge_base)

    return knowledge_base

# 获取用户所有知识库, 仅返回用户创建的知识库
def list_knowledge_bases(
    db: Session,
    owner_id: int,
) -> list[KnowledgeBase]:
    statement = (
        select(KnowledgeBase)
        .where(KnowledgeBase.owner_id == owner_id)
        .order_by(KnowledgeBase.updated_at.desc())
    )
    # db.scalars(statement): 取出查询结果中的ORM对象
    return list(db.scalars(statement).all())

# 获取知识库详情, 仅返回用户创建的知识库
def get_knowledge_base(
    db: Session,
    owner_id: int,
    knowledge_base_id: int,
) -> KnowledgeBase:
    # 必须同时满足知识库ID和用户ID正确才能返回知识库详情
    statement = select(KnowledgeBase).where(
        KnowledgeBase.id == knowledge_base_id,
        KnowledgeBase.owner_id == owner_id,
    )

    knowledge_base = db.scalar(statement)

    # 这里返回的是404而不是403,是对当前用户不可见的资源，统一表现为不存在，避免泄露其他用户是否拥有这个资源。
    if knowledge_base is None:
        raise KnowledgeBaseNotFoundError

    return knowledge_base

# 删除知识库
def delete_knowledge_base(
    db: Session,
    owner_id: int,
    knowledge_base_id: int,
) -> None:
    # 这里复用了get_knowledge_base函数，因为删除知识库时需要先检查知识库是否存在，再删除知识库
    # 删除操作天然满足只能删除自己已有的知识库，不会删除其他用户的知识库
    knowledge_base = get_knowledge_base(
        db,
        owner_id,
        knowledge_base_id,
    )

    db.delete(knowledge_base)
    db.commit()