"""⏰ Nhắc QUÁ HẠN hàng tuần vào nhóm Google Chat (vòng rà app 31/10/2026, mục A1 + A2; làm 01/11/2026).

Hai bản tin, thứ Hai từ 8h (giờ VN), mỗi tuần một lần (scheduler.py; mốc bền trong audit_log bang «nhac_qua_han»):
  1. 💸 CÔNG NỢ PHẢI THU QUÁ HẠN  → nhóm Duyệt chi (webhook riêng, hạn chế người xem) — hoặc nhóm riêng khai ở
     GCHAT_WEBHOOK_CONG_NO. Mốc quá hạn = «ngày TT tiếp theo» sales đã hẹn, chưa hẹn thì lấy hạn của khoản;
     bỏ khoản đã đánh dấu Hoàn thành / đã thu đủ (cùng luật với bảng Bán hàng › Công nợ khách).
  2. 🚚 PO ĐÃ DUYỆT QUÁ HẸN GIAO, CHƯA NHẬN ĐỦ → nhóm Purchasing Team (GCHAT_WEBHOOK_PURCHASING); chưa khai webhook
     đó thì gửi vào nhóm Duyệt chi để CEO vẫn thấy (ghi rõ trong tin).
  + (04/11/2026) 📄 ĐƠN BÁN CHƯA XUẤT HÓA ĐƠN quá 30 ngày (app/don_chua_xuat_hd.py) gộp vào CUỐI bản tin công nợ — có đơn
     mà không có công nợ quá hạn thì bản công nợ vẫn gửi (ghi «không có khoản nào quá hạn»).
Không ném lỗi ra ngoài: nhắn hỏng không được làm hỏng luồng nền. Chỉ đọc đúng cột cần (test chạy SQLite với bảng tối giản).
"""
from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .config import settings

TOI_DA_KHACH = 12          # số khách hàng liệt kê trong tin công nợ
TOI_DA_KHOAN_MOI_KHACH = 4
TOI_DA_PO = 25
BAC = ((1, 30, "1–30 ngày"), (31, 60, "31–60 ngày"), (61, 90, "61–90 ngày"), (91, 10 ** 6, "trên 90 ngày"))


def _vnd(v) -> str:
    try:
        f = float(v or 0)
    except (TypeError, ValueError):
        return str(v)
    return f"{f:,.0f}".replace(",", ".") + " đ"


def _dmy(d) -> str:
    return d.strftime("%d/%m/%Y") if d else "…"


def hom_nay_vn() -> date:
    from .nhac_viec_service import gio_hien_tai
    return gio_hien_tai().date()


def _bac(ngay: int) -> str:
    for a, b, ten in BAC:
        if a <= ngay <= b:
            return ten
    return BAC[-1][2]


