"""
Cho thuê — vận hành: quản lý tài sản, chi phí vận hành (gắn đề xuất mua qua mã bán hàng),
kế hoạch bảo trì, báo cáo vận hành, vật tư/thiết bị. Module RBAC 'cho_thue'.
"""
from decimal import Decimal
from datetime import date, timedelta
import os, uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..config import settings
from ..rbac import yeu_cau
from ..deps import nhan_vien_id_cua
from ..audit import ghi_audit
from ..models import (NguoiDung, KhachHang, YeuCauMua, HangHoa, HoaDon,
                      TaiSanChoThue, ChiPhiVanHanh, KeHoachBaoTri,
                      DinhMucTieuHao, TieuHaoThucTe, TepDinhKem)

router = APIRouter(prefix="/cho-thue", tags=["cho_thue_ops"])
MODULE = "cho_thue"
TINH_TRANG = {"SAN_SANG", "DANG_THUE", "BAO_TRI", "HONG", "THANH_LY"}


def _ten_kh(db, kid):
    if not kid:
        return None
    kh = db.get(KhachHang, kid)
    return kh.ten if kh else None


def _ts_ra(db, t: TaiSanChoThue) -> dict:
    return {"id": t.id, "ma": t.ma, "ten_du_an": t.ten_du_an or t.ma, "ten": t.ten, "loai": t.loai,
            "nguyen_gia": float(t.nguyen_gia or 0), "gia_thue_thang": float(t.gia_thue_thang or 0),
            "khau_hao_thang": float(t.khau_hao_thang or 0),
            "ngay_mua": str(t.ngay_mua) if t.ngay_mua else None,
            "tinh_trang": t.tinh_trang, "khach_hang_id": t.khach_hang_id,
            "khach_hang": _ten_kh(db, t.khach_hang_id), "vi_tri": t.vi_tri, "ghi_chu": t.ghi_chu}


# ===================== TÀI SẢN CHO THUÊ =====================
class TaiSanVaoCT(BaseModel):
    ma: str
    ten_du_an: str | None = None
    ten: str
    loai: str = Field(default="THIET_BI", pattern="^(THIET_BI|HE_THONG|XE|KHAC)$")
    nguyen_gia: Decimal = 0
    gia_thue_thang: Decimal = 0
    khau_hao_thang: Decimal = 0
    ngay_mua: date | None = None
    vi_tri: str | None = None
    ghi_chu: str | None = None


class TaiSanSuaCT(BaseModel):
    ten_du_an: str | None = None
    ten: str | None = None
    loai: str | None = None
    nguyen_gia: Decimal | None = None
    gia_thue_thang: Decimal | None = None
    khau_hao_thang: Decimal | None = None
    tinh_trang: str | None = None
    khach_hang_id: int | None = None
    vi_tri: str | None = None
    ghi_chu: str | None = None
    bo_khach: bool = False


