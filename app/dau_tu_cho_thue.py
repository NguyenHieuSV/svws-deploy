"""
ĐẦU TƯ – CHO THUÊ (hợp đồng bán nước / cho thuê hệ thống theo THÁNG hoặc theo M³) — công thức dùng chung.

Bản chất (chốt với CEO 19/09/2026):
  • Thiết bị Sóng Việt BỎ VỐN, vẫn thuộc Sóng Việt khi hết hợp đồng  → là TÀI SẢN, không phải giá vốn một lần bán.
  • KHẤU HAO THEO THỜI GIAN hợp đồng:  khấu hao tháng = vốn đầu tư / số tháng hợp đồng.
  • Hợp đồng CÓ SẢN LƯỢNG TỐI THIỂU mỗi tháng:  m³ tính tiền = max(m³ thực tế, m³ tối thiểu).

Cách ghi trong hệ thống:
  • DỰ ÁN CHO THUÊ (tai_san_cho_thue) = MÃ MẸ, giữ thông số hợp đồng (đơn giá · số tháng · ngày bắt đầu · sản lượng).
  • ĐƠN «ĐẦU TƯ» (don_hang.loai_don = 'DAU_TU', nối mã mẹ): mọi PO / chi phí của đơn = VỐN ĐẦU TƯ của dự án —
    KHÔNG vào giá vốn, KHÔNG tính doanh thu, không bị gắn cờ bất thường.
  • ĐƠN THÁNG (DV-…-MMYY…): doanh thu + chi phí vận hành của tháng — lãi/lỗ theo mã như thường.
  • Lãi/lỗ dự án:  tháng  = DT tháng − CP vận hành tháng − khấu hao tháng
                   lũy kế = Σ DT − Σ CP vận hành − vốn đầu tư  →  % hoàn vốn.
"""
import re
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from .ma_code import phan_tich
from .models import DonHang, TaiSanChoThue

LOAI_DAU_TU = "DAU_TU"
NGUONG_NGHI = 20_000_000        # đ — mã DV chi từ mức này mà gần như không có doanh thu → gợi ý xem có phải đơn đầu tư


def _f(v) -> float:
    return float(v or 0)


def la_don_dau_tu(dh) -> bool:
    return (getattr(dh, "loai_don", None) or "").upper() == LOAI_DAU_TU


def goc_cua_ma(ma) -> str | None:
    """'DV-COA-NT-0926-01' / 'DV-COA-NT-2024' → 'DV-COA-NT' (phần gốc, bỏ tháng / năm + hậu tố)."""
    p = phan_tich(ma)
    return p["goc_khong_thang"] or None


def du_an_cua_ma(db: Session, ma, ds=None):
    """Dự án cho thuê (mã mẹ) mà một mã đơn / mã tháng thuộc về: trùng mã, hoặc cùng GỐC (mã mẹ = gốc · gốc-YYYY · gốc-MMYY)."""
    m = str(ma or "").strip()
    if not m:
        return None
    ds = ds if ds is not None else db.query(TaiSanChoThue).all()
    for t in ds:
        if (t.ma or "").strip().lower() == m.lower():
            return t
    goc = goc_cua_ma(m)
    if not goc:
        return None
    for t in ds:
        for ten in ((t.ma or "").strip(), (t.ten_du_an or "").strip()):
            if not ten.lower().startswith(goc.lower()):
                continue
            con = ten[len(goc):]
            if con == "" or re.fullmatch(r"-\d{4}", con):
                return t
    return None


def goc_du_an(ts) -> str:
    """Gốc mã của dự án: 'DV-COA-NT-2024' → 'DV-COA-NT' · 'DV-COA-REJ-0926' → 'DV-COA-REJ' · 'DV-COH-NT-EDI' → giữ nguyên."""
    for ten in ((getattr(ts, "ten_du_an", None) or ""), (getattr(ts, "ma", None) or "")):
        ten = ten.strip()
        if ten:
            return goc_cua_ma(ten) or ten.upper()
    return ""


