from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from .database import get_db
from .security import doc_token
from .models import NguoiDung, NhanVien

oauth2 = OAuth2PasswordBearer(tokenUrl="auth/login")


def lay_nguoi_dung_hien_tai(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> NguoiDung:
    loi = HTTPException(status.HTTP_401_UNAUTHORIZED, "Token không hợp lệ",
                        headers={"WWW-Authenticate": "Bearer"})
    try:
        uid = doc_token(token)
    except jwt.PyJWTError:
        raise loi
    nd = db.get(NguoiDung, uid)
    if nd is None or nd.trang_thai != "HOAT_DONG":
        raise loi
    return nd


def nhan_vien_id_cua(db: Session, nguoi_dung_id: int):
    """Tìm nhan_vien tương ứng người dùng (để gán nguoi_tao trên phiếu)."""
    return db.query(NhanVien.id).filter_by(nguoi_dung_id=nguoi_dung_id).scalar()
