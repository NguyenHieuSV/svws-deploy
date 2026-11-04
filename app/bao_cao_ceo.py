"""📋 BÁO CÁO CEO — bản TUẦN (anh Hiếu chốt 04/11/2026): một trang gom số của cả công ty, ba tầng:
  ① 12 chỉ số sức khỏe (Tiền · Lãi · Nợ · Vận hành · Con người), chỉ số nào so được thì kèm kỳ trước;
  ② «Việc cần CEO quyết» = mọi ngoại lệ đang treo trong app, kèm nơi xử lý (trang + tab);
  ③ sáu khối theo nhóm menu: Thương mại · Cung ứng · Dịch vụ · Tài chính · Nội bộ · Tuân thủ.

KHÔNG tính lại công thức nào — gọi đúng hàm của từng module đang dùng: Overall Financial (số dư ngân hàng, Lãi/Lỗ Record,
ngân sách thực thu / thực chi), Kiểm soát lợi nhuận (kiem_soat_ln), nhắc quá hạn (nhac_qua_han), đơn chưa xuất hóa đơn
(don_chua_xuat_hd), việc kế toán treo (ke_toan_quy), tạm ứng mua hàng, kho, báo cáo ngày, tiến độ, sao lưu, sao kê.
Mỗi phần bọc try/except: phần nào hỏng ghi vào `loi`, các phần khác vẫn ra số (không bao giờ trắng trang).

Nơi dùng: Overall Financial › tab 📋 Báo cáo CEO (chỉ CEO; API /tai-chinh/bao-cao-ceo/tuan?lui=n, n tuần lùi) và tin Google
Chat thứ Hai 8h (scheduler, mốc bền audit_log bang «bao_cao_ceo» / TUAN) vào nhóm CEO (GCHAT_WEBHOOK_CEO) — chưa khai thì
nhóm Duyệt chi. Tin tuần là bản TÓM TẮT; ba tin chi tiết (📉 lợi nhuận · ⏰ quá hạn · 🚚 PO) vẫn gửi cho nhóm làm việc.
"""
from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import settings

NGAY_SAP_TOI = 30            # «30 ngày tới» cho phải thu / phải chi
TOI_DA_QUYET_TIN = 8         # số việc cần quyết liệt kê trong tin Chat
SAO_LUU_TRE_GIO = 30         # sao lưu gần nhất cách quá số giờ này → cảnh báo
_DON_DANG_LAM = ("MOI", "DANG_THUC_HIEN", "DA_XUAT")
_MUC_THU_TU = {"Cao": 0, "Vừa": 1, "Thấp": 2}


# ---------------------------------------------------------------- tiện ích
def _f(v) -> float:
    return float(v or 0)


def _tr(v) -> str:
    """Số tiền gọn cho tin Chat / dòng chữ: 1,23 tỷ · 450 tr · 12.500 đ."""
    f = _f(v)
    a = abs(f)
    if a >= 1e9:
        return f"{f / 1e9:.2f}".replace(".", ",") + " tỷ"
    if a >= 1e6:
        return f"{f / 1e6:,.0f}".replace(",", ".") + " tr"
    return f"{f:,.0f}".replace(",", ".") + " đ"


def _dmy_s(s) -> str:
    s = str(s or "")
    return f"{s[8:10]}/{s[5:7]}/{s[0:4]}" if len(s) >= 10 else "…"


def _dm_s(s) -> str:
    s = str(s or "")
    return f"{s[8:10]}/{s[5:7]}" if len(s) >= 10 else "…"


def hom_nay_vn() -> date:
    from .nhac_viec_service import gio_hien_tai
    return gio_hien_tai().date()


def ky_tuan(hom_nay: date, lui: int = 0) -> dict:
    """Tuần ISO (thứ Hai → Chủ nhật) chứa `hom_nay`, lùi `lui` tuần; kèm tuần liền trước để so."""
    lui = max(int(lui or 0), 0)
    tu = hom_nay - timedelta(days=hom_nay.weekday() + 7 * lui)
    den = tu + timedelta(days=6)
    t_tu = tu - timedelta(days=7)
    return {"tu": tu, "den": den, "den_hieu_luc": min(den, hom_nay), "nhan": f"Tuần {tu:%V/%G}",
            "truoc_tu": t_tu, "truoc_den": tu - timedelta(days=1), "truoc_nhan": f"Tuần {t_tu:%V/%G}",
            "hom_nay": hom_nay, "hien_tai": lui == 0, "lui": lui}


# ---------------------------------------------------------------- từng phần số liệu
def _thu_chi(db: Session, tu: date, den: date) -> tuple[float, float]:
    """(tiền khách trả, tiền trả NCC) trong [tu, den] — theo thanh toán công nợ, cùng cách tính «Ngân sách vs thực tế»."""
    from .models import CongNo, ThanhToan

    def s(loai):
        return _f(db.query(func.coalesce(func.sum(ThanhToan.so_tien), 0))
                  .join(CongNo, ThanhToan.cong_no_id == CongNo.id)
                  .filter(CongNo.loai == loai, ThanhToan.ngay >= tu, ThanhToan.ngay <= den).scalar())
    return s("PHAI_THU"), s("PHAI_TRA")


