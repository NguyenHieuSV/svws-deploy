# Snapshot FINANCIAL — CEO: MỘT file lũy kế Fin_bien_dong.csv — mỗi biến động tiền
# thêm MỘT DÒNG chỉ tiêu tổng hợp (trang Overall Financial), dòng mới nhất trên cùng.
# Giãn cách tối thiểu giữa 2 dòng tự động để biến động dồn dập không ghi quá dày.
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func

from .models import (TepDinhKem, CongNo, DonHang, DonMua, ThanhToan)
from . import luu_tru
from .nhac_viec_service import gio_hien_tai

TEN = "Fin_bien_dong.csv"
HEADER = ("\ufeffThời điểm,Sự kiện,Đã thu từ khách,Còn phải thu,Đã trả NCC,Còn phải trả,"
          "Tổng giá trị đơn bán,Doanh thu đã xuất HĐ,Đơn chưa xuất HĐ,"
          "Khách trả trước (cọc),Tổng giá trị đơn mua (PO),Trả trước NCC")


def _c(v):
    return '"' + str(v if v is not None else "").replace('"', '""') + '"'


def _f(v):
    return float(v or 0)


def snapshot_financial(db, su_kien: str, toi_thieu_phut: int = 30):
    """Thêm một dòng chỉ tiêu vào Fin_bien_dong.csv. su_kien='THU CONG' bỏ qua giãn cách.
    Lỗi snapshot không được làm hỏng nghiệp vụ chính — nuốt mọi exception."""
    try:
        luc = gio_hien_tai()
        t_cu = db.query(TepDinhKem).filter_by(doi_tuong="FIN_CEO", ten_file=TEN).first()
        cu = []
        if t_cu is not None:
            try:
                lines = luu_tru.doc(t_cu.duong_dan).decode("utf-8").splitlines()
                cu = [l for l in lines[1:] if l.strip()][:20000]
            except Exception:
                cu = []
        # giãn cách: so thời điểm của dòng gần nhất (cột đầu) với bây giờ
        if toi_thieu_phut and su_kien != "THU CONG" and cu:
            try:
                truoc = datetime.strptime(cu[0].split(",")[0], "%Y-%m-%d %H:%M:%S")
                if (luc.replace(tzinfo=None) - truoc).total_seconds() < toi_thieu_phut * 60:
                    return None
            except Exception:
                pass

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
        dhs = db.query(DonHang).all()
        dms = db.query(DonMua).all()
        dh_tong = sum(_f(o.tong_tien) for o in dhs)
        dh_xuat = sum(_f(o.tong_tien) for o in dhs if o.trang_thai in ("DA_XUAT_HD", "HOAN_THANH"))
        dh_coc = sum(_f(o.thanh_toan_coc) for o in dhs if o.trang_thai != "HOAN_THANH")
        dm_tong = sum(_f(m.tong_tien) for m in dms)
        dm_tra_truoc = sum(_f(m.de_nghi_tt) for m in dms if _f(m.de_nghi_tt) > 0 and not m.tt_du)

        dong_moi = ",".join([luc.strftime("%Y-%m-%d %H:%M:%S"), _c(su_kien),
                             str(da_thu), str(phai_thu), str(da_tra), str(phai_tra),
                             str(dh_tong), str(dh_xuat), str(dh_tong - dh_xuat),
                             str(dh_coc), str(dm_tong), str(dm_tra_truoc)])

        if t_cu is not None:
            luu_tru.xoa(t_cu.duong_dan)
            db.delete(t_cu)
            db.flush()
        data = "\n".join([HEADER, dong_moi] + cu).encode("utf-8")
        ref = luu_tru.luu(data, "fin_ceo", "bien_dong", TEN, "text/csv")
        t = TepDinhKem(doi_tuong="FIN_CEO", doi_tuong_id=0, loai=(su_kien or "SNAPSHOT")[:20],
                       ten_file=TEN, duong_dan=ref, kich_thuoc=len(data), content_type="text/csv")
        db.add(t)
        return t
    except Exception:
        return None
