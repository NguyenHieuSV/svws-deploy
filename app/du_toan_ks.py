"""
KIỂM SOÁT ĐỀ XUẤT / PO THEO DỰ TOÁN — quyết định CEO 13/09/2026: "CHẶN và CHỜ DUYỆT".

Mã có dự toán (Dự toán hàng bán và/hoặc BOQ dự án cùng mã) thì mỗi mặt hàng được mua tối đa
= dự toán dòng × (1 + DUNG_SAI). Vượt mức, hoặc mặt hàng KHÔNG có trong dự toán:
  • lúc lập đề xuất / PO: chặn (409) — người lập phải xác nhận có chủ đích (xac_nhan_du_toan)
  • sau xác nhận: bản ghi mang cờ vuot_du_toan (lý do) và CHỈ CEO/ADMIN mới duyệt được.
Mã CHƯA có dự toán nào (CEO chốt 18/09/2026 — "mức 2"): mã loại TM · DA · DV bắt buộc có dự toán.
Chưa có → chặn lúc lập, xác nhận có chủ đích → cờ vuot_du_toan ("⛔ MÃ CHƯA CÓ DỰ TOÁN…") → chỉ CEO/ADMIN duyệt.
MIỄN: mã OP (định mức tháng) · KHO / không mã (mua dự trữ) · mặt hàng đã khai định mức tiêu hao tháng (cho thuê)
· LŨY KẾ mua dưới mã (đã cam kết + lần này) < NGUONG_MIEN
· MÃ ĐẶT RA TỪ NGAY_AP_DUNG TRỞ VỀ TRƯỚC (CEO 18/09/2026: trước mắt chỉ áp dụng cho mã hàng bán đặt ra SAU hôm nay —
  mã cũ đang chạy không phải lập dự toán bù).
"""
from datetime import date, timedelta, timezone
from decimal import Decimal
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .models import (HangHoa, DonHang, DonMua, DonMuaCt, YeuCauMua, YeuCauMuaCt,
                     DuToanBan, DuToanBanMuc, DuAn, DuAnDuToan)

DUNG_SAI = 0.10          # 10% — cùng mức với định mức tiêu hao tháng (CEO chốt)
NGUONG_MIEN = 5_000_000  # lũy kế mua dưới mã < 5 triệu (chưa VAT) → chưa cần dự toán (CEO chốt 18/09/2026)
LOAI_BAT_BUOC = ("TM", "DA", "DV")
NGAY_AP_DUNG = date(2026, 9, 18)   # chỉ mã ĐẶT RA SAU ngày này mới bắt buộc dự toán (CEO chốt 18/09/2026)


def _f(v) -> float:
    return float(v or 0)


def _ten_map(db, ids):
    ids = [i for i in set(ids) if i]
    if not ids:
        return {}
    return {i: t for (i, t) in db.query(HangHoa.id, HangHoa.ten).filter(HangHoa.id.in_(ids)).all()}


def du_toan_cua_ma(db: Session, ma: str):
    """{hang_hoa_id: {"sl", "tien"}} gộp Dự toán hàng bán + BOQ dự án cùng mã; None nếu mã chưa có dự toán."""
    ma = str(ma or "").strip().lower()
    if not ma:
        return None
    out, co = {}, False
    for d in db.query(DuToanBan).filter(func.lower(func.trim(DuToanBan.ma)) == ma).all():
        co = True
        for m in db.query(DuToanBanMuc).filter_by(du_toan_id=d.id).all():
            hid = m.hang_hoa_id
            if not hid:
                h = db.query(HangHoa).filter(func.lower(func.trim(HangHoa.ten)) == str(m.ten or "").strip().lower()).first()
                hid = h.id if h else None
            if not hid:
                continue
            o = out.setdefault(hid, {"sl": 0.0, "tien": 0.0})
            o["sl"] += _f(m.so_luong)
            o["tien"] += _f(m.so_luong) * _f(m.don_gia)
    for da in db.query(DuAn).filter(func.lower(func.trim(DuAn.ma)) == ma).all():
        co = True
        for x in db.query(DuAnDuToan).filter_by(du_an_id=da.id).all():
            hid = getattr(x, "hang_hoa_id", None)
            if not hid:
                h = db.query(HangHoa).filter(func.lower(func.trim(HangHoa.ten)) == str(x.ten or "").strip().lower()).first()
                hid = h.id if h else None
            if not hid:
                continue
            o = out.setdefault(hid, {"sl": 0.0, "tien": 0.0})
            o["sl"] += _f(x.so_luong)
            o["tien"] += _f(x.so_luong) * _f(x.don_gia)
    return out if co else None


