"""⭐ KPI lời nhắc việc (Work Reminder) — anh Hiếu 29/10/2026.

Mỗi lời nhắc được chấm theo hai vế, mỗi vế 50%:
• THỜI GIAN (tự động, 0–5): mốc = hạn hoàn thành (không đặt hạn → thời điểm nhắc).
  Xong đúng hạn / sớm 5 · trễ ≤ 4 giờ 4 · ≤ 24 giờ 3 · ≤ 72 giờ 2 · trễ hơn 1 · chưa xong mà đã quá hạn 0 (tạm) ·
  chưa đến hạn → chưa chấm.
• KẾT QUẢ (người đặt lời nhắc khi nhắc người khác, hoặc CEO/Admin chấm 1–5 sao sau khi việc đã XONG).
KPI % = thời gian/5 × 50 + kết quả/5 × 50. Chưa chấm kết quả → KPI tạm = theo thời gian (đánh dấu `tam`).
Việc HỦY không tính. Việc xong mà không ghi giờ xong (dữ liệu cũ) → chỉ chấm theo kết quả.
"""
from datetime import datetime

NGUONG_TRE = ((4, 4), (24, 3), (72, 2))      # (trễ tối đa X giờ → điểm)
NHAN_SAO = {1: "Không đạt", 2: "Yếu", 3: "Đạt", 4: "Tốt", 5: "Xuất sắc"}


def _gio_nhan(h: float) -> str:
    h = abs(float(h))
    if h < 1:
        return f"{int(round(h * 60))} phút"
    if h < 24:
        return f"{h:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " giờ"
    return f"{h / 24:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " ngày"


def diem_thoi_gian(xong_luc: datetime | None, moc: datetime, now: datetime):
    """→ (điểm 0–5 hoặc None nếu chưa chấm được, nhãn, số giờ trễ (âm = sớm))."""
    if xong_luc is not None:
        tre = (xong_luc - moc).total_seconds() / 3600
        if tre <= 0:
            return 5, ("đúng hạn" if tre > -1 else f"sớm {_gio_nhan(tre)}"), round(tre, 2)
        for toi_da, diem in NGUONG_TRE:
            if tre <= toi_da:
                return diem, f"trễ {_gio_nhan(tre)}", round(tre, 2)
        return 1, f"trễ {_gio_nhan(tre)}", round(tre, 2)
    if moc < now:
        tre = (now - moc).total_seconds() / 3600
        return 0, f"đang trễ {_gio_nhan(tre)}", round(tre, 2)
    return None, "chưa đến hạn", None


def tinh_kpi(r, now: datetime) -> dict:
    """KPI của một lời nhắc (ORM NhacViec hoặc đối tượng có cùng thuộc tính)."""
    tt = getattr(r, "trang_thai", None)
    if tt == "HUY":
        return {"tinh": False, "nhan": "hủy — không tính", "kpi": None}
    moc = getattr(r, "han_hoan_thanh", None) or getattr(r, "thoi_diem", None)
    if moc is None:
        return {"tinh": False, "nhan": "—", "kpi": None}
    kq = getattr(r, "ket_qua_diem", None)
    kq = int(kq) if kq else None
    xong = getattr(r, "xong_luc", None) if tt == "XONG" else None
    if tt == "XONG" and xong is None:                      # dữ liệu cũ: xong nhưng không ghi giờ
        tg, tg_nhan, tre = None, "xong — không ghi giờ", None
        kpi = round(kq / 5 * 100) if kq else None
    else:
        tg, tg_nhan, tre = diem_thoi_gian(xong, moc, now)
        kpi = None if tg is None else round(tg / 5 * 50 + ((kq / 5 * 50) if kq else (tg / 5 * 50)))
    return {"tinh": True, "tg_diem": tg, "tg_nhan": tg_nhan, "tre_gio": tre,
            "kq_diem": kq, "kq_nhan": NHAN_SAO.get(kq) if kq else None,
            "kpi": kpi, "tam": kq is None, "xong": tt == "XONG"}


def duoc_cham(r, me: int | None, la_qtv: bool) -> bool:
    """CEO/Admin chấm mọi việc; người đặt lời nhắc chấm việc mình nhắc NGƯỜI KHÁC (tự nhắc mình → chỉ CEO/Admin)."""
    if la_qtv:
        return True
    return me is not None and r.nguoi_tao == me and r.nhan_vien_id != me