# ---------------------------------------------------------------- số liệu
def cong_no_qua_han(db: Session, hom_nay: date | None = None) -> list[dict]:
    """Khoản PHẢI THU còn nợ, chưa đánh dấu Hoàn thành, mốc (ngày TT tiếp theo hoặc hạn) đã qua."""
    from .models import CongNo, DonHang, HoaDon, KhachHang, NhanVien
    hom_nay = hom_nay or hom_nay_vn()
    rows = (db.query(CongNo.id, CongNo.khach_hang_id, CongNo.hoa_don_id, CongNo.don_hang_id, CongNo.so_tien,
                     CongNo.da_thanh_toan, CongNo.han, CongNo.ngay_tt_tiep, CongNo.trang_thai, CongNo.nhac_trang_thai,
                     CongNo.so_ct, CongNo.ma_ban_ngoai)
            .filter(CongNo.loai == "PHAI_THU").all())
    chon = []
    for r in rows:
        con = float(r.so_tien or 0) - float(r.da_thanh_toan or 0)
        if con <= 0 or r.nhac_trang_thai == "XONG" or r.trang_thai == "THU_DU":
            continue
        moc = r.ngay_tt_tiep or r.han
        if not moc or moc >= hom_nay:
            continue
        chon.append((r, con, moc))
    if not chon:
        return []
    hd_ids = {r.hoa_don_id for r, _, _ in chon if r.hoa_don_id}
    hd = {}
    if hd_ids:
        hd = {h.id: h for h in db.query(HoaDon.id, HoaDon.so, HoaDon.don_hang_id, HoaDon.khach_hang_id)
              .filter(HoaDon.id.in_(hd_ids)).all()}
    dh_ids = {r.don_hang_id for r, _, _ in chon if r.don_hang_id} | {h.don_hang_id for h in hd.values() if h.don_hang_id}
    dh = {}
    if dh_ids:
        dh = {d.id: d for d in db.query(DonHang.id, DonHang.so, DonHang.khach_hang_id).filter(DonHang.id.in_(dh_ids)).all()}
    out = []
    for r, con, moc in chon:
        h = hd.get(r.hoa_don_id) if r.hoa_don_id else None
        d = dh.get(r.don_hang_id or (h.don_hang_id if h else None))
        kh_id = (d.khach_hang_id if d else None) or r.khach_hang_id or (h.khach_hang_id if h else None)
        so_ngay = (hom_nay - moc).days
        out.append({"id": r.id, "khach_hang_id": kh_id, "ma_ban": (d.so if d else None) or r.ma_ban_ngoai,
                    "so_hd": r.so_ct or (h.so if h else None), "con_lai": con, "moc": moc, "han": r.han,
                    "hen_tt": bool(r.ngay_tt_tiep), "qua_han_ngay": so_ngay, "bac": _bac(so_ngay)})
    kh_ids = {x["khach_hang_id"] for x in out if x["khach_hang_id"]}
    kh = {}
    if kh_ids:
        kh = {k.id: k for k in db.query(KhachHang.id, KhachHang.ten, KhachHang.nguoi_phu_trach)
              .filter(KhachHang.id.in_(kh_ids)).all()}
    nv_ids = {k.nguoi_phu_trach for k in kh.values() if k.nguoi_phu_trach}
    nv = {}
    if nv_ids:
        nv = dict(db.query(NhanVien.id, NhanVien.ho_ten).filter(NhanVien.id.in_(nv_ids)).all())
    for x in out:
        k = kh.get(x["khach_hang_id"])
        x["khach"] = (k.ten if k else None) or "— chưa gắn khách —"
        x["phu_trach"] = nv.get(k.nguoi_phu_trach) if (k and k.nguoi_phu_trach) else None
    out.sort(key=lambda x: (-x["qua_han_ngay"], -x["con_lai"]))
    return out


def po_qua_hen(db: Session, hom_nay: date | None = None) -> list[dict]:
    """PO ĐÃ DUYỆT, có ngày hẹn giao đã qua, chưa nhận đủ hàng."""
    from .models import AuditLog, DonHang, DonMua, DonMuaCt, HangHoa, NguoiDung, NhaCungCap, NhanVien
    hom_nay = hom_nay or hom_nay_vn()
    rows = (db.query(DonMua.id, DonMua.so, DonMua.nha_cung_cap_id, DonMua.ngay_hen_giao, DonMua.trang_thai_nhan,
                     DonMua.ma_ban, DonMua.don_hang_id, DonMua.ngay)
            .filter(DonMua.trang_thai == "DA_DUYET", DonMua.ngay_hen_giao.isnot(None), DonMua.ngay_hen_giao < hom_nay,
                    or_(DonMua.trang_thai_nhan.is_(None), DonMua.trang_thai_nhan != "DU")).all())
    if not rows:
        return []
    ids = [r.id for r in rows]
    ncc = dict(db.query(NhaCungCap.id, NhaCungCap.ten)
               .filter(NhaCungCap.id.in_({r.nha_cung_cap_id for r in rows if r.nha_cung_cap_id})).all()) \
        if any(r.nha_cung_cap_id for r in rows) else {}
    dh_ids = {r.don_hang_id for r in rows if r.don_hang_id}
    dh = dict(db.query(DonHang.id, DonHang.so).filter(DonHang.id.in_(dh_ids)).all()) if dh_ids else {}
    hang = {}
    for dmid, ten in (db.query(DonMuaCt.don_mua_id, HangHoa.ten).join(HangHoa, HangHoa.id == DonMuaCt.hang_hoa_id)
                      .filter(DonMuaCt.don_mua_id.in_(ids)).order_by(DonMuaCt.id).all()):
        hang.setdefault(dmid, []).append(ten or "")
    nguoi = {}
    try:
        tao = {}
        for bid, nd_id in (db.query(AuditLog.ban_ghi_id, AuditLog.nguoi_dung_id)
                           .filter(AuditLog.bang == "don_mua", AuditLog.ban_ghi_id.in_(ids), AuditLog.nguoi_dung_id.isnot(None))
                           .order_by(AuditLog.id.desc()).all()):
            tao[bid] = nd_id                                   # lặp giảm dần → phần tử cuối cùng là bản ghi ĐẦU tiên
        nd_ids = set(tao.values())
        if nd_ids:
            ten_nv = dict(db.query(NhanVien.nguoi_dung_id, NhanVien.ho_ten).filter(NhanVien.nguoi_dung_id.in_(nd_ids)).all())
            email = dict(db.query(NguoiDung.id, NguoiDung.email).filter(NguoiDung.id.in_(nd_ids)).all())
            nguoi = {bid: (ten_nv.get(n) or email.get(n)) for bid, n in tao.items()}
    except Exception:                                                    # noqa: BLE001
        nguoi = {}
    out = []
    for r in rows:
        hh = hang.get(r.id) or []
        out.append({"id": r.id, "so": r.so or f"PO #{r.id}", "ncc": ncc.get(r.nha_cung_cap_id) or "—",
                    "ma_ban": dh.get(r.don_hang_id) or r.ma_ban, "hen_giao": r.ngay_hen_giao,
                    "tre_ngay": (hom_nay - r.ngay_hen_giao).days,
                    "nhan": "nhận một phần" if r.trang_thai_nhan == "MOT_PHAN" else "chưa nhận",
                    "hang_hoa": (" · ".join(hh[:2]) + (f" +{len(hh) - 2}" if len(hh) > 2 else "")) if hh else None,
                    "nguoi_lap": nguoi.get(r.id)})
    out.sort(key=lambda x: (-x["tre_ngay"], x["so"]))
    return out