def _p_tien(db: Session, ky: dict) -> dict:
    from .models import BankTaiKhoan, CongNo, LenhChiBank, TaiKhoanQuy
    from .routers.tai_chinh import _btk_so_du
    hn = ky["hom_nay"]
    nh = sum(_btk_so_du(db, t)[2] for t in db.query(BankTaiKhoan).all())
    tm = _f(db.query(func.coalesce(func.sum(TaiKhoanQuy.so_du), 0))
            .filter(TaiKhoanQuy.loai == "TIEN_MAT", TaiKhoanQuy.hoat_dong.is_(True)).scalar())
    vao, ra = _thu_chi(db, ky["tu"], ky["den"])
    vao_t, ra_t = _thu_chi(db, ky["truoc_tu"], ky["truoc_den"])
    moc = hn + timedelta(days=NGAY_SAP_TOI)
    con = CongNo.so_tien - CongNo.da_thanh_toan
    lenh = _f(db.query(func.coalesce(func.sum(LenhChiBank.so_tien), 0)).filter(LenhChiBank.trang_thai == "DA_DUYET").scalar())
    tra_30 = _f(db.query(func.coalesce(func.sum(con), 0))
                .filter(CongNo.loai == "PHAI_TRA", CongNo.trang_thai != "THU_DU", con > 0,
                        CongNo.han.isnot(None), CongNo.han >= hn, CongNo.han <= moc).scalar())
    thu_30 = 0.0
    n_thu_30 = 0
    for r in (db.query(CongNo.so_tien, CongNo.da_thanh_toan, CongNo.han, CongNo.ngay_tt_tiep, CongNo.nhac_trang_thai)
              .filter(CongNo.loai == "PHAI_THU", CongNo.trang_thai != "THU_DU").all()):
        c = _f(r.so_tien) - _f(r.da_thanh_toan)
        m = r.ngay_tt_tiep or r.han
        if c > 0 and r.nhac_trang_thai != "XONG" and m and hn <= m <= moc:
            thu_30 += c
            n_thu_30 += 1
    return {"ngan_hang": nh, "tien_mat": tm, "hien_co": nh + tm, "vao": vao, "ra": ra, "vao_truoc": vao_t, "ra_truoc": ra_t,
            "lenh_cho_chi": lenh, "tra_30": tra_30, "phai_chi_30": lenh + tra_30, "thu_30": thu_30, "n_thu_30": n_thu_30}


def _don_trong_ky(db: Session, tu: date, den: date) -> tuple[int, float]:
    """Đơn bán chốt (ngày đơn) trong kỳ — bỏ đơn đầu tư và mã nội bộ; giá trị CHƯA VAT."""
    from .kiem_soat_ln import mien_kiem
    from .models import DonHang
    rows = [r for r in db.query(DonHang.so, DonHang.tong_tien, DonHang.loai_don)
            .filter(DonHang.ngay >= tu, DonHang.ngay <= den).all()
            if (r.loai_don or "THUONG").upper() != "DAU_TU" and not (r.so and mien_kiem(r.so))]
    return len(rows), sum(_f(r.tong_tien) for r in rows)


def _p_lai(db: Session, ky: dict) -> dict:
    from .models import LaiLoRecord
    n, gt = _don_trong_ky(db, ky["tu"], ky["den"])
    n_t, gt_t = _don_trong_ky(db, ky["truoc_tu"], ky["truoc_den"])
    out = {"don_n": n, "don_gt": gt, "don_n_truoc": n_t, "don_gt_truoc": gt_t, "gia_uoc": []}
    try:                                                     # Lãi/Lỗ Record — cùng hàm Overall Financial dùng
        from .routers.tai_chinh import _tinh_lai_lo_tong
        t = _tinh_lai_lo_tong(db)
        thang = [x for x in ((t.get("nhan_su") or {}).get("theo_thang") or []) if _f(x.get("tong"))]
        out.update({"doanh_thu_nam": _f(t["doanh_thu"]), "lai_gop": _f(t["lai_gop"]), "lai_lo": _f(t["lai_lo"]),
                    "chi_nhan_su": _f(t["chi_nhan_su"]), "chi_phi_khac": _f(t["chi_phi_khac"]),
                    "bien": round(_f(t["lai_gop"]) / _f(t["doanh_thu"]) * 100, 1) if _f(t["doanh_thu"]) else None,
                    "ns_thang": thang[-1]["thang"] if thang else None,
                    "ns_thang_tong": _f(thang[-1]["tong"]) if thang else 0.0})
    except Exception as e:                                   # noqa: BLE001
        db.rollback()
        out["loi_lai_lo"] = f"{type(e).__name__}: {str(e)[:100]}"
    r = db.query(LaiLoRecord).filter(LaiLoRecord.ngay <= ky["truoc_den"]).order_by(LaiLoRecord.ngay.desc()).first()
    if r is not None:
        out.update({"lai_lo_truoc": _f(r.lai_lo), "lai_gop_truoc": _f(r.lai_gop), "doanh_thu_truoc": _f(r.doanh_thu),
                    "ngay_truoc": str(r.ngay)})
    try:                                                     # 📉 Kiểm soát lợi nhuận theo nhóm mã
        from .kiem_soat_ln import bao_cao_tuan as _ks
        ks = _ks(db, ky["hom_nay"])
        out.update({"so_lo": len(ks["lo"]), "so_bien_thap": len(ks["bien_thap"]), "so_chua_dt": len(ks["chua_dt"]),
                    "so_tut_bien": len(ks.get("tut_bien") or []), "gia_uoc": list(ks.get("gia_uoc") or []),
                    "nguong": ks["nguong"], "lo_tong": sum(o["cp"] - o["dt"] for o in ks["lo"]),
                    "lo_top": [{"nhom": o["nhom"], "lo": o["cp"] - o["dt"]} for o in ks["lo"][:3]]})
    except Exception as e:                                   # noqa: BLE001
        db.rollback()
        out["loi_kiem_soat"] = f"{type(e).__name__}: {str(e)[:100]}"
    return out


def _top_khach(qh: list, n: int = 3) -> list[dict]:
    g = {}
    for x in qh:
        g[x["khach"]] = g.get(x["khach"], 0.0) + x["con_lai"]
    return [{"khach": k, "tong": v} for k, v in sorted(g.items(), key=lambda kv: -kv[1])[:n]]