def ma_thang_chuan(ts, ngay: date) -> str:
    """Mã tháng ĐÚNG QUY TẮC của dự án: GỐC-MMYY (DV-COA-NT-0926) — dùng khi tháng đó chưa có đơn bán."""
    return f"{goc_du_an(ts)}-{ngay:%m%y}"


def don_thang_cua_du_an(db: Session, ts, ngay: date) -> list:
    """Các ĐƠN BÁN của dự án trong tháng của `ngay`: mã = GỐC-MMYY hoặc GỐC-MMYY-…; thêm đơn viết tắt (cùng khách, cùng
    đuôi gốc, cùng MMYY). Đơn GỐC-MMYY (mã gốc tháng) xếp trước, rồi theo mã."""
    goc, mmyy = goc_du_an(ts).lower(), f"{ngay:%m%y}"
    if not goc:
        return []
    out = []
    for dh in db.query(DonHang).filter(DonHang.so.isnot(None)).all():
        s = (dh.so or "").strip().lower()
        p = phan_tich(dh.so)
        if p["thang"] != mmyy or (p["loai"] or "") == "OP":
            continue
        if s == f"{goc}-{mmyy}" or s.startswith(f"{goc}-{mmyy}-"):
            out.append(dh)
        elif (getattr(ts, "khach_hang_id", None) and dh.khach_hang_id == ts.khach_hang_id
              and (p["goc_khong_thang"] or "").split("-")[-1].lower() == goc.split("-")[-1]
              and p["loai"] == phan_tich(goc)["loai"]):
            out.append(dh)
    out.sort(key=lambda d: (0 if (d.so or "").strip().lower() == f"{goc}-{mmyy}" else 1, (d.so or "")))
    return out


def la_ma_me(ma) -> bool:
    """Mã MẸ dự án (không có tháng MMYY): DV-IIVI-D26 · DV-COA-NT-2024 · DV-COH-NT-EDI."""
    p = phan_tich(ma)
    return bool(p["loai"]) and p["thang"] is None


def po_ma_me_cua_du_an(db: Session, ds_ts=None) -> dict:
    """PO ĐÃ DUYỆT không gắn đơn bán, mang MÃ MẸ của một dự án cho thuê (+ công nợ nhập ngoài cùng kiểu) → là VỐN ĐẦU TƯ của
    dự án đó (thiết bị, lắp đặt), không phải chi phí tháng. Trả {ts.id: [{loai, id, so, ngay, tong, so_hoa_don}]}."""
    from .models import DonMua, CongNo
    ds_ts = ds_ts if ds_ts is not None else db.query(TaiSanChoThue).all()
    out = {}
    for dm in (db.query(DonMua).filter(DonMua.trang_thai == "DA_DUYET", DonMua.don_hang_id.is_(None),
                                       DonMua.ma_ban.isnot(None)).all()):
        if not la_ma_me(dm.ma_ban):
            continue
        ts = du_an_cua_ma(db, dm.ma_ban, ds_ts)
        if ts is not None:
            out.setdefault(ts.id, []).append({"loai": "PO", "id": dm.id, "so": dm.so, "ngay": str(dm.ngay) if dm.ngay else None,
                                              "ma": dm.ma_ban, "tong": _f(dm.tong_tien), "so_hoa_don": dm.so_hoa_don})
    for cn in (db.query(CongNo).filter(CongNo.loai == "PHAI_TRA", CongNo.don_mua_id.is_(None), CongNo.hoa_don_id.is_(None),
                                       CongNo.ma_ban_ngoai.isnot(None)).all()):
        if not la_ma_me(cn.ma_ban_ngoai) or str(cn.so_ct or "").upper().startswith("HDM-"):
            continue
        ts = du_an_cua_ma(db, cn.ma_ban_ngoai, ds_ts)
        if ts is not None:
            out.setdefault(ts.id, []).append({"loai": "CN", "id": cn.id, "so": f"CN-{cn.id}", "ngay": str(cn.ngay_ct) if cn.ngay_ct else None,
                                              "ma": cn.ma_ban_ngoai, "tong": _f(cn.so_tien), "so_hoa_don": cn.so_ct})
    return out


