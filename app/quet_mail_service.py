"""📬 TỰ QUÉT THƯ HÀNG TUẦN — AI đọc hộp thư mua hàng theo lịch, 3 bước:
  1. hóa đơn mua từ email  → Kế toán › Hóa đơn chờ xác nhận
  2. báo giá / datasheet   → Nhà cung cấp › Báo giá chờ xác nhận
  3. bổ sung SPEC cho thư đã xác nhận (chỉ điền sản phẩm khớp; spec nhập tay không ghi đè)
KHÔNG tự xác nhận gì. Kiểu «ĐẾN HẠN THÌ CHẠY»: mốc hẹn = thứ + giờ (giờ VN); qua mốc mà tuần đó chưa chạy
(mốc lưu trong CSDL, không nằm trong bộ nhớ) → chạy ngay khi app thức. Bản tin gửi group Google Chat RIÊNG
(GCHAT_WEBHOOK_QUET_MAIL). Hóa đơn hóa chất bên Cho thuê KHÔNG gộp vào đây (luồng riêng)."""
import threading
from datetime import date, timedelta

from .config import settings
from .database import SessionLocal

THU = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
_khoa = threading.Lock()                       # một lần chạy tại một thời điểm (trong tiến trình này)
_TONG = ("them", "khong_doc", "dung_ai", "xu_ly", "so_spec")   # cộng dồn qua các vòng lặp; khóa khác lấy giá trị cuối


def cau_hinh(db):
    from .models import CauHinhQuetMail
    c = db.get(CauHinhQuetMail, 1)
    if c is None:
        c = CauHinhQuetMail(id=1)
        db.add(c)
        db.commit()
    return c


def moc_gan_nhat(c, bay_gio):
    """Mốc hẹn gần nhất ≤ bây giờ theo cấu hình (thứ + giờ)."""
    d = bay_gio.replace(minute=0, second=0, microsecond=0)
    lech = (d.weekday() - int(c.thu or 0)) % 7
    moc = (d - timedelta(days=lech)).replace(hour=int(c.gio or 0))
    if moc > bay_gio:
        moc -= timedelta(days=7)
    return moc


def lan_chay_cuoi(db):
    from .models import LichQuetMail
    return (db.query(LichQuetMail).filter(LichQuetMail.trang_thai.in_(["XONG", "LOI"]))
            .order_by(LichQuetMail.id.desc()).first())


def dang_chay(db):
    from .models import LichQuetMail
    from .nhac_viec_service import gio_hien_tai
    r = (db.query(LichQuetMail).filter(LichQuetMail.trang_thai == "DANG_CHAY")
         .order_by(LichQuetMail.id.desc()).first())
    return r is not None and (gio_hien_tai() - r.bat_dau) < timedelta(hours=2)


def den_han(db, bay_gio):
    """(đến hạn?, cấu hình, mốc gần nhất) — đến hạn khi bật, đã qua mốc gần nhất mà lần chạy cuối trước mốc đó."""
    c = cau_hinh(db)
    if not c.bat:
        return False, c, None
    moc = moc_gan_nhat(c, bay_gio)
    cuoi = lan_chay_cuoi(db)
    if cuoi is not None and cuoi.bat_dau >= moc:
        return False, c, moc
    if dang_chay(db):
        return False, c, moc
    return True, c, moc


def _nd_he_thong(db):
    """Tài khoản chạy thay khi theo lịch: ADMIN / CEO đang hoạt động (audit ghi rõ «theo lịch»)."""
    from .models import NguoiDung, VaiTro
    return (db.query(NguoiDung).join(VaiTro, NguoiDung.vai_tro_id == VaiTro.id)
            .filter(VaiTro.ma.in_(["ADMIN", "CEO"]), NguoiDung.trang_thai == "HOAT_DONG")
            .order_by(NguoiDung.id).first())


def _gop(tong: dict, k: dict):
    for kk, v in (k or {}).items():
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        tong[kk] = (tong.get(kk, 0) + v) if kk in _TONG else v


