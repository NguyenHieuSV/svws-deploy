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
import re
import unicodedata
from datetime import date, timedelta, timezone
from decimal import Decimal
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .models import (HangHoa, DonHang, DonMua, DonMuaCt, YeuCauMua,
                     DuToanBan, DuToanBanMuc, DuAn, DuAnDuToan)

DUNG_SAI = 0.10          # 10% — cùng mức với định mức tiêu hao tháng (CEO chốt)
NGUONG_MIEN = 5_000_000  # lũy kế mua dưới mã < 5 triệu (chưa VAT) → chưa cần dự toán (CEO chốt 18/09/2026)
LOAI_BAT_BUOC = ("TM", "DA", "DV")
NGAY_AP_DUNG = date(2026, 9, 18)   # chỉ mã ĐẶT RA SAU ngày này mới bắt buộc dự toán (CEO chốt 18/09/2026)


def _f(v) -> float:
    return float(v or 0)


_RE_SO = re.compile(r"\d+(?:[.,]\d+)?")


def khoa_ma(ma):
    """Khóa so khớp mã KHÔNG phụ thuộc thứ tự: DV-COH-NT-0826-EDI và DV-COH-NT-EDI-0826 cùng một dự án → cùng khóa.
    (Dự toán hàng bán, BOQ dự án và PO thường bị gõ lệch thứ tự phần hạng mục / tháng.)"""
    s = unicodedata.normalize("NFD", str(ma or "").replace("Đ", "D").replace("đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    toks = [t for t in re.split(r"[^A-Za-z0-9]+", s.upper()) if t]
    return tuple(sorted(toks)) or None


def cung_ma(a, b) -> bool:
    """Hai mã là MỘT: trùng từng ký tự (bỏ hoa thường / khoảng trắng) hoặc cùng bộ thành phần khác thứ tự."""
    a0, b0 = str(a or "").strip().lower(), str(b or "").strip().lower()
    if not a0 or not b0:
        return False
    if a0 == b0:
        return True
    ka, kb = khoa_ma(a), khoa_ma(b)
    return bool(ka and ka == kb)


def tim_dtb_theo_ma(db: Session, ma: str) -> list:
    """Các Dự toán hàng bán thuộc mã (trùng hẳn trước, rồi mã khác thứ tự)."""
    ds = [d for d in db.query(DuToanBan).all() if cung_ma(d.ma, ma)]
    ds.sort(key=lambda d: (0 if str(d.ma or "").strip().lower() == str(ma or "").strip().lower() else 1, d.id))
    return ds


def tim_da_theo_ma(db: Session, ma: str) -> list:
    """Các dự án (BOQ) thuộc mã (trùng hẳn trước, rồi mã khác thứ tự)."""
    ds = [d for d in db.query(DuAn).filter(DuAn.ma.isnot(None)).all() if cung_ma(d.ma, ma)]
    ds.sort(key=lambda d: (0 if str(d.ma or "").strip().lower() == str(ma or "").strip().lower() else 1, d.id))
    return ds


def gan_giong_nhat(ten: str, dt: dict):
    """Dòng dự toán có tên GIỐNG NHẤT với `ten` (≥ 60 %, chưa đủ để coi là cùng mặt hàng) → (tên dòng, điểm) hoặc None.
    Chỉ dùng để GỢI Ý cho người lập PO khi mặt hàng vẫn bị coi là ngoài dự toán."""
    if not ten or not dt:
        return None
    from .gia_dau_vao import diem_giong
    best, bd = None, 0.0
    for b in dt.values():
        for t2 in (b.get("ten") or []):
            d = diem_giong(ten, t2)
            if d > bd:
                best, bd = t2, d
    return (best, round(bd, 2)) if best and bd >= 0.6 else None


def quy_map(db: Session, dt: dict, hids) -> dict:
    """{hang_hoa_id → hang_hoa_id của dòng dự toán GẦN GIỐNG} cho mặt hàng chưa có trong dự toán: cùng bộ số
    (kích thước · model) và tên giống ≥ 88 % (không phân biệt dấu / hoa thường / khoảng trắng). Chặt có chủ đích:
    «Cát» ≠ «Cát đen», «Co 90» ≠ «Co 60» — giống chút ít vẫn là hàng ngoài dự toán."""
    out = {}
    if not dt:
        return out
    cand = [h for h in set(hids or []) if h and h not in dt]
    if not cand:
        return out
    from .gia_dau_vao import diem_giong, _chuan
    ten = _ten_map(db, cand)
    for h in cand:
        t = ten.get(h) or ""
        if not t:
            continue
        nt = sorted(_RE_SO.findall(_chuan(t)))
        best, bd = None, 0.0
        for h2, b in dt.items():
            for t2 in (b.get("ten") or []):
                if sorted(_RE_SO.findall(_chuan(t2))) != nt:
                    continue
                d = diem_giong(t, t2)
                if d >= 0.88 and d > bd:
                    best, bd = h2, d
        if best is not None:
            out[h] = best
    return out


def _ten_map(db, ids):
    ids = [i for i in set(ids) if i]
    if not ids:
        return {}
    return {i: t for (i, t) in db.query(HangHoa.id, HangHoa.ten).filter(HangHoa.id.in_(ids)).all()}


def du_toan_cua_ma(db: Session, ma: str):
    """{hang_hoa_id: {"sl", "tien", "ten": [tên dòng dự toán / tên kho]}} gộp Dự toán hàng bán + BOQ dự án CÙNG MÃ
    (kể cả mã viết khác thứ tự); None nếu mã chưa có dự toán."""
    ma = str(ma or "").strip().lower()
    if not ma:
        return None
    out, co = {}, False
    for d in tim_dtb_theo_ma(db, ma):
        co = True
        for m in db.query(DuToanBanMuc).filter_by(du_toan_id=d.id).all():
            hid = m.hang_hoa_id
            if not hid:
                h = db.query(HangHoa).filter(func.lower(func.trim(HangHoa.ten)) == str(m.ten or "").strip().lower()).first()
                hid = h.id if h else None
            if not hid:
                continue
            o = out.setdefault(hid, {"sl": 0.0, "tien": 0.0, "ten": []})
            o["sl"] += _f(m.so_luong)
            o["tien"] += _f(m.so_luong) * _f(m.don_gia)
            if m.ten:
                o["ten"].append(m.ten)
    for da in tim_da_theo_ma(db, ma):
        co = True
        for x in db.query(DuAnDuToan).filter_by(du_an_id=da.id).all():
            hid = getattr(x, "hang_hoa_id", None)
            if not hid:
                h = db.query(HangHoa).filter(func.lower(func.trim(HangHoa.ten)) == str(x.ten or "").strip().lower()).first()
                hid = h.id if h else None
            if not hid:
                continue
            o = out.setdefault(hid, {"sl": 0.0, "tien": 0.0, "ten": []})
            o["sl"] += _f(x.so_luong)
            o["tien"] += _f(x.so_luong) * _f(x.don_gia)
            if x.ten:
                o["ten"].append(x.ten)
    if out:
        for hid, ten in _ten_map(db, list(out.keys())).items():
            if ten and ten not in out[hid]["ten"]:
                out[hid]["ten"].append(ten)
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
    """{hang_hoa_id: {"sl","tien"}} đã CAM KẾT dưới mã: dòng PO không bị từ chối (kể cả PO chờ duyệt), tính cả PO mang mã
    viết khác thứ tự. Bỏ qua chính PO đang xét (bo_qua_dm); bo_qua_ycm giữ cho tương thích — bước đề xuất đã bỏ 10/10/2026."""
    ma = str(ma or "").strip().lower()
    dh_ids = [d.id for d in db.query(DonHang).filter(DonHang.so.isnot(None)).all() if cung_ma(d.so, ma)]
    out = {}

    def cong(hid, sl, tien):
        o = out.setdefault(hid, {"sl": 0.0, "tien": 0.0})
        o["sl"] += sl
        o["tien"] += tien

    dk = DonMua.ma_ban.isnot(None)
    if dh_ids:
        dk = or_(dk, DonMua.don_hang_id.in_(dh_ids))
    q = (db.query(DonMuaCt, DonMua).join(DonMua, DonMuaCt.don_mua_id == DonMua.id)
         .filter(dk, DonMua.trang_thai != "TU_CHOI"))
    if bo_qua_dm:
        q = q.filter(DonMua.id != bo_qua_dm)
    for ct, dm in q.all():
        if (dm.ma_ban and cung_ma(dm.ma_ban, ma)) or (dm.don_hang_id and dm.don_hang_id in dh_ids):
            cong(ct.hang_hoa_id, _f(ct.so_luong), _f(ct.so_luong) * _f(ct.don_gia))
    return out


def kiem_tra(db: Session, ma: str, lines, bo_qua_ycm=None, bo_qua_dm=None):
    """lines = [(hang_hoa_id, so_luong, don_gia)] → (vi_pham: list, mo_ta: str | None).
    vi_pham: {hang_hoa_id, ten, loai: VUOT | NGOAI, du_toan_tien, du_toan_sl, da_dung_tien, them_tien, vuot_pct}
    Mặt hàng chưa có trong dự toán nhưng TÊN GẦN GIỐNG một dòng dự toán (cùng bộ số) được tính chung vào dòng đó."""
    dt = du_toan_cua_ma(db, ma)
    if dt is None:
        return [], None
    them_raw = {}
    for hid, sl, dg in lines:
        if not hid:
            continue
        o = them_raw.setdefault(hid, {"sl": 0.0, "tien": 0.0})
        o["sl"] += _f(sl)
        o["tien"] += _f(sl) * _f(dg)
    if not them_raw:
        return [], None
    dung_raw = da_dung_theo_ma(db, ma, bo_qua_ycm, bo_qua_dm)
    al = quy_map(db, dt, list(them_raw.keys()) + list(dung_raw.keys()))
    them, dung = {}, {}
    for hid, o in them_raw.items():
        t = them.setdefault(al.get(hid, hid), {"sl": 0.0, "tien": 0.0, "hid": hid})
        t["sl"] += o["sl"]
        t["tien"] += o["tien"]
    for hid, o in dung_raw.items():
        d0 = dung.setdefault(al.get(hid, hid), {"sl": 0.0, "tien": 0.0})
        d0["sl"] += o["sl"]
        d0["tien"] += o["tien"]
    ten = _ten_map(db, [t["hid"] for t in them.values()])
    vp = []
    for kk, t in them.items():
        hid = t["hid"]
        b = dt.get(kk)
        d = dung.get(kk, {"sl": 0.0, "tien": 0.0})
        if b is None:
            gg = gan_giong_nhat(ten.get(hid, ""), dt)
            vp.append({"hang_hoa_id": hid, "ten": ten.get(hid, f"HH#{hid}"), "loai": "NGOAI",
                       "du_toan_tien": 0.0, "du_toan_sl": 0.0, "da_dung_tien": d["tien"],
                       "them_tien": t["tien"], "vuot_pct": None,
                       "gan_giong": gg[0] if gg else None})
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
            gg = f" · gần giống dòng «{v['gan_giong']}» trong dự toán, nếu cùng mặt hàng thì nối đúng mặt hàng kho" if v.get("gan_giong") else ""
            phan.append(f"{v['ten']}: NGOÀI dự toán (+{v['them_tien']:,.0f}đ){gg}")
        elif v["du_toan_tien"] > 0:
            phan.append(f"{v['ten']}: dự toán {v['du_toan_tien']:,.0f}đ, đã dùng {v['da_dung_tien']:,.0f}đ, "
                        f"thêm {v['them_tien']:,.0f}đ → vượt {v['vuot_pct']:+.1f}%")
        else:
            phan.append(f"{v['ten']}: dự toán {v['du_toan_sl']:g} (chưa có giá), vượt SL {v['vuot_pct']:+.1f}%")
    if len(vp) > 6:
        phan.append(f"… và {len(vp) - 6} mặt hàng khác")
    mo_ta = (f"⛔ VƯỢT DỰ TOÁN {str(ma).upper()} (dung sai {int(DUNG_SAI * 100)}%): " + " | ".join(phan))
    return vp, mo_ta
