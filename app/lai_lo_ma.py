"""
Công thức CHUNG chi phí / lãi-lỗ theo MÃ ĐƠN HÀNG BÁN — dùng ở 4 nơi để ra CÙNG MỘT con số:
  Kế toán → Lãi/Lỗ mã bán · NCC → Kiểm soát (Chi phí theo Mã) · Overall Financial (theo mã)
  · Bán hàng → lãi/lỗ từng đơn.

Nguyên tắc (chốt 2026-08-19 — "chi phí theo NGHĨA VỤ, không theo tiến độ trả tiền"):
  • GIÁ VỐN PO      = Σ tổng giá trị PO ĐÃ DUYỆT gắn mã (cam kết; không đổi khi trả từng đợt).
  • CHI PHÍ KHÁC    = công nợ phải trả NHẬP NGOÀI khớp mã (tổng khoản)
                      + hóa đơn MUA gắn mã KHÔNG qua PO (ghi từ email / tay; bỏ hóa đơn tự sinh khi nhận hàng).
  • LỢI NHUẬN       = Doanh thu (GỒM VAT) − Giá vốn PO − Chi phí khác   (hai vế cùng gồm VAT).
  • DÒNG TIỀN (tách riêng, không ảnh hưởng lãi/lỗ): Đã trả NCC / Còn phải trả (từ công nợ của mã).
  • ĐÃ THU          = đã thanh toán trên công nợ PHẢI THU của mã (gồm cọc đã cấn)
                      + trả trước khách chưa cấn + cọc ghi trên đơn khi chưa có công nợ.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import DonHang, DonMua, DonMuaCt, CongNo, HoaDon, PhieuThuChi


def _f(v) -> float:
    return float(v or 0)


def chi_phi_ma(db: Session, dh: DonHang) -> dict:
    doanh_thu = _f(dh.tong_tien) + _f(dh.tien_thue)
    pos = (db.query(DonMua).filter(DonMua.don_hang_id == dh.id,
                                   DonMua.trang_thai != "TU_CHOI").all())
    po_ids = [p.id for p in pos]
    gia_von_po = sum(_f(p.tong_tien) for p in pos if p.trang_thai == "DA_DUYET")
    po_cho_duyet = sum(_f(p.tong_tien) for p in pos if p.trang_thai == "CHO_DUYET")
    # giá vốn THỰC NHẬN (theo số lượng đã nhận) — thông tin phụ, không dùng tính lãi/lỗ
    gia_von_thuc = 0.0
    if po_ids:
        for ct in db.query(DonMuaCt).filter(DonMuaCt.don_mua_id.in_(po_ids)).all():
            gia_von_thuc += _f(ct.so_luong_nhan) * _f(ct.don_gia)
    # công nợ phải trả gắn mã: theo PO + nhập ngoài (khớp mã)
    cn_po = (db.query(CongNo).filter(CongNo.loai == "PHAI_TRA",
                                     CongNo.don_mua_id.in_(po_ids)).all()) if po_ids else []
    cn_ngoai = []
    if dh.so:
        cn_ngoai = (db.query(CongNo)
                    .filter(CongNo.loai == "PHAI_TRA", CongNo.don_mua_id.is_(None),
                            func.lower(CongNo.ma_ban_ngoai) == dh.so.lower()).all())
    chi_ngoai_cn = sum(_f(c.so_tien) for c in cn_ngoai)
    # hóa đơn MUA gắn mã KHÔNG qua PO (email / nhập tay) — bỏ hóa đơn tự sinh khi nhận hàng PO
    hd_po = {c.hoa_don_id for c in cn_po if c.hoa_don_id}
    hd_ngoai_po = []
    for hd in db.query(HoaDon).filter(HoaDon.loai == "MUA", HoaDon.don_hang_id == dh.id).all():
        if hd.id in hd_po or str(hd.dien_giai or "").startswith("Nhận hàng PO"):
            continue
        hd_ngoai_po.append(hd)
    chi_hd_ngoai_po = sum(_f(h.tong_tien) for h in hd_ngoai_po)
    # công nợ sinh từ các hóa đơn ngoài PO (luồng cũ) — chỉ dùng cho DÒNG TIỀN, không cộng chi phí
    cn_hd = []
    if hd_ngoai_po:
        cn_hd = (db.query(CongNo).filter(CongNo.loai == "PHAI_TRA",
                                         CongNo.hoa_don_id.in_([h.id for h in hd_ngoai_po])).all())
    tat_ca_cn = cn_po + cn_ngoai + cn_hd
    da_tra_ncc = sum(_f(c.da_thanh_toan) for c in tat_ca_cn)
    con_phai_tra = sum(max(_f(c.so_tien) - _f(c.da_thanh_toan), 0.0) for c in tat_ca_cn)

    chi_phi_khac = chi_ngoai_cn + chi_hd_ngoai_po
    tong_chi_phi = gia_von_po + chi_phi_khac
    loi_nhuan = doanh_thu - tong_chi_phi

    # ĐÃ THU của mã
    cn_thu = db.query(CongNo).filter(CongNo.loai == "PHAI_THU", CongNo.don_hang_id == dh.id).all()
    da_thu_cn = sum(_f(c.da_thanh_toan) for c in cn_thu)
    tu_thu_clt = _f(db.query(func.coalesce(func.sum(PhieuThuChi.so_tien - PhieuThuChi.da_can_tru), 0))
                    .filter(PhieuThuChi.don_hang_id == dh.id, PhieuThuChi.loai == "THU",
                            PhieuThuChi.la_tam_ung.is_(True),
                            PhieuThuChi.trang_thai == "DA_DUYET").scalar())
    coc_don = _f(dh.thanh_toan_coc) if not cn_thu else 0.0
    da_thu = da_thu_cn + max(tu_thu_clt, 0.0) + coc_don

    return {
        "doanh_thu": doanh_thu,
        "gia_von_po": gia_von_po, "po_cho_duyet": po_cho_duyet, "gia_von_thuc": gia_von_thuc,
        "chi_ngoai_cn": chi_ngoai_cn, "chi_hd_ngoai_po": chi_hd_ngoai_po,
        "chi_phi_khac": chi_phi_khac, "tong_chi_phi": tong_chi_phi,
        "loi_nhuan": loi_nhuan,
        "ty_suat": round(loi_nhuan / doanh_thu * 100, 1) if doanh_thu else None,
        "da_tra_ncc": da_tra_ncc, "con_phai_tra": con_phai_tra,
        "da_thu": da_thu, "con_phai_thu": max(doanh_thu - da_thu, 0.0),
        "so_po": len(pos),
        "danh_sach_po": [{"id": p.id, "so": p.so, "nha_cung_cap_id": p.nha_cung_cap_id,
                          "tong_tien": _f(p.tong_tien), "trang_thai": p.trang_thai,
                          "trang_thai_nhan": p.trang_thai_nhan} for p in pos],
    }