def ma_me_dang_dau_tu(db: Session) -> set:
    """Các mã (chữ thường) mà PO / công nợ mang mã mẹ dự án đang được tính là VỐN ĐẦU TƯ — Lãi/Lỗ không xếp thành mã lẻ."""
    return {str(p["ma"]).strip().lower() for ds in po_ma_me_cua_du_an(db).values() for p in ds}


def vh_ma_le_cua_du_an(db: Session) -> dict:
    """Chi phí vận hành ĐƯỢC TÍNH (hóa đơn email · ghi tay · bảo trì; chưa nối PO / hóa đơn) nhưng CHƯA gắn đơn bán —
    theo dự án: {ts.id: tổng}. Khoản đã gắn đơn đã nằm trong chi_phi_ma của đơn đó."""
    from .lai_lo_ma import VH_TINH_CHI_PHI
    from .models import ChiPhiVanHanh
    out = {}
    for (tid, st) in (db.query(ChiPhiVanHanh.tai_san_id, ChiPhiVanHanh.so_tien)
                      .filter(ChiPhiVanHanh.tai_san_id.isnot(None), ChiPhiVanHanh.nguon.in_(VH_TINH_CHI_PHI),
                              ChiPhiVanHanh.don_hang_id.is_(None), ChiPhiVanHanh.don_mua_id.is_(None),
                              ChiPhiVanHanh.hoa_don_id.is_(None)).all()):
        out[tid] = out.get(tid, 0.0) + _f(st)
    return out


def chi_phi_du_an_theo_thang(db: Session, ts, months: list) -> dict:
    """CHI PHÍ THẬT của dự án theo tháng — CÙNG CÔNG THỨC với Kế toán / Overall Financial:
      po_ct    = PO đã duyệt + công nợ nhập ngoài + hóa đơn mua của các ĐƠN THÁNG (chi_phi_ma, đã loại trùng; bỏ đơn đầu tư)
      hoa_chat / bao_tri / khac = chi phí vận hành cho thuê ĐƯỢC TÍNH (hóa đơn email · ghi tay · bảo trì; chưa nối PO / hóa đơn)
                 của dự án theo tháng phát sinh — gồm cả khoản đã gắn đơn tháng (đã trừ khỏi po_ct để không đếm 2 lần)
      tham_khao = khoản đồng bộ từ đề xuất mua / tiêu hao định mức / đã nối PO-hóa đơn — KHÔNG cộng (PO đã là giá vốn).
    Trả {YYYY-MM: {po_ct, hoa_chat, bao_tri, khac, tong, tham_khao, don: [mã đơn]}}."""
    from .lai_lo_ma import chi_phi_ma, VH_TINH_CHI_PHI
    from .models import ChiPhiVanHanh
    out = {m: {"po_ct": 0.0, "hoa_chat": 0.0, "bao_tri": 0.0, "khac": 0.0, "tong": 0.0, "tham_khao": 0.0, "don": []}
           for m in months}
    for m in months:
        y, mm = int(m[:4]), int(m[5:7])
        for dh in don_thang_cua_du_an(db, ts, date(y, mm, 1)):
            if la_don_dau_tu(dh):
                continue
            cp = chi_phi_ma(db, dh)
            out[m]["po_ct"] += cp["tong_chi_phi"] - _f(cp.get("chi_van_hanh"))
            out[m]["don"].append(dh.so or f"DH-{dh.id}")
    for c in db.query(ChiPhiVanHanh).filter(ChiPhiVanHanh.tai_san_id == ts.id).all():
        mk = c.ngay.strftime("%Y-%m") if c.ngay else None
        if mk not in out:
            continue
        v = _f(c.so_tien)
        if (c.nguon or "") not in VH_TINH_CHI_PHI or c.don_mua_id or c.hoa_don_id:
            out[mk]["tham_khao"] += v
            continue
        if (c.nguon or "") == "BAO_TRI" or (c.loai_chi_phi or "") == "SUA_CHUA":
            out[mk]["bao_tri"] += v
        elif (c.loai_chi_phi or "") == "VAT_TU":
            out[mk]["hoa_chat"] += v
        else:
            out[mk]["khac"] += v
    for o in out.values():
        o["tong"] = o["po_ct"] + o["hoa_chat"] + o["bao_tri"] + o["khac"]
    return out


