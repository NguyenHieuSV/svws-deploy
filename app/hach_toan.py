"""
HẠCH TOÁN KÉP theo hệ thống tài khoản VAS (TT 200/133).
Sinh bút toán tự động cho hóa đơn bán & thu tiền. Tách riêng để tái dùng/kiểm thử.
"""
from decimal import Decimal
from sqlalchemy.orm import Session
from .models import ButToan

# Tài khoản dùng trong lát cắt này
TK = {
    "PHAI_THU": "131", "PHAI_TRA": "331",
    "DOANH_THU": "511", "THUE_GTGT_RA": "3331",
    "TIEN_MAT": "111", "TIEN_NH": "112",
    "CP_LUONG": "642", "PHAI_TRA_NLD": "334", "THUE_GTGT_VAO": "1331",
    "GIA_VON": "632", "CP_QLDN": "642",
    "BHXH": "3383", "BHYT": "3384", "BHTN": "3389", "THUE_TNCN": "3335",
    "VAY": "341", "CP_LAI_VAY": "635",
}


def hach_toan_hoa_don_ban(db: Session, hoa_don) -> list[ButToan]:
    """Nợ 131 / Có 511 (trước thuế) và Nợ 131 / Có 3331 (thuế)."""
    bts = []
    if hoa_don.tien_truoc_thue:
        bts.append(ButToan(tk_no=TK["PHAI_THU"], tk_co=TK["DOANH_THU"],
                           so_tien=hoa_don.tien_truoc_thue, hoa_don_id=hoa_don.id,
                           don_hang_id=hoa_don.don_hang_id,
                           dien_giai=f"Doanh thu HĐ {hoa_don.so or hoa_don.id}"))
    if hoa_don.tien_thue:
        bts.append(ButToan(tk_no=TK["PHAI_THU"], tk_co=TK["THUE_GTGT_RA"],
                           so_tien=hoa_don.tien_thue, hoa_don_id=hoa_don.id,
                           don_hang_id=hoa_don.don_hang_id,
                           dien_giai=f"Thuế GTGT đầu ra HĐ {hoa_don.so or hoa_don.id}"))
    for bt in bts:
        db.add(bt)
    return bts


def hach_toan_hoa_don_mua(db: Session, hoa_don) -> list[ButToan]:
    """Hóa đơn MUA/chi phí đầu vào: Nợ <chi phí/giá vốn> + Nợ 1331 (thuế GTGT vào) / Có 331."""
    tkcp = hoa_don.tk_chi_phi or TK["CP_QLDN"]
    bts = []
    if hoa_don.tien_truoc_thue:
        bts.append(ButToan(tk_no=tkcp, tk_co=TK["PHAI_TRA"],
                           so_tien=hoa_don.tien_truoc_thue, hoa_don_id=hoa_don.id,
                           don_hang_id=hoa_don.don_hang_id,
                           dien_giai=f"Chi phí/giá vốn HĐ mua {hoa_don.so or hoa_don.id}"))
    if hoa_don.tien_thue:
        bts.append(ButToan(tk_no=TK["THUE_GTGT_VAO"], tk_co=TK["PHAI_TRA"],
                           so_tien=hoa_don.tien_thue, hoa_don_id=hoa_don.id,
                           don_hang_id=hoa_don.don_hang_id,
                           dien_giai=f"Thuế GTGT đầu vào HĐ {hoa_don.so or hoa_don.id}"))
    for bt in bts:
        db.add(bt)
    return bts


def hach_toan_thu_tien(db: Session, cong_no, so_tien: Decimal, tien_mat=False) -> ButToan:
    """Nợ 111/112 / Có 131 (thu nợ phải thu)."""
    tk_thu = TK["TIEN_MAT"] if tien_mat else TK["TIEN_NH"]
    bt = ButToan(tk_no=tk_thu, tk_co=TK["PHAI_THU"], so_tien=so_tien,
                 hoa_don_id=cong_no.hoa_don_id, dien_giai=f"Thu nợ công nợ {cong_no.id}")
    db.add(bt)
    return bt


def hach_toan_luong(db: Session, bl) -> list:
    """Lương đầy đủ:
    - Nợ CP(642/622/627) / Có 334  = tổng thu nhập (lương thực tế + phụ cấp + OT)
    - Nợ CP / Có 3383/3384/3389    = BHXH/BHYT/BHTN phần DN (chi phí DN)
    - Nợ 334 / Có 3383/3384/3389/3335 = khấu trừ NLĐ (BH + thuế TNCN)
    """
    from datetime import date as _date
    from .models import NhanVien
    nv = db.get(NhanVien, bl.nhan_vien_id)
    tkcp = (nv.tk_chi_phi if nv and nv.tk_chi_phi else TK["CP_LUONG"])
    gross = (bl.luong_thuc_te or bl.luong_co_ban or 0) + (bl.phu_cap or 0) + (bl.ot or 0)
    dg = f"Lương {bl.thang} NV {bl.nhan_vien_id}"
    bts = [ButToan(tk_no=tkcp, tk_co=TK["PHAI_TRA_NLD"], so_tien=gross, ngay=_date.today(),
                   nguon="LUONG", nguon_id=bl.id, dien_giai=dg)]
    # BH phần DN -> chi phí DN
    for tien, tk in [(bl.bhxh_dn, TK["BHXH"]), (bl.bhyt_dn, TK["BHYT"]), (bl.bhtn_dn, TK["BHTN"])]:
        if tien:
            bts.append(ButToan(tk_no=tkcp, tk_co=tk, so_tien=tien, ngay=_date.today(),
                               nguon="LUONG", nguon_id=bl.id, dien_giai=f"BH phần DN {bl.thang} NV {bl.nhan_vien_id}"))
    # Khấu trừ NLĐ
    for tien, tk in [(bl.bhxh, TK["BHXH"]), (bl.bhyt, TK["BHYT"]),
                     (bl.bhtn, TK["BHTN"]), (bl.thue_tncn, TK["THUE_TNCN"])]:
        if tien:
            bts.append(ButToan(tk_no=TK["PHAI_TRA_NLD"], tk_co=tk, so_tien=tien, ngay=_date.today(),
                               nguon="LUONG", nguon_id=bl.id, dien_giai=f"Khấu trừ {bl.thang} NV {bl.nhan_vien_id}"))
    for bt in bts:
        db.add(bt)
    return bts
