"""📋 KIỂM SOÁT BÁO GIÁ ↔ DỰ TOÁN (anh Hiếu chốt 28/10/2026).

  ① Báo giá phải có DỰ TOÁN cùng mã (Dự toán hàng bán, hoặc BOQ dự án), có ≥ 1 dòng và MỌI dòng có số lượng
     đều có đơn giá → mới TRÌNH DUYỆT / DUYỆT / GỬI KHÁCH được. Thiếu → người thường bị chặn, CEO được vượt
     sau khi xác nhận (ghi audit). Nút «+ Tạo báo giá» TRỐNG chỉ CEO dùng; người khác tạo từ dự toán.
  ② Báo giá lưu liên kết dự toán gốc (noi_dung.du_toan_id / du_toan_ma). Lúc DUYỆT: so TỔNG báo giá (chưa VAT)
     với TỔNG dự toán (giá vốn, chưa VAT) → biên < ngưỡng (mặc định 15%) hoặc báo giá không có dòng giá để so
     (báo giá theo file) → cờ 📉, chỉ CEO duyệt (phải xác nhận).
  ③ Tạo báo giá từ dự toán: đơn giá bán GỢI Ý = giá dự toán × (1 + biên gợi ý, mặc định 20%), làm tròn nghìn.
"""
from sqlalchemy.orm import Session

from .config import settings


def bien_toi_thieu() -> float:
    try:
        return float(settings.bg_bien_toi_thieu)
    except (TypeError, ValueError):
        return 15.0


def bien_goi_y() -> float:
    try:
        return float(settings.bg_bien_goi_y)
    except (TypeError, ValueError):
        return 20.0


def _tr(v) -> str:
    return f"{float(v or 0) / 1e6:,.1f} tr".replace(",", "X").replace(".", ",").replace("X", ".")


def _pt(b) -> str:
    return f"{float(b):.1f}".replace(".", ",")


def tim_du_toan(db: Session, bgf) -> dict | None:
    """Dự toán gốc của báo giá: liên kết đã lưu → Dự toán hàng bán cùng mã → BOQ dự án cùng mã (kể cả mã khác thứ tự).
    → {loai DTB|BOQ, id, ma, so_dong, dong_thieu_gia[], tong} hoặc None."""
    from .du_toan_ks import tim_da_theo_ma, tim_dtb_theo_ma
    from .models import DuAnDuToan, DuToanBan, DuToanBanMuc
    nd = bgf.noi_dung or {}
    ma = str(bgf.so or nd.get("so") or "").strip()
    dt = None
    if nd.get("du_toan_id"):
        try:
            dt = db.get(DuToanBan, int(nd["du_toan_id"]))
        except (TypeError, ValueError):
            dt = None
    if dt is None and ma:
        ds = tim_dtb_theo_ma(db, ma)
        dt = ds[0] if ds else None
    if dt is not None:
        rows = [(m.ten, float(m.so_luong or 0), float(m.don_gia or 0))
                for m in db.query(DuToanBanMuc).filter_by(du_toan_id=dt.id).all()]
        loai, did, dma = "DTB", dt.id, dt.ma
    else:
        das = tim_da_theo_ma(db, ma) if ma else []
        if not das:
            return None
        da = das[0]
        rows = [(x.ten, float(x.so_luong or 0), float(x.don_gia or 0))
                for x in db.query(DuAnDuToan).filter_by(du_an_id=da.id).all()]
        loai, did, dma = "BOQ", da.id, da.ma
    co_sl = [r for r in rows if r[1] > 0]
    return {"loai": loai, "id": did, "ma": dma, "so_dong": len(co_sl),
            "dong_thieu_gia": [r[0] for r in co_sl if r[2] <= 0],
            "tong": sum(r[1] * r[2] for r in co_sl)}


def kiem_tra(db: Session, bgf) -> dict:
    """Kết quả kiểm soát của một báo giá (dùng cho cổng trình duyệt / duyệt / gửi và nhãn trên danh sách)."""
    from .bao_gia_pdf import tinh_bao_gia
    dt = tim_du_toan(db, bgf)
    ma = str(bgf.so or (bgf.noi_dung or {}).get("so") or "").strip()
    thieu = None
    if dt is None:
        thieu = f"Báo giá {ma or '(chưa có số)'} CHƯA CÓ DỰ TOÁN cùng mã (Dự toán hàng bán / BOQ dự án)."
    elif dt["so_dong"] == 0:
        thieu = f"Dự toán {dt['ma']} chưa có dòng sản phẩm nào."
    elif dt["dong_thieu_gia"]:
        n = len(dt["dong_thieu_gia"])
        thieu = (f"Dự toán {dt['ma']} còn {n} dòng CHƯA CÓ ĐƠN GIÁ (vd: {', '.join(dt['dong_thieu_gia'][:3])}"
                 + ("…" if n > 3 else "") + ").")
    try:
        tong_bg = float(tinh_bao_gia(bgf.noi_dung or {})[0])
    except Exception:                                                    # noqa: BLE001
        tong_bg = 0.0
    bien, ly_do_bien = None, None
    ng = bien_toi_thieu()
    if dt is not None and not thieu:
        if tong_bg <= 0:
            ly_do_bien = (f"Báo giá không có dòng giá để so với dự toán {dt['ma']} ({_tr(dt['tong'])}) — "
                          "báo giá theo file đính kèm / chưa nhập đơn giá.")
        else:
            bien = round((tong_bg - dt["tong"]) / tong_bg * 100, 1)
            if bien < ng:
                ly_do_bien = (f"Tổng báo giá {_tr(tong_bg)} (chưa VAT) so với dự toán {dt['ma']} {_tr(dt['tong'])} → "
                              + (f"LỖ {_tr(dt['tong'] - tong_bg)} (biên {_pt(bien)}%)" if bien < 0
                                 else f"biên chỉ {_pt(bien)}% < ngưỡng {ng:g}%") + ".")
    return {"du_toan": dt, "thieu_du_toan": thieu, "tong_bg": tong_bg, "bien": bien, "nguong": ng,
            "canh_bao_bien": ly_do_bien}


