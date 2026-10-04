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
    """So khớp từng dòng sao kê với ứng viên 4 nguồn: cùng chiều + đúng số tiền
    + lệch ngày ≤3; mỗi bản ghi app chỉ khớp 1 dòng; ưu tiên phiếu/lệnh chi."""
    from ..models import SaoKeBank, SaoKeDong
    sk = db.get(SaoKeBank, sk_id)
    dongs = (db.query(SaoKeDong).filter_by(sao_ke_id=sk_id)
             .order_by(SaoKeDong.ngay, SaoKeDong.id).all())
    if sk is None or not dongs:
        return {"tong_dong": 0, "khop": 0, "chua_khop": 0, "app_thieu": []}
    tu = (sk.tu_ngay or date.today()) - timedelta(days=5)
    den = (sk.den_ngay or date.today()) + timedelta(days=5)
    ung = _ung_vien_sao_ke(db, tu, den)
    UU_TIEN = {"PHIEU": 0, "LENH_CHI": 0, "THU_CN_BAN": 1, "BANK_REC": 2}
    da_dung, khop = set(), 0
    for d in dongs:
        d.khop_loai = None; d.khop_id = None; d.khop_mo_ta = None
        so = float(d.tien_vao or 0) or float(d.tien_ra or 0)
        if so <= 0:
            continue
        chieu = "VAO" if float(d.tien_vao or 0) > 0 else "RA"
        tot, tot_key = None, None
        for u in ung:
            if (u["loai"], u["id"]) in da_dung or u["chieu"] != chieu:
                continue
            if abs(u["so_tien"] - so) > 0.5:
                continue
            lech = abs((u["ngay"] - d.ngay).days) if (d.ngay and u["ngay"]) else 99
            if lech > 3:
                continue
            key = (lech, UU_TIEN.get(u["loai"], 9))
            if tot is None or key < tot_key:
                tot, tot_key = u, key
        if tot is not None:
            da_dung.add((tot["loai"], tot["id"]))
            d.khop_loai = tot["loai"]; d.khop_id = tot["id"]
            d.khop_mo_ta = tot["mo_ta"][:300]
            khop += 1
    return {"tong_dong": len(dongs), "khop": khop, "chua_khop": len(dongs) - khop,
            "app_thieu": _thieu_tren_sao_ke(sk, ung, da_dung)}


@router.post("/sao-ke", status_code=201)
def tai_sao_ke(ngan_hang: str = "", bo_qua_trung: bool = False, file: UploadFile = File(...),
               db: Session = Depends(get_db),
               nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT"))):
    """📥 Tải file sao kê (PDF/ảnh/Excel/CSV) — AI đọc từng dòng, lưu lại, đối soát ngay.
    File CÙNG TÊN đã tải trước đó → hỏi xác nhận (tránh chồng nhiều bản trùng)."""
    from ..models import SaoKeBank, SaoKeDong
    from ..ai_gateway import doc_sao_ke_tep
    from ..nhac_viec_service import gio_hien_tai
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
    dong = doc_sao_ke_tep(data, file.content_type or "", file.filename or "")
    if not dong:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "AI không đọc được sao kê từ file này — kiểm tra file / cấu hình AI")
    sk = SaoKeBank(ten_file=(file.filename or "sao_ke")[:200],
                   ngan_hang=(ngan_hang or "").strip()[:60] or None,
                   nguoi_tao=nd.id, tao_luc=gio_hien_tai())
    db.add(sk); db.flush()
    n, ngays = 0, []
    for d in dong[:500]:
        vao, ra = _ske_so(d.get("tien_vao")), _ske_so(d.get("tien_ra"))
        if not vao and not ra:
            continue
        ng = None
        try:
            if d.get("ngay"):
                ng = date.fromisoformat(str(d["ngay"])[:10])
        except Exception:
            pass
        sd = _ske_so(d.get("so_du")) if d.get("so_du") is not None else None
        db.add(SaoKeDong(sao_ke_id=sk.id, ngay=ng,
                         dien_giai=(str(d.get("dien_giai") or "")[:400]) or None,
                         tien_vao=vao, tien_ra=ra, so_du=sd))
        if ng:
            ngays.append(ng)
        n += 1
    if not n:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không thấy dòng giao dịch hợp lệ nào trong file")
    sk.so_dong = n
    sk.tu_ngay = min(ngays) if ngays else None
    sk.den_ngay = max(ngays) if ngays else None
    ghi_audit(db, nd.id, "TAI_SAO_KE", "sao_ke_bank", sk.id,
              moi={"file": sk.ten_file, "ngan_hang": sk.ngan_hang, "so_dong": n})
    db.flush()
    kq = _doi_soat_sao_ke(db, sk.id)
    db.commit()
    return {"ok": True, "id": sk.id, "so_dong": n, "doi_soat": kq}


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
