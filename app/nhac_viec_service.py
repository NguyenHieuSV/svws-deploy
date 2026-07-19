"""Gửi lời nhắc công việc qua Google Chat.

Hai luồng:
  1. gui_khi_tao(...)   — gửi ngay khi vừa đặt lời nhắc.
  2. gui_ban_tin_ngay() — bản tin tổng hợp đầu ngày cho từng người
                          (việc đến hạn hôm nay + việc đang quá hạn).

Mọi hàm ở đây đều NUỐT LỖI: gửi tin hỏng không được phép làm hỏng nghiệp vụ.
"""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .chat_gateway import lay_chat_provider, dang_bat
from .config import settings
from .models import NhacViec, NhacViecBanTin, NhanVien

_MUC_DO_NHAN = {"THAP": "Thấp", "BINH_THUONG": "Bình thường", "CAO": "Cao", "KHAN": "🔴 KHẨN"}


def gio_hien_tai() -> datetime:
    """Giờ ĐỊA PHƯƠNG (Việt Nam) dạng naive — khớp với cách lưu thoi_diem/han_hoan_thanh.
    Máy chủ chạy UTC nên phải cộng offset, nếu không mọi so sánh 'quá hạn' lệch 7 tiếng."""
    return (datetime.now(timezone.utc).replace(tzinfo=None)
            + timedelta(hours=settings.tz_offset_gio))


def ngay_hien_tai() -> date:
    return gio_hien_tai().date()


def _gio(d: datetime | None) -> str:
    return d.strftime("%d/%m %H:%M") if d else "—"


def _mo_ta(r: NhacViec, ten: dict) -> str:
    """Một lời nhắc -> đoạn text gọn cho Google Chat."""
    d = [f"*{r.tieu_de}*"]
    d.append(f"• Nhắc lúc: {_gio(r.thoi_diem)}")
    if r.han_hoan_thanh:
        tre = " ⚠️ *ĐÃ QUÁ HẠN*" if r.han_hoan_thanh < gio_hien_tai() else ""
        d.append(f"• Hạn hoàn thành: {_gio(r.han_hoan_thanh)}{tre}")
    if r.ma_lien_quan:
        d.append(f"• Mã liên quan: {r.ma_lien_quan}")
    if r.chuan_bi:
        d.append(f"• Cần chuẩn bị: {r.chuan_bi}")
    if r.nguoi_ho_tro_id:
        ho_tro = ten.get(r.nguoi_ho_tro_id) or "—"
        d.append(f"• Người hỗ trợ: {ho_tro}" + (f" ({r.ho_tro_gi})" if r.ho_tro_gi else ""))
    if (r.muc_do or "") in ("CAO", "KHAN"):
        d.append(f"• Mức độ: {_MUC_DO_NHAN.get(r.muc_do, r.muc_do)}")
    if r.ghi_chu:
        d.append(f"• Ghi chú: {r.ghi_chu}")
    return "\n".join(d)


def _ten_map(db: Session, ids) -> dict:
    ids = {i for i in ids if i}
    if not ids:
        return {}
    return {nv.id: nv.ho_ten for nv in db.query(NhanVien).filter(NhanVien.id.in_(ids)).all()}


def gui_khi_tao(db: Session, rows: list[NhacViec]) -> dict:
    """Gửi ngay sau khi đặt lời nhắc. rows = các dòng vừa tạo (1 hoặc N khi 'nhắc tất cả')."""
    if not rows or not settings.nhac_viec_gui_khi_tao or not dang_bat():
        return {"da_gui": 0, "bo_qua": len(rows or [])}
    prov = lay_chat_provider()
    ten = _ten_map(db, [r.nhan_vien_id for r in rows] +
                       [r.nguoi_ho_tro_id for r in rows] + [rows[0].nguoi_tao])
    nguoi_dat = ten.get(rows[0].nguoi_tao) or "một đồng nghiệp"
    da_gui, loi = 0, []
    for r in rows:
        nv = db.get(NhanVien, r.nhan_vien_id)
        if nv is None:
            continue
        tu = "Bạn tự đặt lời nhắc này" if r.nguoi_tao == r.nhan_vien_id else f"{nguoi_dat} nhắc bạn"
        noi_dung = f"🔔 *Nhắc việc SVWS* — {tu}:\n\n{_mo_ta(r, ten)}"
        kq = prov.gui_ca_nhan(nv.email or "", noi_dung)
        if kq.get("da_gui"):
            r.da_gui_tao = True
            da_gui += 1
        elif kq.get("loi"):
            loi.append(f"{nv.ho_ten}: {kq['loi']}")
    return {"da_gui": da_gui, "loi": loi[:5]}