@router.get("/tai-san")
def ds_tai_san(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return [_ts_ra(db, t) for t in db.query(TaiSanChoThue).order_by(TaiSanChoThue.id).all()]


@router.post("/tai-san", status_code=201)
def them_tai_san(data: TaiSanVaoCT, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.query(TaiSanChoThue).filter_by(ma=data.ma).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mã tài sản đã tồn tại")
    d = data.model_dump()
    if not d.get("ten_du_an"):
        d["ten_du_an"] = d["ma"]
    t = TaiSanChoThue(**d)
    db.add(t); db.flush()
    ghi_audit(db, nd.id, "TAO", "tai_san_cho_thue", t.id, moi={"ma": data.ma})
    db.commit()
    return _ts_ra(db, t)


@router.put("/tai-san/{ts_id}")
def sua_tai_san(ts_id: int, data: TaiSanSuaCT, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    t = db.get(TaiSanChoThue, ts_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài sản")
    if data.tinh_trang is not None and data.tinh_trang not in TINH_TRANG:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tình trạng không hợp lệ")
    for f in ("ten_du_an", "ten", "loai", "nguyen_gia", "gia_thue_thang", "khau_hao_thang",
              "tinh_trang", "vi_tri", "ghi_chu"):
        v = getattr(data, f)
        if v is not None:
            setattr(t, f, v)
    if data.bo_khach:
        t.khach_hang_id = None
    elif data.khach_hang_id is not None:
        t.khach_hang_id = data.khach_hang_id
    ghi_audit(db, nd.id, "SUA", "tai_san_cho_thue", t.id)
    db.commit()
    return _ts_ra(db, t)


@router.get("/tai-san/{ts_id}")
def chi_tiet_tai_san(ts_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    t = db.get(TaiSanChoThue, ts_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài sản")
    cps = db.query(ChiPhiVanHanh).filter_by(tai_san_id=ts_id).order_by(ChiPhiVanHanh.ngay.desc()).all()
    bts = db.query(KeHoachBaoTri).filter_by(tai_san_id=ts_id).order_by(KeHoachBaoTri.ngay_ke_tiep).all()
    tong_cp = sum(float(c.so_tien or 0) for c in cps)
    return {"tai_san": _ts_ra(db, t), "tong_chi_phi": tong_cp,
            "chi_phi": [{"id": c.id, "ngay": str(c.ngay), "loai_chi_phi": c.loai_chi_phi,
                         "so_tien": float(c.so_tien or 0), "mo_ta": c.mo_ta, "nguon": c.nguon}
                        for c in cps],
            "bao_tri": [{"id": b.id, "ten_cong_viec": b.ten_cong_viec, "chu_ky_ngay": b.chu_ky_ngay,
                         "ngay_ke_tiep": str(b.ngay_ke_tiep) if b.ngay_ke_tiep else None,
                         "trang_thai": b.trang_thai} for b in bts]}


# ===================== CHI PHÍ VẬN HÀNH =====================
class ChiPhiVao(BaseModel):
    tai_san_id: int | None = None
    ma_ban_hang: str | None = None
    loai_chi_phi: str = Field(default="VAT_TU", pattern="^(VAT_TU|SUA_CHUA|NHAN_CONG|KHAC)$")
    so_tien: Decimal = Field(gt=0)
    ngay: date | None = None
    mo_ta: str | None = None


@router.get("/chi-phi")
def ds_chi_phi(tai_san_id: int | None = None, db: Session = Depends(get_db),
               _=Depends(yeu_cau(MODULE, "XEM"))):
    q = db.query(ChiPhiVanHanh)
    if tai_san_id:
        q = q.filter_by(tai_san_id=tai_san_id)
    rows = q.order_by(ChiPhiVanHanh.ngay.desc(), ChiPhiVanHanh.id.desc()).all()
    out = []
    for c in rows:
        ts = db.get(TaiSanChoThue, c.tai_san_id) if c.tai_san_id else None
        out.append({"id": c.id, "tai_san": ts.ten if ts else None, "ma_ban_hang": c.ma_ban_hang,
                    "loai_chi_phi": c.loai_chi_phi, "so_tien": float(c.so_tien or 0),
                    "ngay": str(c.ngay), "mo_ta": c.mo_ta, "nguon": c.nguon})
    return {"tong": sum(o["so_tien"] for o in out), "danh_sach": out}


@router.post("/chi-phi", status_code=201)
def them_chi_phi(data: ChiPhiVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    ma = data.ma_ban_hang
    if data.tai_san_id and not ma:
        ts = db.get(TaiSanChoThue, data.tai_san_id)
        ma = ts.ma if ts else None
    c = ChiPhiVanHanh(tai_san_id=data.tai_san_id, ma_ban_hang=ma, loai_chi_phi=data.loai_chi_phi,
                      so_tien=data.so_tien, ngay=data.ngay or date.today(), mo_ta=data.mo_ta,
                      nguon="THU_CONG")
    db.add(c); db.flush()
    ghi_audit(db, nd.id, "TAO", "chi_phi_van_hanh", c.id, moi={"so_tien": float(data.so_tien)})
    db.commit()
    return {"id": c.id}


@router.post("/dong-bo-chi-phi")
def dong_bo_chi_phi(db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Sinh chi phí vận hành từ các đề xuất mua đã gắn mã cho thuê (chưa đồng bộ)."""
    da_co = {c.yeu_cau_mua_id for c in db.query(ChiPhiVanHanh)
             .filter(ChiPhiVanHanh.yeu_cau_mua_id.isnot(None)).all()}
    ycs = db.query(YeuCauMua).filter(YeuCauMua.cho_thue_ma.isnot(None)).all()
    ts_theo_ma = {}
    for t in db.query(TaiSanChoThue).all():
        ts_theo_ma[t.ten_du_an or t.ma] = t
        ts_theo_ma[t.ma] = t
    them = 0
    tong = Decimal(0)
    for yc in ycs:
        if yc.id in da_co:
            continue
        hh = db.get(HangHoa, yc.hang_hoa_id)
        don_gia = yc.don_gia if yc.don_gia is not None else (hh.gia_ban if hh else Decimal(0))
        so_tien = (yc.so_luong or Decimal(0)) * (don_gia or Decimal(0))
        code = yc.cho_thue_ma or ""
        prefix = code[:-4] if len(code) > 4 else code
        ts = ts_theo_ma.get(prefix) or ts_theo_ma.get(code)
        ngay = yc.ngay or date.today()
        suf = code[-4:]
        if suf.isdigit() and len(suf) == 4:
            mm, yy = int(suf[:2]), 2000 + int(suf[2:])
            if 1 <= mm <= 12:
                ngay = date(yy, mm, 1)
        db.add(ChiPhiVanHanh(tai_san_id=ts.id if ts else None, ma_ban_hang=code,
                             loai_chi_phi="VAT_TU", so_tien=so_tien, ngay=ngay,
                             yeu_cau_mua_id=yc.id, nguon="DE_XUAT_MUA",
                             mo_ta=f"Mua {hh.ten if hh else 'vật tư'} ×{float(yc.so_luong or 0):g}"))
        them += 1
        tong += so_tien
    ghi_audit(db, nd.id, "TAO", "chi_phi_van_hanh", None, moi={"dong_bo": them})
    db.commit()
    return {"so_chi_phi_them": them, "tong_tien": float(tong)}


# ===================== VẬT TƯ & THIẾT BỊ (đề xuất mua gắn mã cho thuê) =====================
class DeXuatMuaCT(BaseModel):
    hang_hoa_id: int
    so_luong: Decimal = Field(gt=0)
    don_gia: Decimal | None = None
    cho_thue_ma: str
    ly_do: str | None = None


@router.get("/de-xuat-mua")
def ds_de_xuat(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    yc_id_da_dong_bo = {c.yeu_cau_mua_id for c in db.query(ChiPhiVanHanh)
                        .filter(ChiPhiVanHanh.yeu_cau_mua_id.isnot(None)).all()}
    rows = db.query(YeuCauMua).filter(YeuCauMua.cho_thue_ma.isnot(None)) \
             .order_by(YeuCauMua.id.desc()).all()
    out = []
    for yc in rows:
        hh = db.get(HangHoa, yc.hang_hoa_id)
        dg = yc.don_gia if yc.don_gia is not None else (hh.gia_ban if hh else 0)
        out.append({"id": yc.id, "hang_hoa": hh.ten if hh else None, "ma_hh": hh.ma if hh else None,
                    "loai": hh.loai if hh else None,
                    "so_luong": float(yc.so_luong or 0), "don_gia": float(dg or 0),
                    "thanh_tien": float((yc.so_luong or 0) * (dg or 0)),
                    "cho_thue_ma": yc.cho_thue_ma, "trang_thai": yc.trang_thai,
                    "ngay": str(yc.ngay) if yc.ngay else None,
                    "da_dong_bo": yc.id in yc_id_da_dong_bo, "ly_do": yc.ly_do})
    return out


@router.post("/de-xuat-mua", status_code=201)
def tao_de_xuat(data: DeXuatMuaCT, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.get(HangHoa, data.hang_hoa_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hàng hóa")
    yc = YeuCauMua(hang_hoa_id=data.hang_hoa_id, so_luong=data.so_luong, don_gia=data.don_gia,
                   cho_thue_ma=data.cho_thue_ma, ly_do=data.ly_do or "Vật tư/thiết bị cho thuê",
                   trang_thai="MOI", nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(yc); db.flush()
    ghi_audit(db, nd.id, "TAO", "yeu_cau_mua", yc.id, moi={"cho_thue_ma": data.cho_thue_ma})
    db.commit()
    return {"id": yc.id, "trang_thai": yc.trang_thai}


# ===================== KẾ HOẠCH BẢO TRÌ =====================
class BaoTriVao(BaseModel):
    tai_san_id: int
    ten_cong_viec: str
    chu_ky_ngay: int = 90
    ngay_ke_tiep: date | None = None
    chi_phi_du_kien: Decimal = 0
    ghi_chu: str | None = None


def _bt_ra(db, b: KeHoachBaoTri) -> dict:
    ts = db.get(TaiSanChoThue, b.tai_san_id)
    qh = bool(b.ngay_ke_tiep and b.ngay_ke_tiep < date.today())
    return {"id": b.id, "tai_san_id": b.tai_san_id, "tai_san": ts.ten if ts else None,
            "ma": ts.ma if ts else None, "ten_cong_viec": b.ten_cong_viec,
            "chu_ky_ngay": b.chu_ky_ngay,
            "ngay_ke_tiep": str(b.ngay_ke_tiep) if b.ngay_ke_tiep else None,
            "lan_cuoi": str(b.lan_cuoi) if b.lan_cuoi else None,
            "trang_thai": b.trang_thai, "qua_han": qh,
            "chi_phi_du_kien": float(b.chi_phi_du_kien or 0), "ghi_chu": b.ghi_chu}


@router.get("/bao-tri")
def ds_bao_tri(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return [_bt_ra(db, b) for b in db.query(KeHoachBaoTri).order_by(KeHoachBaoTri.ngay_ke_tiep).all()]


@router.get("/bao-tri/den-han")
def bao_tri_den_han(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    moc = date.today() + timedelta(days=7)
    rows = db.query(KeHoachBaoTri).filter(KeHoachBaoTri.ngay_ke_tiep <= moc).order_by(KeHoachBaoTri.ngay_ke_tiep).all()
    return [_bt_ra(db, b) for b in rows]


@router.post("/bao-tri", status_code=201)
def them_bao_tri(data: BaoTriVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.get(TaiSanChoThue, data.tai_san_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài sản")
    b = KeHoachBaoTri(tai_san_id=data.tai_san_id, ten_cong_viec=data.ten_cong_viec,
                      chu_ky_ngay=data.chu_ky_ngay,
                      ngay_ke_tiep=data.ngay_ke_tiep or (date.today() + timedelta(days=data.chu_ky_ngay)),
                      chi_phi_du_kien=data.chi_phi_du_kien, ghi_chu=data.ghi_chu, trang_thai="KE_HOACH")
    db.add(b); db.flush()
    ghi_audit(db, nd.id, "TAO", "ke_hoach_bao_tri", b.id)
    db.commit()
    return _bt_ra(db, b)


@router.post("/bao-tri/{bt_id}/hoan-thanh")
def hoan_thanh_bao_tri(bt_id: int, db: Session = Depends(get_db),
                       nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    b = db.get(KeHoachBaoTri, bt_id)
    if b is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy kế hoạch bảo trì")
    b.lan_cuoi = date.today()
    b.ngay_ke_tiep = date.today() + timedelta(days=b.chu_ky_ngay or 90)
    b.trang_thai = "KE_HOACH"
    # ghi chi phí bảo trì nếu có dự kiến
    if b.chi_phi_du_kien and float(b.chi_phi_du_kien) > 0:
        ts = db.get(TaiSanChoThue, b.tai_san_id)
        db.add(ChiPhiVanHanh(tai_san_id=b.tai_san_id, ma_ban_hang=ts.ma if ts else None,
                             loai_chi_phi="SUA_CHUA", so_tien=b.chi_phi_du_kien, ngay=date.today(),
                             nguon="BAO_TRI", mo_ta=f"Bảo trì: {b.ten_cong_viec}"))
    ghi_audit(db, nd.id, "SUA", "ke_hoach_bao_tri", b.id, moi={"hoan_thanh": True})
    db.commit()
    return _bt_ra(db, b)


# ===================== BÁO CÁO VẬN HÀNH =====================
@router.get("/bao-cao-van-hanh")
def bao_cao_van_hanh(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    ts = db.query(TaiSanChoThue).all()
    theo_tt: dict[str, int] = {}
    nguyen_gia = Decimal(0)
    dt_thang = Decimal(0)
    for t in ts:
        theo_tt[t.tinh_trang] = theo_tt.get(t.tinh_trang, 0) + 1
        nguyen_gia += t.nguyen_gia or 0
        if t.tinh_trang == "DANG_THUE":
            dt_thang += t.gia_thue_thang or 0
    so = len(ts)
    dang_thue = theo_tt.get("DANG_THUE", 0)
    chi_phi = db.query(func.coalesce(func.sum(ChiPhiVanHanh.so_tien), 0)).scalar() or Decimal(0)
    dt_hoa_don = db.query(func.coalesce(func.sum(HoaDon.tong_tien), 0)) \
                   .filter(HoaDon.loai == "THUE").scalar() or Decimal(0)
    bt_den_han = db.query(func.count(KeHoachBaoTri.id)) \
                   .filter(KeHoachBaoTri.ngay_ke_tiep <= date.today() + timedelta(days=7)).scalar() or 0
    return {
        "so_tai_san": so, "theo_tinh_trang": theo_tt,
        "ty_le_su_dung": round(dang_thue / so * 100, 1) if so else 0,
        "nguyen_gia_tong": float(nguyen_gia),
        "doanh_thu_thang_dk": float(dt_thang),
        "doanh_thu_hd_thue": float(dt_hoa_don),
        "chi_phi_van_hanh": float(chi_phi),
        "loi_nhuan_uoc": float(dt_thang - chi_phi),
        "bao_tri_den_han": int(bt_den_han),
    }


# ===================== ĐỊNH MỨC & TIÊU HAO THEO HỆ THỐNG/THÁNG =====================
def _hh_info(db, hid):
    h = db.get(HangHoa, hid)
    if h is None:
        return {"ma": None, "ten": "?", "don_vi": None, "gia_ban": 0.0}
    return {"ma": h.ma, "ten": h.ten, "don_vi": h.don_vi, "gia_ban": float(h.gia_ban or 0)}


class DinhMucVao(BaseModel):
    tai_san_id: int
    hang_hoa_id: int
    dinh_muc_thang: Decimal = Field(ge=0)
    ghi_chu: str | None = None


@router.get("/dinh-muc")
def ds_dinh_muc(tai_san_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    rows = db.query(DinhMucTieuHao).filter_by(tai_san_id=tai_san_id).all()
    out = []
    for d in rows:
        hh = _hh_info(db, d.hang_hoa_id)
        out.append({"id": d.id, "hang_hoa_id": d.hang_hoa_id, "ma_hh": hh["ma"], "ten": hh["ten"],
                    "don_vi": hh["don_vi"], "gia_ban": hh["gia_ban"],
                    "dinh_muc_thang": float(d.dinh_muc_thang or 0),
                    "chi_phi_dinh_muc": float(d.dinh_muc_thang or 0) * hh["gia_ban"], "ghi_chu": d.ghi_chu})
    return out


@router.post("/dinh-muc", status_code=201)
def luu_dinh_muc(data: DinhMucVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.get(TaiSanChoThue, data.tai_san_id) is None or db.get(HangHoa, data.hang_hoa_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài sản hoặc hàng hóa")
    d = db.query(DinhMucTieuHao).filter_by(tai_san_id=data.tai_san_id, hang_hoa_id=data.hang_hoa_id).first()
    if d is None:
        d = DinhMucTieuHao(tai_san_id=data.tai_san_id, hang_hoa_id=data.hang_hoa_id)
        db.add(d)
    d.dinh_muc_thang = data.dinh_muc_thang
    d.ghi_chu = data.ghi_chu
    db.flush()
    ghi_audit(db, nd.id, "LUU", "dinh_muc_tieu_hao", d.id)
    db.commit()
    return {"id": d.id}


@router.delete("/dinh-muc/{dm_id}")
def xoa_dinh_muc(dm_id: int, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    d = db.get(DinhMucTieuHao, dm_id)
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy định mức")
    db.delete(d)
    ghi_audit(db, nd.id, "XOA", "dinh_muc_tieu_hao", dm_id)
    db.commit()
    return {"id": dm_id, "trang_thai": "DA_XOA"}


class TieuHaoVao(BaseModel):
    tai_san_id: int
    thang: str
    chi_tiet: list[dict]  # [{hang_hoa_id, so_luong}]


@router.post("/tieu-hao", status_code=201)
def ghi_tieu_hao(data: TieuHaoVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.get(TaiSanChoThue, data.tai_san_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài sản")
    n = 0
    for ct in data.chi_tiet:
        hid = int(ct.get("hang_hoa_id"))
        sl = Decimal(str(ct.get("so_luong") or 0))
        hh = db.get(HangHoa, hid)
        if hh is None:
            continue
        th = db.query(TieuHaoThucTe).filter_by(tai_san_id=data.tai_san_id, hang_hoa_id=hid, thang=data.thang).first()
        if th is None:
            th = TieuHaoThucTe(tai_san_id=data.tai_san_id, hang_hoa_id=hid, thang=data.thang)
            db.add(th)
        th.so_luong = sl
        th.don_gia = hh.gia_ban or Decimal(0)
        n += 1
    ghi_audit(db, nd.id, "GHI", "tieu_hao_thuc_te", None, moi={"thang": data.thang, "so_dong": n})
    db.commit()
    return {"thang": data.thang, "so_dong": n}


@router.get("/bao-cao-tieu-hao")
def bao_cao_tieu_hao(tai_san_id: int, thang: str, db: Session = Depends(get_db),
                     _=Depends(yeu_cau(MODULE, "XEM"))):
    dms = {d.hang_hoa_id: d for d in db.query(DinhMucTieuHao).filter_by(tai_san_id=tai_san_id).all()}
    ths = {t.hang_hoa_id: t for t in db.query(TieuHaoThucTe)
           .filter_by(tai_san_id=tai_san_id, thang=thang).all()}
    hids = set(dms) | set(ths)
    rows = []
    t_dm = t_tt = t_cp_dm = t_cp_tt = 0.0
    for hid in hids:
        hh = _hh_info(db, hid)
        gia = hh["gia_ban"]
        dm = float(dms[hid].dinh_muc_thang) if hid in dms else 0.0
        th = ths.get(hid)
        tt = float(th.so_luong) if th else 0.0
        gia_tt = float(th.don_gia) if th and th.don_gia else gia
        chenh = round(tt - dm, 3)
        pct = round(tt / dm * 100, 1) if dm > 0 else (None if tt == 0 else 999)
        cp_dm = dm * gia
        cp_tt = tt * gia_tt
        t_dm += dm; t_tt += tt; t_cp_dm += cp_dm; t_cp_tt += cp_tt
        rows.append({"hang_hoa_id": hid, "ma_hh": hh["ma"], "ten": hh["ten"], "don_vi": hh["don_vi"],
                     "dinh_muc": dm, "thuc_te": tt, "chenh_lech": chenh, "pct": pct,
                     "don_gia": gia, "chi_phi_dinh_muc": cp_dm, "chi_phi_thuc_te": cp_tt,
                     "vuot_dinh_muc": chenh > 0,
                     "da_ghi_chi_phi": bool(th.da_ghi_chi_phi) if th else False})
    rows.sort(key=lambda r: (r["ten"] or ""))
    ts = db.get(TaiSanChoThue, tai_san_id)
    return {"tai_san_id": tai_san_id, "tai_san": ts.ten if ts else None, "ma": ts.ma if ts else None,
            "thang": thang, "chi_tiet": rows,
            "tong": {"dinh_muc": round(t_dm, 3), "thuc_te": round(t_tt, 3),
                     "chi_phi_dinh_muc": t_cp_dm, "chi_phi_thuc_te": t_cp_tt,
                     "chenh_chi_phi": t_cp_tt - t_cp_dm}}


@router.post("/tieu-hao/{thang}/ghi-chi-phi")
def ghi_chi_phi_tu_tieu_hao(thang: str, tai_san_id: int, db: Session = Depends(get_db),
                            nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Đẩy tiêu hao thực tế (chưa ghi) của hệ thống/tháng vào chi phí vận hành."""
    ts = db.get(TaiSanChoThue, tai_san_id)
    ths = db.query(TieuHaoThucTe).filter_by(tai_san_id=tai_san_id, thang=thang).all()
    them = 0
    tong = Decimal(0)
    for th in ths:
        if th.da_ghi_chi_phi or float(th.so_luong or 0) <= 0:
            continue
        hh = db.get(HangHoa, th.hang_hoa_id)
        so_tien = (th.so_luong or Decimal(0)) * (th.don_gia or Decimal(0))
        db.add(ChiPhiVanHanh(tai_san_id=tai_san_id, ma_ban_hang=ts.ma if ts else None,
                             loai_chi_phi="VAT_TU", so_tien=so_tien, ngay=date.today(),
                             nguon="TIEU_HAO",
                             mo_ta=f"Tiêu hao {thang}: {hh.ten if hh else ''} ×{float(th.so_luong or 0):g}"))
        th.da_ghi_chi_phi = True
        them += 1
        tong += so_tien
    ghi_audit(db, nd.id, "TAO", "chi_phi_van_hanh", None, moi={"tu_tieu_hao": them, "thang": thang})
    db.commit()
    return {"thang": thang, "so_chi_phi_them": them, "tong_tien": float(tong)}


# ===================== SO SÁNH TIÊU HAO NHIỀU THÁNG =====================
def _month_list(den_thang: str, n: int) -> list[str]:
    y, m = int(den_thang[:4]), int(den_thang[5:7])
    out = []
    for i in range(n - 1, -1, -1):
        yy, mm = y, m - i
        while mm <= 0:
            mm += 12; yy -= 1
        out.append(f"{yy:04d}-{mm:02d}")
    return out


@router.get("/so-sanh-tieu-hao")
def so_sanh_tieu_hao(tai_san_id: int, den_thang: str | None = None, so_thang: int = 6,
                     db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    if not den_thang:
        den_thang = date.today().strftime("%Y-%m")
    so_thang = max(2, min(int(so_thang), 12))
    months = _month_list(den_thang, so_thang)
    norms = {d.hang_hoa_id: d for d in db.query(DinhMucTieuHao).filter_by(tai_san_id=tai_san_id).all()}
    ths = db.query(TieuHaoThucTe).filter(TieuHaoThucTe.tai_san_id == tai_san_id,
                                         TieuHaoThucTe.thang.in_(months)).all()
    act = {(t.hang_hoa_id, t.thang): t for t in ths}
    hids = set(norms) | {t.hang_hoa_id for t in ths}
    info = {hid: _hh_info(db, hid) for hid in hids}
    rows = []
    for hid in hids:
        hh = info[hid]
        dm = float(norms[hid].dinh_muc_thang) if hid in norms else 0.0
        per = {}
        tong = 0.0
        for mth in months:
            t = act.get((hid, mth))
            q = float(t.so_luong) if t else 0.0
            per[mth] = q
            tong += q
        rows.append({"hang_hoa_id": hid, "ma_hh": hh["ma"], "ten": hh["ten"], "don_vi": hh["don_vi"],
                     "dinh_muc": dm, "gia": hh["gia_ban"], "theo_thang": per,
                     "tb_thuc_te": round(tong / len(months), 3),
                     "vuot_thang": [m for m in months if dm > 0 and per[m] > dm]})
    rows.sort(key=lambda r: (r["ten"] or ""))
    cp_tt = []
    for mth in months:
        s = 0.0
        for hid in hids:
            t = act.get((hid, mth))
            if t:
                s += float(t.so_luong) * (float(t.don_gia) if t.don_gia else info[hid]["gia_ban"])
        cp_tt.append(round(s))
    cdm = sum(float(norms[hid].dinh_muc_thang) * info[hid]["gia_ban"] for hid in norms)
    ts = db.get(TaiSanChoThue, tai_san_id)
    return {"tai_san_id": tai_san_id, "tai_san": ts.ten if ts else None, "ma": ts.ma if ts else None,
            "thang_list": months, "chi_phi_thuc_te": cp_tt,
            "chi_phi_dinh_muc_thang": round(cdm), "chi_phi_dinh_muc": [round(cdm)] * len(months),
            "theo_hang_hoa": rows}


# ===================== MÃ BÁN HÀNG THEO THÁNG (kiểm soát chi phí–doanh thu) =====================
def _ma_thang(prefix: str, thang: str) -> str:
    """thang dạng YYYY-MM -> prefix + MMYY (vd RO-STH + 2026-01 = RO-STH0126)."""
    return f"{prefix}{thang[5:7]}{thang[2:4]}"


@router.get("/du-an/{ts_id}/cac-thang")
def du_an_cac_thang(ts_id: int, so_thang: int = 12, db: Session = Depends(get_db),
                    _=Depends(yeu_cau(MODULE, "XEM"))):
    ts = db.get(TaiSanChoThue, ts_id)
    if ts is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án")
    prefix = ts.ten_du_an or ts.ma
    so_thang = max(1, min(int(so_thang), 24))
    months = _month_list(date.today().strftime("%Y-%m"), so_thang)
    # chi phí theo tháng (theo ngày phát sinh) cho dự án này
    cps = db.query(ChiPhiVanHanh).filter_by(tai_san_id=ts_id).all()
    cp_thang: dict[str, float] = {}
    for c in cps:
        mk = c.ngay.strftime("%Y-%m") if c.ngay else None
        if mk:
            cp_thang[mk] = cp_thang.get(mk, 0.0) + float(c.so_tien or 0)
    dt = float(ts.gia_thue_thang or 0)
    dang_thue = ts.tinh_trang == "DANG_THUE"
    rows = []
    for m in months:
        cp = round(cp_thang.get(m, 0.0))
        rows.append({"thang": m, "ma_ban_hang": _ma_thang(prefix, m),
                     "doanh_thu": dt, "chi_phi": cp, "loi_nhuan": dt - cp})
    return {"tai_san_id": ts_id, "ten_du_an": prefix, "gia_thue_thang": dt,
            "dang_thue": dang_thue, "cac_thang": rows}


# ===================== BÁO CÁO THEO DỰ ÁN (pivot) =====================
@router.get("/bao-cao-theo-du-an")
def bao_cao_theo_du_an(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    moc = date.today() + timedelta(days=7)
    out = []
    for t in db.query(TaiSanChoThue).order_by(TaiSanChoThue.id).all():
        cp = db.query(func.coalesce(func.sum(ChiPhiVanHanh.so_tien), 0)).filter_by(tai_san_id=t.id).scalar() or 0
        bt = db.query(func.count(KeHoachBaoTri.id)).filter(
            KeHoachBaoTri.tai_san_id == t.id, KeHoachBaoTri.ngay_ke_tiep <= moc).scalar() or 0
        dt = float(t.gia_thue_thang or 0) if t.tinh_trang == "DANG_THUE" else 0.0
        out.append({"tai_san_id": t.id, "ten_du_an": t.ten_du_an or t.ma, "ten": t.ten,
                    "tinh_trang": t.tinh_trang, "khach_hang": _ten_kh(db, t.khach_hang_id),
                    "nguyen_gia": float(t.nguyen_gia or 0),
                    "gia_thue_thang": float(t.gia_thue_thang or 0), "doanh_thu_thang": dt,
                    "chi_phi_luy_ke": float(cp), "bao_tri_den_han": int(bt)})
    return {"du_an": out,
            "tong": {"so": len(out),
                     "doanh_thu_thang": sum(o["doanh_thu_thang"] for o in out),
                     "chi_phi_luy_ke": sum(o["chi_phi_luy_ke"] for o in out)}}


# ===================== TÀI LIỆU DỰ ÁN (Document) =====================
NHOM_TL = {"BIEU_MAU", "CO_CQ", "BAN_VE", "CODE", "KHAC"}


async def _luu_tep_ct(file: UploadFile, ts_id: int):
    thu_muc = os.path.join(settings.storage_dir, "cho_thue_da", str(ts_id))
    os.makedirs(thu_muc, exist_ok=True)
    safe = f"{uuid.uuid4().hex}_{os.path.basename(file.filename or 'file')}"
    dd = os.path.join(thu_muc, safe)
    data = await file.read()
    with open(dd, "wb") as f:
        f.write(data)
    return dd, len(data)


@router.post("/du-an/{ts_id}/tai-lieu", status_code=201)
async def them_tai_lieu_ct(ts_id: int, file: UploadFile = File(...), loai: str = Form("KHAC"),
                           ten: str = Form(None), db: Session = Depends(get_db),
                           nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.get(TaiSanChoThue, ts_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án")
    loai = (loai or "KHAC").upper()
    if loai not in NHOM_TL:
        loai = "KHAC"
    dd, kt = await _luu_tep_ct(file, ts_id)
    tep = TepDinhKem(doi_tuong="CHO_THUE_DA", doi_tuong_id=ts_id, loai=loai,
                     ten_file=ten or file.filename or os.path.basename(dd), duong_dan=dd,
                     kich_thuoc=kt, content_type=file.content_type,
                     nguoi_tai_len=nhan_vien_id_cua(db, nd.id))
    db.add(tep); db.flush()
    ghi_audit(db, nd.id, "TAO", "tep_dinh_kem", tep.id, moi={"cho_thue_da": ts_id, "loai": loai})
    db.commit(); db.refresh(tep)
    return {"id": tep.id, "ten": tep.ten_file, "loai": tep.loai, "kich_thuoc": tep.kich_thuoc}


@router.get("/du-an/{ts_id}/tai-lieu")
def ds_tai_lieu_ct(ts_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    rs = db.query(TepDinhKem).filter_by(doi_tuong="CHO_THUE_DA", doi_tuong_id=ts_id) \
           .order_by(TepDinhKem.id.desc()).all()
    return [{"id": t.id, "ten": t.ten_file, "loai": t.loai, "kich_thuoc": t.kich_thuoc,
             "content_type": t.content_type,
             "ngay": str(t.created_at)[:10] if t.created_at else None} for t in rs]


@router.get("/tai-lieu/{tep_id}/tai")
def tai_tai_lieu_ct(tep_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    t = db.get(TepDinhKem, tep_id)
    if t is None or t.doi_tuong != "CHO_THUE_DA":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài liệu")
    return FileResponse(t.duong_dan, filename=t.ten_file,
                        media_type=t.content_type or "application/octet-stream")


@router.delete("/tai-lieu/{tep_id}")
def xoa_tai_lieu_ct(tep_id: int, db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    t = db.get(TepDinhKem, tep_id)
    if t is None or t.doi_tuong != "CHO_THUE_DA":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài liệu")
    try:
        os.remove(t.duong_dan)
    except OSError:
        pass
    db.delete(t)
    ghi_audit(db, nd.id, "XOA", "tep_dinh_kem", tep_id)
    db.commit()
    return {"id": tep_id, "trang_thai": "DA_XOA"}
