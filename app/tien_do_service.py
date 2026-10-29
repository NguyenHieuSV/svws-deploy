"""⏱ % TIẾN ĐỘ công việc trong báo cáo ngày (Working time & Report) — anh Hiếu 29/10/2026.

• Mỗi báo cáo ngày BẮT BUỘC nhập % tiến độ (0–100) của việc đang báo cáo (bao_cao_ngay.tien_do).
• Việc được giao (giao_viec) giữ % MỚI NHẤT = tiến độ của báo cáo có NGÀY gần nhất gắn việc. Đạt 100% lần đầu →
  hoan_thanh_luc + nhắn người giao việc (APP: riêng người giao; WEBHOOK: phòng chung). Tụt lại dưới 100 → bỏ mốc.
• Tiến độ THEO THỜI GIAN = (ngày thứ i / tổng số ngày của việc) × 100, tính cả ngày đầu và ngày cuối.
  Báo cáo thấp hơn mức này từ `tien_do_lech_diem` điểm (mặc định 20), hoặc quá hạn mà chưa 100% → «chậm»:
  cảnh báo ngay khi gửi báo cáo, và bộ hẹn giờ nhắc mỗi sáng (từ bao_cao_nhac_gio, trừ Chủ nhật) — mỗi việc mỗi ngày
  MỘT tin (mốc giao_viec.nhac_lech_ngay nên khởi động lại máy chủ không nhắn trùng). Việc quá hạn trên 14 ngày thôi nhắc.
"""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from .config import settings
from .models import BaoCaoNgay, GiaoViec, NguoiDung, NhanVien

QUA_HAN_THOI_NHAC = 14      # ngày — việc quá hạn lâu hơn ngần này không nhắc tự động nữa (CEO xử lý tay)


def dmy(d) -> str:
    return d.strftime("%d/%m/%Y") if d else "…"


def nguong_lech() -> float:
    try:
        return float(settings.tien_do_lech_diem)
    except (TypeError, ValueError, AttributeError):
        return 20.0


def _g(v) -> str:
    """Số gọn: 33.3 → '33,3' · 100.0 → '100'."""
    return f"{float(v):g}".replace(".", ",")


def tien_do_theo_thoi_gian(bd, kt, ngay):
    """% kỳ vọng theo thời gian tại `ngay`; thiếu ngày bắt đầu / kết thúc → None.
    Trước ngày bắt đầu → 0; từ ngày kết thúc trở đi → 100."""
    if bd is None or kt is None or ngay is None or kt < bd:
        return None
    if ngay < bd:
        return 0.0
    if ngay >= kt:
        return 100.0
    tong = (kt - bd).days + 1
    return round(100.0 * ((ngay - bd).days + 1) / tong, 1)


def ngay_thu(bd, kt, ngay):
    """→ (ngày thứ i của việc tại `ngay`, tổng số ngày) — (None, None) nếu thiếu ngày."""
    if bd is None or kt is None or ngay is None or kt < bd:
        return None, None
    tong = (kt - bd).days + 1
    return max(1, min((ngay - bd).days + 1, tong)), tong


def danh_gia(tien_do, bd, kt, ngay) -> dict:
    """So % báo cáo với % theo thời gian tại `ngay`.
    → {tien_do, ky_vong, lech (báo − kỳ vọng), cham, qua_han, ngay_thu, tong_ngay, nhan}."""
    td = float(tien_do) if tien_do is not None else None
    kv = tien_do_theo_thoi_gian(bd, kt, ngay)
    i, tong = ngay_thu(bd, kt, ngay)
    out = {"tien_do": td, "ky_vong": kv, "lech": None, "cham": False, "qua_han": False,
           "ngay_thu": i, "tong_ngay": tong, "nhan": ""}
    if td is not None and td >= 100:
        out["nhan"] = "✅ hoàn thành"
        return out
    if kv is None:
        out["nhan"] = "chưa so được (việc không có ngày bắt đầu / kết thúc)" if td is not None else ""
        return out
    t0 = td if td is not None else 0.0
    out["lech"] = round(t0 - kv, 1)
    out["qua_han"] = bool(kt is not None and ngay > kt)
    out["cham"] = out["qua_han"] or (kv - t0) >= nguong_lech()
    if out["qua_han"]:
        out["nhan"] = f"⚠ quá hạn {(ngay - kt).days} ngày, mới {_g(t0)}%" if td is not None else f"⚠ quá hạn {(ngay - kt).days} ngày, chưa báo tiến độ"
    elif out["cham"]:
        out["nhan"] = f"⏳ chậm {_g(kv - t0)} điểm so với thời gian ({_g(kv)}%)" + ("" if td is not None else ", chưa báo tiến độ")
    else:
        out["nhan"] = f"đúng tiến độ (theo thời gian {_g(kv)}%)"
    return out


