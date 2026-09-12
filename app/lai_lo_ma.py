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
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session

from .models import DonHang, DonMua, DonMuaCt, CongNo, HoaDon, PhieuThuChi


def _f(v) -> float:
    return float(v or 0)


def chi_phi_ma(db: Session, dh: DonHang) -> dict:
    doanh_thu = _f(dh.tong_tien) + _f(dh.tien_thue)
    # PO gắn đơn + PO chỉ mang MÃ CHUỖI trùng số đơn (sinh từ Dự toán / Dự án trước khi có
    # đơn bán) — đơn bán cùng số tạo sau vẫn gom đủ giá vốn.
    _dk_pos = DonMua.don_hang_id == dh.id
    if (dh.so or "").strip():
        _dk_pos = or_(_dk_pos, and_(DonMua.don_hang_id.is_(None),
                                    func.lower(func.trim(DonMua.ma_ban)) == dh.so.strip().lower()))
    pos = (db.query(DonMua).filter(_dk_pos,
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
        # chỉ khoản NHẬP NGOÀI thật (không sinh từ hóa đơn trong hệ thống, không phải hóa đơn
        # nhận hàng PO) — khoản có hóa đơn đã được tính ở nhánh hóa đơn, tính nữa là 2 lần
        cn_ngoai = [c for c in (db.query(CongNo)
                    .filter(CongNo.loai == "PHAI_TRA", CongNo.don_mua_id.is_(None),
                            CongNo.hoa_don_id.is_(None),
                            func.lower(CongNo.ma_ban_ngoai) == dh.so.lower()).all())
                    if not str(c.so_ct or "").upper().startswith("HDM-")]
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


# ================= NHÓM MÃ GỐC + THÁNG · CHI PHÍ NGOÀI MÃ (dùng chung Overall Financial · Kiểm soát) =================
import re as _re_nm


def nhom_ma(ma):
    """'DV-COA-NT-0826-02 (1)' → 'DV-COA-NT-0826' — dùng BỘ ĐỌC CHUNG app/ma_code.py."""
    from .ma_code import nhom
    return nhom(ma)


def chi_phi_ngoai_ma(db: Session) -> dict:
    """Khoản chi ĐÃ DUYỆT không gắn đơn bán nào (PO không don_hang_id · công nợ nhập ngoài
    thật — không sinh từ hóa đơn, không phải HĐ nhận hàng PO), chia theo mã:
      ma_le      {mã thường: {ma, chi}}  mã có nhưng chưa có đơn bán → hiện thành dòng riêng
      chi_op     mã OP-… (vận hành doanh nghiệp)
      chi_chua_ma không có mã
      chi_kho    mã KHO (mua dự trữ — tồn kho)"""
    so_dh = {str(x).strip().lower() for (x,) in db.query(DonHang.so).filter(DonHang.so.isnot(None)).all()}
    r = {"ma_le": {}, "chi_op": 0.0, "chi_chua_ma": 0.0, "chi_kho": 0.0}

    def cong(mb, v):
        k = str(mb or "").strip().lower()
        if not k:
            r["chi_chua_ma"] += v
        elif k == "kho":
            r["chi_kho"] += v
        elif k.startswith("op"):
            if k not in so_dh:
                r["chi_op"] += v
        elif k not in so_dh:
            o = r["ma_le"].setdefault(k, {"ma": str(mb).strip(), "chi": 0.0})
            o["chi"] += v

    for (dhid, mb, tt) in db.query(DonMua.don_hang_id, DonMua.ma_ban, DonMua.tong_tien).filter(
            DonMua.trang_thai == "DA_DUYET").all():
        if not dhid:
            cong(mb, _f(tt))
    for (mbn, st, sct, hdid, dmid) in db.query(
            CongNo.ma_ban_ngoai, CongNo.so_tien, CongNo.so_ct,
            CongNo.hoa_don_id, CongNo.don_mua_id).filter(CongNo.loai == "PHAI_TRA").all():
        if dmid or hdid or str(sct or "").upper().startswith("HDM-"):
            continue
        cong(mbn, _f(st))
    return r


def gom_theo_nhom(rows):
    """rows có 'nhom' → [{nhom, so_ma, doanh_thu, tong_chi_phi, loi_nhuan, ty_suat, ma}] cho nhóm ≥ 2 mã."""
    nh = {}
    for x in rows:
        k = x.get("nhom")
        if k:
            nh.setdefault(k, []).append(x)
    out = []
    for k, rs in nh.items():
        if len(rs) < 2:
            continue
        dt = sum(_f(x.get("doanh_thu")) for x in rs)
        cp = sum(_f(x.get("tong_chi_phi")) for x in rs)
        out.append({"nhom": k, "so_ma": len(rs), "doanh_thu": dt, "tong_chi_phi": cp,
                    "loi_nhuan": dt - cp, "ty_suat": round((dt - cp) / dt * 100, 1) if dt else None,
                    "ma": [x.get("ma_ban") for x in rs]})
    out.sort(key=lambda o: -o["doanh_thu"])
    return out