def _p_no(db: Session, ky: dict) -> dict:
    from .don_chua_xuat_hd import NGUONG_NHAC_NGAY, danh_sach
    from .models import CongNo
    from .nhac_qua_han import cong_no_qua_han
    hn = ky["hom_nay"]
    con = CongNo.so_tien - CongNo.da_thanh_toan

    def tong(loai):
        return _f(db.query(func.coalesce(func.sum(con), 0))
                  .filter(CongNo.loai == loai, CongNo.trang_thai != "THU_DU", con > 0).scalar())
    out = {"phai_thu": tong("PHAI_THU"), "phai_tra": tong("PHAI_TRA")}
    qh = cong_no_qua_han(db, hn)
    qh60 = [x for x in qh if x["qua_han_ngay"] > 60]
    out.update({"qh_n": len(qh), "qh_tong": sum(x["con_lai"] for x in qh), "qh_60_n": len(qh60),
                "qh_60_tong": sum(x["con_lai"] for x in qh60), "qh_top": _top_khach(qh)})
    tra_qh = (db.query(CongNo.so_tien, CongNo.da_thanh_toan)
              .filter(CongNo.loai == "PHAI_TRA", CongNo.trang_thai != "THU_DU", con > 0,
                      CongNo.han.isnot(None), CongNo.han < hn).all())
    out.update({"tra_qh_n": len(tra_qh), "tra_qh_tong": sum(_f(a) - _f(b) for a, b in tra_qh)})
    ds = danh_sach(db, hn)
    qn = [x for x in ds if x["qua_nguong"]]
    out.update({"dchd_n": len(ds), "dchd_con": sum(x["con_phai_thu"] for x in ds), "dchd_qn_n": len(qn),
                "dchd_qn_tong": sum(x["tong"] for x in qn), "dchd_nguong": NGUONG_NHAC_NGAY})
    return out


def _p_van_hanh(db: Session, ky: dict) -> dict:
    from .kiem_soat_ln import mien_kiem
    from .models import BaoGiaForm, CoHoi, DonHang, DonMua, HopDongThue
    from .nhac_qua_han import po_qua_hen
    hn = ky["hom_nay"]
    rows = [r for r in db.query(DonHang.so, DonHang.tong_tien, DonHang.loai_don)
            .filter(DonHang.trang_thai.in_(_DON_DANG_LAM)).all()
            if (r.loai_don or "THUONG").upper() != "DAU_TU" and not (r.so and mien_kiem(r.so))]
    da = [r for r in rows if str(r.so or "").upper().startswith("DA-")]
    out = {"don_dang_n": len(rows), "don_dang_gt": sum(_f(r.tong_tien) for r in rows),
           "du_an_n": len(da), "du_an_gt": sum(_f(r.tong_tien) for r in da)}
    q = db.query(DonMua.trang_thai, DonMua.tong_tien, DonMua.ngay, DonMua.trang_thai_nhan).filter(DonMua.trang_thai != "TU_CHOI").all()
    cho = [r for r in q if r.trang_thai == "CHO_DUYET"]
    moi = [r for r in q if r.ngay and ky["tu"] <= r.ngay <= ky["den"]]
    moi_t = [r for r in q if r.ngay and ky["truoc_tu"] <= r.ngay <= ky["truoc_den"]]
    out.update({"po_cho_n": len(cho), "po_cho_gt": sum(_f(r.tong_tien) for r in cho),
                "po_moi_n": len(moi), "po_moi_gt": sum(_f(r.tong_tien) for r in moi),
                "po_moi_n_truoc": len(moi_t), "po_moi_gt_truoc": sum(_f(r.tong_tien) for r in moi_t),
                "po_cho_nhan_n": sum(1 for r in q if r.trang_thai == "DA_DUYET" and (r.trang_thai_nhan or "") != "DU")})
    po_qh = po_qua_hen(db, hn)
    out.update({"po_qh_n": len(po_qh), "po_qh_lau": po_qh[0]["tre_ngay"] if po_qh else 0})
    try:
        from .tam_ung_mua import tam_ung_mua_hang
        tu = tam_ung_mua_hang(db)
        out.update({"tam_ung_mua": _f(tu.get("tong")), "tam_ung_mua_n": int(tu.get("so_po") or 0)})
    except Exception:                                        # noqa: BLE001
        db.rollback()
        out.update({"tam_ung_mua": 0.0, "tam_ung_mua_n": 0})
    try:
        from .routers.kho import tong_quan as _kho_tq
        k = _kho_tq(db)
        out.update({"ton_gia_tri": _f(k.get("gia_tri_ton")), "ton_duoi_min": int(k.get("duoi_min") or 0),
                    "ton_mat_hang": int(k.get("so_mat_hang") or 0)})
    except Exception:                                        # noqa: BLE001
        db.rollback()
    try:
        from .routers.ke_toan_quy import viec_ke_toan_treo
        out["treo"] = viec_ke_toan_treo(db)
    except Exception:                                        # noqa: BLE001
        db.rollback()
        out["treo"] = {}
    hd = (db.query(HopDongThue.gia_thue, HopDongThue.chu_ky, HopDongThue.ngay_ket_thuc)
          .filter(HopDongThue.trang_thai == "HIEU_LUC", HopDongThue.ngay_ket_thuc >= hn).all())
    out.update({"thue_n": len(hd),
                "thue_thang": sum(_f(h.gia_thue) / (3 if (h.chu_ky or "").upper() == "QUY" else 1) for h in hd),
                "thue_sap_het": sum(1 for h in hd if h.ngay_ket_thuc <= hn + timedelta(days=30))})
    bg = [t for (t,) in db.query(BaoGiaForm.trang_thai).all()]
    out.update({"bg_cho_duyet": sum(1 for t in bg if t == "CHO_DUYET"), "bg_nhap": sum(1 for t in bg if t == "NHAP")})
    out["co_hoi_mo"] = int(db.query(func.count(CoHoi.id))
                          .filter(CoHoi.giai_doan.notin_(("THANG", "THUA", "HUY", "DONG"))).scalar() or 0)
    return out


