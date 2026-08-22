from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path 
from uuid import uuid4 # 生成随机唯一 ID

from fastapi import UploadFile

from app.core.config import settings
from app.core.file_security import (
    HASH_CHUNK_SIZE,
    MAX_FILE_SIZE,
    ensure_safe_path,
    normalize_filename,
    validate_extension,
)

# 文件大小为 0 时抛出
class EmptyFileError(Exception):
    pass

# 超过 10 MB 时抛出
class FileTooLargeError(Exception):
    pass

# 数据结构，这是一个保存结果对象
# frozen=True表示对象创建后不能修改字段，避免保存结果被意外改变
@dataclass(frozen=True)
class SavedFile:
    original_filename: str # 用户原始文件名
    stored_filename: str # 服务器实际保存的文件名
    storage_path: Path # 文件在服务器上的实际路径
    file_type: str
    file_size: int # 文件字节数
    file_sha256: str # 文件内容指纹

# 保存上传文件
async def save_uploaded_file(
    upload_file: UploadFile,
) -> SavedFile:
    # 规范化文件名
    original_filename = normalize_filename(
        upload_file.filename or ""
    )

    # 校验扩展名
    file_type = validate_extension(original_filename)

    # 取得后缀，这个后缀的用途是：生成随机存储名时仍然保留文件类型
    suffix = Path(original_filename).suffix.lower()

    # 创建上传目录
    upload_dir = settings.upload_dir.resolve()
    upload_dir.mkdir(
        # parents=True：父目录不存在时一并创建；
        # exist_ok=True：目录已经存在时不报错。
        parents=True,
        exist_ok=True,
    )

    # 使用随机存储名，避免同名上传覆盖已有文件
    stored_filename = f"{uuid4().hex}{suffix}"

    # 再次检查路径
    target_path = ensure_safe_path(
        upload_dir,
        stored_filename,
    )

    # 初始化哈希和计数器
    digest = sha256()
    # file_size 统计已经读取的字节数
    file_size = 0

    # 创建文件并分块写入
    try:
        # "wb":写入二进制的意思
        with target_path.open("wb") as output_file:
            # 循环持续读取文件内容，直到读取到空数据块
            while True:
                # 每次读取1MB数据
                chunk = await upload_file.read(
                    HASH_CHUNK_SIZE
                )

                if not chunk:
                    break

                file_size += len(chunk)

                if file_size > MAX_FILE_SIZE:
                    raise FileTooLargeError(
                        "File size exceeds the 10 MB limit"
                    )
                # 把这块数据加入 SHA-256
                digest.update(chunk)
                # 把这块数据写入磁盘
                output_file.write(chunk)

        if file_size == 0:
            raise EmptyFileError("Uploaded file is empty")

    # 清理半成品文件
    except Exception:
        # 保存过程中任何一步失败，都删除已经写入的半成品
        # missing_ok=True 表示文件已经不存在时，删除操作也不再报错
        target_path.unlink(missing_ok=True)
        raise

        # 关闭上传文件
    finally:
        await upload_file.close()

    return SavedFile(
        original_filename=original_filename,
        stored_filename=stored_filename,
        storage_path=target_path,
        file_type=file_type.removeprefix("."),
        file_size=file_size,
        file_sha256=digest.hexdigest(),
    )