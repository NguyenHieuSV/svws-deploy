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
_THANG_SAO_KE = ""     # tháng đã kiểm tra nhắc tải sao kê (ngày 7 hàng tháng)
_NGAY_NHAC_TRN = ""    # ngày đã chạy nhắc thi Training (8h–17h VN, trừ Chủ nhật)
_NGAY_NHAC_BC = ""     # ngày đã chạy nhắc «chưa hoàn thành báo cáo ngày» (sáng hôm sau, giờ VN)
_TUAN_LN = ""          # tuần đã gửi 📉 bản kiểm soát lợi nhuận theo mã (thứ Hai từ 8h VN; mốc bền nằm trong audit_log)


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
            # 🧾 Nhắc tải SAO KÊ tháng trước: từ ngày 7 hàng tháng (8h VN) chưa thấy sao kê → nhắc nhóm Duyệt chi NH
            #    (1 lần/tháng — mốc đã nhắc nằm trong CSDL; app ngủ qua ngày 7 thì lần thức đầu tiên sau đó nhắc bù)
            global _THANG_SAO_KE
            g3 = gio_hien_tai()
            thang3 = g3.strftime("%Y-%m")
            if g3.day >= 7 and g3.hour >= 8 and _THANG_SAO_KE != thang3:
                _THANG_SAO_KE = thang3
                db = SessionLocal()
                try:
                    from .routers.tai_chinh import nhac_sao_ke_thang
                    kq3 = nhac_sao_ke_thang(db)
                    print(f"[SCHEDULER] Nhắc sao kê tháng: {kq3.get('thang')} → {kq3.get('da_gui')} {kq3.get('ly_do') or kq3.get('loi') or ''}")
                finally:
                    db.close()
            # 🎓 Nhắc nhân viên chưa thi / chưa đạt các bài Training BẮT BUỘC: mỗi ngày 1 lần trong 8h–17h (VN), trừ Chủ nhật.
            #    Nhịp nhắc từng người nằm trong bảng trn_nhac (nên khởi động lại không nhắn trùng).
            global _NGAY_NHAC_TRN
            g4 = gio_hien_tai()
            ngay4 = g4.strftime("%Y-%m-%d")
            if 8 <= g4.hour <= 17 and g4.weekday() != 6 and _NGAY_NHAC_TRN != ngay4:
                _NGAY_NHAC_TRN = ngay4
                db = SessionLocal()
                try:
                    from .routers.dao_tao import nhac_tu_dong_hang_ngay
                    kq4 = nhac_tu_dong_hang_ngay(db)
                    if kq4.get("da_gui") or kq4.get("loi"):
                        print(f"[SCHEDULER] 🎓 Nhắc thi Training: {kq4}")
                finally:
                    db.close()
            # 📝 Nhắc người CHƯA HOÀN THÀNH BÁO CÁO NGÀY hôm qua: mỗi ngày 1 lần từ bao_cao_nhac_gio (giờ VN).
            #    Mỗi (ngày, người) chỉ nhắc một lần — mốc nằm trong bảng bao_cao_nhac nên khởi động lại không nhắn trùng.
            global _NGAY_NHAC_BC
            g5 = gio_hien_tai()
            ngay5 = g5.strftime("%Y-%m-%d")
            if g5.hour >= settings.bao_cao_nhac_gio and _NGAY_NHAC_BC != ngay5:
                _NGAY_NHAC_BC = ngay5
                db = SessionLocal()
                try:
                    from .bao_cao_ngay_service import nhac_tu_dong_hang_ngay as _nhac_bc
                    kq5 = _nhac_bc(db)
                    if kq5.get("da_gui") or kq5.get("loi"):
                        print(f"[SCHEDULER] 📝 Nhắc báo cáo ngày: {kq5}")
                finally:
                    db.close()
            # 📉 Bản KIỂM SOÁT LỢI NHUẬN THEO MÃ: thứ Hai từ 8h (VN) → nhóm Duyệt chi, mỗi tuần một lần.
            #    Đã gửi trong tuần (audit_log NHAC_TUAN) thì thôi — khởi động lại máy chủ không gửi trùng.
            global _TUAN_LN
            g6 = gio_hien_tai()
            tuan6 = g6.strftime("%G-W%V")
            if settings.ln_nhac_tuan and g6.weekday() == 0 and g6.hour >= 8 and _TUAN_LN != tuan6:
                _TUAN_LN = tuan6
                db = SessionLocal()
                try:
                    from datetime import timedelta as _td
                    from .models import AuditLog as _AL
                    dau_tuan = (g6 - _td(hours=settings.tz_offset_gio)).replace(hour=0, minute=0, second=0, microsecond=0) - _td(days=1)
                    da = (db.query(_AL.id).filter(_AL.bang == "kiem_soat_ln", _AL.hanh_dong == "NHAC_TUAN",
                                                  _AL.thoi_gian >= dau_tuan).first())
                    if da is None:
                        from .kiem_soat_ln import gui_tuan
                        from .audit import ghi_audit as _ga
                        kq6 = gui_tuan(db)
                        _ga(db, None, "NHAC_TUAN", "kiem_soat_ln", None, moi={k: v for k, v in kq6.items() if k != "loi"})
                        db.commit()
                        print(f"[SCHEDULER] 📉 Kiểm soát lợi nhuận tuần: {kq6}")
                finally:
                    db.close()
            # 📬 Tự quét thư hàng tuần — «đến hạn thì chạy»: mốc thứ+giờ (VN) lưu trong CSDL; app ngủ qua giờ hẹn
            # thì lần thức đầu tiên trong tuần chạy bù. Chạy ở luồng riêng (AI đọc thư mất vài phút).
            db = SessionLocal()
            try:
                from .quet_mail_service import den_han, chay_nen
                ok_qm, _c, _moc = den_han(db, gio_hien_tai())
            finally:
                db.close()
            if ok_qm:
                print("[SCHEDULER] 📬 Quét thư tuần: đến hạn → chạy")
                chay_nen("LICH")
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