def _p_con_nguoi(db: Session, ky: dict) -> dict:
    from .models import GiaoViec, NhacViec, NhanVien
    hn = ky["hom_nay"]
    nv = [l for (l,) in db.query(NhanVien.loai_hop_dong).filter(NhanVien.trang_thai == "DANG_LAM").all()]
    out = {"nv_n": len(nv), "nv_thu_viec": sum(1 for l in nv if (l or "") == "THU_VIEC")}
    try:                                                     # 📝 báo cáo ngày: các ngày ĐÃ QUA trong kỳ
        from .bao_cao_ngay_service import ds_phai_bao_cao

        def bc(tu, den):
            phai = da = 0
            d = tu
            while d <= den:
                for x in ds_phai_bao_cao(db, d):
                    phai += 1
                    da += 1 if x["da_bao_cao"] else 0
                d += timedelta(days=1)
            return phai, da
        p, d_ = bc(ky["tu"], min(ky["den"], hn - timedelta(days=1)))
        pt, dt_ = bc(ky["truoc_tu"], ky["truoc_den"])
        out.update({"bc_phai": p, "bc_da": d_, "bc_pct": round(d_ / p * 100) if p else None,
                    "bc_pct_truoc": round(dt_ / pt * 100) if pt else None})
    except Exception:                                        # noqa: BLE001
        db.rollback()
        out.update({"bc_phai": 0, "bc_da": 0, "bc_pct": None, "bc_pct_truoc": None})
    try:
        from .tien_do_service import ds_cham_tien_do
        cham = ds_cham_tien_do(db, hn)
        out.update({"cham_n": len(cham), "cham_qua_han": sum(1 for x in cham if x.get("qua_han")),
                    "cham_top": [f"{x['ho_ten']}: {x['ten_cong_viec']}" for x in cham[:3]]})
    except Exception:                                        # noqa: BLE001
        db.rollback()
        out.update({"cham_n": 0, "cham_qua_han": 0, "cham_top": []})
    bd = datetime.combine(hn, datetime.min.time())
    out["nhac_qua_han"] = int(db.query(func.count(NhacViec.id))
                              .filter(NhacViec.trang_thai.notin_(("XONG", "HUY")), NhacViec.han_hoan_thanh.isnot(None),
                                      NhacViec.han_hoan_thanh < bd).scalar() or 0)
    k_tu = datetime.combine(ky["tu"], datetime.min.time())
    k_den = datetime.combine(ky["den"] + timedelta(days=1), datetime.min.time())
    out["giao_xong_tuan"] = int(db.query(func.count(GiaoViec.id))
                                .filter(GiaoViec.hoan_thanh_luc >= k_tu, GiaoViec.hoan_thanh_luc < k_den).scalar() or 0)
    return out


def _p_tuan_thu(db: Session, ky: dict) -> dict:
    from .models import AuditLog, SaoLuuLog
    from .nhac_viec_service import gio_hien_tai
    out = {}
    sl = db.query(SaoLuuLog).filter(SaoLuuLog.trang_thai == "THANH_CONG").order_by(SaoLuuLog.id.desc()).first()
    if sl is not None:
        luc = sl.ket_thuc or sl.bat_dau
        tre = (gio_hien_tai().replace(tzinfo=None) - luc.replace(tzinfo=None)).total_seconds() / 3600 if luc else None
        out.update({"sao_luu_luc": str(luc)[:16], "sao_luu_ok": bool(tre is not None and tre <= SAO_LUU_TRE_GIO)})
    else:
        out.update({"sao_luu_luc": None, "sao_luu_ok": False})
    k_tu = datetime.combine(ky["tu"], datetime.min.time())
    k_den = datetime.combine(ky["den"] + timedelta(days=1), datetime.min.time())
    out["audit_n"] = int(db.query(func.count(AuditLog.id)).filter(AuditLog.thoi_gian >= k_tu, AuditLog.thoi_gian < k_den).scalar() or 0)
    out["audit_nguoi"] = int(db.query(func.count(func.distinct(AuditLog.nguoi_dung_id)))
                             .filter(AuditLog.thoi_gian >= k_tu, AuditLog.thoi_gian < k_den, AuditLog.nguoi_dung_id.isnot(None))
                             .scalar() or 0)
    try:
        from .routers.tai_chinh import trang_thai_nhac_sao_ke
        sk = trang_thai_nhac_sao_ke(db)
        out.update({"sao_ke_co": bool(sk.get("co_sao_ke")), "sao_ke_thang": sk.get("thang_hien")})
    except Exception:                                        # noqa: BLE001
        db.rollback()
    return out


_PHAN = (("tien", _p_tien), ("lai", _p_lai), ("no", _p_no), ("van_hanh", _p_van_hanh),
         ("con_nguoi", _p_con_nguoi), ("tuan_thu", _p_tuan_thu))


# ---------------------------------------------------------------- ghép ba tầng
def _cs(ma, nhom, ten, gia_tri, don_vi="tien", phu="", ky_truoc=None, tot_khi=None, mo=None) -> dict:
    return {"ma": ma, "nhom": nhom, "ten": ten, "gia_tri": gia_tri, "don_vi": don_vi, "phu": phu,
            "ky_truoc": ky_truoc, "tot_khi": tot_khi, "mo": mo or {}}


