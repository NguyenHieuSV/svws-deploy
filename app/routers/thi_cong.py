"""
Module THI CÔNG — quản lý THIẾT BỊ / dụng cụ thi công (sổ cá thể) và việc cấp phát
ra công trường, thu hồi về kho theo dự án (mig 165).

Dùng lại phân quyền MODULE "du_an" (không thêm vai trò mới):
  • XEM: xem sổ thiết bị + lịch sử cấp phát.
  • THAO_TAC: thêm/sửa thiết bị, cấp phát.
  • DUYET (hoặc CEO/ADMIN): xóa thiết bị, thu hồi.
Người nhận tại công trường là NHÂN VIÊN CÓ TÀI KHOẢN (nguoi_nhan_id → nhan_vien).
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..rbac import yeu_cau
from ..audit import ghi_audit
from ..deps import nhan_vien_id_cua
from ..models import NguoiDung, NhanVien, DuAn, ThietBiThiCong, CapPhatThietBi

router = APIRouter(prefix="/thi-cong", tags=["thi_cong"])
MODULE = "du_an"

TINH_TRANG = {"SAN_SANG", "DANG_CAP_PHAT", "BAO_TRI", "HONG", "THANH_LY"}


class ThietBiVao(BaseModel):
    ma: str | None = None
    ten: str | None = None   # bắt buộc khi TẠO (kiểm ở endpoint); PUT cho sửa từng phần
    loai: str | None = "MAY_MOC"
    model: str | None = None
    serial: str | None = None
    nguyen_gia: float | None = 0
    ngay_mua: date | None = None
    tinh_trang: str | None = None
    ghi_chu: str | None = None


class CapPhatVao(BaseModel):
    du_an_id: int
    nguoi_nhan_id: int
    tinh_trang_cap: str | None = None
    ngay_cap: date | None = None
    ghi_chu: str | None = None


class ThuHoiVao(BaseModel):
    tinh_trang_tra: str | None = None
    ngay_tra: date | None = None
    ve_bao_tri: bool = False   # True → thiết bị về trạng thái BAO_TRI thay vì SAN_SANG
    ghi_chu: str | None = None


def _ten_nv(db: Session, nv_id):
    if not nv_id:
        return None
    nv = db.get(NhanVien, nv_id)
    return nv.ho_ten if nv else None


def _tb_ra(db: Session, t: ThietBiThiCong) -> dict:
    da = db.get(DuAn, t.du_an_hien_tai_id) if t.du_an_hien_tai_id else None
    return {
        "id": t.id, "ma": t.ma, "ten": t.ten, "loai": t.loai, "model": t.model,
        "serial": t.serial, "nguyen_gia": float(t.nguyen_gia or 0),
        "ngay_mua": str(t.ngay_mua) if t.ngay_mua else None, "tinh_trang": t.tinh_trang,
        "du_an_hien_tai_id": t.du_an_hien_tai_id,
        "du_an_hien_tai": (da.ma or da.ten) if da else None,
        "ghi_chu": t.ghi_chu,
    }


def _cp_ra(db: Session, c: CapPhatThietBi) -> dict:
    da = db.get(DuAn, c.du_an_id) if c.du_an_id else None
    return {
        "id": c.id, "thiet_bi_id": c.thiet_bi_id, "du_an_id": c.du_an_id,
        "du_an": (da.ma or da.ten) if da else None,
        "nguoi_nhan_id": c.nguoi_nhan_id, "nguoi_nhan": _ten_nv(db, c.nguoi_nhan_id),
        "ngay_cap": str(c.ngay_cap) if c.ngay_cap else None,
        "tinh_trang_cap": c.tinh_trang_cap,
        "ngay_tra": str(c.ngay_tra) if c.ngay_tra else None,
        "tinh_trang_tra": c.tinh_trang_tra,
        "nguoi_duyet": _ten_nv(db, c.nguoi_duyet_id),
        "dang_giu": c.ngay_tra is None, "ghi_chu": c.ghi_chu,
    }


# ---------------- Sổ thiết bị ----------------
@router.get("/thiet-bi")
def ds_thiet_bi(du_an_id: int | None = None, tinh_trang: str | None = None,
                db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    q = db.query(ThietBiThiCong)
    if du_an_id is not None:
        q = q.filter(ThietBiThiCong.du_an_hien_tai_id == du_an_id)
    if tinh_trang:
        q = q.filter(ThietBiThiCong.tinh_trang == tinh_trang)
    rows = q.order_by(ThietBiThiCong.id.desc()).all()
    theo_tt = {}
    for t in db.query(ThietBiThiCong.tinh_trang, func.count(ThietBiThiCong.id)).group_by(ThietBiThiCong.tinh_trang).all():
        theo_tt[t[0]] = t[1]
    return {"tong": len(rows), "theo_tinh_trang": theo_tt,
            "danh_sach": [_tb_ra(db, t) for t in rows]}


@router.post("/thiet-bi", status_code=201)
def them_thiet_bi(data: ThietBiVao, db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if not (data.ten or "").strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Thiếu tên thiết bị")
    if data.ma:
        if db.query(ThietBiThiCong).filter(func.lower(ThietBiThiCong.ma) == data.ma.strip().lower()).first():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Mã thiết bị '{data.ma}' đã tồn tại")
    tt = (data.tinh_trang or "SAN_SANG").upper()
    t = ThietBiThiCong(
        ma=(data.ma or None), ten=data.ten, loai=(data.loai or "MAY_MOC"),
        model=data.model, serial=data.serial, nguyen_gia=data.nguyen_gia or 0,
        ngay_mua=data.ngay_mua, tinh_trang=tt if tt in TINH_TRANG else "SAN_SANG",
        ghi_chu=data.ghi_chu)
    db.add(t); db.flush()
    if not t.ma:
        t.ma = f"TB-{t.id:04d}"
    ghi_audit(db, nd.id, "TAO", "thiet_bi_thi_cong", t.id, moi={"ten": t.ten, "ma": t.ma})
    db.commit()
    return _tb_ra(db, t)


@router.put("/thiet-bi/{tb_id}")
def sua_thiet_bi(tb_id: int, data: ThietBiVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    t = db.get(ThietBiThiCong, tb_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thiết bị")
    if data.ma and data.ma.strip().lower() != (t.ma or "").lower():
        if db.query(ThietBiThiCong).filter(func.lower(ThietBiThiCong.ma) == data.ma.strip().lower()).first():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Mã thiết bị '{data.ma}' đã tồn tại")
    for k in ("ma", "ten", "loai", "model", "serial", "nguyen_gia", "ngay_mua", "ghi_chu"):
        v = getattr(data, k)
        if v is not None:
            setattr(t, k, v)
    if data.tinh_trang:
        tt = data.tinh_trang.upper()
        # Không cho đổi tay sang/khỏi DANG_CAP_PHAT — trạng thái này do cấp phát/thu hồi quản.
        if tt in TINH_TRANG and tt != "DANG_CAP_PHAT" and t.tinh_trang != "DANG_CAP_PHAT":
            t.tinh_trang = tt
    ghi_audit(db, nd.id, "SUA", "thiet_bi_thi_cong", t.id, moi={"ten": t.ten})
    db.commit()
    return _tb_ra(db, t)


@router.delete("/thiet-bi/{tb_id}")
def xoa_thiet_bi(tb_id: int, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "DUYET"))):
    t = db.get(ThietBiThiCong, tb_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thiết bị")
    if t.tinh_trang == "DANG_CAP_PHAT":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Thiết bị đang ở công trường — thu hồi trước khi xóa")
    ghi_audit(db, nd.id, "XOA", "thiet_bi_thi_cong", tb_id, cu={"ten": t.ten, "ma": t.ma})
    db.delete(t)
    db.commit()
    return {"ok": True}


# ---------------- Cấp phát / Thu hồi ----------------
@router.get("/thiet-bi/{tb_id}/lich-su")
def lich_su_cap_phat(tb_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    rows = (db.query(CapPhatThietBi).filter_by(thiet_bi_id=tb_id)
            .order_by(CapPhatThietBi.id.desc()).all())
    return [_cp_ra(db, c) for c in rows]


@router.post("/thiet-bi/{tb_id}/cap-phat", status_code=201)
def cap_phat(tb_id: int, data: CapPhatVao, db: Session = Depends(get_db),
             nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    t = db.get(ThietBiThiCong, tb_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thiết bị")
    if t.tinh_trang == "DANG_CAP_PHAT":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Thiết bị đang được cấp phát — thu hồi trước đã")
    if t.tinh_trang in ("HONG", "THANH_LY"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Thiết bị đang '{t.tinh_trang}' — không cấp phát được")
    if db.get(DuAn, data.du_an_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án")
    if db.get(NhanVien, data.nguoi_nhan_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy nhân viên nhận")
    c = CapPhatThietBi(
        thiet_bi_id=tb_id, du_an_id=data.du_an_id, nguoi_nhan_id=data.nguoi_nhan_id,
        ngay_cap=data.ngay_cap or date.today(), tinh_trang_cap=data.tinh_trang_cap,
        nguoi_duyet_id=nhan_vien_id_cua(db, nd.id), ghi_chu=data.ghi_chu)
    db.add(c)
    t.tinh_trang = "DANG_CAP_PHAT"
    t.du_an_hien_tai_id = data.du_an_id
    db.flush()
    ghi_audit(db, nd.id, "CAP_PHAT", "thiet_bi_thi_cong", tb_id,
              moi={"du_an_id": data.du_an_id, "nguoi_nhan_id": data.nguoi_nhan_id})
    db.commit()
    return _cp_ra(db, c)


@router.post("/cap-phat/{cp_id}/thu-hoi")
def thu_hoi(cp_id: int, data: ThuHoiVao, db: Session = Depends(get_db),
            nd: NguoiDung = Depends(yeu_cau(MODULE, "DUYET"))):
    c = db.get(CapPhatThietBi, cp_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiếu cấp phát")
    if c.ngay_tra is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Phiếu này đã thu hồi rồi")
    c.ngay_tra = data.ngay_tra or date.today()
    c.tinh_trang_tra = data.tinh_trang_tra
    if data.ghi_chu:
        c.ghi_chu = (c.ghi_chu + " · " if c.ghi_chu else "") + data.ghi_chu
    t = db.get(ThietBiThiCong, c.thiet_bi_id)
    if t is not None:
        t.tinh_trang = "BAO_TRI" if data.ve_bao_tri else "SAN_SANG"
        t.du_an_hien_tai_id = None
    ghi_audit(db, nd.id, "THU_HOI", "thiet_bi_thi_cong", c.thiet_bi_id,
              moi={"cap_phat_id": cp_id, "ve_bao_tri": data.ve_bao_tri})
    db.commit()
    return _cp_ra(db, c)


@router.get("/du-an/{da_id}/thiet-bi")
def thiet_bi_cua_du_an(da_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Thiết bị ĐANG ở công trường của dự án + lịch sử cấp phát của dự án."""
    dang = (db.query(ThietBiThiCong)
            .filter(ThietBiThiCong.du_an_hien_tai_id == da_id,
                    ThietBiThiCong.tinh_trang == "DANG_CAP_PHAT")
            .order_by(ThietBiThiCong.ten).all())
    lich_su = (db.query(CapPhatThietBi).filter_by(du_an_id=da_id)
               .order_by(CapPhatThietBi.id.desc()).all())
    return {"dang_o_cong_truong": [_tb_ra(db, t) for t in dang],
            "lich_su": [_cp_ra(db, c) for c in lich_su]}
