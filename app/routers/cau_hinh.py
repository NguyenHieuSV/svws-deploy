"""
Cấu hình hệ thống — phân quyền truy cập tab 'Overall Operation' (module dieu_hanh).

Cơ chế: dùng đúng RBAC sẵn có (bảng phan_quyen). 'CEO duyệt vị trí' = CEO cấp/thu hồi
quyền module 'dieu_hanh' (mức XEM) cho từng vai trò. Khi vai trò có 'dieu_hanh' thì
/auth/quyen-cua-toi trả về -> UI hiện tab. Bên trong tab, mỗi lối tắt vẫn theo quyền
module đích của vai trò (không nới quyền).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import NguoiDung, VaiTro, PhanQuyen
from ..rbac import yeu_cau
from ..audit import ghi_audit

router = APIRouter(prefix="/cau-hinh", tags=["cau_hinh"])

MODULE = "dieu_hanh"


class DuyetVaiTro(BaseModel):
    vai_tro: str
    cho_phep: bool


@router.get("/vai-tro-dieu-hanh")
def danh_sach_vai_tro(
    nd: NguoiDung = Depends(yeu_cau(MODULE, "QUAN_TRI")),
    db: Session = Depends(get_db),
):
    """Liệt kê mọi vị trí + trạng thái được truy cập Overall Operation (chỉ CEO/Quản trị)."""
    vai_tros = db.query(VaiTro).order_by(VaiTro.id).all()
    co = {pq.vai_tro_id for pq in db.query(PhanQuyen).filter_by(module=MODULE).all()}
    return [
        {"ma": v.ma, "ten": v.ten, "co_quyen": (v.ma == "CEO") or (v.id in co)}
        for v in vai_tros
    ]


@router.post("/dieu-hanh/duyet")
def duyet_vai_tro(
    payload: DuyetVaiTro,
    nd: NguoiDung = Depends(yeu_cau(MODULE, "QUAN_TRI")),
    db: Session = Depends(get_db),
):
    """CEO cấp/thu hồi quyền truy cập Overall Operation cho 1 vị trí."""
    if nd.vai_tro.ma != "CEO":
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Chỉ CEO được duyệt quyền truy cập Overall Operation.")
    vt = db.query(VaiTro).filter_by(ma=payload.vai_tro).first()
    if not vt:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy vị trí.")
    if vt.ma == "CEO":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "CEO luôn có quyền — không thể thay đổi.")
    pq = db.query(PhanQuyen).filter_by(vai_tro_id=vt.id, module=MODULE).first()
    if payload.cho_phep:
        if pq:
            pq.muc = "XEM"
        else:
            db.add(PhanQuyen(vai_tro_id=vt.id, module=MODULE, muc="XEM"))
    else:
        if pq:
            db.delete(pq)
    ghi_audit(db, nd.id, "DUYET", "phan_quyen", vt.id,
              moi={"module": MODULE, "vai_tro": vt.ma, "cho_phep": payload.cho_phep})
    db.commit()
    return {"vai_tro": vt.ma, "co_quyen": payload.cho_phep}


# ============================================================
# MA TRẬN PHÂN QUYỀN ĐẦY ĐỦ — CEO đặt: vị trí × module × mức
#   mức: KHONG (không truy cập) / XEM / THAO_TAC (đề xuất) / DUYET / QUAN_TRI
# ============================================================
MUC_HOP_LE = {"KHONG", "XEM", "THAO_TAC", "DUYET", "QUAN_TRI"}


class DatQuyen(BaseModel):
    vai_tro: str
    module: str
    muc: str


@router.get("/ma-tran-quyen")
def ma_tran_quyen(
    nd: NguoiDung = Depends(yeu_cau(MODULE, "QUAN_TRI")),
    db: Session = Depends(get_db),
):
    """Toàn bộ ma trận phân quyền (chỉ CEO/Quản trị) để dựng bảng điều chỉnh."""
    vts = db.query(VaiTro).order_by(VaiTro.id).all()
    mt: dict[int, dict[str, str]] = {}
    for pq in db.query(PhanQuyen).all():
        mt.setdefault(pq.vai_tro_id, {})[pq.module] = pq.muc
    return {
        "vai_tro": [{"ma": v.ma, "ten": v.ten} for v in vts],
        "ma_tran": {v.ma: mt.get(v.id, {}) for v in vts},
    }


@router.post("/phan-quyen")
def dat_quyen(
    p: DatQuyen,
    nd: NguoiDung = Depends(yeu_cau(MODULE, "QUAN_TRI")),
    db: Session = Depends(get_db),
):
    """CEO đặt mức quyền của 1 vị trí cho 1 module (KHONG = thu hồi truy cập)."""
    if nd.vai_tro.ma != "CEO":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ CEO được phân quyền.")
    if p.muc not in MUC_HOP_LE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mức quyền không hợp lệ.")
    vt = db.query(VaiTro).filter_by(ma=p.vai_tro).first()
    if not vt:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy vị trí.")
    # Chống tự khóa: CEO phải giữ Quản trị ở 'dieu_hanh' để không mất bảng phân quyền
    if vt.ma == "CEO" and p.module == "dieu_hanh" and p.muc != "QUAN_TRI":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "CEO phải giữ 'Quản trị' ở Overall Operation (tránh tự khóa bảng phân quyền).")
    pq = db.query(PhanQuyen).filter_by(vai_tro_id=vt.id, module=p.module).first()
    if p.muc == "KHONG":
        if pq:
            db.delete(pq)
    else:
        if pq:
            pq.muc = p.muc
        else:
            db.add(PhanQuyen(vai_tro_id=vt.id, module=p.module, muc=p.muc))
    ghi_audit(db, nd.id, "SUA", "phan_quyen", vt.id,
              moi={"vai_tro": vt.ma, "module": p.module, "muc": p.muc})
    db.commit()
    return {"vai_tro": vt.ma, "module": p.module, "muc": p.muc}
