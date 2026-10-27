"""📉 KIỂM SOÁT LỢI NHUẬN THEO MÃ (anh Hiếu chốt 27/10/2026) — chi phí mua hàng của mã so với DOANH THU của mã.

Đọc theo NHÓM mã gốc + tháng (DV-COA-NT-0826-01/-02/-03 + PO ghi mã gốc = một nhóm), cùng công thức Kiểm soát
(app/lai_lo_ma.py: chi phí = PO đã duyệt + công nợ nhập ngoài + hóa đơn mua gắn mã; doanh thu gồm VAT).

  ① Lúc DUYỆT đơn mua: tổng chi phí nhóm (tính cả PO đang duyệt) > doanh thu, biên lợi nhuận < ngưỡng
     (mặc định 15%), hoặc nhóm chưa có doanh thu → cờ 📉, CHỈ CEO duyệt (phải xác nhận).
     Miễn: mã OP-… (chi phí vận hành DN), KHO (mua dự trữ), dự án ĐẦU TƯ – cho thuê, mã mẹ theo năm.
     Mã DV-… chưa ghi doanh thu tháng này → so với doanh thu THÁNG TRƯỚC cùng mã gốc (DV ghi doanh thu cuối tháng).
  ② Nhắc HẰNG TUẦN (thứ Hai) vào nhóm Google Chat Duyệt chi (nhóm hạn chế người xem): nhóm mã lỗ · có chi phí
     mà chưa có doanh thu · biên thấp.
"""
import re
from datetime import date

from sqlalchemy.orm import Session

from .config import settings

_MMYY = re.compile(r"^(0[1-9]|1[0-2])(\d{2})$")


def nguong() -> float:
    try:
        return float(settings.po_bien_ln_toi_thieu)
    except (TypeError, ValueError):
        return 15.0


def _tr(v) -> str:
    return f"{float(v or 0) / 1e6:,.1f} tr".replace(",", "X").replace(".", ",").replace("X", ".")


def mien_kiem(ma: str) -> bool:
    """Mã không so với doanh thu: OP- / KHO / mã mẹ theo năm (cho thuê) / không có mã."""
    from .ma_code import phan_tich
    s = str(ma or "").strip().upper()
    if not s or s.startswith("OP-") or s == "OP" or s.startswith("KHO"):
        return True
    p = phan_tich(s)
    return p.get("kieu") == "NAM"


def nhom_cua(ma: str) -> str:
    from .lai_lo_ma import nhom_ma
    return nhom_ma(ma) or str(ma or "").strip().upper()


def nhom_thang_truoc(nh: str) -> str | None:
    """'DV-COA-NT-1026' → 'DV-COA-NT-0926'."""
    parts = str(nh or "").split("-")
    for i, x in enumerate(parts):
        mt = _MMYY.match(x) if i else None
        if mt:
            m, y = int(mt.group(1)), int(mt.group(2))
            m, y = (12, y - 1) if m == 1 else (m - 1, y)
            parts[i] = f"{m:02d}{y % 100:02d}"
            return "-".join(parts)
    return None


def so_lieu_nhom(db: Session, nh: str) -> dict:
    """Doanh thu / chi phí của MỘT nhóm gốc + tháng — chỉ tính các đơn bán + mã lẻ thuộc nhóm (nhanh)."""
    from .lai_lo_ma import chi_phi_ma, chi_phi_ngoai_ma, nhom_ma
    from .models import DonHang
    dt = cp = 0.0
    dau_tu = False
    ma = []
    goc = str(nh or "").strip()
    if not goc:
        return {"dt": 0.0, "cp": 0.0, "dau_tu": False, "ma": []}
    for dh in db.query(DonHang).filter(DonHang.so.ilike(goc + "%")).all():
        if (nhom_ma(dh.so) or (dh.so or "").strip().upper()) != goc.upper():
            continue
        c = chi_phi_ma(db, dh)
        dt += float(c.get("doanh_thu") or 0)
        cp += float(c.get("tong_chi_phi") or 0)
        dau_tu = dau_tu or bool(c.get("la_dau_tu"))
        ma.append(dh.so)
    for g in chi_phi_ngoai_ma(db)["ma_le"].values():
        if (nhom_ma(g["ma"]) or str(g["ma"]).strip().upper()) == goc.upper():
            cp += float(g.get("chi") or 0)
            ma.append(g["ma"])
    return {"dt": dt, "cp": cp, "dau_tu": dau_tu, "ma": ma}