def bao_cao(db: Session, hom_nay: date | None = None) -> dict:
    hom_nay = hom_nay or hom_nay_vn()
    cn = cong_no_qua_han(db, hom_nay)
    po = po_qua_hen(db, hom_nay)
    try:
        from .don_chua_xuat_hd import qua_nguong
        dchd = qua_nguong(db, hom_nay)
    except Exception:                                                    # noqa: BLE001 — không để hỏng bản công nợ / PO
        db.rollback()
        dchd = []
    return {"hom_nay": hom_nay, "cong_no": cn, "tong_cong_no": sum(x["con_lai"] for x in cn), "po": po,
            "don_chua_hd": dchd, "tong_don_chua_hd": sum(x["tong"] for x in dchd)}


# ---------------------------------------------------------------- nội dung tin
def _nhan(hom_nay: date, nhan: str) -> str:
    return nhan or f"— tuần {hom_nay:%V/%Y} (tính đến {_dmy(hom_nay)})"


TOI_DA_DON_CHUA_HD = 20
_TT_DON = {"MOI": "Mới", "DANG_THUC_HIEN": "Đang thực hiện", "DA_XUAT": "Đã xuất kho"}


def _dmy_s(s) -> str:
    s = str(s or "")
    return f"{s[8:10]}/{s[5:7]}/{s[0:4]}" if len(s) >= 10 else "…"


def _khoi_don_chua_hd(ds: list[dict]) -> list[str]:
    """📄 Khối đơn bán chưa xuất hóa đơn quá ngưỡng — nối vào cuối bản tin công nợ."""
    from .don_chua_xuat_hd import NGUONG_NHAC_NGAY
    tong, da_thu, con = (sum(x[k] for x in ds) for k in ("tong", "da_thu", "con_phai_thu"))
    l = [f"📄 *ĐƠN BÁN CHƯA XUẤT HÓA ĐƠN quá {NGUONG_NHAC_NGAY} ngày*: *{len(ds)} đơn · {_vnd(tong)}* (gồm VAT) — "
         f"đã thu {_vnd(da_thu)} · còn phải thu {_vnd(con)}",
         "(chưa có hóa đơn nên chưa nằm trong công nợ phải thu; tính từ ngày đơn; bỏ đơn đầu tư – cho thuê và mã nội bộ OP / KHO)"]
    for x in ds[:TOI_DA_DON_CHUA_HD]:
        thu = (f" · đã thu {_vnd(x['da_thu'])}" + (f" ({x['nguon_da_thu']})" if x["nguon_da_thu"] else "")) if x["da_thu"] > 0 else ""
        hd = f" · ⚠ đã ghi số HĐ {x['so_hd_san']} nhưng trạng thái chưa đổi" if x["so_hd_san"] else ""
        l.append(f"   – *{x['so']}* · {x['khach'] or '— chưa gắn khách —'} · ngày {_dmy_s(x['ngay'])} → *{x['so_ngay']} ngày* · "
                 f"{_vnd(x['tong'])}{thu} · còn {_vnd(x['con_phai_thu'])} · {_TT_DON.get(x['trang_thai'], x['trang_thai'])}{hd}")
    if len(ds) > TOI_DA_DON_CHUA_HD:
        l.append(f"   … và {len(ds) - TOI_DA_DON_CHUA_HD} đơn khác — xem trong app")
    l.append("👉 App SVWS → Bán hàng → Công nợ khách → bảng «📄 Đơn chưa xuất hóa đơn»: xuất hóa đơn cho khách rồi nhập số HĐ "
             "và bấm «Đã xuất HĐ» (app mở công nợ, đơn rời bảng); đơn không còn bán thì xóa / sửa giá trị ở tab Đơn hàng.")
    return l


