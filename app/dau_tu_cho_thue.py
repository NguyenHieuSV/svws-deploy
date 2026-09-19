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


def so_thang_giua(a: date, b: date) -> int:
    """Số tháng đã chạy từ a đến b, tính TRỌN tháng bắt đầu và tháng hiện tại (a=15/07, b=19/09 → 3)."""
    if not a or not b or b < a:
        return 0
    return (b.year - a.year) * 12 + (b.month - a.month) + 1


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


def tong_hop(db: Session, hom_nay: date | None = None) -> dict:
    """Bảng vốn đầu tư – khấu hao – hoàn vốn của MỌI dự án cho thuê + danh sách đơn đầu tư / đơn nghi là đầu tư."""
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
    out, tong = [], {"von": 0.0, "kh_luy_ke": 0.0, "con_lai": 0.0, "dt": 0.0, "cp": 0.0}
    for t in ds_ts:
        g = theo_ts[t.id]
        von = _f(t.nguyen_gia) + g["von_po"]
        if von <= 0 and not g["don_thang"] and not g["don_dau_tu"]:
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
                    "so_thang_hd": n_hd, "ngay_bat_dau_hd": str(bat_dau) if bat_dau else None,
                    "san_luong_toi_thieu": _f(getattr(t, "san_luong_toi_thieu", 0)),
                    "san_luong_du_kien": _f(getattr(t, "san_luong_du_kien", 0)),
                    "gia_tri_hd_uoc_tinh": gia_tri_hd_uoc_tinh(t),
                    "nguyen_gia_dau_ky": _f(t.nguyen_gia), "von_tu_don": g["von_po"], "von_dau_tu": von,
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
