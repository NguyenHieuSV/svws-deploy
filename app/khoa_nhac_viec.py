"""🔒 KHÓA TÀI KHOẢN khi KHÔNG PHẢN HỒI việc được giao — Work Reminder (anh Hiếu 05/11/2026).

Luật: lời nhắc do NGƯỜI KHÁC đặt (việc được giao) mà người được nhắc KHÔNG PHẢN HỒI — vẫn «Chờ làm», chưa bấm ▶ Đang làm /
✓ Xong, chưa bị hủy — quá NHAC_VIEC_KHOA_SAU_NGAY (2) ngày sau HẠN (hạn hoàn thành; không đặt hạn → thời điểm nhắc) thì:
  • khóa tài khoản đăng nhập (nguoi_dung.trang_thai = KHOA) — trừ CEO / ADMIN (quản trị không bị khóa, không tính);
  • KPI THÁNG (tháng của hạn) của người đó = 0 — ghi bảng nhac_viec_khoa, kpi_thang() trả 0 kèm lý do;
  • nhắn Google Chat cho người đó: «Tài khoản của bạn bị khóa do không phản hồi việc được giao. KPI tháng = 0.»
    + báo cho người giao việc; khi đăng nhập, tài khoản bị khóa theo luật này cũng thấy đúng câu đó.
Việc có hạn TRƯỚC ngày áp dụng (NHAC_VIEC_KHOA_TU) tính N ngày từ ngày áp dụng — được báo trước, không khóa hồi tố.
Mỗi lời nhắc chỉ khóa MỘT lần (UNIQUE nhac_viec_id). Mở khóa: CEO / ADMIN (nút ở Work Reminder hoặc Cấu hình › người dùng);
KPI tháng vẫn = 0. Chạy mỗi ngày từ BAO_CAO_NHAC_GIO (scheduler) hoặc nút ▶ Quét ngay của quản trị.
"""
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from .audit import ghi_audit
from .config import settings
from .models import NguoiDung, NhacViec, NhacViecKhoa, NhanVien, VaiTro

THONG_BAO = "Tài khoản của bạn bị khóa do không phản hồi việc được giao. KPI tháng = 0."
VAI_TRO_MIEN = ("CEO", "ADMIN")
_TT_CHUA_PHAN_HOI = "CHO_LAM"


def _gio() -> datetime:
    from .nhac_viec_service import gio_hien_tai
    return gio_hien_tai()


def ngay_ap_dung() -> date:
    try:
        return date.fromisoformat(str(settings.nhac_viec_khoa_tu or "")[:10])
    except ValueError:
        return date(2026, 11, 5)


def quy_tac() -> dict:
    return {"bat": bool(settings.nhac_viec_khoa_tu_dong), "sau_ngay": int(settings.nhac_viec_khoa_sau_ngay or 2),
            "ap_dung_tu": str(ngay_ap_dung()), "thong_bao": THONG_BAO, "mien": list(VAI_TRO_MIEN)}


def moc_cua(r) -> datetime | None:
    return getattr(r, "han_hoan_thanh", None) or getattr(r, "thoi_diem", None)


def han_khoa(r) -> datetime | None:
    """Thời điểm sẽ khóa nếu vẫn không phản hồi = max(hạn, 0h ngày áp dụng) + N ngày.
    None = luật không áp dụng cho việc này (tự nhắc mình · đã phản hồi / xong / hủy · không có mốc)."""
    if getattr(r, "trang_thai", None) != _TT_CHUA_PHAN_HOI or r.nguoi_tao == r.nhan_vien_id:
        return None
    moc = moc_cua(r)
    if moc is None:
        return None
    ap_dung = datetime.combine(ngay_ap_dung(), datetime.min.time())
    return max(moc, ap_dung) + timedelta(days=int(settings.nhac_viec_khoa_sau_ngay or 2))


def viec_khong_phan_hoi(db: Session, now: datetime) -> list:
    """Lời nhắc đã QUÁ thời điểm khóa mà vẫn «Chờ làm», chưa có dòng khóa."""
    da = {k for (k,) in db.query(NhacViecKhoa.nhac_viec_id).all()}
    rows = (db.query(NhacViec).filter(NhacViec.trang_thai == _TT_CHUA_PHAN_HOI,
                                      NhacViec.nguoi_tao != NhacViec.nhan_vien_id)
            .order_by(NhacViec.id).all())
    out = []
    for r in rows:
        if r.id in da:
            continue
        hk = han_khoa(r)
        if hk is not None and hk <= now:
            out.append(r)
    return out