def so_thang_giua(a: date, b: date) -> int:
    """Số tháng đã chạy từ a đến b, tính TRỌN tháng bắt đầu và tháng hiện tại (a=15/07, b=19/09 → 3)."""
    if not a or not b or b < a:
        return 0
    return (b.year - a.year) * 12 + (b.month - a.month) + 1


def _cong_thang(bat_dau, n):
    """Ngày kết thúc hợp đồng = ngày bắt đầu + n tháng − 1 ngày (chuỗi ISO); thiếu dữ liệu → None."""
    from datetime import timedelta
    if not bat_dau or not n:
        return None
    y, m = bat_dau.year + (bat_dau.month - 1 + int(n)) // 12, (bat_dau.month - 1 + int(n)) % 12 + 1
    d, cat = bat_dau.day, False
    while d > 28:
        try:
            date(y, m, d)
            break
        except ValueError:
            d, cat = d - 1, True
    return str(date(y, m, d) - timedelta(days=0 if cat else 1))   # bắt đầu 31/01 + 1 tháng → hết 28/02


def _con_ngay(ket_thuc_iso, hom_nay):
    return (date.fromisoformat(ket_thuc_iso) - hom_nay).days if ket_thuc_iso else None


def khau_hao_thang(ts, von: float) -> float:
    """Khấu hao THEO THỜI GIAN: vốn / số tháng hợp đồng. Ô «khấu hao tháng» nhập tay (> 0) thì ưu tiên số nhập tay."""
    tay = _f(getattr(ts, "khau_hao_thang", 0))
    if tay > 0:
        return tay
    n = int(getattr(ts, "so_thang_hd", 0) or 0)
    return round(von / n) if (n > 0 and von > 0) else 0.0


def m3_tinh_tien(ts, m3_thuc) -> float:
    """Sản lượng tính tiền của một tháng có ghi chỉ số: max(thực tế, tối thiểu cam kết)."""
    toi_thieu = _f(getattr(ts, "san_luong_toi_thieu", 0))
    return max(_f(m3_thuc), toi_thieu) if _f(m3_thuc) > 0 else 0.0


def gia_tri_hd_uoc_tinh(ts) -> float:
    """Giá trị hợp đồng ƯỚC TÍNH = đơn giá × sản lượng dự kiến (≥ tối thiểu) × số tháng; hợp đồng theo tháng: giá thuê × số tháng."""
    n = int(getattr(ts, "so_thang_hd", 0) or 0)
    gia = _f(ts.gia_thue_thang)
    if n <= 0 or gia <= 0:
        return 0.0
    if (ts.don_vi_gia or "").upper() == "VND/M3":
        sl = max(_f(getattr(ts, "san_luong_du_kien", 0)), _f(getattr(ts, "san_luong_toi_thieu", 0)))
        return round(gia * sl * n)
    return round(gia * n)