def la_ceo(nd) -> bool:
    return (getattr(getattr(nd, "vai_tro", None), "ma", None) or "").upper() == "CEO"


def la_qtv(nd) -> bool:
    """CEO / ADMIN — được chỉnh giá bán DƯỚI sàn biên (anh Hiếu 28/10/2026)."""
    return (getattr(getattr(nd, "vai_tro", None), "ma", None) or "").upper() in ("CEO", "ADMIN")


def san_bien() -> dict:
    """Sàn biên theo nhóm (%) + chi phí chung — nhân viên không được đặt giá bán dưới sàn."""
    def _f(v, mac):
        try:
            return float(v)
        except (TypeError, ValueError):
            return mac
    return {"THIET_BI": _f(settings.bg_bien_thiet_bi, 15.0), "VAT_TU": _f(settings.bg_bien_vat_tu, 25.0),
            "NHAN_CONG": _f(settings.bg_bien_nhan_cong, 30.0), "chi_phi_chung": _f(settings.bg_chi_phi_chung, 5.0)}


def dong_duoi_san(noi_dung: dict) -> list:
    """Các dòng có giá vốn mà biên (trên giá bán, sau chi phí chung) < sàn của nhóm → [{ten, nhom, bien, san}].
    Dòng không có giá vốn (chưa ước) không xét."""
    nd = noi_dung or {}
    san = san_bien()
    cpc = nd.get("chi_phi_chung")
    cpc = san["chi_phi_chung"] if cpc in (None, "") else float(cpc)
    out = []
    for it in nd.get("items") or []:
        von = float(it.get("gia_von") or 0)
        gia = float(it.get("don_gia") or 0)
        if von <= 0 or float(it.get("so_luong") or 0) <= 0:
            continue
        nhom = (it.get("nhom") or "VAT_TU").upper()
        s = san.get(nhom, san["VAT_TU"])
        v = von * (1 + cpc / 100)
        bien = (gia - v) / gia * 100 if gia > 0 else -100.0
        if bien + 1e-9 < s:
            out.append({"ten": it.get("ten") or "", "nhom": nhom, "bien": round(bien, 1), "san": s})
    return out


def chan_duoi_san(noi_dung: dict, nd) -> None:
    """Lưu / trình duyệt báo giá: có dòng dưới sàn mà không phải CEO / Admin → 403."""
    from fastapi import HTTPException, status
    if la_qtv(nd):
        return
    ds = dong_duoi_san(noi_dung)
    if ds:
        vd = "; ".join(f"«{x['ten'][:40]}» {_pt(x['bien'])}% < sàn {x['san']:g}%" for x in ds[:3])
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            f"🔒 {len(ds)} dòng có giá bán DƯỚI SÀN biên ({vd}{'…' if len(ds) > 3 else ''}). "
                            "Nhân viên chỉ chỉnh giá từ sàn trở lên — muốn thấp hơn, nhờ CEO / Admin sửa.")


def cong(db: Session, bgf, nd, xac_nhan: bool, buoc: str, kiem_bien: bool = False) -> dict:
    """Cổng kiểm soát một bước (TRÌNH DUYỆT / DUYỆT / GỬI KHÁCH).
    Thiếu dự toán: người thường 400; CEO chưa xác nhận 409 (📋). Biên thấp (khi kiem_bien): người thường 403; CEO 409 (📉)."""
    from fastapi import HTTPException, status
    k = kiem_tra(db, bgf)
    van_de = []
    if k["thieu_du_toan"]:
        if not la_ceo(nd):
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"📋 {k['thieu_du_toan']} Báo giá phải lập từ dự toán có đủ dòng và đủ giá mới {buoc} được — "
                                "lập / hoàn thiện ở Bán hàng → Dự toán hàng bán (hoặc BOQ dự án) rồi làm lại. CEO được vượt.")
        van_de.append("📋 " + k["thieu_du_toan"])
    if kiem_bien and k["canh_bao_bien"]:
        if not la_ceo(nd):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"📉 {k['canh_bao_bien']} — chỉ CEO duyệt được báo giá này.")
        van_de.append("📉 " + k["canh_bao_bien"])
    if van_de and not xac_nhan:
        raise HTTPException(status.HTTP_409_CONFLICT, " ".join(van_de))
    k["vuot"] = van_de
    return k
