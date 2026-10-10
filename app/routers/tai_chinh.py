"""
Module TÀI CHÍNH — tổng hợp dòng tiền & công nợ quá hạn (cảnh báo tự động).
Đọc dữ liệu do Kế toán/Bán hàng sinh ra; không nhập liệu trùng.
"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
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
    from ..models import BankTaiKhoan, ChiCoDinh, DonMua as _UtDm2
    tuan = max(4, min(26, tuan))
    hom_nay = date.today()
    start = hom_nay - timedelta(days=hom_nay.weekday())
    horizon_end = start + timedelta(weeks=tuan)
    thu = [0.0] * tuan
    chi = [0.0] * tuan
    cod = [0.0] * tuan
    thu_ut = [0.0] * tuan
    chi_ut = [0.0] * tuan
    kh_thu = kh_chi = nk_thu = nk_chi = 0.0
    for cn in db.query(CongNo).filter(CongNo.trang_thai != "THU_DU").all():
        con = float((cn.so_tien or 0) - (cn.da_thanh_toan or 0))
        if con <= 0:
            continue
        la_thu = cn.loai == "PHAI_THU"
        if cn.han is None:
            # Hạn ƯỚC TÍNH = ngày chứng từ / nhận hàng + 30 ngày — vào lịch RIÊNG (uoc_tinh)
            goc = cn.ngay_ct
            if goc is None and getattr(cn, "don_mua_id", None):
                _dm = db.get(_UtDm2, cn.don_mua_id)
                if _dm is not None:
                    goc = _dm.ngay_giao_thuc or _dm.ngay
            han_ut = (goc or hom_nay) + timedelta(days=30)
            iu = (han_ut - start).days // 7
            if iu < 0:
                iu = 0
            if iu >= tuan:
                iu = tuan - 1                    # xa hơn kỳ → dồn tuần cuối
            (thu_ut if la_thu else chi_ut)[iu] += con
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
    ut_ra = [{"bat_dau": ra[i]["bat_dau"], "ket_thuc": ra[i]["ket_thuc"],
              "thu": thu_ut[i], "chi": chi_ut[i], "rong": thu_ut[i] - chi_ut[i]}
             for i in range(tuan)]
    return {"so_du_dau": so_du, "tuan": ra,
            "khong_han": {"thu": kh_thu, "chi": kh_chi},
            "ngoai_ky": {"thu": nk_thu, "chi": nk_chi},
            "uoc_tinh": {"tuan": ut_ra, "tong_thu": sum(thu_ut), "tong_chi": sum(chi_ut)}}


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
    # doanh thu GỒM VAT — cùng cơ sở với công nợ phải thu (hóa đơn gồm VAT)
    dt90 = float(db.query(func.coalesce(func.sum(DonHang.tong_tien + func.coalesce(DonHang.tien_thue, 0)), 0))
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
                nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT"))):
    from ..models import VonMuc
    v = db.get(VonMuc, vm_id)
    if v is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy mục kê khai")
    ghi_audit(db, nd.id, "XOA", "von_muc", v.id, cu={"loai": v.loai, "ten": v.ten})
    db.delete(v); db.commit()
    return {"ok": True}


@router.post("/financial-snapshot")
def chup_financial(db: Session = Depends(get_db), nd=Depends(chi_vai_tro("CEO", "ADMIN"))):
    """CEO bấm chụp thủ công một bản snapshot Financial ngay bây giờ (bỏ qua giãn cách)."""
    from ..fin_snapshot import snapshot_financial
    t = snapshot_financial(db, "THU CONG")
    if t is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Không chụp được snapshot")
    ghi_audit(db, nd.id, "SNAPSHOT", "fin_ceo", 0, moi={"tep": t.ten_file})
    db.commit()
    return {"ok": True, "tep": t.ten_file}


def _chi_nhan_su_nam(db, hom_nay) -> dict:
    """👥 CHI PHÍ NHÂN SỰ lũy kế từ đầu năm tới tháng hiện tại (mig 142 — anh Hiếu chọn tính CẢ bảng lương chờ duyệt):
    · bảng lương từng tháng = chi_phi_dn (tổng thu nhập + BHXH/BHYT/BHTN + KPCĐ phần DN — đúng số bút toán Nợ 642);
      bảng chưa DA_DUYET = «tạm tính»
    · thuê ngoài ĐÃ CHI = thu nhập + khoản khác, xếp theo kỳ YYYY-MM (thiếu kỳ → ngày chi)
    · tháng CHƯA có bảng lương → DỰ PHÒNG = tổng khoản Chi cố định có chữ «lương»; tháng có bảng lương không cộng
      khoản này (không tính 2 lần) — Chi phí khác cũng đã trừ khoản «lương» ra."""
    import unicodedata
    from ..models import BangLuong, ThanhToanThueNgoai, ChiCoDinh

    def _kd(s):
        s = unicodedata.normalize("NFD", str(s or ""))
        return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d").replace("Đ", "D").lower()

    nam, thang_hien = hom_nay.year, hom_nay.month
    thangs = [f"{nam}-{m:02d}" for m in range(1, thang_hien + 1)]
    luong = {t: {"chi_phi_dn": 0.0, "so_nv": 0, "cho_duyet": 0} for t in thangs}
    for bl in db.query(BangLuong).filter(BangLuong.thang.in_(thangs)).all():
        g = luong.get(str(bl.thang))
        if g is None:
            continue
        cp = float(bl.chi_phi_dn or 0)
        if cp <= 0:          # bản ghi cũ chưa lưu chi_phi_dn → tính lại đúng như bút toán lương
            cp = (float(bl.luong_thuc_te or bl.luong_co_ban or 0) + float(bl.phu_cap or 0) + float(bl.ot or 0)
                  + float(bl.bhxh_dn or 0) + float(bl.bhyt_dn or 0) + float(bl.bhtn_dn or 0)
                  + float(getattr(bl, "kpcd_dn", 0) or 0))
        g["chi_phi_dn"] += cp
        g["so_nv"] += 1
        if bl.trang_thai != "DA_DUYET":
            g["cho_duyet"] += 1
    tn = {t: 0.0 for t in thangs}
    for t in db.query(ThanhToanThueNgoai).filter(ThanhToanThueNgoai.trang_thai == "DA_CHI").all():
        k = str(t.ky or "")[:7]
        if k not in tn:
            k = str(t.ngay_chi or t.ngay or "")[:7]
        if k in tn:
            tn[k] += float(t.thu_nhap or 0) + float(t.khoan_khac or 0)
    cd_luong = float(sum(float(c.so_tien or 0)
                         for c in db.query(ChiCoDinh).filter(ChiCoDinh.dang_ap_dung.is_(True)).all()
                         if "luong" in _kd(c.ten)))
    theo_thang = []
    for t in thangs:
        l = luong[t]
        du_phong = cd_luong if (l["so_nv"] == 0 and cd_luong > 0) else 0.0
        theo_thang.append({"thang": t, "luong": l["chi_phi_dn"], "so_nv": l["so_nv"], "cho_duyet": l["cho_duyet"],
                           "thue_ngoai": tn[t], "du_phong": du_phong, "tong": l["chi_phi_dn"] + tn[t] + du_phong})
    return {"tong": sum(x["tong"] for x in theo_thang),
            "luong": sum(x["luong"] for x in theo_thang),
            "thue_ngoai": sum(x["thue_ngoai"] for x in theo_thang),
            "du_phong": sum(x["du_phong"] for x in theo_thang),
            "so_thang_luong": sum(1 for x in theo_thang if x["so_nv"]),
            "so_thang_cho_duyet": sum(1 for x in theo_thang if x["cho_duyet"]),
            "so_thang_thieu": sum(1 for x in theo_thang if not x["so_nv"]),
            "cd_luong_thang": cd_luong, "theo_thang": theo_thang}


def _tinh_lai_lo_tong(db: Session) -> dict:
    """Lãi/lỗ tổng: doanh thu & chi phí TỪNG MÃ đơn hàng bán (cùng công thức bảng
    Chi phí theo Mã bên Kiểm soát) + chi phí khác = chi cố định/tháng x số tháng từ đầu năm."""
    from sqlalchemy import func
    from ..models import DonHang, DonMua, CongNo, ChiCoDinh
    from ..nhac_viec_service import gio_hien_tai
    from ..lai_lo_ma import chi_phi_ma, nhom_ma, chi_phi_ngoai_ma, gom_theo_nhom   # CÔNG THỨC CHUNG (app/lai_lo_ma.py)
    theo_ma, tong_dt, tong_cp = [], 0.0, 0.0
    for dh in db.query(DonHang).order_by(DonHang.id.desc()).all():
        cp = chi_phi_ma(db, dh)
        doanh_thu = cp["doanh_thu"]          # GỒM VAT — cùng cơ sở với chi phí
        chi_phi = cp["tong_chi_phi"]         # PO đã duyệt + nhập ngoài + hóa đơn mua ngoài PO gắn mã
        if cp.get("la_dau_tu"):              # 🏗 đơn ĐẦU TƯ – cho thuê: vốn đầu tư, không vào doanh thu / chi phí theo mã
            theo_ma.append({"don_hang_id": dh.id, "ma_ban": dh.so or f"DH-{dh.id}", "nhom": nhom_ma(dh.so),
                            "doanh_thu": 0.0, "tong_chi_phi": 0.0, "loi_nhuan": 0.0, "ty_suat": None,
                            "la_dau_tu": True, "von_dau_tu": cp["von_dau_tu"], "gia_tri_hd": cp["gia_tri_hd"],
                            "tai_san_cho_thue_id": cp.get("tai_san_cho_thue_id")})
            continue
        if doanh_thu == 0 and chi_phi == 0:
            continue
        tong_dt += doanh_thu
        tong_cp += chi_phi
        theo_ma.append({"don_hang_id": dh.id, "ma_ban": dh.so or f"DH-{dh.id}",
                        "nhom": nhom_ma(dh.so),
                        "doanh_thu": doanh_thu, "tong_chi_phi": chi_phi,
                        "loi_nhuan": doanh_thu - chi_phi,
                        "ty_suat": round((doanh_thu - chi_phi) / doanh_thu * 100, 1)
                                   if doanh_thu else None})
    hom_nay = gio_hien_tai().date()
    ns = _chi_nhan_su_nam(db, hom_nay)             # 👥 mig 142: lương (kể cả chờ duyệt) + thuê ngoài đã chi + dự phòng «lương»
    chi_nhan_su = ns["tong"]
    chi_thang_all = float(db.query(func.coalesce(func.sum(ChiCoDinh.so_tien), 0))
                          .filter(ChiCoDinh.dang_ap_dung.is_(True)).scalar() or 0)
    chi_thang = max(chi_thang_all - ns["cd_luong_thang"], 0.0)   # chi cố định KHÔNG gồm khoản «lương» (đã tính ở nhân sự)
    chi_khac = chi_thang * hom_nay.month          # lũy kế từ đầu năm, tính trọn tháng hiện tại
    # 🧾 CHI PHÍ HÓA ĐƠN MUA NGOÀI PO (ghi qua Kế toán: email / nhập tay) — trước đây bị bỏ sót
    from ..models import HoaDon
    po_cn_hd = {h for (h,) in db.query(CongNo.hoa_don_id)
                .filter(CongNo.don_mua_id.isnot(None), CongNo.hoa_don_id.isnot(None)).all()}
    chi_hd_mua = 0.0
    from ..lai_lo_ma import po_trung_khoan as _po_trung
    _pos_all = db.query(DonMua).filter(DonMua.trang_thai != "TU_CHOI").all()
    _po_khop = set()
    for hd0 in db.query(HoaDon).filter(HoaDon.loai == "MUA", HoaDon.don_hang_id.is_(None)).all():
        # chỉ hóa đơn KHÔNG gắn mã (hóa đơn gắn mã đã nằm trong chi phí theo mã ở trên)
        # bỏ hóa đơn tự sinh khi nhận hàng PO — chi phí PO đã tính ở trên
        if hd0.id in po_cn_hd or str(hd0.dien_giai or "").startswith("Nhận hàng PO"):
            continue
        # 🔁 hóa đơn nhập trực tiếp ở Kế toán mà chính là một PO (cùng số HĐ / NCC / số tiền) → không cộng lần 2
        _p = _po_trung(_pos_all, hd0.so, hd0.nha_cung_cap_id, hd0.tong_tien, hd0.tien_truoc_thue, _po_khop)
        if _p is not None:
            chi_hd_mua += max(float(hd0.tong_tien or 0) - float(_p.tong_tien or 0), 0.0)
            continue
        chi_hd_mua += float(hd0.tong_tien or 0)
    # ⚙️ CHI PHÍ VẬN HÀNH (mã OP-…): PO đã duyệt mang mã OP nhưng KHÔNG có đơn hàng bán cùng số —
    # chi phí doanh nghiệp, tách dòng riêng (không nằm trong lãi/lỗ theo mã bán hàng).
    # 🧩 và CHƯA PHÂN MÃ: khoản chi không mang mã (không vào được Lãi/Lỗ của mã nào)
    #    · KHO: mua dự trữ → tồn kho (tài sản), theo dõi riêng, KHÔNG trừ vào lãi/lỗ
    #    · MÃ LẺ: mã chưa có đơn bán trong app → vẫn hiện thành dòng riêng ở bảng theo mã
    _ngoai = chi_phi_ngoai_ma(db)          # cùng một hàm với Kiểm soát → hai nơi ra cùng số
    chi_op, chi_chua_ma, chi_kho = _ngoai["chi_op"], _ngoai["chi_chua_ma"], _ngoai["chi_kho"]
    ma_le = _ngoai["ma_le"]
    for k, g in sorted(ma_le.items(), key=lambda x: -x[1]["chi"]):
        tong_cp += g["chi"]
        theo_ma.append({"don_hang_id": None, "ma_ban": g["ma"], "nhom": nhom_ma(g["ma"]),
                        "doanh_thu": 0.0,
                        "tong_chi_phi": g["chi"], "loi_nhuan": -g["chi"], "ty_suat": None,
                        "chua_co_don_ban": True})
    lai_gop = tong_dt - tong_cp
    # 🏗 ĐẦU TƯ – CHO THUÊ: vốn đầu tư là TÀI SẢN; chỉ KHẤU HAO lũy kế (theo thời gian hợp đồng) mới là chi phí
    from ..dau_tu_cho_thue import tong_hop as _dt_tong_hop
    _dtct = _dt_tong_hop(db, hom_nay)
    khau_hao_ct = _dtct["tong"]["kh_luy_ke"]
    return {"dau_tu_cho_thue": {"tong": _dtct["tong"], "so_du_an": len([x for x in _dtct["du_an"] if x["von_dau_tu"] > 0]),
                                "so_nghi": len(_dtct["nghi_dau_tu"]), "so_chua_noi": len(_dtct["don_dau_tu_chua_noi"])},
            "khau_hao_cho_thue": khau_hao_ct,
            "doanh_thu": tong_dt, "chi_phi_don": tong_cp, "lai_gop": lai_gop,
            "chi_thang": chi_thang, "chi_thang_all": chi_thang_all, "chi_phi_khac": chi_khac,
            "chi_nhan_su": chi_nhan_su, "nhan_su": ns,
            "chi_phi_hd_mua": chi_hd_mua,
            "chi_phi_op": chi_op, "chi_chua_ma": chi_chua_ma, "chi_kho": chi_kho,
            "so_ma_le": len(ma_le),
            "lai_lo": lai_gop - chi_nhan_su - chi_khac - chi_hd_mua - chi_op - chi_chua_ma - khau_hao_ct,
            "theo_ma": theo_ma, "theo_nhom": gom_theo_nhom(theo_ma), "ngay": str(hom_nay)}


def luu_lai_lo_hom_nay(db: Session) -> dict:
    """Ghi/cập nhật bản ghi Lãi/Lỗ của HÔM NAY (giờ VN) — gọi từ scheduler mỗi giờ
    và mỗi lần mở panel; bản ghi ngày cuối tháng chính là record chốt tháng."""
    from ..models import LaiLoRecord
    from ..nhac_viec_service import gio_hien_tai
    t = _tinh_lai_lo_tong(db)
    hom_nay = gio_hien_tai().date()
    r = db.query(LaiLoRecord).filter_by(ngay=hom_nay).first()
    if r is None:
        r = LaiLoRecord(ngay=hom_nay)
        db.add(r)
    r.doanh_thu = t["doanh_thu"]
    r.chi_phi_don = t["chi_phi_don"]
    r.lai_gop = t["lai_gop"]
    r.chi_phi_khac = t["chi_phi_khac"]
    r.chi_nhan_su = t["chi_nhan_su"]
    r.lai_lo = t["lai_lo"]
    r.tao_luc = gio_hien_tai()
    return t


@router.get("/lai-lo-record")
def lai_lo_record(db: Session = Depends(get_db), nd_xem=Depends(yeu_cau(MODULE, "XEM"))):
    """Lãi/Lỗ Record 3 phần: ① theo ngày · ② theo mã đơn hàng · ③ chốt cuối tháng."""
    from ..models import LaiLoRecord
    from ..nhac_viec_service import gio_hien_tai
    t = _tinh_lai_lo_tong(db)     # CHỈ ĐỌC — bản ghi theo ngày do scheduler tự lưu mỗi giờ
    rows = db.query(LaiLoRecord).order_by(LaiLoRecord.ngay.desc()).limit(400).all()
    ser = lambda r: {"ngay": str(r.ngay), "doanh_thu": float(r.doanh_thu or 0),
                     "chi_phi_don": float(r.chi_phi_don or 0), "lai_gop": float(r.lai_gop or 0),
                     "chi_phi_khac": float(r.chi_phi_khac or 0), "lai_lo": float(r.lai_lo or 0),
                     "chi_nhan_su": float(getattr(r, "chi_nhan_su", 0) or 0)}
    theo_ngay = [ser(r) for r in rows]
    thang = {}
    for r in sorted(rows, key=lambda x: str(x.ngay)):     # bản ghi MUỘN NHẤT của mỗi tháng
        thang[str(r.ngay)[:7]] = ser(r)
    thang_nay = str(gio_hien_tai().date())[:7]
    theo_thang = [dict(v, thang=k, tam_tinh=(k == thang_nay))
                  for k, v in sorted(thang.items(), reverse=True)]
    theo_ma = t.pop("theo_ma")
    theo_nhom = t.pop("theo_nhom", [])
    if nd_xem.vai_tro.ma != "CEO":               # 🔒 số vốn đầu tư cho thuê: CHỈ CEO (khấu hao vẫn nằm trong LÃI/LỖ)
        t.pop("dau_tu_cho_thue", None)
        for x in theo_ma:
            if x.get("la_dau_tu"):
                x["von_dau_tu"] = None
                x["gia_tri_hd"] = None
    return {"tong": t, "theo_ngay": theo_ngay, "theo_ma": theo_ma, "theo_nhom": theo_nhom,
            "theo_thang": theo_thang}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _=Depends(yeu_cau("dashboard", "XEM"))):
    """Tổng quan điều hành — TỔNG HỢP THẬT từ Bán hàng, Mua hàng (NCC), Kho, Công nợ.
    Không nhập liệu trùng: đọc thẳng dữ liệu do các module sinh ra."""
    from ..models import DonHang, DonMua, BaoGia
    hom_nay = date.today()

    # --- Tài chính: tách rõ đã THU (từ khách) vs đã TRẢ (cho NCC) ---
    # ĐÃ THU / ĐÃ TRẢ đọc từ CHÍNH CÔNG NỢ — gồm mọi đường tiền (💳, phiếu thu-chi
    # cấn công nợ, cấn trừ tạm ứng); đếm theo bảng ThanhToan bị thiếu vì các đường
    # sau không tạo bản ghi ThanhToan.
    da_thu = db.query(func.coalesce(func.sum(CongNo.da_thanh_toan), 0)) \
               .filter(CongNo.loai == "PHAI_THU").scalar()
    da_tra = db.query(func.coalesce(func.sum(CongNo.da_thanh_toan), 0)) \
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

    # --- 💵 Đã tạm ứng mua hàng: đã trả tiền NCC nhưng chưa nhận hàng & chưa có hóa đơn ---
    from ..tam_ung_mua import tam_ung_mua_hang
    try:
        _tu = tam_ung_mua_hang(db)
    except Exception:
        _tu = {"tong": 0, "so_po": 0, "so_phieu": 0, "so_tre_giao": 0}

    # --- Kho: hàng dưới tồn tối thiểu ---
    kho_duoi_min = db.query(func.count(TonKho.id)) \
                     .filter(TonKho.ton_min > 0, TonKho.so_luong < TonKho.ton_min).scalar()

    return {
        "tai_chinh": {"da_thu": float(da_thu), "da_tra_ncc": float(da_tra),
                      "con_phai_thu": float(phai_thu), "con_phai_tra": float(phai_tra)},
        "ban_hang": {"so_don": int(bh_so_don), "gia_tri_don": float(bh_gia_tri),
                     "so_don_chua_xuat": int(bh_chua_xuat), "so_bao_gia_cho": int(bh_bao_gia_cho)},
        "mua_hang": {"so_po": int(mh_so_po), "gia_tri_po": float(mh_gia_tri),
                     "so_po_cho_duyet": int(mh_cho_duyet), "so_po_cho_nhan": int(mh_cho_nhan),
                     "tam_ung_mua": float(_tu["tong"]), "so_po_tam_ung": int(_tu["so_po"]),
                     "so_phieu_tam_ung": int(_tu["so_phieu"]),
                     "so_tam_ung_tre_giao": int(_tu["so_tre_giao"])},
        "kho": {"so_duoi_min": int(kho_duoi_min)},
        "canh_bao": {"congno_qua_han": int(congno_qh)},
    }


@router.get("/tam-ung-mua-hang")
def ds_tam_ung_mua_hang(db: Session = Depends(get_db), _=Depends(yeu_cau("dashboard", "XEM"))):
    """💵 Danh mục ĐÃ TẠM ỨNG MUA HÀNG: PO đã trả tiền nhưng chưa nhận hàng & chưa có hóa đơn
    + phiếu chi tạm ứng NCC chưa cấn trừ (bấm thẻ trên Overall Financial)."""
    from ..tam_ung_mua import tam_ung_mua_hang
    return tam_ung_mua_hang(db)


@router.get("/daily-remind")
def daily_remind(db: Session = Depends(get_db), _=Depends(yeu_cau("dashboard", "XEM"))):
    """Nhắc việc trong ngày: báo giá mới · mua hàng mới · phiếu chi chờ duyệt ·
    phiếu thu hôm nay · nhắc thu công nợ đến hạn/quá hạn."""
    from ..models import (AuditLog, DonMua, DonHang, PhieuThuChi, BaoGiaForm, KhachHang, NhaCungCap,
                          HangHoa, NgayNghiOt, NhanVien, ChienDichEmail, CoHoi, BaoGia)
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

    # ƯỚC TÍNH RIÊNG cho khoản CHƯA có hạn: hạn tạm = ngày chứng từ / nhận hàng + 30 ngày.
    # Trả thành bảng riêng (uoc_tinh) — KHÔNG cộng vào weeks chính.
    from ..models import DonMua as _UtDm
    ut = [{"tuan": i + 1, "tu_ngay": weeks[i]["tu_ngay"], "den_ngay": weeks[i]["den_ngay"],
           "thu": 0.0, "chi": 0.0} for i in range(so_tuan)]
    ut_thu = ut_chi = 0.0
    for cn in db.query(CongNo).filter(CongNo.han.is_(None)).all():
        if cn.loai == "PHAI_THU" and cn.trang_thai == "THU_DU":
            continue
        if cn.loai == "PHAI_TRA" and cn.trang_thai == "DA_TRA":
            continue
        con = _f((cn.so_tien or 0) - (cn.da_thanh_toan or 0))
        if con <= 0:
            continue
        goc = cn.ngay_ct
        if goc is None and getattr(cn, "don_mua_id", None):
            _dm = db.get(_UtDm, cn.don_mua_id)
            if _dm is not None:
                goc = _dm.ngay_giao_thuc or _dm.ngay
        han_ut = (goc or today) + timedelta(days=30)
        wi = bucket(han_ut)                      # hạn ước tính xa hơn kỳ → dồn tuần cuối
        if cn.loai == "PHAI_THU":
            ut[wi]["thu"] += con; ut_thu += con
        else:
            ut[wi]["chi"] += con; ut_chi += con
    for u in ut:
        u["rong"] = u["thu"] - u["chi"]
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
            "ar_khong_han": ar_khong_han, "ap_khong_han": ap_khong_han,
            "uoc_tinh": {"weeks": ut, "tong_thu": ut_thu, "tong_chi": ut_chi}, "canh_bao": canh_bao}


# ============ 🧾 ĐỐI SOÁT SAO KÊ NGÂN HÀNG ============
def _ske_so(v):
    """Ép số AI trả về thành Decimal không âm."""
    from decimal import Decimal as _D
    try:
        d = _D(str(int(float(str(v).replace(",", "").replace(".", "")
                             if isinstance(v, str) else v))))
        return d if d > 0 else _D(0)
    except Exception:
        return _D(0)


def _ung_vien_sao_ke(db: Session, tu: date, den: date) -> list[dict]:
    """Gom ứng viên đối soát từ 4 nguồn trong khoảng ngày [tu, den]:
    ① phiếu thu-chi kế toán ĐÃ DUYỆT qua quỹ NGÂN HÀNG · ② thu công nợ BÁN HÀNG
    ③ lệnh Duyệt chi Ngân hàng ĐÃ CHI (NCC) · ④ Bank record CEO tự ghi."""
    from ..models import (PhieuThuChi, LenhChiBank, BankRecord, DonMua, NhaCungCap)
    ung = []
    quy_nh = {q.id for q in db.query(TaiKhoanQuy).filter(TaiKhoanQuy.loai == "NGAN_HANG").all()}
    for p in db.query(PhieuThuChi).filter(PhieuThuChi.trang_thai == "DA_DUYET",
                                          PhieuThuChi.ngay >= tu, PhieuThuChi.ngay <= den).all():
        if p.quy_id not in quy_nh:
            continue
        ung.append({"loai": "PHIEU", "id": p.id, "ngay": p.ngay,
                    "so_tien": float(p.so_tien or 0),
                    "chieu": "VAO" if p.loai == "THU" else "RA",
                    "mo_ta": f"Phiếu {p.so or p.id} — {(p.dien_giai or '')[:60]}"})
    for tt, cn in (db.query(ThanhToan, CongNo).join(CongNo, ThanhToan.cong_no_id == CongNo.id)
                   .filter(CongNo.loai == "PHAI_THU",
                           ThanhToan.ngay >= tu, ThanhToan.ngay <= den).all()):
        ung.append({"loai": "THU_CN_BAN", "id": tt.id, "ngay": tt.ngay,
                    "so_tien": float(tt.so_tien or 0), "chieu": "VAO",
                    "mo_ta": f"Thu công nợ bán hàng #CN{cn.id}"
                             + (f" — HĐ {cn.so_ct}" if cn.so_ct else "")})
    from ..models import LenhChiBank as _LCB2
    for r in db.query(_LCB2).filter(_LCB2.trang_thai == "DA_CHI").all():
        ng = r.ngay_tt or (r.chi_luc.date() if r.chi_luc else None)
        if ng is None or ng < tu or ng > den:
            continue
        mo_ta = "Duyệt chi NCC"
        if r.don_mua_id:
            dm0 = db.get(DonMua, r.don_mua_id)
            nc0 = db.get(NhaCungCap, dm0.nha_cung_cap_id) if dm0 else None
            mo_ta = f"Duyệt chi PO {dm0.so if dm0 else r.don_mua_id}" + (f" — {nc0.ten[:40]}" if nc0 else "")
        elif r.cong_no_id:
            cn0 = db.get(CongNo, r.cong_no_id)
            nc0 = db.get(NhaCungCap, cn0.nha_cung_cap_id) if (cn0 and cn0.nha_cung_cap_id) else None
            mo_ta = f"Duyệt chi công nợ #CN{r.cong_no_id}" + (f" — {nc0.ten[:40]}" if nc0 else "")
        ung.append({"loai": "LENH_CHI", "id": r.id, "ngay": ng,
                    "so_tien": float(r.so_tien or 0), "chieu": "RA", "mo_ta": mo_ta})
    from ..models import BankRecord as _BR2
    for b in db.query(_BR2).filter(_BR2.ngay >= tu, _BR2.ngay <= den).all():
        ung.append({"loai": "BANK_REC", "id": b.id, "ngay": b.ngay,
                    "so_tien": float(b.so_tien or 0),
                    "chieu": "VAO" if b.loai == "THU" else "RA",
                    "mo_ta": f"Bank record — {(b.dien_giai or '')[:60]}"})
    return ung


def _thieu_tren_sao_ke(sk, ung, da_dung):
    """Khoản có trong app (đúng kỳ sao kê) nhưng KHÔNG khớp dòng sao kê nào."""
    thieu = [u for u in ung
             if (u["loai"], u["id"]) not in da_dung and u["ngay"] is not None
             and sk.tu_ngay and sk.den_ngay and sk.tu_ngay <= u["ngay"] <= sk.den_ngay]
    thieu.sort(key=lambda x: str(x["ngay"]))
    return [{"loai": u["loai"], "ngay": str(u["ngay"]), "so_tien": u["so_tien"],
             "chieu": u["chieu"], "mo_ta": u["mo_ta"]} for u in thieu][:200]


def _doi_soat_sao_ke(db: Session, sk_id: int) -> dict:
    """Lưu kết quả so sánh (bộ mới: Duyệt chi NH · thu công nợ bán hàng) vào khop_loai từng dòng.
    Dòng kế toán đã ghi tay từ tab Thống kê thu–chi (DA_CHI_SK / GHI_THU_SK / PHIEU_SK) GIỮ NGUYÊN."""
    from ..models import SaoKeBank, SaoKeDong
    sk = db.get(SaoKeBank, sk_id)
    dongs = (db.query(SaoKeDong).filter_by(sao_ke_id=sk_id)
             .order_by(SaoKeDong.ngay, SaoKeDong.id).all())
    if sk is None or not dongs:
        return {"tong_dong": 0, "khop": 0, "chua_khop": 0, "app_thieu": []}
    kq = _sk_so_sanh(db, sk, dongs)
    auto = kq.get("_auto") or {}
    khop = 0
    for d in dongs:
        if d.khop_loai in _SK_MANUAL:
            khop += 1
            continue
        a = auto.get(d.id)
        if a:
            d.khop_loai, d.khop_id, d.khop_mo_ta = a[0], a[1], (a[2] or "")[:300]
            khop += 1
        else:
            d.khop_loai = None; d.khop_id = None; d.khop_mo_ta = None
    return {"tong_dong": len(dongs), "khop": khop, "chua_khop": len(dongs) - khop,
            "app_thieu": [r for r in kq["rows"] if r["ket_qua"] == "CHI_APP"][:200]}


@router.post("/sao-ke", status_code=201)
def tai_sao_ke(ngan_hang: str = "", bo_qua_trung: bool = False, tu_ngay: date | None = None, den_ngay: date | None = None,
               file: UploadFile = File(...), db: Session = Depends(get_db),
               nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT"))):
    """📥 Tải file sao kê + KỲ SAO KÊ (từ → đến). Excel / CSV đọc THẲNG bằng máy (đủ dòng, đúng từng đồng);
    PDF / ảnh nhờ AI đọc theo từng phần. Chỉ giữ dòng trong kỳ, báo rõ khi đọc thiếu, đối soát ngay.
    File CÙNG TÊN đã tải trước đó → hỏi xác nhận (tránh chồng nhiều bản trùng)."""
    from ..models import SaoKeBank, SaoKeDong
    from ..ai_gateway import doc_sao_ke_tep
    from ..sao_ke_doc import doc_bang
    from ..nhac_viec_service import gio_hien_tai
    if (tu_ngay is None) != (den_ngay is None):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nhập đủ kỳ sao kê: từ ngày và đến ngày")
    if tu_ngay and den_ngay and tu_ngay > den_ngay:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kỳ sao kê: 'từ ngày' phải trước 'đến ngày'")
    data = file.file.read()
    if not data or len(data) > 15 * 1024 * 1024:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File trống hoặc lớn hơn 15MB")
    if not bo_qua_trung:
        cu = (db.query(SaoKeBank).filter(SaoKeBank.ten_file == (file.filename or "sao_ke")[:200])
              .order_by(SaoKeBank.id.desc()).first())
        if cu is not None:
            raise HTTPException(status.HTTP_409_CONFLICT,
                                f"⚠TRÙNGSK: file '{cu.ten_file}' đã tải trước đó (kỳ {cu.tu_ngay} → {cu.den_ngay}, "
                                f"{cu.so_dong} dòng). Tải tiếp sẽ tạo BẢN MỚI trùng lặp — nên xóa bản cũ (nút 🗑) "
                                "hoặc xác nhận nếu đây là sao kê KHÁC trùng tên file.")
    canh_bao = []
    cach, meta = "AI", None
    kq_may = doc_bang(data, file.content_type or "", file.filename or "")
    fn_l = (file.filename or "").lower()
    if kq_may and kq_may[0]:
        dong, meta = kq_may
        cach = "MAY"
    else:
        if fn_l.endswith((".xlsx", ".xlsm", ".csv", ".txt")):
            canh_bao.append("Không nhận diện được cột Ngày / Ghi nợ / Ghi có trong file bảng — đã nhờ AI đọc, có thể thiếu dòng; "
                            "nên xuất lại sao kê từ ngân hàng dạng Excel có tiêu đề cột.")
        dong = doc_sao_ke_tep(data, file.content_type or "", file.filename or "", tu_ngay, den_ngay)
        if not dong:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "AI không đọc được sao kê từ file này — kiểm tra file / cấu hình AI")
    sk = SaoKeBank(ten_file=(file.filename or "sao_ke")[:200],
                   ngan_hang=(ngan_hang or "").strip()[:60] or None,
                   nguoi_tao=nd.id, tao_luc=gio_hien_tai())
    db.add(sk); db.flush()
    n, ngays, ngoai_ky, khong_ngay = 0, [], 0, 0
    for d in dong[:5000]:
        vao, ra = _ske_so(d.get("tien_vao")), _ske_so(d.get("tien_ra"))
        if not vao and not ra:
            continue
        ng = d.get("ngay")
        if isinstance(ng, str):
            try:
                ng = date.fromisoformat(ng[:10])
            except Exception:
                ng = None
        elif ng is not None and not isinstance(ng, date):
            ng = None
        if ng is None:
            khong_ngay += 1
        if tu_ngay and den_ngay and ng is not None and not (tu_ngay <= ng <= den_ngay):
            ngoai_ky += 1
            continue
        sd = _ske_so(d.get("so_du")) if d.get("so_du") is not None else None
        db.add(SaoKeDong(sao_ke_id=sk.id, ngay=ng,
                         dien_giai=(str(d.get("dien_giai") or "")[:400]) or None,
                         tien_vao=vao, tien_ra=ra, so_du=sd))
        if ng:
            ngays.append(ng)
        n += 1
    if not n:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Không thấy dòng giao dịch hợp lệ nào trong file" + (" thuộc kỳ đã nhập" if tu_ngay else ""))
    sk.so_dong = n
    if tu_ngay and den_ngay:
        sk.tu_ngay, sk.den_ngay = tu_ngay, den_ngay
        if ngays and (min(ngays) > tu_ngay + timedelta(days=3) or max(ngays) < den_ngay - timedelta(days=3)):
            canh_bao.append(f"Dòng đọc được chỉ từ {min(ngays)} đến {max(ngays)} trong khi kỳ nhập là {tu_ngay} → {den_ngay} — "
                            "có thể file thiếu dữ liệu đầu / cuối kỳ (hoặc AI đọc thiếu); kiểm tra lại file.")
    else:
        sk.tu_ngay = min(ngays) if ngays else None
        sk.den_ngay = max(ngays) if ngays else None
        canh_bao.append("Chưa nhập kỳ sao kê — kỳ đang lấy theo ngày nhỏ nhất / lớn nhất của các dòng đọc được.")
    if ngoai_ky:
        canh_bao.append(f"Bỏ {ngoai_ky} dòng ngoài kỳ.")
    if khong_ngay:
        canh_bao.append(f"{khong_ngay} dòng không đọc được ngày.")
    if cach == "AI" and len(dong) >= 280 and not fn_l.endswith(".pdf"):
        canh_bao.append("AI đọc gần giới hạn — file dài có thể bị thiếu dòng; dùng Excel / CSV để máy đọc thẳng.")
    ghi_audit(db, nd.id, "TAI_SAO_KE", "sao_ke_bank", sk.id,
              moi={"file": sk.ten_file, "ngan_hang": sk.ngan_hang, "so_dong": n, "cach": cach,
                   "ky": [str(sk.tu_ngay), str(sk.den_ngay)], "ngoai_ky": ngoai_ky})
    db.flush()
    kq = _doi_soat_sao_ke(db, sk.id)
    db.commit()
    return {"ok": True, "id": sk.id, "so_dong": n, "cach": cach, "canh_bao": canh_bao,
            "tu_ngay": str(sk.tu_ngay) if sk.tu_ngay else None, "den_ngay": str(sk.den_ngay) if sk.den_ngay else None,
            "doi_soat": kq}


class SaoKeSuaVao(_BRBase):
    tu_ngay: date | None = None
    den_ngay: date | None = None
    ngan_hang: str | None = None


@router.put("/sao-ke/{sk_id}")
def sua_sao_ke(sk_id: int, data: SaoKeSuaVao, db: Session = Depends(get_db),
               nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT"))):
    """✏️ Sửa KỲ SAO KÊ / ngân hàng của bản đã tải rồi đối soát lại theo kỳ mới."""
    from ..models import SaoKeBank
    sk = db.get(SaoKeBank, sk_id)
    if sk is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sao kê")
    cu = {"tu_ngay": str(sk.tu_ngay), "den_ngay": str(sk.den_ngay), "ngan_hang": sk.ngan_hang}
    if data.tu_ngay is not None:
        sk.tu_ngay = data.tu_ngay
    if data.den_ngay is not None:
        sk.den_ngay = data.den_ngay
    if sk.tu_ngay and sk.den_ngay and sk.tu_ngay > sk.den_ngay:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kỳ sao kê: 'từ ngày' phải trước 'đến ngày'")
    if data.ngan_hang is not None:
        sk.ngan_hang = data.ngan_hang.strip()[:60] or None
    kq = _doi_soat_sao_ke(db, sk.id)
    ghi_audit(db, nd.id, "SUA_SAO_KE", "sao_ke_bank", sk.id, cu=cu,
              moi={"tu_ngay": str(sk.tu_ngay), "den_ngay": str(sk.den_ngay), "ngan_hang": sk.ngan_hang})
    db.commit()
    return {"ok": True, "id": sk.id, "tu_ngay": str(sk.tu_ngay) if sk.tu_ngay else None,
            "den_ngay": str(sk.den_ngay) if sk.den_ngay else None, "doi_soat": kq}


@router.get("/sao-ke")
def ds_sao_ke(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    from ..models import SaoKeBank, SaoKeDong
    out = []
    for sk in db.query(SaoKeBank).order_by(SaoKeBank.id.desc()).limit(50).all():
        khop = db.query(func.count(SaoKeDong.id)).filter(
            SaoKeDong.sao_ke_id == sk.id, SaoKeDong.khop_loai.isnot(None)).scalar() or 0
        out.append({"id": sk.id, "ten_file": sk.ten_file, "ngan_hang": sk.ngan_hang,
                    "tu_ngay": str(sk.tu_ngay) if sk.tu_ngay else None,
                    "den_ngay": str(sk.den_ngay) if sk.den_ngay else None,
                    "so_dong": sk.so_dong, "khop": int(khop),
                    "chua_khop": int((sk.so_dong or 0) - khop),
                    "tao_luc": str(sk.tao_luc)[:16] if sk.tao_luc else None})
    return out


# ============ 🧾 SO SÁNH SAO KÊ ↔ APP — 2 nguồn anh Hiếu chốt (07/10/2026) ============
#   tiền RA  ↔ lệnh DUYỆT CHI NGÂN HÀNG (mục Nhà cung cấp) đã duyệt / đã chi
#   tiền VÀO ↔ THU CÔNG NỢ BÁN HÀNG (mục Bán hàng), ưu tiên công nợ ĐÃ HOÀN THÀNH
# Bảng hợp nhất sắp ngày mới lên trên, mỗi dòng có phân tích; dòng kế toán đã ghi tay từ sao kê giữ nguyên.
_SK_MANUAL = ("DA_CHI_SK", "GHI_THU_SK", "PHIEU_SK", "GAN_TAY", "BO_KHOP", "COC_SK")   # GAN_TAY/BO_KHOP/COC_SK: mig 148
_SK_NHOM_TEN = {"NOI_BO": "chuyển nội bộ", "NOP_RUT": "nộp / rút tiền mặt", "LUONG": "chi lương", "BHXH": "bảo hiểm xã hội",
                "THUE": "nộp thuế", "PHI_NH": "phí ngân hàng / bảo lãnh / trả nợ vay",
                "CHI_CHUNG": "điện nước, thuê văn phòng, viễn thông"}


def _sk_vnd(x):
    return f"{float(x or 0):,.0f} đ"


def _sk_kd(s0):
    import unicodedata
    s0 = unicodedata.normalize("NFD", s0 or "")
    s0 = "".join(c for c in s0 if unicodedata.category(c) != "Mn")
    return s0.replace("đ", "d").replace("Đ", "D").lower()


def _sk_phan_loai(dg):
    """Nhóm giao dịch KHÔNG đi qua Duyệt chi NH / thu công nợ (suy từ diễn giải) — để phân tích dòng chỉ có trên sao kê."""
    k = " " + _sk_kd(dg) + " "
    if "chuyen noi bo" in k or " noi bo" in k:
        return "NOI_BO"
    if "rut tien" in k or "nhap quy" in k or "nop tien mat" in k:
        return "NOP_RUT"
    if "chi luong" in k or "luong thang" in k or "thanh toan luong" in k or "luong t" in k:
        return "LUONG"
    if "bhxh" in k or "bao hiem xa hoi" in k:
        return "BHXH"
    if "nop thue" in k or "thue gtgt" in k or "thue tndn" in k or "thue mon bai" in k:
        return "THUE"
    if (" phi " in k or k.strip().startswith("phi ") or "phi chuyen" in k or "phi phat hanh" in k or "phi quan ly" in k
            or "bao lanh" in k or "phi thuong nien" in k or "thu no tk" in k or "sao ke tin dung" in k or "lai vay" in k):
        return "PHI_NH"
    if ("tien dien" in k or "tien nuoc" in k or "internet" in k or "vien thong" in k or "thue xuong" in k
            or "thue van phong" in k or "thue nha" in k or "thue mat bang" in k):
        return "CHI_CHUNG"
    return None


def _sk_cn_hoan_thanh(cn) -> bool:
    return (cn.nhac_trang_thai == "XONG" or cn.trang_thai == "THU_DU"
            or (float(cn.so_tien or 0) > 0 and float(cn.da_thanh_toan or 0) >= float(cn.so_tien or 0)))


def _sk_ma_cn(db, cn):
    from ..models import DonHang as _DHs
    if cn.don_hang_id:
        dh = db.get(_DHs, cn.don_hang_id)
        if dh and dh.so:
            return dh.so
    return cn.ma_ban_ngoai


# ---- 📖 ĐỌC NỘI DUNG CHUYỂN KHOẢN (10/10/2026): số hóa đơn · mã bán hàng · cọc / tạm ứng — chìa khóa ghép chính ----
import re as _sk_re
_SK_RE_COC = _sk_re.compile(r"\b(dat coc|tien coc|thu coc|tt coc|coc|tam ung|tra truoc|ung truoc)\b")
_SK_RE_HD = _sk_re.compile(r"(?:\bhd\b|\bhoa don\b|\binv(?:oice)?\b|\bhdbh\b)\s*(?:so\b)?\s*[:#.]?\s*([0-9][0-9 ,\-/&+]*)")
_SK_RE_MA = _sk_re.compile(r"\b(?:TM|DA|DV|OP)-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")


def _sk_so_hd(v) -> str:
    from ..lai_lo_ma import so_hd_chuan
    return so_hd_chuan(v)


def _sk_so_hd_set(v) -> set:
    """Các dạng số của một số hóa đơn trong app: «C26TAP-00004260» → {c26tap4260, 4260} — sao kê thường chỉ ghi số đuôi."""
    k = _sk_so_hd(v)
    out = set()
    if k:
        out.add(k)
        m = _sk_re.search(r"(\d+)$", k)
        if m and m.group(1).lstrip("0"):
            out.add(m.group(1).lstrip("0"))
    return out


def _sk_doc_dien_giai(dg) -> dict:
    """Nội dung chuyển khoản → {coc, so_hd[], ma[]}: «Thu từ HD 139-140-141 - COATS» → so_hd 139 140 141;
    «TT HD 17 DA-VEDAN-0825-02» → so_hd 17 · ma DA-VEDAN-0825-02; «Thu cọc COAT» → coc. Bỏ số kèm % (30%, 50%)."""
    kd = " " + _sk_kd(dg) + " "
    kd = _sk_re.sub(r"\d+\s*%", " ", kd)
    coc = bool(_SK_RE_COC.search(kd))
    so_hd = []
    for m in _SK_RE_HD.finditer(kd):
        for t in _sk_re.split(r"[ ,\-/&+]+", m.group(1)):
            t = t.strip()
            if t.isdigit() and 1 <= len(t) <= 8 and t not in so_hd:
                so_hd.append(t)
    ma = []
    for m in _SK_RE_MA.finditer(str(dg or "").upper()):
        if m.group(0) not in ma:
            ma.append(m.group(0))
    return {"coc": coc, "so_hd": so_hd, "ma": ma}


def _sk_ung_vien(db: Session, tu: date, den: date):
    """(tiền RA: lệnh Duyệt chi NH · tiền VÀO: thu công nợ bán hàng · cọc VÀO: phiếu thu tạm ứng đã duyệt) trong [tu, den]
    — kèm đối tác, SỐ HÓA ĐƠN và MÃ bán hàng của từng khoản để ghép theo nội dung chuyển khoản."""
    from ..models import LenhChiBank, DonMua, NhaCungCap, KhachHang, PhieuThuChi, DonHang as _DHs
    ra, vao, coc_vao = [], [], []
    for r in db.query(LenhChiBank).filter(LenhChiBank.trang_thai.in_(["DA_DUYET", "DA_CHI"])).all():
        ng = r.ngay_tt or (r.chi_luc.date() if r.chi_luc else None) or (r.duyet_luc.date() if r.duyet_luc else None)
        if ng is None or ng < tu or ng > den:
            continue
        cac = {float(r.so_tien or 0)}
        if r.so_tien_dot is not None and float(r.so_tien_dot) > 0:
            cac.add(float(r.so_tien_dot))
        cac = {c for c in cac if c > 0}
        if not cac:
            continue
        nc, so_hd, ma, la_cn_hd = None, set(), None, False
        if r.don_mua_id:
            dm = db.get(DonMua, r.don_mua_id)
            nc = db.get(NhaCungCap, dm.nha_cung_cap_id) if (dm and dm.nha_cung_cap_id) else None
            mo_ta = f"Lệnh chi PO {dm.so if (dm and dm.so) else r.don_mua_id}" + (f" — {nc.ten[:40]}" if nc else "")
            if dm is not None:
                if dm.so_hoa_don and not str(dm.so_hoa_don).upper().startswith("HDM-"):
                    so_hd |= _sk_so_hd_set(dm.so_hoa_don)
                ma = (dm.ma_ban or "").strip() or None
                if not ma and dm.don_hang_id:
                    dh = db.get(_DHs, dm.don_hang_id)
                    ma = (dh.so or "").strip() if dh else None
        elif r.cong_no_id:
            cn = db.get(CongNo, r.cong_no_id)
            nc = db.get(NhaCungCap, cn.nha_cung_cap_id) if (cn and cn.nha_cung_cap_id) else None
            mo_ta = (f"Lệnh chi công nợ CN{r.cong_no_id}" + (f" — {nc.ten[:40]}" if nc else "")
                     + (f" · HĐ {cn.so_ct}" if (cn and cn.so_ct) else ""))
            if cn is not None:
                la_cn_hd = bool(cn.so_ct)
                if cn.so_ct:
                    so_hd |= _sk_so_hd_set(cn.so_ct)
                ma = _sk_ma_cn(db, cn)
        else:
            mo_ta = "Lệnh chi tạm ứng / cọc NCC" + (f" (phiếu #{r.phieu_id})" if r.phieu_id else "")
        ra.append({"loai": "LENH_CHI", "id": r.id, "ngay": ng, "so_tien": max(cac), "cac": cac, "chieu": "RA",
                   "trang_thai": "ĐÃ CHI" if r.trang_thai == "DA_CHI" else "ĐÃ DUYỆT · chờ ngân hàng chi",
                   "uu_tien": 0 if r.trang_thai == "DA_CHI" else 1, "mo_ta": mo_ta,
                   "doi_tac": nc.id if nc else None, "doi_tac_ten": nc.ten if nc else None,
                   "so_hd": {x for x in so_hd if x}, "ma": (ma or "").upper() or None, "la_cn_hd": la_cn_hd})
    co_tt = {x[0] for x in db.query(ThanhToan.cong_no_id).distinct().all()}
    for tt, cn in (db.query(ThanhToan, CongNo).join(CongNo, ThanhToan.cong_no_id == CongNo.id)
                   .filter(CongNo.loai == "PHAI_THU", ThanhToan.ngay >= tu, ThanhToan.ngay <= den).all()):
        kh = db.get(KhachHang, cn.khach_hang_id) if cn.khach_hang_id else None
        xong = _sk_cn_hoan_thanh(cn)
        ma = _sk_ma_cn(db, cn)
        vao.append({"loai": "THU_CN_BAN", "id": tt.id, "ngay": tt.ngay, "so_tien": float(tt.so_tien or 0),
                    "cac": {float(tt.so_tien or 0)}, "chieu": "VAO",
                    "trang_thai": "công nợ HOÀN THÀNH" if xong else "thu một phần · công nợ chưa hoàn thành",
                    "uu_tien": 0 if xong else 1,
                    "mo_ta": (f"Thu công nợ {kh.ten[:40] if kh else ('CN' + str(cn.id))}"
                              + (f" · HĐ {cn.so_ct}" if cn.so_ct else "") + (f" · {ma}" if ma else "")),
                    "doi_tac": kh.id if kh else None, "doi_tac_ten": kh.ten if kh else None,
                    "so_hd": _sk_so_hd_set(cn.so_ct), "ma": (ma or "").upper() or None,
                    "cong_no_id": cn.id})
    # công nợ ĐÃ HOÀN THÀNH (đánh dấu ở Bán hàng) mà app không có lần thu nào → đối chiếu theo tổng công nợ
    for cn in db.query(CongNo).filter(CongNo.loai == "PHAI_THU").all():
        if cn.id in co_tt or not _sk_cn_hoan_thanh(cn):
            continue
        ng = cn.han or cn.ngay_ct
        if ng is None or ng < tu or ng > den or float(cn.so_tien or 0) <= 0:
            continue
        kh = db.get(KhachHang, cn.khach_hang_id) if cn.khach_hang_id else None
        ma = _sk_ma_cn(db, cn)
        vao.append({"loai": "CN_HOAN_THANH", "id": cn.id, "ngay": ng, "so_tien": float(cn.so_tien or 0),
                    "cac": {float(cn.so_tien or 0)}, "chieu": "VAO", "trang_thai": "công nợ HOÀN THÀNH (đánh dấu tay, chưa ghi lần thu)",
                    "uu_tien": 0,
                    "mo_ta": (f"Công nợ hoàn thành {kh.ten[:40] if kh else ('CN' + str(cn.id))}"
                              + (f" · HĐ {cn.so_ct}" if cn.so_ct else "") + (f" · {ma}" if ma else "")),
                    "doi_tac": kh.id if kh else None, "doi_tac_ten": kh.ten if kh else None,
                    "so_hd": _sk_so_hd_set(cn.so_ct), "ma": (ma or "").upper() or None,
                    "cong_no_id": cn.id})
    # 💰 cọc / trả trước của khách: phiếu thu TẠM ỨNG đã duyệt — chỉ ghép với dòng sao kê có chữ cọc / tạm ứng
    for p in (db.query(PhieuThuChi).filter(PhieuThuChi.loai == "THU", PhieuThuChi.la_tam_ung.is_(True),
                                           PhieuThuChi.trang_thai == "DA_DUYET",
                                           PhieuThuChi.ngay >= tu, PhieuThuChi.ngay <= den).all()):
        if float(p.so_tien or 0) <= 0:
            continue
        kh = db.get(KhachHang, p.khach_hang_id) if p.khach_hang_id else None
        dh = db.get(_DHs, p.don_hang_id) if p.don_hang_id else None
        con = float(p.so_tien or 0) - float(p.da_can_tru or 0)
        coc_vao.append({"loai": "TAM_UNG_THU", "id": p.id, "ngay": p.ngay, "so_tien": float(p.so_tien or 0),
                        "cac": {float(p.so_tien or 0)}, "chieu": "VAO",
                        "trang_thai": "phiếu thu tạm ứng ĐÃ DUYỆT" + (f" · còn {con:,.0f} đ chưa cấn trừ" if con > 0 else " · đã cấn trừ hết"),
                        "uu_tien": 0,
                        "mo_ta": (f"Phiếu thu tạm ứng {p.so or ('#' + str(p.id))} · {kh.ten[:40] if kh else 'khách lẻ'}"
                                  + (f" · {dh.so}" if (dh and dh.so) else "")),
                        "doi_tac": kh.id if kh else None, "doi_tac_ten": kh.ten if kh else None,
                        "so_hd": set(), "ma": ((dh.so or "").upper() if dh else None) or None})
    return ra, vao, coc_vao


def _sk_u_out(u):
    return {"loai": u["loai"], "id": u["id"], "mo_ta": u["mo_ta"], "so_tien": u["so_tien"],
            "ngay": str(u["ngay"]) if u.get("ngay") else None, "trang_thai": u.get("trang_thai"),
            "doi_tac": u.get("doi_tac_ten")}


def _sk_loai_luu(u):
    return "THU_CN_BAN" if u["loai"] == "CN_HOAN_THANH" else u["loai"]


def _sk_hd_thieu_text(so_list, chieu, cn_theo_so, hd_theo_so) -> str:
    """Số hóa đơn ghi trong nội dung CK mà không ghép được: chưa có trong app / có nhưng chưa ghi thu-chi."""
    chua_co, chua_ghi, co_hd = [], [], []
    for so in so_list:
        cns = cn_theo_so.get(chieu, {}).get(so)
        if cns:
            cn = cns[0]
            da = float(cn.da_thanh_toan or 0)
            chua_ghi.append(so + (" (đã thu một phần)" if (chieu == "VAO" and da > 0) else ""))
        elif so in hd_theo_so.get(chieu, set()):
            co_hd.append(so)
        else:
            chua_co.append(so)
    phan = []
    if chua_co:
        phan.append("HĐ CHƯA CÓ trong app: " + ", ".join(chua_co) + " — kế toán nhập hóa đơn / công nợ")
    if chua_ghi:
        phan.append(("HĐ có trong app nhưng chưa ghi thu / công nợ chưa hoàn thành: " if chieu == "VAO"
                     else "HĐ có trong app nhưng chưa có lệnh Duyệt chi NH: ") + ", ".join(chua_ghi))
    if co_hd:
        phan.append("HĐ có trong sổ hóa đơn nhưng chưa có dòng công nợ: " + ", ".join(co_hd))
    return " · ".join(phan)


def _sk_so_sanh(db: Session, sk, dongs) -> dict:
    """Bảng hợp nhất sao kê ↔ app — ⓪ dòng kế toán đã ghi tay (phiếu · 🔗 gắn tay · ✕ bỏ khớp · 💰 cọc) giữ nguyên ·
    ①a THEO SỐ HÓA ĐƠN ghi trong nội dung chuyển khoản (không giới hạn số HĐ; thiếu thì nêu HĐ nào chưa có trong app) ·
    ① 1 đối 1 (ưu tiên cùng đối tác, cùng mã) · ② 1 dòng sao kê trả gộp 2–3 khoản — chỉ ✓ khi nội dung nêu đúng đối tác,
    không thì «? nghi gộp» (không tự ghi) · ③ 1 khoản app nhận NHIỀU ĐỢT · ④ TRẢ MỘT PHẦN cùng đối tác · ⑤ còn lại:
    💰 cọc / trả trước đi riêng (ghép phiếu thu tạm ứng, không ghép hóa đơn) · chỉ sao kê (kèm HĐ ghi trong nội dung có hay
    không có trong app) · chỉ app. Trả {tong, phan_tich[], rows[] (ngày mới lên trên), _auto{dong_id: (loai, id, mo_ta)}}."""
    import itertools
    from ..models import NhaCungCap, KhachHang, SaoKeKhop, HoaDon
    from .ke_toan_quy import _khop_ncc
    tu = (sk.tu_ngay or date.today()) - timedelta(days=7)
    den = (sk.den_ngay or date.today()) + timedelta(days=7)
    ra, vao, coc_vao = _sk_ung_vien(db, tu, den)
    pool_idx = {(u["loai"], u["id"]): u for u in ra + vao + coc_vao}
    ds_ncc = db.query(NhaCungCap).all()
    ds_kh = db.query(KhachHang).all()
    ten_cua = {"RA": {n.id: n.ten for n in ds_ncc}, "VAO": {k.id: k.ten for k in ds_kh}}
    # tra cứu công nợ / hóa đơn theo SỐ (mọi trạng thái) — để báo «HĐ … chưa có trong app» / «có nhưng chưa ghi thu»
    cn_theo_so = {"VAO": {}, "RA": {}}
    for cn in db.query(CongNo).filter(CongNo.so_ct.isnot(None)).all():
        for k0 in _sk_so_hd_set(cn.so_ct):
            cn_theo_so["VAO" if cn.loai == "PHAI_THU" else "RA"].setdefault(k0, []).append(cn)
    hd_theo_so = {"VAO": set(), "RA": set()}
    for (lo, so0) in db.query(HoaDon.loai, HoaDon.so).filter(HoaDon.so.isnot(None)).all():
        hd_theo_so["RA" if lo == "MUA" else "VAO"] |= _sk_so_hd_set(so0)

    def lech(a, b):
        return abs((a - b).days) if (a and b) else 99

    def ten_dt(chieu, i):
        return ten_cua[chieu].get(i) if i else None

    def eps_cua(chieu, so):
        # tiền vào: ngân hàng trừ phí chuyển (thường 11.000–33.000 đ, có khi 0,2 %) → cho lệch ≤ 50.000 đ hoặc ≤ 0,2 % (trần 300.000 đ)
        return max(50000.0, min(so * 0.002, 300000.0)) if chieu == "VAO" else 0.5

    def pool_cua(chieu):
        return ra if chieu == "RA" else vao

    def gh_cua(chieu):
        return 7 if chieu == "RA" else 5

    def dt_ok(x, u):
        return x["dt"] is None or u.get("doi_tac") is None or x["dt"] == u["doi_tac"]

    def dt_uu(x, u):
        if x["dt"] and u.get("doi_tac") == x["dt"]:
            return 0
        return 1 if (x["dt"] is None or u.get("doi_tac") is None) else 2

    def ma_uu(x, u):
        m = u.get("ma")
        return 0 if (m and any(m == a or a.startswith(m) or m.startswith(a) for a in x["ma"])) else 1

    def pt_dt(x, u):
        if x["dt"] and u.get("doi_tac") and x["dt"] != u["doi_tac"]:
            return f" ⚠ diễn giải ghi «{ten_dt(x['chieu'], x['dt'])}» còn app là «{u.get('doi_tac_ten') or ''}» — kiểm tra"
        return ""

    D = []
    for d in sorted(dongs, key=lambda x: (x.ngay or date.min, x.id)):
        vao_d, ra_d = float(d.tien_vao or 0), float(d.tien_ra or 0)
        so = ra_d if ra_d > 0 else vao_d
        if so <= 0:
            continue
        chieu = "RA" if ra_d > 0 else "VAO"
        dt = _khop_ncc(ds_ncc if chieu == "RA" else ds_kh, d.dien_giai or "") if (d.dien_giai or "").strip() else None
        nd = _sk_doc_dien_giai(d.dien_giai)
        D.append({"d": d, "id": d.id, "so": so, "chieu": chieu, "dt": dt, "ngay": d.ngay,
                  "manual": d.khop_loai in _SK_MANUAL, "coc": nd["coc"],
                  "so_hd": {_sk_so_hd(t) for t in nd["so_hd"] if _sk_so_hd(t)}, "ma": nd["ma"]})
    khop_tay = {}
    if D:
        for k in db.query(SaoKeKhop).filter(SaoKeKhop.dong_id.in_([x["id"] for x in D])).order_by(SaoKeKhop.id).all():
            khop_tay.setdefault(k.dong_id, []).append(k)

    def skd(x):
        return {"id": x["id"], "dien_giai": x["d"].dien_giai, "so_tien": x["so"],
                "ngay": str(x["ngay"]) if x["ngay"] else None, "doi_tac": ten_dt(x["chieu"], x["dt"]),
                "so_hd": sorted(x["so_hd"]), "ma": x["ma"], "coc": x["coc"], "khop_loai": x["d"].khop_loai}

    dung, dung_sk, rows, auto = set(), set(), [], {}
    ngay_s = lambda x: str(x["ngay"]) if x["ngay"] else None
    hd_txt = lambda x: ", ".join(sorted(x["so_hd"]))

    # ---------- ⓪ kế toán đã ghi tay ----------
    for x in D:
        if not x["manual"]:
            continue
        d = x["d"]
        dung_sk.add(x["id"])
        if d.khop_loai == "GAN_TAY":
            apps = []
            for k in khop_tay.get(d.id, []):
                u = pool_idx.get((k.loai, k.khoan_id))
                if u is not None:
                    dung.add((u["loai"], u["id"]))
                    o = _sk_u_out(u)
                    if k.so_tien is not None and float(k.so_tien) > 0:
                        o["so_tien"] = float(k.so_tien)
                    o["trang_thai"] = ((o.get("trang_thai") or "") + " · ✍ gắn tay").strip(" ·")
                else:
                    o = {"loai": k.loai, "id": k.khoan_id, "mo_ta": k.ghi_chu or f"{k.loai} #{k.khoan_id}",
                         "so_tien": float(k.so_tien or 0), "ngay": None, "trang_thai": "✍ gắn tay (khoản ngoài kỳ đối soát)"}
                apps.append(o)
            tong_g = sum(a["so_tien"] for a in apps)
            lech_t = tong_g - x["so"]
            pt = f"✓ Kế toán gắn tay {len(apps)} khoản app cho dòng sao kê này"
            if abs(lech_t) > eps_cua(x["chieu"], x["so"]):
                pt += f" · tổng gắn {_sk_vnd(tong_g)} {'lớn' if lech_t > 0 else 'nhỏ'} hơn sao kê {_sk_vnd(abs(lech_t))}"
            if d.khop_mo_ta and not str(d.khop_mo_ta).startswith("gắn tay:"):
                pt += f" · {d.khop_mo_ta}"
            rows.append({"ngay": ngay_s(x), "chieu": x["chieu"], "sk": skd(x), "app": apps, "ket_qua": "KHOP",
                         "lech_ngay": 0, "nhom": None, "gan_tay": True, "phan_tich": pt})
        elif d.khop_loai == "BO_KHOP":
            rows.append({"ngay": ngay_s(x), "chieu": x["chieu"], "sk": skd(x), "app": [], "ket_qua": "BO_KHOP",
                         "lech_ngay": None, "nhom": None, "gan_tay": True,
                         "phan_tich": "✕ Kế toán xác nhận dòng này KHÔNG khớp khoản nào trong app"
                                      + (f" — {d.khop_mo_ta}" if d.khop_mo_ta else "")})
        elif d.khop_loai == "COC_SK":
            u = pool_idx.get(("TAM_UNG_THU", d.khop_id)) if d.khop_id else None
            if u is not None:
                dung.add((u["loai"], u["id"]))
            rows.append({"ngay": ngay_s(x), "chieu": x["chieu"], "sk": skd(x), "app": [_sk_u_out(u)] if u else [],
                         "ket_qua": "COC_KH" if x["chieu"] == "VAO" else "COC_NCC", "lech_ngay": None, "nhom": "COC",
                         "gan_tay": True,
                         "phan_tich": "💰 Kế toán ghi nhận là tiền cọc / trả trước — không ghép với hóa đơn"
                                      + (" · đã nối phiếu thu tạm ứng" if u else "")
                                      + (f" · {d.khop_mo_ta}" if d.khop_mo_ta else "")})
        else:
            rows.append({"ngay": ngay_s(x), "chieu": x["chieu"], "sk": skd(x), "ket_qua": "KHOP", "lech_ngay": 0, "nhom": None,
                         "app": [{"loai": "DA_GHI", "id": d.khop_id, "mo_ta": d.khop_mo_ta or "Kế toán đã ghi từ dòng sao kê",
                                  "so_tien": x["so"], "ngay": ngay_s(x), "trang_thai": "đã ghi tay"}],
                         "phan_tich": "✓ Kế toán đã ghi phiếu / lệnh từ dòng sao kê này (Kế toán › Thống kê thu–chi)"})
    # ---------- ①a THEO SỐ HÓA ĐƠN ghi trong nội dung chuyển khoản ----------
    for x in D:
        if x["id"] in dung_sk or x["coc"] or not x["so_hd"]:
            continue
        cands = [u for u in pool_cua(x["chieu"]) if (u["loai"], u["id"]) not in dung and (u["so_hd"] & x["so_hd"])]
        if not cands:
            continue
        eps = eps_cua(x["chieu"], x["so"])
        tong_c = sum(u["so_tien"] for u in cands)
        combo, thieu = None, None
        if abs(tong_c - x["so"]) <= eps:
            combo = cands
        elif tong_c > x["so"] + eps and len(cands) <= 12:
            for n in range(1, min(5, len(cands)) + 1):
                for c in itertools.combinations(cands, n):
                    if abs(sum(u["so_tien"] for u in c) - x["so"]) <= eps:
                        combo = list(c)
                        break
                if combo:
                    break
        elif tong_c < x["so"] - eps:
            combo, thieu = cands, x["so"] - tong_c
        if combo is None:
            continue
        for u in combo:
            dung.add((u["loai"], u["id"]))
        dung_sk.add(x["id"])
        so_co = set().union(*(u["so_hd"] for u in combo))
        so_thieu = [t for t in sorted(x["so_hd"]) if t not in so_co]
        ds_hd = ", ".join(sorted(so_co))
        le = max(lech(u["ngay"], x["ngay"]) for u in combo)
        if thieu:
            pt = (f"◐ Nội dung CK ghi HĐ {hd_txt(x)}; app có {len(combo)} khoản (HĐ {ds_hd}) = {_sk_vnd(tong_c)}, "
                  f"sao kê {_sk_vnd(x['so'])} → còn chênh {_sk_vnd(thieu)}")
        else:
            pt = (f"✓ Khớp theo SỐ HÓA ĐƠN ghi trong nội dung chuyển khoản (HĐ {ds_hd}) — {len(combo)} khoản app"
                  + (f" · lệch {le} ngày" if le > 3 else ""))
        if so_thieu:
            pt += " · " + _sk_hd_thieu_text(so_thieu, x["chieu"], cn_theo_so, hd_theo_so)
        rows.append({"ngay": ngay_s(x), "chieu": x["chieu"], "sk": skd(x), "app": [_sk_u_out(u) for u in combo],
                     "ket_qua": ("THEO_HD_THIEU" if thieu else ("KHOP" if len(combo) == 1 else "KHOP_GOP")),
                     "theo_hd": True, "lech_ngay": le, "nhom": None, "con_thieu": float(thieu or 0), "phan_tich": pt})
        auto[x["id"]] = (_sk_loai_luu(combo[0]), combo[0]["id"],
                         f"theo số HĐ {ds_hd}: " + "; ".join(u["mo_ta"] for u in combo))
    # ---------- ① 1 đối 1 — ưu tiên cùng đối tác / cùng mã; tiền vào cho lệch phí; dòng CỌC tiền vào không ghép hóa đơn ----------
    for x in D:
        if x["id"] in dung_sk or (x["coc"] and x["chieu"] == "VAO"):
            continue
        best = None
        for u in pool_cua(x["chieu"]):
            if (u["loai"], u["id"]) in dung:
                continue
            if x["coc"] and u.get("la_cn_hd"):
                continue                                   # cọc NCC không ghép lệnh chi trả hóa đơn công nợ
            diff = min(abs(c - x["so"]) for c in u["cac"])
            if diff > eps_cua(x["chieu"], x["so"]):
                continue
            le = lech(u["ngay"], x["ngay"])
            if le > gh_cua(x["chieu"]):
                continue
            key = (dt_uu(x, u), ma_uu(x, u), le, u["uu_tien"], diff)
            if best is None or key < best[0]:
                best = (key, u, diff, le)
        if best is None:
            continue
        _, u, diff, le = best
        dung.add((u["loai"], u["id"])); dung_sk.add(x["id"])
        pt = f"✓ Khớp {u['mo_ta']} · {u['trang_thai']}"
        if diff > 0.5:
            pt += f" · lệch phí ngân hàng {diff:,.0f} đ"
        if le > 3:
            pt += f" · lệch {le} ngày so với app"
        if x["coc"]:
            pt += " · nội dung ghi cọc / tạm ứng"
        khac_dt = bool(x["dt"] and u.get("doi_tac") and x["dt"] != u["doi_tac"])
        pt += pt_dt(x, u)
        rows.append({"ngay": ngay_s(x), "chieu": x["chieu"], "sk": skd(x), "app": [_sk_u_out(u)], "ket_qua": "KHOP",
                     "lech_ngay": le, "nhom": None, "khac_doi_tac": khac_dt, "phan_tich": pt})
        auto[x["id"]] = (_sk_loai_luu(u), u["id"], u["mo_ta"] + (" (khác đối tác?)" if khac_dt else ""))
    # ---------- ② 1 dòng sao kê trả gộp 2–3 khoản app — chỉ ✓ khi nội dung CK nêu đúng đối tác ----------
    for x in D:
        if x["id"] in dung_sk or x["coc"]:
            continue
        gh = gh_cua(x["chieu"])
        cands = [u for u in pool_cua(x["chieu"]) if (u["loai"], u["id"]) not in dung
                 and lech(u["ngay"], x["ngay"]) <= gh and dt_ok(x, u)]
        cands.sort(key=lambda u: (dt_uu(x, u), lech(u["ngay"], x["ngay"]), u["uu_tien"]))
        cands = cands[:12]
        eps = max(1000.0, x["so"] * 0.001)
        combo = None
        for n in (2, 3):
            for c in itertools.combinations(cands, n):
                if abs(sum(u["so_tien"] for u in c) - x["so"]) <= eps:
                    combo = list(c)
                    break
            if combo:
                break
        if not combo:
            continue
        tin = bool(x["dt"]) and all(u.get("doi_tac") == x["dt"] for u in combo)
        dung_sk.add(x["id"])
        if not tin:
            rows.append({"ngay": ngay_s(x), "chieu": x["chieu"], "sk": skd(x), "app": [_sk_u_out(u) for u in combo],
                         "ket_qua": "NGHI_GOP", "lech_ngay": None, "nhom": None,
                         "phan_tich": (f"? Tổng {len(combo)} khoản trong app bằng số tiền này nhưng nội dung chuyển khoản "
                                       "KHÔNG nêu đối tác / số hóa đơn tương ứng — chưa tự ghi; kế toán kiểm tra rồi 🔗 Gắn "
                                       "hoặc ✕ Bỏ khớp")})
            continue
        for u in combo:
            dung.add((u["loai"], u["id"]))
        le = max(lech(u["ngay"], x["ngay"]) for u in combo)
        rows.append({"ngay": ngay_s(x), "chieu": x["chieu"], "sk": skd(x), "app": [_sk_u_out(u) for u in combo], "ket_qua": "KHOP_GOP",
                     "lech_ngay": le, "nhom": None,
                     "phan_tich": f"✓ Một lần chuyển trả gộp {len(combo)} khoản trong app (cùng đối tác «{ten_dt(x['chieu'], x['dt'])}»)"
                                  + (f" · lệch tới {le} ngày" if le > 3 else "")})
        auto[x["id"]] = (_sk_loai_luu(combo[0]), combo[0]["id"], "; ".join(u["mo_ta"] for u in combo))
    # ---------- ③ 1 khoản app nhận NHIỀU ĐỢT (2–4 dòng sao kê) ----------
    for u in ra + vao:
        if (u["loai"], u["id"]) in dung or u["ngay"] is None:
            continue
        cands = [x for x in D if x["id"] not in dung_sk and x["chieu"] == u["chieu"] and not x["coc"]
                 and lech(u["ngay"], x["ngay"]) <= 15 and dt_ok(x, u)]
        cands.sort(key=lambda x: (dt_uu(x, u), lech(u["ngay"], x["ngay"])))
        cands = cands[:10]
        eps = max(1000.0, u["so_tien"] * 0.001)
        combo = None
        for n in (2, 3, 4):
            for c in itertools.combinations(cands, n):
                if abs(sum(x["so"] for x in c) - u["so_tien"]) <= eps:
                    combo = list(c)
                    break
            if combo:
                break
        if not combo:
            continue
        dung.add((u["loai"], u["id"]))
        combo.sort(key=lambda x: (x["ngay"] or date.min, x["id"]))
        for k, x in enumerate(combo, 1):
            dung_sk.add(x["id"])
            auto[x["id"]] = (_sk_loai_luu(u), u["id"], f"đợt {k}/{len(combo)} · {u['mo_ta']}")
        ng_max = max((x["ngay"] for x in combo if x["ngay"]), default=u["ngay"])
        rows.append({"ngay": str(ng_max), "chieu": u["chieu"], "sk": None, "sk_list": [skd(x) for x in combo],
                     "app": [_sk_u_out(u)], "ket_qua": "KHOP_NHIEU_DOT", "lech_ngay": None, "nhom": None,
                     "phan_tich": f"✓ Ngân hàng chuyển {len(combo)} đợt ({', '.join(_sk_vnd(x['so']) for x in combo)}) cho một khoản trong app"})
    # ---------- ④ TRẢ MỘT PHẦN — cùng đối tác, dòng sao kê nhỏ hơn khoản app ----------
    phan = {}      # key app → {"u": u, "sk": [x...]}
    for x in D:
        if x["id"] in dung_sk or not x["dt"] or x["coc"]:
            continue
        best = None
        for u in pool_cua(x["chieu"]):
            k = (u["loai"], u["id"])
            if k in dung or u.get("doi_tac") != x["dt"] or u["ngay"] is None:
                continue
            da = sum(y["so"] for y in phan.get(k, {}).get("sk", []))
            if u["so_tien"] - da < x["so"] - eps_cua(x["chieu"], x["so"]):
                continue                                   # phần còn lại không đủ chứa dòng này
            le = lech(u["ngay"], x["ngay"])
            if le > 30:
                continue
            if best is None or le < best[0]:
                best = (le, u, k)
        if best is None:
            continue
        _, u, k = best
        phan.setdefault(k, {"u": u, "sk": []})["sk"].append(x)
        dung_sk.add(x["id"])
    for k, g in phan.items():
        u, xs = g["u"], sorted(g["sk"], key=lambda x: (x["ngay"] or date.min, x["id"]))
        da = sum(x["so"] for x in xs)
        con = u["so_tien"] - da
        du = con <= max(1000.0, u["so_tien"] * 0.001)
        if du:
            dung.add(k)
        for i2, x in enumerate(xs, 1):
            auto[x["id"]] = (_sk_loai_luu(u), u["id"], f"trả một phần {i2}/{len(xs)} · {u['mo_ta']}")
        ng_max = max((x["ngay"] for x in xs if x["ngay"]), default=u["ngay"])
        rows.append({"ngay": str(ng_max), "chieu": u["chieu"], "sk": None, "sk_list": [skd(x) for x in xs],
                     "app": [_sk_u_out(u)], "ket_qua": ("KHOP_NHIEU_DOT" if du else "MOT_PHAN"), "lech_ngay": None, "nhom": None,
                     "con_thieu": (0.0 if du else con),
                     "phan_tich": (f"✓ Đủ sau {len(xs)} đợt trả cho {u['mo_ta']}" if du else
                                   f"◐ Trả một phần cho {u['mo_ta']}: đã thấy {_sk_vnd(da)} / {_sk_vnd(u['so_tien'])} trên sao kê ({len(xs)} đợt), "
                                   f"còn thiếu {_sk_vnd(con)} chưa thấy trong kỳ")})
        if not du:
            dung.add(k)       # không liệt kê lại ở «chỉ app» — đã có dòng một phần
    # ---------- ⑤ còn lại: 💰 cọc / trả trước đi riêng · chỉ sao kê · chỉ app ----------
    for x in D:
        if x["id"] in dung_sk:
            continue
        dt_ten = ten_dt(x["chieu"], x["dt"])
        ma_txt = x["ma"][0] if x["ma"] else None
        if x["coc"]:
            if x["chieu"] == "VAO":
                best = None
                for u in coc_vao:
                    if (u["loai"], u["id"]) in dung:
                        continue
                    diff = min(abs(c - x["so"]) for c in u["cac"])
                    if diff > eps_cua("VAO", x["so"]):
                        continue
                    le = lech(u["ngay"], x["ngay"])
                    if le > 7:
                        continue
                    key = (dt_uu(x, u), ma_uu(x, u), le, diff)
                    if best is None or key < best[0]:
                        best = (key, u, le)
                if best is not None:
                    _, u, le = best
                    dung.add((u["loai"], u["id"])); dung_sk.add(x["id"])
                    rows.append({"ngay": ngay_s(x), "chieu": "VAO", "sk": skd(x), "app": [_sk_u_out(u)], "ket_qua": "KHOP",
                                 "lech_ngay": le, "nhom": "COC", "coc": True,
                                 "phan_tich": f"✓ Tiền cọc / trả trước — khớp {u['mo_ta']} · {u['trang_thai']}" + pt_dt(x, u)})
                    auto[x["id"]] = ("TAM_UNG_THU", u["id"], u["mo_ta"])
                    continue
                rows.append({"ngay": ngay_s(x), "chieu": "VAO", "sk": skd(x), "app": [], "ket_qua": "COC_KH", "lech_ngay": None,
                             "nhom": "COC",
                             "phan_tich": ("💰 Tiền cọc / trả trước" + (f" từ {dt_ten}" if dt_ten else "")
                                           + " — KHÔNG ghép với hóa đơn. Lập PHIẾU THU TẠM ỨNG (Kế toán › Phiếu thu, tick tạm ứng"
                                           + (f", gắn mã {ma_txt}" if ma_txt else ", gắn mã đơn") + ") để cấn trừ khi xuất hóa đơn, "
                                           "hoặc bấm 💰 Cọc để ghi nhận trên dòng này")})
            else:
                rows.append({"ngay": ngay_s(x), "chieu": "RA", "sk": skd(x), "app": [], "ket_qua": "COC_NCC", "lech_ngay": None,
                             "nhom": "COC",
                             "phan_tich": ("💰 Tiền cọc / tạm ứng trả nhà cung cấp" + (f" {dt_ten}" if dt_ten else "")
                                           + " — app chưa có lệnh Duyệt chi NH tương ứng: ghi đợt cọc trên PO"
                                           + (f" mã {ma_txt}" if ma_txt else "") + " (Thanh toán mua hàng) hoặc lệnh chi tạm ứng NCC"
                                           + (" · nội dung ghi HĐ " + hd_txt(x) if x["so_hd"] else ""))})
            continue
        nhom = _sk_phan_loai(x["d"].dien_giai)
        if x["chieu"] == "RA":
            pt = (f"Ngân hàng chi {_SK_NHOM_TEN[nhom]} — không đi qua Duyệt chi NH; ghi phiếu chi ở Kế toán › Thống kê thu–chi"
                  if nhom else ("⚠ Ngân hàng đã chi" + (f" cho {dt_ten}" if dt_ten else "") +
                                " nhưng app KHÔNG có lệnh Duyệt chi NH tương ứng — kiểm tra NCC / PO, có thể lệnh chưa lập"))
        else:
            pt = (f"Tiền vào {_SK_NHOM_TEN[nhom]} — không phải thu công nợ bán hàng"
                  if nhom else ("⚠ Tiền vào" + (f" từ {dt_ten}" if dt_ten else "") +
                                " nhưng app chưa ghi thu công nợ bán hàng (hoặc công nợ chưa đánh dấu hoàn thành) — ghi thu ở Bán hàng › Công nợ hoặc Kế toán › Thống kê thu–chi"))
        if x["so_hd"] and not nhom:
            pt += " · " + _sk_hd_thieu_text(sorted(x["so_hd"]), x["chieu"], cn_theo_so, hd_theo_so)
        rows.append({"ngay": ngay_s(x), "chieu": x["chieu"], "sk": skd(x), "app": [], "ket_qua": "CHI_SK", "lech_ngay": None,
                     "nhom": nhom, "phan_tich": pt})
    for u in ra + vao:
        if (u["loai"], u["id"]) in dung or u["ngay"] is None:
            continue
        if not (sk.tu_ngay and sk.den_ngay and sk.tu_ngay <= u["ngay"] <= sk.den_ngay):
            continue
        if u["loai"] == "LENH_CHI":
            pt = ("Lệnh đã duyệt nhưng trong kỳ sao kê ngân hàng chưa chi — bình thường nếu chi sau kỳ; quá kỳ vẫn chưa chi thì nhắc kế toán"
                  if "DUYỆT" in u["trang_thai"]
                  else "⚠ App ghi ĐÃ CHI nhưng sao kê không có khoản này — kiểm tra ngày / số tiền / tài khoản đã chi")
        elif u["loai"] == "THU_CN_BAN":
            pt = "⚠ App ghi đã thu nhưng sao kê không thấy tiền vào — kiểm tra ngày / số tiền, hoặc thu bằng tiền mặt / tài khoản khác"
        else:
            pt = "Công nợ đánh dấu hoàn thành nhưng app không có lần thu và sao kê không thấy tiền vào — xem lại ở Bán hàng › Công nợ"
        rows.append({"ngay": str(u["ngay"]), "chieu": u["chieu"], "sk": None, "app": [_sk_u_out(u)], "ket_qua": "CHI_APP",
                     "lech_ngay": None, "nhom": None, "phan_tich": pt})
    rows.sort(key=lambda r: (r["ngay"] or "0000-00-00", ((r.get("sk") or {}).get("id")) or 0), reverse=True)
    # ---------- tổng + phân tích ----------
    sk_vao = sum(float(d.tien_vao or 0) for d in dongs)
    sk_ra = sum(float(d.tien_ra or 0) for d in dongs)
    trong_ky = lambda u: bool(sk.tu_ngay and sk.den_ngay and u["ngay"] and sk.tu_ngay <= u["ngay"] <= sk.den_ngay)
    app_ra = sum(u["so_tien"] for u in ra if trong_ky(u))
    app_vao = sum(u["so_tien"] for u in vao if trong_ky(u))
    KHOPS = ("KHOP", "KHOP_GOP", "KHOP_NHIEU_DOT")
    kh = [r for r in rows if r["ket_qua"] in KHOPS]
    mp = [r for r in rows if r["ket_qua"] in ("MOT_PHAN", "THEO_HD_THIEU")]
    csk = [r for r in rows if r["ket_qua"] == "CHI_SK"]
    capp = [r for r in rows if r["ket_qua"] == "CHI_APP"]
    nghi = [r for r in rows if r["ket_qua"] == "NGHI_GOP"]
    coc_rows = [r for r in rows if r["ket_qua"] in ("COC_KH", "COC_NCC") or r.get("coc")]
    bo = [r for r in rows if r["ket_qua"] == "BO_KHOP"]
    khac_dt = [r for r in rows if r.get("khac_doi_tac")]

    def tien_sk(r):
        if r.get("sk_list"):
            return sum(x["so_tien"] for x in r["sk_list"])
        return r["sk"]["so_tien"] if r.get("sk") else sum(a["so_tien"] for a in r["app"])

    tien = lambda rs, chieu=None: sum(tien_sk(r) for r in rs if chieu is None or r["chieu"] == chieu)
    tong = {"dong": len(dongs), "sk_vao": sk_vao, "sk_ra": sk_ra, "app_vao": app_vao, "app_ra": app_ra,
            "khop": len(kh), "khop_tien": tien(kh), "nhieu_dot": sum(1 for r in kh if r["ket_qua"] == "KHOP_NHIEU_DOT"),
            "theo_hd": sum(1 for r in rows if r.get("theo_hd")), "gan_tay": sum(1 for r in rows if r.get("gan_tay")),
            "mot_phan": len(mp), "mot_phan_tien": tien(mp), "con_thieu": sum(r.get("con_thieu") or 0 for r in mp),
            "chi_sk": len(csk), "chi_sk_tien": tien(csk), "chi_app": len(capp), "chi_app_tien": tien(capp),
            "nghi_gop": len(nghi), "nghi_gop_tien": tien(nghi), "coc": len(coc_rows), "coc_tien": tien(coc_rows),
            "bo_khop": len(bo), "khac_doi_tac": len(khac_dt)}
    pt = []
    for chieu, nhan, sk_t, app_t, dong_tu in (("RA", "Tiền RA", sk_ra, app_ra, "lệnh Duyệt chi NH"),
                                               ("VAO", "Tiền VÀO", sk_vao, app_vao, "thu công nợ bán hàng")):
        k2 = [r for r in kh if r["chieu"] == chieu]
        m2 = [r for r in mp if r["chieu"] == chieu]
        c2 = [r for r in csk if r["chieu"] == chieu]
        nhom_cnt = {}
        for r in c2:
            nhom_cnt.setdefault(r["nhom"], [0, 0.0])
            nhom_cnt[r["nhom"]][0] += 1
            nhom_cnt[r["nhom"]][1] += r["sk"]["so_tien"]
        phan_s = ", ".join(f"{_SK_NHOM_TEN[k]} {v[0]} khoản ({_sk_vnd(v[1])})" for k, v in nhom_cnt.items() if k)
        ro = nhom_cnt.get(None, [0, 0.0])
        n_gop = sum(1 for r in k2 if r["ket_qua"] == "KHOP_GOP")
        n_dot = sum(1 for r in k2 if r["ket_qua"] == "KHOP_NHIEU_DOT")
        n_hd = sum(1 for r in k2 if r.get("theo_hd"))
        cau = (f"{nhan}: sao kê {_sk_vnd(sk_t)} · {dong_tu} trong kỳ {_sk_vnd(app_t)} → khớp {len(k2)} khoản ({_sk_vnd(tien(k2))})")
        if n_gop or n_dot or n_hd:
            cau += f" [theo số HĐ {n_hd}, trả gộp {n_gop}, nhiều đợt {n_dot}]"
        if m2:
            cau += f"; trả một phần / thiếu {len(m2)} khoản, còn chênh {_sk_vnd(sum(r.get('con_thieu') or 0 for r in m2))}"
        if c2:
            cau += f"; {len(c2)} khoản ({_sk_vnd(tien(c2))}) ngân hàng có mà app không có"
            if phan_s:
                cau += f": {phan_s}"
            if ro[0]:
                cau += f"; còn {ro[0]} khoản ({_sk_vnd(ro[1])}) chưa rõ nguồn — cần rà"
        else:
            cau += "; không có khoản nào chỉ có trên sao kê"
        pt.append(cau + ".")
    if nghi:
        pt.append(f"? {len(nghi)} khoản ({_sk_vnd(tien(nghi))}) trùng tổng tiền với 2–3 khoản app nhưng nội dung chuyển khoản không nêu "
                  "đối tác / số hóa đơn — chưa tự ghi, kế toán xác nhận bằng 🔗 Gắn hoặc ✕ Bỏ khớp.")
    if coc_rows:
        n_coc_ok = sum(1 for r in coc_rows if r["ket_qua"] == "KHOP")
        pt.append(f"💰 {len(coc_rows)} khoản cọc / trả trước ({_sk_vnd(tien(coc_rows))}) đi riêng, không ghép với hóa đơn"
                  + (f" — {n_coc_ok} đã nối phiếu thu tạm ứng" if n_coc_ok else "")
                  + "; tiền vào: lập phiếu thu tạm ứng để cấn trừ khi xuất hóa đơn · tiền ra: ghi đợt cọc trên PO.")
    n_hd_thieu = sum(1 for r in rows if r["ket_qua"] in ("CHI_SK", "THEO_HD_THIEU") and "CHƯA CÓ trong app" in (r.get("phan_tich") or ""))
    if n_hd_thieu:
        pt.append(f"📄 {n_hd_thieu} dòng sao kê ghi số hóa đơn mà app chưa có hóa đơn / công nợ tương ứng — kế toán nhập trước rồi 🔁 Đối soát lại.")
    if capp:
        n_duyet = sum(1 for r in capp if any("DUYỆT" in (a.get("trang_thai") or "") for a in r["app"]))
        pt.append(f"App có nhưng sao kê không có: {len(capp)} khoản ({_sk_vnd(tien(capp))}) — {n_duyet} lệnh đã duyệt chưa chi, "
                  f"{len(capp) - n_duyet} khoản app ghi đã chi / đã thu mà ngân hàng không thấy → rà gấp.")
    else:
        pt.append("Mọi khoản app ghi trong kỳ đều thấy trên sao kê.")
    if khac_dt:
        pt.append(f"⚠ {len(khac_dt)} khoản khớp số tiền nhưng tên đối tác trên sao kê KHÁC đối tác trong app — kiểm tra trước khi tin.")
    if not csk and not capp and not mp and not nghi:
        pt.append("✅ Sao kê và app khớp hoàn toàn trong kỳ này" + (" (ngoài các khoản cọc đi riêng)." if coc_rows else "."))
    else:
        pt.append(f"Chênh lệch: tiền ra sao kê − app = {_sk_vnd(sk_ra - app_ra)} · tiền vào sao kê − app = {_sk_vnd(sk_vao - app_vao)}.")
    return {"tong": tong, "phan_tich": pt, "rows": rows, "_auto": auto}


# ============ ✍ GẮN TAY / BỎ KHỚP / CỌC trên từng dòng sao kê (mig 148) — CEO · ADMIN · KTT ============
_SK_LOAI_GAN = ("LENH_CHI", "THU_CN_BAN", "CN_HOAN_THANH", "TAM_UNG_THU")


class SkKhoanVao(_BRBase):
    loai: str
    id: int
    so_tien: float | None = None


class SkGanVao(_BRBase):
    khoan: list[SkKhoanVao]
    ghi_chu: str | None = None


class SkLyDoVao(_BRBase):
    ly_do: str | None = None
    phieu_id: int | None = None


def _sk_dong_404(db, dong_id):
    from ..models import SaoKeDong
    d = db.get(SaoKeDong, dong_id)
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dòng sao kê")
    return d


@router.get("/sao-ke/{sk_id}/ung-vien")
def sk_ung_vien(sk_id: int, chieu: str | None = None, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Khoản app trong kỳ (± 7 ngày) để kế toán 🔗 gắn tay: lệnh Duyệt chi NH · thu công nợ bán hàng · công nợ hoàn thành ·
    phiếu thu tạm ứng — kèm số HĐ, mã, đối tác."""
    from ..models import SaoKeBank
    sk = db.get(SaoKeBank, sk_id)
    if sk is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sao kê")
    tu = (sk.tu_ngay or date.today()) - timedelta(days=7)
    den = (sk.den_ngay or date.today()) + timedelta(days=7)
    ra, vao, coc_vao = _sk_ung_vien(db, tu, den)

    def _o(u):
        return {**_sk_u_out(u), "chieu": u["chieu"], "so_hd": sorted(u.get("so_hd") or []), "ma": u.get("ma")}
    out = {"ra": [_o(u) for u in ra], "vao": [_o(u) for u in vao + coc_vao]}
    if chieu in ("RA", "VAO"):
        return {chieu.lower(): out[chieu.lower()]}
    return out


