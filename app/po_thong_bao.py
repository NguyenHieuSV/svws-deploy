"""🛒 Tin nhắn nhóm Google Chat «Purchasing Team» khi có ĐƠN MUA (PO) mới — anh Hiếu chốt 27/10/2026.

Nội dung: số PO · mã dự án (mã chuỗi / đơn bán / dự toán / BOQ) · nhà cung cấp · danh sách sản phẩm + số lượng.
Bắt MỌI đường tạo PO (lập tay, từ dự toán hàng bán / BOQ / cho thuê / kho, AI đọc báo giá…) bằng sự kiện phiên
SQLAlchemy: chỉ gửi SAU KHI COMMIT thành công, gửi ở luồng riêng để không làm chậm thao tác.
Webhook nhóm khai ở biến môi trường GCHAT_WEBHOOK_PURCHASING (Render); để trống = không gửi gì.
Mọi lỗi đều nuốt: nhắn hỏng không được làm hỏng việc lập PO.
"""
import threading

from sqlalchemy import event
from sqlalchemy.orm import Session

from .config import settings

_KHOA = "_po_moi_purchasing"
_TOI_DA_DONG = 15


def _url() -> str:
    return (settings.gchat_webhook_purchasing or "").strip()


def _so(v) -> str:
    try:
        f = float(v or 0)
    except (TypeError, ValueError):
        return str(v)
    return (f"{f:,.0f}" if f == int(f) else f"{f:,.2f}").replace(",", "X").replace(".", ",").replace("X", ".")


def noi_dung_po(db, po_id: int) -> str | None:
    """Soạn tin cho một PO (None nếu PO không còn). Chỉ đọc đúng các cột cần."""
    from .models import (DonHang, DonMua, DonMuaCt, DuAn, DuAnDuToan, DuToanBan, DuToanBanMuc, HangHoa,
                         NhaCungCap)
    dm = (db.query(DonMua.id, DonMua.so, DonMua.nha_cung_cap_id, DonMua.ma_ban, DonMua.don_hang_id,
                   DonMua.trang_thai, DonMua.ngay_hen_giao).filter(DonMua.id == po_id).first())
    if dm is None:
        return None
    ncc = db.query(NhaCungCap.ten).filter(NhaCungCap.id == dm.nha_cung_cap_id).scalar() if dm.nha_cung_cap_id else None
    dong = (db.query(HangHoa.ten, HangHoa.don_vi, DonMuaCt.so_luong)
            .join(HangHoa, HangHoa.id == DonMuaCt.hang_hoa_id)
            .filter(DonMuaCt.don_mua_id == po_id).order_by(DonMuaCt.id).all())
    # mã dự án: dự toán / BOQ nguồn của PO → mã chuỗi trên PO → số đơn bán gắn với PO
    ma_dt = sorted({m for (m,) in db.query(DuToanBan.ma).join(DuToanBanMuc, DuToanBanMuc.du_toan_id == DuToanBan.id)
                    .filter(DuToanBanMuc.don_mua_id == po_id).all() if m})
    ma_boq = sorted({m for (m,) in db.query(DuAn.ma).join(DuAnDuToan, DuAnDuToan.du_an_id == DuAn.id)
                     .filter(DuAnDuToan.don_mua_id == po_id).all() if m})
    so_dh = db.query(DonHang.so).filter(DonHang.id == dm.don_hang_id).scalar() if dm.don_hang_id else None
    ma_ds = ma_dt or ma_boq or [m for m in ((dm.ma_ban or "").strip(), (so_dh or "").strip()) if m][:1]
    if ma_dt:
        nguon = "lập từ Dự toán hàng bán"
    elif ma_boq:
        nguon = "lập từ BOQ dự án"
    else:
        nguon = "lập tay"
    nguoi = None
    try:
        from .models import AuditLog, NguoiDung, NhanVien
        nd_id = (db.query(AuditLog.nguoi_dung_id).filter(AuditLog.bang == "don_mua", AuditLog.ban_ghi_id == po_id)
                 .order_by(AuditLog.id).limit(1).scalar())
        if nd_id:
            nguoi = (db.query(NhanVien.ho_ten).filter(NhanVien.nguoi_dung_id == nd_id).limit(1).scalar()
                     or db.query(NguoiDung.email).filter(NguoiDung.id == nd_id).scalar())
    except Exception:                                                    # noqa: BLE001
        nguoi = None
    tt = {"CHO_DUYET": "Chờ duyệt", "DA_DUYET": "Đã duyệt", "TU_CHOI": "Từ chối", "NHAP": "Nháp"}.get(
        str(dm.trang_thai), str(dm.trang_thai or ""))
    l = [f"🛒 *ĐƠN MUA MỚI* {dm.so or ('PO #' + str(dm.id))} · {tt}",
         f"• Mã dự án: *{', '.join(ma_ds)}* ({nguon})" if ma_ds else f"• Mã dự án: — chưa gắn mã ({nguon})",
         f"• Nhà cung cấp: {ncc or '—'}"]
    l.append(f"• Sản phẩm ({len(dong)}):")
    for ten, dv, sl in dong[:_TOI_DA_DONG]:
        l.append(f"   – {ten} — {_so(sl)}{(' ' + dv) if dv else ''}")
    if len(dong) > _TOI_DA_DONG:
        l.append(f"   … và {len(dong) - _TOI_DA_DONG} mặt hàng khác")
    if dm.ngay_hen_giao:
        l.append(f"• Hẹn giao: {dm.ngay_hen_giao.strftime('%d/%m/%Y')}")
    if nguoi:
        l.append(f"• Người lập: {nguoi}")
    l.append("👉 App SVWS → Nhà cung cấp → Đơn mua (PO)")
    return "\n".join(l)


