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
        rows = [(m.id, m.ten, float(m.so_luong or 0), float(m.don_gia or 0))
                for m in db.query(DuToanBanMuc).filter_by(du_toan_id=dt.id).all()]
        loai, did, dma = "DTB", dt.id, dt.ma
    else:
        das = tim_da_theo_ma(db, ma) if ma else []
        if not das:
            return None
        da = das[0]
        rows = [(x.id, x.ten, float(x.so_luong or 0), float(x.don_gia or 0))
                for x in db.query(DuAnDuToan).filter_by(du_an_id=da.id).all()]
        loai, did, dma = "BOQ", da.id, da.ma
    co_sl = [r for r in rows if r[2] > 0]
    # dòng báo giá đánh dấu «không chào» (khong_chao) → trừ khỏi tổng dự toán dùng để so biên
    bo = {int(it.get("dt_muc_id")) for it in (nd.get("items") or [])
          if (it.get("khong_chao") or it.get("tuy_chon")) and it.get("dt_muc_id") not in (None, "")}
    tong = sum(r[2] * r[3] for r in co_sl if r[0] not in bo)
    # dòng NGOÀI dự toán (nhân viên tự thêm) có chi phí dự kiến → cộng vào giá vốn khi so biên
    ngoai = [it for it in (nd.get("items") or []) if it.get("ngoai_du_toan") and not it.get("khong_chao")
             and not it.get("tuy_chon") and float(it.get("so_luong") or 0) > 0]
    tong += sum(float(it.get("so_luong") or 0) * float(it.get("gia_von") or 0) for it in ngoai)
    return {"loai": loai, "id": did, "ma": dma, "so_dong": len(co_sl),
            "dong_thieu_gia": [r[1] for r in co_sl if r[3] <= 0 and r[0] not in bo],
            "tong": tong, "so_bo": len(bo),
            "dong": [{"id": r[0], "ten": r[1], "so_luong": r[2], "don_gia": r[3]} for r in rows],
            "ngoai_du_toan": [{"ten": it.get("ten") or "", "so_luong": float(it.get("so_luong") or 0),
                               "gia_von": float(it.get("gia_von") or 0), "don_gia": float(it.get("don_gia") or 0)}
                              for it in ngoai],
            "ngoai_chua_uoc": [it.get("ten") or "" for it in ngoai if float(it.get("gia_von") or 0) <= 0]}


def luu_phien_ban(db: Session, bgf, nd_id, gui_den: str | None) -> dict:
    """Mỗi lần ✉️ gửi khách: lưu bản chụp Rev.A / B / C… kèm tổng chính, tổng tùy chọn, giá vốn, biên."""
    from .bao_gia_pdf import tinh_bao_gia, tinh_tuy_chon
    from .models import BaoGiaPhienBan
    from .nhac_viec_service import gio_hien_tai
    so_cu = db.query(BaoGiaPhienBan).filter(BaoGiaPhienBan.bao_gia_form_id == bgf.id).count()
    rev = chr(65 + so_cu) if so_cu < 26 else f"Z{so_cu - 25}"
    nd = bgf.noi_dung or {}
    k = kiem_tra(db, bgf)
    sub, _v, tong = tinh_bao_gia(nd)
    von = float((k["du_toan"] or {}).get("tong") or 0)
    pb = BaoGiaPhienBan(bao_gia_form_id=bgf.id, rev=rev, so=bgf.so or nd.get("so"), noi_dung=nd,
                        tong_chua_vat=round(sub), tong_gom_vat=round(tong), tong_tuy_chon=round(tinh_tuy_chon(nd)),
                        gia_von=round(von), bien=k["bien"], gui_den=(gui_den or "")[:300] or None, nguoi_gui=nd_id,
                        gui_luc=gio_hien_tai())
    db.add(pb); db.flush()
    return {"rev": rev, "id": pb.id, "tong_chua_vat": float(pb.tong_chua_vat), "bien": k["bien"]}


def ds_phien_ban(db: Session, bgf_id: int) -> list:
    from .models import BaoGiaPhienBan
    out = []
    for p in db.query(BaoGiaPhienBan).filter(BaoGiaPhienBan.bao_gia_form_id == bgf_id).order_by(BaoGiaPhienBan.id).all():
        out.append({"id": p.id, "rev": p.rev, "so": p.so, "tong_chua_vat": float(p.tong_chua_vat or 0),
                    "tong_gom_vat": float(p.tong_gom_vat or 0), "tong_tuy_chon": float(p.tong_tuy_chon or 0),
                    "gia_von": float(p.gia_von or 0), "bien": float(p.bien) if p.bien is not None else None,
                    "gui_den": p.gui_den, "gui_luc": p.gui_luc.strftime("%d/%m/%Y %H:%M") if p.gui_luc else None,
                    "so_dong": len([it for it in (p.noi_dung or {}).get("items") or [] if not it.get("khong_chao")])})
    return out


