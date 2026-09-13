"""
KIỂM SOÁT ĐỀ XUẤT / PO THEO DỰ TOÁN — quyết định CEO 13/09/2026: "CHẶN và CHỜ DUYỆT".

Mã có dự toán (Dự toán hàng bán và/hoặc BOQ dự án cùng mã) thì mỗi mặt hàng được mua tối đa
= dự toán dòng × (1 + DUNG_SAI). Vượt mức, hoặc mặt hàng KHÔNG có trong dự toán:
  • lúc lập đề xuất / PO: chặn (409) — người lập phải xác nhận có chủ đích (xac_nhan_du_toan)
  • sau xác nhận: bản ghi mang cờ vuot_du_toan (lý do) và CHỈ CEO/ADMIN mới duyệt được.
Mã chưa có dự toán nào → không kiểm soát (không có gì để so).
"""
from decimal import Decimal
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .models import (HangHoa, DonHang, DonMua, DonMuaCt, YeuCauMua, YeuCauMuaCt,
                     DuToanBan, DuToanBanMuc, DuAn, DuAnDuToan)

DUNG_SAI = 0.10          # 10% — cùng mức với định mức tiêu hao tháng (CEO chốt)


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