def tong_hop(db: Session, hom_nay: date | None = None, tat_ca: bool = False) -> dict:
    """Bảng vốn đầu tư – khấu hao – hoàn vốn của MỌI dự án cho thuê + danh sách đơn đầu tư / đơn nghi là đầu tư.
    tat_ca=True → kể cả dự án chưa có vốn / chưa có mã tháng (để mở form thông số hợp đồng của dự án mới)."""
    from .lai_lo_ma import chi_phi_ma
    hom_nay = hom_nay or date.today()
    ds_ts = db.query(TaiSanChoThue).order_by(TaiSanChoThue.id).all()
    theo_ts = {t.id: {"don_dau_tu": [], "don_thang": [], "von_po": 0.0, "dt": 0.0, "cp": 0.0} for t in ds_ts}
    chua_noi, nghi_dau_tu, dt_nhom = [], [], {}
    for dh in db.query(DonHang).order_by(DonHang.id).all():
        dau_tu = la_don_dau_tu(dh)
        ts = db.get(TaiSanChoThue, dh.tai_san_cho_thue_id) if getattr(dh, "tai_san_cho_thue_id", None) else None
        if ts is None:
            ts = du_an_cua_ma(db, dh.so, ds_ts)
        if ts is None and dh.khach_hang_id:
            # mã tháng viết tắt, bỏ tên khách (DV-D10-0926 ↔ dự án DV-IIVI-D10-2026): cùng KHÁCH + cùng đuôi gốc
            duoi = (goc_cua_ma(dh.so) or "").split("-")[-1].lower()
            ung = [t for t in ds_ts if t.khach_hang_id == dh.khach_hang_id and duoi and len(duoi) >= 2
                   and (goc_cua_ma(t.ma) or t.ma or "").split("-")[-1].lower() == duoi
                   and phan_tich(t.ma)["loai"] == phan_tich(dh.so)["loai"]]
            ts = ung[0] if len(ung) == 1 else None
        la_dv = (phan_tich(dh.so)["loai"] == "DV")
        if ts is None and not dau_tu and not la_dv:
            continue
        cp = chi_phi_ma(db, dh, tho=True)
        dong = {"don_hang_id": dh.id, "ma": dh.so or f"DH-{dh.id}", "ngay": str(dh.ngay) if dh.ngay else None,
                "doanh_thu": cp["doanh_thu"], "chi_phi": cp["tong_chi_phi"], "so_po": cp["so_po"]}
        # NGHI LÀ ĐẦU TƯ (để CEO / KTT xem và quyết): mã DV có chi phí lớn mà doanh thu = 0 hoặc < 5% chi phí
        nh = phan_tich(dh.so)["goc"] or (dh.so or "")
        dt_nhom[nh] = dt_nhom.get(nh, 0.0) + cp["doanh_thu"]
        if not dau_tu and cp["tong_chi_phi"] >= NGUONG_NGHI and cp["doanh_thu"] < cp["tong_chi_phi"] * 0.05:
            nghi_dau_tu.append({**dong, "tai_san_id": ts.id if ts else None, "du_an": ts.ma if ts else None, "_nhom": nh})
        if ts is None and not dau_tu:
            continue
        if dau_tu:
            if ts is None:
                chua_noi.append(dong)
                continue
            theo_ts[ts.id]["don_dau_tu"].append(dong)
            theo_ts[ts.id]["von_po"] += cp["tong_chi_phi"]
            continue
        theo_ts[ts.id]["don_thang"].append(dong)
        theo_ts[ts.id]["dt"] += cp["doanh_thu"]
        theo_ts[ts.id]["cp"] += cp["tong_chi_phi"]
    # mã con CHỈ MANG CHI PHÍ của một tháng đã có doanh thu ở mã anh em (DV-COA-NT-0926-02 bên cạnh -01) = chi phí vận hành
    # tháng, KHÔNG phải đầu tư → bỏ khỏi danh sách nghi
    nghi_dau_tu = [{k: v for k, v in x.items() if k != "_nhom"} for x in nghi_dau_tu
                   if dt_nhom.get(x["_nhom"], 0.0) - x["doanh_thu"] < NGUONG_NGHI]
    po_mm, vh_le = po_ma_me_cua_du_an(db, ds_ts), vh_ma_le_cua_du_an(db)
    out, tong = [], {"von": 0.0, "kh_luy_ke": 0.0, "con_lai": 0.0, "dt": 0.0, "cp": 0.0}
    for t in ds_ts:
        g = theo_ts[t.id]
        von_mm = sum(p["tong"] for p in po_mm.get(t.id, []))     # 🏗 PO / công nợ mang MÃ MẸ dự án = vốn đầu tư
        von = _f(t.nguyen_gia) + g["von_po"] + von_mm
        g["cp"] += vh_le.get(t.id, 0.0)                          # chi phí vận hành chưa gắn đơn tháng (mã lẻ) của dự án
        if von <= 0 and not g["don_thang"] and not g["don_dau_tu"] and not tat_ca:
            continue
        kh = khau_hao_thang(t, von)
        bat_dau = getattr(t, "ngay_bat_dau_hd", None) or t.ngay_mua
        n_hd = int(getattr(t, "so_thang_hd", 0) or 0)
        da_chay = so_thang_giua(bat_dau, hom_nay) if bat_dau else 0
        if n_hd:
            da_chay = min(da_chay, n_hd)
        kh_luy_ke = min(kh * da_chay, von) if von > 0 else 0.0
        lai_vh = g["dt"] - g["cp"]                      # lãi vận hành lũy kế (chưa trừ vốn)
        out.append({"tai_san_id": t.id, "ma": t.ma, "ten": t.ten, "khach_hang_id": t.khach_hang_id,
                    "don_gia": _f(t.gia_thue_thang), "don_vi_gia": t.don_vi_gia or "VND/THANG",
                    "so_hop_dong": getattr(t, "so_hop_dong", None),
                    "ngay_ky_hd": str(t.ngay_ky_hd) if getattr(t, "ngay_ky_hd", None) else None,
                    "ngay_ket_thuc_hd": _cong_thang(bat_dau, n_hd), "con_ngay_hd": _con_ngay(_cong_thang(bat_dau, n_hd), hom_nay),
                    "so_thang_hd": n_hd, "ngay_bat_dau_hd": str(bat_dau) if bat_dau else None,
                    "san_luong_toi_thieu": _f(getattr(t, "san_luong_toi_thieu", 0)),
                    "san_luong_du_kien": _f(getattr(t, "san_luong_du_kien", 0)),
                    "gia_tri_hd_uoc_tinh": gia_tri_hd_uoc_tinh(t),
                    "nguyen_gia_dau_ky": _f(t.nguyen_gia), "von_tu_don": g["von_po"], "von_dau_tu": von,
                    "von_ma_me": von_mm, "po_ma_me": po_mm.get(t.id, []),
                    "khau_hao_thang": kh, "khau_hao_nhap_tay": _f(t.khau_hao_thang) > 0,
                    "thang_da_chay": da_chay, "khau_hao_luy_ke": kh_luy_ke, "gia_tri_con_lai": max(von - kh_luy_ke, 0.0),
                    "dt_luy_ke": g["dt"], "cp_van_hanh_luy_ke": g["cp"], "lai_van_hanh_luy_ke": lai_vh,
                    "lai_sau_khau_hao": lai_vh - kh_luy_ke,
                    "von_chua_thu_hoi": max(von - max(lai_vh, 0.0), 0.0),
                    "hoan_von_pct": round(max(lai_vh, 0.0) / von * 100, 1) if von > 0 else None,
                    "thang_hoan_von_con": (round((von - lai_vh) / (lai_vh / da_chay)) if (von > lai_vh > 0 and da_chay > 0) else None),
                    "thieu_thong_so": [x for x, ok in (("số tháng hợp đồng", n_hd > 0), ("ngày bắt đầu", bool(bat_dau))) if not ok] if von > 0 else [],
                    "don_dau_tu": g["don_dau_tu"], "so_don_thang": len(g["don_thang"])})
        tong["von"] += von; tong["kh_luy_ke"] += kh_luy_ke; tong["con_lai"] += max(von - kh_luy_ke, 0.0)
        tong["dt"] += g["dt"]; tong["cp"] += g["cp"]
    tong["von_chua_thu_hoi"] = sum(x["von_chua_thu_hoi"] for x in out)
    return {"ngay": str(hom_nay), "du_an": out, "tong": tong, "don_dau_tu_chua_noi": chua_noi, "nghi_dau_tu": nghi_dau_tu}
