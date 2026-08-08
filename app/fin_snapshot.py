# Snapshot FINANCIAL — CEO: chụp CSV toàn cảnh Mua hàng – Bán hàng – Công nợ
# (bức tranh trang Overall Financial) vào Kho tệp dùng chung mỗi khi có biến động tiền.
# Giãn cách tối thiểu giữa 2 bản tự động để biến động dồn dập không sinh quá nhiều file.
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func

from .models import (TepDinhKem, CongNo, DonHang, DonMua, KhachHang,
                     NhaCungCap, ThanhToan)
from . import luu_tru
from .nhac_viec_service import gio_hien_tai


def _c(v):
    return '"' + str(v if v is not None else "").replace('"', '""') + '"'


def _f(v):
    return float(v or 0)


def snapshot_financial(db, su_kien: str, toi_thieu_phut: int = 30):
    """Chụp CSV Financial — CEO. su_kien='THU CONG' (nút bấm) bỏ qua giãn cách.
    Lỗi snapshot không được làm hỏng nghiệp vụ chính — nuốt mọi exception."""
    try:
        luc = gio_hien_tai()
        if toi_thieu_phut and su_kien != "THU CONG":
            gan_nhat = (db.query(TepDinhKem).filter_by(doi_tuong="FIN_CEO")
                        .order_by(TepDinhKem.id.desc()).first())
            if gan_nhat is not None:
                try:  # tên file dạng Fin_YYYYmmdd_HHMMSS.csv → so thời gian không lệ thuộc timezone DB
                    truoc = datetime.strptime(gan_nhat.ten_file[4:19], "%Y%m%d_%H%M%S")
                    if (luc.replace(tzinfo=None) - truoc).total_seconds() < toi_thieu_phut * 60:
                        return None
                except Exception:
                    pass

        kh_ten = {k.id: k.ten for k in db.query(KhachHang).all()}
        nc_ten = {n.id: n.ten for n in db.query(NhaCungCap).all()}

        # --- tổng hợp (cùng công thức trang Overall Financial) ---
        da_thu = _f(db.query(func.coalesce(func.sum(ThanhToan.so_tien), 0))
                    .join(CongNo, ThanhToan.cong_no_id == CongNo.id)
                    .filter(CongNo.loai == "PHAI_THU").scalar())
        da_tra = _f(db.query(func.coalesce(func.sum(ThanhToan.so_tien), 0))
                    .join(CongNo, ThanhToan.cong_no_id == CongNo.id)
                    .filter(CongNo.loai == "PHAI_TRA").scalar())
        phai_thu = _f(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
                      .filter(CongNo.loai == "PHAI_THU", CongNo.trang_thai != "THU_DU").scalar())
        phai_tra = _f(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
                      .filter(CongNo.loai == "PHAI_TRA", CongNo.trang_thai != "THU_DU").scalar())
        dhs = db.query(DonHang).order_by(DonHang.id).all()
        dms = db.query(DonMua).order_by(DonMua.id).all()
        dh_tong = sum(_f(o.tong_tien) for o in dhs)
        dh_xuat = sum(_f(o.tong_tien) for o in dhs if o.trang_thai in ("DA_XUAT_HD", "HOAN_THANH"))
        dh_coc = sum(_f(o.thanh_toan_coc) for o in dhs if o.trang_thai != "HOAN_THANH")
        dm_tong = sum(_f(m.tong_tien) for m in dms)
        dm_tra_truoc = sum(_f(m.de_nghi_tt) for m in dms if _f(m.de_nghi_tt) > 0 and not m.tt_du)

        dong = ["﻿SNAPSHOT FINANCIAL — CEO",
                "Thời điểm," + luc.strftime("%Y-%m-%d %H:%M:%S"),
                "Sự kiện," + _c(su_kien), "",
                "TỔNG HỢP", "Chỉ tiêu,Giá trị",
                "Đã thu từ khách," + str(da_thu),
                "Còn phải thu," + str(phai_thu),
                "Đã trả NCC," + str(da_tra),
                "Còn phải trả," + str(phai_tra),
                "Tổng giá trị đơn hàng bán," + str(dh_tong),
                "Doanh thu đã xuất hóa đơn," + str(dh_xuat),
                "Đơn chưa xuất hóa đơn," + str(dh_tong - dh_xuat),
                "Khách trả trước (cọc đơn đang triển khai)," + str(dh_coc),
                "Tổng giá trị đơn mua (PO)," + str(dm_tong),
                "Trả trước NCC (PO trả một phần)," + str(dm_tra_truoc)]

        dong += ["", "BÁN HÀNG — DANH SÁCH ĐƠN",
                 "Số,Ngày,Khách hàng,Giá trị,Tạm ứng (cọc),Trạng thái"]
        for o in dhs:
            dong.append(",".join([_c(o.so), str(o.ngay or ""), _c(kh_ten.get(o.khach_hang_id)),
                                  str(_f(o.tong_tien)), str(_f(o.thanh_toan_coc)), _c(o.trang_thai)]))

        dong += ["", "MUA HÀNG — DANH SÁCH PO",
                 "Số,Ngày,Nhà cung cấp,Giá trị,Đã trả,Còn lại,Trạng thái,TT đủ"]
        for m in dms:
            dong.append(",".join([_c(m.so), str(m.ngay or ""), _c(nc_ten.get(m.nha_cung_cap_id)),
                                  str(_f(m.tong_tien)), str(_f(m.de_nghi_tt)),
                                  str(_f(m.tong_tien) - _f(m.de_nghi_tt)), _c(m.trang_thai),
                                  "x" if m.tt_du else ""]))

        for loai, nhan in (("PHAI_THU", "CÔNG NỢ PHẢI THU"), ("PHAI_TRA", "CÔNG NỢ PHẢI TRẢ")):
            dong += ["", nhan + " — TỪNG KHOẢN",
                     "Đối tác,Số HĐ,Tổng,Đã thanh toán,Còn lại,Hạn,Trạng thái"]
            for c in (db.query(CongNo).filter(CongNo.loai == loai)
                      .order_by(CongNo.id).all()):
                doi_tac = kh_ten.get(c.khach_hang_id) if loai == "PHAI_THU" else nc_ten.get(c.nha_cung_cap_id)
                dong.append(",".join([_c(doi_tac), _c(c.so_ct), str(_f(c.so_tien)),
                                      str(_f(c.da_thanh_toan)),
                                      str(_f(c.so_tien) - _f(c.da_thanh_toan)),
                                      str(c.han or ""), _c(c.trang_thai)]))

        data = "\n".join(dong).encode("utf-8")
        ten = "Fin_" + luc.strftime("%Y%m%d_%H%M%S") + ".csv"
        ref = luu_tru.luu(data, "fin_ceo", luc.strftime("%Y%m"), ten, "text/csv")
        t = TepDinhKem(doi_tuong="FIN_CEO", doi_tuong_id=0, loai=(su_kien or "SNAPSHOT")[:20],
                       ten_file=ten, duong_dan=ref, kich_thuoc=len(data), content_type="text/csv")
        db.add(t)
        return t
    except Exception:
        return None
