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

from .models import DonHang, DonMua, DonMuaCt, CongNo, HoaDon, PhieuThuChi, ChiPhiVanHanh

# Chi phí vận hành cho thuê ĐƯỢC TÍNH vào lãi/lỗ theo mã: hóa đơn email · ghi tay · bảo trì.
# KHÔNG tính: DE_XUAT_MUA (sinh từ đề xuất → PO đã là giá vốn) · TIEU_HAO (ước tính theo định mức, hóa chất đã mua qua PO).
VH_TINH_CHI_PHI = ("HD_EMAIL", "THU_CONG", "BAO_TRI")


def _f(v) -> float:
    return float(v or 0)


def tra_truoc_theo_don(db: Session, dh_ids=None) -> dict:
    """TIỀN KHÁCH TRẢ TRƯỚC của từng đơn — QUY TẮC CHUNG (chốt 13/09/2026):
         trả trước = max(cọc ghi trên đơn, tạm ứng phiếu thu ĐÃ DUYỆT chưa cấn trừ)
    Hai đường ghi cùng một khoản tiền (cọc gõ tay trên đơn · phiếu thu tạm ứng có tiền vào quỹ)
    → lấy số lớn hơn, không cộng dồn (tránh trừ 2 lần). Trả {id: {coc, tam_ung, tra_truoc, nguon}}."""
    q = db.query(DonHang.id, DonHang.thanh_toan_coc)
    if dh_ids is not None:
        q = q.filter(DonHang.id.in_(list(dh_ids)))
    out = {i: {"coc": _f(c), "tam_ung": 0.0} for (i, c) in q.all()}
    qt = (db.query(PhieuThuChi.don_hang_id, func.coalesce(func.sum(PhieuThuChi.so_tien - PhieuThuChi.da_can_tru), 0))
          .filter(PhieuThuChi.loai == "THU", PhieuThuChi.la_tam_ung.is_(True),
                  PhieuThuChi.trang_thai == "DA_DUYET", PhieuThuChi.don_hang_id.isnot(None))
          .group_by(PhieuThuChi.don_hang_id))
    if dh_ids is not None:
        qt = qt.filter(PhieuThuChi.don_hang_id.in_(list(dh_ids)))
    for (i, t) in qt.all():
        if i in out:
            out[i]["tam_ung"] = max(_f(t), 0.0)
    for o in out.values():
        o["tra_truoc"] = max(o["coc"], o["tam_ung"])
        o["nguon"] = (("cả hai" if (o["coc"] and o["tam_ung"]) else ("phiếu thu" if o["tam_ung"] else "cọc trên đơn"))
                      if o["tra_truoc"] else None)
    return out


# ================= NHẬN DIỆN KHOẢN NHẬP TRỰC TIẾP TRÙNG VỚI PO (một khoản mua đi 2 cửa) =================
import re as _re_tr

LECH_TRUNG = 1000.0          # đ — lệch làm tròn cho phép


def so_hd_chuan(s) -> str:
    """'00004731' = '4731' = ' 4731 ' ; 'C26TAP-00004260' = 'c26tap4260'."""
    t = _re_tr.sub(r"[^0-9a-z]", "", str(s or "").lower())
    return _re_tr.sub(r"^0+", "", t)


def po_trung_khoan(pos, so_ct, ncc_id, tong, truoc_thue=None, da_dung=None):
    """PO (cùng mã) chính là khoản mua của hóa đơn / công nợ nhập trực tiếp này?
    Trùng khi: (cùng SỐ HÓA ĐƠN và [cùng tiền hoặc cùng NCC]) hoặc (cùng NCC và cùng tiền).
    «Cùng tiền» = bằng tổng PO, hoặc PO ghi THIẾU VAT nên bằng tiền trước thuế của hóa đơn."""
    so = so_hd_chuan(so_ct)
    tong, truoc = _f(tong), _f(truoc_thue)
    for p in pos:
        if p.trang_thai == "TU_CHOI" or (da_dung is not None and p.id in da_dung):
            continue
        pt = _f(p.tong_tien)
        if pt <= 0:
            continue
        cung_so = bool(so) and so_hd_chuan(p.so_hoa_don) == so
        cung_ncc = bool(ncc_id) and p.nha_cung_cap_id == ncc_id
        cung_tien = abs(pt - tong) <= LECH_TRUNG or (truoc > 0 and abs(pt - truoc) <= LECH_TRUNG)
        if (cung_so and (cung_tien or cung_ncc)) or (cung_ncc and cung_tien):
            if da_dung is not None:
                da_dung.add(p.id)
            return p
    return None