def nv_mien(db: Session) -> set:
    """Nhân viên có tài khoản CEO / ADMIN — luật không áp dụng (không khóa, không cảnh báo, không KPI 0)."""
    try:
        return {nv_id for (nv_id, ma) in (db.query(NhanVien.id, VaiTro.ma)
                                           .join(NguoiDung, NguoiDung.id == NhanVien.nguoi_dung_id)
                                           .join(VaiTro, VaiTro.id == NguoiDung.vai_tro_id).all())
                if (ma or "").upper() in VAI_TRO_MIEN}
    except Exception:                                            # noqa: BLE001
        db.rollback()
        return set()


def sap_bi_khoa(db: Session, now: datetime) -> list:
    """Việc được giao đã quá hạn, chưa phản hồi, CHƯA tới giờ khóa — để cảnh báo trong bản tin / giao diện (bỏ CEO / ADMIN)."""
    da = {k for (k,) in db.query(NhacViecKhoa.nhac_viec_id).all()}
    mien = nv_mien(db)
    rows = (db.query(NhacViec).filter(NhacViec.trang_thai == _TT_CHUA_PHAN_HOI,
                                      NhacViec.nguoi_tao != NhacViec.nhan_vien_id).all())
    return [r for r in rows if r.id not in da and r.nhan_vien_id not in mien
            and (hk := han_khoa(r)) is not None and hk > now and (moc_cua(r) or now) < now]


def _tai_khoan(db: Session, nv) -> NguoiDung | None:
    return db.get(NguoiDung, nv.nguoi_dung_id) if (nv is not None and nv.nguoi_dung_id) else None


def _vai_tro(tk) -> str:
    return ((tk.vai_tro.ma if (tk is not None and tk.vai_tro) else "") or "").upper()


