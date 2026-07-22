"""DỊCH VỤ KỸ THUẬT — sổ quản lý dịch vụ kỹ thuật của SVWS.
Các loại: Site survey · CIP · Cleaning · Membrane/Material replacement · System audit.
Mỗi phiếu lưu dữ liệu kỹ thuật theo loại (JSON) + báo cáo, theo dõi trạng thái & giá trị."""
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..rbac import yeu_cau
from ..audit import ghi_audit
from ..models import NguoiDung, DichVuKT, KhachHang, DuAn
from ..schemas import DichVuKTVao, DichVuKTTrangThai

router = APIRouter(prefix="/dich-vu-kt", tags=["dich_vu_kt"])
MODULE = "dich_vu_kt"

TRANG_THAI = {"KHAO_SAT", "BAO_GIA", "DA_DUYET", "DANG_THUC_HIEN", "HOAN_THANH", "HUY"}
LOAI = {"SITE_SURVEY", "CIP", "CLEANING", "MEMBRANE", "MATERIAL", "AUDIT",
        "OPERATION", "GAS", "CONSULT"}
PREFIX = {"SITE_SURVEY": "SS", "CIP": "CIP", "CLEANING": "CL",
          "MEMBRANE": "MB", "MATERIAL": "MT", "AUDIT": "AD",
          "OPERATION": "VH", "GAS": "KT", "CONSULT": "TV"}


def _f(x):
    return float(x) if x is not None else 0


def _dict(db: Session, d: DichVuKT) -> dict:
    kh = db.get(KhachHang, d.khach_hang_id) if d.khach_hang_id else None
    da = db.get(DuAn, d.du_an_id) if d.du_an_id else None
    return {
        "id": d.id, "ma": d.ma or f"DVKT-{d.id}", "loai_dv": d.loai_dv,
        "chi_tiet_dv": d.chi_tiet_dv, "ten": d.ten,
        "khach_hang_id": d.khach_hang_id, "ten_khach_hang": kh.ten if kh else None,
        "du_an_id": d.du_an_id, "ten_du_an": (da.ten if da else None),
        "khach_ten": d.khach_ten, "cong_ty": d.cong_ty,
        "dien_thoai": d.dien_thoai, "email": d.email,
        "dia_diem": d.dia_diem, "thiet_bi": d.thiet_bi,
        "nguoi_phu_trach": d.nguoi_phu_trach,
        "ngay_hen": str(d.ngay_hen) if d.ngay_hen else None,
        "ngay_bat_dau": str(d.ngay_bat_dau) if d.ngay_bat_dau else None,
        "ngay_ket_thuc": str(d.ngay_ket_thuc) if d.ngay_ket_thuc else None,
        "gia_tri": _f(d.gia_tri), "trang_thai": d.trang_thai,
        "du_lieu_ky_thuat": d.du_lieu_ky_thuat or {},
        "bao_cao": d.bao_cao, "ghi_chu": d.ghi_chu,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.get("")
def ds_dich_vu(loai: str | None = None, trang_thai: str | None = None,
               db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    q = db.query(DichVuKT)
    if loai:
        q = q.filter(DichVuKT.loai_dv == loai)
    if trang_thai:
        q = q.filter(DichVuKT.trang_thai == trang_thai)
    return [_dict(db, d) for d in q.order_by(DichVuKT.id.desc()).all()]


@router.post("", status_code=201)
def tao_dich_vu(data: DichVuKTVao, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if data.loai_dv not in LOAI:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Loại dịch vụ không hợp lệ")
    tt = data.trang_thai if data.trang_thai in TRANG_THAI else "KHAO_SAT"
    d = DichVuKT(
        loai_dv=data.loai_dv, chi_tiet_dv=data.chi_tiet_dv, ten=data.ten,
        khach_hang_id=data.khach_hang_id, du_an_id=data.du_an_id,
        khach_ten=data.khach_ten, cong_ty=data.cong_ty,
        dien_thoai=data.dien_thoai, email=data.email,
        dia_diem=data.dia_diem, thiet_bi=data.thiet_bi,
        nguoi_phu_trach=data.nguoi_phu_trach, ngay_hen=data.ngay_hen,
        ngay_bat_dau=data.ngay_bat_dau, ngay_ket_thuc=data.ngay_ket_thuc,
        gia_tri=Decimal(data.gia_tri or 0), trang_thai=tt,
        du_lieu_ky_thuat=data.du_lieu_ky_thuat, bao_cao=data.bao_cao, ghi_chu=data.ghi_chu)
    db.add(d)
    db.flush()
    d.ma = f"{PREFIX.get(data.loai_dv, 'DV')}-{date.today():%Y%m%d}-{d.id}"
    ghi_audit(db, nd.id, "TAO", "dich_vu_kt", d.id, moi={"ma": d.ma, "loai_dv": d.loai_dv})
    db.commit()
    return _dict(db, d)


@router.put("/{dv_id}")
def sua_dich_vu(dv_id: int, data: DichVuKTVao, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    d = db.get(DichVuKT, dv_id)
    if not d:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dịch vụ")
    if data.loai_dv not in LOAI:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Loại dịch vụ không hợp lệ")
    d.loai_dv = data.loai_dv
    d.chi_tiet_dv = data.chi_tiet_dv
    d.ten = data.ten
    d.khach_hang_id = data.khach_hang_id
    d.du_an_id = data.du_an_id
    d.khach_ten = data.khach_ten
    d.cong_ty = data.cong_ty
    d.dien_thoai = data.dien_thoai
    d.email = data.email
    d.dia_diem = data.dia_diem
    d.thiet_bi = data.thiet_bi
    d.nguoi_phu_trach = data.nguoi_phu_trach
    d.ngay_hen = data.ngay_hen
    d.ngay_bat_dau = data.ngay_bat_dau
    d.ngay_ket_thuc = data.ngay_ket_thuc
    d.gia_tri = Decimal(data.gia_tri or 0)
    if data.trang_thai in TRANG_THAI:
        d.trang_thai = data.trang_thai
    d.du_lieu_ky_thuat = data.du_lieu_ky_thuat
    d.bao_cao = data.bao_cao
    d.ghi_chu = data.ghi_chu
    ghi_audit(db, nd.id, "SUA", "dich_vu_kt", d.id)
    db.commit()
    return _dict(db, d)


@router.post("/{dv_id}/trang-thai")
def doi_trang_thai(dv_id: int, data: DichVuKTTrangThai, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    d = db.get(DichVuKT, dv_id)
    if not d:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dịch vụ")
    if data.trang_thai not in TRANG_THAI:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Trạng thái không hợp lệ")
    d.trang_thai = data.trang_thai
    ghi_audit(db, nd.id, "SUA", "dich_vu_kt", d.id, moi={"trang_thai": data.trang_thai})
    db.commit()
    return _dict(db, d)


@router.delete("/{dv_id}")
def xoa_dich_vu(dv_id: int, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "DUYET"))):
    d = db.get(DichVuKT, dv_id)
    if not d:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dịch vụ")
    ma = d.ma
    ghi_audit(db, nd.id, "XOA", "dich_vu_kt", d.id, moi={"ma": ma})
    db.delete(d)
    db.commit()
    return {"da_xoa": True, "ma": ma}