def chi_so(d: dict) -> list[dict]:
    """① 12 chỉ số — gia_tri None = phần đó chưa tính được."""
    t, l, n, v, c = (d.get(k) or {} for k in ("tien", "lai", "no", "van_hanh", "con_nguoi"))
    g = lambda m, k, mac=None: m.get(k, mac)                 # noqa: E731
    bien = g(l, "bien")
    return [
        _cs("tien_hien_co", "Tiền", "Tiền hiện có", g(t, "hien_co"),
            phu=(f"ngân hàng {_tr(g(t, 'ngan_hang', 0))} · quỹ tiền mặt {_tr(g(t, 'tien_mat', 0))}" if t else ""),
            mo={"page": "overall_financial", "tab": "tongquan"}),
        _cs("tien_vao", "Tiền", "Tiền khách trả trong tuần", g(t, "vao"), ky_truoc=g(t, "vao_truoc"), tot_khi="tang",
            phu="theo thanh toán công nợ phải thu (gồm VAT)", mo={"page": "ban_hang", "tab": "cong_no"}),
        _cs("tien_ra", "Tiền", "Tiền trả NCC trong tuần", g(t, "ra"), ky_truoc=g(t, "ra_truoc"),
            phu="theo thanh toán công nợ phải trả (gồm VAT)", mo={"page": "ncc", "tab": "duyet_chi"}),
        _cs("thu_30", "Tiền", f"Phải thu {NGAY_SAP_TOI} ngày tới", g(t, "thu_30"),
            phu=f"{g(t, 'n_thu_30', 0)} khoản đến hạn hoặc đã hẹn", mo={"page": "ban_hang", "tab": "cong_no"}),
        _cs("chi_30", "Tiền", f"Phải chi {NGAY_SAP_TOI} ngày tới", g(t, "phai_chi_30"),
            phu=f"lệnh chi đã duyệt chờ chi {_tr(g(t, 'lenh_cho_chi', 0))} + phải trả đến hạn {_tr(g(t, 'tra_30', 0))}",
            mo={"page": "ncc", "tab": "duyet_chi"}),
        _cs("don_tuan", "Lãi", "Đơn chốt trong tuần", g(l, "don_gt"), ky_truoc=g(l, "don_gt_truoc"), tot_khi="tang",
            phu=f"{g(l, 'don_n', 0)} đơn (tuần trước {g(l, 'don_n_truoc', 0)}) · giá trị chưa VAT",
            mo={"page": "ban_hang", "tab": "don_hang"}),
        _cs("lai_lo", "Lãi", "Lãi/Lỗ Record", g(l, "lai_lo"), ky_truoc=g(l, "lai_lo_truoc"), tot_khi="tang",
            phu=(f"lãi gộp {_tr(g(l, 'lai_gop', 0))} · biên {str(bien).replace('.', ',')}%" if bien is not None
                 else "chưa tính được"),
            mo={"page": "overall_financial", "tab": "tongquan"}),
        _cs("ma_lo", "Lãi", "Nhóm mã đang lỗ", g(l, "so_lo"), don_vi="so", tot_khi="giam",
            phu=f"lỗ {_tr(g(l, 'lo_tong', 0))} · {g(l, 'so_bien_thap', 0)} nhóm biên dưới {_f(g(l, 'nguong', 15)):g}% · "
                f"{g(l, 'so_chua_dt', 0)} nhóm có chi phí chưa có doanh thu",
            mo={"page": "ke_toan", "tab": "lailo"}),
        _cs("phai_thu_qh", "Nợ", "Phải thu quá hạn", g(n, "qh_tong"), tot_khi="giam",
            phu=f"{g(n, 'qh_n', 0)} khoản · quá 60 ngày: {g(n, 'qh_60_n', 0)} ({_tr(g(n, 'qh_60_tong', 0))}) · "
                f"tổng còn phải thu {_tr(g(n, 'phai_thu', 0))}",
            mo={"page": "ban_hang", "tab": "cong_no"}),
        _cs("dchd", "Nợ", "Đơn chưa xuất hóa đơn, còn phải thu", g(n, "dchd_con"), tot_khi="giam",
            phu=f"{g(n, 'dchd_n', 0)} đơn · quá {g(n, 'dchd_nguong', 30)} ngày: {g(n, 'dchd_qn_n', 0)} "
                f"({_tr(g(n, 'dchd_qn_tong', 0))})",
            mo={"page": "ban_hang", "tab": "cong_no"}),
        _cs("po", "Vận hành", "PO quá hẹn giao", g(v, "po_qh_n"), don_vi="so", tot_khi="giam",
            phu=f"trễ lâu nhất {g(v, 'po_qh_lau', 0)} ngày · PO chờ duyệt {g(v, 'po_cho_n', 0)} ({_tr(g(v, 'po_cho_gt', 0))}) · "
                f"đơn đang thực hiện {g(v, 'don_dang_n', 0)}",
            mo={"page": "ncc", "tab": "po"}),
        _cs("nhan_su", "Con người", "Báo cáo ngày hoàn thành", g(c, "bc_pct"), don_vi="pct", ky_truoc=g(c, "bc_pct_truoc"),
            tot_khi="tang",
            phu=f"{g(c, 'bc_da', 0)}/{g(c, 'bc_phai', 0)} lượt · {g(c, 'cham_n', 0)} việc chậm tiến độ · "
                f"{g(c, 'nv_n', 0)} nhân sự đang làm",
            mo={"page": "working_time", "tab": "report"}),
    ]