def danh_gia(db: Session, ma: str, them_chi_phi: float = 0.0) -> dict | None:
    """Đánh giá mã khi thêm một khoản chi (PO đang duyệt). None = ổn / được miễn; dict = cờ 📉."""
    if mien_kiem(ma):
        return None
    nh = nhom_cua(ma)
    s = so_lieu_nhom(db, nh)
    if s["dau_tu"]:
        return None
    dt, cp = s["dt"], s["cp"] + float(them_chi_phi or 0)
    tham_chieu = None
    if dt <= 0 and str(nh).upper().startswith("DV-"):
        truoc = nhom_thang_truoc(nh)
        if truoc:
            s2 = so_lieu_nhom(db, truoc)
            if s2["dt"] > 0:
                dt, tham_chieu = s2["dt"], truoc
    ng = nguong()
    if dt <= 0:
        return {"muc": "CHUA_DT", "nhom": nh, "doanh_thu": 0.0, "chi_phi": cp, "bien": None, "nguong": ng,
                "ly_do": f"Mã {nh} CHƯA CÓ DOANH THU — chi phí sẽ là {_tr(cp)} (tính cả đơn này)."}
    bien = round((dt - cp) / dt * 100, 1)
    if bien >= ng:
        return None
    nguon_dt = f"doanh thu tháng trước ({tham_chieu}) {_tr(dt)}" if tham_chieu else f"doanh thu {_tr(dt)}"
    return {"muc": "LO" if bien < 0 else "BIEN_THAP", "nhom": nh, "doanh_thu": dt, "chi_phi": cp, "bien": bien,
            "nguong": ng, "tham_chieu": tham_chieu,
            "ly_do": (f"Mã {nh}: chi phí {_tr(cp)} (tính cả đơn này) so với {nguon_dt} → "
                      + (f"LỖ {_tr(cp - dt)} (biên {bien}%)" if bien < 0 else f"biên lợi nhuận chỉ {bien}% < ngưỡng {ng:g}%")
                      + ".")}


def danh_gia_po(db: Session, dm) -> dict | None:
    """Cờ 📉 cho một đơn mua (PO chưa duyệt: cộng tổng PO vào chi phí nhóm)."""
    from .routers.ncc import _ma_ban_hang_po
    ma = _ma_ban_hang_po(db, dm)
    if not ma:
        return None
    them = 0.0 if dm.trang_thai == "DA_DUYET" else float(dm.tong_tien or 0)
    return danh_gia(db, ma, them)


# ---------------- ② nhắc hằng tuần ----------------
def bao_cao_tuan(db: Session, hom_nay: date | None = None) -> dict:
    """Theo nhóm gốc + tháng (cùng bảng Kiểm soát): nhóm LỖ · có chi phí CHƯA CÓ doanh thu · BIÊN THẤP.
    Bỏ OP / KHO / đầu tư / mã mẹ; nhóm của THÁNG HIỆN TẠI chưa có doanh thu thì chưa tính (doanh thu ghi cuối tháng)."""
    from .routers.ncc import chi_phi_theo_don
    hom_nay = hom_nay or date.today()
    thang_nay = f"{hom_nay:%m%y}"
    g = {}
    for x in chi_phi_theo_don(db, None):
        ma = x.get("ma_ban") or ""
        if mien_kiem(ma):
            continue
        k = x.get("nhom") or str(ma).strip().upper()
        o = g.setdefault(k, {"nhom": k, "dt": 0.0, "cp": 0.0, "dau_tu": False})
        o["dt"] += float(x.get("doanh_thu") or 0)
        o["cp"] += float(x.get("tong_chi_phi") or 0)
        o["dau_tu"] = o["dau_tu"] or bool(x.get("la_dau_tu"))
    ng = nguong()
    lo, chua_dt, bien_thap = [], [], []
    for o in g.values():
        if o["dau_tu"] or o["cp"] <= 0:
            continue
        if o["dt"] <= 0:
            if not str(o["nhom"]).endswith(thang_nay) and f"-{thang_nay}" not in str(o["nhom"]):
                chua_dt.append(o)
            continue
        bien = (o["dt"] - o["cp"]) / o["dt"] * 100
        o["bien"] = round(bien, 1)
        if bien < 0:
            lo.append(o)
        elif bien < ng:
            bien_thap.append(o)
    lo.sort(key=lambda o: o["dt"] - o["cp"])
    chua_dt.sort(key=lambda o: -o["cp"])
    bien_thap.sort(key=lambda o: o["bien"])
    return {"lo": lo, "chua_dt": chua_dt, "bien_thap": bien_thap, "nguong": ng}