def noi_dung_cong_no(bc: dict, nhan: str = "") -> str | None:
    ds = bc["cong_no"]
    dchd = bc.get("don_chua_hd") or []
    if not ds and not dchd:
        return None
    hom_nay = bc["hom_nay"]
    l = [f"💸 *CÔNG NỢ PHẢI THU QUÁ HẠN* {_nhan(hom_nay, nhan)}"]
    if not ds:
        l.append("Không có khoản công nợ nào quá hạn 🎉")
        return "\n".join(l + [""] + _khoi_don_chua_hd(dchd))
    theo_bac = {}
    for x in ds:
        b = theo_bac.setdefault(x["bac"], [0, 0.0])
        b[0] += 1
        b[1] += x["con_lai"]
    tom = " · ".join(f"{ten}: {theo_bac[ten][0]} ({_vnd(theo_bac[ten][1])})" for _, _, ten in BAC if ten in theo_bac)
    l += [f"Tổng: *{len(ds)} khoản · {_vnd(bc['tong_cong_no'])}* — {tom}",
          "(mốc = ngày thanh toán tiếp theo đã hẹn với khách, chưa hẹn thì lấy hạn; đã đánh dấu Hoàn thành thì không nhắc)"]
    nhom = {}
    for x in ds:
        g = nhom.setdefault(x["khach"], {"khoan": [], "tong": 0.0, "phu_trach": x["phu_trach"], "lau": 0})
        g["khoan"].append(x)
        g["tong"] += x["con_lai"]
        g["lau"] = max(g["lau"], x["qua_han_ngay"])
    thu_tu = sorted(nhom.items(), key=lambda kv: (-kv[1]["tong"], -kv[1]["lau"]))
    for ten, g in thu_tu[:TOI_DA_KHACH]:
        pt = f" · phụ trách: {g['phu_trach']}" if g["phu_trach"] else ""
        l.append(f"🏢 *{ten}* — {len(g['khoan'])} khoản · {_vnd(g['tong'])} · lâu nhất {g['lau']} ngày{pt}")
        for x in g["khoan"][:TOI_DA_KHOAN_MOI_KHACH]:
            ma = x["ma_ban"] or "—"
            hd = f" · HĐ {x['so_hd']}" if x["so_hd"] else ""
            moc = ("hẹn TT " if x["hen_tt"] else "hạn ") + _dmy(x["moc"])
            l.append(f"   – {ma}{hd} · {_vnd(x['con_lai'])} · quá {x['qua_han_ngay']} ngày ({moc})")
        if len(g["khoan"]) > TOI_DA_KHOAN_MOI_KHACH:
            l.append(f"   … và {len(g['khoan']) - TOI_DA_KHOAN_MOI_KHACH} khoản khác của khách này")
    if len(thu_tu) > TOI_DA_KHACH:
        con = sum(len(g["khoan"]) for _, g in thu_tu[TOI_DA_KHACH:])
        l.append(f"… và {len(thu_tu) - TOI_DA_KHACH} khách khác ({con} khoản) — xem trong app")
    l.append("👉 App SVWS → Bán hàng → Công nợ khách: ghi ngày TT tiếp theo đã hẹn hoặc đánh dấu Hoàn thành để ngừng nhắc.")
    if dchd:
        l += [""] + _khoi_don_chua_hd(dchd)
    return "\n".join(l)