def canh_bao_khi_gui(r: BaoCaoNgay, g) -> str | None:
    """Cảnh báo trả về NGAY khi gửi báo cáo gắn việc (None = không có gì đáng nhắc)."""
    if g is None or r.tien_do is None:
        return None
    dg = danh_gia(r.tien_do, g.bat_dau, g.ket_thuc, r.ngay)
    if not dg["cham"]:
        return None
    td = float(r.tien_do)
    if dg["qua_han"]:
        return (f"⚠ Việc «{g.ten_cong_viec}» đã quá hạn {dmy(g.ket_thuc)} ({(r.ngay - g.ket_thuc).days} ngày) mà tiến độ mới "
                f"{_g(td)}% — nêu rõ khó khăn và kế hoạch hoàn thành để người giao việc nắm.")
    return (f"⏳ Tiến độ {_g(td)}% thấp hơn tiến độ theo thời gian {_g(dg['ky_vong'])}% "
            f"(ngày {dg['ngay_thu']}/{dg['tong_ngay']} của việc «{g.ten_cong_viec}», chậm {_g(dg['ky_vong'] - td)} điểm) — "
            "nêu rõ khó khăn và kế hoạch bù trong báo cáo.")


def cap_nhat_giao_viec(db: Session, g: GiaoViec, luc) -> dict:
    """Sau khi lưu / sửa / xóa báo cáo gắn việc: g.tien_do = tiến độ của báo cáo có NGÀY gần nhất gắn việc.
    Đạt 100% lần đầu → hoan_thanh_luc = `luc` (vua_100 = True → gọi thong_bao_hoan_thanh sau khi commit);
    tụt dưới 100 → bỏ mốc (hoàn thành lại sẽ báo lại). → {tien_do, vua_100, ngay}"""
    r = (db.query(BaoCaoNgay).filter(BaoCaoNgay.giao_viec_id == g.id, BaoCaoNgay.tien_do.isnot(None))
         .order_by(BaoCaoNgay.ngay.desc(), BaoCaoNgay.id.desc()).first())
    td = float(r.tien_do) if r is not None else None
    g.tien_do = Decimal(str(round(td, 1))) if td is not None else None
    vua_100 = False
    if td is not None and td >= 100:
        if g.hoan_thanh_luc is None:
            g.hoan_thanh_luc = luc
            vua_100 = True
    else:
        g.hoan_thanh_luc = None
    db.flush()
    return {"tien_do": td, "vua_100": vua_100, "ngay": r.ngay if r is not None else None}


def _ten_nguoi_dung(db: Session, u) -> str:
    if u is None:
        return "CEO"
    nv = db.query(NhanVien).filter(NhanVien.nguoi_dung_id == u.id).first()
    return (nv.ho_ten if nv is not None and nv.ho_ten else None) or getattr(u, "ho_ten", None) or u.email or "CEO"


def noi_dung_hoan_thanh(g, nv: NhanVien, ngay, nguoi_giao: str) -> str:
    som = ""
    if g.ket_thuc and ngay:
        d = (g.ket_thuc - ngay).days
        som = " (đúng hạn)" if d == 0 else (f" (sớm {d} ngày)" if d > 0 else f" (trễ {-d} ngày)")
    ma = f"• Mã dự án: {g.ma_du_an}\n" if getattr(g, "ma_du_an", None) else ""
    return (f"✅ {nv.ho_ten} báo HOÀN THÀNH 100% việc: *{g.ten_cong_viec}*\n"
            f"• Thời gian giao: {dmy(g.bat_dau)} → {dmy(g.ket_thuc)}\n{ma}"
            f"• Ngày báo cáo hoàn thành: {dmy(ngay)}{som}\n• Người giao: {nguoi_giao}\n"
            "Xem báo cáo ở app SVWS → Working time & Report → Report.")


