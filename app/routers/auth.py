from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import NguoiDung, PhanQuyen
from ..security import kiem_mat_khau, tao_token
from ..schemas import TokenRa, NguoiDungRa
from ..deps import lay_nguoi_dung_hien_tai

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenRa)
def dang_nhap(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2 dùng trường 'username' -> ở đây là email
    nd = db.query(NguoiDung).filter_by(email=form.username).first()
    if not nd or not kiem_mat_khau(form.password, nd.mat_khau_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sai email hoặc mật khẩu")
    return TokenRa(access_token=tao_token(nd.id))


@router.get("/me", response_model=NguoiDungRa)
def toi(nd: NguoiDung = Depends(lay_nguoi_dung_hien_tai)):
    return nd


@router.get("/quyen-cua-toi")
def quyen_cua_toi(nd: NguoiDung = Depends(lay_nguoi_dung_hien_tai),
                  db: Session = Depends(get_db)):
    """Trả quyền theo module của vai trò hiện tại -> UI dựng menu & ẩn/hiện nút."""
    rows = db.query(PhanQuyen).filter_by(vai_tro_id=nd.vai_tro_id).all()
    return {
        "vai_tro": nd.vai_tro.ma, "ten_vai_tro": nd.vai_tro.ten, "email": nd.email,
        "quyen": {r.module: r.muc for r in rows},
    }