def co_du_toan(db: Session, ma: str) -> bool:
    """Mã đã có dự toán chưa: trùng mã, hoặc CÙNG NHÓM gốc + tháng (dự toán lập ở mã gốc TM-X-0926,
    PO tách -01/-02 vẫn tính là có dự toán)."""
    if du_toan_cua_ma(db, ma) is not None:
        return True
    from .ma_code import nhom
    g = nhom(ma)
    if not g:
        return False
    for (m,) in db.query(DuToanBan.ma).all():
        if m and nhom(m) == g:
            return True
    for (m,) in db.query(DuAn.ma).all():
        if m and nhom(m) == g:
            return True
    return False


def ma_dat_truoc(db: Session, ma: str) -> bool:
    """Mã (hoặc NHÓM gốc + tháng của nó) đã được đặt ra từ NGAY_AP_DUNG trở về trước? → miễn bắt buộc dự toán.
    Dấu vết: tháng trong mã < tháng áp dụng · đơn bán · PO / đề xuất / công nợ ngoài mang mã · dự án · tài sản cho thuê."""
    from .ma_code import phan_tich, nhom
    from .models import AuditLog, CongNo, TaiSanChoThue
    ma = str(ma or "").strip()
    if not ma:
        return True
    p = phan_tich(ma)
    th, nam = p.get("thang"), p.get("nam")
    try:
        if th and (2000 + int(th[2:]), int(th[:2])) < (NGAY_AP_DUNG.year, NGAY_AP_DUNG.month):
            return True                                   # TM-X-0826…: mã của tháng trước
        if nam and int(nam) < NGAY_AP_DUNG.year:
            return True                                   # mã mẹ cho thuê DV-X-2024
    except (TypeError, ValueError):
        pass
    ml, g = ma.lower(), nhom(ma)

    def trung(m):
        m = str(m or "").strip()
        return bool(m) and (m.lower() == ml or (g is not None and nhom(m) == g))

    nguon = (
        db.query(DonHang.so).filter(DonHang.so.isnot(None), DonHang.ngay <= NGAY_AP_DUNG),
        db.query(DonMua.ma_ban).filter(DonMua.ma_ban.isnot(None), DonMua.ngay <= NGAY_AP_DUNG),
        db.query(YeuCauMua.ma_ban).filter(YeuCauMua.ma_ban.isnot(None), YeuCauMua.ngay <= NGAY_AP_DUNG),
        db.query(YeuCauMua.cho_thue_ma).filter(YeuCauMua.cho_thue_ma.isnot(None), YeuCauMua.ngay <= NGAY_AP_DUNG),
        db.query(CongNo.ma_ban_ngoai).filter(CongNo.ma_ban_ngoai.isnot(None), CongNo.ngay_ct <= NGAY_AP_DUNG),
    )
    for q in nguon:
        for (m,) in q.distinct().all():
            if trung(m):
                return True
    gio_vn = timezone(timedelta(hours=7))
    for (m, c) in db.query(TaiSanChoThue.ma, TaiSanChoThue.created_at).all():
        if trung(m) and (c is None or c.astimezone(gio_vn).date() <= NGAY_AP_DUNG):
            return True
    for (i, m) in db.query(DuAn.id, DuAn.ma).filter(DuAn.ma.isnot(None)).all():
        if not trung(m):
            continue
        t = (db.query(func.min(AuditLog.thoi_gian))
             .filter(AuditLog.bang == "du_an", AuditLog.hanh_dong == "TAO", AuditLog.ban_ghi_id == i).scalar())
        if t is None or t.astimezone(gio_vn).date() <= NGAY_AP_DUNG:   # không có vết tạo = dữ liệu nạp từ trước
            return True
    return False