def chi_phi_ma(db: Session, dh: DonHang, tho: bool = False) -> dict:
    """tho=True → số THÔ (không áp quy tắc đơn ĐẦU TƯ) — dùng để tính vốn đầu tư của dự án cho thuê."""
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
    # 🔁 LOẠI NHÂN ĐÔI: khoản nhập TRỰC TIẾP (hóa đơn Kế toán / công nợ nhập ngoài) mà CHÍNH LÀ một PO của mã này
    # → không cộng lần 2; PO ghi thiếu VAT so với hóa đơn → chỉ cộng phần CHÊNH (chi phí thật = hóa đơn).
    _po_da_khop = set()
    trung_po, chi_chenh_trung = [], 0.0

    def _ghi_trung(loai, so_ct, tien, p):
        nonlocal chi_chenh_trung
        chenh = max(_f(tien) - _f(p.tong_tien), 0.0)
        if chenh <= LECH_TRUNG:
            chenh = 0.0
        chi_chenh_trung += chenh
        trung_po.append({"loai": loai, "so_ct": so_ct, "so_tien": _f(tien), "po": p.so, "don_mua_id": p.id,
                         "tien_po": _f(p.tong_tien), "chenh_cong_them": chenh})

    _cn_giu = []
    for c in cn_ngoai:
        p = po_trung_khoan(pos, c.so_ct, c.nha_cung_cap_id, c.so_tien,
                           _f(c.so_tien) - _f(getattr(c, "tien_thue", 0)), _po_da_khop)
        if p is not None:
            _ghi_trung("CONG_NO", c.so_ct or f"CN-{c.id}", c.so_tien, p)
        else:
            _cn_giu.append(c)
    cn_ngoai = _cn_giu
    chi_ngoai_cn = sum(_f(c.so_tien) for c in cn_ngoai)
    # hóa đơn MUA gắn mã KHÔNG qua PO (email / nhập tay) — bỏ hóa đơn tự sinh khi nhận hàng PO
    hd_po = {c.hoa_don_id for c in cn_po if c.hoa_don_id}
    hd_ngoai_po = []
    for hd in db.query(HoaDon).filter(HoaDon.loai == "MUA", HoaDon.don_hang_id == dh.id).all():
        if hd.id in hd_po or str(hd.dien_giai or "").startswith("Nhận hàng PO"):
            continue
        p = po_trung_khoan(pos, hd.so, hd.nha_cung_cap_id, hd.tong_tien, hd.tien_truoc_thue, _po_da_khop)
        if p is not None:
            _ghi_trung("HOA_DON", hd.so or f"HD-{hd.id}", hd.tong_tien, p)
            continue
        hd_ngoai_po.append(hd)
    chi_hd_ngoai_po = sum(_f(h.tong_tien) for h in hd_ngoai_po) + chi_chenh_trung
    # công nợ sinh từ các hóa đơn ngoài PO (luồng cũ) — chỉ dùng cho DÒNG TIỀN, không cộng chi phí
    cn_hd = []
    if hd_ngoai_po:
        cn_hd = (db.query(CongNo).filter(CongNo.loai == "PHAI_TRA",
                                         CongNo.hoa_don_id.in_([h.id for h in hd_ngoai_po])).all())
    tat_ca_cn = cn_po + cn_ngoai + cn_hd
    da_tra_ncc = sum(_f(c.da_thanh_toan) for c in tat_ca_cn)
    con_phai_tra = sum(max(_f(c.so_tien) - _f(c.da_thanh_toan), 0.0) for c in tat_ca_cn)

    # 🏭 CHI PHÍ VẬN HÀNH CHO THUÊ (hóa đơn đầu vào ghi ở Cho thuê / ghi tay / bảo trì) gắn mã này.
    #    Khoản đã NỐI với PO / hóa đơn MUA, hoặc trùng số HĐ + tiền với PO / hóa đơn MUA → đã tính ở nhánh đó, bỏ qua.
    chi_van_hanh, trung_vh = 0.0, []
    _dk_vh = ChiPhiVanHanh.don_hang_id == dh.id
    if (dh.so or "").strip():
        _dk_vh = or_(_dk_vh, and_(ChiPhiVanHanh.don_hang_id.is_(None),
                                  func.lower(func.trim(ChiPhiVanHanh.ma_ban_hang)) == dh.so.strip().lower()))
    vh_rows = db.query(ChiPhiVanHanh).filter(_dk_vh, ChiPhiVanHanh.nguon.in_(VH_TINH_CHI_PHI)).all()
    if vh_rows:
        hd_mua = [(so_hd_chuan(s), _f(t)) for (s, t) in db.query(HoaDon.so, HoaDon.tong_tien)
                  .filter(HoaDon.loai == "MUA").all()]
        for r in vh_rows:
            st, so = _f(r.so_tien), so_hd_chuan(r.so_hoa_don)
            ly = None
            if r.don_mua_id or r.hoa_don_id:
                ly = "đã nối PO" if r.don_mua_id else "đã nối hóa đơn MUA"
            elif po_trung_khoan(pos, r.so_hoa_don, None, st, da_dung=_po_da_khop) is not None:
                ly = "trùng PO (số HĐ + tiền)"
            elif so and any(k == so and abs(t - st) <= LECH_TRUNG for (k, t) in hd_mua):
                ly = "trùng hóa đơn MUA (số HĐ + tiền)"
            if ly:
                trung_vh.append({"id": r.id, "so_hoa_don": r.so_hoa_don, "so_tien": st, "ly_do": ly})
                continue
            chi_van_hanh += st

    chi_phi_khac = chi_ngoai_cn + chi_hd_ngoai_po + chi_van_hanh
    tong_chi_phi = gia_von_po + chi_phi_khac
    loi_nhuan = doanh_thu - tong_chi_phi

    # ĐÃ THU của mã
    cn_thu = db.query(CongNo).filter(CongNo.loai == "PHAI_THU", CongNo.don_hang_id == dh.id).all()
    da_thu_cn = sum(_f(c.da_thanh_toan) for c in cn_thu)
    tu_thu_clt = _f(db.query(func.coalesce(func.sum(PhieuThuChi.so_tien - PhieuThuChi.da_can_tru), 0))
                    .filter(PhieuThuChi.don_hang_id == dh.id, PhieuThuChi.loai == "THU",
                            PhieuThuChi.la_tam_ung.is_(True),
                            PhieuThuChi.trang_thai == "DA_DUYET").scalar())
    # QUY TẮC CHUNG (tra_truoc_theo_don): chưa có công nợ → trả trước = max(cọc, tạm ứng) — không cộng
    # dồn 2 đường ghi của cùng khoản tiền; đã có công nợ → cọc đã cấn vào da_thanh_toan, chỉ cộng tạm ứng còn dư
    coc_don = _f(dh.thanh_toan_coc) if not cn_thu else 0.0
    da_thu = da_thu_cn + (max(tu_thu_clt, coc_don) if not cn_thu else max(tu_thu_clt, 0.0))

    # 🏗 ĐƠN ĐẦU TƯ – CHO THUÊ: PO / chi phí của đơn là VỐN ĐẦU TƯ (tài sản, khấu hao dần) — KHÔNG phải giá vốn;
    #    giá trị đơn là giá trị hợp đồng ước tính — KHÔNG phải doanh thu. Xem app/dau_tu_cho_thue.py
    dau_tu = {}
    if not tho and (getattr(dh, "loai_don", None) or "").upper() == "DAU_TU":
        dau_tu = {"la_dau_tu": True, "von_dau_tu": tong_chi_phi, "von_po": gia_von_po, "von_khac": chi_phi_khac,
                  "gia_tri_hd": doanh_thu, "tai_san_cho_thue_id": getattr(dh, "tai_san_cho_thue_id", None)}
        doanh_thu = gia_von_po = chi_phi_khac = chi_ngoai_cn = chi_hd_ngoai_po = tong_chi_phi = loi_nhuan = 0.0
        da_thu = 0.0

    return {
        **dau_tu,
        "doanh_thu": doanh_thu,
        "gia_von_po": gia_von_po, "po_cho_duyet": po_cho_duyet, "gia_von_thuc": gia_von_thuc,
        "chi_ngoai_cn": chi_ngoai_cn, "chi_hd_ngoai_po": chi_hd_ngoai_po,
        "chi_van_hanh": chi_van_hanh, "trung_vh": trung_vh,
        "trung_po": trung_po, "tien_trung_po": sum(t["so_tien"] for t in trung_po),
        "chenh_trung_po": chi_chenh_trung,
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
    from .dau_tu_cho_thue import ma_me_dang_dau_tu
    ma_me = ma_me_dang_dau_tu(db)      # 🏗 PO / công nợ mang MÃ MẸ dự án cho thuê = VỐN ĐẦU TƯ (khấu hao), không phải mã lẻ
    r = {"ma_le": {}, "chi_op": 0.0, "chi_chua_ma": 0.0, "chi_kho": 0.0, "chi_dau_tu": 0.0}

    def cong(mb, v):
        k = str(mb or "").strip().lower()
        if not k:
            r["chi_chua_ma"] += v
        elif k == "kho":
            r["chi_kho"] += v
        elif k in ma_me:
            r["chi_dau_tu"] += v
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
    # 🏭 chi phí vận hành cho thuê mang mã CHƯA có đơn bán (chưa nối PO / hóa đơn MUA) → dòng mã lẻ
    for (mb, st) in (db.query(ChiPhiVanHanh.ma_ban_hang, ChiPhiVanHanh.so_tien)
                     .filter(ChiPhiVanHanh.nguon.in_(VH_TINH_CHI_PHI), ChiPhiVanHanh.don_hang_id.is_(None),
                             ChiPhiVanHanh.don_mua_id.is_(None), ChiPhiVanHanh.hoa_don_id.is_(None)).all()):
        cong(mb, _f(st))
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


# ================= DÒNG TIỀN THỰC TẾ THEO MÃ (Kế toán → Thu–chi theo mã hàng bán) =================
def dong_tien_theo_ma(db: Session) -> dict:
    """{mã (chữ thường): {"ma", "thu", "chi"}} — TIỀN THỰC đã thu của khách / đã trả NCC theo từng mã,
    lấy từ SỔ CÔNG NỢ (nơi ✔ Đã chi · 💳 · ghi thu đều trừ vào) — cùng nguyên tắc với chi_phi_ma:
      chi = Σ «đã thanh toán» của công nợ PHẢI TRẢ (theo PO của mã · nhập ngoài khớp mã · hóa đơn mua gắn mã)
            + PO cũ chưa có dòng công nợ: lũy kế đã duyệt chi (da_duyet_tt), không có thì de_nghi_tt
      thu = Σ «đã thanh toán» của công nợ PHẢI THU của đơn + trả trước chưa cấn
            (đơn chưa có công nợ: max(cọc, tạm ứng); đã có công nợ: chỉ cộng tạm ứng còn dư)."""
    so_dh = {i: (s or "").strip() for (i, s) in db.query(DonHang.id, DonHang.so).all()}
    so_key = {s.lower(): i for i, s in so_dh.items() if s}
    out = {}

    def cong(ma, thu=0.0, chi=0.0):
        ma = str(ma or "").strip()
        k = ma.lower() or "(không gắn)"
        o = out.setdefault(k, {"ma": ma or "(không gắn)", "thu": 0.0, "chi": 0.0})
        o["thu"] += thu
        o["chi"] += chi

    po = {i: (dh, mb, dd, dn) for (i, dh, mb, dd, dn) in
          db.query(DonMua.id, DonMua.don_hang_id, DonMua.ma_ban, DonMua.da_duyet_tt, DonMua.de_nghi_tt)
          .filter(DonMua.trang_thai != "TU_CHOI").all()}

    def ma_po(pid):
        p = po.get(pid)
        if not p:
            return None
        return so_dh.get(p[0]) or (p[1] or "").strip() or None

    hd_dh = {i: d for (i, d) in db.query(HoaDon.id, HoaDon.don_hang_id).filter(HoaDon.don_hang_id.isnot(None)).all()}
    po_co_cn, dh_co_cn_thu = set(), set()
    for c in db.query(CongNo).all():
        da = _f(c.da_thanh_toan)
        if c.loai == "PHAI_TRA":
            if c.don_mua_id:
                po_co_cn.add(c.don_mua_id)
                ma = ma_po(c.don_mua_id)
            elif c.hoa_don_id and hd_dh.get(c.hoa_don_id):
                ma = so_dh.get(hd_dh[c.hoa_don_id])
            else:
                ma = (c.ma_ban_ngoai or "").strip() or None
            if da:
                cong(ma, chi=da)
        elif c.loai == "PHAI_THU":
            dh_id = c.don_hang_id or (hd_dh.get(c.hoa_don_id) if c.hoa_don_id else None)
            ma = so_dh.get(dh_id) if dh_id else ((c.ma_ban_ngoai or "").strip() or None)
            if not dh_id and ma:                       # công nợ thu NHẬP NGOÀI mang mã trùng số đơn bán
                dh_id = so_key.get(ma.lower())
            if dh_id:
                dh_co_cn_thu.add(dh_id)                # đơn đã có công nợ thu → cọc coi như đã cấn, không cộng lần 2
            if da:
                cong(ma, thu=da)
    for pid, (dh, mb, dd, dn) in po.items():          # PO cũ: đã ghi trả nhưng chưa có dòng công nợ
        if pid in po_co_cn:
            continue
        da = _f(dd if dd is not None else dn)
        if da > 0:
            cong(ma_po(pid), chi=da)
    for i, o in tra_truoc_theo_don(db).items():       # trả trước của khách chưa cấn vào công nợ
        v = o["tam_ung"] if i in dh_co_cn_thu else o["tra_truoc"]
        if v:
            cong(so_dh.get(i), thu=v)
    return out