def viec_can_quyet(d: dict) -> list[dict]:
    """② Mọi ngoại lệ đang treo — chỉ liệt kê mục có số > 0; Cao → Vừa → Thấp, tiền lớn lên trước."""
    l, n, v, c, tt = (d.get(k) or {} for k in ("lai", "no", "van_hanh", "con_nguoi", "tuan_thu"))
    treo = v.get("treo") or {}
    q = []

    def add(ten, so, tien=0.0, muc="Vừa", mo=None, ghi_chu=""):
        if so:
            q.append({"ten": ten, "so": int(so), "tien": _f(tien), "muc": muc, "mo": mo or {}, "ghi_chu": ghi_chu or ""})
    add("Phiếu thu chi chờ duyệt", treo.get("phieu_cho"), treo.get("phieu_cho_tong"), "Cao", {"page": "ke_toan", "tab": "phieu"})
    add("Lệnh chi đã duyệt chờ ✔ Đã chi", treo.get("lenh_cho"), treo.get("lenh_cho_tong"),
        "Cao" if treo.get("lenh_qua7") else "Vừa", {"page": "ncc", "tab": "duyet_chi"},
        f"{treo.get('lenh_qua7')} lệnh quá 7 ngày" if treo.get("lenh_qua7") else "")
    add("PO chờ duyệt", v.get("po_cho_n"), v.get("po_cho_gt"), "Vừa", {"page": "ncc", "tab": "po"})
    add("Báo giá gửi khách chờ duyệt", v.get("bg_cho_duyet"), 0, "Vừa", {"page": "ban_hang", "tab": "bao_gia"})
    add("Nhóm mã đang lỗ", l.get("so_lo"), l.get("lo_tong"), "Cao", {"page": "ke_toan", "tab": "lailo"},
        " · ".join(o["nhom"] for o in (l.get("lo_top") or [])))
    add(f"Nhóm mã biên dưới {_f(l.get('nguong', 15)):g}%", l.get("so_bien_thap"), 0, "Vừa", {"page": "ke_toan", "tab": "lailo"})
    add("Dự toán giá vốn ƯỚC chưa rà", len(l.get("gia_uoc") or []), 0, "Thấp", {"page": "ban_hang", "tab": "bao_gia"},
        " · ".join((l.get("gia_uoc") or [])[:5]))
    add("Công nợ phải thu quá 60 ngày", n.get("qh_60_n"), n.get("qh_60_tong"), "Cao", {"page": "ban_hang", "tab": "cong_no"},
        " · ".join(f"{x['khach']} {_tr(x['tong'])}" for x in (n.get("qh_top") or [])))
    add("Công nợ phải trả quá hạn", n.get("tra_qh_n"), n.get("tra_qh_tong"), "Vừa", {"page": "ncc", "tab": "cong_no"})
    add(f"Đơn chưa xuất hóa đơn quá {n.get('dchd_nguong', 30)} ngày", n.get("dchd_qn_n"), n.get("dchd_qn_tong"), "Vừa",
        {"page": "ban_hang", "tab": "cong_no"})
    add("PO quá hẹn giao chưa nhận đủ", v.get("po_qh_n"), 0, "Vừa", {"page": "ncc", "tab": "po"},
        f"trễ lâu nhất {v.get('po_qh_lau', 0)} ngày" if v.get("po_qh_n") else "")
    add("Hóa đơn mua chưa hạch toán", treo.get("hd_chua_ht"), treo.get("hd_chua_ht_tong"), "Thấp", {"page": "ke_toan", "tab": "hoadon"})
    add("Hóa đơn email chờ xác nhận", treo.get("hdc_cho"), 0, "Thấp", {"page": "ke_toan", "tab": "hoadon"})
    add("Khoản phải trả thiếu số hóa đơn", treo.get("cn_thieu_hd"), treo.get("cn_thieu_hd_tong"), "Thấp", {"page": "ncc", "tab": "cong_no"})
    add("Hợp đồng thuê sắp hết hạn (≤ 30 ngày)", v.get("thue_sap_het"), 0, "Vừa", {"page": "cho_thue", "tab": "hop_dong"})
    add("Hàng dưới mức tồn tối thiểu", v.get("ton_duoi_min"), 0, "Thấp", {"page": "kho", "tab": "canh_bao"})
    add("Việc giao đang chậm tiến độ", c.get("cham_n"), 0, "Vừa", {"page": "working_time", "tab": "report"},
        " · ".join(c.get("cham_top") or []))
    add("Nhắc việc quá hạn chưa xong", c.get("nhac_qua_han"), 0, "Thấp", {"page": "working_time", "tab": "remind"})
    if tt and tt.get("sao_luu_ok") is False:
        add(f"Sao lưu CSDL không chạy quá {SAO_LUU_TRE_GIO} giờ", 1, 0, "Cao", {"page": "cau_hinh"},
            f"bản gần nhất {tt.get('sao_luu_luc') or 'chưa có'}")
    if tt.get("sao_ke_co") is False:
        add(f"Chưa có sao kê ngân hàng tháng {tt.get('sao_ke_thang') or ''}".strip(), 1, 0, "Vừa",
            {"page": "overall_financial", "tab": "tongquan"})
    q.sort(key=lambda x: (_MUC_THU_TU.get(x["muc"], 9), -x["tien"], -x["so"]))
    return q


