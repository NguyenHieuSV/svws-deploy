"""📄 ĐƠN BÁN CHƯA XUẤT HÓA ĐƠN — gom về một chỗ để theo dõi (04/11/2026).

Trước đây các đơn này nằm rải rác: tab Đơn hàng (cột trạng thái), ba ô tổng ở Overall Financial, còn tab Bán hàng › Công nợ
khách không thấy vì công nợ phải thu chỉ sinh khi đơn đã xuất kho / đã có số hóa đơn. Module này cấp:
  • danh_sach(db)   → từng đơn chưa xuất hóa đơn: tuổi đơn, giá trị gồm VAT, khách đã trả bao nhiêu, còn phải thu
                      (bảng «📄 Đơn chưa xuất hóa đơn» đặt trên bảng công nợ ở tab Công nợ khách — API /ban-hang/don-chua-xuat-hd).
  • qua_nguong(db)  → đơn có giá trị, quá NGUONG_NHAC_NGAY ngày — gộp vào bản nhắc công nợ thứ Hai (app/nhac_qua_han.py).

Đơn CHƯA XUẤT HÓA ĐƠN = trạng thái chưa phải «Đã xuất hóa đơn» / «Hoàn thành»; bỏ đơn đầu tư – cho thuê (hóa đơn ở mã tháng)
và mã nội bộ OP- / KHO / mã mẹ theo năm (kiem_soat_ln.mien_kiem — không phải hàng bán cho khách).
Đơn đã XUẤT KHO (có công nợ + hóa đơn bán mang SỐ TẠM = mã đơn) vẫn là chưa xuất hóa đơn cho tới khi có số hóa đơn thật.
ĐÃ THU của đơn — cùng quy tắc với Lãi/lỗ theo mã (app/lai_lo_ma.py):
  có công nợ   → đã thanh toán trên công nợ + tạm ứng phiếu thu đã duyệt chưa cấn;
  chưa công nợ → max(cọc ghi trên đơn, tạm ứng) — hai đường ghi cùng một khoản tiền, không cộng dồn.
Chỉ đọc đúng cột cần (test chạy SQLite với bảng tối giản).
"""
import re
from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session

NGUONG_NHAC_NGAY = 30                       # đơn quá số ngày này (tính từ ngày đơn) thì vào bản nhắc thứ Hai
_SO_TAM = re.compile(r"(hd|dh)-\d+")        # số tạm app tự đặt (HD-<id> / DH-<id>) — cùng luật với routers/ban_hang._so_hd_that


def _f(v) -> float:
    return float(v or 0)


def so_hd_that(so, ma_don) -> bool:
    """Số hóa đơn THẬT: có giá trị, không phải mã đơn và không phải số tạm HD-/DH-<id>."""
    s = (so or "").strip().lower()
    return bool(s) and s != (ma_don or "").strip().lower() and not _SO_TAM.fullmatch(s)


def hom_nay_vn() -> date:
    from .nhac_viec_service import gio_hien_tai
    return gio_hien_tai().date()