def thong_bao_hoan_thanh(db: Session, g, nv: NhanVien, ngay) -> dict:
    """Nhắn khi việc đạt 100%: APP → riêng người giao việc (không có → phòng chung); WEBHOOK → phòng chung.
    Không bao giờ ném lỗi (báo cáo vẫn lưu dù nhắn hỏng)."""
    from .chat_gateway import dang_bat, lay_chat_provider
    from .nhac_viec_service import gui_toi_nguoi
    kq = {"da_gui": False, "kieu": None, "loi": None}
    try:
        if not dang_bat():
            kq["loi"] = "Google Chat chưa bật trên máy chủ (chế độ DEMO)"
            return kq
        prov = lay_chat_provider()
        rieng = getattr(prov, "che_do", "") == "APP"
        u = db.get(NguoiDung, g.nguoi_giao) if g.nguoi_giao else None
        nd_ = noi_dung_hoan_thanh(g, nv, ngay, _ten_nguoi_dung(db, u))
        if rieng and u is not None and u.email:
            kq["kieu"] = "RIENG"
            r = gui_toi_nguoi(db, prov, u.email, nd_)
        else:
            kq["kieu"] = "PHONG_CHUNG"
            r = prov.gui_phong(nd_)
        kq["da_gui"] = bool(r.get("da_gui"))
        kq["loi"] = None if kq["da_gui"] else str(r.get("loi") or "không gửi được")
    except Exception as e:                                              # noqa: BLE001
        kq["loi"] = f"{type(e).__name__}: {str(e)[:120]}"
    return kq


# ---------------- nhắc việc CHẬM TIẾN ĐỘ so với thời gian ----------------
def ds_cham_tien_do(db: Session, hom_nay: date) -> list:
    """Việc đang chậm tại `hom_nay`: đã bắt đầu, có ngày bắt đầu + kết thúc, chưa 100%, người nhận đang làm;
    quá hạn chưa xong cũng tính (tối đa QUA_HAN_THOI_NHAC ngày sau hạn)."""
    out = []
    q = (db.query(GiaoViec, NhanVien).join(NhanVien, NhanVien.id == GiaoViec.nhan_vien_id)
         .filter(GiaoViec.bat_dau.isnot(None), GiaoViec.ket_thuc.isnot(None), GiaoViec.bat_dau <= hom_nay))
    for g, nv in q.order_by(GiaoViec.ket_thuc, GiaoViec.id).all():
        if g.tien_do is not None and float(g.tien_do) >= 100:
            continue
        if getattr(nv, "trang_thai", "DANG_LAM") != "DANG_LAM":
            continue
        if hom_nay > g.ket_thuc + timedelta(days=QUA_HAN_THOI_NHAC):
            continue
        dg = danh_gia(g.tien_do, g.bat_dau, g.ket_thuc, hom_nay)
        if not dg["cham"]:
            continue
        u = db.get(NguoiDung, nv.nguoi_dung_id) if nv.nguoi_dung_id else None
        out.append({"giao_viec_id": g.id, "nhan_vien_id": nv.id, "ho_ten": nv.ho_ten,
                    "email": (u.email if u is not None else None) or g.email,
                    "ten_cong_viec": g.ten_cong_viec, "ma_du_an": g.ma_du_an,
                    "bat_dau": str(g.bat_dau), "ket_thuc": str(g.ket_thuc),
                    "tien_do": dg["tien_do"], "ky_vong": dg["ky_vong"], "lech": dg["lech"], "qua_han": dg["qua_han"],
                    "ngay_thu": dg["ngay_thu"], "tong_ngay": dg["tong_ngay"], "nhan": dg["nhan"],
                    "da_nhac_hom_nay": g.nhac_lech_ngay == hom_nay,
                    "co_tai_khoan": bool(nv.nguoi_dung_id)})
    return out


def _dong_cham(x: dict) -> str:
    bao = f"{_g(x['tien_do'])}%" if x["tien_do"] is not None else "chưa báo tiến độ"
    tg = (f"quá hạn {dmy(date.fromisoformat(x['ket_thuc']))}" if x["qua_han"]
          else f"ngày {x['ngay_thu']}/{x['tong_ngay']}, theo thời gian {_g(x['ky_vong'])}%")
    return f"«{x['ten_cong_viec']}»{(' · ' + x['ma_du_an']) if x.get('ma_du_an') else ''}: {tg} · báo {bao}"