def trang_thai_ma(db: Session, ma: str) -> dict:
    """Tra cứu (chỉ đọc): mã này có BẮT BUỘC dự toán không, vì sao miễn, đã mua lũy kế bao nhiêu."""
    from .ma_code import phan_tich
    ma = str(ma or "").strip()
    loai = (phan_tich(ma).get("loai") or "").upper() if ma else ""
    mien = None
    if not ma:
        mien = "không mã — mua dự trữ KHO"
    elif loai not in LOAI_BAT_BUOC:
        mien = f"mã loại {loai or 'khác'} — không thuộc TM · DA · DV"
    elif co_du_toan(db, ma):
        mien = "mã đã có dự toán — kiểm soát theo dự toán (vượt / ngoài dự toán)"
    elif ma_dat_truoc(db, ma):
        mien = f"mã đặt ra từ {NGAY_AP_DUNG:%d/%m/%Y} trở về trước — chưa áp dụng"
    da = sum(v["tien"] for v in da_dung_theo_ma(db, ma).values()) if ma else 0.0
    return {"ma": ma, "loai": loai or None, "bat_buoc": mien is None, "ly_do_mien": mien,
            "da_mua_luy_ke": da, "nguong_mien": NGUONG_MIEN, "ngay_ap_dung": str(NGAY_AP_DUNG)}


def thieu_du_toan(db: Session, ma: str, lines, mien_hh=None, bo_qua_ycm=None, bo_qua_dm=None):
    """Mã TM · DA · DV CHƯA có dự toán → mô tả vi phạm (str); được miễn → None.
    lines = [(hang_hoa_id, so_luong, don_gia)]; mien_hh = các mặt hàng đã khai định mức tháng (miễn)."""
    ma = str(ma or "").strip()
    if not ma:
        return None
    from .ma_code import phan_tich
    loai = (phan_tich(ma).get("loai") or "").upper()
    if loai not in LOAI_BAT_BUOC:
        return None
    if co_du_toan(db, ma):
        return None
    if ma_dat_truoc(db, ma):
        return None                                   # mã cũ (đặt ra ≤ NGAY_AP_DUNG) — chưa áp dụng
    mien = set(mien_hh or [])
    them = sum(_f(sl) * _f(dg) for (hid, sl, dg) in lines if hid and hid not in mien)
    if not any(hid and hid not in mien for (hid, _sl, _dg) in lines):
        return None                                   # mọi dòng đều đã có định mức tháng
    da = sum(v["tien"] for hid, v in da_dung_theo_ma(db, ma, bo_qua_ycm, bo_qua_dm).items() if hid not in mien)
    if da + them < NGUONG_MIEN:
        return None
    return (f"⛔ MÃ CHƯA CÓ DỰ TOÁN: {ma.upper()} (loại {loai}) chưa có Dự toán hàng bán / BOQ dự án — "
            f"lần này {them:,.0f}đ + đã mua dưới mã {da:,.0f}đ = {da + them:,.0f}đ ≥ ngưỡng miễn "
            f"{NGUONG_MIEN:,.0f}đ. Lập dự toán trước (Bán hàng → Báo giá → 🧾 Dự toán, hoặc BOQ dự án) rồi đề xuất từ đó")


def da_dung_theo_ma(db: Session, ma: str, bo_qua_ycm=None, bo_qua_dm=None):
    """{hang_hoa_id: {"sl","tien"}} đã CAM KẾT dưới mã: dòng PO (không từ chối) + dòng đề xuất
    còn hiệu lực chưa thành PO. Bỏ qua chính đề xuất / PO đang xét."""
    ma = str(ma or "").strip().lower()
    dh_ids = [i for (i,) in db.query(DonHang.id).filter(func.lower(func.trim(DonHang.so)) == ma).all()]
    out = {}

    def cong(hid, sl, tien):
        o = out.setdefault(hid, {"sl": 0.0, "tien": 0.0})
        o["sl"] += sl
        o["tien"] += tien

    dk_po = func.lower(func.trim(DonMua.ma_ban)) == ma
    if dh_ids:
        dk_po = or_(dk_po, DonMua.don_hang_id.in_(dh_ids))
    q = (db.query(DonMuaCt, DonMua).join(DonMua, DonMuaCt.don_mua_id == DonMua.id)
         .filter(dk_po, DonMua.trang_thai != "TU_CHOI"))
    if bo_qua_dm:
        q = q.filter(DonMua.id != bo_qua_dm)
    for ct, dm in q.all():
        cong(ct.hang_hoa_id, _f(ct.so_luong), _f(ct.so_luong) * _f(ct.don_gia))
    dk_y = or_(func.lower(func.trim(YeuCauMua.ma_ban)) == ma,
               func.lower(func.trim(YeuCauMua.cho_thue_ma)) == ma)
    if dh_ids:
        dk_y = or_(dk_y, YeuCauMua.don_hang_id.in_(dh_ids))
    qy = (db.query(YeuCauMua).filter(dk_y, YeuCauMua.don_mua_id.is_(None),
                                     YeuCauMua.trang_thai.in_(["MOI", "CHO_DUYET", "DA_DUYET"])))
    if bo_qua_ycm:
        qy = qy.filter(YeuCauMua.id != bo_qua_ycm)
    for y in qy.all():
        cts = db.query(YeuCauMuaCt).filter_by(yeu_cau_mua_id=y.id).all()
        if cts:
            for c in cts:
                cong(c.hang_hoa_id, _f(c.so_luong), _f(c.so_luong) * _f(c.don_gia))
        else:
            cong(y.hang_hoa_id, _f(y.so_luong), _f(y.so_luong) * _f(y.don_gia))
    return out


