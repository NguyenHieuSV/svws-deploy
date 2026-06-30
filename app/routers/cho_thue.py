"""
Module DỊCH VỤ CHO THUÊ — lát cắt dọc thứ bảy. TÁI DÙNG hạ tầng sẵn có:
  • xuất/nhập tài sản qua kho_service (như Bán hàng).
  • lập hóa đơn THUÊ + công nợ -> module Kế toán phát hành HĐĐT & thu tiền.
Đặc thù: hợp đồng định kỳ, thu phí theo kỳ, nhắc hết hạn.
"""
from decimal import Decimal
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..rbac import yeu_cau
from ..audit import ghi_audit
from ..kho_service import xuat_ton, nhap_ton
from ..models import (NguoiDung, KhachHang, HopDongThue, TaiSanThue, HoaDon, CongNo)
from ..schemas import HopDongThueVao, HopDongThueRa

router = APIRouter(prefix="/cho-thue", tags=["cho_thue"])
MODULE = "cho_thue"
THUE_SUAT = Decimal("0.10")  # cho thuê thiết bị thường 10% — nên cấu hình theo đối tượng
TU_KHO = {"HOA_CHAT", "VAT_TU", "THIET_BI"}


@router.get("/hop-dong", response_model=list[HopDongThueRa])
def ds_hop_dong(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(HopDongThue).order_by(HopDongThue.id.desc()).all()


# ----- Ký HĐ + xuất tài sản (HC/VT/TB trừ kho; NHAN_SU điều phối người) -----
@router.post("/hop-dong", response_model=HopDongThueRa, status_code=201)
def tao_hop_dong(data: HopDongThueVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.get(KhachHang, data.khach_hang_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khách hàng")
    hd = HopDongThue(so=data.so, khach_hang_id=data.khach_hang_id, doi_tuong=data.doi_tuong,
                     gia_thue=data.gia_thue, chu_ky=data.chu_ky,
                     ngay_bat_dau=data.ngay_bat_dau, ngay_ket_thuc=data.ngay_ket_thuc,
                     trang_thai="HIEU_LUC")
    db.add(hd); db.flush()
    if not hd.so:
        hd.so = f"HDT-{date.today():%Y%m%d}-{hd.id}"
    canh_bao_ton = []
    for ts in data.tai_san:
        db.add(TaiSanThue(hop_dong_thue_id=hd.id, hang_hoa_id=ts.hang_hoa_id,
                          nhan_vien_id=ts.nhan_vien_id, so_luong=ts.so_luong))
        if data.doi_tuong in TU_KHO:
            if ts.hang_hoa_id is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tài sản kho cần hang_hoa_id")
            if xuat_ton(db, ts.hang_hoa_id, ts.so_luong):
                canh_bao_ton.append(ts.hang_hoa_id)
    ghi_audit(db, nd.id, "TAO", "hop_dong_thue", hd.id,
              moi={"doi_tuong": data.doi_tuong, "gia_thue": float(data.gia_thue)})
    db.commit(); db.refresh(hd)
    return hd


# ----- Thu phí một kỳ: lập hóa đơn THUÊ + công nợ (bàn giao Kế toán) -----
@router.post("/hop-dong/{hd_id}/thu-phi")
def thu_phi_ky(hd_id: int, db: Session = Depends(get_db),
               nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    hd = db.get(HopDongThue, hd_id)
    if hd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hợp đồng")
    if hd.trang_thai != "HIEU_LUC":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Hợp đồng không còn hiệu lực")
    truoc_thue = hd.gia_thue
    thue = (truoc_thue * THUE_SUAT).quantize(Decimal("1"))
    hoa_don = HoaDon(loai="THUE", hop_dong_thue_id=hd.id, ngay=date.today(),
                     tien_truoc_thue=truoc_thue, tien_thue=thue, tong_tien=truoc_thue + thue,
                     hddt_trang_thai="CHUA_PHAT_HANH")
    db.add(hoa_don); db.flush()
    han = date.today() + timedelta(days=15)
    db.add(CongNo(loai="PHAI_THU", hoa_don_id=hoa_don.id, khach_hang_id=hd.khach_hang_id,
                  so_tien=hoa_don.tong_tien, han=han, trang_thai="CHUA_THU"))
    ghi_audit(db, nd.id, "TAO", "hoa_don", hoa_don.id,
              moi={"loai": "THUE", "hop_dong": hd.id, "tong_tien": float(hoa_don.tong_tien)})
    db.commit()
    return {"hop_dong_id": hd.id, "hoa_don_id": hoa_don.id,
            "tong_tien": float(hoa_don.tong_tien), "han_thu": str(han),
            "ghi_chu": "Hóa đơn THUÊ chờ phát hành HĐĐT ở module Kế toán."}


# ----- Chạy thu phí định kỳ cho mọi HĐ còn hiệu lực -----
@router.post("/chay-thu-phi-dinh-ky")
def chay_thu_phi(db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    hds = db.query(HopDongThue).filter_by(trang_thai="HIEU_LUC").all()
    ket_qua = []
    for hd in hds:
        truoc = hd.gia_thue
        thue = (truoc * THUE_SUAT).quantize(Decimal("1"))
        hoa_don = HoaDon(loai="THUE", hop_dong_thue_id=hd.id, ngay=date.today(),
                         tien_truoc_thue=truoc, tien_thue=thue, tong_tien=truoc + thue,
                         hddt_trang_thai="CHUA_PHAT_HANH")
        db.add(hoa_don); db.flush()
        db.add(CongNo(loai="PHAI_THU", hoa_don_id=hoa_don.id, khach_hang_id=hd.khach_hang_id,
                      so_tien=hoa_don.tong_tien, han=date.today() + timedelta(days=15),
                      trang_thai="CHUA_THU"))
        ket_qua.append({"hop_dong_id": hd.id, "hoa_don_id": hoa_don.id,
                        "tong_tien": float(hoa_don.tong_tien)})
    db.commit()
    return {"so_hop_dong_thu_phi": len(ket_qua), "chi_tiet": ket_qua}


# ----- Nhận trả tài sản: nhập lại kho + kết thúc HĐ -----
@router.post("/hop-dong/{hd_id}/nhan-tra")
def nhan_tra(hd_id: int, db: Session = Depends(get_db),
             nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    hd = db.get(HopDongThue, hd_id)
    if hd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hợp đồng")
    tra = 0
    for ts in hd.tai_san:
        if ts.ngay_tra is None and ts.hang_hoa_id is not None:
            nhap_ton(db, ts.hang_hoa_id, ts.so_luong)  # nhập lại kho
            ts.ngay_tra = date.today()
            tra += 1
    hd.trang_thai = "KET_THUC"
    ghi_audit(db, nd.id, "SUA", "hop_dong_thue", hd.id, moi={"trang_thai": "KET_THUC", "tai_san_tra": tra})
    db.commit()
    return {"hop_dong_id": hd.id, "tai_san_nhap_lai": tra, "trang_thai": "KET_THUC"}


# ----- Nhắc hợp đồng sắp hết hạn (≤ 30 ngày) -----
@router.get("/sap-het-han")
def sap_het_han(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    hom_nay = date.today()
    moc = hom_nay + timedelta(days=30)
    hds = db.query(HopDongThue).filter(
        HopDongThue.trang_thai == "HIEU_LUC",
        HopDongThue.ngay_ket_thuc >= hom_nay,
        HopDongThue.ngay_ket_thuc <= moc,
    ).all()
    ds = [{"hop_dong_id": h.id, "so": h.so, "khach_hang_id": h.khach_hang_id,
           "ngay_ket_thuc": str(h.ngay_ket_thuc),
           "con_ngay": (h.ngay_ket_thuc - hom_nay).days,
           "canh_bao": "Nhắc CEO + P.Kinh doanh — đề xuất gia hạn"} for h in hds]
    return {"hom_nay": str(hom_nay), "so_hop_dong_sap_het_han": len(ds), "danh_sach": ds}