def khoa_khong_phan_hoi(db: Session, now: datetime | None = None, ep: bool = False) -> dict:
    """Quét + khóa + ghi KPI 0 + nhắn. Không ném lỗi vì gửi tin; ep=True chạy kể cả khi tắt tự động (nút ▶ của quản trị)."""
    now = now or _gio()
    kq = {"bat": bool(settings.nhac_viec_khoa_tu_dong), "luc": now.isoformat(timespec="minutes"), "so_viec": 0,
          "da_khoa_tk": 0, "khong_tk": 0, "da_khoa_truoc": 0, "mien": 0, "chat_da_gui": 0, "loi": [], "chi_tiet": []}
    if not settings.nhac_viec_khoa_tu_dong and not ep:
        kq["bo_qua"] = "Đang TẮT (NHAC_VIEC_KHOA_TU_DONG=0)"
        return kq
    ds = viec_khong_phan_hoi(db, now)
    if not ds:
        return kq
    from .chat_gateway import dang_bat, lay_chat_provider
    from .nhac_viec_service import _ten_map, gui_toi_nguoi
    prov = lay_chat_provider() if dang_bat() else None
    ten = _ten_map(db, [r.nhan_vien_id for r in ds] + [r.nguoi_tao for r in ds])
    n_ngay = int(settings.nhac_viec_khoa_sau_ngay or 2)
    for r in ds:
        nv = db.get(NhanVien, r.nhan_vien_id)
        if nv is None:
            continue
        tk = _tai_khoan(db, nv)
        if _vai_tro(tk) in VAI_TRO_MIEN:
            kq["mien"] += 1
            continue
        moc = moc_cua(r)
        k = NhacViecKhoa(nhac_viec_id=r.id, nhan_vien_id=nv.id, nguoi_dung_id=(tk.id if tk else None),
                         thang=moc.strftime("%Y-%m"), han=moc, khoa_luc=now, da_khoa_tai_khoan=False, chat_da_gui=False)
        if tk is None:
            kq["khong_tk"] += 1
        elif tk.trang_thai == "HOAT_DONG":
            tk.trang_thai = "KHOA"
            k.da_khoa_tai_khoan = True
            kq["da_khoa_tk"] += 1
            ghi_audit(db, None, "KHOA_KHONG_PH", "nguoi_dung", tk.id, cu={"trang_thai": "HOAT_DONG"},
                      moi={"trang_thai": "KHOA", "nhac_viec_id": r.id, "tieu_de": r.tieu_de})
        else:
            kq["da_khoa_truoc"] += 1                          # tài khoản đã bị khóa từ trước → chỉ ghi KPI 0
        db.add(k)
        db.flush()
        ghi_audit(db, None, "KHOA", "nhac_viec_khoa", k.id,
                  moi={"nhan_vien": nv.ho_ten, "nhac_viec_id": r.id, "tieu_de": r.tieu_de, "thang": k.thang,
                       "han": moc.isoformat(timespec="minutes"), "da_khoa_tai_khoan": k.da_khoa_tai_khoan})
        nguoi_giao = ten.get(r.nguoi_tao) or "người giao việc"
        if prov is not None:
            nd_nv = (f"🔒 *{THONG_BAO}*\n\nViệc: *{r.tieu_de}* — {nguoi_giao} giao, hạn {moc:%d/%m %H:%M}, "
                     f"không phản hồi quá {n_ngay} ngày.\nKPI tháng {k.thang[5:7]}/{k.thang[:4]} = 0. "
                     "Liên hệ CEO / Admin để mở khóa, rồi vào Work Reminder bấm ▶ Đang làm / ✓ Xong.")
            try:
                g = gui_toi_nguoi(db, prov, nv.email or "", nd_nv)
                k.chat_da_gui = bool(g.get("da_gui"))
                k.chat_loi = (str(g.get("loi"))[:500] if g.get("loi") else None)
            except Exception as e:                               # noqa: BLE001
                k.chat_loi = f"{type(e).__name__}: {str(e)[:300]}"
            if k.chat_da_gui:
                kq["chat_da_gui"] += 1
            elif k.chat_loi:
                kq["loi"].append(f"{nv.ho_ten}: {k.chat_loi}")
            ng = db.get(NhanVien, r.nguoi_tao)
            if ng is not None and (ng.email or "").strip():
                try:
                    gui_toi_nguoi(db, prov, ng.email, f"🔒 Đã khóa tài khoản *{nv.ho_ten}* do không phản hồi việc anh/chị giao: "
                                                      f"*{r.tieu_de}* (hạn {moc:%d/%m %H:%M}). KPI tháng {k.thang[5:7]}/{k.thang[:4]} "
                                                      f"của {nv.ho_ten} = 0." + ("" if tk else " (Người này chưa có tài khoản đăng nhập.)"))
                except Exception:                                # noqa: BLE001
                    pass
        kq["so_viec"] += 1
        kq["chi_tiet"].append({"khoa_id": k.id, "nhac_viec_id": r.id, "nhan_vien": nv.ho_ten, "tieu_de": r.tieu_de,
                               "han": moc.isoformat(timespec="minutes"), "thang": k.thang,
                               "tai_khoan": ("đã khóa" if k.da_khoa_tai_khoan else ("không có tài khoản" if tk is None else "đã khóa từ trước")),
                               "chat_da_gui": k.chat_da_gui})
    db.commit()
    return kq


def dang_bi_khoa(db: Session, nguoi_dung_id: int):
    """Dòng khóa còn hiệu lực (đã khóa tài khoản, chưa mở) của một tài khoản — dùng cho câu báo khi đăng nhập."""
    return (db.query(NhacViecKhoa)
            .filter(NhacViecKhoa.nguoi_dung_id == nguoi_dung_id, NhacViecKhoa.da_khoa_tai_khoan.is_(True),
                    NhacViecKhoa.mo_khoa_luc.is_(None))
            .order_by(NhacViecKhoa.id.desc()).first())


def thong_bao_dang_nhap(db: Session, nd) -> str:
    """Câu báo khi tài khoản không HOAT_DONG: khóa theo luật này → đúng câu anh Hiếu chốt; còn lại → câu chung."""
    try:
        if nd.trang_thai != "HOAT_DONG" and dang_bi_khoa(db, nd.id) is not None:
            return THONG_BAO + " Liên hệ CEO / Admin để mở khóa."
    except Exception:                                            # noqa: BLE001
        db.rollback()
    return "Tài khoản đã bị khóa. Liên hệ Admin/CEO để mở lại."


