"""
Module BÁN HÀNG — lát cắt dọc thứ tư, minh họa LIÊN THÔNG rõ nhất:
  báo giá -> duyệt (han_muc 'bao_gia') -> đơn hàng -> XUẤT KHO (gọi kho_service)
  -> lập HÓA ĐƠN (BAN) + CÔNG NỢ (PHẢI THU) [bàn giao Kế toán].
"""
from decimal import Decimal
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..rbac import yeu_cau, kiem_han_muc
from ..deps import nhan_vien_id_cua
from ..audit import ghi_audit
from ..kho_service import xuat_ton
from ..models import (NguoiDung, KhachHang, HangHoa, BaoGia, BaoGiaCt,
                      DonHang, DonHangCt, PhieuKho, PhieuKhoCt, HoaDon, CongNo)
from ..schemas import (KhachHangVao, KhachHangRa, BaoGiaVao, BaoGiaRa, DonHangRa)

router = APIRouter(prefix="/ban-hang", tags=["ban_hang"])
MODULE = "ban_hang"
LOAI_DUYET = "bao_gia"   # khớp seed han_muc_duyet (TP_KD 100tr · CEO vô hạn)
THUE_SUAT = Decimal("0.08")


# ----- Khách hàng -----
@router.get("/khach-hang", response_model=list[KhachHangRa])
def ds_kh(q: str | None = None, db: Session = Depends(get_db),
          _=Depends(yeu_cau(MODULE, "XEM"))):
    qr = db.query(KhachHang)
    if q:
        like = f"%{q.strip()}%"
        qr = qr.filter(KhachHang.ten.ilike(like))
    return qr.order_by(KhachHang.ten).limit(50).all()


