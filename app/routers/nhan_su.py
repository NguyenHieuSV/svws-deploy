"""
Module NHÂN SỰ / LƯƠNG — lát cắt dọc thứ sáu.
Điểm mới: QUY TRÌNH DUYỆT TUẦN TỰ (không theo hạn mức tiền):
  NV_HCNS lập lương -> KTT duyệt + hạch toán -> CEO ký cuối.
Dùng primitive chi_vai_tro(...) cho các bước gắn đúng vai trò.
Tính lương (BHXH/TNCN) tách trong luong_service; bút toán trong hach_toan.
"""
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..rbac import yeu_cau, chi_vai_tro
from ..deps import nhan_vien_id_cua
from ..audit import ghi_audit
from ..luong_service import tinh_luong
from ..hach_toan import hach_toan_luong
from ..models import (NguoiDung, NhanVien, ChamCong, NghiPhep, BangLuong, KyLuong, ThamSoLuong)
from ..schemas import (NhanVienRa, ChamCongVao, NghiPhepVao, TinhLuongVao, BangLuongRa,
                        HoSoLuongVao, KyLuongVao, ChamCongLuongVao, ThamSoLuongVao, ChamCongImportVao)
import json as _json
from datetime import date, datetime
from ..email_gateway import lay_email_provider
from ..config import settings
from decimal import Decimal as _Dec

router = APIRouter(prefix="/nhan-su", tags=["nhan_su"])
MODULE = "nhan_su"