def mo_khoa(db: Session, khoa_id: int, nd, now: datetime | None = None):
    """CEO / ADMIN mở khóa một dòng: tài khoản HOAT_DONG lại (nếu không còn dòng khóa khác đang hiệu lực); KPI tháng vẫn 0."""
    k = db.get(NhacViecKhoa, khoa_id)
    if k is None:
        return None
    if k.mo_khoa_luc is not None:
        return k
    now = now or _gio()
    k.mo_khoa_luc, k.mo_khoa_boi = now, nd.id
    if k.nguoi_dung_id and k.da_khoa_tai_khoan:
        con = (db.query(NhacViecKhoa.id)
               .filter(NhacViecKhoa.nguoi_dung_id == k.nguoi_dung_id, NhacViecKhoa.da_khoa_tai_khoan.is_(True),
                       NhacViecKhoa.mo_khoa_luc.is_(None), NhacViecKhoa.id != k.id).first())
        tk = db.get(NguoiDung, k.nguoi_dung_id)
        if tk is not None and tk.trang_thai == "KHOA" and con is None:
            tk.trang_thai = "HOAT_DONG"
            ghi_audit(db, nd.id, "MO_KHOA", "nguoi_dung", tk.id, cu={"trang_thai": "KHOA"}, moi={"trang_thai": "HOAT_DONG", "khoa_id": k.id})
    ghi_audit(db, nd.id, "MO_KHOA", "nhac_viec_khoa", k.id, moi={"mo_khoa_luc": now.isoformat(timespec="minutes")})
    db.commit()
    return k


def dong_khoa_khi_mo_tay(db: Session, nguoi_dung_id: int, nd_id, now: datetime | None = None) -> int:
    """Quản trị mở khóa ở Cấu hình › người dùng (không qua nút Work Reminder) → đóng các dòng khóa đang hiệu lực cho khớp."""
    now = now or _gio()
    n = 0
    for k in (db.query(NhacViecKhoa)
              .filter(NhacViecKhoa.nguoi_dung_id == nguoi_dung_id, NhacViecKhoa.da_khoa_tai_khoan.is_(True),
                      NhacViecKhoa.mo_khoa_luc.is_(None)).all()):
        k.mo_khoa_luc, k.mo_khoa_boi = now, nd_id
        n += 1
    return n


def _khoa_ra(k: NhacViecKhoa, ten: dict, tieu_de: dict, email_tk: dict) -> dict:
    return {"id": k.id, "nhac_viec_id": k.nhac_viec_id, "nhan_vien_id": k.nhan_vien_id, "nhan_vien": ten.get(k.nhan_vien_id),
            "tieu_de": tieu_de.get(k.nhac_viec_id), "nguoi_dung_id": k.nguoi_dung_id, "email": email_tk.get(k.nguoi_dung_id),
            "thang": k.thang, "han": k.han.isoformat(timespec="minutes") if k.han else None,
            "khoa_luc": k.khoa_luc.isoformat(timespec="minutes") if k.khoa_luc else None,
            "da_khoa_tai_khoan": bool(k.da_khoa_tai_khoan),
            "mo_khoa_luc": k.mo_khoa_luc.isoformat(timespec="minutes") if k.mo_khoa_luc else None,
            "mo_khoa_boi": k.mo_khoa_boi, "chat_da_gui": bool(k.chat_da_gui), "chat_loi": k.chat_loi,
            "hieu_luc": bool(k.da_khoa_tai_khoan) and k.mo_khoa_luc is None}


