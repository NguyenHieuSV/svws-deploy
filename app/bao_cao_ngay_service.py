"""Báo cáo ngày (Working time & Report): ngày nào PHẢI báo cáo, tổng hợp + tỉ lệ hoàn thành, nhắc hôm sau.

Quy tắc «phải báo cáo» (anh Hiếu chốt 26/10/2026):
  • Ngày thường và thứ Bảy: phải báo cáo, TRỪ ngày đang nghỉ (nghỉ phép / việc riêng / ốm…) hoặc ngày lễ trong lịch nghỉ lễ.
  • Chủ nhật và ngày lễ: KHÔNG phải báo cáo, TRỪ khi có đăng ký tăng ca ngày đó → khi đó phải báo cáo.
  • Tăng ca luôn phải báo cáo. Đăng ký (kể cả đang chờ duyệt) bị từ chối thì không tính.
  • Nghỉ nửa ngày (0 < số ngày < 1) vẫn phải báo cáo.
  • Chỉ tính người ĐANG LÀM, trong khoảng ngày vào làm … ngày nghỉ việc, và CÓ tài khoản đăng nhập gắn hồ sơ (không có tài khoản thì không báo cáo được).
  • CHỈ ngày người đó là NGƯỜI NHẬN của một việc được giao còn hiệu lực (bắt đầu ≤ ngày ≤ kết thúc) mới phải báo cáo
    (anh Hiếu 26/10/2026) — không có việc được giao thì không tính thiếu, không tính tỉ lệ, không nhắc.
Nhắc: sáng hôm sau, ai thiếu báo cáo của ngày hôm trước → «Bạn chưa hoàn thành báo cáo ngày …» qua Google Chat.
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from .models import BaoCaoNgay, BaoCaoNhac, NgayNghiOt, NguoiDung, NhanVien

NHAN_NGHI = {"NGHI_PHEP": "Nghỉ phép", "KHONG_PHEP": "Nghỉ không phép", "NGHI_LE": "Nghỉ lễ",
             "VIEC_RIENG_CO_LUONG": "Việc riêng (có lương)", "VIEC_RIENG_KHONG_LUONG": "Việc riêng (không lương)",
             "NGHI_BU": "Nghỉ bù", "NGHI_OM_BHXH": "Nghỉ ốm", "NGHI_THAI_SAN": "Nghỉ thai sản"}
THU = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ nhật"]


def dmy(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def ngay_ap_dung() -> date | None:
    """Ngày bắt đầu áp dụng (config bao_cao_tinh_tu, mặc định 26/10/2026 — ngày bật tính năng).
    Trước ngày này không tính thiếu báo cáo, không tính tỉ lệ, không nhắc."""
    from .config import settings
    try:
        return date.fromisoformat((settings.bao_cao_tinh_tu or "").strip()) if (settings.bao_cao_tinh_tu or "").strip() else None
    except ValueError:
        return None


def la_ngay_le(d: date) -> bool:
    """Ngày lễ trong lịch nghỉ lễ của Working time (cố định hằng năm + lễ chốt theo năm)."""
    from .routers.nhan_su import _wt_loai_ngay
    return _wt_loai_ngay(d) == "OT_LE"


def phai_bao_cao(d: date, co_ot: bool, loai_nghi: str | None):
    """→ (phải báo cáo?, lý do khi KHÔNG phải)."""
    if co_ot:
        return True, None
    if d.weekday() == 6:
        return False, "Chủ nhật"
    if la_ngay_le(d):
        return False, "Ngày lễ"
    if loai_nghi:
        return False, NHAN_NGHI.get(loai_nghi, "Nghỉ")
    return True, None


def nap_du_lieu(db: Session, nv_ids, tu: date, den: date):
    """Nạp một lượt báo cáo + tăng ca + nghỉ + VIỆC ĐƯỢC GIAO của các nhân viên trong khoảng ngày.
    → (bc, ot, nghi, viec) — viec = {nhan_vien_id: [(bắt đầu, kết thúc), …]}."""
    from .models import GiaoViec
    from .routers.nhan_su import _WT_OT, _WT_NGHI
    ids = list(nv_ids)
    bc, ot, nghi, viec = {}, set(), {}, {}
    if not ids:
        return bc, ot, nghi, viec
    for g in (db.query(GiaoViec).filter(GiaoViec.nhan_vien_id.in_(ids),
                                        (GiaoViec.bat_dau.is_(None)) | (GiaoViec.bat_dau <= den),
                                        (GiaoViec.ket_thuc.is_(None)) | (GiaoViec.ket_thuc >= tu)).all()):
        viec.setdefault(g.nhan_vien_id, []).append((g.bat_dau, g.ket_thuc))
    for r in (db.query(BaoCaoNgay).filter(BaoCaoNgay.nhan_vien_id.in_(ids), BaoCaoNgay.ngay >= tu,
                                          BaoCaoNgay.ngay <= den).all()):
        bc[(r.nhan_vien_id, r.ngay)] = r
    for r in (db.query(NgayNghiOt).filter(NgayNghiOt.nhan_vien_id.in_(ids), NgayNghiOt.ngay >= tu,
                                          NgayNghiOt.ngay <= den, NgayNghiOt.trang_thai != "TU_CHOI").all()):
        if r.loai in _WT_OT:
            ot.add((r.nhan_vien_id, r.ngay))
        elif r.loai in _WT_NGHI:
            sn = float(r.so_ngay or 0)
            if not (0 < sn < 1):                       # nghỉ nửa ngày vẫn phải báo cáo
                nghi[(r.nhan_vien_id, r.ngay)] = r.loai
    return bc, ot, nghi, viec


def co_viec(viec: dict, nv_id: int, d: date) -> bool:
    """Ngày d người này có việc được giao còn hiệu lực (bắt đầu ≤ d ≤ kết thúc; để trống = không giới hạn)."""
    return any((bd is None or bd <= d) and (kt is None or kt >= d) for bd, kt in viec.get(nv_id, ()))


def tong_hop_nv(nv: NhanVien, bc, ot, nghi, viec, tu: date, den: date, hom_nay: date) -> dict:
    """Từng ngày trong [tu, min(den, hôm nay)] + tỉ lệ hoàn thành.
    Trạng thái: DA (đã báo cáo) · THIEU (đến hạn mà chưa báo cáo) · CHO (hôm nay, chưa tới hạn) · MIEN (không phải báo cáo)."""
    if nv.ngay_vao_lam and nv.ngay_vao_lam > tu:
        tu = nv.ngay_vao_lam
    ad = ngay_ap_dung()
    if ad and ad > tu:                                   # trước ngày áp dụng: không liệt kê, không tính
        tu = ad
    cuoi = min(den, hom_nay)
    if nv.ngay_nghi_viec and nv.ngay_nghi_viec < cuoi:
        cuoi = nv.ngay_nghi_viec
    ngay_ds, can, xong = [], 0, 0
    d = tu
    while d <= cuoi:
        r = bc.get((nv.id, d))
        bat_buoc, ly_do = phai_bao_cao(d, (nv.id, d) in ot, nghi.get((nv.id, d)))
        if bat_buoc and not co_viec(viec, nv.id, d):
            bat_buoc, ly_do = False, "Không có việc được giao"
        if r is not None:
            tt = "DA"
        elif not bat_buoc:
            tt = "MIEN"
        elif d < hom_nay:
            tt = "THIEU"
        else:
            tt = "CHO"
        if bat_buoc and (d < hom_nay or r is not None):
            can += 1
            xong += 1 if r is not None else 0
        ngay_ds.append({
            "ngay": str(d), "thu": THU[d.weekday()], "trang_thai": tt, "bat_buoc": bat_buoc, "ly_do": ly_do,
            "ket_qua": ((r.ket_qua or "").strip() or (r.da_lam or "").strip()) if r is not None else "",
            "ten_cong_viec": r.ten_cong_viec if r is not None else None})
        d += timedelta(days=1)
    return {"ngay": ngay_ds, "can": can, "xong": xong, "thieu": sum(1 for x in ngay_ds if x["trang_thai"] == "THIEU"),
            "ty_le": round(100.0 * xong / can, 1) if can else None}


def nv_du_dieu_kien(db: Session):
    """Nhân viên đang làm VÀ có tài khoản đăng nhập đang hoạt động gắn hồ sơ → [(NhanVien, NguoiDung)]."""
    return (db.query(NhanVien, NguoiDung).join(NguoiDung, NguoiDung.id == NhanVien.nguoi_dung_id)
            .filter(NhanVien.trang_thai == "DANG_LAM", NguoiDung.trang_thai == "HOAT_DONG")
            .order_by(NhanVien.ho_ten).all())


def ds_phai_bao_cao(db: Session, ngay: date) -> list:
    """Người PHẢI báo cáo ngày `ngay` (người nhận việc còn hiệu lực, ngày làm việc, không nghỉ, từ ngày áp dụng)
    → [{nhan_vien_id, ten, email, co_viec, da_bao_cao}]."""
    ad = ngay_ap_dung()
    if ad and ngay < ad:
        return []
    cap = nv_du_dieu_kien(db)
    bc, ot, nghi, viec = nap_du_lieu(db, [nv.id for nv, _ in cap], ngay, ngay)
    out = []
    for nv, u in cap:
        if nv.ngay_vao_lam and nv.ngay_vao_lam > ngay:
            continue
        if nv.ngay_nghi_viec and nv.ngay_nghi_viec < ngay:
            continue
        if phai_bao_cao(ngay, (nv.id, ngay) in ot, nghi.get((nv.id, ngay)))[0] and co_viec(viec, nv.id, ngay):
            out.append({"nhan_vien_id": nv.id, "ten": nv.ho_ten, "email": u.email, "co_viec": True,
                        "da_bao_cao": (nv.id, ngay) in bc})
    return out


def ds_thieu_bao_cao(db: Session, ngay: date) -> list:
    """Người phải báo cáo ngày `ngay` mà CHƯA có báo cáo → [{nhan_vien_id, ten, email, co_viec}]."""
    return [{k: v for k, v in x.items() if k != "da_bao_cao"} for x in ds_phai_bao_cao(db, ngay) if not x["da_bao_cao"]]


def thieu_gan_day(db: Session, nv_id: int, hom_nay: date, so_ngay: int = 14) -> list:
    """Các ngày ĐẾN HẠN mà người này chưa báo cáo trong `so_ngay` ngày gần nhất (không gồm hôm nay)."""
    nv = db.get(NhanVien, nv_id)
    if nv is None:
        return []
    tu, den = hom_nay - timedelta(days=so_ngay), hom_nay - timedelta(days=1)
    bc, ot, nghi, viec = nap_du_lieu(db, [nv_id], tu, den)
    th = tong_hop_nv(nv, bc, ot, nghi, viec, tu, den, hom_nay)
    return [x["ngay"] for x in th["ngay"] if x["trang_thai"] == "THIEU"]


# ---------------- nhắc qua Google Chat ----------------
def noi_dung_rieng(ngay: date) -> str:
    return (f"📝 Bạn chưa hoàn thành báo cáo ngày: {dmy(ngay)} ({THU[ngay.weekday()]}).\n"
            "Vui lòng vào app SVWS → Working time & Report → Report để hoàn thành báo cáo.")


def noi_dung_chung(ngay: date, ds: list) -> str:
    ten = "\n".join(f"• {x['ten']}" for x in ds)
    return (f"📝 Chưa hoàn thành báo cáo ngày: {dmy(ngay)} ({THU[ngay.weekday()]}) — {len(ds)} người nhận việc:\n{ten}\n"
            "Các bạn vui lòng vào app SVWS → Working time & Report → Report để hoàn thành báo cáo.")


def gui_nhac(db: Session, ngay: date, nguon: str = "TU_DONG", nguoi_gui=None) -> dict:
    """Nhắc những người thiếu báo cáo `ngay` (mỗi người một lần). Không ném lỗi chat ra ngoài.
    CHỈ nhắc người là NGƯỜI NHẬN của việc được giao còn hiệu lực ngày đó (anh Hiếu 26/10/2026);
    không ai có việc được giao → không gửi tin nào.
    • Chế độ APP: mỗi người MỘT tin riêng «Bạn chưa hoàn thành báo cáo ngày: …».
    • Chế độ WEBHOOK (chỉ đăng phòng chung): MỘT tin gộp ghi tên những người thiếu."""
    from .chat_gateway import dang_bat, lay_chat_provider
    from .nhac_viec_service import gio_hien_tai, gui_toi_nguoi
    tong = {"ngay": str(ngay), "thieu": 0, "da_gui": 0, "da_nhac_truoc": 0, "khong_co_viec": 0, "loi": [], "kieu": None, "ten": []}
    tat_ca = ds_thieu_bao_cao(db, ngay)
    ds = [x for x in tat_ca if x["co_viec"]]
    tong["thieu"] = len(tat_ca)
    tong["khong_co_viec"] = len(tat_ca) - len(ds)
    da = {r.nhan_vien_id for r in db.query(BaoCaoNhac).filter(BaoCaoNhac.ngay == ngay, BaoCaoNhac.ket_qua == "OK").all()}
    chon = [x for x in ds if x["nhan_vien_id"] not in da]
    tong["da_nhac_truoc"] = len(ds) - len(chon)
    if not chon:
        return tong
    if not dang_bat():
        tong["loi"].append("Google Chat chưa được bật trên máy chủ (đang ở chế độ DEMO) nên chưa gửi được.")
        return tong
    prov = lay_chat_provider()
    rieng = getattr(prov, "che_do", "") == "APP"
    tong["kieu"] = "RIENG" if rieng else "PHONG_CHUNG"
    now = gio_hien_tai()

    def ghi(x, ok, loi=None):
        db.add(BaoCaoNhac(ngay=ngay, nhan_vien_id=x["nhan_vien_id"], nguon=nguon, ket_qua="OK" if ok else "LOI",
                          loi=None if ok else (str(loi or "")[:500] or None), nguoi_gui=nguoi_gui, tao_luc=now))

    if not rieng:
        try:
            kq = prov.gui_phong(noi_dung_chung(ngay, chon))
        except Exception as e:                                          # noqa: BLE001
            kq = {"da_gui": False, "loi": f"{type(e).__name__}: {str(e)[:120]}"}
        ok = bool(kq.get("da_gui"))
        for x in chon:
            ghi(x, ok, kq.get("loi"))
        if ok:
            tong["da_gui"] = len(chon)
            tong["ten"] = [x["ten"] for x in chon]
        else:
            tong["loi"].append(str(kq.get("loi") or "không gửi được vào phòng chung"))
        db.commit()
        return tong
    for x in chon:
        try:
            kq = gui_toi_nguoi(db, prov, x["email"], noi_dung_rieng(ngay))
        except Exception as e:                                          # noqa: BLE001
            kq = {"da_gui": False, "loi": f"{type(e).__name__}: {str(e)[:120]}"}
        ok = bool(kq.get("da_gui"))
        ghi(x, ok, kq.get("loi"))
        if ok:
            tong["da_gui"] += 1
            tong["ten"].append(x["ten"])
        else:
            tong["loi"].append(f"{x['ten']}: {kq.get('loi') or 'không gửi được'}")
    db.commit()
    return tong


def noi_dung_giao_viec(g, ten_nv: str, nguoi_giao: str, la_sua: bool, rieng: bool) -> str:
    if rieng:
        tieu = ("✏️ Cập nhật việc được giao cho bạn" if la_sua else "📌 Bạn được giao việc") + f": *{g.ten_cong_viec}*"
    else:
        tieu = ("✏️ Cập nhật việc giao cho " if la_sua else "📌 Giao việc cho ") + f"{ten_nv}: *{g.ten_cong_viec}*"
    bd = dmy(g.bat_dau) if g.bat_dau else "…"
    kt = dmy(g.ket_thuc) if g.ket_thuc else "…"
    ma = f"• Mã dự án: {g.ma_du_an}\n" if getattr(g, "ma_du_an", None) else ""
    return (f"{tieu}\n• Thời gian: {bd} → {kt}\n{ma}• Người giao: {nguoi_giao}\n"
            "Khi báo cáo ngày, chọn việc này ở ô «Công việc được giao» (app SVWS → Working time & Report → Report).")


def thong_bao_giao_viec(db: Session, g, nv: NhanVien, nguoi_giao: str, la_sua: bool = False) -> dict:
    """Nhắn người nhận việc qua Google Chat. Không bao giờ ném lỗi (giao việc vẫn lưu dù nhắn hỏng).
    APP: nhắn riêng người nhận. WEBHOOK: một tin vào phòng chung ghi tên người nhận."""
    from .chat_gateway import dang_bat, lay_chat_provider
    from .nhac_viec_service import gui_toi_nguoi
    kq = {"da_gui": False, "kieu": None, "loi": None}
    try:
        if not dang_bat():
            kq["loi"] = "Google Chat chưa bật trên máy chủ (chế độ DEMO)"
            return kq
        prov = lay_chat_provider()
        rieng = getattr(prov, "che_do", "") == "APP"
        kq["kieu"] = "RIENG" if rieng else "PHONG_CHUNG"
        nd_ = noi_dung_giao_viec(g, nv.ho_ten, nguoi_giao, la_sua, rieng)
        if rieng:
            u = db.get(NguoiDung, nv.nguoi_dung_id) if nv.nguoi_dung_id else None
            email = (u.email if u is not None else None) or g.email
            r = gui_toi_nguoi(db, prov, email, nd_)
        else:
            r = prov.gui_phong(nd_)
        kq["da_gui"] = bool(r.get("da_gui"))
        kq["loi"] = None if kq["da_gui"] else str(r.get("loi") or "không gửi được")
    except Exception as e:                                              # noqa: BLE001
        kq["loi"] = f"{type(e).__name__}: {str(e)[:120]}"
    return kq


def nhac_tu_dong_hang_ngay(db: Session) -> dict:
    """Bộ hẹn giờ gọi: từ `bao_cao_nhac_gio` (giờ VN) nhắc báo cáo của HÔM QUA. Tắt bằng BAO_CAO_NHAC_TU_DONG=0."""
    from .config import settings
    from .nhac_viec_service import gio_hien_tai
    if not settings.bao_cao_nhac_tu_dong:
        return {"da_gui": 0, "tat": True}
    now = gio_hien_tai()
    if now.hour < settings.bao_cao_nhac_gio:
        return {"da_gui": 0, "chua_den_gio": True}
    return gui_nhac(db, now.date() - timedelta(days=1), "TU_DONG")
