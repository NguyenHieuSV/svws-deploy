"""
Module TÀI CHÍNH — tổng hợp dòng tiền & công nợ quá hạn (cảnh báo tự động).
Đọc dữ liệu do Kế toán/Bán hàng sinh ra; không nhập liệu trùng.
"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..rbac import yeu_cau, chi_vai_tro
from ..models import (CongNo, ThanhToan, ButToan, TaiKhoanQuy, TonKho, HangHoa,
                      NguoiDung, ThamSoTaiChinh, KhoanVay, LichTraNo)
from ..ai_gateway import tu_van_tai_chinh
from ..schemas import ThamSoTaiChinhVao
from ..audit import ghi_audit

router = APIRouter(prefix="/tai-chinh", tags=["tai_chinh"])
MODULE = "tai_chinh"


@router.get("/dong-tien")
def dong_tien(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    tong_thu = db.query(func.coalesce(func.sum(ThanhToan.so_tien), 0)).scalar()
    phai_thu = db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0)) \
                 .filter(CongNo.loai == "PHAI_THU", CongNo.trang_thai != "THU_DU").scalar()
    phai_tra = db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0)) \
                 .filter(CongNo.loai == "PHAI_TRA", CongNo.trang_thai != "THU_DU").scalar()
    return {
        "tong_da_thu": float(tong_thu),
        "con_phai_thu": float(phai_thu),
        "con_phai_tra": float(phai_tra),
        "dong_tien_rong_du_kien": float(phai_thu - phai_tra),
    }


@router.get("/thu-tra-chi-tiet")
def thu_tra_chi_tiet(loai: str = "PHAI_THU", db: Session = Depends(get_db),
                     _=Depends(yeu_cau("dashboard", "XEM"))):
    """Chi tiết từng lần ĐÃ THU (khách) / ĐÃ TRẢ (NCC) — khớp đúng số lũy kế trên
    thẻ Overall Financial: ngày, mã hàng, đối tác, số hóa đơn, số tiền."""
    from ..models import KhachHang, NhaCungCap, DonHang, DonMua, HoaDon
    if loai not in ("PHAI_THU", "PHAI_TRA"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "loai phải là PHAI_THU hoặc PHAI_TRA")
    rows = (db.query(ThanhToan, CongNo).join(CongNo, ThanhToan.cong_no_id == CongNo.id)
            .filter(CongNo.loai == loai)
            .order_by(ThanhToan.ngay.desc(), ThanhToan.id.desc()).limit(800).all())
    out = []
    for tt, cn in rows:
        ma = cn.ma_ban_ngoai
        if not ma and cn.don_hang_id:
            dh = db.get(DonHang, cn.don_hang_id)
            ma = dh.so if dh else None
        if not ma and cn.don_mua_id:
            dm = db.get(DonMua, cn.don_mua_id)
            ma = dm.so if dm else None
        if not ma and cn.hoa_don_id:
            hd = db.get(HoaDon, cn.hoa_don_id)
            if hd and hd.don_hang_id:
                dh = db.get(DonHang, hd.don_hang_id)
                ma = dh.so if dh else None
        if loai == "PHAI_THU":
            kh = db.get(KhachHang, cn.khach_hang_id) if cn.khach_hang_id else None
            doi_tac = kh.ten if kh else None
        else:
            nc = db.get(NhaCungCap, cn.nha_cung_cap_id) if cn.nha_cung_cap_id else None
            doi_tac = nc.ten if nc else None
        out.append({"ngay": str(tt.ngay) if tt.ngay else None, "ma": ma,
                    "doi_tac": doi_tac, "so_hd": cn.so_ct,
                    "so_tien": float(tt.so_tien or 0)})
    return {"tong": sum(x["so_tien"] for x in out), "so_dong": len(out), "rows": out}


@router.get("/con-phai-chi-tiet")
def con_phai_chi_tiet(loai: str = "PHAI_THU", db: Session = Depends(get_db),
                      _=Depends(yeu_cau("dashboard", "XEM"))):
    """Chi tiết khoản CÒN PHẢI THU / CÒN PHẢI TRẢ — khớp đúng số trên thẻ
    Overall Financial (cùng công thức với dashboard): ngày, mã hàng, đối tác,
    số HĐ, tổng, đã trả, còn lại, hạn (quá hạn đánh dấu)."""
    from ..models import KhachHang, NhaCungCap, DonHang, DonMua, HoaDon
    if loai not in ("PHAI_THU", "PHAI_TRA"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "loai phải là PHAI_THU hoặc PHAI_TRA")
    hom_nay = date.today()
    rows = (db.query(CongNo).filter(CongNo.loai == loai, CongNo.trang_thai != "THU_DU")
            .order_by(CongNo.id.desc()).limit(1000).all())
    out, tong = [], 0.0
    for cn in rows:
        con = float((cn.so_tien or 0) - (cn.da_thanh_toan or 0))
        tong += con                      # cộng đủ mọi dòng — khớp tuyệt đối công thức thẻ
        if con == 0:
            continue                     # dòng đã trả đủ không cần hiển thị
        ma = cn.ma_ban_ngoai
        ngay = cn.ngay_ct
        if not ma and cn.don_hang_id:
            dh = db.get(DonHang, cn.don_hang_id)
            ma = dh.so if dh else None
        if cn.don_mua_id:
            dm = db.get(DonMua, cn.don_mua_id)
            if dm:
                ma = ma or dm.so
                ngay = ngay or dm.ngay
        if not ma and cn.hoa_don_id:
            hd = db.get(HoaDon, cn.hoa_don_id)
            if hd:
                ngay = ngay or hd.ngay
                if hd.don_hang_id:
                    dh = db.get(DonHang, hd.don_hang_id)
                    ma = dh.so if dh else None
        if loai == "PHAI_THU":
            kh = db.get(KhachHang, cn.khach_hang_id) if cn.khach_hang_id else None
            doi_tac = kh.ten if kh else None
        else:
            nc = db.get(NhaCungCap, cn.nha_cung_cap_id) if cn.nha_cung_cap_id else None
            doi_tac = nc.ten if nc else None
        out.append({"ngay": str(ngay) if ngay else None, "ma": ma, "doi_tac": doi_tac,
                    "so_hd": cn.so_ct, "tong": float(cn.so_tien or 0),
                    "da_tra": float(cn.da_thanh_toan or 0), "con_lai": con,
                    "han": str(cn.han) if cn.han else None,
                    "qua_han": bool(cn.han and con > 0 and cn.han < hom_nay)})
    out.sort(key=lambda x: (x["han"] or "9999-12-31"))
    return {"tong": tong, "so_dong": len(out), "rows": out}


# ============ 🏦 Bank record — sổ thu/chi ngân hàng CEO tự cập nhật ============
from pydantic import BaseModel as _BRBase


class BankRecordVao(_BRBase):
    ngay: date | None = None
    loai: str = "CHI"                 # THU | CHI
    ngan_hang: str | None = None
    dien_giai: str | None = None
    ma_ban: str | None = None
    so_tien: float = 0


def _br_dict(r):
    return {"id": r.id, "ngay": str(r.ngay) if r.ngay else None, "loai": r.loai,
            "ngan_hang": r.ngan_hang, "dien_giai": r.dien_giai, "ma_ban": r.ma_ban,
            "so_tien": float(r.so_tien or 0)}


@router.get("/bank-record")
def ds_bank_record(db: Session = Depends(get_db),
                   nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import BankRecord
    rows = db.query(BankRecord).order_by(BankRecord.ngay.desc(), BankRecord.id.desc()).limit(500).all()
    return [_br_dict(r) for r in rows]


@router.post("/bank-record", status_code=201)
def tao_bank_record(data: BankRecordVao, db: Session = Depends(get_db),
                    nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import BankRecord
    from ..nhac_viec_service import gio_hien_tai
    if data.loai not in ("THU", "CHI"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Loại phải là THU hoặc CHI")
    if not (data.so_tien and data.so_tien > 0):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nhập số tiền lớn hơn 0")
    r = BankRecord(ngay=data.ngay or date.today(), loai=data.loai,
                   ngan_hang=(data.ngan_hang or "").strip()[:60] or None,
                   dien_giai=(data.dien_giai or "").strip()[:300] or None,
                   ma_ban=(data.ma_ban or "").strip()[:60] or None,
                   so_tien=data.so_tien, nguoi_tao=nd.id, tao_luc=gio_hien_tai())
    db.add(r); db.flush()
    ghi_audit(db, nd.id, "TAO", "bank_record", r.id,
              moi={"loai": r.loai, "so_tien": float(r.so_tien), "ngan_hang": r.ngan_hang})
    db.commit()
    return _br_dict(r)


@router.put("/bank-record/{br_id}")
def sua_bank_record(br_id: int, data: BankRecordVao, db: Session = Depends(get_db),
                    nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import BankRecord
    r = db.get(BankRecord, br_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dòng bank record")
    if data.loai not in ("THU", "CHI"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Loại phải là THU hoặc CHI")
    if not (data.so_tien and data.so_tien > 0):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nhập số tiền lớn hơn 0")
    cu = _br_dict(r)
    r.ngay = data.ngay or r.ngay
    r.loai = data.loai
    r.ngan_hang = (data.ngan_hang or "").strip()[:60] or None
    r.dien_giai = (data.dien_giai or "").strip()[:300] or None
    r.ma_ban = (data.ma_ban or "").strip()[:60] or None
    r.so_tien = data.so_tien
    ghi_audit(db, nd.id, "SUA", "bank_record", r.id, cu=cu, moi=_br_dict(r))
    db.commit()
    return _br_dict(r)


@router.delete("/bank-record/{br_id}")
def xoa_bank_record(br_id: int, db: Session = Depends(get_db),
                    nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import BankRecord
    r = db.get(BankRecord, br_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dòng bank record")
    ghi_audit(db, nd.id, "XOA", "bank_record", r.id, cu=_br_dict(r))
    db.delete(r); db.commit()
    return {"ok": True}


# ============ 💼 Số dư ngân hàng + 📅 Lịch dòng tiền dự kiến ============
class BankTkVao(_BRBase):
    ten: str = ""
    so_tk: str | None = None
    so_du_dau: float = 0
    ngay_du_dau: date | None = None
    ghi_chu: str | None = None


class ChiCoDinhVao(_BRBase):
    ten: str = ""
    so_tien: float = 0
    ngay_trong_thang: int = 5
    ghi_chu: str | None = None


def _btk_so_du(db, tk):
    """(tiền vào, tiền ra, số dư) của một tài khoản: khớp Bank record theo tên NH từ ngày đầu kỳ."""
    from ..models import BankRecord
    q = db.query(BankRecord).filter(func.lower(BankRecord.ngan_hang) == (tk.ten or "").strip().lower())
    if tk.ngay_du_dau:
        q = q.filter(BankRecord.ngay >= tk.ngay_du_dau)
    rows = q.all()
    thu = sum(float(r.so_tien or 0) for r in rows if r.loai == "THU")
    chi = sum(float(r.so_tien or 0) for r in rows if r.loai == "CHI")
    return thu, chi, float(tk.so_du_dau or 0) + thu - chi


@router.get("/bank-tai-khoan")
def ds_bank_tk(db: Session = Depends(get_db), nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import BankTaiKhoan, BankRecord
    tks = db.query(BankTaiKhoan).order_by(BankTaiKhoan.id).all()
    ten_set = {(t.ten or "").strip().lower() for t in tks}
    out = []
    for t in tks:
        thu, chi, so_du = _btk_so_du(db, t)
        out.append({"id": t.id, "ten": t.ten, "so_tk": t.so_tk,
                    "so_du_dau": float(t.so_du_dau or 0),
                    "ngay_du_dau": str(t.ngay_du_dau) if t.ngay_du_dau else None,
                    "thu": thu, "chi": chi, "so_du": so_du})
    kk_thu = kk_chi = 0.0
    kk_n = 0
    for r in db.query(BankRecord).all():
        if (r.ngan_hang or "").strip().lower() not in ten_set:
            kk_n += 1
            if r.loai == "THU":
                kk_thu += float(r.so_tien or 0)
            else:
                kk_chi += float(r.so_tien or 0)
    return {"tai_khoan": out, "tong": sum(x["so_du"] for x in out),
            "khong_khop": {"so_dong": kk_n, "thu": kk_thu, "chi": kk_chi}}


@router.post("/bank-tai-khoan", status_code=201)
def tao_bank_tk(data: BankTkVao, db: Session = Depends(get_db),
                nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import BankTaiKhoan
    if not (data.ten or "").strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nhập tên ngân hàng")
    t = BankTaiKhoan(ten=data.ten.strip()[:60], so_tk=(data.so_tk or "").strip()[:40] or None,
                     so_du_dau=data.so_du_dau or 0, ngay_du_dau=data.ngay_du_dau or date.today(),
                     ghi_chu=(data.ghi_chu or "").strip()[:200] or None)
    db.add(t); db.flush()
    ghi_audit(db, nd.id, "TAO", "bank_tai_khoan", t.id, moi={"ten": t.ten, "so_du_dau": float(t.so_du_dau or 0)})
    db.commit()
    return {"id": t.id}


@router.put("/bank-tai-khoan/{tk_id}")
def sua_bank_tk(tk_id: int, data: BankTkVao, db: Session = Depends(get_db),
                nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import BankTaiKhoan
    t = db.get(BankTaiKhoan, tk_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản")
    if not (data.ten or "").strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nhập tên ngân hàng")
    cu = {"ten": t.ten, "so_du_dau": float(t.so_du_dau or 0)}
    t.ten = data.ten.strip()[:60]
    t.so_tk = (data.so_tk or "").strip()[:40] or None
    t.so_du_dau = data.so_du_dau or 0
    t.ngay_du_dau = data.ngay_du_dau or t.ngay_du_dau
    ghi_audit(db, nd.id, "SUA", "bank_tai_khoan", t.id, cu=cu,
              moi={"ten": t.ten, "so_du_dau": float(t.so_du_dau or 0)})
    db.commit()
    return {"ok": True}


@router.delete("/bank-tai-khoan/{tk_id}")
def xoa_bank_tk(tk_id: int, db: Session = Depends(get_db),
                nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import BankTaiKhoan
    t = db.get(BankTaiKhoan, tk_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản")
    ghi_audit(db, nd.id, "XOA", "bank_tai_khoan", t.id, cu={"ten": t.ten})
    db.delete(t); db.commit()
    return {"ok": True}


@router.get("/chi-co-dinh")
def ds_chi_co_dinh(db: Session = Depends(get_db), nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import ChiCoDinh
    return [{"id": c.id, "ten": c.ten, "so_tien": float(c.so_tien or 0),
             "ngay_trong_thang": int(c.ngay_trong_thang or 5), "ghi_chu": c.ghi_chu}
            for c in db.query(ChiCoDinh).filter(ChiCoDinh.dang_ap_dung.is_(True))
                       .order_by(ChiCoDinh.ngay_trong_thang, ChiCoDinh.id).all()]


@router.post("/chi-co-dinh", status_code=201)
def tao_chi_co_dinh(data: ChiCoDinhVao, db: Session = Depends(get_db),
                    nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import ChiCoDinh
    if not (data.ten or "").strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nhập tên khoản chi")
    if not (data.so_tien and data.so_tien > 0):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Số tiền phải lớn hơn 0")
    ng = min(max(int(data.ngay_trong_thang or 5), 1), 28)
    c = ChiCoDinh(ten=data.ten.strip()[:120], so_tien=data.so_tien, ngay_trong_thang=ng,
                  ghi_chu=(data.ghi_chu or "").strip()[:200] or None)
    db.add(c); db.flush()
    ghi_audit(db, nd.id, "TAO", "chi_co_dinh", c.id, moi={"ten": c.ten, "so_tien": float(c.so_tien)})
    db.commit()
    return {"id": c.id}


@router.put("/chi-co-dinh/{cd_id}")
def sua_chi_co_dinh(cd_id: int, data: ChiCoDinhVao, db: Session = Depends(get_db),
                    nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import ChiCoDinh
    c = db.get(ChiCoDinh, cd_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khoản chi")
    if not (data.so_tien and data.so_tien > 0):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Số tiền phải lớn hơn 0")
    cu = {"ten": c.ten, "so_tien": float(c.so_tien or 0)}
    c.ten = (data.ten or c.ten).strip()[:120]
    c.so_tien = data.so_tien
    c.ngay_trong_thang = min(max(int(data.ngay_trong_thang or 5), 1), 28)
    c.ghi_chu = (data.ghi_chu or "").strip()[:200] or None
    ghi_audit(db, nd.id, "SUA", "chi_co_dinh", c.id, cu=cu, moi={"ten": c.ten, "so_tien": float(c.so_tien)})
    db.commit()
    return {"ok": True}


@router.delete("/chi-co-dinh/{cd_id}")
def xoa_chi_co_dinh(cd_id: int, db: Session = Depends(get_db),
                    nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import ChiCoDinh
    c = db.get(ChiCoDinh, cd_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khoản chi")
    ghi_audit(db, nd.id, "XOA", "chi_co_dinh", c.id, cu={"ten": c.ten})
    db.delete(c); db.commit()
    return {"ok": True}


@router.get("/dong-tien-du-kien")
def dong_tien_du_kien(tuan: int = 13, db: Session = Depends(get_db),
                      nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    """Lịch dòng tiền theo tuần: thu = công nợ phải thu theo hạn; chi = công nợ phải
    trả theo hạn + chi cố định hàng tháng; số dư chạy từ tổng Số dư ngân hàng.
    Khoản quá hạn dồn vào tuần hiện tại; khoản không hạn / ngoài kỳ trả về riêng."""
    from datetime import timedelta
    from ..models import BankTaiKhoan, ChiCoDinh
    tuan = max(4, min(26, tuan))
    hom_nay = date.today()
    start = hom_nay - timedelta(days=hom_nay.weekday())
    horizon_end = start + timedelta(weeks=tuan)
    thu = [0.0] * tuan
    chi = [0.0] * tuan
    cod = [0.0] * tuan
    kh_thu = kh_chi = nk_thu = nk_chi = 0.0
    for cn in db.query(CongNo).filter(CongNo.trang_thai != "THU_DU").all():
        con = float((cn.so_tien or 0) - (cn.da_thanh_toan or 0))
        if con <= 0:
            continue
        la_thu = cn.loai == "PHAI_THU"
        if cn.han is None:
            if la_thu:
                kh_thu += con
            else:
                kh_chi += con
            continue
        idx = (cn.han - start).days // 7
        if idx < 0:
            idx = 0                      # quá hạn → dồn tuần hiện tại
        if idx >= tuan:
            if la_thu:
                nk_thu += con
            else:
                nk_chi += con
            continue
        (thu if la_thu else chi)[idx] += con
    for c in db.query(ChiCoDinh).filter(ChiCoDinh.dang_ap_dung.is_(True)).all():
        d = min(int(c.ngay_trong_thang or 5), 28)
        y, m = start.year, start.month
        for _ in range(tuan // 4 + 3):
            ng = date(y, m, d)
            if start <= ng < horizon_end:
                idx = (ng - start).days // 7
                if 0 <= idx < tuan:
                    cod[idx] += float(c.so_tien or 0)
            m += 1
            if m > 12:
                m = 1
                y += 1
    so_du = 0.0
    for t in db.query(BankTaiKhoan).all():
        so_du += _btk_so_du(db, t)[2]
    ra = []
    run = so_du
    for i in range(tuan):
        rong = thu[i] - chi[i] - cod[i]
        run += rong
        ra.append({"bat_dau": str(start + timedelta(weeks=i)),
                   "ket_thuc": str(start + timedelta(weeks=i, days=6)),
                   "thu": thu[i], "chi_cong_no": chi[i], "chi_co_dinh": cod[i],
                   "rong": rong, "so_du": run})
    return {"so_du_dau": so_du, "tuan": ra,
            "khong_han": {"thu": kh_thu, "chi": kh_chi},
            "ngoai_ky": {"thu": nk_thu, "chi": nk_chi}}


# ============ 🧾 Thuế & bắt buộc · 📈 Chỉ số dòng tiền · 🎯 Ngân sách ============
def _thue_thang(db, thang):
    """Ước tính nghĩa vụ của một tháng 'YYYY-MM' từ hóa đơn + bảng lương trong hệ thống."""
    from ..models import HoaDon, BangLuong
    y, m = int(thang[:4]), int(thang[5:7])
    d1 = date(y, m, 1)
    d2 = date(y + (1 if m == 12 else 0), 1 if m == 12 else m + 1, 1)
    hds = db.query(HoaDon).filter(HoaDon.ngay >= d1, HoaDon.ngay < d2).all()
    vat_ra = sum(float(h.tien_thue or 0) for h in hds if h.loai != "MUA")
    vat_vao = sum(float(h.tien_thue or 0) for h in hds if h.loai == "MUA")
    bls = db.query(BangLuong).filter(BangLuong.thang == thang).all()
    bhxh = sum(float((b.bhxh or 0)) + float(b.bhyt or 0) + float(b.bhtn or 0)
               + float(b.bhxh_dn or 0) + float(b.bhyt_dn or 0) + float(b.bhtn_dn or 0)
               + float(b.kpcd_dn or 0) for b in bls)
    tncn = sum(float(b.thue_tncn or 0) for b in bls)
    han = d2.replace(day=20)             # hạn VAT/TNCN: 20 tháng sau
    han_bh = (d2 - __import__("datetime").timedelta(days=1))   # BHXH: cuối tháng phát sinh
    return {"thang": thang, "vat_ra": vat_ra, "vat_vao": vat_vao,
            "vat_nop": max(0.0, vat_ra - vat_vao), "tncn": tncn, "bhxh": bhxh,
            "han_vat": str(han), "han_bhxh": str(han_bh), "so_hd": len(hds), "so_bl": len(bls)}


@router.get("/thue-du-kien")
def thue_du_kien(db: Session = Depends(get_db), nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    hom_nay = date.today()
    thang_nay = hom_nay.strftime("%Y-%m")
    truoc = (hom_nay.replace(day=1) - __import__("datetime").timedelta(days=1)).strftime("%Y-%m")
    return {"ky_truoc": _thue_thang(db, truoc), "ky_nay": _thue_thang(db, thang_nay)}


@router.get("/chi-so-tai-chinh")
def chi_so_tai_chinh(db: Session = Depends(get_db), nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    """DSO/DPO 90 ngày: bình quân bao nhiêu ngày thu được tiền khách / chiếm dụng vốn NCC."""
    from datetime import timedelta
    from ..models import DonHang, DonMua
    moc = date.today() - timedelta(days=90)
    dt90 = float(db.query(func.coalesce(func.sum(DonHang.tong_tien), 0))
                 .filter(DonHang.ngay >= moc).scalar())
    mua90 = float(db.query(func.coalesce(func.sum(DonMua.tong_tien), 0))
                  .filter(DonMua.ngay >= moc).scalar())
    phai_thu = float(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
                     .filter(CongNo.loai == "PHAI_THU", CongNo.trang_thai != "THU_DU").scalar())
    phai_tra = float(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
                     .filter(CongNo.loai == "PHAI_TRA", CongNo.trang_thai != "THU_DU").scalar())
    dso = round(phai_thu / (dt90 / 90), 1) if dt90 > 0 else None
    dpo = round(phai_tra / (mua90 / 90), 1) if mua90 > 0 else None
    return {"dso": dso, "dpo": dpo,
            "chenh": round(dso - dpo, 1) if (dso is not None and dpo is not None) else None,
            "doanh_thu_90": dt90, "mua_90": mua90,
            "phai_thu": phai_thu, "phai_tra": phai_tra}


class NganSachVao(_BRBase):
    thang: str = ""                       # 'YYYY-MM'
    thu_ke_hoach: float = 0
    chi_ke_hoach: float = 0
    ghi_chu: str | None = None


@router.get("/ngan-sach")
def ds_ngan_sach(db: Session = Depends(get_db), nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import NganSach
    out = []
    for ns in db.query(NganSach).order_by(NganSach.thang.desc()).limit(12).all():
        y, m = int(ns.thang[:4]), int(ns.thang[5:7])
        d1 = date(y, m, 1)
        d2 = date(y + (1 if m == 12 else 0), 1 if m == 12 else m + 1, 1)
        thuc_thu = float(db.query(func.coalesce(func.sum(ThanhToan.so_tien), 0))
                         .join(CongNo, ThanhToan.cong_no_id == CongNo.id)
                         .filter(CongNo.loai == "PHAI_THU",
                                 ThanhToan.ngay >= d1, ThanhToan.ngay < d2).scalar())
        thuc_chi = float(db.query(func.coalesce(func.sum(ThanhToan.so_tien), 0))
                         .join(CongNo, ThanhToan.cong_no_id == CongNo.id)
                         .filter(CongNo.loai == "PHAI_TRA",
                                 ThanhToan.ngay >= d1, ThanhToan.ngay < d2).scalar())
        out.append({"id": ns.id, "thang": ns.thang,
                    "thu_ke_hoach": float(ns.thu_ke_hoach or 0),
                    "chi_ke_hoach": float(ns.chi_ke_hoach or 0),
                    "thuc_thu": thuc_thu, "thuc_chi": thuc_chi, "ghi_chu": ns.ghi_chu})
    return out


@router.post("/ngan-sach")
def luu_ngan_sach(data: NganSachVao, db: Session = Depends(get_db),
                  nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import NganSach
    import re as _re
    if not _re.match(r"^\d{4}-\d{2}$", data.thang or ""):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tháng phải dạng YYYY-MM")
    ns = db.query(NganSach).filter_by(thang=data.thang).first()
    if ns is None:
        ns = NganSach(thang=data.thang)
        db.add(ns)
    ns.thu_ke_hoach = data.thu_ke_hoach or 0
    ns.chi_ke_hoach = data.chi_ke_hoach or 0
    ns.ghi_chu = (data.ghi_chu or "").strip()[:200] or None
    db.flush()
    ghi_audit(db, nd.id, "LUU", "ngan_sach", ns.id,
              moi={"thang": ns.thang, "thu": float(ns.thu_ke_hoach), "chi": float(ns.chi_ke_hoach)})
    db.commit()
    return {"id": ns.id}


@router.delete("/ngan-sach/{ns_id}")
def xoa_ngan_sach(ns_id: int, db: Session = Depends(get_db),
                  nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import NganSach
    ns = db.get(NganSach, ns_id)
    if ns is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy ngân sách")
    ghi_audit(db, nd.id, "XOA", "ngan_sach", ns.id, cu={"thang": ns.thang})
    db.delete(ns); db.commit()
    return {"ok": True}


# ============ 📋 Danh mục kê khai VCSH / TSCĐ / Nợ dài hạn ============
_VM_LOAI = {"VCSH", "TSCD", "NO_DH"}


class VonMucVao(_BRBase):
    loai: str = ""
    ten: str = ""
    so_tien: float = 0
    ghi_chu: str | None = None


@router.get("/von-muc")
def ds_von_muc(loai: str = "", db: Session = Depends(get_db),
               _=Depends(yeu_cau(MODULE, "XEM"))):
    from ..models import VonMuc
    q = db.query(VonMuc)
    if loai:
        q = q.filter(VonMuc.loai == loai)
    return [{"id": v.id, "loai": v.loai, "ten": v.ten,
             "so_tien": float(v.so_tien or 0), "ghi_chu": v.ghi_chu}
            for v in q.order_by(VonMuc.id).all()]


@router.post("/von-muc", status_code=201)
def tao_von_muc(data: VonMucVao, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    from ..models import VonMuc
    if data.loai not in _VM_LOAI:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Loại phải là VCSH / TSCD / NO_DH")
    if not (data.ten or "").strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nhập tên mục")
    v = VonMuc(loai=data.loai, ten=data.ten.strip()[:160], so_tien=data.so_tien or 0,
               ghi_chu=(data.ghi_chu or "").strip()[:200] or None)
    db.add(v); db.flush()
    ghi_audit(db, nd.id, "TAO", "von_muc", v.id,
              moi={"loai": v.loai, "ten": v.ten, "so_tien": float(v.so_tien or 0)})
    db.commit()
    return {"id": v.id}


@router.put("/von-muc/{vm_id}")
def sua_von_muc(vm_id: int, data: VonMucVao, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    from ..models import VonMuc
    v = db.get(VonMuc, vm_id)
    if v is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy mục kê khai")
    cu = {"ten": v.ten, "so_tien": float(v.so_tien or 0)}
    if (data.ten or "").strip():
        v.ten = data.ten.strip()[:160]
    v.so_tien = data.so_tien or 0
    v.ghi_chu = (data.ghi_chu or "").strip()[:200] or None
    ghi_audit(db, nd.id, "SUA", "von_muc", v.id, cu=cu,
              moi={"ten": v.ten, "so_tien": float(v.so_tien or 0)})
    db.commit()
    return {"ok": True}


@router.delete("/von-muc/{vm_id}")
def xoa_von_muc(vm_id: int, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    from ..models import VonMuc
    v = db.get(VonMuc, vm_id)
    if v is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy mục kê khai")
    ghi_audit(db, nd.id, "XOA", "von_muc", v.id, cu={"loai": v.loai, "ten": v.ten})
    db.delete(v); db.commit()
    return {"ok": True}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _=Depends(yeu_cau("dashboard", "XEM"))):
    """Tổng quan điều hành — TỔNG HỢP THẬT từ Bán hàng, Mua hàng (NCC), Kho, Công nợ.
    Không nhập liệu trùng: đọc thẳng dữ liệu do các module sinh ra."""
    from ..models import DonHang, DonMua, BaoGia
    hom_nay = date.today()

    # --- Tài chính: tách rõ đã THU (từ khách) vs đã TRẢ (cho NCC) ---
    da_thu = db.query(func.coalesce(func.sum(ThanhToan.so_tien), 0)) \
               .join(CongNo, ThanhToan.cong_no_id == CongNo.id) \
               .filter(CongNo.loai == "PHAI_THU").scalar()
    da_tra = db.query(func.coalesce(func.sum(ThanhToan.so_tien), 0)) \
               .join(CongNo, ThanhToan.cong_no_id == CongNo.id) \
               .filter(CongNo.loai == "PHAI_TRA").scalar()
    phai_thu = db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0)) \
                 .filter(CongNo.loai == "PHAI_THU", CongNo.trang_thai != "THU_DU").scalar()
    phai_tra = db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0)) \
                 .filter(CongNo.loai == "PHAI_TRA", CongNo.trang_thai != "THU_DU").scalar()
    congno_qh = db.query(func.count(CongNo.id)) \
                  .filter(CongNo.loai == "PHAI_THU", CongNo.trang_thai != "THU_DU",
                          CongNo.so_tien - CongNo.da_thanh_toan > 0,
                          CongNo.han.isnot(None), CongNo.han < hom_nay).scalar()

    # --- Bán hàng ---
    bh_so_don = db.query(func.count(DonHang.id)).scalar()
    bh_gia_tri = db.query(func.coalesce(func.sum(DonHang.tong_tien), 0)).scalar()
    bh_chua_xuat = db.query(func.count(DonHang.id)).filter(DonHang.trang_thai != "DA_XUAT").scalar()
    bh_bao_gia_cho = db.query(func.count(BaoGia.id)) \
                       .filter(BaoGia.trang_thai.in_(["NHAP", "CHO_DUYET"])).scalar()

    # --- Mua hàng (NCC) ---
    mh_q = db.query(DonMua).filter(DonMua.trang_thai != "TU_CHOI")
    mh_so_po = mh_q.count()
    mh_gia_tri = db.query(func.coalesce(func.sum(DonMua.tong_tien), 0)) \
                   .filter(DonMua.trang_thai != "TU_CHOI").scalar()
    mh_cho_duyet = db.query(func.count(DonMua.id)).filter(DonMua.trang_thai == "CHO_DUYET").scalar()
    mh_cho_nhan = db.query(func.count(DonMua.id)) \
                    .filter(DonMua.trang_thai == "DA_DUYET", DonMua.trang_thai_nhan != "DU").scalar()

    # --- Kho: hàng dưới tồn tối thiểu ---
    kho_duoi_min = db.query(func.count(TonKho.id)) \
                     .filter(TonKho.ton_min > 0, TonKho.so_luong < TonKho.ton_min).scalar()

    return {
        "tai_chinh": {"da_thu": float(da_thu), "da_tra_ncc": float(da_tra),
                      "con_phai_thu": float(phai_thu), "con_phai_tra": float(phai_tra)},
        "ban_hang": {"so_don": int(bh_so_don), "gia_tri_don": float(bh_gia_tri),
                     "so_don_chua_xuat": int(bh_chua_xuat), "so_bao_gia_cho": int(bh_bao_gia_cho)},
        "mua_hang": {"so_po": int(mh_so_po), "gia_tri_po": float(mh_gia_tri),
                     "so_po_cho_duyet": int(mh_cho_duyet), "so_po_cho_nhan": int(mh_cho_nhan)},
        "kho": {"so_duoi_min": int(kho_duoi_min)},
        "canh_bao": {"congno_qua_han": int(congno_qh)},
    }


@router.get("/daily-remind")
def daily_remind(db: Session = Depends(get_db), _=Depends(yeu_cau("dashboard", "XEM"))):
    """Nhắc việc trong ngày: báo giá mới · mua hàng mới · phiếu chi chờ duyệt ·
    phiếu thu hôm nay · nhắc thu công nợ đến hạn/quá hạn."""
    from ..models import (AuditLog, DonMua, DonHang, PhieuThuChi, BaoGiaForm, KhachHang, NhaCungCap,
                          YeuCauMua, HangHoa, NgayNghiOt, NhanVien, ChienDichEmail, CoHoi, BaoGia)
    hom_nay = date.today()

    def ten_kh(kid):
        k = db.get(KhachHang, kid) if kid else None
        return k.ten if k else None

    # 1) Báo giá mới hôm nay (theo audit TAO bao_gia_form)
    bg = []
    ids_bg = [lg.ban_ghi_id for lg in
              db.query(AuditLog).filter(AuditLog.bang == "bao_gia_form",
                                        AuditLog.hanh_dong == "TAO",
                                        func.date(AuditLog.thoi_gian) == hom_nay).all()
              if lg.ban_ghi_id]
    if ids_bg:
        for b in db.query(BaoGiaForm).filter(BaoGiaForm.id.in_(ids_bg)).all():
            bg.append({"id": b.id, "so": b.so or f"BG-{b.id}",
                       "khach": ten_kh(b.khach_hang_id), "trang_thai": b.trang_thai})

    # 1b) Đơn hàng / PO-HĐ mới hôm nay (đơn hàng bán tạo hôm nay)
    dh = []
    ids_dh = [lg.ban_ghi_id for lg in
              db.query(AuditLog).filter(AuditLog.bang == "don_hang",
                                        AuditLog.hanh_dong == "TAO",
                                        func.date(AuditLog.thoi_gian) == hom_nay).all()
              if lg.ban_ghi_id]
    if ids_dh:
        for o in db.query(DonHang).filter(DonHang.id.in_(ids_dh)).all():
            kh = db.get(KhachHang, o.khach_hang_id)
            dh.append({"id": o.id, "so": o.so or f"DH-{o.id}",
                       "khach": kh.ten if kh else None,
                       "tong_tien": float((o.tong_tien or 0) + (o.tien_thue or 0)),
                       "trang_thai": o.trang_thai})

    # 2) Mua hàng mới hôm nay (đơn mua có ngày = hôm nay)
    mh = []
    for dm in db.query(DonMua).filter(DonMua.ngay == hom_nay).order_by(DonMua.id.desc()).all():
        ncc = db.get(NhaCungCap, dm.nha_cung_cap_id)
        mh.append({"id": dm.id, "so": dm.so or f"PO-{dm.id}",
                   "ncc": ncc.ten if ncc else None,
                   "tong_tien": float(dm.tong_tien or 0), "trang_thai": dm.trang_thai})

    # 3) Phát sinh duyệt chi — phiếu chi đang chờ duyệt
    dc = []
    for p in (db.query(PhieuThuChi).filter(PhieuThuChi.loai == "CHI",
                                           PhieuThuChi.trang_thai == "CHO_DUYET")
              .order_by(PhieuThuChi.id.desc()).limit(50).all()):
        dc.append({"id": p.id, "so": p.so or f"PC-{p.id}",
                   "so_tien": float(p.so_tien or 0), "ngay": str(p.ngay) if p.ngay else None})

    # 4) Phát sinh thu — phiếu thu hôm nay
    th = []
    for p in (db.query(PhieuThuChi).filter(PhieuThuChi.loai == "THU", PhieuThuChi.ngay == hom_nay)
              .order_by(PhieuThuChi.id.desc()).all()):
        th.append({"id": p.id, "so": p.so or f"PT-{p.id}",
                   "so_tien": float(p.so_tien or 0), "trang_thai": p.trang_thai})

    # 5) Work remind — công nợ ĐẾN HẠN / quá hạn: cả PHẢI THU (khách) và PHẢI TRẢ (NCC)
    wr = []
    for cn in (db.query(CongNo).filter(CongNo.loai.in_(["PHAI_THU", "PHAI_TRA"]))
               .order_by(CongNo.id.desc()).limit(600).all()):
        con_lai = float((cn.so_tien or 0) - (cn.da_thanh_toan or 0))
        if con_lai <= 0:
            continue
        moc = cn.ngay_tt_tiep or cn.han
        if not (moc and moc <= hom_nay):
            continue
        if cn.loai == "PHAI_THU":
            doi_tac = ten_kh(cn.khach_hang_id)
            huong = "Phải thu"
        else:
            ncc = db.get(NhaCungCap, cn.nha_cung_cap_id) if cn.nha_cung_cap_id else None
            doi_tac = ncc.ten if ncc else None
            huong = "Phải trả"
        wr.append({"id": cn.id, "doi_tac": doi_tac, "huong": huong,
                   "con_lai": con_lai, "han": str(moc), "qua_han": moc < hom_nay})
    wr.sort(key=lambda x: (x["han"], x["huong"]))

    # 6) VIỆC ĐANG CHỜ XỬ LÝ — nhắc tới khi xong, không giới hạn hôm nay
    dx_cho = []
    for y in db.query(YeuCauMua).filter(YeuCauMua.trang_thai == "MOI").order_by(YeuCauMua.id.desc()).limit(30).all():
        hh = db.get(HangHoa, y.hang_hoa_id)
        dx_cho.append({"id": y.id, "ten_hh": hh.ten if hh else f"HH #{y.hang_hoa_id}",
                       "ngay": str(y.ngay) if y.ngay else None, "ly_do": y.ly_do})

    po_cho = []
    for dm in (db.query(DonMua).filter(DonMua.trang_thai == "CHO_DUYET")
               .order_by(DonMua.id.desc()).limit(30).all()):
        ncc = db.get(NhaCungCap, dm.nha_cung_cap_id)
        po_cho.append({"id": dm.id, "so": dm.so or f"PO-{dm.id}", "ncc": ncc.ten if ncc else None,
                       "tong_tien": float(dm.tong_tien or 0), "trang_thai": "Chờ duyệt"})

    bg_cho = []
    for b in (db.query(BaoGia).filter(BaoGia.trang_thai.in_(["NHAP", "CHO_DUYET"]))
              .order_by(BaoGia.id.desc()).limit(30).all()):
        bg_cho.append({"id": b.id, "so": b.so or f"BG-{b.id}", "khach": ten_kh(b.khach_hang_id),
                       "trang_thai": "Nháp" if b.trang_thai == "NHAP" else "Chờ duyệt"})

    co_hoi = []
    for c in db.query(CoHoi).filter(CoHoi.giai_doan == "MOI").order_by(CoHoi.id.desc()).limit(30).all():
        co_hoi.append({"id": c.id, "so": c.tieu_de or f"CH-{c.id}",
                       "khach": ten_kh(c.khach_hang_id), "trang_thai": "Mới"})

    cd_cho = []
    for c in (db.query(ChienDichEmail).filter(ChienDichEmail.trang_thai == "CHO_DUYET")
              .order_by(ChienDichEmail.id.desc()).limit(30).all()):
        cd_cho.append({"id": c.id, "so": c.ten, "khach": c.tieu_de, "trang_thai": "Chờ duyệt"})

    _ot_types = ("OT_THUONG", "OT_CUOI_TUAN", "OT_LE")
    ot_cho = []
    for r in (db.query(NgayNghiOt).filter(NgayNghiOt.trang_thai == "CHO_DUYET")
              .order_by(NgayNghiOt.ngay.desc()).limit(30).all()):
        nv = db.get(NhanVien, r.nhan_vien_id)
        ot_cho.append({"id": r.id, "nv": nv.ho_ten if nv else f"NV #{r.nhan_vien_id}",
                       "ngay": str(r.ngay), "loai": r.loai, "so_gio": float(r.so_gio or 0)})

    ot_bc = []
    for r in (db.query(NgayNghiOt).filter(NgayNghiOt.trang_thai == "DA_DUYET",
                                          NgayNghiOt.loai.in_(_ot_types),
                                          NgayNghiOt.bc_ot_luc.is_(None),
                                          NgayNghiOt.ngay <= hom_nay)
              .order_by(NgayNghiOt.ngay.desc()).limit(30).all()):
        nv = db.get(NhanVien, r.nhan_vien_id)
        ot_bc.append({"id": r.id, "nv": nv.ho_ten if nv else f"NV #{r.nhan_vien_id}",
                      "ngay": str(r.ngay), "loai": r.loai, "so_gio": float(r.so_gio or 0)})

    muc = [
        # --- Việc đang chờ xử lý (nhắc tới khi xong) ---
        {"key": "dx_cho", "ten": "Đề xuất mua chờ duyệt", "icon": "🛍", "di_toi": "de_xuat",
         "so": len(dx_cho), "items": dx_cho[:30], "cho": True},
        {"key": "po_cho", "ten": "PO chờ duyệt", "icon": "📦", "di_toi": "ncc",
         "so": len(po_cho), "items": po_cho[:30], "cho": True},
        {"key": "bg_cho", "ten": "Báo giá đang xử lý", "icon": "🧮", "di_toi": "ban_hang",
         "so": len(bg_cho), "items": bg_cho[:30], "cho": True},
        {"key": "co_hoi", "ten": "Cơ hội mới cần theo", "icon": "✨", "di_toi": "ban_hang",
         "so": len(co_hoi), "items": co_hoi[:30], "cho": True},
        {"key": "cd_cho", "ten": "Chiến dịch chờ duyệt", "icon": "📣", "di_toi": "ban_hang",
         "so": len(cd_cho), "items": cd_cho[:30], "cho": True},
        {"key": "ot_cho", "ten": "Tăng ca chờ duyệt", "icon": "🕒", "di_toi": "working_time",
         "so": len(ot_cho), "items": ot_cho[:30], "cho": True},
        {"key": "ot_bc", "ten": "Tăng ca chưa báo cáo kết quả", "icon": "⏱", "di_toi": "working_time",
         "so": len(ot_bc), "items": ot_bc[:30], "cho": True},
        # --- Phát sinh trong hôm nay ---
        {"key": "bao_gia", "ten": "Báo giá mới", "icon": "📝", "di_toi": "ban_hang",
         "so": len(bg), "items": bg[:30]},
        {"key": "don_hang", "ten": "Đơn hàng / PO-HĐ mới", "icon": "🧾", "di_toi": "ban_hang",
         "so": len(dh), "items": dh[:30]},
        {"key": "mua_hang", "ten": "Mua hàng mới", "icon": "🛒", "di_toi": "ncc",
         "so": len(mh), "items": mh[:30]},
        {"key": "duyet_chi", "ten": "Phát sinh duyệt chi", "icon": "✅", "di_toi": "ke_toan",
         "so": len(dc), "items": dc[:30]},
        {"key": "thu", "ten": "Phát sinh thu", "icon": "💰", "di_toi": "ke_toan",
         "so": len(th), "items": th[:30]},
        {"key": "work_remind", "ten": "Work remind (nợ khách & NCC đến hạn)", "icon": "🔔",
         "di_toi": None, "so": len(wr), "items": wr[:40]},
    ]
    return {"ngay": str(hom_nay), "muc": muc}


@router.get("/cong-no-qua-han")
def cong_no_qua_han(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    hom_nay = date.today()
    rows = db.query(CongNo).filter(
        CongNo.loai == "PHAI_THU", CongNo.trang_thai != "THU_DU",
        CongNo.han.isnot(None), CongNo.han < hom_nay,
    ).all()
    ds = []
    for cn in rows:
        so_ngay = (hom_nay - cn.han).days
        ds.append({
            "cong_no_id": cn.id, "khach_hang_id": cn.khach_hang_id,
            "con_lai": float(cn.so_tien - cn.da_thanh_toan),
            "qua_han_ngay": so_ngay,
            "canh_bao": "NHẮC NV kinh doanh" if so_ngay > 30 else "Theo dõi",
        })
    return {"hom_nay": str(hom_nay), "so_cong_no_qua_han": len(ds), "danh_sach": ds}


# ============ CHỈ SỐ TÀI CHÍNH DOANH NGHIỆP + CẢNH BÁO ============
def _f(x):
    return float(x or 0)


def _ps_tk(db, tk, no=True, since=None):
    col = ButToan.tk_no if no else ButToan.tk_co
    q = db.query(func.coalesce(func.sum(ButToan.so_tien), 0)).filter(col == tk)
    if since:
        q = q.filter(ButToan.ngay >= since)
    return _f(q.scalar())


def _ps_nhom(db, tks, no=True, since=None):
    col = ButToan.tk_no if no else ButToan.tk_co
    q = db.query(func.coalesce(func.sum(ButToan.so_tien), 0)).filter(col.in_(tks))
    if since:
        q = q.filter(ButToan.ngay >= since)
    return _f(q.scalar())


def tinh_chi_so(db, so_ngay: int = 90):
    today = date.today()
    since = today - timedelta(days=so_ngay)
    days = max(1, so_ngay)

    # --- Số dư thời điểm (stock) ---
    tien = _f(db.query(func.coalesce(func.sum(TaiKhoanQuy.so_du), 0)).scalar())
    phai_thu = _f(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
                  .filter(CongNo.loai == "PHAI_THU", CongNo.trang_thai != "THU_DU").scalar())
    phai_tra = _f(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
                  .filter(CongNo.loai == "PHAI_TRA", CongNo.trang_thai != "DA_TRA").scalar())
    ton_kho = _f(db.query(func.coalesce(func.sum(TonKho.so_luong * HangHoa.gia_ban), 0))
                 .join(HangHoa, HangHoa.id == TonKho.hang_hoa_id).scalar())
    thue_phai_nop = max(0.0, _ps_tk(db, "3331", no=False) - _ps_tk(db, "3331", no=True))

    vay_nh = _f(db.query(func.coalesce(func.sum(KhoanVay.con_lai_goc), 0))
                .filter(KhoanVay.trang_thai == "DANG_VAY", KhoanVay.loai == "NGAN_HAN").scalar())
    vay_dh = _f(db.query(func.coalesce(func.sum(KhoanVay.con_lai_goc), 0))
                .filter(KhoanVay.trang_thai == "DANG_VAY", KhoanVay.loai == "DAI_HAN").scalar())
    tsnh = tien + phai_thu + ton_kho                      # tài sản ngắn hạn (ước tính)
    no_nh = phai_tra + thue_phai_nop + vay_nh             # nợ ngắn hạn (gồm vay ngắn hạn)

    # --- Dòng (flow) trong kỳ so_ngay ---
    doanh_thu = _ps_tk(db, "511", no=False, since=since)
    gia_von = _ps_tk(db, "632", no=True, since=since)
    chi_phi = _ps_nhom(db, ["641", "642", "627"], no=True, since=since)
    ln_gop = doanh_thu - gia_von
    ln_thuan = doanh_thu - gia_von - chi_phi

    # --- Tiền vào/ra trong kỳ (111+112) ---
    tien_vao = _ps_nhom(db, ["111", "112"], no=True, since=since)
    tien_ra = _ps_nhom(db, ["111", "112"], no=False, since=since)
    dong_tien_rong = tien_vao - tien_ra
    chi_thang = tien_ra / (days / 30.0) if tien_ra > 0 else 0.0

    def _ratio(a, b):
        return round(a / b, 2) if b else None

    cs = {
        "ky_so_ngay": so_ngay,
        "tien_mat_va_nh": tien, "phai_thu": phai_thu, "phai_tra": phai_tra,
        "ton_kho": ton_kho, "thue_phai_nop": thue_phai_nop,
        "tai_san_ngan_han": tsnh, "no_ngan_han": no_nh,
        "vay_ngan_han": vay_nh, "vay_dai_han": vay_dh,
        "lai_vay_ky": _ps_tk(db, "635", no=True, since=since),
        # Thanh khoản
        "ty_so_thanh_toan_hien_hanh": _ratio(tsnh, no_nh),
        "ty_so_thanh_toan_nhanh": _ratio(tien + phai_thu, no_nh),
        "ty_so_thanh_toan_tien_mat": _ratio(tien, no_nh),
        # Sinh lời (kỳ)
        "doanh_thu": doanh_thu, "gia_von": gia_von, "chi_phi": chi_phi,
        "loi_nhuan_gop": ln_gop, "loi_nhuan_thuan": ln_thuan,
        "bien_loi_nhuan_gop": round(ln_gop / doanh_thu, 4) if doanh_thu else None,
        "bien_loi_nhuan_thuan": round(ln_thuan / doanh_thu, 4) if doanh_thu else None,
        "ty_le_chi_phi": round(chi_phi / doanh_thu, 4) if doanh_thu else None,
        # Hiệu quả công nợ / tồn kho (quy ngày)
        "ky_thu_tien_bq": round(phai_thu / (doanh_thu / days), 1) if doanh_thu else None,
        "ky_tra_tien_bq": round(phai_tra / (gia_von / days), 1) if gia_von else None,
        "so_ngay_ton_kho": round(ton_kho / (gia_von / days), 1) if gia_von else None,
        # Dòng tiền
        "tien_vao_ky": tien_vao, "tien_ra_ky": tien_ra, "dong_tien_rong_ky": dong_tien_rong,
        "chi_binh_quan_thang": round(chi_thang),
        "so_thang_tien_mat_con_lai": round(tien / chi_thang, 1) if chi_thang > 0 else None,
    }

    # --- Công nợ quá hạn ---
    ar_qh = _f(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
               .filter(CongNo.loai == "PHAI_THU", CongNo.trang_thai != "THU_DU",
                       CongNo.han.isnot(None), CongNo.han < today).scalar())
    ap_qh = _f(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
               .filter(CongNo.loai == "PHAI_TRA", CongNo.trang_thai != "DA_TRA",
                       CongNo.han.isnot(None), CongNo.han < today).scalar())
    cs["phai_thu_qua_han"] = ar_qh
    cs["phai_tra_qua_han"] = ap_qh

    # --- CẢNH BÁO theo ngưỡng ---
    cb = []
    def warn(ma, muc, tieu_de, chi_tiet, goi_y):
        cb.append({"ma": ma, "muc_do": muc, "tieu_de": tieu_de, "chi_tiet": chi_tiet, "goi_y": goi_y})

    cr = cs["ty_so_thanh_toan_hien_hanh"]
    if cr is not None and cr < 1:
        warn("THANH_KHOAN", "CAO", "Thanh khoản ngắn hạn yếu",
             f"Hệ số thanh toán hiện hành {cr:.2f} < 1 — tài sản ngắn hạn không đủ trả nợ ngắn hạn.",
             "Đẩy nhanh thu hồi công nợ, giãn lịch trả NCC, cân nhắc hạn mức tín dụng ngắn hạn.")
    elif cr is not None and cr < 1.5:
        warn("THANH_KHOAN", "TRUNG", "Thanh khoản ở mức trung bình",
             f"Hệ số thanh toán hiện hành {cr:.2f} (khuyến nghị ≥ 1,5).",
             "Theo dõi sát dòng tiền, tránh tăng nợ ngắn hạn.")
    if cs["ty_so_thanh_toan_tien_mat"] is not None and cs["ty_so_thanh_toan_tien_mat"] < 0.2 and no_nh > 0:
        warn("TIEN_MAT", "TRUNG", "Tỷ lệ tiền mặt thấp",
             f"Tiền/nợ ngắn hạn = {cs['ty_so_thanh_toan_tien_mat']:.2f} (< 0,2).",
             "Giữ đệm tiền mặt tối thiểu, ưu tiên thu tiền trước cho hợp đồng mới.")
    rw = cs["so_thang_tien_mat_con_lai"]
    if rw is not None and rw < 2:
        warn("RUNWAY", "CAO", "Tiền mặt sắp cạn",
             f"Theo nhịp chi hiện tại, tiền mặt chỉ đủ ~{rw:.1f} tháng.",
             "Lập kế hoạch dòng tiền 13 tuần, hoãn chi không cấp thiết, tăng thu đặt cọc.")
    if ln_thuan < 0:
        warn("LO", "CAO", "Đang lỗ trong kỳ",
             f"Lợi nhuận thuần kỳ {so_ngay} ngày = {_fmt(ln_thuan)} (âm).",
             "Rà soát giá vốn & chi phí, xem lại định giá hợp đồng, cắt giảm chi phí kém hiệu quả.")
    bg = cs["bien_loi_nhuan_gop"]
    if bg is not None and bg < 0.1:
        warn("BIEN_GOP", "TRUNG", "Biên lợi nhuận gộp mỏng",
             f"Biên lợi nhuận gộp {bg*100:.1f}% (< 10%).",
             "Đàm phán giá mua, tối ưu kỹ thuật/định mức, tăng giá bán ở hợp đồng mới.")
    dso = cs["ky_thu_tien_bq"]
    if dso is not None and dso > 60:
        warn("DSO", "TRUNG", "Khách trả chậm",
             f"Kỳ thu tiền bình quân {dso:.0f} ngày (> 60).",
             "Siết điều khoản thanh toán, thu đặt cọc, áp chính sách chiết khấu thanh toán sớm.")
    if ar_qh > 0:
        warn("AR_QH", "TRUNG", "Có công nợ phải thu quá hạn",
             f"Phải thu quá hạn {_fmt(ar_qh)}.",
             "Phân công nhắc nợ theo tuổi nợ, ưu tiên khoản lớn/lâu nhất.")
    if ap_qh > 0:
        warn("AP_QH", "CAO", "Có công nợ phải trả quá hạn",
             f"Phải trả quá hạn {_fmt(ap_qh)} — rủi ro uy tín & gián đoạn cung ứng.",
             "Thương lượng gia hạn, lên lịch trả ưu tiên theo mức quan trọng của NCC.")
    if dong_tien_rong < 0:
        warn("DONG_TIEN", "TRUNG", "Dòng tiền ròng trong kỳ âm",
             f"Tiền ra nhiều hơn tiền vào {_fmt(-dong_tien_rong)} trong {so_ngay} ngày.",
             "Cân đối lịch thu–chi, ưu tiên thu trước khi cam kết chi lớn.")

    diem = 100 - sum(20 if c["muc_do"] == "CAO" else 8 if c["muc_do"] == "TRUNG" else 3 for c in cb)
    diem = max(0, min(100, diem))
    return {"ngay": str(today), "chi_so": cs, "canh_bao": cb, "diem_suc_khoe": diem}


def _fmt(x):
    return f"{float(x or 0):,.0f}đ"


@router.get("/chi-so")
def chi_so(so_ngay: int = 90, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return tinh_chi_so(db, so_ngay)


@router.post("/tu-van-ai")
def tu_van_ai(so_ngay: int = 90, db: Session = Depends(get_db),
              _=Depends(yeu_cau(MODULE, "XEM"))):
    kq = tinh_chi_so(db, so_ngay)
    tv = tu_van_tai_chinh({"chi_so": kq["chi_so"], "canh_bao": kq["canh_bao"],
                           "diem_suc_khoe": kq["diem_suc_khoe"]})
    return {"ngay": kq["ngay"], "diem_suc_khoe": kq["diem_suc_khoe"], "tu_van": tv}


# ============ THAM SỐ TÀI CHÍNH (khai báo VCSH/TSCĐ/nợ dài hạn/chi cố định) ============
def _lay_tham_so(db):
    ts = db.get(ThamSoTaiChinh, 1)
    if ts is None:
        ts = ThamSoTaiChinh(id=1); db.add(ts); db.commit(); db.refresh(ts)
    return ts


@router.get("/tham-so")
def lay_tham_so(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    ts = _lay_tham_so(db)
    return {"von_chu_so_huu": _f(ts.von_chu_so_huu), "tai_san_co_dinh": _f(ts.tai_san_co_dinh),
            "no_dai_han": _f(ts.no_dai_han), "chi_co_dinh_thang": _f(ts.chi_co_dinh_thang)}


@router.put("/tham-so")
def cap_nhat_tham_so(data: ThamSoTaiChinhVao, db: Session = Depends(get_db),
                     nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    ts = _lay_tham_so(db)
    ts.von_chu_so_huu = data.von_chu_so_huu
    ts.tai_san_co_dinh = data.tai_san_co_dinh
    ts.no_dai_han = data.no_dai_han
    ts.chi_co_dinh_thang = data.chi_co_dinh_thang
    ghi_audit(db, nd.id, "CAP_NHAT", "tham_so_tai_chinh", 1,
              moi={"vcsh": _f(ts.von_chu_so_huu), "tscd": _f(ts.tai_san_co_dinh)})
    db.commit()
    return lay_tham_so(db)


# ============ BẢNG CÂN ĐỐI KẾ TOÁN (rút gọn) + ROA/ROE/ĐÒN BẨY ============
@router.get("/can-doi-ke-toan")
def can_doi_ke_toan(so_ngay: int = 90, db: Session = Depends(get_db),
                    _=Depends(yeu_cau(MODULE, "XEM"))):
    kq = tinh_chi_so(db, so_ngay)
    cs = kq["chi_so"]
    ts = _lay_tham_so(db)
    tien, phai_thu, ton_kho = cs["tien_mat_va_nh"], cs["phai_thu"], cs["ton_kho"]
    tsnh = cs["tai_san_ngan_han"]
    tscd = _f(ts.tai_san_co_dinh)
    tong_ts = tsnh + tscd
    no_nh = cs["no_ngan_han"]            # đã gồm vay ngắn hạn
    no_dh = _f(ts.no_dai_han) + cs.get("vay_dai_han", 0)   # nợ DH khai báo + vay dài hạn
    tong_no = no_nh + no_dh
    vcsh = _f(ts.von_chu_so_huu)
    tong_nv = tong_no + vcsh
    chenh_lech = tong_ts - tong_nv     # phần chưa khớp (LN giữ lại chưa khai báo)

    def _r(a, b):
        return round(a / b, 4) if b else None

    ln_nam = cs["loi_nhuan_thuan"] * 365.0 / max(1, so_ngay)
    chi_so_co_cau = {
        "roa": _r(ln_nam, tong_ts), "roe": _r(ln_nam, vcsh),
        "he_so_no": _r(tong_no, tong_ts), "no_tren_vcsh": _r(tong_no, vcsh),
        "he_so_tu_tai_tro": _r(vcsh, tong_ts), "loi_nhuan_nam_uoc_tinh": round(ln_nam),
    }
    canh_bao = []
    if chi_so_co_cau["he_so_no"] is not None and chi_so_co_cau["he_so_no"] > 0.7:
        canh_bao.append({"muc_do": "CAO", "tieu_de": "Đòn bẩy nợ cao",
                         "chi_tiet": f"Hệ số nợ {chi_so_co_cau['he_so_no']*100:.0f}% (> 70%).",
                         "goi_y": "Giảm vay nợ, tăng vốn chủ, kiểm soát chi phí lãi vay."})
    if vcsh > 0 and chi_so_co_cau["roe"] is not None and chi_so_co_cau["roe"] < 0:
        canh_bao.append({"muc_do": "CAO", "tieu_de": "ROE âm",
                         "chi_tiet": "Vốn chủ đang sinh lời âm.",
                         "goi_y": "Rà soát hiệu quả kinh doanh và cơ cấu chi phí."})
    return {
        "so_ngay": so_ngay,
        "tai_san": {"tien": tien, "phai_thu": phai_thu, "ton_kho": ton_kho,
                    "tai_san_ngan_han": tsnh, "tai_san_co_dinh": tscd, "tong_tai_san": tong_ts},
        "nguon_von": {"no_ngan_han": no_nh, "no_dai_han": no_dh, "tong_no": tong_no,
                      "von_chu_so_huu": vcsh, "tong_nguon_von": tong_nv, "chenh_lech": chenh_lech},
        "chi_so": chi_so_co_cau, "canh_bao": canh_bao,
        "khai_bao_thieu": (vcsh == 0 and tscd == 0),
    }


# ============ DỰ BÁO DÒNG TIỀN 13 TUẦN ============
@router.get("/du-bao-dong-tien")
def du_bao_dong_tien(so_tuan: int = 13, db: Session = Depends(get_db),
                     _=Depends(yeu_cau(MODULE, "XEM"))):
    today = date.today()
    so_tuan = max(1, min(so_tuan, 26))
    ts = _lay_tham_so(db)
    opening = _f(db.query(func.coalesce(func.sum(TaiKhoanQuy.so_du), 0)).scalar())
    weeks = []
    for i in range(so_tuan):
        tu = today + timedelta(days=i * 7)
        weeks.append({"tuan": i + 1, "tu_ngay": str(tu), "den_ngay": str(tu + timedelta(days=6)),
                      "thu": 0.0, "chi": 0.0})

    def bucket(han):
        d = (han - today).days
        return 0 if d < 0 else min(so_tuan - 1, d // 7)

    # Phải thu đến hạn -> dòng tiền vào
    ar = db.query(CongNo).filter(CongNo.loai == "PHAI_THU", CongNo.trang_thai != "THU_DU",
                                 CongNo.han.isnot(None)).all()
    ar_khong_han = _f(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
                      .filter(CongNo.loai == "PHAI_THU", CongNo.trang_thai != "THU_DU",
                              CongNo.han.is_(None)).scalar())
    for cn in ar:
        weeks[bucket(cn.han)]["thu"] += _f(cn.so_tien - cn.da_thanh_toan)
    # Phải trả đến hạn -> dòng tiền ra
    ap = db.query(CongNo).filter(CongNo.loai == "PHAI_TRA", CongNo.trang_thai != "DA_TRA",
                                 CongNo.han.isnot(None)).all()
    ap_khong_han = _f(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
                      .filter(CongNo.loai == "PHAI_TRA", CongNo.trang_thai != "DA_TRA",
                              CongNo.han.is_(None)).scalar())
    for cn in ap:
        weeks[bucket(cn.han)]["chi"] += _f(cn.so_tien - cn.da_thanh_toan)
    # Lịch trả nợ vay (gốc + lãi) chưa trả -> dòng tiền ra theo ngày đến hạn
    no_vay_chua = (db.query(LichTraNo).join(KhoanVay)
                   .filter(LichTraNo.da_tra.is_(False), KhoanVay.trang_thai == "DANG_VAY").all())
    vay_trong_ky = 0.0
    for l in no_vay_chua:
        wi = bucket(l.ngay_den_han)
        if 0 <= wi < so_tuan:
            weeks[wi]["chi"] += _f(l.tong_phai_tra)
            vay_trong_ky += _f(l.tong_phai_tra)
    # Chi phí cố định hằng tuần (lương, thuê...) trải đều
    chi_co_dinh_tuan = round(_f(ts.chi_co_dinh_thang) * 7.0 / 30.0)
    for w in weeks:
        w["chi"] += chi_co_dinh_tuan

    ton = opening
    min_ton = opening
    tuan_thieu_dau = None
    so_tuan_am = 0
    for w in weeks:
        w["rong"] = w["thu"] - w["chi"]
        ton += w["rong"]
        w["ton_cuoi"] = ton
        w["thieu_hut"] = ton < 0
        if ton < min_ton:
            min_ton = ton
        if ton < 0:
            so_tuan_am += 1
            if tuan_thieu_dau is None:
                tuan_thieu_dau = w["tuan"]

    canh_bao = []
    if tuan_thieu_dau is not None:
        canh_bao.append({"muc_do": "CAO", "tieu_de": f"Thiếu hụt tiền mặt từ tuần {tuan_thieu_dau}",
                         "chi_tiet": f"Dự kiến âm quỹ {so_tuan_am} tuần; thấp nhất {min_ton:,.0f}đ.",
                         "goi_y": "Đẩy thu hồi công nợ tới hạn, giãn lịch trả NCC, chuẩn bị hạn mức tín dụng."})
    return {"ngay": str(today), "so_tuan": so_tuan, "opening": opening, "weeks": weeks,
            "min_ton": min_ton, "tuan_thieu_dau": tuan_thieu_dau, "so_tuan_am": so_tuan_am,
            "chi_co_dinh_tuan": chi_co_dinh_tuan, "no_vay_trong_ky": vay_trong_ky,
            "ar_khong_han": ar_khong_han, "ap_khong_han": ap_khong_han, "canh_bao": canh_bao}
