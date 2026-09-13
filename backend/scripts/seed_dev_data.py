"""恢复 DevAtlas 本地开发演示数据。

脚本只面向 development 环境使用：

    python backend/scripts/seed_dev_data.py

它会幂等地创建开发账号、知识库，并导入 tests 目录中的示例文档。
再次执行不会因为相同文件内容而重复创建文档版本。
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from uuid import uuid4


# 脚本位于 backend/scripts，需要把 backend 加入模块搜索路径，
# 这样才能复用项目现有的 app、数据库 Session 和文档导入服务。
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402

from app.core.file_security import (  # noqa: E402
    calculate_sha256,
    ensure_safe_path,
    normalize_filename,
    validate_extension,
)
from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.document_version import DocumentVersion  # noqa: E402
from app.models.knowledge_base import KnowledgeBase  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.document_ingestion import ingest_document  # noqa: E402
from app.services.document_reindex import reindex_document  # noqa: E402
from app.services.file_storage import SavedFile  # noqa: E402


DEFAULT_DOC_NAMES = (
    "DevAtlas团队入门手册.txt",
    "订单服务故障排查手册.md",
    "DevAtlas系统架构与操作规范.pdf",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="创建或恢复 DevAtlas 本地开发演示数据。",
    )
    parser.add_argument(
        "--username",
        default=os.getenv("DEVATLAS_SEED_USERNAME", "devatlas-demo"),
        help="开发账号用户名，默认读取 DEVATLAS_SEED_USERNAME。",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("DEVATLAS_SEED_PASSWORD", "DevAtlas123!"),
        help="开发账号密码，默认读取 DEVATLAS_SEED_PASSWORD。",
    )
    parser.add_argument(
        "--knowledge-base-name",
        default=os.getenv(
            "DEVATLAS_SEED_KB_NAME",
            "DevAtlas 开发演示知识库",
        ),
        help="演示知识库名称。",
    )
    parser.add_argument(
        "--skip-documents",
        action="store_true",
        help="只创建账号和知识库，不导入示例文档。",
    )
    return parser.parse_args()


def _get_or_create_user(
    db,
    username: str,
    password: str,
) -> User:
    user = db.scalar(
        select(User).where(User.username == username)
    )

    if user is not None:
        # 种子脚本不覆盖已有账号密码，只确保开发账号仍可登录。
        if not user.is_active:
            user.is_active = True
            db.commit()
        return user

    user = User(
        username=username,
        password_hash=hash_password(password),
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _get_or_create_knowledge_base(
    db,
    owner_id: int,
    name: str,
) -> KnowledgeBase:
    knowledge_base = db.scalar(
        select(KnowledgeBase).where(
            KnowledgeBase.owner_id == owner_id,
            KnowledgeBase.name == name,
        )
    )

    if knowledge_base is not None:
        return knowledge_base

    knowledge_base = KnowledgeBase(
        owner_id=owner_id,
        name=name,
        description="用于本地开发、演示和面试录屏的示例知识库",
    )
    db.add(knowledge_base)
    db.commit()
    db.refresh(knowledge_base)
    return knowledge_base


def _build_saved_file(
    source_path: Path,
) -> SavedFile:
    """把 tests 中的源文件复制到上传目录，并构造成导入服务需要的 SavedFile。"""
    original_filename = normalize_filename(source_path.name)
    file_type = validate_extension(original_filename)
    upload_dir = PROJECT_ROOT / "others" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(original_filename).suffix.lower()
    stored_filename = f"{uuid4().hex}{suffix}"
    target_path = ensure_safe_path(upload_dir, stored_filename)
    shutil.copy2(source_path, target_path)

    return SavedFile(
        original_filename=original_filename,
        stored_filename=stored_filename,
        storage_path=target_path,
        file_type=file_type.removeprefix("."),
        file_size=target_path.stat().st_size,
        file_sha256=calculate_sha256(target_path),
    )


def _seed_documents(
    db,
    knowledge_base_id: int,
) -> list[str]:
    messages: list[str] = []
    tests_dir = PROJECT_ROOT / "tests"

    for filename in DEFAULT_DOC_NAMES:
        source_path = tests_dir / filename

        if not source_path.is_file():
            messages.append(f"跳过：找不到 {source_path}")
            continue

        source_sha256 = calculate_sha256(source_path)
        normalized_filename = normalize_filename(filename).casefold()
        document = db.scalar(
            select(Document).where(
                Document.knowledge_base_id == knowledge_base_id,
                Document.normalized_filename == normalized_filename,
            )
        )

        if document is not None:
            existing_version = db.scalar(
                select(DocumentVersion).where(
                    DocumentVersion.document_id == document.id,
                    DocumentVersion.file_sha256 == source_sha256,
                )
            )
            if existing_version is not None:
                if existing_version.status == "failed":
                    version = reindex_document(
                        db,
                        knowledge_base_id,
                        document.id,
                    )
                    messages.append(
                        f"已重新索引：{filename} "
                        f"(version_id={version.id}, status={version.status})"
                    )
                    continue

                messages.append(
                    f"已存在：{filename} "
                    f"(version_id={existing_version.id}, status={existing_version.status})"
                )
                continue

        saved_file = _build_saved_file(source_path)
        result = ingest_document(
            db=db,
            knowledge_base_id=knowledge_base_id,
            saved_file=saved_file,
        )
        messages.append(
            f"已导入：{filename} "
            f"(version_id={result.version.id}, status={result.version.status})"
        )

    return messages


def main() -> None:
    args = _parse_args()

    if settings.app_env.strip().lower() in {
        "production",
        "prod",
    }:
        raise SystemExit(
            "拒绝在 production 环境执行开发种子脚本。"
        )

    if not args.username.strip() or not args.password:
        raise SystemExit("开发账号用户名和密码不能为空。")

    db = SessionLocal()
    try:
        user = _get_or_create_user(
            db,
            username=args.username.strip(),
            password=args.password,
        )
        knowledge_base = _get_or_create_knowledge_base(
            db,
            owner_id=user.id,
            name=args.knowledge_base_name.strip(),
        )

        print(f"开发账号：{user.username} (user_id={user.id})")
        print(
            "开发密码：使用本次命令的 --password，或 "
            "DEVATLAS_SEED_PASSWORD 环境变量。"
        )
        print(
            f"开发知识库：{knowledge_base.name} "
            f"(knowledge_base_id={knowledge_base.id})"
        )

        if args.skip_documents:
            print("已跳过示例文档导入。")
            return

        for message in _seed_documents(db, knowledge_base.id):
            print(message)
    finally:
        db.close()


if __name__ == "__main__":
    main()
