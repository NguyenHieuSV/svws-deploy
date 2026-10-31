"""💾 Sao lưu CSDL — nhật ký, chạy tay, tải bản sao lưu (CEO / ADMIN; tải file ZIP chỉ CEO). Logic ở app/sao_luu_service.py."""
import shutil

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import luu_tru, sao_luu_service as sl
from ..config import settings
from ..database import get_db
from ..models import NguoiDung, SaoLuuLog
from ..rbac import chi_vai_tro

router = APIRouter(prefix="/sao-luu", tags=["sao_luu"])


@router.get("")
def xem_sao_luu(db: Session = Depends(get_db), _=Depends(chi_vai_tro("CEO", "ADMIN"))):
    """Cấu hình đang chạy + 20 bản gần nhất + bản thành công gần nhất."""
    ds = sl.danh_sach(db, 20)
    gan = next((x for x in ds if x["trang_thai"] == "THANH_CONG"), None)
    return {"bat": settings.sao_luu_bat, "gio": settings.sao_luu_gio, "giu_ngay": settings.sao_luu_giu_ngay,
            "giu_thang": settings.sao_luu_giu_thang,
            "kho": "kho tệp B2/S3 (bền)" if luu_tru.dung_r2() else "đĩa máy chủ (KHÔNG bền — mất khi khởi động lại)",
            "co_pg_dump": bool(shutil.which("pg_dump")), "gan_nhat": gan, "danh_sach": ds}


@router.post("/chay")
def chay_sao_luu(db: Session = Depends(get_db), nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """💾 Sao lưu ngay (chạy đồng bộ — CSDL hiện tại vài chục MB, mất vài giây đến một phút)."""
    return sl.tao_ban_sao(db, "TAY", nd.id)


@router.get("/{sl_id}/tai")
def tai_sao_luu(sl_id: int, db: Session = Depends(get_db), _=Depends(chi_vai_tro("CEO"))):
    """Tải file ZIP sao lưu — chỉ CEO (chứa toàn bộ dữ liệu công ty)."""
    x = db.get(SaoLuuLog, sl_id)
    if x is None or not x.duong_dan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không còn file sao lưu này")
    return luu_tru.phan_hoi_tai(x.duong_dan, x.ten_file, "application/zip")
