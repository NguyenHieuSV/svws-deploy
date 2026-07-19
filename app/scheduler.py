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