def danh_sach(db: Session, hom_nay: date | None = None) -> list[dict]:
    """Từng đơn chưa xuất hóa đơn, lâu nhất lên trên (rồi còn phải thu nhiều lên trên)."""
    from .kiem_soat_ln import mien_kiem
    from .lai_lo_ma import tra_truoc_theo_don
    from .models import CongNo, DonHang, HoaDon, KhachHang, NhanVien
    hom_nay = hom_nay or hom_nay_vn()
    # bỏ đơn đầu tư – cho thuê và mã NỘI BỘ (OP- vận hành / KHO / mã mẹ theo năm — cùng luật mien_kiem của Kiểm soát):
    # không phải hàng bán cho khách nên không có hóa đơn để xuất
    rows = [r for r in (db.query(DonHang.id, DonHang.so, DonHang.khach_hang_id, DonHang.ngay, DonHang.tong_tien,
                                 DonHang.tien_thue, DonHang.trang_thai, DonHang.thanh_toan_coc, DonHang.so_hoa_don,
                                 DonHang.loai_don)
                        .filter(or_(DonHang.trang_thai.is_(None),
                                    DonHang.trang_thai.notin_(("DA_XUAT_HD", "HOAN_THANH")))).all())
            if (r.loai_don or "THUONG").upper() != "DAU_TU" and not (r.so and mien_kiem(r.so))]
    if not rows:
        return []
    ids = [r.id for r in rows]
    hd_cua_don, hd_to_dh = {}, {}
    for h in (db.query(HoaDon.id, HoaDon.don_hang_id, HoaDon.so, HoaDon.hddt_trang_thai)
              .filter(HoaDon.loai == "BAN", HoaDon.don_hang_id.in_(ids)).all()):
        hd_cua_don.setdefault(h.don_hang_id, []).append(h)
        hd_to_dh[h.id] = h.don_hang_id
    dk = [CongNo.don_hang_id.in_(ids)]
    if hd_to_dh:
        dk.append(CongNo.hoa_don_id.in_(list(hd_to_dh)))
    cn = {}
    for c in (db.query(CongNo.id, CongNo.don_hang_id, CongNo.hoa_don_id, CongNo.da_thanh_toan, CongNo.so_ct)
              .filter(CongNo.loai == "PHAI_THU", or_(*dk)).order_by(CongNo.id).all()):
        dh_id = c.don_hang_id or hd_to_dh.get(c.hoa_don_id)
        if dh_id:
            cn[dh_id] = c                                  # id tăng dần → khoản mới nhất của đơn thắng (như _cong_no_cua_don)
    tt = tra_truoc_theo_don(db, ids)
    kh_ids = {r.khach_hang_id for r in rows if r.khach_hang_id}
    kh = {k.id: k for k in db.query(KhachHang.id, KhachHang.ten, KhachHang.nguoi_phu_trach)
          .filter(KhachHang.id.in_(kh_ids)).all()} if kh_ids else {}
    nv_ids = {k.nguoi_phu_trach for k in kh.values() if k.nguoi_phu_trach}
    nv = dict(db.query(NhanVien.id, NhanVien.ho_ten).filter(NhanVien.id.in_(nv_ids)).all()) if nv_ids else {}
    out = []
    for r in rows:
        truoc, thue = _f(r.tong_tien), _f(r.tien_thue)
        tong = truoc + thue
        c = cn.get(r.id)
        t = tt.get(r.id) or {"coc": _f(r.thanh_toan_coc), "tam_ung": 0.0, "tra_truoc": _f(r.thanh_toan_coc), "nguon": None}
        # số hóa đơn THẬT đã ghi ở đâu đó (trên đơn / hóa đơn bán / công nợ) nhưng trạng thái đơn chưa đổi → nhắc bấm chuyển
        so_san = r.so_hoa_don if so_hd_that(r.so_hoa_don, r.so) else None
        if not so_san:
            for h in hd_cua_don.get(r.id, []):
                if so_hd_that(h.so, r.so) or h.hddt_trang_thai == "DA_PHAT_HANH":
                    so_san = h.so
                    break
        if not so_san and c is not None and so_hd_that(c.so_ct, r.so):
            so_san = c.so_ct
        if c is not None:
            da_thu = _f(c.da_thanh_toan) + t["tam_ung"]
            nguon = ("công nợ" + (" + tạm ứng" if t["tam_ung"] > 0 else "")) if da_thu > 0 else None
        else:
            da_thu, nguon = t["tra_truoc"], t.get("nguon")
        k = kh.get(r.khach_hang_id)
        so_ngay = (hom_nay - r.ngay).days if r.ngay else 0
        out.append({"id": r.id, "so": r.so or f"DH-{r.id}", "ngay": str(r.ngay) if r.ngay else None, "so_ngay": so_ngay,
                    "khach_hang_id": r.khach_hang_id, "khach": (k.ten if k else None),
                    "phu_trach": nv.get(k.nguoi_phu_trach) if (k and k.nguoi_phu_trach) else None,
                    "trang_thai": r.trang_thai or "MOI", "da_xuat_kho": r.trang_thai == "DA_XUAT",
                    "truoc": truoc, "thue": thue, "tong": tong, "coc": t["coc"], "tam_ung": t["tam_ung"],
                    "da_thu": da_thu, "nguon_da_thu": nguon, "con_phai_thu": max(tong - da_thu, 0.0),
                    "cong_no_id": c.id if c else None, "cong_no_so_tam": bool(c is not None and not so_san),
                    "so_hd_san": so_san, "qua_nguong": bool(tong > 0 and so_ngay > NGUONG_NHAC_NGAY)})
    out.sort(key=lambda x: (-x["so_ngay"], -x["con_phai_thu"], x["id"]))
    return out


def qua_nguong(db: Session, hom_nay: date | None = None) -> list[dict]:
    """Đơn có giá trị, quá NGUONG_NHAC_NGAY ngày — phần đưa vào bản nhắc thứ Hai."""
    return [x for x in danh_sach(db, hom_nay) if x["qua_nguong"]]


def tong_hop(ds: list[dict]) -> dict:
    return {"so_don": len(ds), "tong": sum(x["tong"] for x in ds), "da_thu": sum(x["da_thu"] for x in ds),
            "con_phai_thu": sum(x["con_phai_thu"] for x in ds), "qua_nguong": sum(1 for x in ds if x["qua_nguong"]),
            "chua_gia_tri": sum(1 for x in ds if x["tong"] <= 0)}