@router.get("/nhan-vien", response_model=list[NhanVienRa])
def ds_nhan_vien(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(NhanVien).order_by(NhanVien.id).all()


# ----- Chấm công -----
@router.post("/cham-cong", status_code=201)
def cham_cong(data: ChamCongVao, db: Session = Depends(get_db),
              nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    cc = db.query(ChamCong).filter_by(nhan_vien_id=data.nhan_vien_id, ngay=data.ngay).first()
    if cc is None:
        cc = ChamCong(nhan_vien_id=data.nhan_vien_id, ngay=data.ngay)
        db.add(cc)
    cc.gio_vao = data.gio_vao or cc.gio_vao
    cc.gio_ra = data.gio_ra or cc.gio_ra
    db.commit()
    return {"nhan_vien_id": data.nhan_vien_id, "ngay": str(data.ngay), "trang_thai": "DA_GHI"}


# ----- Nghỉ phép -----
@router.post("/nghi-phep", status_code=201)
def xin_nghi(data: NghiPhepVao, db: Session = Depends(get_db),
             nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    np = NghiPhep(nhan_vien_id=data.nhan_vien_id, tu_ngay=data.tu_ngay,
                  den_ngay=data.den_ngay, loai=data.loai, trang_thai="CHO_DUYET")
    db.add(np); db.flush()
    ghi_audit(db, nd.id, "TAO", "nghi_phep", np.id, moi={"loai": data.loai})
    db.commit()
    return {"id": np.id, "trang_thai": "CHO_DUYET"}


@router.post("/nghi-phep/{np_id}/duyet")
def duyet_nghi(np_id: int, db: Session = Depends(get_db),
               nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    np = db.get(NghiPhep, np_id)
    if np is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn")
    np.trang_thai = "DA_DUYET"
    np.nguoi_duyet = nhan_vien_id_cua(db, nd.id)
    db.commit()
    return {"id": np.id, "trang_thai": "DA_DUYET"}


# ----- Tính lương cả tháng (NV_HCNS) -> trạng thái CHO_DUYET -----
@router.post("/tinh-luong")
def tinh_luong_thang(data: TinhLuongVao, db: Session = Depends(get_db),
                     nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    nvs = db.query(NhanVien).filter_by(trang_thai="DANG_LAM").all()
    tong = Decimal(0)
    n = 0
    for nv in nvs:
        bl = db.query(BangLuong).filter_by(nhan_vien_id=nv.id, thang=data.thang).first()
        if bl and bl.trang_thai == "DA_DUYET":
            continue  # đã chốt, không tính lại
        kq = tinh_luong(nv.luong_co_ban)
        if bl is None:
            bl = BangLuong(nhan_vien_id=nv.id, thang=data.thang)
            db.add(bl)
        for k, v in kq.items():
            setattr(bl, k, v)
        bl.trang_thai = "CHO_DUYET"
        bl.nguoi_duyet_ktt = None
        bl.nguoi_ky_ceo = None
        tong += kq["thuc_linh"]; n += 1
    ghi_audit(db, nd.id, "TAO", "bang_luong", None, moi={"thang": data.thang, "so_nv": n})
    db.commit()
    return {"thang": data.thang, "so_bang_luong": n, "tong_thuc_linh": float(tong)}


@router.get("/bang-luong", response_model=list[BangLuongRa])
def ds_bang_luong(thang: str | None = None, db: Session = Depends(get_db),
                  _=Depends(yeu_cau(MODULE, "XEM"))):
    q = db.query(BangLuong)
    if thang:
        q = q.filter_by(thang=thang)
    return q.order_by(BangLuong.id).all()


# ----- KTT duyệt + hạch toán (bước 1, chỉ KTT/CEO) -----
@router.post("/bang-luong/{thang}/duyet-ktt")
def ktt_duyet(thang: str, db: Session = Depends(get_db),
              nd: NguoiDung = Depends(yeu_cau(MODULE, "XEM")),
              __: NguoiDung = Depends(chi_vai_tro("KTT", "CEO"))):
    rows = db.query(BangLuong).filter_by(thang=thang, trang_thai="CHO_DUYET").all()
    chua = [r for r in rows if r.nguoi_duyet_ktt is None]
    if not chua:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không có bảng lương chờ KTT duyệt")
    me = nhan_vien_id_cua(db, nd.id)
    so_bt = 0
    for bl in chua:
        bl.nguoi_duyet_ktt = me
        so_bt += len(hach_toan_luong(db, bl))
    ghi_audit(db, nd.id, "DUYET", "bang_luong", None,
              moi={"thang": thang, "so_bang": len(chua), "so_but_toan": so_bt})
    db.commit()
    return {"thang": thang, "so_bang_ktt_duyet": len(chua), "so_but_toan_luong": so_bt,
            "buoc_tiep": "CEO ký"}


# ----- CEO ký cuối (bước 2, chỉ CEO; yêu cầu KTT đã duyệt) -----
@router.post("/bang-luong/{thang}/ky-ceo")
def ceo_ky(thang: str, db: Session = Depends(get_db),
           nd: NguoiDung = Depends(yeu_cau(MODULE, "XEM")),
           __: NguoiDung = Depends(chi_vai_tro("CEO"))):
    rows = db.query(BangLuong).filter_by(thang=thang, trang_thai="CHO_DUYET").all()
    if not rows:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không có bảng lương chờ ký")
    chua_ktt = [r for r in rows if r.nguoi_duyet_ktt is None]
    if chua_ktt:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Còn {len(chua_ktt)} bảng chưa được KTT duyệt — chưa thể ký.")
    me = nhan_vien_id_cua(db, nd.id)
    for bl in rows:
        bl.trang_thai = "DA_DUYET"
        bl.nguoi_ky_ceo = me
    ghi_audit(db, nd.id, "DUYET", "bang_luong", None, moi={"thang": thang, "ky": len(rows)})
    db.commit()
    return {"thang": thang, "so_bang_da_ky": len(rows), "trang_thai": "DA_DUYET"}


# ====================== QUY TRÌNH LƯƠNG ĐẦY ĐỦ ======================
def _f(x):
    return float(x or 0)


def _lay_tham_so_luong(db):
    ts = db.get(ThamSoLuong, 1)
    if ts is None:
        ts = ThamSoLuong(id=1); db.add(ts); db.commit(); db.refresh(ts)
    return ts


def _cfg_luong(db):
    ts = _lay_tham_so_luong(db)
    try:
        bac = _json.loads(ts.bac_thue) if ts.bac_thue else None
    except Exception:
        bac = None
    return {
        "tl_bhxh_nv": ts.tl_bhxh_nv, "tl_bhyt_nv": ts.tl_bhyt_nv, "tl_bhtn_nv": ts.tl_bhtn_nv,
        "tl_bhxh_dn": ts.tl_bhxh_dn, "tl_bhyt_dn": ts.tl_bhyt_dn, "tl_bhtn_dn": ts.tl_bhtn_dn,
        "tran_bhxh_bhyt": ts.tran_bhxh_bhyt, "tran_bhtn": ts.tran_bhtn,
        "giam_tru_ban_than": ts.giam_tru_ban_than, "giam_tru_phu_thuoc": ts.giam_tru_phu_thuoc,
        "mien_thue_an": ts.mien_thue_an, "hs_ot_thuong": ts.hs_ot_thuong,
        "hs_ot_cuoi_tuan": ts.hs_ot_cuoi_tuan, "hs_ot_le": ts.hs_ot_le,
        "bac_thue": bac,
    }


def _ap_dung_tinh(db, nv: NhanVien, bl: BangLuong, cfg=None):
    cfg = cfg if cfg is not None else _cfg_luong(db)
    kq = tinh_luong(nv.luong_co_ban, nv.luong_dong_bh, bl.cong_chuan, bl.cong_thuc_te,
                    bl.gio_ot_thuong, bl.gio_ot_cuoi_tuan, bl.gio_ot_le,
                    nv.phu_cap_an, nv.phu_cap_di_lai, nv.phu_cap_dien_thoai, nv.phu_cap_trach_nhiem,
                    nv.so_phu_thuoc, bl.tam_ung,
                    (bl.phu_cap_khac or 0) + (bl.thuong_kpi or 0), bl.ngay_nghi_kpep, bl.so_phut_di_tre, bl.khau_tru_khac, cfg)
    bl.luong_co_ban = nv.luong_co_ban
    for k in ("luong_thuc_te", "ot", "phu_cap", "bhxh", "bhyt", "bhtn",
              "bhxh_dn", "bhyt_dn", "bhtn_dn", "thu_nhap_chiu_thue",
              "thue_tncn", "khau_tru", "thuc_linh", "chi_phi_dn",
              "khau_tru_nghi", "khau_tru_tre"):
        setattr(bl, k, kq[k])
    return kq


def _pl_dict(db, bl: BangLuong, nv: NhanVien = None):
    nv = nv or db.get(NhanVien, bl.nhan_vien_id)
    tong_thu_nhap = _f(bl.luong_thuc_te) + _f(bl.phu_cap) + _f(bl.ot)
    return {
        "id": bl.id, "nhan_vien_id": bl.nhan_vien_id, "ho_ten": nv.ho_ten if nv else "",
        "chuc_danh": nv.chuc_danh if nv else "", "thang": bl.thang,
        "ma_so_thue": nv.ma_so_thue if nv else None,
        "so_tai_khoan": nv.so_tai_khoan if nv else None, "ngan_hang": nv.ngan_hang if nv else None,
        "email": (nv.email if nv and nv.email else None),
        "cong_chuan": _f(bl.cong_chuan), "cong_thuc_te": _f(bl.cong_thuc_te),
        "gio_ot_thuong": _f(bl.gio_ot_thuong), "gio_ot_cuoi_tuan": _f(bl.gio_ot_cuoi_tuan),
        "gio_ot_le": _f(bl.gio_ot_le),
        "luong_co_ban": _f(bl.luong_co_ban), "luong_thuc_te": _f(bl.luong_thuc_te),
        "phu_cap": _f(bl.phu_cap), "phu_cap_khac": _f(bl.phu_cap_khac), "thuong_kpi": _f(bl.thuong_kpi), "ot": _f(bl.ot),
        "ngay_nghi_kpep": _f(bl.ngay_nghi_kpep), "so_phut_di_tre": int(bl.so_phut_di_tre or 0),
        "khau_tru_nghi": _f(bl.khau_tru_nghi), "khau_tru_tre": _f(bl.khau_tru_tre),
        "khau_tru_khac": _f(bl.khau_tru_khac), "tong_thu_nhap": tong_thu_nhap,
        "bhxh": _f(bl.bhxh), "bhyt": _f(bl.bhyt), "bhtn": _f(bl.bhtn),
        "bhxh_dn": _f(bl.bhxh_dn), "bhyt_dn": _f(bl.bhyt_dn), "bhtn_dn": _f(bl.bhtn_dn),
        "thu_nhap_chiu_thue": _f(bl.thu_nhap_chiu_thue), "thue_tncn": _f(bl.thue_tncn),
        "tam_ung": _f(bl.tam_ung), "khau_tru": _f(bl.khau_tru), "thuc_linh": _f(bl.thuc_linh),
        "chi_phi_dn": _f(bl.chi_phi_dn), "trang_thai": bl.trang_thai,
        "email_sent": bool(bl.email_sent),
    }


def _cap_nhat_tong_ky(db, ky: KyLuong):
    rows = db.query(BangLuong).filter_by(thang=ky.thang).all()
    ky.tong_thu_nhap = sum((_Dec(str(_f(r.luong_thuc_te) + _f(r.phu_cap) + _f(r.ot))) for r in rows), _Dec(0))
    ky.tong_thuc_linh = sum((_Dec(str(_f(r.thuc_linh))) for r in rows), _Dec(0))
    ky.tong_chi_phi_dn = sum((_Dec(str(_f(r.chi_phi_dn))) for r in rows), _Dec(0))


# ----- Tham số lương theo luật -----
@router.get("/tham-so-luong")
def lay_tham_so_luong_ep(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    ts = _lay_tham_so_luong(db)
    try:
        bac = _json.loads(ts.bac_thue) if ts.bac_thue else []
    except Exception:
        bac = []
    return {k: _f(getattr(ts, k)) for k in (
        "tl_bhxh_nv", "tl_bhyt_nv", "tl_bhtn_nv", "tl_bhxh_dn", "tl_bhyt_dn", "tl_bhtn_dn",
        "tran_bhxh_bhyt", "tran_bhtn", "giam_tru_ban_than", "giam_tru_phu_thuoc",
        "mien_thue_an", "hs_ot_thuong", "hs_ot_cuoi_tuan", "hs_ot_le",
        "luong_co_so", "luong_toi_thieu_vung")} | {"bac_thue": bac}


@router.put("/tham-so-luong")
def cap_nhat_tham_so_luong(data: ThamSoLuongVao, db: Session = Depends(get_db),
                           nd: NguoiDung = Depends(yeu_cau(MODULE, "DUYET"))):
    ts = _lay_tham_so_luong(db)
    for k in ("tl_bhxh_nv", "tl_bhyt_nv", "tl_bhtn_nv", "tl_bhxh_dn", "tl_bhyt_dn", "tl_bhtn_dn",
              "tran_bhxh_bhyt", "tran_bhtn", "giam_tru_ban_than", "giam_tru_phu_thuoc",
              "mien_thue_an", "hs_ot_thuong", "hs_ot_cuoi_tuan", "hs_ot_le",
              "luong_co_so", "luong_toi_thieu_vung"):
        v = getattr(data, k)
        if v is not None:
            setattr(ts, k, v)
    if data.bac_thue is not None:
        ts.bac_thue = _json.dumps(data.bac_thue)
    ghi_audit(db, nd.id, "CAP_NHAT", "tham_so_luong", 1, moi={"cap_nhat": True})
    db.commit()
    return lay_tham_so_luong_ep(db)


# ----- Nhận dữ liệu chấm công từ app chấm công (đẩy theo kỳ) -----
@router.post("/ky-luong/{thang}/cham-cong-import")
def import_cham_cong(thang: str, data: ChamCongImportVao, db: Session = Depends(get_db),
                     nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    ky = db.get(KyLuong, thang)
    if ky is None or ky.trang_thai == "DA_CHOT":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Kỳ chưa tạo hoặc đã chốt — không thể nhập chấm công.")
    cfg = _cfg_luong(db)
    cap_nhat, khong_thay = 0, []
    for rec in data.ban_ghi:
        nv = None
        if rec.nhan_vien_id:
            nv = db.get(NhanVien, rec.nhan_vien_id)
        elif rec.ma:
            nv = db.query(NhanVien).filter_by(ma=rec.ma).first()
        if nv is None:
            khong_thay.append(rec.ma or rec.nhan_vien_id); continue
        bl = db.query(BangLuong).filter_by(nhan_vien_id=nv.id, thang=thang).first()
        if bl is None:
            khong_thay.append(nv.ma or nv.id); continue
        for k in ("cong_thuc_te", "gio_ot_thuong", "gio_ot_cuoi_tuan", "gio_ot_le",
                  "ngay_nghi_kpep", "so_phut_di_tre"):
            v = getattr(rec, k)
            if v is not None:
                setattr(bl, k, v)
        _ap_dung_tinh(db, nv, bl, cfg)
        cap_nhat += 1
    _cap_nhat_tong_ky(db, ky)
    ghi_audit(db, nd.id, "IMPORT", "cham_cong", None, moi={"thang": thang, "so_ban_ghi": cap_nhat})
    db.commit()
    return {"thang": thang, "cap_nhat": cap_nhat, "khong_tim_thay": khong_thay}


# ----- Hồ sơ lương -----
@router.get("/ho-so")
def ds_ho_so(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    out = []
    for nv in db.query(NhanVien).order_by(NhanVien.id).all():
        out.append({"id": nv.id, "ma": nv.ma, "ho_ten": nv.ho_ten, "chuc_danh": nv.chuc_danh,
                    "trang_thai": nv.trang_thai, "luong_co_ban": _f(nv.luong_co_ban),
                    "luong_dong_bh": _f(nv.luong_dong_bh), "so_phu_thuoc": nv.so_phu_thuoc,
                    "phu_cap_an": _f(nv.phu_cap_an), "phu_cap_di_lai": _f(nv.phu_cap_di_lai),
                    "phu_cap_dien_thoai": _f(nv.phu_cap_dien_thoai),
                    "phu_cap_trach_nhiem": _f(nv.phu_cap_trach_nhiem),
                    "ma_so_thue": nv.ma_so_thue, "so_tai_khoan": nv.so_tai_khoan,
                    "ngan_hang": nv.ngan_hang, "email": nv.email, "tk_chi_phi": nv.tk_chi_phi})
    return out


@router.put("/nhan-vien/{nv_id}/ho-so")
def cap_nhat_ho_so(nv_id: int, data: HoSoLuongVao, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    nv = db.get(NhanVien, nv_id)
    if nv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy nhân viên")
    for k in ("luong_co_ban", "luong_dong_bh", "so_phu_thuoc", "phu_cap_an", "phu_cap_di_lai",
              "phu_cap_dien_thoai", "phu_cap_trach_nhiem", "ma_so_thue", "so_tai_khoan",
              "ngan_hang", "email", "tk_chi_phi"):
        setattr(nv, k, getattr(data, k))
    if data.chuc_danh is not None:
        nv.chuc_danh = data.chuc_danh
    ghi_audit(db, nd.id, "CAP_NHAT", "nhan_vien", nv.id, moi={"luong_co_ban": _f(nv.luong_co_ban)})
    db.commit()
    return {"id": nv.id, "trang_thai": "DA_LUU"}


# ----- Kỳ lương: tạo & sinh bảng lương cho toàn bộ NV đang làm -----
@router.post("/ky-luong")
def tao_ky_luong(data: KyLuongVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    y, mth = int(data.thang[:4]), int(data.thang[5:7])
    ngay_chot = data.ngay_chot or date(y, mth, 7) if mth != 12 else (data.ngay_chot or date(y, 12, 7))
    ky = db.get(KyLuong, data.thang)
    if ky is None:
        ky = KyLuong(thang=data.thang); db.add(ky)
    if ky.trang_thai == "DA_CHOT":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kỳ lương đã chốt, không thể sinh lại.")
    ky.cong_chuan = data.cong_chuan
    ky.ngay_chot = ngay_chot
    n = 0
    for nv in db.query(NhanVien).filter_by(trang_thai="DANG_LAM").all():
        bl = db.query(BangLuong).filter_by(nhan_vien_id=nv.id, thang=data.thang).first()
        moi = bl is None
        if bl is None:
            bl = BangLuong(nhan_vien_id=nv.id, thang=data.thang); db.add(bl)
        bl.cong_chuan = data.cong_chuan
        if moi:
            bl.cong_thuc_te = data.cong_chuan
        bl.trang_thai = "CHO_DUYET"
        db.flush()
        _ap_dung_tinh(db, nv, bl)
        n += 1
    _cap_nhat_tong_ky(db, ky)
    ghi_audit(db, nd.id, "TAO", "ky_luong", None, moi={"thang": data.thang, "so_nv": n})
    db.commit()
    return {"thang": data.thang, "so_nhan_vien": n, "ngay_chot": str(ngay_chot),
            "cong_chuan": _f(ky.cong_chuan), "trang_thai": ky.trang_thai}


@router.get("/ky-luong")
def ds_ky_luong(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    out = []
    for ky in db.query(KyLuong).order_by(KyLuong.thang.desc()).all():
        out.append({"thang": ky.thang, "cong_chuan": _f(ky.cong_chuan),
                    "ngay_chot": str(ky.ngay_chot) if ky.ngay_chot else None,
                    "trang_thai": ky.trang_thai, "da_gui_email": bool(ky.da_gui_email),
                    "tong_thu_nhap": _f(ky.tong_thu_nhap), "tong_thuc_linh": _f(ky.tong_thuc_linh),
                    "tong_chi_phi_dn": _f(ky.tong_chi_phi_dn)})
    return out


@router.get("/ky-luong/{thang}")
def chi_tiet_ky(thang: str, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    ky = db.get(KyLuong, thang)
    rows = db.query(BangLuong).filter_by(thang=thang).order_by(BangLuong.id).all()
    pl = [_pl_dict(db, r) for r in rows]
    tre_han = bool(ky and ky.ngay_chot and date.today() > ky.ngay_chot and ky.trang_thai != "DA_CHOT")
    head = ({"thang": ky.thang, "cong_chuan": _f(ky.cong_chuan),
             "ngay_chot": str(ky.ngay_chot) if ky.ngay_chot else None, "trang_thai": ky.trang_thai,
             "da_gui_email": bool(ky.da_gui_email)} if ky else
            {"thang": thang, "trang_thai": "CHUA_TAO"})
    return {"ky": head, "tre_han": tre_han, "phieu": pl,
            "tong": {"thu_nhap": sum(p["tong_thu_nhap"] for p in pl),
                     "thuc_linh": sum(p["thuc_linh"] for p in pl),
                     "bh_nv": sum(p["bhxh"] + p["bhyt"] + p["bhtn"] for p in pl),
                     "bh_dn": sum(p["bhxh_dn"] + p["bhyt_dn"] + p["bhtn_dn"] for p in pl),
                     "thue_tncn": sum(p["thue_tncn"] for p in pl),
                     "chi_phi_dn": sum(p["chi_phi_dn"] for p in pl)}}


@router.get("/phieu-luong/{bl_id}")
def chi_tiet_phieu(bl_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    bl = db.get(BangLuong, bl_id)
    if bl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiếu lương")
    return _pl_dict(db, bl)


# ----- Chấm công / OT / tạm ứng cho 1 nhân viên -> tính lại -----
@router.put("/phieu-luong/{bl_id}")
def cham_cong_phieu(bl_id: int, data: ChamCongLuongVao, db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    bl = db.get(BangLuong, bl_id)
    if bl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiếu lương")
    if bl.trang_thai == "DA_DUYET":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kỳ đã chốt, không sửa được.")
    for k in ("cong_thuc_te", "gio_ot_thuong", "gio_ot_cuoi_tuan", "gio_ot_le", "tam_ung",
              "phu_cap_khac", "ngay_nghi_kpep", "so_phut_di_tre", "khau_tru_khac"):
        v = getattr(data, k)
        if v is not None:
            setattr(bl, k, v)
    nv = db.get(NhanVien, bl.nhan_vien_id)
    _ap_dung_tinh(db, nv, bl)
    ky = db.get(KyLuong, bl.thang)
    if ky:
        _cap_nhat_tong_ky(db, ky)
    db.commit()
    return _pl_dict(db, bl, nv)


# ----- CHỐT lương: tính lại + hạch toán chi phí + khóa kỳ -----
@router.post("/ky-luong/{thang}/chot")
def chot_ky_luong(thang: str, db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "XEM")),
                  __: NguoiDung = Depends(chi_vai_tro("KTT", "CEO"))):
    ky = db.get(KyLuong, thang)
    if ky is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chưa tạo kỳ lương này")
    if ky.trang_thai == "DA_CHOT":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kỳ lương đã chốt rồi.")
    rows = db.query(BangLuong).filter_by(thang=thang).all()
    if not rows:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kỳ chưa có bảng lương.")
    me = nhan_vien_id_cua(db, nd.id)
    so_bt = 0
    for bl in rows:
        nv = db.get(NhanVien, bl.nhan_vien_id)
        _ap_dung_tinh(db, nv, bl)
        so_bt += len(hach_toan_luong(db, bl))
        bl.trang_thai = "DA_DUYET"
        bl.nguoi_duyet_ktt = me
        bl.nguoi_ky_ceo = me
    ky.trang_thai = "DA_CHOT"
    ky.nguoi_chot = me
    _cap_nhat_tong_ky(db, ky)
    ghi_audit(db, nd.id, "DUYET", "ky_luong", None,
              moi={"thang": thang, "so_bang": len(rows), "so_but_toan": so_bt})
    db.commit()
    return {"thang": thang, "so_bang": len(rows), "so_but_toan_luong": so_bt,
            "tong_chi_phi_dn": _f(ky.tong_chi_phi_dn), "trang_thai": "DA_CHOT"}


# ----- GỬI EMAIL phiếu lương từng người (chậm nhất ngày 7) -----
def _email_phieu_luong_html(nv, p):
    def vn(x):
        return f"{x:,.0f}đ"
    return f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;color:#1f2937">
<div style="background:#0e7490;color:#fff;padding:14px 18px;border-radius:8px 8px 0 0">
  <div style="font-size:16px;font-weight:bold">{settings.cong_ty_ten}</div>
  <div style="font-size:12px;opacity:.9">{settings.cong_ty_dia_chi}</div></div>
<div style="border:1px solid #e5e7eb;border-top:0;padding:18px;border-radius:0 0 8px 8px">
  <h2 style="margin:0 0 4px">PHIẾU LƯƠNG THÁNG {p['thang']}</h2>
  <div style="color:#6b7280;font-size:13px;margin-bottom:12px">Nhân viên: <b>{nv.ho_ten}</b>{' · ' + (nv.chuc_danh or '') if nv.chuc_danh else ''} · Mã NV: {nv.ma or nv.id}</div>
  <table style="width:100%;border-collapse:collapse;font-size:14px">
    <tr><td style="padding:5px 0">Công chuẩn / thực tế</td><td style="text-align:right">{p['cong_chuan']:.0f} / {p['cong_thuc_te']:.0f}</td></tr>
    <tr><td>Lương theo công</td><td style="text-align:right">{vn(p['luong_thuc_te'] + p.get('khau_tru_nghi',0) + p.get('khau_tru_tre',0))}</td></tr>
    <tr><td>Tăng ca (thường {p['gio_ot_thuong']:.0f}h · cuối tuần {p['gio_ot_cuoi_tuan']:.0f}h · lễ {p['gio_ot_le']:.0f}h)</td><td style="text-align:right">{vn(p['ot'])}</td></tr>
    <tr><td>Phụ cấp{(' (gồm phát sinh ' + vn(p['phu_cap_khac']) + ')') if p.get('phu_cap_khac') else ''}</td><td style="text-align:right">{vn(p['phu_cap'])}</td></tr>
    {f'<tr><td style="color:#b91c1c">Trừ nghỉ không phép ({p["ngay_nghi_kpep"]:.1f} ngày)</td><td style="text-align:right;color:#b91c1c">-{vn(p["khau_tru_nghi"])}</td></tr>' if p.get('khau_tru_nghi') else ''}
    {f'<tr><td style="color:#b91c1c">Trừ đi trễ ({p["so_phut_di_tre"]} phút)</td><td style="text-align:right;color:#b91c1c">-{vn(p["khau_tru_tre"])}</td></tr>' if p.get('khau_tru_tre') else ''}
    <tr style="border-top:1px solid #e5e7eb;font-weight:bold"><td style="padding-top:6px">TỔNG THU NHẬP</td><td style="text-align:right;padding-top:6px">{vn(p['tong_thu_nhap'])}</td></tr>
    <tr><td style="color:#b91c1c">BHXH (8%)</td><td style="text-align:right;color:#b91c1c">-{vn(p['bhxh'])}</td></tr>
    <tr><td style="color:#b91c1c">BHYT (1,5%)</td><td style="text-align:right;color:#b91c1c">-{vn(p['bhyt'])}</td></tr>
    <tr><td style="color:#b91c1c">BHTN (1%)</td><td style="text-align:right;color:#b91c1c">-{vn(p['bhtn'])}</td></tr>
    <tr><td style="color:#b91c1c">Thuế TNCN</td><td style="text-align:right;color:#b91c1c">-{vn(p['thue_tncn'])}</td></tr>
    {f'<tr><td style="color:#b91c1c">Khấu trừ khác</td><td style="text-align:right;color:#b91c1c">-{vn(p["khau_tru_khac"])}</td></tr>' if p.get('khau_tru_khac') else ''}
    {f'<tr><td style="color:#b91c1c">Tạm ứng</td><td style="text-align:right;color:#b91c1c">-{vn(p["tam_ung"])}</td></tr>' if p['tam_ung'] else ''}
    <tr style="border-top:2px solid #0e7490;font-weight:bold;font-size:16px"><td style="padding-top:8px;color:#0e7490">THỰC LĨNH</td><td style="text-align:right;padding-top:8px;color:#0e7490">{vn(p['thuc_linh'])}</td></tr>
  </table>
  {f'<div style="color:#6b7280;font-size:12px;margin-top:10px">Chuyển khoản: {nv.so_tai_khoan} - {nv.ngan_hang or ""}</div>' if nv.so_tai_khoan else ''}
  <div style="color:#9ca3af;font-size:11px;margin-top:14px;border-top:1px solid #f3f4f6;padding-top:8px">
    Phiếu lương tự động từ hệ thống ERP SVWS. Mọi thắc mắc vui lòng liên hệ Phòng Hành chính - Nhân sự.</div>
</div></div>"""


@router.post("/ky-luong/{thang}/gui-email")
def gui_email_luong(thang: str, db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    ky = db.get(KyLuong, thang)
    if ky is None or ky.trang_thai != "DA_CHOT":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cần CHỐT kỳ lương trước khi gửi email.")
    rows = db.query(BangLuong).filter_by(thang=thang).all()
    provider = lay_email_provider()
    da_gui, bo_qua = 0, []
    for bl in rows:
        nv = db.get(NhanVien, bl.nhan_vien_id)
        to = nv.email
        if not to and nv.nguoi_dung_id:
            u = db.get(NguoiDung, nv.nguoi_dung_id)
            to = u.email if u else None
        if not to:
            bo_qua.append(nv.ho_ten); continue
        p = _pl_dict(db, bl, nv)
        provider.gui(to, f"[SVWS] Phiếu lương tháng {thang} - {nv.ho_ten}",
                     _email_phieu_luong_html(nv, p), gui_tu=settings.cong_ty_email)
        bl.email_sent = True
        bl.ngay_gui_email = datetime.now()
        da_gui += 1
    ky.da_gui_email = True
    tre_han = bool(ky.ngay_chot and date.today() > ky.ngay_chot)
    ghi_audit(db, nd.id, "GUI_EMAIL", "ky_luong", None, moi={"thang": thang, "da_gui": da_gui})
    db.commit()
    return {"thang": thang, "da_gui": da_gui, "bo_qua_thieu_email": bo_qua,
            "tre_han": tre_han, "han_chot": str(ky.ngay_chot) if ky.ngay_chot else None}