@router.post("/sao-ke/dong/{dong_id}/gan")
def sk_gan_tay(dong_id: int, data: SkGanVao, db: Session = Depends(get_db),
               nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT"))):
    """🔗 Gắn tay một dòng sao kê với một hoặc nhiều khoản app (số tiền từng khoản) — giữ qua các lần 🔁 Đối soát."""
    from decimal import Decimal as _Dec
    from ..models import SaoKeKhop
    d = _sk_dong_404(db, dong_id)
    if not data.khoan:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chọn ít nhất một khoản app")
    for k in data.khoan:
        if k.loai not in _SK_LOAI_GAN:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Loại khoản không hợp lệ: {k.loai}")
    db.query(SaoKeKhop).filter_by(dong_id=d.id).delete()
    for k in data.khoan:
        db.add(SaoKeKhop(dong_id=d.id, loai=k.loai, khoan_id=k.id, so_tien=_Dec(str(round(k.so_tien or 0))),
                         ghi_chu=(data.ghi_chu or "").strip()[:300] or None, nguoi_dung_id=nd.id))
    d.khop_loai = "GAN_TAY"
    d.khop_id = data.khoan[0].id
    d.khop_mo_ta = ("gắn tay: " + ", ".join(f"{k.loai}#{k.id}" for k in data.khoan))[:300]
    ghi_audit(db, nd.id, "GAN_SAO_KE", "sao_ke_dong", d.id,
              moi={"khoan": [{"loai": k.loai, "id": k.id, "so_tien": k.so_tien} for k in data.khoan], "ghi_chu": data.ghi_chu})
    kq = _doi_soat_sao_ke(db, d.sao_ke_id)
    db.commit()
    return {"ok": True, "doi_soat": {"khop": kq["khop"], "chua_khop": kq["chua_khop"], "tong_dong": kq["tong_dong"]}}


@router.post("/sao-ke/dong/{dong_id}/bo-khop")
def sk_bo_khop(dong_id: int, data: SkLyDoVao, db: Session = Depends(get_db),
               nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT"))):
    """✕ Kế toán xác nhận dòng sao kê KHÔNG khớp khoản app nào (máy ghép sai, VD tổng hóa đơn trùng tiền cọc)."""
    from ..models import SaoKeKhop
    d = _sk_dong_404(db, dong_id)
    db.query(SaoKeKhop).filter_by(dong_id=d.id).delete()
    d.khop_loai, d.khop_id = "BO_KHOP", None
    d.khop_mo_ta = (data.ly_do or "").strip()[:300] or None
    ghi_audit(db, nd.id, "BO_KHOP_SAO_KE", "sao_ke_dong", d.id, moi={"ly_do": data.ly_do})
    kq = _doi_soat_sao_ke(db, d.sao_ke_id)
    db.commit()
    return {"ok": True, "doi_soat": {"khop": kq["khop"], "chua_khop": kq["chua_khop"], "tong_dong": kq["tong_dong"]}}


@router.post("/sao-ke/dong/{dong_id}/coc")
def sk_ghi_coc(dong_id: int, data: SkLyDoVao, db: Session = Depends(get_db),
               nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT"))):
    """💰 Ghi nhận dòng sao kê là tiền cọc / trả trước (không ghép hóa đơn); tùy chọn nối phiếu thu tạm ứng."""
    from ..models import SaoKeKhop, PhieuThuChi
    d = _sk_dong_404(db, dong_id)
    if data.phieu_id:
        p = db.get(PhieuThuChi, data.phieu_id)
        if p is None or not p.la_tam_ung:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiếu thu tạm ứng")
    db.query(SaoKeKhop).filter_by(dong_id=d.id).delete()
    d.khop_loai, d.khop_id = "COC_SK", (data.phieu_id or None)
    d.khop_mo_ta = (data.ly_do or "").strip()[:300] or None
    ghi_audit(db, nd.id, "COC_SAO_KE", "sao_ke_dong", d.id, moi={"phieu_id": data.phieu_id, "ly_do": data.ly_do})
    kq = _doi_soat_sao_ke(db, d.sao_ke_id)
    db.commit()
    return {"ok": True, "doi_soat": {"khop": kq["khop"], "chua_khop": kq["chua_khop"], "tong_dong": kq["tong_dong"]}}


@router.post("/sao-ke/dong/{dong_id}/mo-lai")
def sk_mo_lai(dong_id: int, db: Session = Depends(get_db),
              nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT"))):
    """↺ Bỏ nhãn ghi tay (gắn tay / bỏ khớp / cọc) để máy ghép lại dòng này."""
    from ..models import SaoKeKhop
    d = _sk_dong_404(db, dong_id)
    if d.khop_loai not in ("GAN_TAY", "BO_KHOP", "COC_SK"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dòng này không có nhãn gắn tay / bỏ khớp / cọc")
    db.query(SaoKeKhop).filter_by(dong_id=d.id).delete()
    cu = d.khop_loai
    d.khop_loai, d.khop_id, d.khop_mo_ta = None, None, None
    ghi_audit(db, nd.id, "MO_LAI_SAO_KE", "sao_ke_dong", d.id, cu={"khop_loai": cu})
    kq = _doi_soat_sao_ke(db, d.sao_ke_id)
    db.commit()
    return {"ok": True, "doi_soat": {"khop": kq["khop"], "chua_khop": kq["chua_khop"], "tong_dong": kq["tong_dong"]}}


@router.get("/sao-ke/{sk_id}/so-sanh")
def so_sanh_sao_ke(sk_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Bảng hợp nhất sao kê ↔ app (Duyệt chi NH · thu công nợ bán hàng), ngày mới lên trên, kèm phân tích."""
    from ..models import SaoKeBank, SaoKeDong
    sk = db.get(SaoKeBank, sk_id)
    if sk is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sao kê")
    dongs = (db.query(SaoKeDong).filter_by(sao_ke_id=sk_id).order_by(SaoKeDong.ngay, SaoKeDong.id).all())
    kq = _sk_so_sanh(db, sk, dongs)
    kq.pop("_auto", None)
    return {"id": sk.id, "ten_file": sk.ten_file, "ngan_hang": sk.ngan_hang,
            "tu_ngay": str(sk.tu_ngay) if sk.tu_ngay else None,
            "den_ngay": str(sk.den_ngay) if sk.den_ngay else None, **kq}


# ---- 📥 XUẤT EXCEL bảng đối soát (kế toán kiểm tra lại) — mỗi khoản một dòng, lọc theo kết quả; sheet tổng hợp + phân tích ----
_SK_KQ_TEN = {"KHOP": "✓ Khớp", "KHOP_GOP": "✓ Trả gộp", "KHOP_NHIEU_DOT": "✓ Nhiều đợt", "MOT_PHAN": "◐ Một phần",
              "THEO_HD_THIEU": "◐ Theo số HĐ, còn chênh", "NGHI_GOP": "? Nghi gộp — cần xác nhận",
              "COC_KH": "💰 Cọc / trả trước", "COC_NCC": "💰 Cọc NCC", "BO_KHOP": "✕ Không khớp (đã xem)",
              "CHI_SK": "⚠ Chỉ có trên sao kê", "CHI_APP": "⚠ Chỉ có trong app"}


def _sk_xuat_excel_bytes(sk_info: dict, kq: dict) -> bytes:
    """Dựng file Excel từ kết quả _sk_so_sanh: sheet «Đối soát» (mỗi khoản app / dòng sao kê một dòng, STT nhóm để lọc),
    sheet «Tổng hợp» (thẻ tổng + phân tích). Không công thức — số liệu để kế toán đối chiếu lại."""
    import io as _io
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    ws = wb.active
    ws.title = "Đối soát"
    ten = f"ĐỐI SOÁT SAO KÊ ↔ APP — {sk_info.get('ten_file') or ''}"
    if sk_info.get("ngan_hang"):
        ten += f" · {sk_info['ngan_hang']}"
    ten += f" · kỳ {sk_info.get('tu_ngay') or '—'} → {sk_info.get('den_ngay') or '—'}"
    ws["A1"] = ten
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = ("Tiền ra so với lệnh Duyệt chi Ngân hàng (Nhà cung cấp) · tiền vào so với thu công nợ bán hàng (Bán hàng) và phiếu thu "
                "tạm ứng · ghép theo số hóa đơn / mã / cọc đọc từ nội dung chuyển khoản. Mỗi khoản một dòng; cột A là số nhóm — "
                "các dòng cùng nhóm là một cặp đối chiếu. Lọc cột D để xem từng loại kết quả.")
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A2:Q2")
    ws.row_dimensions[2].height = 42
    cot = ["Nhóm", "Ngày", "Thu / Chi", "Kết quả", "Nhãn", "Khoản ở APP", "Ngày app", "Trạng thái app", "Tiền app (đ)",
           "Dòng SAO KÊ (diễn giải)", "Ngày sao kê", "Đối tác (đọc từ diễn giải)", "Số HĐ / mã đọc được", "Tiền sao kê (đ)",
           "Chênh lệch nhóm (sao kê − app)", "Phân tích", "Nhóm chi phí"]
    rong = [7, 11, 9, 24, 18, 44, 11, 30, 16, 48, 11, 30, 22, 16, 18, 70, 14]
    hdr_row = 4
    fill = PatternFill("solid", fgColor="E3EDF6")
    thin = Side(style="thin", color="C9D3DD")
    bd = Border(left=thin, right=thin, top=thin, bottom=thin)
    for i, (c, w) in enumerate(zip(cot, rong), 1):
        cell = ws.cell(row=hdr_row, column=i, value=c)
        cell.font = Font(bold=True)
        cell.fill = fill
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        cell.border = bd
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[hdr_row].height = 30
    mau_nen = {"CHI_SK": "FFF7ED", "CHI_APP": "FEF2F2", "MOT_PHAN": "FFFBEB", "THEO_HD_THIEU": "FFFBEB", "NGHI_GOP": "FFFBEB",
               "COC_KH": "EEF6FF", "COC_NCC": "EEF6FF", "BO_KHOP": "F8FAFC"}
    r_i = hdr_row + 1
    for stt, r in enumerate(kq.get("rows") or [], 1):
        apps = r.get("app") or []
        sks = r.get("sk_list") or ([r["sk"]] if r.get("sk") else [])
        n = max(len(apps), len(sks), 1)
        tong_app = sum(float(a.get("so_tien") or 0) for a in apps)
        tong_sk = sum(float(x.get("so_tien") or 0) for x in sks)
        nhan = []
        if r.get("theo_hd"):
            nhan.append("theo số HĐ")
        if r.get("gan_tay"):
            nhan.append("ghi tay")
        if r.get("khac_doi_tac"):
            nhan.append("khác đối tác")
        if r.get("coc"):
            nhan.append("cọc")
        chieu = "Thu (vào)" if r.get("chieu") == "VAO" else "Chi (ra)"
        nen = mau_nen.get(r.get("ket_qua"))
        for i in range(n):
            a = apps[i] if i < len(apps) else None
            x = sks[i] if i < len(sks) else None
            vals = [stt if i == 0 else None, r.get("ngay") if i == 0 else None, chieu if i == 0 else None,
                    _SK_KQ_TEN.get(r.get("ket_qua"), r.get("ket_qua")) if i == 0 else None,
                    ", ".join(nhan) if (i == 0 and nhan) else None,
                    (a or {}).get("mo_ta"), (a or {}).get("ngay"), (a or {}).get("trang_thai"),
                    float(a.get("so_tien") or 0) if a else None,
                    (x or {}).get("dien_giai"), (x or {}).get("ngay"), (x or {}).get("doi_tac"),
                    (" · ".join(filter(None, [("HĐ " + ", ".join(x.get("so_hd") or [])) if x.get("so_hd") else None,
                                              " ".join(x.get("ma") or []) or None])) or None) if x else None,
                    float(x.get("so_tien") or 0) if x else None,
                    (tong_sk - tong_app) if (i == 0 and apps and sks) else None,
                    r.get("phan_tich") if i == 0 else None,
                    (_SK_NHOM_TEN.get(r.get("nhom")) if r.get("nhom") in _SK_NHOM_TEN else ("cọc" if r.get("nhom") == "COC" else None)) if i == 0 else None]
            for j, v in enumerate(vals, 1):
                cell = ws.cell(row=r_i, column=j, value=v)
                cell.border = bd
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                if j in (9, 14, 15):
                    cell.number_format = "#,##0;[Red]-#,##0"
                if nen:
                    cell.fill = PatternFill("solid", fgColor=nen)
            r_i += 1
    ws.freeze_panes = ws.cell(row=hdr_row + 1, column=1)
    if r_i > hdr_row + 1:
        ws.auto_filter.ref = f"A{hdr_row}:{get_column_letter(len(cot))}{r_i - 1}"
    # ---- sheet tổng hợp ----
    w2 = wb.create_sheet("Tổng hợp")
    t = kq.get("tong") or {}
    w2["A1"] = ten
    w2["A1"].font = Font(bold=True, size=13)
    dong2 = [("Dòng sao kê", t.get("dong")), ("Tiền vào theo sao kê (đ)", t.get("sk_vao")), ("Tiền vào app thu công nợ (đ)", t.get("app_vao")),
             ("Tiền ra theo sao kê (đ)", t.get("sk_ra")), ("Tiền ra app Duyệt chi NH (đ)", t.get("app_ra")),
             ("Khớp app ↔ sao kê (khoản)", t.get("khop")), ("Tiền khớp (đ)", t.get("khop_tien")),
             ("Trong đó khớp theo số hóa đơn", t.get("theo_hd")), ("Trong đó nhiều đợt", t.get("nhieu_dot")), ("Trong đó ghi tay", t.get("gan_tay")),
             ("Một phần / còn chênh (khoản)", t.get("mot_phan")), ("Còn chênh (đ)", t.get("con_thieu")),
             ("Nghi gộp — cần xác nhận (khoản)", t.get("nghi_gop")), ("Cọc / trả trước đi riêng (khoản)", t.get("coc")), ("Tiền cọc (đ)", t.get("coc_tien")),
             ("Chỉ có trên sao kê (khoản)", t.get("chi_sk")), ("Tiền chỉ sao kê (đ)", t.get("chi_sk_tien")),
             ("Chỉ có trong app (khoản)", t.get("chi_app")), ("Tiền chỉ app (đ)", t.get("chi_app_tien")),
             ("Không khớp đã xem (khoản)", t.get("bo_khop")), ("Khớp tiền nhưng khác đối tác (khoản)", t.get("khac_doi_tac"))]
    for i, (k, v) in enumerate(dong2, 3):
        w2.cell(row=i, column=1, value=k)
        c = w2.cell(row=i, column=2, value=v)
        c.number_format = "#,##0"
    w2.column_dimensions["A"].width = 42
    w2.column_dimensions["B"].width = 20
    r2 = len(dong2) + 5
    w2.cell(row=r2, column=1, value="PHÂN TÍCH SAU KHI SO SÁNH").font = Font(bold=True)
    for i, p in enumerate(kq.get("phan_tich") or [], r2 + 1):
        c = w2.cell(row=i, column=1, value=p)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        w2.merge_cells(start_row=i, start_column=1, end_row=i, end_column=6)
        w2.row_dimensions[i].height = 32
    r3 = r2 + len(kq.get("phan_tich") or []) + 3
    w2.cell(row=r3, column=1, value="CHÚ GIẢI KẾT QUẢ").font = Font(bold=True)
    for i, (k, v) in enumerate(_SK_KQ_TEN.items(), r3 + 1):
        w2.cell(row=i, column=1, value=v)
        w2.cell(row=i, column=2, value={
            "KHOP": "một dòng sao kê = một khoản app (cùng tiền ± phí, gần ngày, ưu tiên cùng đối tác / số HĐ / mã)",
            "KHOP_GOP": "một dòng sao kê trả cho nhiều khoản app (theo số HĐ, hoặc cùng đối tác)",
            "KHOP_NHIEU_DOT": "một khoản app nhận nhiều dòng sao kê",
            "MOT_PHAN": "đã thấy một phần tiền trên sao kê, còn thiếu phần ghi ở cột chênh lệch",
            "THEO_HD_THIEU": "nội dung CK ghi nhiều số HĐ, app chỉ có một phần — HĐ thiếu nêu ở phân tích",
            "NGHI_GOP": "tổng 2–3 khoản trùng tiền nhưng nội dung không nêu đối tác / HĐ — chưa tự ghi",
            "COC_KH": "tiền vào ghi cọc / tạm ứng / trả trước — không ghép hóa đơn, nối phiếu thu tạm ứng",
            "COC_NCC": "tiền ra ghi cọc / tạm ứng cho NCC — ghi đợt cọc trên PO",
            "BO_KHOP": "kế toán xác nhận dòng không khớp khoản app nào",
            "CHI_SK": "ngân hàng có, app chưa có (phân tích nêu nhóm chi phí hoặc HĐ cần nhập)",
            "CHI_APP": "app ghi có, sao kê không thấy"}.get(k, ""))
    bio = _io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


@router.get("/sao-ke/{sk_id}/xuat-excel")
def xuat_excel_sao_ke(sk_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """📥 Xuất bảng đối soát sao kê ↔ app ra Excel để kế toán kiểm tra lại."""
    from fastapi.responses import Response
    from ..models import SaoKeBank, SaoKeDong
    sk = db.get(SaoKeBank, sk_id)
    if sk is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sao kê")
    dongs = (db.query(SaoKeDong).filter_by(sao_ke_id=sk_id).order_by(SaoKeDong.ngay, SaoKeDong.id).all())
    kq = _sk_so_sanh(db, sk, dongs)
    info = {"ten_file": sk.ten_file, "ngan_hang": sk.ngan_hang,
            "tu_ngay": str(sk.tu_ngay) if sk.tu_ngay else None, "den_ngay": str(sk.den_ngay) if sk.den_ngay else None}
    data = _sk_xuat_excel_bytes(info, kq)
    ten = f"Doi-soat-sao-ke-{sk.id}_{info['tu_ngay'] or ''}_{info['den_ngay'] or ''}.xlsx".replace("__", "_")
    return Response(content=data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{ten}"', "Cache-Control": "no-store"})


# ---- 📅 Mỗi tháng 1 sao kê: từ NGÀY 7 hàng tháng chưa thấy sao kê tháng trước → nhắc nhóm Duyệt chi NH ----
NGAY_NHAC_SAO_KE = 7


def _sk_thang_truoc(hom_nay: date):
    dau = hom_nay.replace(day=1)
    cuoi_truoc = dau - timedelta(days=1)
    return cuoi_truoc.replace(day=1), cuoi_truoc


def _sk_co_sao_ke(db: Session, tu: date, den: date) -> bool:
    from ..models import SaoKeBank
    return db.query(SaoKeBank).filter(SaoKeBank.tu_ngay <= den, SaoKeBank.den_ngay >= tu).first() is not None


def trang_thai_nhac_sao_ke(db: Session) -> dict:
    from ..models import NhacSaoKeThang
    from ..nhac_viec_service import gio_hien_tai
    from ..config import settings as _st
    hom = gio_hien_tai().date()
    tu, den = _sk_thang_truoc(hom)
    key = tu.strftime("%Y-%m")
    da = db.get(NhacSaoKeThang, key)
    return {"thang": key, "thang_hien": tu.strftime("%m/%Y"), "co_sao_ke": _sk_co_sao_ke(db, tu, den),
            "da_nhac_luc": str(da.gui_luc)[:16] if (da and da.gui_luc) else None,
            "webhook": bool((_st.gchat_webhook_duyet_chi or "").strip()), "ngay_nhac": NGAY_NHAC_SAO_KE,
            "den_han": hom.day >= NGAY_NHAC_SAO_KE}


def nhac_sao_ke_thang(db: Session, ep: bool = False, nguoi: str | None = None) -> dict:
    """Gửi nhắc vào nhóm Duyệt chi NH nếu tháng trước chưa có sao kê; mỗi tháng 1 lần (ep=True: gửi lại theo tay)."""
    from ..models import NhacSaoKeThang
    from ..nhac_viec_service import gio_hien_tai
    from ..chat_gateway import gui_webhook_rieng
    from ..config import settings as _st
    tt = trang_thai_nhac_sao_ke(db)
    if tt["co_sao_ke"]:
        return {"da_gui": False, "ly_do": "đã có sao kê", **tt}
    if tt["da_nhac_luc"] and not ep:
        return {"da_gui": False, "ly_do": "đã nhắc", **tt}
    text = (f"🧾 *NHẮC ĐỐI SOÁT SAO KÊ NGÂN HÀNG* — chưa thấy sao kê tháng *{tt['thang_hien']}* được tải lên app.\n"
            "Đề nghị kế toán tải file sao kê (PDF / Excel) tại *Overall Financial › Đối soát SAO KÊ ngân hàng* để so với "
            "lệnh Duyệt chi NH và thu công nợ bán hàng. Mỗi tháng một sao kê; app nhắc từ ngày "
            f"{NGAY_NHAC_SAO_KE} hàng tháng." + (f" (gửi tay bởi {nguoi})" if nguoi else ""))
    kq = gui_webhook_rieng((_st.gchat_webhook_duyet_chi or "").strip(), text)
    if kq.get("da_gui"):
        r = db.get(NhacSaoKeThang, tt["thang"])
        if r is None:
            r = NhacSaoKeThang(thang=tt["thang"])
            db.add(r)
        r.gui_luc = gio_hien_tai()
        r.ket_qua = {"nguoi": nguoi, "ep": ep}
        db.commit()
    return {**kq, **tt}


@router.get("/sao-ke/nhac-thang")
def xem_nhac_sao_ke(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return trang_thai_nhac_sao_ke(db)


@router.post("/sao-ke/nhac-thang")
def gui_nhac_sao_ke(db: Session = Depends(get_db), nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT"))):
    """📣 Nhắc ngay nhóm Duyệt chi NH tải sao kê tháng trước (gửi lại được dù đã nhắc)."""
    kq = nhac_sao_ke_thang(db, ep=True, nguoi=(getattr(nd, "ho_ten", None) or nd.email))
    if kq.get("co_sao_ke"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Tháng {kq['thang_hien']} đã có sao kê — không cần nhắc")
    if not kq.get("da_gui"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, kq.get("loi") or "Không gửi được")
    ghi_audit(db, nd.id, "NHAC_SAO_KE", "nhac_sao_ke_thang", None, moi={"thang": kq["thang"]})
    db.commit()
    return kq


@router.get("/sao-ke/{sk_id}")
def chi_tiet_sao_ke(sk_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    from ..models import SaoKeBank, SaoKeDong
    sk = db.get(SaoKeBank, sk_id)
    if sk is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sao kê")
    dongs = (db.query(SaoKeDong).filter_by(sao_ke_id=sk_id)
             .order_by(SaoKeDong.ngay, SaoKeDong.id).all())
    tu = (sk.tu_ngay or date.today()) - timedelta(days=5)
    den = (sk.den_ngay or date.today()) + timedelta(days=5)
    ung = _ung_vien_sao_ke(db, tu, den)
    da_dung = {(d.khop_loai, d.khop_id) for d in dongs if d.khop_loai}
    return {"id": sk.id, "ten_file": sk.ten_file, "ngan_hang": sk.ngan_hang,
            "tu_ngay": str(sk.tu_ngay) if sk.tu_ngay else None,
            "den_ngay": str(sk.den_ngay) if sk.den_ngay else None,
            "dong": [{"id": d.id, "ngay": str(d.ngay) if d.ngay else None,
                      "dien_giai": d.dien_giai,
                      "tien_vao": float(d.tien_vao or 0), "tien_ra": float(d.tien_ra or 0),
                      "so_du": float(d.so_du) if d.so_du is not None else None,
                      "khop_loai": d.khop_loai, "khop_mo_ta": d.khop_mo_ta} for d in dongs],
            "app_thieu": _thieu_tren_sao_ke(sk, ung, da_dung)}


@router.post("/sao-ke/{sk_id}/doi-soat")
def doi_soat_sao_ke(sk_id: int, db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT"))):
    """🔁 Chạy lại đối soát (sau khi kế toán bổ sung phiếu / duyệt thêm lệnh chi)."""
    from ..models import SaoKeBank
    if db.get(SaoKeBank, sk_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sao kê")
    kq = _doi_soat_sao_ke(db, sk_id)
    ghi_audit(db, nd.id, "DOI_SOAT_SAO_KE", "sao_ke_bank", sk_id,
              moi={"khop": kq["khop"], "chua_khop": kq["chua_khop"]})
    db.commit()
    return kq


@router.delete("/sao-ke/{sk_id}")
def xoa_sao_ke(sk_id: int, db: Session = Depends(get_db),
               nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import SaoKeBank, SaoKeDong
    sk = db.get(SaoKeBank, sk_id)
    if sk is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sao kê")
    db.query(SaoKeDong).filter_by(sao_ke_id=sk_id).delete()
    ghi_audit(db, nd.id, "XOA", "sao_ke_bank", sk_id,
              cu={"file": sk.ten_file, "so_dong": sk.so_dong})
    db.delete(sk)
    db.commit()
    return {"ok": True}


# =====================================================================================
# 📊 DOANH THU THEO MẢNG (Overall Financial): TM thương mại · DV dịch vụ · DA dự án (+ Khác) —
# cùng công thức Lãi/Lỗ Record (_tinh_lai_lo_tong) và dòng tiền thật theo mã (lai_lo_ma.dong_tien_theo_ma),
# nên tổng các mảng = tổng Lãi/Lỗ Record.
# =====================================================================================
_MANG_TEN = {"TM": "Thương mại", "DV": "Dịch vụ", "DA": "Dự án", "KHAC": "Khác (OP · chưa phân mảng)"}


def _mang_cua(ma) -> str:
    from ..ma_code import phan_tich
    l = phan_tich(ma)["loai"]
    return l if l in ("TM", "DV", "DA") else "KHAC"


@router.get("/doanh-thu-theo-mang")
def doanh_thu_theo_mang(nam: int | None = None, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM")),
                        __=Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import DonHang, DonMua, HoaDon
    from ..lai_lo_ma import dong_tien_theo_ma
    from ..nhac_viec_service import gio_hien_tai
    hom_nay = gio_hien_tai().date()
    nam = nam or hom_nay.year
    seg = {k: {"ma": k, "ten": v, "so_ma": 0, "doanh_thu": 0.0, "chi_phi": 0.0, "da_thu": 0.0, "da_chi": 0.0,
               "con_phai_thu": 0.0, "con_phai_tra": 0.0, "so_cn_thu": 0, "so_cn_tra": 0, "top": []}
           for k, v in _MANG_TEN.items()}
    # ① doanh thu / chi phí theo mã (Lãi/Lỗ Record)
    t = _tinh_lai_lo_tong(db)
    for x in t.get("theo_ma") or []:
        if x.get("la_dau_tu"):
            continue                                   # 🏗 vốn đầu tư cho thuê: tài sản, không phải doanh thu
        s = seg[_mang_cua(x.get("ma_ban"))]
        s["so_ma"] += 1
        s["doanh_thu"] += float(x.get("doanh_thu") or 0)
        s["chi_phi"] += float(x.get("tong_chi_phi") or 0)
        s["top"].append({"ma": x.get("ma_ban"), "doanh_thu": float(x.get("doanh_thu") or 0),
                         "chi_phi": float(x.get("tong_chi_phi") or 0), "lai": float(x.get("loi_nhuan") or 0)})
    # ② tiền thật đã thu / đã chi theo mã
    for k, o in dong_tien_theo_ma(db).items():
        s = seg[_mang_cua(o.get("ma"))] if o.get("ma") and o.get("ma") != "(không gắn)" else seg["KHAC"]
        s["da_thu"] += float(o.get("thu") or 0)
        s["da_chi"] += float(o.get("chi") or 0)
    # ③ công nợ còn lại theo mảng
    so_dh = {i: (s or "").strip() for (i, s) in db.query(DonHang.id, DonHang.so).all()}
    hd_dh = {i: d for (i, d) in db.query(HoaDon.id, HoaDon.don_hang_id).filter(HoaDon.don_hang_id.isnot(None)).all()}
    po_ma = {i: (so_dh.get(dh) or (mb or "").strip()) for (i, dh, mb) in db.query(DonMua.id, DonMua.don_hang_id, DonMua.ma_ban).all()}

    def ma_cn(c):
        if c.loai == "PHAI_TRA":
            if c.don_mua_id:
                return po_ma.get(c.don_mua_id)
            if c.hoa_don_id and hd_dh.get(c.hoa_don_id):
                return so_dh.get(hd_dh[c.hoa_don_id])
            return (c.ma_ban_ngoai or "").strip() or None
        dh_id = c.don_hang_id or (hd_dh.get(c.hoa_don_id) if c.hoa_don_id else None)
        return so_dh.get(dh_id) if dh_id else ((c.ma_ban_ngoai or "").strip() or None)

    for c in db.query(CongNo).filter(CongNo.trang_thai != "THU_DU").all():
        con = float(c.so_tien or 0) - float(c.da_thanh_toan or 0)
        if con <= 0:
            continue
        s = seg[_mang_cua(ma_cn(c))]
        if c.loai == "PHAI_THU":
            s["con_phai_thu"] += con; s["so_cn_thu"] += 1
        else:
            s["con_phai_tra"] += con; s["so_cn_tra"] += 1
    # ④ theo tháng của năm: doanh thu hóa đơn BÁN · đã thu (sổ thanh toán phải thu) · đã chi (sổ thanh toán phải trả)
    thang = {f"{nam}-{m:02d}": {k: {"dt": 0.0, "thu": 0.0, "chi": 0.0} for k in _MANG_TEN} for m in range(1, 13)}
    for hd in db.query(HoaDon).filter(HoaDon.loai == "BAN", HoaDon.ngay >= date(nam, 1, 1), HoaDon.ngay <= date(nam, 12, 31)).all():
        k = str(hd.ngay)[:7]
        ma = so_dh.get(hd.don_hang_id) if hd.don_hang_id else None
        if k in thang:
            thang[k][_mang_cua(ma)]["dt"] += float(hd.tong_tien or 0)
    cn_map = {c.id: c for c in db.query(CongNo).all()}
    for tt in db.query(ThanhToan).filter(ThanhToan.ngay >= date(nam, 1, 1), ThanhToan.ngay <= date(nam, 12, 31)).all():
        c = cn_map.get(tt.cong_no_id)
        if c is None:
            continue
        k = str(tt.ngay)[:7]
        if k not in thang:
            continue
        m = _mang_cua(ma_cn(c))
        thang[k][m]["thu" if c.loai == "PHAI_THU" else "chi"] += float(tt.so_tien or 0)
    out_mang = []
    for k in ("TM", "DV", "DA", "KHAC"):
        s = seg[k]
        s["lai"] = s["doanh_thu"] - s["chi_phi"]
        s["ty_suat"] = round(s["lai"] / s["doanh_thu"] * 100, 1) if s["doanh_thu"] else None
        s["dong_tien_rong"] = s["da_thu"] - s["da_chi"]
        s["top"] = sorted(s["top"], key=lambda x: -x["doanh_thu"])[:8]
        if k == "KHAC" and not (s["so_ma"] or s["da_thu"] or s["da_chi"] or s["con_phai_thu"] or s["con_phai_tra"]):
            continue
        out_mang.append(s)
    tong = {kk: sum(float(s[kk]) for s in out_mang) for kk in
            ("so_ma", "doanh_thu", "chi_phi", "lai", "da_thu", "da_chi", "dong_tien_rong", "con_phai_thu", "con_phai_tra")}
    theo_thang = [dict(thang=k, **{m: v[m] for m in _MANG_TEN}) for k, v in sorted(thang.items())]
    nam_co = sorted({int(str(n)[:4]) for (n,) in db.query(HoaDon.ngay).filter(HoaDon.loai == "BAN", HoaDon.ngay.isnot(None)).distinct().all()} | {hom_nay.year})
    return {"nam": nam, "nam_co": nam_co, "mang": out_mang, "tong": tong, "theo_thang": theo_thang,
            "ten": _MANG_TEN, "ngay_tinh": str(hom_nay)}

# ============ 🏗 ĐẦU TƯ / KHẤU HAO theo mã dự án cho thuê — Overall Financial (chỉ CEO) ============
def _thang_tu_den(tu: str, den: date) -> list:
    y, m = int(tu[:4]), int(tu[5:7])
    out = []
    while (y, m) <= (den.year, den.month):
        out.append(f"{y}-{m:02d}")
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def _tra_theo_thang_cn(db, cn_ids) -> dict:
    """Tiền THẬT đã trả cho các dòng công nợ phải trả, xếp theo tháng trả: sổ thanh toán (ThanhToan.ngay — lệnh chi công nợ
    ✔ Đã chi, khớp sao kê, ghi tay) + phiếu chi ĐÃ DUYỆT cấn vào công nợ (PhieuThuChi.ngay — đường lệnh chi PO).
    Cấn trừ tạm ứng không có dòng ngày → phần đó về «không rõ ngày». → {YYYY-MM: tiền}"""
    from ..models import PhieuThuChi
    out = {}
    ids = [i for i in cn_ids if i]
    if not ids:
        return out
    for (ngay, st) in db.query(ThanhToan.ngay, ThanhToan.so_tien).filter(ThanhToan.cong_no_id.in_(ids)).all():
        k = str(ngay)[:7] if ngay else None
        if k:
            out[k] = out.get(k, 0.0) + float(st or 0)
    for (ngay, st) in (db.query(PhieuThuChi.ngay, PhieuThuChi.so_tien)
                       .filter(PhieuThuChi.cong_no_id.in_(ids), PhieuThuChi.loai == "CHI",
                               PhieuThuChi.trang_thai == "DA_DUYET").all()):
        k = str(ngay)[:7] if ngay else None
        if k:
            out[k] = out.get(k, 0.0) + float(st or 0)
    return out


def _gan_thuc_chi(db, items):
    """Gắn THỰC CHI cho từng khoản vốn: da_tra (tiền thật đã trả NCC, lũy kế — sổ công nợ), tra_thang ({tháng: tiền}, tổng ≤ da_tra),
    theo_doi=False khi không theo dõi được (nguyên giá nhập tay, chi phí vận hành, phần chênh VAT).
    Phần đã trả CHƯA có dòng ngày trên sổ thanh toán (cọc / đợt ghi thẳng trên PO, không qua Duyệt chi) → lấy NGÀY GHI TRÊN PO:
    đợt thanh toán của PO (DonMuaDotTt.ngay), còn dư thì ngày thanh toán gần nhất của PO (ngay_tt) — tra_thang_po ({tháng: tiền},
    đã nằm trong tra_thang) để giao diện gắn nhãn «ngày theo PO» (kém chắc hơn sổ thanh toán)."""
    from ..models import DonMua, DonMuaDotTt
    from .ncc import _da_tra_that
    for it in items:
        it["theo_doi"], it["da_tra"], it["tra_thang"], it["tra_thang_po"] = True, 0.0, {}, {}
        cn_ids, dm = [], None
        if it.get("_dm"):
            dm = db.get(DonMua, it["_dm"])
            if dm is not None:
                it["da_tra"] = float(_da_tra_that(db, dm))
                cn_ids = [c for (c,) in db.query(CongNo.id).filter(CongNo.don_mua_id == dm.id).all()]
        elif it.get("_cn"):
            cn = db.get(CongNo, it["_cn"])
            if cn is not None:
                it["da_tra"] = float(cn.da_thanh_toan or 0)
                cn_ids = [cn.id]
        elif it.get("_hd"):
            cns = db.query(CongNo).filter(CongNo.loai == "PHAI_TRA", CongNo.hoa_don_id == it["_hd"]).all()
            it["da_tra"] = sum(float(c.da_thanh_toan or 0) for c in cns)
            cn_ids = [c.id for c in cns]
        else:
            it["theo_doi"] = False
            it["da_tra"] = None
        con, tt = float(it["da_tra"] or 0), {}
        if cn_ids and con > 0:
            tt = _tra_theo_thang_cn(db, cn_ids)
            for k in sorted(tt):                       # không vượt số đã trả thật (sổ công nợ là nguồn sự thật)
                v = min(float(tt[k]), con)
                if v <= 0:
                    break
                it["tra_thang"][k] = v
                con -= v
        if dm is not None and con > 0.5:               # phần đã trả chưa có dòng ngày trên sổ → ngày ghi trên PO
            dot = {}
            for (ngay, st) in db.query(DonMuaDotTt.ngay, DonMuaDotTt.so_tien).filter(DonMuaDotTt.don_mua_id == dm.id).all():
                if ngay:
                    dot[str(ngay)[:7]] = dot.get(str(ngay)[:7], 0.0) + float(st or 0)
            for k in sorted(dot):                      # đợt cùng tháng đã có dòng sổ thanh toán → không tính lần 2
                v = min(max(dot[k] - float(tt.get(k, 0.0)), 0.0), con)
                if v <= 0:
                    continue
                it["tra_thang_po"][k] = it["tra_thang_po"].get(k, 0.0) + v
                con -= v
            ngay_tt = dm.ngay_tt or dm.ngay_tt_du
            if con > 0.5 and ngay_tt:
                k = str(ngay_tt)[:7]
                it["tra_thang_po"][k] = it["tra_thang_po"].get(k, 0.0) + con
                con = 0.0
            for k, v in it["tra_thang_po"].items():
                it["tra_thang"][k] = it["tra_thang"].get(k, 0.0) + v
        for k in ("_dm", "_cn", "_hd"):
            it.pop(k, None)
    return items


def _dau_tu_items_du_an(db, ts, du_an_row, po_mm_items):
    """Khoản VỐN ĐẦU TƯ có NGÀY của một dự án cho thuê: nguyên giá đầu kỳ (ngày mua) · PO đã duyệt / công nợ nhập ngoài /
    hóa đơn mua ngoài PO / chi phí vận hành của các ĐƠN ĐẦU TƯ (loại trùng PO như chi_phi_ma) · PO / công nợ mang MÃ MẸ.
    → [{loai, so, ngay, tong, ma, da_tra, tra_thang, theo_doi}]"""
    from ..models import DonHang, DonMua, HoaDon, ChiPhiVanHanh
    from ..lai_lo_ma import po_trung_khoan, VH_TINH_CHI_PHI, LECH_TRUNG
    items = []
    if float(ts.nguyen_gia or 0) > 0:
        items.append({"loai": "NG", "so": "Nguyên giá đầu kỳ", "ngay": str(ts.ngay_mua) if ts.ngay_mua else None,
                      "tong": float(ts.nguyen_gia or 0), "ma": ts.ma})
    for d in du_an_row.get("don_dau_tu") or []:
        dh = db.get(DonHang, d["don_hang_id"])
        if dh is None:
            continue
        so = (dh.so or "").strip().lower()
        q = db.query(DonMua).filter(DonMua.trang_thai != "TU_CHOI")
        if so:
            q = q.filter((DonMua.don_hang_id == dh.id) | (DonMua.don_hang_id.is_(None) & (func.lower(func.trim(DonMua.ma_ban)) == so)))
        else:
            q = q.filter(DonMua.don_hang_id == dh.id)
        pos = q.all()
        po_ids = {p.id for p in pos}
        for p in pos:
            if p.trang_thai == "DA_DUYET":
                items.append({"loai": "PO", "so": p.so or f"PO-{p.id}", "ngay": str(p.ngay) if p.ngay else None,
                              "tong": float(p.tong_tien or 0), "ma": dh.so, "_dm": p.id})
        da_dung = set()
        if so:
            for c in db.query(CongNo).filter(CongNo.loai == "PHAI_TRA", CongNo.don_mua_id.is_(None), CongNo.hoa_don_id.is_(None),
                                             func.lower(CongNo.ma_ban_ngoai) == so).all():
                if str(c.so_ct or "").upper().startswith("HDM-"):
                    continue
                p = po_trung_khoan(pos, c.so_ct, c.nha_cung_cap_id, c.so_tien,
                                   float(c.so_tien or 0) - float(getattr(c, "tien_thue", 0) or 0), da_dung)
                ngay = str(c.ngay_ct or c.han) if (c.ngay_ct or c.han) else None
                if p is not None:
                    chenh = max(float(c.so_tien or 0) - float(p.tong_tien or 0), 0.0)
                    if chenh > LECH_TRUNG:
                        items.append({"loai": "CN", "so": f"{c.so_ct or 'CN-' + str(c.id)} (chênh VAT)", "ngay": ngay, "tong": chenh, "ma": dh.so})
                    continue
                items.append({"loai": "CN", "so": c.so_ct or f"CN-{c.id}", "ngay": ngay, "tong": float(c.so_tien or 0), "ma": dh.so, "_cn": c.id})
        hd_po = {c.hoa_don_id for c in (db.query(CongNo).filter(CongNo.don_mua_id.in_(list(po_ids))).all() if po_ids else [])
                 if c.hoa_don_id}
        for h in db.query(HoaDon).filter(HoaDon.loai == "MUA", HoaDon.don_hang_id == dh.id).all():
            if h.id in hd_po or str(h.dien_giai or "").startswith("Nhận hàng PO"):
                continue
            p = po_trung_khoan(pos, h.so, h.nha_cung_cap_id, h.tong_tien, h.tien_truoc_thue, da_dung)
            ngay = str(h.ngay) if h.ngay else None
            if p is not None:
                chenh = max(float(h.tong_tien or 0) - float(p.tong_tien or 0), 0.0)
                if chenh > LECH_TRUNG:
                    items.append({"loai": "HD", "so": f"{h.so} (chênh VAT)", "ngay": ngay, "tong": chenh, "ma": dh.so})
                continue
            items.append({"loai": "HD", "so": h.so or f"HD-{h.id}", "ngay": ngay, "tong": float(h.tong_tien or 0), "ma": dh.so, "_hd": h.id})
        qv = db.query(ChiPhiVanHanh).filter(ChiPhiVanHanh.nguon.in_(VH_TINH_CHI_PHI))
        if so:
            qv = qv.filter((ChiPhiVanHanh.don_hang_id == dh.id) | (ChiPhiVanHanh.don_hang_id.is_(None) & (func.lower(func.trim(ChiPhiVanHanh.ma_ban_hang)) == so)))
        else:
            qv = qv.filter(ChiPhiVanHanh.don_hang_id == dh.id)
        for v in qv.all():
            if v.don_mua_id or v.hoa_don_id:
                continue
            if po_trung_khoan(pos, v.so_hoa_don, None, float(v.so_tien or 0), da_dung=da_dung) is not None:
                continue
            items.append({"loai": "VH", "so": v.so_hoa_don or (v.mo_ta or "Chi phí vận hành")[:40], "ngay": str(v.ngay) if v.ngay else None,
                          "tong": float(v.so_tien or 0), "ma": dh.so})
    for p in po_mm_items or []:
        it = {"loai": p["loai"], "so": p["so"], "ngay": p.get("ngay"), "tong": float(p["tong"] or 0), "ma": p.get("ma")}
        if p["loai"] == "PO":
            it["_dm"] = p["id"]
        elif p["loai"] == "CN":
            it["_cn"] = p["id"]
        items.append(it)
    return _gan_thuc_chi(db, items)


@router.get("/dau-tu-khau-hao")
def dau_tu_khau_hao(tu_thang: str = "2026-07", db: Session = Depends(get_db), _=Depends(chi_vai_tro("CEO"))):
    """🏗 Overall Financial › Đầu tư / Khấu hao: theo MÃ dự án cho thuê, tính từ `tu_thang` (mặc định 07/2026):
    vốn đầu tư thực tế phát sinh trong kỳ (theo chứng từ) · THỰC CHI (tiền thật đã trả NCC, theo ngày trả — sổ thanh toán, thiếu
    thì ngày ghi trên PO, đánh dấu thuc_chi_po) · khấu hao trong kỳ
    (vốn ÷ số tháng hợp đồng, từng tháng từ tháng bắt đầu HĐ) · doanh thu thực tế các đơn tháng (gồm VAT, cùng Lãi/Lỗ Record) ·
    chi phí vận hành · lãi sau khấu hao; kèm bảng theo tháng. Chỉ CEO — số vốn đầu tư."""
    import re as _re
    from ..dau_tu_cho_thue import tong_hop as _th, don_thang_cua_du_an, chi_phi_du_an_theo_thang, la_don_dau_tu, po_ma_me_cua_du_an
    from ..lai_lo_ma import chi_phi_ma
    from ..models import TaiSanChoThue, KhachHang
    from ..nhac_viec_service import gio_hien_tai
    hom_nay = gio_hien_tai().date()
    nay = str(hom_nay)[:7]
    if not _re.fullmatch(r"\d{4}-\d{2}", tu_thang or "") or not (1 <= int(tu_thang[5:7]) <= 12):
        tu_thang = "2026-07"
    if tu_thang > nay:
        tu_thang = nay
    months = _thang_tu_den(tu_thang, hom_nay)
    th = _th(db, hom_nay)
    ds_ts = {t.id: t for t in db.query(TaiSanChoThue).all()}
    po_mm = po_ma_me_cua_du_an(db, list(ds_ts.values()))
    kh_ten = {k.id: k.ten for k in db.query(KhachHang).all()}
    out = []
    keys = ("dau_tu_ky", "dau_tu_tong", "thuc_chi_ky", "thuc_chi_ky_po", "thuc_chi_tong", "thuc_chi_khong_ngay", "con_no", "khong_theo_doi",
            "kh_ky", "kh_luy_ke", "dt_ky", "cp_vh_ky", "lai_ky")
    tong = {k: 0.0 for k in keys}
    tt_thang = {m: {"dau_tu": 0.0, "thuc_chi": 0.0, "thuc_chi_po": 0.0, "khau_hao": 0.0, "doanh_thu": 0.0, "cp_vh": 0.0} for m in months}
    for r in th["du_an"]:
        ts = ds_ts.get(r["tai_san_id"])
        if ts is None:
            continue
        items = _dau_tu_items_du_an(db, ts, r, po_mm.get(ts.id, []))
        von = float(r["von_dau_tu"] or 0)
        kh = float(r["khau_hao_thang"] or 0)
        bat_dau = ts.ngay_bat_dau_hd or ts.ngay_mua
        n_hd = int(ts.so_thang_hd or 0)
        # lịch khấu hao: từng tháng từ tháng bắt đầu HĐ, tối đa n_hd tháng, không vượt vốn (cùng cách tính kh_luy_ke)
        kh_thang = {}
        if bat_dau and kh > 0:
            y, m, con = bat_dau.year, bat_dau.month, (von if von > 0 else float("inf"))
            for _i in range(n_hd if n_hd > 0 else 600):
                k = f"{y}-{m:02d}"
                if k > nay or con <= 0:
                    break
                v = min(kh, con)
                kh_thang[k] = v
                con -= v
                m += 1
                if m > 12:
                    y, m = y + 1, 1
        cp_thang = chi_phi_du_an_theo_thang(db, ts, months)
        theo, dau_tu_ky, tc_ky, kh_ky, dt_ky, cp_ky, tc_ky_po = [], 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        for mk in months:
            y, mm = int(mk[:4]), int(mk[5:7])
            dt = 0.0
            for dh in don_thang_cua_du_an(db, ts, date(y, mm, 1)):
                if la_don_dau_tu(dh):
                    continue
                dt += float(chi_phi_ma(db, dh)["doanh_thu"] or 0)
            dtu = sum(float(x["tong"]) for x in items if (x.get("ngay") or "")[:7] == mk)
            tcm = sum(float((x.get("tra_thang") or {}).get(mk, 0.0)) for x in items)
            tcm_po = sum(float((x.get("tra_thang_po") or {}).get(mk, 0.0)) for x in items)   # trong đó: ngày theo PO
            khm = float(kh_thang.get(mk, 0.0))
            cpm = float((cp_thang.get(mk) or {}).get("tong", 0.0))
            theo.append({"thang": mk, "dau_tu": dtu, "thuc_chi": tcm, "thuc_chi_po": tcm_po, "khau_hao": khm, "doanh_thu": dt,
                         "cp_vh": cpm, "lai": dt - cpm - khm})
            dau_tu_ky += dtu; tc_ky += tcm; tc_ky_po += tcm_po; kh_ky += khm; dt_ky += dt; cp_ky += cpm
            t0 = tt_thang[mk]
            t0["dau_tu"] += dtu; t0["thuc_chi"] += tcm; t0["thuc_chi_po"] += tcm_po; t0["khau_hao"] += khm; t0["doanh_thu"] += dt; t0["cp_vh"] += cpm
        theo_doi = [x for x in items if x.get("theo_doi")]
        tc_tong = sum(float(x["da_tra"] or 0) for x in theo_doi)
        tc_co_ngay = sum(sum(float(v) for v in (x.get("tra_thang") or {}).values()) for x in theo_doi)
        row = {"tai_san_id": ts.id, "ma": ts.ma, "ten": ts.ten, "khach": kh_ten.get(ts.khach_hang_id),
               "so_hop_dong": r.get("so_hop_dong"), "so_thang_hd": n_hd, "ngay_bat_dau_hd": str(bat_dau) if bat_dau else None,
               "ngay_ket_thuc_hd": r.get("ngay_ket_thuc_hd"), "khau_hao_thang": kh, "khau_hao_nhap_tay": bool(r.get("khau_hao_nhap_tay")),
               "dau_tu_ky": dau_tu_ky, "dau_tu_tong": von, "dau_tu_truoc_ky": max(von - dau_tu_ky, 0.0),
               "dau_tu_khong_ngay": sum(float(x["tong"]) for x in items if not x.get("ngay")),
               "thuc_chi_ky": tc_ky, "thuc_chi_ky_po": tc_ky_po, "thuc_chi_tong": tc_tong,
               "thuc_chi_khong_ngay": max(tc_tong - tc_co_ngay, 0.0),
               "con_no": sum(max(float(x["tong"]) - float(x["da_tra"] or 0), 0.0) for x in theo_doi),
               "khong_theo_doi": sum(float(x["tong"]) for x in items if not x.get("theo_doi")),
               "kh_ky": kh_ky, "kh_luy_ke": float(r.get("khau_hao_luy_ke") or 0), "gia_tri_con_lai": float(r.get("gia_tri_con_lai") or 0),
               "dt_ky": dt_ky, "cp_vh_ky": cp_ky, "lai_ky": dt_ky - cp_ky - kh_ky,
               "dt_luy_ke": float(r.get("dt_luy_ke") or 0), "hoan_von_pct": r.get("hoan_von_pct"),
               "von_chua_thu_hoi": float(r.get("von_chua_thu_hoi") or 0),
               "thieu_thong_so": r.get("thieu_thong_so") or [], "theo_thang": theo,
               "dau_tu_items": sorted(items, key=lambda x: (x.get("ngay") or "", str(x["so"])))[:80]}
        out.append(row)
        for k in keys:
            tong[k] += float(row[k] or 0)
    out.sort(key=lambda x: (-x["dau_tu_tong"], x["ma"] or ""))
    theo_thang = [dict(thang=k, **v, lai=v["doanh_thu"] - v["cp_vh"] - v["khau_hao"]) for k, v in tt_thang.items()]
    return {"tu_thang": tu_thang, "den_thang": nay, "ngay": str(hom_nay), "months": months, "du_an": out, "tong": tong,
            "theo_thang": theo_thang, "don_dau_tu_chua_noi": th.get("don_dau_tu_chua_noi") or [],
            "nghi_dau_tu": th.get("nghi_dau_tu") or []}


# ============ 📊 PHÂN TÍCH DỮ LIỆU — Overall Financial (chỉ CEO: có lương, vốn đầu tư) ============
def _pt_ai_moi_nhat(db):
    from ..models import PhanTichAi
    r = db.query(PhanTichAi).order_by(PhanTichAi.id.desc()).first()
    if r is None:
        return None
    return {"id": r.id, "tao_luc": r.tao_luc.strftime("%d/%m/%Y %H:%M") if r.tao_luc else None,
            "mo_hinh": r.mo_hinh, "ket_qua": r.ket_qua}


@router.get("/phan-tich")
def phan_tich_du_lieu(db: Session = Depends(get_db), _=Depends(chi_vai_tro("CEO"))):
    """📊 Overall Financial › Phân tích dữ liệu: 6 đề mục (bán hàng · nhân sự · chi phí · dòng tiền · công nợ · quản trị),
    mỗi đề mục có biểu đồ + nhận xét + đề xuất tính từ số liệu thật; kèm bản nhận định AI gần nhất (nếu đã tạo). Chỉ đọc."""
    from ..phan_tich_du_lieu import phan_tich
    from ..nhac_viec_service import gio_hien_tai
    from ..config import settings
    out = phan_tich(db, gio_hien_tai().date())
    try:
        out["ai"] = _pt_ai_moi_nhat(db)
    except Exception:                      # bảng mig 144 chưa có → tab vẫn chạy, chỉ thiếu phần AI
        db.rollback()
        out["ai"] = None
    out["ai_bat"] = bool(settings.ai_provider.upper() == "ANTHROPIC" and settings.anthropic_api_key)
    return out


@router.post("/phan-tich/ai")
def phan_tich_du_lieu_ai(db: Session = Depends(get_db), nd: NguoiDung = Depends(chi_vai_tro("CEO"))):
    """🤖 Gọi AI nhận định 4 chuyên gia trên gói số liệu tổng hợp hiện tại, lưu lại bản mới nhất."""
    from ..phan_tich_du_lieu import phan_tich, goi_ai
    from ..ai_gateway import phan_tich_chuyen_gia
    from ..models import PhanTichAi
    from ..nhac_viec_service import gio_hien_tai
    from ..config import settings
    pt = phan_tich(db, gio_hien_tai().date())
    try:
        kq = phan_tich_chuyen_gia(goi_ai(pt))
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    r = PhanTichAi(tao_luc=gio_hien_tai(), nguoi_dung_id=nd.id, mo_hinh=str(settings.anthropic_model)[:60], ket_qua=kq)
    db.add(r)
    db.flush()
    ghi_audit(db, nd.id, "TAO", "phan_tich_ai", r.id, moi={"mo_hinh": r.mo_hinh})
    db.commit()
    return _pt_ai_moi_nhat(db)
