from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from .config import settings


def bam_mat_khau(mat_khau: str) -> str:
    # bcrypt giới hạn 72 byte
    return bcrypt.hashpw(mat_khau.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def kiem_mat_khau(mat_khau: str, hash_: str) -> bool:
    try:
        return bcrypt.checkpw(mat_khau.encode("utf-8")[:72], hash_.encode("utf-8"))
    except ValueError:
        return False


def tao_token(nguoi_dung_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": str(nguoi_dung_id), "exp": exp},
                      settings.jwt_secret, algorithm=settings.jwt_algorithm)


def doc_token(token: str) -> int:
    data = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return int(data["sub"])
