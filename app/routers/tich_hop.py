"""
Module TÍCH HỢP — endpoint máy-tới-máy cho app ngoài (ProjectFlow AI) ĐỌC dữ liệu
vật tư – thiết bị thi công theo MÃ DỰ ÁN (du_an.ma). Chỉ đọc, một chiều.

Bảo mật: KHÔNG dùng token người dùng — xác thực bằng khóa chung qua header 'X-API-Key'
so với settings.tich_hop_api_key. Khóa để trống ⇒ endpoint TẮT (trả 503) để an toàn mặc định.
Khóa khai trên Render (biến TICH_HOP_API_KEY), không commit.
"""
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..config import settings
from ..models import DuAn

router = APIRouter(prefix="/tich-hop", tags=["tich_hop"])


def _kiem_key(x_api_key: str | None = Header(default=None)):
    key = (settings.tich_hop_api_key or "").strip()
    if not key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Tích hợp chưa bật (thiếu TICH_HOP_API_KEY)")
    if not x_api_key or x_api_key.strip() != key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key không hợp lệ")
    return True


@router.get("/vat-tu-thiet-bi")
def vat_tu_thiet_bi(ma: str, db: Session = Depends(get_db), _=Depends(_kiem_key)):
    """Đọc vật tư – thiết bị thi công của một dự án theo MÃ (du_an.ma, không phân biệt hoa/thường).
    Trả gọn cho ProjectFlow AI hiển thị: đối chiếu vật tư, thiết bị đang ở công trường, phiếu cấp."""
    ma = (ma or "").strip()
    if not ma:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Thiếu mã dự án")
    da = (db.query(DuAn)
          .filter(func.lower(func.trim(DuAn.ma)) == ma.lower())
          .first())
    if da is None:
        return {"tim_thay": False, "ma": ma,
                "thong_bao": "Chưa có Dự án trùng mã trong SVWS (vào module Dự án tạo dự án cùng mã)."}
    # Tái dùng đúng công thức của 3 tab (một nguồn số, khỏi lệch)
    from .du_an import vat_tu_doi_chieu
    from .thi_cong import thiet_bi_cua_du_an
    from .kho import phieu_theo_du_an
    vt = vat_tu_doi_chieu(da.id, db)
    tb = thiet_bi_cua_du_an(da.id, db)
    pc = phieu_theo_du_an(da.id, db)
    return {
        "tim_thay": True, "ma": da.ma, "ten": da.ten, "du_an_id": da.id,
        "vat_tu": vt,                       # {danh_sach:[...định mức/đã cấp...], tong:{...}}
        "thiet_bi": tb,                     # {dang_o_cong_truong:[...], lich_su:[...]}
        "phieu_cap_cho_duyet": [p for p in pc if p.get("trang_thai") == "MOI"],
        "nguon": "SVWS", "svws_du_an_id": da.id,
    }