def so_sanh_lan_truoc(db: Session, bgf) -> dict | None:
    """Bản hiện tại so với lần gửi khách gần nhất: chênh tổng, chênh biên, dòng thêm / bớt / đổi giá."""
    from .bao_gia_pdf import tinh_bao_gia
    ds = ds_phien_ban(db, bgf.id)
    if not ds:
        return None
    from .models import BaoGiaPhienBan
    p = db.get(BaoGiaPhienBan, ds[-1]["id"])
    cu = {str(it.get("dt_muc_id") or ("#" + str(it.get("ten") or ""))): it
          for it in (p.noi_dung or {}).get("items") or [] if not it.get("khong_chao")}
    moi = {str(it.get("dt_muc_id") or ("#" + str(it.get("ten") or ""))): it
           for it in (bgf.noi_dung or {}).get("items") or [] if not it.get("khong_chao")}
    them = [moi[k].get("ten") or "" for k in moi if k not in cu]
    bot = [cu[k].get("ten") or "" for k in cu if k not in moi]
    doi = [{"ten": moi[k].get("ten") or "", "cu": float(cu[k].get("don_gia") or 0), "moi": float(moi[k].get("don_gia") or 0)}
           for k in moi if k in cu and abs(float(cu[k].get("don_gia") or 0) - float(moi[k].get("don_gia") or 0)) > 0.5]
    k = kiem_tra(db, bgf)
    sub = float(tinh_bao_gia(bgf.noi_dung or {})[0])
    return {"rev": ds[-1]["rev"], "gui_luc": ds[-1]["gui_luc"], "tong_truoc": ds[-1]["tong_chua_vat"], "tong_nay": sub,
            "chenh_tong": sub - ds[-1]["tong_chua_vat"], "bien_truoc": ds[-1]["bien"], "bien_nay": k["bien"],
            "them": them, "bot": bot, "doi_gia": doi, "so_phien_ban": len(ds)}


def dt_doi_gia(du_toan: dict | None, noi_dung: dict) -> list:
    """Dòng báo giá có dt_muc_id mà giá vốn / SL lưu trong báo giá khác dự toán HIỆN TẠI → [{ten, cu, moi, sl_cu, sl_moi}]
    (dự toán đổi sau khi lập báo giá — ví dụ mua được rẻ hơn)."""
    if not du_toan:
        return []
    hien = {d["id"]: d for d in du_toan.get("dong") or []}
    out = []
    for it in noi_dung.get("items") or []:
        mid = it.get("dt_muc_id")
        if mid in (None, "") or it.get("khong_chao"):
            continue
        d = hien.get(int(mid))
        if d is None:
            out.append({"ten": it.get("ten") or "", "cu": float(it.get("gia_von") or 0), "moi": None,
                        "sl_cu": float(it.get("so_luong") or 0), "sl_moi": None})
            continue
        cu, moi = float(it.get("gia_von") or 0), d["don_gia"]
        if abs(cu - moi) > 0.5 or abs(float(it.get("so_luong") or 0) - d["so_luong"]) > 1e-6:
            out.append({"ten": it.get("ten") or "", "cu": cu, "moi": moi,
                        "sl_cu": float(it.get("so_luong") or 0), "sl_moi": d["so_luong"]})
    return out


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
        nd_ = dict(bgf.noi_dung or {})
        nd_["items"] = [it for it in (nd_.get("items") or []) if not it.get("khong_chao")]
        tong_bg = float(tinh_bao_gia(nd_)[0])             # tinh_bao_gia đã bỏ dòng tùy chọn
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
            "canh_bao_bien": ly_do_bien,
            "ngoai_du_toan": (dt or {}).get("ngoai_du_toan") or [], "ngoai_chua_uoc": (dt or {}).get("ngoai_chua_uoc") or [],
            "so_bo": (dt or {}).get("so_bo") or 0, "dt_doi_gia": dt_doi_gia(dt, bgf.noi_dung or {})}


MAU_DIEU_KHOAN = {
    "TM": {"ten": "Thương mại (bán thiết bị / vật tư)", "hieu_luc": "30 days from quotation date",
           "tt": "100% payment within 30 days after delivery and invoice", "giao": "2-4 weeks after order placement",
           "dia_diem": "Delivered to customer's site (DAP)", "bao_hanh": "12 months from delivery"},
    "DA": {"ten": "Dự án (thiết kế – cung cấp – lắp đặt)", "hieu_luc": "45 days from quotation date",
           "tt": "40% deposit upon order, 50% upon delivery notification, 10% after commissioning and acceptance",
           "giao": "8-10 weeks after order placement", "dia_diem": "Installed at customer's site",
           "bao_hanh": "12 months from acceptance or 18 months from delivery, whichever comes first"},
    "DV": {"ten": "Dịch vụ vận hành / bảo trì", "hieu_luc": "30 days from quotation date",
           "tt": "Monthly, within 15 days after invoice", "giao": "As per service schedule",
           "dia_diem": "Customer's site", "bao_hanh": "Service quality guaranteed as per SLA"},
}


def mau_dieu_khoan_theo_ma(ma: str) -> str:
    loai = str(ma or "").strip().upper().split("-")[0]
    return loai if loai in MAU_DIEU_KHOAN else "TM"


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
    if k["ngoai_chua_uoc"]:
        ten = ", ".join(x[:40] for x in k["ngoai_chua_uoc"][:3]) + ("…" if len(k["ngoai_chua_uoc"]) > 3 else "")
        msg = f"➕ {len(k['ngoai_chua_uoc'])} dòng NGOÀI DỰ TOÁN chưa có chi phí dự kiến ({ten}) — nhập giá vốn ước để tính biên."
        if not la_ceo(nd):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, msg + " CEO được vượt.")
        van_de.append(msg)
    if kiem_bien and k["canh_bao_bien"]:
        if not la_ceo(nd):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"📉 {k['canh_bao_bien']} — chỉ CEO duyệt được báo giá này.")
        van_de.append("📉 " + k["canh_bao_bien"])
    if van_de and not xac_nhan:
        raise HTTPException(status.HTTP_409_CONFLICT, " ".join(van_de))
    k["vuot"] = van_de
    return k
