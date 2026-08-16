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
from ..luu_tru import luu, xoa, ton_tai, phan_hoi_tai
from ..rbac import yeu_cau, chi_vai_tro
from ..deps import nhan_vien_id_cua
from ..audit import ghi_audit
from ..models import (NguoiDung, KhachHang, YeuCauMua, HangHoa, HoaDon,
                      TaiSanChoThue, ChiPhiVanHanh, KeHoachBaoTri,
                      DinhMucTieuHao, TieuHaoThucTe, TepDinhKem, CtThietBi, CtBaoCaoVh,
                      CtBcvhChiTieu, NhanVien)

router = APIRouter(prefix="/cho-thue", tags=["cho_thue_ops"])
MODULE = "cho_thue"
# Các tab từ Tài sản trở đi: chỉ CEO / ADMIN / TP_QLNB (xem cho_thue.py).
quan_ly_ct = chi_vai_tro("CEO", "ADMIN", "TP_QLNB")
TINH_TRANG = {"SAN_SANG", "DANG_THUE", "BAO_TRI", "HONG", "THANH_LY"}


def _ten_kh(db, kid):
    if not kid:
        return None
    kh = db.get(KhachHang, kid)
    return kh.ten if kh else None


def _ts_ra(db, t: TaiSanChoThue) -> dict:
    return {"id": t.id, "ma": t.ma, "ten_du_an": t.ten_du_an or t.ma, "ten": t.ten, "loai": t.loai,
            "loai_he_thong": t.loai_he_thong,
            "nguyen_gia": float(t.nguyen_gia or 0), "gia_thue_thang": float(t.gia_thue_thang or 0),
            "don_vi_gia": t.don_vi_gia or "VND/THANG",
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
    loai_he_thong: str | None = None
    nguyen_gia: Decimal = 0
    gia_thue_thang: Decimal = 0
    don_vi_gia: str = Field(default="VND/THANG", pattern="^(VND/THANG|VND/M3)$")
    khau_hao_thang: Decimal = 0
    ngay_mua: date | None = None
    vi_tri: str | None = None
    ghi_chu: str | None = None
    khach_hang_id: int | None = None   # khách thuê gắn ngay khi tạo dự án


class TaiSanSuaCT(BaseModel):
    ten_du_an: str | None = None
    ten: str | None = None
    loai: str | None = None
    loai_he_thong: str | None = None
    nguyen_gia: Decimal | None = None
    gia_thue_thang: Decimal | None = None
    don_vi_gia: str | None = Field(default=None, pattern="^(VND/THANG|VND/M3)$")
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
    if data.khach_hang_id and db.get(KhachHang, data.khach_hang_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khách hàng")
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
    for f in ("ten_du_an", "ten", "loai", "loai_he_thong", "nguyen_gia", "gia_thue_thang",
              "don_vi_gia", "khau_hao_thang", "tinh_trang", "vi_tri", "ghi_chu"):
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


# ===================== THIẾT BỊ / VẬT TƯ CỦA DỰ ÁN CHO THUÊ =====================
class CtTbVao(BaseModel):
    ten: str
    thong_so: str | None = None
    so_luong: Decimal = 1
    don_gia: Decimal = 0
    ghi_chu: str | None = None


class CtTbSua(BaseModel):
    ten: str | None = None
    thong_so: str | None = None
    so_luong: Decimal | None = None
    don_gia: Decimal | None = None
    ghi_chu: str | None = None


@router.get("/tai-san/{ts_id}/thiet-bi")
def ds_thiet_bi(ts_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM")), _ql: NguoiDung = Depends(quan_ly_ct)):
    if db.get(TaiSanChoThue, ts_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án cho thuê")
    rows = db.query(CtThietBi).filter_by(tai_san_id=ts_id).order_by(CtThietBi.id).all()
    ds = [{"id": r.id, "ten": r.ten, "thong_so": r.thong_so,
           "so_luong": float(r.so_luong or 0), "don_gia": float(r.don_gia or 0),
           "thanh_tien": float((r.so_luong or 0) * (r.don_gia or 0)),
           "ghi_chu": r.ghi_chu} for r in rows]
    return {"danh_sach": ds, "tong": sum(x["thanh_tien"] for x in ds)}


@router.post("/tai-san/{ts_id}/thiet-bi", status_code=201)
def them_thiet_bi(ts_id: int, data: CtTbVao, db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC")), _ql: NguoiDung = Depends(quan_ly_ct)):
    if db.get(TaiSanChoThue, ts_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án cho thuê")
    tb = CtThietBi(tai_san_id=ts_id, ten=data.ten.strip()[:250], thong_so=data.thong_so,
                   so_luong=data.so_luong, don_gia=data.don_gia, ghi_chu=data.ghi_chu)
    db.add(tb); db.flush()
    ghi_audit(db, nd.id, "TAO", "ct_thiet_bi", tb.id, moi={"tai_san_id": ts_id, "ten": tb.ten})
    db.commit()
    return {"id": tb.id, "ok": True}


@router.put("/thiet-bi/{tb_id}")
def sua_thiet_bi(tb_id: int, data: CtTbSua, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC")), _ql: NguoiDung = Depends(quan_ly_ct)):
    tb = db.get(CtThietBi, tb_id)
    if tb is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thiết bị/vật tư")
    for f in ("ten", "thong_so", "so_luong", "don_gia", "ghi_chu"):
        v = getattr(data, f)
        if v is not None:
            setattr(tb, f, v)
    ghi_audit(db, nd.id, "SUA", "ct_thiet_bi", tb.id, moi=data.model_dump(exclude_none=True, mode="json"))
    db.commit()
    return {"ok": True}


@router.delete("/thiet-bi/{tb_id}")
def xoa_thiet_bi(tb_id: int, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    tb = db.get(CtThietBi, tb_id)
    if tb is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thiết bị/vật tư")
    ghi_audit(db, nd.id, "XOA", "ct_thiet_bi", tb_id, cu={"ten": tb.ten, "tai_san_id": tb.tai_san_id})
    db.delete(tb)
    db.commit()
    return {"ok": True}


# ===================== BÁO CÁO VẬN HÀNH (KY_THUAT | HOA_CHAT_VT) =====================
class BcvhVao(BaseModel):
    loai: str = Field(default="KY_THUAT", pattern="^(KY_THUAT|HOA_CHAT_VT)$")
    ngay: date | None = None
    noi_dung: str
    thong_so: str | None = None
    so_luong: Decimal | None = None
    don_vi: str | None = None
    ghi_chu: str | None = None


@router.get("/tai-san/{ts_id}/bao-cao")
def ds_bao_cao_vh(ts_id: int, loai: str | None = None, db: Session = Depends(get_db),
                  _=Depends(yeu_cau(MODULE, "XEM"))):
    if db.get(TaiSanChoThue, ts_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án cho thuê")
    q = db.query(CtBaoCaoVh).filter_by(tai_san_id=ts_id)
    if loai:
        q = q.filter(CtBaoCaoVh.loai == loai)
    out = []
    for r in q.order_by(CtBaoCaoVh.ngay.desc(), CtBaoCaoVh.id.desc()).limit(300).all():
        nv = db.get(NhanVien, r.nguoi_tao) if r.nguoi_tao else None
        out.append({"id": r.id, "loai": r.loai, "ngay": str(r.ngay) if r.ngay else None,
                    "vi_tri": r.vi_tri, "noi_dung": r.noi_dung, "thong_so": r.thong_so,
                    "so_luong": float(r.so_luong) if r.so_luong is not None else None,
                    "luong_ton": float(r.luong_ton) if r.luong_ton is not None else None,
                    "luong_nhap": float(r.luong_nhap) if r.luong_nhap is not None else None,
                    "don_vi": r.don_vi, "ghi_chu": r.ghi_chu,
                    "nguoi_bc": nv.ho_ten if nv else None})
    return out


@router.post("/tai-san/{ts_id}/bao-cao", status_code=201)
def them_bao_cao_vh(ts_id: int, data: BcvhVao, db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.get(TaiSanChoThue, ts_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án cho thuê")
    r = CtBaoCaoVh(tai_san_id=ts_id, loai=data.loai, ngay=data.ngay or date.today(),
                   noi_dung=data.noi_dung.strip(), thong_so=data.thong_so,
                   so_luong=data.so_luong, don_vi=data.don_vi, ghi_chu=data.ghi_chu,
                   nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(r); db.flush()
    ghi_audit(db, nd.id, "TAO", "ct_bao_cao_vh", r.id, moi={"tai_san_id": ts_id, "loai": data.loai})
    db.commit()
    return {"id": r.id, "ok": True}


@router.post("/tai-san/{ts_id}/chuyen-bcvh")
def chuyen_bcvh(ts_id: int, den_ts_id: int, loai: str = "HOA_CHAT_VT",
                noi_dung: str | None = None,
                db: Session = Depends(get_db),
                nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """Chuyển toàn bộ dữ liệu Báo cáo vận hành MỘT LOẠI (KY_THUAT | HOA_CHAT_VT |
    KHOI_LUONG) kèm danh mục chỉ tiêu tương ứng từ dự án này sang dự án khác —
    dùng khi nhập nhầm dự án. Chỉ CEO/ADMIN; có audit."""
    if loai not in ("KY_THUAT", "HOA_CHAT_VT", "KHOI_LUONG"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Loại không hợp lệ")
    tu = db.get(TaiSanChoThue, ts_id)
    den = db.get(TaiSanChoThue, den_ts_id)
    if tu is None or den is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án nguồn/đích")
    if ts_id == den_ts_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dự án nguồn và đích phải khác nhau")
    q_bc = db.query(CtBaoCaoVh).filter_by(tai_san_id=ts_id, loai=loai)
    q_ct = db.query(CtBcvhChiTieu).filter_by(tai_san_id=ts_id, loai=loai)
    if noi_dung:
        # chuyển CHỌN LỌC theo tên hệ thống / chỉ tiêu — nhiều tên cách nhau '|',
        # so khớp không phân biệt hoa thường; các tên khác giữ nguyên ở dự án nguồn
        tens = [t.strip().lower() for t in noi_dung.split("|") if t.strip()]
        if tens:
            q_bc = q_bc.filter(func.lower(CtBaoCaoVh.noi_dung).in_(tens))
            q_ct = q_ct.filter(func.lower(CtBcvhChiTieu.chi_tieu).in_(tens))
    so_bc = q_bc.update({"tai_san_id": den_ts_id}, synchronize_session=False)
    so_ct = q_ct.update({"tai_san_id": den_ts_id}, synchronize_session=False)
    ghi_audit(db, nd.id, "CHUYEN_BCVH", "tai_san_cho_thue", ts_id,
              moi={"den_ts_id": den_ts_id, "loai": loai, "noi_dung": noi_dung,
                   "so_bao_cao": so_bc, "so_chi_tieu": so_ct,
                   "tu": tu.ten_du_an or tu.ma, "den": den.ten_du_an or den.ma})
    db.commit()
    return {"ok": True, "loai": loai, "so_bao_cao": so_bc, "so_chi_tieu": so_ct,
            "tu": tu.ten_du_an or tu.ma, "den": den.ten_du_an or den.ma}


# --- Bộ CHỈ TIÊU MẪU báo cáo kỹ thuật (lưu theo dự án, dùng lại mỗi ngày) ---
class CtChiTieuVao(BaseModel):
    loai: str = Field(default="KY_THUAT", pattern="^(KY_THUAT|HOA_CHAT_VT|KHOI_LUONG)$")
    vi_tri: str | None = None
    chi_tieu: str          # tên chỉ tiêu / hóa chất-vật tư / hệ thống
    don_vi: str | None = None


@router.get("/tai-san/{ts_id}/chi-tieu")
def ds_chi_tieu(ts_id: int, loai: str | None = None, db: Session = Depends(get_db),
                _=Depends(yeu_cau(MODULE, "XEM"))):
    q = db.query(CtBcvhChiTieu).filter_by(tai_san_id=ts_id)
    if loai:
        q = q.filter(CtBcvhChiTieu.loai == loai)
    return [{"id": c.id, "loai": c.loai or "KY_THUAT", "vi_tri": c.vi_tri,
             "chi_tieu": c.chi_tieu, "don_vi": c.don_vi}
            for c in q.order_by(CtBcvhChiTieu.thu_tu, CtBcvhChiTieu.id).all()]


@router.post("/tai-san/{ts_id}/chi-tieu", status_code=201)
def them_chi_tieu(ts_id: int, data: CtChiTieuVao, db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.get(TaiSanChoThue, ts_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án cho thuê")
    c = CtBcvhChiTieu(tai_san_id=ts_id, loai=data.loai, vi_tri=(data.vi_tri or "").strip()[:150] or None,
                      chi_tieu=data.chi_tieu.strip()[:250], don_vi=(data.don_vi or "").strip()[:20] or None)
    db.add(c); db.flush()
    ghi_audit(db, nd.id, "TAO", "ct_bcvh_chi_tieu", c.id, moi={"tai_san_id": ts_id, "loai": data.loai, "chi_tieu": c.chi_tieu})
    db.commit()
    return {"id": c.id, "loai": c.loai, "vi_tri": c.vi_tri, "chi_tieu": c.chi_tieu, "don_vi": c.don_vi}


class CtChiTieuSua(BaseModel):
    vi_tri: str | None = None
    chi_tieu: str | None = None
    don_vi: str | None = None


@router.put("/chi-tieu/{ct_id}")
def sua_chi_tieu(ct_id: int, data: CtChiTieuSua, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Sửa chỉ tiêu trong bộ mẫu nhập liệu BCVH (vị trí / tên / đơn vị).
    Các dòng báo cáo ĐÃ GHI giữ nguyên nội dung cũ."""
    c = db.get(CtBcvhChiTieu, ct_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy chỉ tiêu")
    cu = {"vi_tri": c.vi_tri, "chi_tieu": c.chi_tieu, "don_vi": c.don_vi}
    if data.chi_tieu is not None and data.chi_tieu.strip():
        c.chi_tieu = data.chi_tieu.strip()[:250]
    if data.vi_tri is not None:
        c.vi_tri = data.vi_tri.strip()[:150] or None
    if data.don_vi is not None:
        c.don_vi = data.don_vi.strip()[:20] or None
    ghi_audit(db, nd.id, "SUA", "ct_bcvh_chi_tieu", c.id, cu=cu,
              moi={"vi_tri": c.vi_tri, "chi_tieu": c.chi_tieu, "don_vi": c.don_vi})
    db.commit()
    return {"id": c.id, "loai": c.loai, "vi_tri": c.vi_tri, "chi_tieu": c.chi_tieu, "don_vi": c.don_vi}


@router.delete("/chi-tieu/{ct_id}")
def xoa_chi_tieu(ct_id: int, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    c = db.get(CtBcvhChiTieu, ct_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy chỉ tiêu")
    ghi_audit(db, nd.id, "XOA", "ct_bcvh_chi_tieu", ct_id, cu={"chi_tieu": c.chi_tieu})
    db.delete(c)
    db.commit()
    return {"ok": True}


# --- Lưu báo cáo kỹ thuật NGÀY (nhiều chỉ tiêu 1 lần) ---
class BcKtDong(BaseModel):
    vi_tri: str | None = None
    chi_tieu: str
    ket_qua: str | None = None
    ghi_chu: str | None = None


class BcKtBatch(BaseModel):
    ngay: date | None = None
    dong: list[BcKtDong]


@router.post("/tai-san/{ts_id}/bao-cao-kt", status_code=201)
def luu_bao_cao_kt(ts_id: int, data: BcKtBatch, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.get(TaiSanChoThue, ts_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án cho thuê")
    ng = data.ngay or date.today()
    nv_id = nhan_vien_id_cua(db, nd.id)
    n = 0
    for d in data.dong:
        if not (d.ket_qua or "").strip():
            continue
        db.add(CtBaoCaoVh(tai_san_id=ts_id, loai="KY_THUAT", ngay=ng, vi_tri=d.vi_tri,
                          noi_dung=d.chi_tieu, thong_so=d.ket_qua.strip(),
                          ghi_chu=d.ghi_chu, nguoi_tao=nv_id))
        n += 1
    if not n:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chưa nhập kết quả cho chỉ tiêu nào")
    ghi_audit(db, nd.id, "TAO", "ct_bao_cao_vh", None, moi={"tai_san_id": ts_id, "ngay": str(ng), "so_dong": n})
    db.commit()
    return {"so_dong": n, "ngay": str(ng)}


# --- TỔNG HỢP BCVH THEO THÁNG: chất lượng nước · hóa chất · tổng lượng nước ---
def _so_tu_text(v):
    """Rút số đầu tiên từ chuỗi kết quả test ('7.2', '45 ppm', 'pH 6,8')."""
    import re
    if v is None:
        return None
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(v))
    return float(m.group(0).replace(",", ".")) if m else None


@router.get("/tai-san/{ts_id}/tong-hop-thang")
def tong_hop_thang(ts_id: int, thang: str | None = None, db: Session = Depends(get_db),
                   _=Depends(yeu_cau(MODULE, "XEM")), _ql: NguoiDung = Depends(quan_ly_ct)):
    """Tổng hợp báo cáo vận hành theo tháng của dự án: chất lượng nước (BC kỹ thuật),
    hóa chất (SL dùng/nhập), tổng lượng nước (chỉ số cuối − mốc trước tháng)."""
    import calendar
    if db.get(TaiSanChoThue, ts_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án cho thuê")
    try:
        y, m = (thang or date.today().strftime("%Y-%m")).split("-")
        d1 = date(int(y), int(m), 1)
        d2 = date(int(y), int(m), calendar.monthrange(int(y), int(m))[1])
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tháng không hợp lệ (YYYY-MM)")
    rows = (db.query(CtBaoCaoVh)
            .filter(CtBaoCaoVh.tai_san_id == ts_id,
                    CtBaoCaoVh.ngay >= d1, CtBaoCaoVh.ngay <= d2)
            .order_by(CtBaoCaoVh.ngay, CtBaoCaoVh.id).all())
    # 1) Chất lượng nước — nhóm theo (vị trí, chỉ tiêu)
    kt = {}
    for r in (x for x in rows if x.loai == "KY_THUAT"):
        e = kt.setdefault((r.vi_tri or "", r.noi_dung),
                          {"vi_tri": r.vi_tri, "chi_tieu": r.noi_dung, "series": []})
        e["series"].append({"ngay": str(r.ngay), "kq": r.thong_so, "gia_tri": _so_tu_text(r.thong_so)})
    for e in kt.values():
        nums = [p["gia_tri"] for p in e["series"] if p["gia_tri"] is not None]
        e["so_lan"] = len(e["series"])
        e["min"] = min(nums) if nums else None
        e["max"] = max(nums) if nums else None
        e["tb"] = round(sum(nums) / len(nums), 2) if nums else None
        e["gan_nhat"] = e["series"][-1]["kq"] if e["series"] else None
    # 2) Hóa chất - vật tư — nhóm theo tên
    hc = {}
    for r in (x for x in rows if x.loai == "HOA_CHAT_VT"):
        e = hc.setdefault(r.noi_dung, {"ten": r.noi_dung, "don_vi": r.don_vi,
                                       "tong_dung": 0.0, "tong_nhap": 0.0, "series": []})
        if r.don_vi:
            e["don_vi"] = r.don_vi
        if r.so_luong is not None:
            e["tong_dung"] += float(r.so_luong)
        if r.luong_nhap is not None:
            e["tong_nhap"] += float(r.luong_nhap)
        e["series"].append({"ngay": str(r.ngay),
                            "sl_dung": float(r.so_luong) if r.so_luong is not None else None,
                            "ton": float(r.luong_ton) if r.luong_ton is not None else None})
    for e in hc.values():
        e["tong_dung"] = round(e["tong_dung"], 3)
        e["tong_nhap"] = round(e["tong_nhap"], 3)
    # 3) Tổng lượng nước — nhóm theo hệ thống, mốc = chỉ số cuối cùng TRƯỚC tháng
    kl = {}
    for r in (x for x in rows if x.loai == "KHOI_LUONG" and x.luong_ton is not None):
        e = kl.setdefault(r.noi_dung, {"he_thong": r.noi_dung, "don_vi": r.don_vi, "series": []})
        if r.don_vi:
            e["don_vi"] = r.don_vi
        e["series"].append({"ngay": str(r.ngay), "chi_so": float(r.luong_ton)})
    for ten, e in kl.items():
        moc = (db.query(CtBaoCaoVh)
               .filter(CtBaoCaoVh.tai_san_id == ts_id, CtBaoCaoVh.loai == "KHOI_LUONG",
                       CtBaoCaoVh.noi_dung == ten, CtBaoCaoVh.luong_ton.isnot(None),
                       CtBaoCaoVh.ngay < d1)
               .order_by(CtBaoCaoVh.ngay.desc(), CtBaoCaoVh.id.desc()).first())
        dau = float(moc.luong_ton) if moc else (e["series"][0]["chi_so"] if e["series"] else None)
        cuoi = e["series"][-1]["chi_so"] if e["series"] else None
        e["chi_so_dau"] = dau
        e["chi_so_cuoi"] = cuoi
        e["tong"] = round(cuoi - dau, 3) if (dau is not None and cuoi is not None) else None
    return {"thang": f"{int(y):04d}-{int(m):02d}",
            "chat_luong": list(kt.values()), "hoa_chat": list(hc.values()),
            "luong_nuoc": list(kl.values())}


# --- Lưu báo cáo Hóa chất - Vật tư theo LƯỢNG TỒN (SL dùng tự tính) ---
def _ton_lien_truoc(db, ts_id: int, ten: str, ngay, exclude_id: int | None = None):
    """Bản ghi tồn gần nhất TRƯỚC ngày đã cho của cùng mặt hàng (để tính SL dùng)."""
    q = db.query(CtBaoCaoVh).filter(CtBaoCaoVh.tai_san_id == ts_id,
                                    CtBaoCaoVh.loai == "HOA_CHAT_VT",
                                    CtBaoCaoVh.noi_dung == ten,
                                    CtBaoCaoVh.luong_ton.isnot(None),
                                    CtBaoCaoVh.ngay <= ngay)
    if exclude_id:
        q = q.filter(CtBaoCaoVh.id != exclude_id)
    return q.order_by(CtBaoCaoVh.ngay.desc(), CtBaoCaoVh.id.desc()).first()


class BcHcDong(BaseModel):
    ten: str
    luong_nhap: Decimal | None = None   # lượng nhập trong ngày (0/bỏ trống nếu không nhập)
    luong_ton: Decimal | None = None    # tồn thực tế CUỐI NGÀY (đã gồm hàng nhập trong ngày)
    don_vi: str | None = None
    ghi_chu: str | None = None


class BcHcBatch(BaseModel):
    ngay: date | None = None
    dong: list[BcHcDong]


@router.post("/tai-san/{ts_id}/bao-cao-hc", status_code=201)
def luu_bao_cao_hc(ts_id: int, data: BcHcBatch, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Lưu báo cáo hóa chất - vật tư theo ngày: nhập LƯỢNG TỒN, SL dùng tự tính
    = tồn liền trước − tồn cùng dòng (âm nghĩa là vừa nạp/bổ sung thêm)."""
    if db.get(TaiSanChoThue, ts_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án cho thuê")
    ng = data.ngay or date.today()
    nv_id = nhan_vien_id_cua(db, nd.id)
    n = 0
    for d in data.dong:
        if d.luong_ton is None:
            continue
        truoc = _ton_lien_truoc(db, ts_id, d.ten, ng)
        # SL dùng = tồn liền trước + lượng nhập hôm nay − tồn cuối ngày hôm nay
        sl_dung = (truoc.luong_ton + (d.luong_nhap or 0) - d.luong_ton) if truoc else None
        db.add(CtBaoCaoVh(tai_san_id=ts_id, loai="HOA_CHAT_VT", ngay=ng,
                          noi_dung=d.ten, luong_ton=d.luong_ton, luong_nhap=d.luong_nhap,
                          so_luong=sl_dung,
                          don_vi=d.don_vi, ghi_chu=d.ghi_chu, nguoi_tao=nv_id))
        db.flush()
        n += 1
    if not n:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chưa nhập lượng tồn cho mặt hàng nào")
    ghi_audit(db, nd.id, "TAO", "ct_bao_cao_vh", None,
              moi={"tai_san_id": ts_id, "loai": "HOA_CHAT_VT", "ngay": str(ng), "so_dong": n})
    db.commit()
    return {"so_dong": n, "ngay": str(ng)}


# --- Lưu báo cáo KHỐI LƯỢNG theo ngày (chỉ số nước theo hệ thống) ---
class BcKlDong(BaseModel):
    he_thong: str
    chi_so: Decimal | None = None
    don_vi: str | None = None
    ghi_chu: str | None = None


class BcKlBatch(BaseModel):
    ngay: date | None = None
    dong: list[BcKlDong]


@router.post("/tai-san/{ts_id}/bao-cao-kl", status_code=201)
def luu_bao_cao_kl(ts_id: int, data: BcKlBatch, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Báo cáo khối lượng: ghi CHỈ SỐ NƯỚC theo từng hệ thống của dự án."""
    if db.get(TaiSanChoThue, ts_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án cho thuê")
    ng = data.ngay or date.today()
    nv_id = nhan_vien_id_cua(db, nd.id)
    n = 0
    for d in data.dong:
        if d.chi_so is None:
            continue
        db.add(CtBaoCaoVh(tai_san_id=ts_id, loai="KHOI_LUONG", ngay=ng,
                          noi_dung=d.he_thong, luong_ton=d.chi_so,
                          don_vi=d.don_vi, ghi_chu=d.ghi_chu, nguoi_tao=nv_id))
        n += 1
    if not n:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chưa nhập chỉ số cho hệ thống nào")
    ghi_audit(db, nd.id, "TAO", "ct_bao_cao_vh", None,
              moi={"tai_san_id": ts_id, "loai": "KHOI_LUONG", "ngay": str(ng), "so_dong": n})
    db.commit()
    return {"so_dong": n, "ngay": str(ng)}


class BcvhSua(BaseModel):
    ngay: date | None = None
    vi_tri: str | None = None
    noi_dung: str | None = None
    thong_so: str | None = None
    so_luong: Decimal | None = None
    luong_ton: Decimal | None = None
    luong_nhap: Decimal | None = None
    don_vi: str | None = None
    ghi_chu: str | None = None


@router.put("/bao-cao-vh/{bc_id}")
def sua_bao_cao_vh(bc_id: int, data: BcvhSua, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    r = db.get(CtBaoCaoVh, bc_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo cáo")
    for f in ("ngay", "vi_tri", "noi_dung", "thong_so", "so_luong", "luong_ton", "luong_nhap", "don_vi", "ghi_chu"):
        v = getattr(data, f)
        if v is not None:
            setattr(r, f, v)
    # sửa lượng tồn/nhập (hoặc ngày/tên) của dòng HC → tính lại SL dùng
    if r.loai == "HOA_CHAT_VT" and r.luong_ton is not None and \
       (data.luong_ton is not None or data.luong_nhap is not None or
            data.ngay is not None or data.noi_dung is not None):
        truoc = _ton_lien_truoc(db, r.tai_san_id, r.noi_dung, r.ngay, exclude_id=r.id)
        r.so_luong = (truoc.luong_ton + (r.luong_nhap or 0) - r.luong_ton) if truoc else None
    ghi_audit(db, nd.id, "SUA", "ct_bao_cao_vh", r.id, moi=data.model_dump(exclude_none=True, mode="json"))
    db.commit()
    return {"ok": True, "so_luong": float(r.so_luong) if r.so_luong is not None else None}


@router.delete("/bao-cao-vh/{bc_id}")
def xoa_bao_cao_vh(bc_id: int, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    r = db.get(CtBaoCaoVh, bc_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo cáo")
    ghi_audit(db, nd.id, "XOA", "ct_bao_cao_vh", bc_id,
              cu={"loai": r.loai, "ngay": str(r.ngay), "noi_dung": (r.noi_dung or "")[:150]})
    db.delete(r)
    db.commit()
    return {"ok": True}


# ----- DUYET: xóa tài sản cho thuê -----
@router.delete("/tai-san/{ts_id}")
def xoa_tai_san(ts_id: int, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """Xóa tài sản cùng kế hoạch bảo trì và định mức; chi phí vận hành cũ chỉ bị
    gỡ liên kết. Chặn khi tài sản đang cho thuê hoặc gắn hợp đồng thuê."""
    from sqlalchemy import text as _sql
    from sqlalchemy.exc import IntegrityError
    t = db.get(TaiSanChoThue, ts_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài sản")
    if t.tinh_trang == "DANG_THUE" or t.khach_hang_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Tài sản '{t.ten}' đang cho thuê/gắn khách hàng — kết thúc cho thuê trước khi xóa.")
    # kiểm tra dòng hợp đồng thuê (bảng có thể không tồn tại ở schema hiện tại —
    # dùng savepoint để câu SQL hỏng không làm treo transaction)
    n = 0
    sp = db.begin_nested()
    try:
        n = db.execute(_sql("SELECT COUNT(*) FROM hop_dong_thue_ct WHERE tai_san_id = :i"),
                       {"i": ts_id}).scalar() or 0
        sp.commit()
    except Exception:
        sp.rollback()
    if n:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Tài sản '{t.ten}' đang gắn {n} dòng hợp đồng thuê — không thể xóa để giữ vết.")
    ma_cu, ten_cu = t.ma, t.ten
    db.query(KeHoachBaoTri).filter_by(tai_san_id=ts_id).delete()
    db.query(DinhMucTieuHao).filter_by(tai_san_id=ts_id).delete()
    db.query(TieuHaoThucTe).filter_by(tai_san_id=ts_id).delete()
    db.query(ChiPhiVanHanh).filter_by(tai_san_id=ts_id).update({"tai_san_id": None})
    try:
        db.delete(t)
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Tài sản '{ten_cu}' còn dữ liệu liên kết ở phân hệ khác nên không thể xóa.")
    ghi_audit(db, nd.id, "XOA", "tai_san_cho_thue", ts_id, cu={"ma": ma_cu, "ten": ten_cu})
    db.commit()
    return {"ok": True, "ten": ten_cu}


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
               _=Depends(yeu_cau(MODULE, "XEM")), _ql: NguoiDung = Depends(quan_ly_ct)):
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
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC")), _ql: NguoiDung = Depends(quan_ly_ct)):
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


# ----- DUYET: xóa chi phí vận hành -----
@router.delete("/chi-phi/{cp_id}")
def xoa_chi_phi(cp_id: int, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    c = db.get(ChiPhiVanHanh, cp_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy chi phí")
    ghi_audit(db, nd.id, "XOA", "chi_phi_van_hanh", cp_id,
              cu={"ma_ban_hang": c.ma_ban_hang, "loai": c.loai_chi_phi,
                  "so_tien": float(c.so_tien or 0), "nguon": c.nguon})
    db.delete(c)
    db.commit()
    return {"ok": True}


@router.post("/dong-bo-chi-phi")
def dong_bo_chi_phi(db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC")), _ql: NguoiDung = Depends(quan_ly_ct)):
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
def ds_de_xuat(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM")), _ql: NguoiDung = Depends(quan_ly_ct)):
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
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC")), _ql: NguoiDung = Depends(quan_ly_ct)):
    if db.get(HangHoa, data.hang_hoa_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hàng hóa")
    yc = YeuCauMua(hang_hoa_id=data.hang_hoa_id, so_luong=data.so_luong, don_gia=data.don_gia,
                   cho_thue_ma=data.cho_thue_ma, ly_do=data.ly_do or "Vật tư/thiết bị cho thuê",
                   trang_thai="MOI", nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(yc); db.flush()
    ghi_audit(db, nd.id, "TAO", "yeu_cau_mua", yc.id, moi={"cho_thue_ma": data.cho_thue_ma})
    db.commit()
    return {"id": yc.id, "trang_thai": yc.trang_thai}


# ----- DUYET: xóa đề xuất mua cho thuê -----
@router.delete("/de-xuat-mua/{ycm_id}")
def xoa_de_xuat_ct(ycm_id: int, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    yc = db.get(YeuCauMua, ycm_id)
    if yc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đề xuất")
    if yc.don_mua_id or yc.trang_thai == "DA_TAO_PO":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Đề xuất đã được tạo PO — không thể xóa. Hãy xóa PO liên quan trước.")
    so_cp = db.query(func.count(ChiPhiVanHanh.id)).filter_by(yeu_cau_mua_id=ycm_id).scalar() or 0
    if so_cp:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Đề xuất đã đồng bộ thành {so_cp} chi phí vận hành — xóa chi phí đó trước.")
    ghi_audit(db, nd.id, "XOA", "yeu_cau_mua", ycm_id,
              cu={"cho_thue_ma": yc.cho_thue_ma, "trang_thai": yc.trang_thai})
    db.delete(yc)
    db.commit()
    return {"ok": True}


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


class BaoTriSua(BaseModel):
    ten_cong_viec: str | None = None
    chu_ky_ngay: int | None = Field(default=None, ge=1, le=3660)
    ngay_ke_tiep: date | None = None
    chi_phi_du_kien: Decimal | None = None
    ghi_chu: str | None = None


@router.put("/bao-tri/{bt_id}")
def sua_bao_tri(bt_id: int, data: BaoTriSua, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Sửa kế hoạch bảo trì: công việc, chu kỳ, ngày kế tiếp, chi phí dự kiến, ghi chú."""
    b = db.get(KeHoachBaoTri, bt_id)
    if b is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy kế hoạch bảo trì")
    cu = {"ten_cong_viec": b.ten_cong_viec, "chu_ky_ngay": b.chu_ky_ngay,
          "ngay_ke_tiep": str(b.ngay_ke_tiep) if b.ngay_ke_tiep else None,
          "chi_phi_du_kien": float(b.chi_phi_du_kien or 0), "ghi_chu": b.ghi_chu}
    if data.ten_cong_viec is not None and data.ten_cong_viec.strip():
        b.ten_cong_viec = data.ten_cong_viec.strip()[:200]
    if data.chu_ky_ngay is not None:
        b.chu_ky_ngay = data.chu_ky_ngay
    if data.ngay_ke_tiep is not None:
        b.ngay_ke_tiep = data.ngay_ke_tiep
    if data.chi_phi_du_kien is not None:
        b.chi_phi_du_kien = data.chi_phi_du_kien
    if data.ghi_chu is not None:
        b.ghi_chu = data.ghi_chu.strip() or None
    ghi_audit(db, nd.id, "SUA", "ke_hoach_bao_tri", b.id, cu=cu,
              moi=data.model_dump(exclude_none=True, mode="json"))
    db.commit()
    return _bt_ra(db, b)


# ----- DUYET: xóa kế hoạch bảo trì -----
@router.delete("/bao-tri/{bt_id}")
def xoa_bao_tri(bt_id: int, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    b = db.get(KeHoachBaoTri, bt_id)
    if b is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy kế hoạch bảo trì")
    ghi_audit(db, nd.id, "XOA", "ke_hoach_bao_tri", bt_id,
              cu={"tai_san_id": b.tai_san_id, "ten_cong_viec": b.ten_cong_viec})
    db.delete(b)
    db.commit()
    return {"ok": True}


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
def ds_dinh_muc(tai_san_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM")), _ql: NguoiDung = Depends(quan_ly_ct)):
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
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC")), _ql: NguoiDung = Depends(quan_ly_ct)):
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
                 nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
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
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC")), _ql: NguoiDung = Depends(quan_ly_ct)):
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
                     _=Depends(yeu_cau(MODULE, "XEM")), _ql: NguoiDung = Depends(quan_ly_ct)):
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
                            nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC")), _ql: NguoiDung = Depends(quan_ly_ct)):
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
                     db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM")), _ql: NguoiDung = Depends(quan_ly_ct)):
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


def _rut_hd_email(tieu_de: str, noi_dung: str) -> dict:
    """Bộ đọc dự phòng bằng regex khi AI chưa bật: số HĐ, ngày, số tiền lớn nhất."""
    import re as _re
    t = f"{tieu_de}\n{noi_dung or ''}"
    so_hd = None
    m = _re.search(r"(?:hóa đơn số|hoa don so|số hóa đơn|invoice|HĐ số|HD so|HĐ|inv)[:\s#]*([A-Za-z0-9\-/\.]{2,30})", t, _re.I)
    if m:
        so_hd = m.group(1)
    ngay = None
    m = _re.search(r"(\d{4})-(\d{2})-(\d{2})", t)
    if m:
        ngay = m.group(0)
    else:
        m = _re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", t)
        if m:
            ngay = f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    tien = 0
    for m in _re.finditer(r"\d[\d\.,]{3,}", t):
        try:
            n = int(_re.sub(r"[.,]", "", m.group(0)))
            if 1000 <= n <= 10 ** 12 and n > tien:
                tien = n
        except Exception:
            pass
    return {"so_hoa_don": so_hd, "ngay": ngay, "so_tien": tien or None,
            "ncc_ten": None, "mo_ta": None}


@router.get("/tai-san/{ts_id}/ncc-email")
def ds_ncc_email(ts_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    from ..models import CtNccEmail
    return [{"id": e.id, "email": e.email, "ten_ncc": e.ten_ncc,
             "hoa_chat_vat_tu": e.hoa_chat_vat_tu}
            for e in db.query(CtNccEmail).filter_by(tai_san_id=ts_id).order_by(CtNccEmail.id).all()]


class NccEmailVao(BaseModel):
    email: str
    ten_ncc: str | None = None
    hoa_chat_vat_tu: str | None = None


@router.post("/tai-san/{ts_id}/ncc-email", status_code=201)
def them_ncc_email(ts_id: int, data: NccEmailVao, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    from ..models import CtNccEmail
    from ..nhac_viec_service import gio_hien_tai
    if db.get(TaiSanChoThue, ts_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án")
    em = (data.email or "").strip().lower()[:160]
    if "@" not in em or "." not in em.split("@")[-1]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Email '{em}' không hợp lệ")
    if db.query(CtNccEmail).filter_by(tai_san_id=ts_id, email=em).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email này đã khai cho dự án")
    e = CtNccEmail(tai_san_id=ts_id, email=em,
                   ten_ncc=(data.ten_ncc or "").strip()[:200] or None,
                   hoa_chat_vat_tu=(data.hoa_chat_vat_tu or "").strip()[:300] or None,
                   tao_luc=gio_hien_tai())
    db.add(e)
    db.flush()
    ghi_audit(db, nd.id, "TAO", "ct_ncc_email", e.id, moi={"tai_san_id": ts_id, "email": em})
    db.commit()
    return {"id": e.id, "ok": True}


@router.delete("/ncc-email/{e_id}")
def xoa_ncc_email(e_id: int, db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    from ..models import CtNccEmail
    e = db.get(CtNccEmail, e_id)
    if e is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy")
    ghi_audit(db, nd.id, "XOA", "ct_ncc_email", e_id, cu={"email": e.email})
    db.delete(e)
    db.commit()
    return {"ok": True}


@router.post("/hoa-don-dau-vao/quet")
def quet_hoa_don_email(tu_ngay: date | None = None, db: Session = Depends(get_db),
                       nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """🤖 Quét hộp thư công ty: thư mới của NCC được AI đọc (số HĐ · ngày · số tiền),
    tự gắn dự án nếu tiêu đề/nội dung chứa MÃ DỰ ÁN → vào hàng CHỜ XÁC NHẬN."""
    from ..inbound_gateway import lay_inbound_provider
    from ..ai_gateway import doc_hoa_don_email
    from ..models import CtHoaDonDauVao
    from ..nhac_viec_service import gio_hien_tai
    prov = lay_inbound_provider()
    moc = tu_ngay or (date.today() - timedelta(days=30))
    try:
        thu = prov.lay_thu(moc) if hasattr(prov, "lay_thu") else prov.lay_thu_moi()
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Không đọc được hộp thư ({prov.ten}): {str(e)[:150]} — "
                            "kiểm tra INBOUND_PROVIDER=IMAP + IMAP_HOST/USER/PASS trên Render.")
    ds_ts = db.query(TaiSanChoThue).all()
    from ..models import CtNccEmail
    theo_email = {}
    for e in db.query(CtNccEmail).all():
        k = (e.email or "").strip().lower()
        if k:
            theo_email[k] = e
    them = trung = dung_ai = khong_khop = con_lai = 0
    GIOI_HAN = 25          # mỗi lần quét AI đọc tối đa 25 thư mới — phần còn lại quét lần sau
    for m in thu:
        mid = (m.get("message_id") or "").strip()[:250] or None
        if mid and db.query(CtHoaDonDauVao).filter_by(message_id=mid).first():
            trung += 1
            continue
        if them >= GIOI_HAN:
            con_lai += 1
            continue
        tieu_de = (m.get("tieu_de") or "")[:250]
        nd_thu = m.get("noi_dung") or ""
        tU = (tieu_de + "\n" + nd_thu).upper()
        ts_id, ma_da, best = None, None, ""
        for t in ds_ts:
            for ma in {(t.ten_du_an or "").strip().upper(), (t.ma or "").strip().upper()}:
                if ma and len(ma) >= 4 and ma in tU and len(ma) > len(best):
                    best, ts_id, ma_da = ma, t.id, ma
        # ƯU TIÊN DANH BẠ: thư từ email NCC đã khai → gắn thẳng dự án của danh bạ
        dk = theo_email.get((m.get("tu_email") or "").strip().lower())
        if dk is not None and dk.tai_san_id:
            ts_id = dk.tai_san_id
            t_dk = db.get(TaiSanChoThue, dk.tai_san_id)
            ma_da = (t_dk.ten_du_an or t_dk.ma) if t_dk else ma_da
        elif ts_id is None and theo_email:
            # đã có danh bạ nhưng thư không thuộc NCC nào và không chứa mã dự án → bỏ qua
            khong_khop += 1
            continue
        info = doc_hoa_don_email(tieu_de, nd_thu, dk.hoa_chat_vat_tu if dk else None)
        if info:
            dung_ai += 1
        else:
            info = _rut_hd_email(tieu_de, nd_thu)
        # 📎 Thân thư không có số tiền → AI đọc FILE ĐÍNH KÈM (PDF/XML hóa đơn điện tử)
        if not float(info.get("so_tien") or 0):
            from ..ai_gateway import doc_hoa_don_tep
            for tep in (m.get("dinh_kem") or []):
                info2 = doc_hoa_don_tep(tep.get("data") or b"", tep.get("content_type") or "",
                                        tep.get("ten_file") or "",
                                        dk.hoa_chat_vat_tu if dk else None)
                if info2 and float(info2.get("so_tien") or 0):
                    for k in ("ncc_ten", "so_hoa_don", "ngay", "so_tien", "mo_ta"):
                        if info2.get(k):
                            info[k] = info2[k]
                    break
        ngay_hd = None
        try:
            if info.get("ngay"):
                ngay_hd = date.fromisoformat(str(info["ngay"])[:10])
        except Exception:
            pass
        try:
            tien = Decimal(str(int(float(info.get("so_tien") or 0))))
        except Exception:
            tien = Decimal(0)
        db.add(CtHoaDonDauVao(
            tai_san_id=ts_id, ma_du_an=ma_da,
            tu_email=(m.get("tu_email") or "")[:160] or None,
            ncc_ten=(str(info.get("ncc_ten") or "")[:200]) or (dk.ten_ncc if dk else None),
            so_hoa_don=(str(info.get("so_hoa_don") or "")[:60]) or None,
            ngay_hd=ngay_hd, so_tien=tien,
            mo_ta=(str(info.get("mo_ta") or "")[:300]) or None,
            tieu_de=tieu_de or None, message_id=mid, tao_luc=gio_hien_tai()))
        them += 1
    db.commit()
    return {"ok": True, "che_do": prov.ten, "thu_moi": len(thu),
            "tu_ngay": str(moc), "da_them": them, "trung_bo_qua": trung,
            "ai": dung_ai, "khong_khop": khong_khop, "con_lai": con_lai}


@router.get("/hoa-don-dau-vao")
def ds_hoa_don_dau_vao(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    from ..models import CtHoaDonDauVao
    out = []
    for r in (db.query(CtHoaDonDauVao).order_by(CtHoaDonDauVao.id.desc()).limit(400).all()):
        ts = db.get(TaiSanChoThue, r.tai_san_id) if r.tai_san_id else None
        out.append({"id": r.id, "tai_san_id": r.tai_san_id,
                    "ten_du_an": (ts.ten_du_an or ts.ma) if ts else None,
                    "ma_du_an": r.ma_du_an, "tu_email": r.tu_email, "ncc_ten": r.ncc_ten,
                    "so_hoa_don": r.so_hoa_don,
                    "ngay_hd": str(r.ngay_hd) if r.ngay_hd else None,
                    "so_tien": float(r.so_tien or 0), "mo_ta": r.mo_ta,
                    "loai_chi_phi": getattr(r, "loai_chi_phi", None) or "VAT_TU",
                    "tieu_de": r.tieu_de, "trang_thai": r.trang_thai})
    return out


class HdVaoSua(BaseModel):
    tai_san_id: int | None = None
    ncc_ten: str | None = None
    so_hoa_don: str | None = None
    ngay_hd: date | None = None
    so_tien: Decimal | None = None
    mo_ta: str | None = None
    loai_chi_phi: str | None = None


@router.put("/hoa-don-dau-vao/{hd_id}")
def sua_hoa_don_dau_vao(hd_id: int, data: HdVaoSua, db: Session = Depends(get_db),
                        nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    from ..models import CtHoaDonDauVao
    r = db.get(CtHoaDonDauVao, hd_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hóa đơn")
    if r.trang_thai == "DA_GHI":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Hóa đơn đã ghi vào chi phí — không sửa được nữa")
    if data.tai_san_id is not None:
        r.tai_san_id = data.tai_san_id or None
    if data.ncc_ten is not None:
        r.ncc_ten = data.ncc_ten.strip()[:200] or None
    if data.so_hoa_don is not None:
        r.so_hoa_don = data.so_hoa_don.strip()[:60] or None
    if data.ngay_hd is not None:
        r.ngay_hd = data.ngay_hd
    if data.so_tien is not None:
        r.so_tien = data.so_tien
    if data.mo_ta is not None:
        r.mo_ta = data.mo_ta.strip()[:300] or None
    if data.loai_chi_phi is not None and data.loai_chi_phi in ("VAT_TU", "SUA_CHUA", "NHAN_CONG", "KHAC"):
        r.loai_chi_phi = data.loai_chi_phi
    db.commit()
    return {"ok": True}


@router.post("/hoa-don-dau-vao/{hd_id}/ghi")
def ghi_hoa_don_dau_vao(hd_id: int, db: Session = Depends(get_db),
                        nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """XÁC NHẬN: ghi hóa đơn thành khoản Chi phí vận hành của dự án theo đúng ngày HĐ."""
    from ..models import CtHoaDonDauVao
    r = db.get(CtHoaDonDauVao, hd_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hóa đơn")
    if r.trang_thai == "DA_GHI":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Hóa đơn này đã ghi rồi")
    if not r.tai_san_id or db.get(TaiSanChoThue, r.tai_san_id) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chưa chọn dự án cho hóa đơn")
    if float(r.so_tien or 0) <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Số tiền phải lớn hơn 0")
    ts = db.get(TaiSanChoThue, r.tai_san_id)
    ngay_hd = r.ngay_hd or date.today()
    ma_bh = _ma_thang(ts.ten_du_an or ts.ma, ngay_hd.strftime("%Y-%m"))
    cp = ChiPhiVanHanh(tai_san_id=r.tai_san_id, ma_ban_hang=ma_bh,
                       loai_chi_phi=(r.loai_chi_phi or "VAT_TU"), so_tien=r.so_tien, ngay=ngay_hd,
                       mo_ta=(f"HĐ {r.so_hoa_don or '—'} — {r.ncc_ten or r.tu_email or 'NCC'}")[:300],
                       nguon="HD_EMAIL")
    db.add(cp)
    db.flush()
    r.trang_thai = "DA_GHI"
    r.chi_phi_id = cp.id
    ghi_audit(db, nd.id, "GHI_HD_EMAIL", "ct_hoa_don_dau_vao", r.id,
              moi={"chi_phi_id": cp.id, "so_tien": float(r.so_tien or 0), "ma": ma_bh})
    db.commit()
    return {"ok": True, "chi_phi_id": cp.id, "ma_ban_hang": ma_bh}


@router.post("/hoa-don-dau-vao/{hd_id}/bo-qua")
def bo_qua_hoa_don_dau_vao(hd_id: int, db: Session = Depends(get_db),
                           nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    from ..models import CtHoaDonDauVao
    r = db.get(CtHoaDonDauVao, hd_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hóa đơn")
    if r.trang_thai == "DA_GHI":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Hóa đơn đã ghi — không bỏ qua được")
    r.trang_thai = "BO_QUA"
    db.commit()
    return {"ok": True}


@router.delete("/hoa-don-dau-vao/{hd_id}")
def xoa_hoa_don_dau_vao(hd_id: int, db: Session = Depends(get_db),
                        nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """Xóa bản ghi hóa đơn đầu vào (thư rác / quét nhầm). Khoản chi phí đã ghi (nếu có) giữ nguyên."""
    from ..models import CtHoaDonDauVao
    r = db.get(CtHoaDonDauVao, hd_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hóa đơn")
    ghi_audit(db, nd.id, "XOA", "ct_hoa_don_dau_vao", hd_id,
              cu={"tieu_de": r.tieu_de, "so_tien": float(r.so_tien or 0), "trang_thai": r.trang_thai})
    db.delete(r)
    db.commit()
    return {"ok": True}


@router.get("/tai-san/{ts_id}/chi-phi-van-hanh-tong-hop")
def chi_phi_vh_tong_hop(ts_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Tổng hợp chi phí vận hành TỰ ĐỘNG từ mục vận hành: SL dùng hóa chất-vật tư
    (Báo cáo hóa chất) × đơn giá hàng hóa trong Kho + các khoản Bảo trì/Sửa chữa đã ghi.
    Bảng thống kê để kiểm soát — không ghi sổ kế toán."""
    if db.get(TaiSanChoThue, ts_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án")
    import unicodedata

    def _bo_dau(s2: str) -> str:
        s2 = unicodedata.normalize("NFD", s2 or "")
        s2 = "".join(ch for ch in s2 if unicodedata.category(ch) != "Mn")
        return s2.replace("đ", "d").replace("Đ", "D").lower().strip()

    kho = []          # (ten_chuan, gia_ban) — dùng khớp gần đúng theo tên
    gia = {}
    for h in db.query(HangHoa).all():
        k = _bo_dau(h.ten or "")
        if not k:
            continue
        g0 = float(h.gia_ban or 0)
        if k not in gia:
            gia[k] = g0
        kho.append((k, g0))

    def _tim_gia(ten: str):
        k = _bo_dau(ten)
        if not k:
            return None
        if k in gia and gia[k] > 0:
            return gia[k]
        # khớp gần đúng: tên kho CHỨA tên báo cáo (hoặc ngược lại) — ưu tiên mục có giá, tên ngắn nhất
        ung = [(t, g0) for (t, g0) in kho
               if g0 > 0 and ((len(k) >= 3 and k in t) or (len(t) >= 4 and t in k))]
        if ung:
            return sorted(ung, key=lambda x: len(x[0]))[0][1]
        return gia.get(k)          # khớp đúng tên nhưng giá 0 → vẫn trả 0 để hiện cảnh báo
    out = []
    for r in (db.query(CtBaoCaoVh).filter_by(tai_san_id=ts_id, loai="HOA_CHAT_VT")
              .order_by(CtBaoCaoVh.ngay.desc(), CtBaoCaoVh.id.desc()).limit(1000).all()):
        sl = float(r.so_luong or 0)
        if sl <= 0:
            continue
        g = _tim_gia(r.noi_dung or "")
        out.append({"ngay": str(r.ngay) if r.ngay else None, "nhom": "HOA_CHAT_VT",
                    "ten": r.noi_dung, "sl": sl, "don_vi": r.don_vi,
                    "don_gia": g or 0, "thanh_tien": round(sl * (g or 0)),
                    "co_gia": bool(g)})
    for c in db.query(ChiPhiVanHanh).filter_by(tai_san_id=ts_id).all():
        if (c.nguon or "") == "BAO_TRI" or (c.loai_chi_phi or "") == "SUA_CHUA":
            out.append({"ngay": str(c.ngay) if c.ngay else None, "nhom": "BAO_TRI",
                        "ten": c.mo_ta or "Bảo trì / sửa chữa", "sl": None, "don_vi": None,
                        "don_gia": None, "thanh_tien": float(c.so_tien or 0), "co_gia": True})
    return out


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
    cp_hc: dict[str, float] = {}     # 1. Hóa chất - Vật tư (loại VAT_TU)
    cp_bt: dict[str, float] = {}     # 2. Bảo trì (nguồn BAO_TRI hoặc loại SUA_CHUA)
    cp_khac: dict[str, float] = {}   # còn lại (nhân công, khác)
    for c in cps:
        mk = c.ngay.strftime("%Y-%m") if c.ngay else None
        if mk:
            v = float(c.so_tien or 0)
            cp_thang[mk] = cp_thang.get(mk, 0.0) + v
            if (c.nguon or "") == "BAO_TRI" or (c.loai_chi_phi or "") == "SUA_CHUA":
                cp_bt[mk] = cp_bt.get(mk, 0.0) + v
            elif (c.loai_chi_phi or "") == "VAT_TU":
                cp_hc[mk] = cp_hc.get(mk, 0.0) + v
            else:
                cp_khac[mk] = cp_khac.get(mk, 0.0) + v
    dt = float(ts.gia_thue_thang or 0)
    dang_thue = ts.tinh_trang == "DANG_THUE"
    # KHỐI LƯỢNG nước xử lý theo tháng = tổng chênh lệch chỉ số giữa các lần ghi
    # (tính riêng từng hệ thống, cộng dồn vào tháng của lần ghi sau)
    kls = (db.query(CtBaoCaoVh).filter_by(tai_san_id=ts_id, loai="KHOI_LUONG")
           .order_by(CtBaoCaoVh.ngay, CtBaoCaoVh.id).all())
    he_thong: dict = {}
    don_vi_kl = None
    for r in kls:
        if r.luong_ton is None:
            continue
        if r.don_vi and not don_vi_kl:
            don_vi_kl = r.don_vi
        he_thong.setdefault((r.noi_dung or "").strip().lower(), []).append(r)
    kl_thang: dict[str, float] = {}
    for arr in he_thong.values():
        for i in range(1, len(arr)):
            mk = arr[i].ngay.strftime("%Y-%m") if arr[i].ngay else None
            if mk:
                kl_thang[mk] = kl_thang.get(mk, 0.0) + (float(arr[i].luong_ton) - float(arr[i - 1].luong_ton))
    theo_m3 = (ts.don_vi_gia or "").upper() == "VND/M3"
    rows = []
    for m in months:
        cp = round(cp_thang.get(m, 0.0))
        kl = round(kl_thang.get(m, 0.0), 1)
        # Dự án tính VND/m³: DOANH THU = KHỐI LƯỢNG × ĐƠN GIÁ; dự án VND/tháng: giá thuê tháng
        doanh_thu = round(kl * dt) if theo_m3 else dt
        rows.append({"thang": m, "ma_ban_hang": _ma_thang(prefix, m),
                     "khoi_luong": kl,
                     "don_vi_kl": don_vi_kl or "m³",
                     "don_gia": dt, "don_vi_gia": ts.don_vi_gia or "VND/THANG",
                     "cp_hoa_chat": round(cp_hc.get(m, 0.0)),
                     "cp_bao_tri": round(cp_bt.get(m, 0.0)),
                     "cp_khac": round(cp_khac.get(m, 0.0)),
                     "doanh_thu": doanh_thu, "chi_phi": cp, "loi_nhuan": doanh_thu - cp})
    return {"tai_san_id": ts_id, "ten_du_an": prefix, "gia_thue_thang": dt,
            "dang_thue": dang_thue, "cac_thang": rows}


# ===================== BÁO CÁO THEO DỰ ÁN (pivot) =====================
@router.get("/bao-cao-theo-du-an")
def bao_cao_theo_du_an(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM")), _ql: NguoiDung = Depends(quan_ly_ct)):
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
    data = await file.read()
    ref = luu(data, "cho_thue_da", ts_id, file.filename, file.content_type)
    return ref, len(data)


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
    return phan_hoi_tai(t.duong_dan, t.ten_file, t.content_type)


@router.delete("/tai-lieu/{tep_id}")
def xoa_tai_lieu_ct(tep_id: int, db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    t = db.get(TepDinhKem, tep_id)
    if t is None or t.doi_tuong != "CHO_THUE_DA":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài liệu")
    xoa(t.duong_dan)
    db.delete(t)
    ghi_audit(db, nd.id, "XOA", "tep_dinh_kem", tep_id)
    db.commit()
    return {"id": tep_id, "trang_thai": "DA_XOA"}