def noi_dung_tuan(bc: dict, nhan: str = "") -> str | None:
    lo, chua, thap = bc["lo"], bc["chua_dt"], bc["bien_thap"]
    if not (lo or chua or thap):
        return None
    l = [f"📉 *KIỂM SOÁT LỢI NHUẬN THEO MÃ* {nhan}".rstrip(), "(theo nhóm mã gốc + tháng · chi phí = PO đã duyệt + công nợ / hóa đơn gắn mã)"]
    if lo:
        l.append(f"\n🔴 *Đang lỗ* — {len(lo)} nhóm:")
        l += [f"• {o['nhom']}: doanh thu {_tr(o['dt'])} · chi phí {_tr(o['cp'])} · lỗ {_tr(o['cp'] - o['dt'])}" for o in lo[:10]]
    if chua:
        l.append(f"\n🟠 *Có chi phí, CHƯA có doanh thu* — {len(chua)} nhóm (tổng {_tr(sum(o['cp'] for o in chua))}):")
        l += [f"• {o['nhom']}: chi phí {_tr(o['cp'])}" for o in chua[:10]]
    if thap:
        l.append(f"\n🟡 *Biên lợi nhuận dưới {bc['nguong']:g}%* — {len(thap)} nhóm:")
        l += [f"• {o['nhom']}: biên {o['bien']}% (doanh thu {_tr(o['dt'])} · chi phí {_tr(o['cp'])})" for o in thap[:10]]
    l.append("\n👉 App SVWS → Nhà cung cấp → Kiểm soát (Chi phí theo mã) · Kế toán → Lãi/Lỗ mã bán")
    return "\n".join(l)


def gui_tuan(db: Session, nguon: str = "TU_DONG", nguoi=None) -> dict:
    """Gửi bản kiểm soát lợi nhuận vào nhóm Duyệt chi (webhook riêng, hạn chế người xem). Không ném lỗi."""
    from .chat_gateway import gui_webhook_rieng
    url = (settings.gchat_webhook_duyet_chi or "").strip()
    if not url:
        return {"da_gui": False, "ly_do": "Chưa cấu hình GCHAT_WEBHOOK_DUYET_CHI (nhóm Duyệt chi)"}
    try:
        bc = bao_cao_tuan(db)
        nd = noi_dung_tuan(bc, f"— tuần {date.today():%V/%Y}")
        if not nd:
            return {"da_gui": False, "ly_do": "Không có nhóm mã nào lỗ / chưa có doanh thu / biên thấp"}
        kq = gui_webhook_rieng(url, nd)
        return {"da_gui": bool(kq.get("da_gui")), "loi": kq.get("loi"), "so_lo": len(bc["lo"]),
                "so_chua_dt": len(bc["chua_dt"]), "so_bien_thap": len(bc["bien_thap"])}
    except Exception as e:                                               # noqa: BLE001
        return {"da_gui": False, "loi": f"{type(e).__name__}: {str(e)[:150]}"}
