"""
Dịch vụ tồn kho DÙNG CHUNG — module Kho và Bán hàng cùng gọi.
Đây là cách 'liên thông': bán hàng xuất kho thì gọi đúng một logic, không lặp.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from .models import TonKho, YeuCauMua


def _lay_ton(db: Session, hang_hoa_id: int) -> TonKho:
    ton = db.query(TonKho).filter_by(hang_hoa_id=hang_hoa_id).with_for_update().first()
    if ton is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Hàng hóa {hang_hoa_id} chưa có bản ghi tồn")
    return ton


def nhap_ton(db: Session, hang_hoa_id: int, so_luong) -> None:
    ton = _lay_ton(db, hang_hoa_id)
    ton.so_luong = ton.so_luong + so_luong


def xuat_ton(db: Session, hang_hoa_id: int, so_luong) -> bool:
    """Trừ tồn (khóa dòng), kiểm đủ. Nếu xuống dưới min -> tự sinh yêu cầu mua.
    Trả True nếu đã sinh yêu cầu mua."""
    ton = _lay_ton(db, hang_hoa_id)
    if so_luong > ton.so_luong:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Tồn không đủ cho hàng hóa {hang_hoa_id} (còn {ton.so_luong})")
    ton.so_luong = ton.so_luong - so_luong
    if ton.so_luong < ton.ton_min:
        muc_tieu = ton.ton_max if ton.ton_max is not None else ton.ton_min
        db.add(YeuCauMua(hang_hoa_id=hang_hoa_id, so_luong=muc_tieu - ton.so_luong, ly_do="TON_DUOI_MIN"))
        return True
    return False
