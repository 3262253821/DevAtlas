"""create documents tables

Revision ID: 8f3c265b9cf5
Revises: 6e204972da4f
Create Date: 2026-08-22 22:45:48.159287

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '8f3c265b9cf5'
down_revision: Union[str, Sequence[str], None] = '6e204972da4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 先创建 documents。
    # 注意：此时暂时不创建 current_version_id 的外键。
    op.create_table(
        "documents",
        sa.Column(
            "id",
            mysql.BIGINT(unsigned=True),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "knowledge_base_id",
            mysql.BIGINT(unsigned=True),
            nullable=False,
        ),
        sa.Column(
            "original_filename",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "normalized_filename",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "file_type",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "current_version_id",
            mysql.BIGINT(unsigned=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id"],
            ["knowledge_bases.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "knowledge_base_id",
            "normalized_filename",
            name="uq_documents_knowledge_base_filename",
        ),
    )

    op.create_index(
        "ix_documents_knowledge_base_updated",
        "documents",
        ["knowledge_base_id", "updated_at"],
        unique=False,
    )

    # documents 已存在，现在创建 document_versions。
    op.create_table(
        "document_versions",
        sa.Column(
            "id",
            mysql.BIGINT(unsigned=True),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "document_id",
            mysql.BIGINT(unsigned=True),
            nullable=False,
        ),
        sa.Column(
            "version_number",
            mysql.INTEGER(unsigned=True),
            nullable=False,
        ),
        sa.Column(
            "file_sha256",
            mysql.CHAR(length=64),
            nullable=False,
        ),
        sa.Column(
            "storage_path",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "file_size",
            mysql.BIGINT(unsigned=True),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "chunk_count",
            mysql.INTEGER(unsigned=True),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_document_versions_number",
        ),
        sa.UniqueConstraint(
            "document_id",
            "file_sha256",
            name="uq_document_versions_sha256",
        ),
    )

    op.create_index(
        "ix_document_versions_document_status",
        "document_versions",
        ["document_id", "status"],
        unique=False,
    )

    # 两个表都存在后，再补上 documents.current_version_id 外键。
    op.create_foreign_key(
        "fk_documents_current_version_id",
        "documents",
        "document_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_documents_current_version_id",
        "documents",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_documents_knowledge_base_updated",
        table_name="documents",
    )
    op.drop_table("documents")

    op.drop_index(
        "ix_document_versions_document_status",
        table_name="document_versions",
    )
    op.drop_table("document_versions")