def danh_sach_khoa(db: Session, nhan_vien_id: int | None = None, thang: str | None = None) -> list[dict]:
    q = db.query(NhacViecKhoa)
    if nhan_vien_id is not None:
        q = q.filter(NhacViecKhoa.nhan_vien_id == nhan_vien_id)
    if thang:
        q = q.filter(NhacViecKhoa.thang == thang)
    rows = q.order_by(NhacViecKhoa.id.desc()).limit(300).all()
    if not rows:
        return []
    ten = {nv.id: nv.ho_ten for nv in db.query(NhanVien).filter(NhanVien.id.in_({k.nhan_vien_id for k in rows})).all()}
    tieu_de = {r.id: r.tieu_de for r in db.query(NhacViec).filter(NhacViec.id.in_({k.nhac_viec_id for k in rows})).all()}
    uids = {k.nguoi_dung_id for k in rows if k.nguoi_dung_id}
    email_tk = {u.id: u.email for u in db.query(NguoiDung).filter(NguoiDung.id.in_(uids)).all()} if uids else {}
    return [_khoa_ra(k, ten, tieu_de, email_tk) for k in rows]


def kpi_thang(db: Session, thang: str, now: datetime | None = None, nhan_vien_id: int | None = None) -> dict:
    """⭐ KPI THÁNG theo nhân viên = trung bình KPI các lời nhắc có mốc trong tháng (bỏ hủy; chưa chấm được không tính);
    có dòng khóa trong tháng → KPI tháng = 0 kèm lý do. Lời nhắc tự đặt cho mình vẫn tính như cũ."""
    from .kpi_nhac_viec import tinh_kpi
    now = now or _gio()
    y, m = int(thang[:4]), int(thang[5:7])
    d1 = datetime(y, m, 1)
    d2 = datetime(y + (1 if m == 12 else 0), 1 if m == 12 else m + 1, 1)
    rows = db.query(NhacViec).filter(NhacViec.trang_thai != "HUY").all()
    khoa = {}
    for k in db.query(NhacViecKhoa).filter(NhacViecKhoa.thang == thang).all():
        khoa.setdefault(k.nhan_vien_id, []).append(k)
    theo: dict[int, dict] = {}
    for r in rows:
        moc = moc_cua(r)
        if moc is None or not (d1 <= moc < d2):
            continue
        if nhan_vien_id is not None and r.nhan_vien_id != nhan_vien_id:
            continue
        e = theo.setdefault(r.nhan_vien_id, {"so_viec": 0, "so_xong": 0, "so_qua_han": 0, "chua_phan_hoi": 0, "kpi_ds": []})
        e["so_viec"] += 1
        if r.trang_thai == "XONG":
            e["so_xong"] += 1
        elif moc < now:
            e["so_qua_han"] += 1
            if r.trang_thai == _TT_CHUA_PHAN_HOI and r.nguoi_tao != r.nhan_vien_id:
                e["chua_phan_hoi"] += 1
        k = tinh_kpi(r, now)
        if k.get("tinh") and k.get("kpi") is not None:
            e["kpi_ds"].append(k["kpi"])
    for nv_id in khoa:
        if nhan_vien_id is None or nv_id == nhan_vien_id:
            theo.setdefault(nv_id, {"so_viec": 0, "so_xong": 0, "so_qua_han": 0, "chua_phan_hoi": 0, "kpi_ds": []})
    ids = set(theo)
    ten = {nv.id: nv for nv in db.query(NhanVien).filter(NhanVien.id.in_(ids)).all()} if ids else {}
    out = []
    for nv_id, e in theo.items():
        nv = ten.get(nv_id)
        kpi_tb = round(sum(e["kpi_ds"]) / len(e["kpi_ds"])) if e["kpi_ds"] else None
        ks = khoa.get(nv_id) or []
        out.append({"nhan_vien_id": nv_id, "ho_ten": nv.ho_ten if nv else f"NV#{nv_id}", "chuc_danh": nv.chuc_danh if nv else None,
                    "so_viec": e["so_viec"], "so_xong": e["so_xong"], "so_qua_han": e["so_qua_han"],
                    "chua_phan_hoi": e["chua_phan_hoi"], "so_da_cham": len(e["kpi_ds"]), "kpi_tb": kpi_tb,
                    "khoa_n": len(ks), "kpi": (0 if ks else kpi_tb),
                    "ly_do": (f"🔒 khóa do không phản hồi {len(ks)} việc được giao → KPI tháng = 0" if ks else None)})
    out.sort(key=lambda x: (x["kpi"] is None, x["kpi"] if x["kpi"] is not None else 0, x["ho_ten"]))
    return {"thang": thang, "quy_tac": quy_tac(), "danh_sach": out}
