"""
Module KẾ TOÁN — nhận hóa đơn + công nợ từ Bán hàng, phát hành HĐĐT, hạch toán, thu tiền.
Tích hợp HĐĐT qua hddt_gateway (thay được bằng MISA/VNPT/Viettel).
Hạch toán kép qua hach_toan (VAS / TT 200).
"""
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..rbac import yeu_cau
from ..audit import ghi_audit
from ..hddt_gateway import lay_provider
from ..hach_toan import hach_toan_hoa_don_ban, hach_toan_thu_tien
from ..models import NguoiDung, HoaDon, CongNo, ThanhToan, ButToan
from ..schemas import HoaDonRa, CongNoRa, ButToanRa, PhatHanhVao, ThuTienVao

router = APIRouter(prefix="/ke-toan", tags=["ke_toan"])
MODULE = "ke_toan"


# Danh sách hóa đơn: xem ke_toan_quy.ds_hoa_don (đã enrich đối tác/công nợ/mã bán).


# ----- Phát hành HĐĐT (gọi provider) + hạch toán doanh thu -----
@router.post("/hoa-don/{hd_id}/phat-hanh-hddt", response_model=HoaDonRa)
def phat_hanh_hddt(hd_id: int, data: PhatHanhVao = PhatHanhVao(),
                   db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    hd = db.get(HoaDon, hd_id)
    if hd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hóa đơn")
    if hd.hddt_trang_thai == "DA_PHAT_HANH":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Hóa đơn đã phát hành HĐĐT")
    # 1) Gọi cổng HĐĐT (thực tế: MISA/VNPT/Viettel)
    kq = lay_provider(data.provider).phat_hanh(hd)
    hd.hddt_provider = kq["provider"]
    hd.hddt_ma_tra_cuu = kq["ma_tra_cuu"]
    hd.hddt_trang_thai = kq["trang_thai"]
    # 2) Hạch toán doanh thu (chỉ hóa đơn bán, lần đầu)
    bts = hach_toan_hoa_don_ban(db, hd) if hd.loai in ("BAN", "THUE") else []
    ghi_audit(db, nd.id, "PHAT_HANH", "hoa_don", hd.id,
              moi={"provider": kq["provider"], "ma_tra_cuu": kq["ma_tra_cuu"], "so_but_toan": len(bts)})
    db.commit(); db.refresh(hd)
    return hd


@router.get("/cong-no", response_model=list[CongNoRa])
def ds_cong_no(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(CongNo).order_by(CongNo.id.desc()).all()


# ----- Thu tiền công nợ + hạch toán + tự đóng khi đủ -----
@router.post("/cong-no/{cn_id}/thu-tien", response_model=CongNoRa)
def thu_tien(cn_id: int, data: ThuTienVao, db: Session = Depends(get_db),
             nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    cn = db.query(CongNo).filter_by(id=cn_id).with_for_update().first()
    if cn is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy công nợ")
    con_lai = cn.so_tien - cn.da_thanh_toan
    if data.so_tien > con_lai:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Vượt số còn phải thu ({con_lai})")
    db.add(ThanhToan(cong_no_id=cn.id, so_tien=data.so_tien, ngay=date.today(), hinh_thuc=data.hinh_thuc))
    cn.da_thanh_toan = cn.da_thanh_toan + data.so_tien
    cn.trang_thai = "THU_DU" if cn.da_thanh_toan >= cn.so_tien else "THU_MOT_PHAN"
    hach_toan_thu_tien(db, cn, data.so_tien, tien_mat=(data.hinh_thuc == "TM"))
    ghi_audit(db, nd.id, "THU_TIEN", "cong_no", cn.id,
              moi={"so_tien": float(data.so_tien), "trang_thai": cn.trang_thai})
    db.commit(); db.refresh(cn)
    return cn


@router.get("/so-cai", response_model=list[ButToanRa])
def so_cai(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(ButToan).order_by(ButToan.id).all()