def kiem_tra(db: Session, ma: str, lines, bo_qua_ycm=None, bo_qua_dm=None):
    """lines = [(hang_hoa_id, so_luong, don_gia)] → (vi_pham: list, mo_ta: str | None).
    vi_pham: {hang_hoa_id, ten, loai: VUOT | NGOAI, du_toan_tien, du_toan_sl, da_dung_tien, them_tien, vuot_pct}"""
    dt = du_toan_cua_ma(db, ma)
    if dt is None:
        return [], None
    them = {}
    for hid, sl, dg in lines:
        if not hid:
            continue
        o = them.setdefault(hid, {"sl": 0.0, "tien": 0.0})
        o["sl"] += _f(sl)
        o["tien"] += _f(sl) * _f(dg)
    if not them:
        return [], None
    dung = da_dung_theo_ma(db, ma, bo_qua_ycm, bo_qua_dm)
    ten = _ten_map(db, list(them.keys()))
    vp = []
    for hid, t in them.items():
        b = dt.get(hid)
        d = dung.get(hid, {"sl": 0.0, "tien": 0.0})
        if b is None:
            vp.append({"hang_hoa_id": hid, "ten": ten.get(hid, f"HH#{hid}"), "loai": "NGOAI",
                       "du_toan_tien": 0.0, "du_toan_sl": 0.0, "da_dung_tien": d["tien"],
                       "them_tien": t["tien"], "vuot_pct": None})
            continue
        if b["tien"] > 0:
            tong, tran = d["tien"] + t["tien"], b["tien"] * (1 + DUNG_SAI)
            if tong > tran + 0.5:
                vp.append({"hang_hoa_id": hid, "ten": ten.get(hid, f"HH#{hid}"), "loai": "VUOT",
                           "du_toan_tien": b["tien"], "du_toan_sl": b["sl"], "da_dung_tien": d["tien"],
                           "them_tien": t["tien"], "vuot_pct": round((tong - b["tien"]) / b["tien"] * 100, 1)})
        elif b["sl"] > 0:
            tong, tran = d["sl"] + t["sl"], b["sl"] * (1 + DUNG_SAI)
            if tong > tran + 1e-9:
                vp.append({"hang_hoa_id": hid, "ten": ten.get(hid, f"HH#{hid}"), "loai": "VUOT",
                           "du_toan_tien": 0.0, "du_toan_sl": b["sl"], "da_dung_tien": d["tien"],
                           "them_tien": t["tien"], "vuot_pct": round((tong - b["sl"]) / b["sl"] * 100, 1)})
    if not vp:
        return [], None
    phan = []
    for v in vp[:6]:
        if v["loai"] == "NGOAI":
            phan.append(f"{v['ten']}: NGOÀI dự toán (+{v['them_tien']:,.0f}đ)")
        elif v["du_toan_tien"] > 0:
            phan.append(f"{v['ten']}: dự toán {v['du_toan_tien']:,.0f}đ, đã dùng {v['da_dung_tien']:,.0f}đ, "
                        f"thêm {v['them_tien']:,.0f}đ → vượt {v['vuot_pct']:+.1f}%")
        else:
            phan.append(f"{v['ten']}: dự toán {v['du_toan_sl']:g} (chưa có giá), vượt SL {v['vuot_pct']:+.1f}%")
    if len(vp) > 6:
        phan.append(f"… và {len(vp) - 6} mặt hàng khác")
    mo_ta = (f"⛔ VƯỢT DỰ TOÁN {str(ma).upper()} (dung sai {int(DUNG_SAI * 100)}%): " + " | ".join(phan))
    return vp, mo_ta
