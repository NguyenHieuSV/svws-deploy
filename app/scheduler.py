"""Bộ hẹn giờ chạy nền — hiện chỉ phục vụ bản tin nhắc việc đầu ngày.

Chạy trong CHÍNH tiến trình web (một luồng nền), không cần thuê thêm dịch vụ.
An toàn khi khởi động lại vì mốc "đã gửi hôm nay" nằm trong CSDL
(bảng nhac_viec_ban_tin), không nằm trong bộ nhớ.
"""
import threading
import time
from datetime import datetime  # noqa: F401 (giữ cho tương thích)

from .config import settings
from .database import SessionLocal

_CHU_KY = 300          # 5 phút quét một lần
_luong: threading.Thread | None = None
_GIO_LAI_LO = ""       # mốc giờ đã chốt Lãi/Lỗ Record gần nhất
_TUAN_BCVH = ""        # tuần đã gửi nhắc Báo cáo vận hành (thứ Bảy 14h)


def _vong_lap():
    while True:
        try:
            from .nhac_viec_service import gio_hien_tai, gui_ban_tin_ngay
            gio = settings.nhac_viec_gio_ban_tin
            # so theo GIỜ VIỆT NAM, không phải giờ máy chủ (Render chạy UTC)
            if settings.nhac_viec_ban_tin and gio_hien_tai().hour == gio:
                db = SessionLocal()
                try:
                    kq = gui_ban_tin_ngay(db)
                    if kq.get("da_gui"):
                        print(f"[SCHEDULER] Bản tin nhắc việc: {kq}")
                finally:
                    db.close()
            # 📈 Lãi/Lỗ Record: chốt mỗi giờ — bản ghi hôm nay luôn là số mới nhất,
            # nhờ đó ngày cuối tháng luôn có record chốt tháng dù không ai mở app.
            global _GIO_LAI_LO
            gio_nay = gio_hien_tai().strftime("%Y-%m-%d %H")
            if gio_nay != _GIO_LAI_LO:
                _GIO_LAI_LO = gio_nay
                db = SessionLocal()
                try:
                    from .routers.tai_chinh import luu_lai_lo_hom_nay
                    luu_lai_lo_hom_nay(db)
                    db.commit()
                finally:
                    db.close()
            # 📋 Nhắc Báo cáo vận hành thiếu dữ liệu: 14h THỨ BẢY hàng tuần → group Google Chat
            global _TUAN_BCVH
            g2 = gio_hien_tai()
            tuan_nay = g2.strftime("%G-W%V")
            if g2.weekday() == 5 and g2.hour == 14 and _TUAN_BCVH != tuan_nay:
                _TUAN_BCVH = tuan_nay
                db = SessionLocal()
                try:
                    from .routers.cho_thue_ops import gui_nhac_bcvh_tuan
                    kq2 = gui_nhac_bcvh_tuan(db)
                    print(f"[SCHEDULER] Nhắc BCVH tuần: {kq2}")
                finally:
                    db.close()
        except Exception as e:                     # không bao giờ để luồng nền chết
            print(f"[SCHEDULER] Lỗi bỏ qua: {type(e).__name__}: {e}")
        time.sleep(_CHU_KY)


def khoi_dong():
    """Gọi một lần lúc app khởi động."""
    global _luong
    if _luong is not None and _luong.is_alive():
        return
    _luong = threading.Thread(target=_vong_lap, name="svws-scheduler", daemon=True)
    _luong.start()
    print(f"[SCHEDULER] Đã bật — bản tin nhắc việc lúc {settings.nhac_viec_gio_ban_tin}h")