def gui_cac_po(ids) -> list:
    """Soạn + gửi tin cho từng PO (mở phiên riêng). Trả kết quả từng PO — dùng cho log / test."""
    from .chat_gateway import gui_webhook_rieng
    from .database import SessionLocal
    url, out = _url(), []
    if not url:
        return out
    db = SessionLocal()
    try:
        for i in ids:
            try:
                nd = noi_dung_po(db, i)
                if nd:
                    kq = gui_webhook_rieng(url, nd)
                    out.append((i, bool(kq.get("da_gui")), kq.get("loi")))
                    if not kq.get("da_gui"):
                        print(f"[PURCHASING] PO {i} chưa nhắn được: {kq.get('loi')}")
            except Exception as e:                                        # noqa: BLE001
                print(f"[PURCHASING] Lỗi PO {i}: {type(e).__name__}: {e}")
    finally:
        db.close()
    return out


def _phat(ids):
    """Gửi ở luồng nền (tách riêng để test thay được)."""
    threading.Thread(target=gui_cac_po, args=(list(ids),), name="svws-purchasing", daemon=True).start()


def _sau_flush(session, _ctx):
    try:
        from .models import DonMua
        ids = [o.id for o in session.new if isinstance(o, DonMua) and getattr(o, "id", None)]
        if ids:
            session.info.setdefault(_KHOA, set()).update(ids)
    except Exception:                                                    # noqa: BLE001
        pass


def _sau_commit(session):
    ids = session.info.pop(_KHOA, None)
    if ids and _url():
        try:
            _phat(sorted(ids))
        except Exception as e:                                           # noqa: BLE001
            print(f"[PURCHASING] Không phát được: {type(e).__name__}: {e}")


def _sau_rollback(session):
    session.info.pop(_KHOA, None)


_DA_DANG_KY = False


def dang_ky():
    """Gọi một lần lúc app khởi động."""
    global _DA_DANG_KY
    if _DA_DANG_KY:
        return
    event.listen(Session, "after_flush", _sau_flush)
    event.listen(Session, "after_commit", _sau_commit)
    event.listen(Session, "after_rollback", _sau_rollback)
    _DA_DANG_KY = True