def sau_khoi(d: dict) -> list[dict]:
    """③ Sáu khối theo nhóm menu — mỗi khối vài dòng chữ đọc được ngay."""
    t, l, n, v, c, tt = (d.get(k) or {} for k in ("tien", "lai", "no", "van_hanh", "con_nguoi", "tuan_thu"))
    treo = v.get("treo") or {}
    pct = lambda x: "—" if x is None else f"{x}%"                                       # noqa: E731
    bien = l.get("bien")
    return [
        {"ma": "thuong_mai", "icon": "🤝", "ten": "Thương mại", "dong": [
            f"Đơn chốt trong tuần: {l.get('don_n', 0)} đơn · {_tr(l.get('don_gt', 0))} (tuần trước {l.get('don_n_truoc', 0)} đơn · "
            f"{_tr(l.get('don_gt_truoc', 0))}), giá trị chưa VAT",
            f"Đơn đang thực hiện: {v.get('don_dang_n', 0)} đơn · {_tr(v.get('don_dang_gt', 0))}",
            f"Báo giá gửi khách: {v.get('bg_cho_duyet', 0)} chờ duyệt · {v.get('bg_nhap', 0)} đang soạn · "
            f"cơ hội CRM đang mở: {v.get('co_hoi_mo', 0)}",
            f"Công nợ phải thu còn {_tr(n.get('phai_thu', 0))} · quá hạn {n.get('qh_n', 0)} khoản ({_tr(n.get('qh_tong', 0))})"]},
        {"ma": "cung_ung", "icon": "🚚", "ten": "Cung ứng", "dong": [
            f"PO mới trong tuần: {v.get('po_moi_n', 0)} · {_tr(v.get('po_moi_gt', 0))} (tuần trước {v.get('po_moi_n_truoc', 0)} · "
            f"{_tr(v.get('po_moi_gt_truoc', 0))})",
            f"PO chờ duyệt {v.get('po_cho_n', 0)} ({_tr(v.get('po_cho_gt', 0))}) · chờ nhận hàng {v.get('po_cho_nhan_n', 0)} · "
            f"quá hẹn giao {v.get('po_qh_n', 0)}",
            f"Đã tạm ứng mua hàng chưa có hàng: {_tr(v.get('tam_ung_mua', 0))} ({v.get('tam_ung_mua_n', 0)} PO)",
            f"Phải trả NCC còn {_tr(n.get('phai_tra', 0))} · quá hạn {n.get('tra_qh_n', 0)} khoản ({_tr(n.get('tra_qh_tong', 0))}) · "
            f"hóa đơn email chờ xác nhận {treo.get('hdc_cho', 0)}",
            f"Tồn kho: {_tr(v.get('ton_gia_tri', 0))} · {v.get('ton_duoi_min', 0)} mặt hàng dưới mức tồn tối thiểu"]},
        {"ma": "dich_vu", "icon": "🏗", "ten": "Dịch vụ", "dong": [
            f"Dự án (mã DA-) đang triển khai: {v.get('du_an_n', 0)} · {_tr(v.get('du_an_gt', 0))}",
            f"Cho thuê: {v.get('thue_n', 0)} hợp đồng hiệu lực · giá thuê theo hợp đồng ≈ {_tr(v.get('thue_thang', 0))}/tháng · "
            f"sắp hết hạn (≤ 30 ngày): {v.get('thue_sap_het', 0)}",
            f"Đơn chưa xuất hóa đơn: {n.get('dchd_n', 0)} · còn phải thu {_tr(n.get('dchd_con', 0))}"]},
        {"ma": "tai_chinh", "icon": "💰", "ten": "Tài chính", "dong": [
            f"Tiền hiện có {_tr(t.get('hien_co', 0))} (ngân hàng {_tr(t.get('ngan_hang', 0))} · quỹ tiền mặt {_tr(t.get('tien_mat', 0))})",
            f"Tuần này thu {_tr(t.get('vao', 0))} · chi {_tr(t.get('ra', 0))} (tuần trước thu {_tr(t.get('vao_truoc', 0))} · "
            f"chi {_tr(t.get('ra_truoc', 0))})",
            f"{NGAY_SAP_TOI} ngày tới: phải thu {_tr(t.get('thu_30', 0))} · phải chi {_tr(t.get('phai_chi_30', 0))}",
            f"Lãi/Lỗ Record {_tr(l.get('lai_lo', 0))} (cuối tuần trước {_tr(l.get('lai_lo_truoc', 0))}) · lãi gộp "
            f"{_tr(l.get('lai_gop', 0))} · biên {('—' if bien is None else str(bien).replace('.', ','))}%",
            f"Chi phí nhân sự lũy kế {_tr(l.get('chi_nhan_su', 0))} · tháng {l.get('ns_thang') or '—'}: {_tr(l.get('ns_thang_tong', 0))}"]},
        {"ma": "noi_bo", "icon": "👥", "ten": "Nội bộ", "dong": [
            f"Nhân sự đang làm: {c.get('nv_n', 0)} (thử việc {c.get('nv_thu_viec', 0)})",
            f"Báo cáo ngày: {c.get('bc_da', 0)}/{c.get('bc_phai', 0)} lượt = {pct(c.get('bc_pct'))} (tuần trước {pct(c.get('bc_pct_truoc'))})",
            f"Việc giao chậm tiến độ: {c.get('cham_n', 0)} (quá hạn {c.get('cham_qua_han', 0)}) · nhắc việc quá hạn "
            f"{c.get('nhac_qua_han', 0)} · việc hoàn thành trong tuần {c.get('giao_xong_tuan', 0)}"]},
        {"ma": "tuan_thu", "icon": "🛡", "ten": "Tuân thủ", "dong": [
            f"Sao lưu CSDL gần nhất: {tt.get('sao_luu_luc') or 'chưa có'}" + (" ✓" if tt.get("sao_luu_ok") else " ⚠"),
            f"Sao kê ngân hàng tháng {tt.get('sao_ke_thang') or '—'}: " + ("đã tải ✓" if tt.get("sao_ke_co") else "chưa tải ⚠"),
            f"Nhật ký hệ thống trong tuần: {tt.get('audit_n', 0)} thao tác · {tt.get('audit_nguoi', 0)} người",
            f"Dự toán giá vốn ước chưa rà: {len(l.get('gia_uoc') or [])} · hóa đơn bán còn số tạm: {treo.get('hd_ban_so_tam', 0)}"]},
    ]