@router.post("/khach-hang", response_model=KhachHangRa, status_code=201)
def tao_kh(data: KhachHangVao, db: Session = Depends(get_db),
           nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    kh = KhachHang(ma=data.ma, ten=data.ten, ma_so_thue=data.ma_so_thue,
                   dien_thoai=data.dien_thoai, email=data.email, phan_loai_abc=data.phan_loai_abc,
                   nguoi_phu_trach=nhan_vien_id_cua(db, nd.id))
    db.add(kh); db.flush()
    ghi_audit(db, nd.id, "TAO", "khach_hang", kh.id, moi={"ten": data.ten})
    db.commit(); db.refresh(kh)
    return kh


# ----- Báo giá -----
@router.get("/bao-gia", response_model=list[BaoGiaRa])
def ds_bao_gia(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(BaoGia).order_by(BaoGia.id.desc()).all()


@router.post("/bao-gia", response_model=BaoGiaRa, status_code=201)
def tao_bao_gia(data: BaoGiaVao, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.get(KhachHang, data.khach_hang_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khách hàng")
    tong = sum(ct.so_luong * ct.don_gia for ct in data.chi_tiet)
    bg = BaoGia(so=data.so, khach_hang_id=data.khach_hang_id,
                nguoi_tao=nhan_vien_id_cua(db, nd.id), ngay=date.today(),
                tong_tien=tong, trang_thai="CHO_DUYET")
    db.add(bg); db.flush()
    if not bg.so:
        bg.so = f"BG-{date.today():%Y%m%d}-{bg.id}"
    for ct in data.chi_tiet:
        db.add(BaoGiaCt(bao_gia_id=bg.id, hang_hoa_id=ct.hang_hoa_id,
                        so_luong=ct.so_luong, don_gia=ct.don_gia))
    ghi_audit(db, nd.id, "TAO", "bao_gia", bg.id, moi={"tong_tien": float(tong)})
    db.commit(); db.refresh(bg)
    return bg


# ----- DUYỆT báo giá: XEM module + thẩm quyền theo han_muc (TP_KD 100tr / CEO ∞) -----
@router.post("/bao-gia/{bg_id}/duyet", response_model=BaoGiaRa)
def duyet_bao_gia(bg_id: int, db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "XEM"))):
    bg = db.get(BaoGia, bg_id)
    if bg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá")
    if bg.trang_thai != "CHO_DUYET":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Báo giá đang ở {bg.trang_thai}")
    kiem_han_muc(db, nd, LOAI_DUYET, bg.tong_tien)
    bg.trang_thai = "DA_DUYET"
    bg.nguoi_duyet = nhan_vien_id_cua(db, nd.id)
    ghi_audit(db, nd.id, "DUYET", "bao_gia", bg.id, moi={"trang_thai": "DA_DUYET"})
    db.commit(); db.refresh(bg)
    return bg


# ----- Tạo đơn hàng từ báo giá đã duyệt -----
@router.post("/bao-gia/{bg_id}/tao-don", response_model=DonHangRa, status_code=201)
def tao_don_tu_bao_gia(bg_id: int, db: Session = Depends(get_db),
                       nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    bg = db.get(BaoGia, bg_id)
    if bg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá")
    if bg.trang_thai != "DA_DUYET":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Báo giá chưa được duyệt")
    dh = DonHang(khach_hang_id=bg.khach_hang_id, bao_gia_id=bg.id, ngay=date.today(),
                 tong_tien=bg.tong_tien, trang_thai="MOI")
    db.add(dh); db.flush()
    dh.so = f"DH-{date.today():%Y%m%d}-{dh.id}"
    for ct in bg.chi_tiet:
        db.add(DonHangCt(don_hang_id=dh.id, hang_hoa_id=ct.hang_hoa_id,
                         so_luong=ct.so_luong, don_gia=ct.don_gia))
    ghi_audit(db, nd.id, "TAO", "don_hang", dh.id, moi={"tu_bao_gia": bg.id})
    db.commit(); db.refresh(dh)
    return dh


@router.get("/don-hang", response_model=list[DonHangRa])
def ds_don_hang(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(DonHang).order_by(DonHang.id.desc()).all()


# ----- XUẤT KHO: liên thông Kho + tạo Hóa đơn + Công nợ (giao dịch nguyên tử) -----
@router.post("/don-hang/{dh_id}/xuat-kho")
def xuat_kho_don_hang(dh_id: int, db: Session = Depends(get_db),
                      nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    dh = db.get(DonHang, dh_id)
    if dh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn hàng")
    if dh.trang_thai == "DA_XUAT":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Đơn đã xuất kho")

    # 1) Phiếu xuất + trừ tồn qua service dùng chung (tự sinh yêu cầu mua nếu < min)
    phieu = PhieuKho(loai="XUAT", don_hang_id=dh.id, ngay=date.today(),
                     nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(phieu); db.flush()
    phieu.so = f"PX-{date.today():%Y%m%d}-{phieu.id}"
    canh_bao_ton = []
    for ct in dh.chi_tiet:
        db.add(PhieuKhoCt(phieu_kho_id=phieu.id, hang_hoa_id=ct.hang_hoa_id, so_luong=ct.so_luong))
        if xuat_ton(db, ct.hang_hoa_id, ct.so_luong):
            canh_bao_ton.append(ct.hang_hoa_id)

    # 2) Hóa đơn BAN (chừa sẵn chỗ nối HĐĐT) + 3) Công nợ phải thu (bàn giao Kế toán)
    truoc_thue = dh.tong_tien
    thue = (truoc_thue * THUE_SUAT).quantize(Decimal("1"))
    hd = HoaDon(loai="BAN", don_hang_id=dh.id, ngay=date.today(),
                tien_truoc_thue=truoc_thue, tien_thue=thue, tong_tien=truoc_thue + thue,
                hddt_provider=None, hddt_trang_thai="CHUA_PHAT_HANH")
    db.add(hd); db.flush()
    cn = CongNo(loai="PHAI_THU", hoa_don_id=hd.id, khach_hang_id=dh.khach_hang_id,
                so_tien=hd.tong_tien, da_thanh_toan=0,
                han=date.today() + timedelta(days=30), trang_thai="CHUA_THU")
    db.add(cn)
    dh.trang_thai = "DA_XUAT"
    ghi_audit(db, nd.id, "XUAT", "don_hang", dh.id,
              moi={"phieu_xuat": phieu.id, "hoa_don": hd.id, "cong_no": float(hd.tong_tien)})
    db.commit()
    return {
        "don_hang_id": dh.id, "phieu_xuat": phieu.so,
        "hoa_don_id": hd.id, "tong_tien_hoa_don": float(hd.tong_tien),
        "cong_no_phai_thu": float(hd.tong_tien), "han_thu": str(cn.han),
        "canh_bao_ton_duoi_min": canh_bao_ton or None,
        "ghi_chu": "Hóa đơn chờ phát hành HĐĐT ở module Kế toán.",
    }