def noi_dung_cham_rieng(x: dict) -> str:
    return (f"⏳ Tiến độ việc của bạn đang chậm so với thời gian\n• {_dong_cham(x)}\n"
            f"• Thời gian giao: {dmy(date.fromisoformat(x['bat_dau']))} → {dmy(date.fromisoformat(x['ket_thuc']))}\n"
            "Vui lòng cập nhật % tiến độ, khó khăn và kế hoạch bù trong báo cáo ngày (app SVWS → Working time & Report → Report).")


def noi_dung_cham_chung(ds: list) -> str:
    dong = "\n".join(f"• {x['ho_ten']} — {_dong_cham(x)}" for x in ds)
    return (f"⏳ Việc đang CHẬM TIẾN ĐỘ so với thời gian — {len(ds)} việc:\n{dong}\n"
            "Các bạn vui lòng cập nhật % tiến độ, khó khăn và kế hoạch bù trong báo cáo ngày (app SVWS → Working time & Report → Report).")


def nhac_cham_tien_do(db: Session, hom_nay: date | None = None, nguon: str = "TU_DONG") -> dict:
    """Nhắc việc chậm tiến độ — mỗi việc mỗi ngày MỘT lần (giao_viec.nhac_lech_ngay), chỉ người có tài khoản.
    APP: tin riêng từng người nhận việc. WEBHOOK (chỉ đăng phòng chung): MỘT tin gộp ghi tên.
    → {ngay, cham, da_gui, da_nhac_truoc, khong_tai_khoan, loi, kieu, ten, nguon}"""
    from .chat_gateway import dang_bat, lay_chat_provider
    from .nhac_viec_service import gui_toi_nguoi, ngay_hien_tai
    hom_nay = hom_nay or ngay_hien_tai()
    tong = {"ngay": str(hom_nay), "cham": 0, "da_gui": 0, "da_nhac_truoc": 0, "khong_tai_khoan": 0, "loi": [],
            "kieu": None, "ten": [], "nguon": nguon}
    ds = ds_cham_tien_do(db, hom_nay)
    tong["cham"] = len(ds)
    chon = [x for x in ds if not x["da_nhac_hom_nay"] and x["co_tai_khoan"]]
    tong["da_nhac_truoc"] = sum(1 for x in ds if x["da_nhac_hom_nay"])
    tong["khong_tai_khoan"] = sum(1 for x in ds if not x["co_tai_khoan"])
    if not chon:
        return tong
    if not dang_bat():
        tong["loi"].append("Google Chat chưa được bật trên máy chủ (đang ở chế độ DEMO) nên chưa gửi được.")
        return tong
    prov = lay_chat_provider()
    rieng = getattr(prov, "che_do", "") == "APP"
    tong["kieu"] = "RIENG" if rieng else "PHONG_CHUNG"

    def danh_dau(x):
        g = db.get(GiaoViec, x["giao_viec_id"])
        if g is not None:
            g.nhac_lech_ngay = hom_nay

    if not rieng:
        try:
            kq = prov.gui_phong(noi_dung_cham_chung(chon))
        except Exception as e:                                          # noqa: BLE001
            kq = {"da_gui": False, "loi": f"{type(e).__name__}: {str(e)[:120]}"}
        if kq.get("da_gui"):
            for x in chon:
                danh_dau(x)
            tong["da_gui"] = len(chon)
            tong["ten"] = [x["ho_ten"] for x in chon]
        else:
            tong["loi"].append(str(kq.get("loi") or "không gửi được vào phòng chung"))
        db.commit()
        return tong
    for x in chon:
        try:
            kq = gui_toi_nguoi(db, prov, x["email"], noi_dung_cham_rieng(x))
        except Exception as e:                                          # noqa: BLE001
            kq = {"da_gui": False, "loi": f"{type(e).__name__}: {str(e)[:120]}"}
        if kq.get("da_gui"):
            danh_dau(x)
            tong["da_gui"] += 1
            tong["ten"].append(x["ho_ten"])
        else:
            tong["loi"].append(f"{x['ho_ten']}: {kq.get('loi') or 'không gửi được'}")
    db.commit()
    return tong