def chay(db, nguon="LICH", nd=None) -> dict:
    """Chạy đủ 3 bước, ghi nhật ký (lich_quet_mail), gửi bản tin group riêng. Trả ket_qua."""
    from fastapi import HTTPException
    from .models import LichQuetMail
    from .nhac_viec_service import gio_hien_tai
    c = cau_hinh(db)
    if nd is None:
        nd = _nd_he_thong(db)
    if nd is None:
        raise RuntimeError("Không có tài khoản ADMIN/CEO đang hoạt động để chạy thay")
    r = LichQuetMail(nguon=nguon, bat_dau=gio_hien_tai(), trang_thai="DANG_CHAY", nguoi_dung_id=nd.id)
    db.add(r)
    db.commit()
    rid = r.id
    tu = date.today() - timedelta(days=int(c.so_ngay or 8))
    kq = {"tu_ngay": str(tu), "nguon": nguon, "hoa_don": {}, "bao_gia": {}, "spec": {}, "loi": []}

    def _lap(ten, ham, toi_da):
        tong = {}
        for _ in range(toi_da):
            try:
                k = ham()
            except HTTPException as e:
                kq["loi"].append(f"{ten}: {e.detail}")
                db.rollback()
                break
            except Exception as e:
                kq["loi"].append(f"{ten}: {type(e).__name__}: {str(e)[:150]}")
                db.rollback()
                break
            _gop(tong, k)
            if not (k or {}).get("con_lai"):
                break
        return tong

    from .routers.ke_toan_quy import quet_hoa_don_mua_email
    kq["hoa_don"] = _lap("Hóa đơn", lambda: quet_hoa_don_mua_email(tu, db, nd), 3)
    from .routers.ncc import quet_bao_gia_email, bo_sung_spec_bao_gia_email
    kq["bao_gia"] = _lap("Báo giá", lambda: quet_bao_gia_email(tu, db, nd), 4)
    kq["spec"] = _lap("Spec", lambda: bo_sung_spec_bao_gia_email(db, nd), 3)
    try:
        from .models import KtHoaDonCho, BgEmailCho
        kq["cho"] = {"hoa_don": db.query(KtHoaDonCho).filter_by(trang_thai="CHO_XAC_NHAN").count(),
                     "bao_gia": db.query(BgEmailCho).filter_by(trang_thai="CHO_XAC_NHAN").count()}
    except Exception:
        kq["cho"] = {}
    kq["gui_chat"] = gui_ban_tin(kq)
    r = db.get(LichQuetMail, rid)
    r.ket_thuc = gio_hien_tai()
    r.trang_thai = "LOI" if (kq["loi"] and not kq["hoa_don"] and not kq["bao_gia"]) else "XONG"
    r.ket_qua = kq
    db.commit()
    return kq


def gui_ban_tin(kq: dict) -> dict:
    url = (settings.gchat_webhook_quet_mail or "").strip()
    if not url:
        return {"da_gui": False, "ly_do": "Chưa cấu hình GCHAT_WEBHOOK_QUET_MAIL (group riêng)"}
    from .chat_gateway import gui_webhook_rieng
    hd, bg, sp, cho = kq.get("hoa_don") or {}, kq.get("bao_gia") or {}, kq.get("spec") or {}, kq.get("cho") or {}
    text = ("📬 *TỰ QUÉT THƯ HÀNG TUẦN* — " + ("theo lịch" if kq.get("nguon") == "LICH" else "chạy tay")
            + f" · thư từ {kq.get('tu_ngay')}\n"
            f"• 🧾 Hóa đơn mua: {hd.get('them', 0)} thư mới → Kế toán › Hóa đơn chờ (đang chờ: {cho.get('hoa_don', '?')})\n"
            f"• 💰 Báo giá / datasheet: {bg.get('them', 0)} thư mới → Nhà cung cấp › Báo giá chờ (đang chờ: {cho.get('bao_gia', '?')})\n"
            f"• 🔧 Spec: đọc lại {sp.get('xu_ly', 0)} thư đã xác nhận, điền spec {sp.get('so_spec', 0)} sản phẩm\n"
            + ("• ⚠ Lỗi: " + " | ".join(kq.get("loi") or [])[:400] + "\n" if kq.get("loi") else "")
            + "→ Vào app xác nhận từng thư — AI không tự ghi gì khi chưa xác nhận.")
    try:
        return gui_webhook_rieng(url, text)
    except Exception as e:
        return {"da_gui": False, "ly_do": str(e)[:150]}


def chay_nen(nguon="TAY", nd_id=None) -> bool:
    """Chạy trong luồng nền (quét + AI mất vài phút — không giữ HTTP). False nếu đang có lần chạy khác."""
    if not _khoa.acquire(blocking=False):
        return False

    def _w():
        db = SessionLocal()
        try:
            from .models import NguoiDung
            nd = db.get(NguoiDung, nd_id) if nd_id else None
            kq = chay(db, nguon, nd)
            print(f"[QUET_MAIL] xong ({nguon}): hoa_don={kq.get('hoa_don')} bao_gia={kq.get('bao_gia')} "
                  f"spec={kq.get('spec')} loi={kq.get('loi')}")
        except Exception as e:
            print(f"[QUET_MAIL] lỗi: {type(e).__name__}: {e}")
            try:
                db.rollback()
                from .models import LichQuetMail
                from .nhac_viec_service import gio_hien_tai
                r = (db.query(LichQuetMail).filter_by(trang_thai="DANG_CHAY")
                     .order_by(LichQuetMail.id.desc()).first())
                if r is not None:
                    r.trang_thai = "LOI"
                    r.ket_thuc = gio_hien_tai()
                    r.ket_qua = {"loi": [f"{type(e).__name__}: {str(e)[:200]}"], "nguon": nguon}
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()
            _khoa.release()

    threading.Thread(target=_w, name="svws-quet-mail", daemon=True).start()
    return True
