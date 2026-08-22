from hashlib import sha256 # SHA-256哈希函数,不是加密,是内容指纹算法,用于判断文件内容是否相同
from pathlib import Path
import re
import unicodedata

# 扩展白名单
# T06 文件上传约束：只允许 API 文档中确认的三种格式
ALLOWED_EXTENSIONS = {
    ".md",
    ".txt",
    ".pdf",
}

# API 文档规定单个文件最大 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# 计算 SHA-256 时分块读取，避免一次性把大文件全部读入内存
# 每次读取1MB
HASH_CHUNK_SIZE = 1024 * 1024

# 自定义异常: 文件格式不支持
class UnsupportedFileTypeError(Exception):
    pass

# 自定义异常: 文件名非法或路径不安全
class InvalidFilenameError(Exception):
    pass

# 文件名规范化
def normalize_filename(filename: str) -> str:
    if not filename or not filename.strip():
        raise InvalidFilenameError("Filename is empty")

    # 统一 Unicode 形式，处理全角字符等等价表示
    # 统一兼容字符表示,例如用户上传文件名中带有不规范的全角字符，可以先做统一处理
    normalized = unicodedata.normalize(
        "NFKC",
        filename,
    ).strip()

    # 统一路径分隔符后只保留最后的文件名部分
    # 这样 ../../secret.txt 不会被当成目录路径使用
    basename = Path(
        normalized.replace("\\", "/")
    ).name

    if basename in {"", ".", ".."}:
        raise InvalidFilenameError("Filename is invalid")

    # 去掉控制字符，避免文件名中出现换行或空字符
    basename = re.sub(
        r"[\x00-\x1f\x7f]",
        "_",
        basename,
    )

    if basename in {"", ".", ".."}:
        raise InvalidFilenameError("Filename is invalid")

    return basename

# 拓展名校验
def validate_extension(filename: str) -> str:
    # 接收已经规范化的文件名;lower()作用是让.PDF,.pdf,.Pdf这样统一处理
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type: {suffix or '<none>'}"
        )
    # 返回拓展名
    return suffix

# 安全路径检查
def ensure_safe_path(
    base_dir: Path,
    filename: str,
) -> Path:
    # resolve的作用是将路径转换为绝对路径，避免路径遍历攻击
    upload_root = base_dir.resolve()
    # / 是路径拼接运算符，将 upload_root 和 filename 拼接成绝对路径，然后再resolve()转换为绝对路径
    target_path = (upload_root / filename).resolve()

    try:
        # 判断target_path 是否位于 upload_root 目录内部
        target_path.relative_to(upload_root)
    except ValueError as error:
        raise InvalidFilenameError(
            "Path traversal is not allowed"
        ) from error

    return target_path

# 计算文件内容指纹
def calculate_sha256(
    file_path: Path,
) -> str:
    # 创建一个哈希计算对象
    digest = sha256()
    # 以二进制只读方式打开文件
    with file_path.open("rb") as file:
        # 每次只读1MB
        # chunk := 是海象运算符，是先把读取结果赋值给chunk，再判断chunk是否为空
        while chunk := file.read(HASH_CHUNK_SIZE):
            digest.update(chunk)
    # 返回 64 位十六进制字符串
    return digest.hexdigest()