def noi_dung_po(bc: dict, nhan: str = "", ghi_chu_nhom: str = "") -> str | None:
    ds = bc["po"]
    if not ds:
        return None
    hom_nay = bc["hom_nay"]
    chua = sum(1 for x in ds if x["nhan"] == "chưa nhận")
    l = [f"🚚 *PO QUÁ HẸN GIAO, CHƯA NHẬN ĐỦ HÀNG* {_nhan(hom_nay, nhan)}",
         f"Tổng: *{len(ds)} PO* — chưa nhận: {chua} · nhận một phần: {len(ds) - chua} · trễ lâu nhất {ds[0]['tre_ngay']} ngày"]
    if ghi_chu_nhom:
        l.append(ghi_chu_nhom)
    for x in ds[:TOI_DA_PO]:
        ma = f" · mã {x['ma_ban']}" if x["ma_ban"] else ""
        hh = f" · {x['hang_hoa']}" if x["hang_hoa"] else ""
        nl = f" · lập: {x['nguoi_lap']}" if x["nguoi_lap"] else ""
        l.append(f"   – *{x['so']}* · {x['ncc']}{ma} · hẹn {_dmy(x['hen_giao'])} → trễ *{x['tre_ngay']} ngày* · {x['nhan']}{hh}{nl}")
    if len(ds) > TOI_DA_PO:
        l.append(f"   … và {len(ds) - TOI_DA_PO} PO khác — xem trong app")
    l.append("👉 App SVWS → Nhà cung cấp → Đơn mua (PO): nhận hàng, hoặc sửa ngày hẹn giao theo xác nhận mới của NCC; "
             "PO không còn giao nữa thì đóng / hủy để khỏi nhắc.")
    return "\n".join(l)


# ---------------------------------------------------------------- nơi gửi + gửi
def noi_gui() -> dict:
    """Webhook thực dùng cho từng bản tin + tên nhóm hiển thị (không lộ đường dẫn)."""
    dc = (settings.gchat_webhook_duyet_chi or "").strip()
    cn = (settings.gchat_webhook_cong_no or "").strip() or dc
    pur = (settings.gchat_webhook_purchasing or "").strip()
    return {"cong_no": cn, "cong_no_nhom": ("nhóm riêng Công nợ" if (settings.gchat_webhook_cong_no or "").strip()
                                             else "nhóm Duyệt chi") if cn else "",
            "po": pur or dc, "po_nhom": "nhóm Purchasing Team" if pur else ("nhóm Duyệt chi (chưa khai GCHAT_WEBHOOK_PURCHASING)"
                                                                            if dc else "")}


def gui_tuan(db: Session, nguon: str = "TU_DONG", nguoi=None) -> dict:
    """Gửi cả hai bản tin. Mỗi bản độc lập: thiếu dữ liệu → bỏ qua, thiếu webhook → ghi lý do. Không ném lỗi."""
    from .chat_gateway import gui_webhook_rieng
    kq = {"nguon": nguon, "cong_no": {"da_gui": False}, "po": {"da_gui": False}}
    try:
        bc = bao_cao(db)
        kq["so_cong_no"], kq["tong_cong_no"], kq["so_po"] = len(bc["cong_no"]), bc["tong_cong_no"], len(bc["po"])
        kq["so_don_chua_hd"] = len(bc["don_chua_hd"])
        ng = noi_gui()
        duoi = f" (gửi tay bởi {nguoi})" if nguoi else ""
        nd_cn = noi_dung_cong_no(bc)
        if not nd_cn:
            kq["cong_no"]["ly_do"] = "Không có công nợ phải thu quá hạn (và không có đơn chưa xuất hóa đơn quá 30 ngày)"
        elif not ng["cong_no"]:
            kq["cong_no"]["ly_do"] = "Chưa cấu hình GCHAT_WEBHOOK_DUYET_CHI (hoặc GCHAT_WEBHOOK_CONG_NO)"
        else:
            r = gui_webhook_rieng(ng["cong_no"], nd_cn + duoi)
            kq["cong_no"] = {"da_gui": bool(r.get("da_gui")), "loi": r.get("loi"), "nhom": ng["cong_no_nhom"]}
        ghi = ("_(gửi vào nhóm Duyệt chi vì chưa khai webhook nhóm Purchasing Team)_"
               if ng["po"] and not (settings.gchat_webhook_purchasing or "").strip() else "")
        nd_po = noi_dung_po(bc, ghi_chu_nhom=ghi)
        if not nd_po:
            kq["po"]["ly_do"] = "Không có PO quá hẹn giao"
        elif not ng["po"]:
            kq["po"]["ly_do"] = "Chưa cấu hình GCHAT_WEBHOOK_PURCHASING (và cũng chưa có GCHAT_WEBHOOK_DUYET_CHI)"
        else:
            r = gui_webhook_rieng(ng["po"], nd_po + duoi)
            kq["po"] = {"da_gui": bool(r.get("da_gui")), "loi": r.get("loi"), "nhom": ng["po_nhom"]}
        kq["da_gui"] = bool(kq["cong_no"].get("da_gui") or kq["po"].get("da_gui"))
    except Exception as e:                                               # noqa: BLE001
        kq["loi"] = f"{type(e).__name__}: {str(e)[:150]}"
        kq["da_gui"] = False
    return kq
