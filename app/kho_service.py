"""
Dịch vụ tồn kho DÙNG CHUNG — module Kho và Bán hàng cùng gọi.
Đây là cách 'liên thông': bán hàng xuất kho thì gọi đúng một logic, không lặp.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from .models import TonKho


def _lay_ton(db: Session, hang_hoa_id: int) -> TonKho:
    ton = db.query(TonKho).filter_by(hang_hoa_id=hang_hoa_id).with_for_update().first()
    if ton is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Hàng hóa {hang_hoa_id} chưa có bản ghi tồn")
    return ton


def nhap_ton(db: Session, hang_hoa_id: int, so_luong) -> None:
    ton = _lay_ton(db, hang_hoa_id)
    ton.so_luong = ton.so_luong + so_luong


def xuat_ton(db: Session, hang_hoa_id: int, so_luong) -> bool:
    """Trừ tồn (khóa dòng), kiểm đủ. Trả True nếu tồn xuống dưới mức tối thiểu — mặt hàng hiện ở
    Kho → Cảnh báo tồn với nút 🛒 Tạo PO (mua bù đến tồn max, mã KHO). Bỏ bước tự sinh đề xuất mua 10/10/2026."""
    ton = _lay_ton(db, hang_hoa_id)
    if so_luong > ton.so_luong:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Tồn không đủ cho hàng hóa {hang_hoa_id} (còn {ton.so_luong})")
    ton.so_luong = ton.so_luong - so_luong
    return ton.so_luong < ton.ton_min