def tuan(db: Session, hom_nay: date | None = None, lui: int = 0) -> dict:
    """Bản tuần đầy đủ. Không ném lỗi: phần hỏng ghi vào `loi`."""
    hom_nay = hom_nay or hom_nay_vn()
    ky = ky_tuan(hom_nay, lui)
    d, loi = {}, []
    for ten, fn in _PHAN:
        try:
            d[ten] = fn(db, ky)
        except Exception as e:                               # noqa: BLE001
            db.rollback()
            d[ten] = {}
            loi.append(f"{ten}: {type(e).__name__}: {str(e)[:120]}")
    for ten in ("lai",):
        for k in ("loi_lai_lo", "loi_kiem_soat"):
            if (d.get(ten) or {}).get(k):
                loi.append(f"{k[4:]}: {d[ten][k]}")
    return {"ky": {k: (str(v) if isinstance(v, date) else v) for k, v in ky.items()},
            "chi_so": chi_so(d), "quyet": viec_can_quyet(d), "khoi": sau_khoi(d), "loi": loi, "so_lieu": d}


# ---------------------------------------------------------------- tin Chat
def noi_dung_tuan(bc: dict, nguoi=None) -> str:
    ky = bc["ky"]
    cs = {x["ma"]: x for x in bc["chi_so"]}

    def v(ma):
        return (cs.get(ma) or {}).get("gia_tri")

    def phu(ma):
        return (cs.get(ma) or {}).get("phu") or ""

    def ss(ma):
        x = cs.get(ma) or {}
        a, b = x.get("gia_tri"), x.get("ky_truoc")
        if a is None or b is None:
            return ""
        return f" (tuần trước {_tr(b) if x['don_vi'] == 'tien' else (str(b) + ('%' if x['don_vi'] == 'pct' else ''))})"
    tien = lambda ma: "—" if v(ma) is None else _tr(v(ma))                                # noqa: E731
    so = lambda ma: "—" if v(ma) is None else str(v(ma))                                  # noqa: E731
    l = [f"📋 *BÁO CÁO TUẦN CEO* — {ky['nhan']} ({_dm_s(ky['tu'])} → {_dm_s(ky['den'])}, số liệu đến {_dmy_s(ky['hom_nay'])})",
         f"💰 *Tiền*: hiện có {tien('tien_hien_co')} · tuần này thu {tien('tien_vao')}{ss('tien_vao')} · chi {tien('tien_ra')}"
         f"{ss('tien_ra')} · {NGAY_SAP_TOI} ngày tới phải thu {tien('thu_30')} / phải chi {tien('chi_30')}",
         f"📈 *Lãi*: đơn chốt tuần {tien('don_tuan')}{ss('don_tuan')} ({phu('don_tuan')}) · Lãi/Lỗ Record {tien('lai_lo')}"
         f"{ss('lai_lo')} · {phu('lai_lo')} · nhóm mã lỗ {so('ma_lo')}",
         f"🧾 *Nợ*: phải thu quá hạn {tien('phai_thu_qh')} ({phu('phai_thu_qh')}) · đơn chưa xuất HĐ còn phải thu {tien('dchd')} "
         f"({phu('dchd')})",
         f"⚙ *Vận hành*: PO quá hẹn giao {so('po')} · {phu('po')}",
         f"👥 *Nhân sự*: báo cáo ngày {so('nhan_su')}{'%' if v('nhan_su') is not None else ''}{ss('nhan_su')} · {phu('nhan_su')}"]
    q = bc.get("quyet") or []
    if q:
        l.append(f"✅ *Cần CEO quyết* ({len(q)} việc):")
        for x in q[:TOI_DA_QUYET_TIN]:
            l.append(f"   – [{x['muc']}] {x['ten']}: *{x['so']}*" + (f" · {_tr(x['tien'])}" if x["tien"] else "")
                     + (f" — {x['ghi_chu']}" if x["ghi_chu"] else ""))
        if len(q) > TOI_DA_QUYET_TIN:
            l.append(f"   … và {len(q) - TOI_DA_QUYET_TIN} việc khác — xem trong app")
    else:
        l.append("✅ Không có việc nào treo chờ CEO quyết 🎉")
    if bc.get("loi"):
        l.append(f"⚠ {len(bc['loi'])} phần chưa tính được: " + "; ".join(bc["loi"])[:240])
    l.append("👉 App SVWS → Overall Financial → 📋 Báo cáo CEO: đủ 12 chỉ số, 6 khối, việc cần quyết (bấm «Mở» tới bảng xử lý), in PDF")
    if nguoi:
        l.append(f"_(gửi tay bởi {nguoi})_")
    return "\n".join(l)


def noi_gui() -> dict:
    ceo = (settings.gchat_webhook_ceo or "").strip()
    dc = (settings.gchat_webhook_duyet_chi or "").strip()
    url = ceo or dc
    return {"url": url, "nhom": ("nhóm riêng CEO" if ceo else "nhóm Duyệt chi") if url else ""}


def gui_tuan(db: Session, nguon: str = "TU_DONG", nguoi=None) -> dict:
    """Gửi tin tóm tắt tuần hiện tại. Không ném lỗi."""
    from .chat_gateway import gui_webhook_rieng
    kq = {"nguon": nguon, "da_gui": False}
    try:
        ng = noi_gui()
        if not ng["url"]:
            kq["ly_do"] = "Chưa cấu hình GCHAT_WEBHOOK_CEO (hoặc GCHAT_WEBHOOK_DUYET_CHI)"
            return kq
        bc = tuan(db)
        r = gui_webhook_rieng(ng["url"], noi_dung_tuan(bc, nguoi))
        kq.update({"da_gui": bool(r.get("da_gui")), "loi": r.get("loi"), "nhom": ng["nhom"], "ky": bc["ky"]["nhan"],
                   "so_quyet": len(bc["quyet"]), "so_loi": len(bc["loi"])})
    except Exception as e:                                   # noqa: BLE001
        kq["loi"] = f"{type(e).__name__}: {str(e)[:150]}"
    return kq