def _viec_can_nhac(db: Session, hom_nay: date) -> dict:
    """Gom việc CHƯA XONG theo từng người: đến hạn hôm nay hoặc đã quá hạn."""
    cuoi_ngay = datetime.combine(hom_nay, datetime.max.time())
    rows = (db.query(NhacViec)
            .filter(NhacViec.trang_thai.in_(("CHO_LAM", "DANG_LAM")))
            .order_by(NhacViec.thoi_diem).all())
    theo_nguoi: dict = {}
    for r in rows:
        moc = r.han_hoan_thanh or r.thoi_diem
        if moc <= cuoi_ngay:                      # tới hạn trong hôm nay hoặc đã trễ
            theo_nguoi.setdefault(r.nhan_vien_id, []).append(r)
    return theo_nguoi


def gui_ban_tin_ngay(db: Session, ep: bool = False) -> dict:
    """Bản tin đầu ngày. Chốt theo ngày trong bảng nhac_viec_ban_tin -> không gửi trùng.
    ep=True: bỏ qua chốt ngày (dùng cho nút gửi thử của quản trị)."""
    hom_nay = ngay_hien_tai()
    if not ep:
        if not settings.nhac_viec_ban_tin or not dang_bat():
            return {"bo_qua": "Chưa bật bản tin hoặc chưa cấu hình Google Chat"}
        # giành quyền gửi: ai chèn được dòng của hôm nay thì người đó gửi
        if db.get(NhacViecBanTin, hom_nay) is not None:
            return {"bo_qua": "Bản tin hôm nay đã gửi"}
        db.add(NhacViecBanTin(ngay=hom_nay))
        try:
            db.commit()
        except Exception:          # tiến trình khác vừa chèn trước -> thôi, khỏi gửi
            db.rollback()
            return {"bo_qua": "Bản tin hôm nay đã gửi (tiến trình khác)"}

    theo_nguoi = _viec_can_nhac(db, hom_nay)
    prov = lay_chat_provider()
    ten = _ten_map(db, [i for i in theo_nguoi] +
                       [r.nguoi_ho_tro_id for ds in theo_nguoi.values() for r in ds])
    da_gui, tong_viec, loi = 0, 0, []
    for nv_id, ds in theo_nguoi.items():
        nv = db.get(NhanVien, nv_id)
        if nv is None:
            continue
        qua_han = [r for r in ds if (r.han_hoan_thanh or r.thoi_diem) < gio_hien_tai()]
        dong = [f"☀️ *Chào {nv.ho_ten}* — việc cần làm hôm nay {hom_nay.strftime('%d/%m/%Y')}:"]
        if qua_han:
            dong.append(f"\n⚠️ *{len(qua_han)} việc đã quá hạn*")
        for i, r in enumerate(ds, 1):
            dong.append(f"\n*{i}.* {_mo_ta(r, ten)}")
        dong.append("\n_Mở app SVWS → Working time & Report → Work Reminder để đánh dấu hoàn thành._")
        kq = prov.gui_ca_nhan(nv.email or "", "\n".join(dong))
        if kq.get("da_gui"):
            da_gui += 1
            tong_viec += len(ds)
        elif kq.get("loi"):
            loi.append(f"{nv.ho_ten}: {kq['loi']}")

    if not ep:
        bt = db.get(NhacViecBanTin, hom_nay)
        if bt is not None:
            bt.so_nguoi, bt.so_viec = da_gui, tong_viec
            bt.ket_qua = ("; ".join(loi))[:2000] if loi else "OK"
            db.commit()
    return {"da_gui": da_gui, "so_viec": tong_viec, "loi": loi[:5],
            "so_nguoi_co_viec": len(theo_nguoi)}
