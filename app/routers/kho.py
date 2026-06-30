"""
Module KHO — lát cắt dọc mẫu. Mọi route gắn kiểm quyền qua yeu_cau("kho", "<mức>").
Cùng khuôn mẫu này áp cho ban_hang, ncc, du_an... chỉ đổi tên module.
"""
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..rbac import yeu_cau
from ..deps import nhan_vien_id_cua
from ..kho_service import nhap_ton, xuat_ton
from ..audit import ghi_audit
from ..models import NguoiDung, HangHoa, TonKho, PhieuKho, PhieuKhoCt, YeuCauMua
from ..schemas import HangHoaVao, HangHoaRa, HangHoaSua, PhieuKhoVao, PhieuKhoRa, DieuChinhVao

router = APIRouter(prefix="/kho", tags=["kho"])
MODULE = "kho"


def _ra(hh: HangHoa) -> HangHoaRa:
    return HangHoaRa(
        id=hh.id, ma=hh.ma, ten=hh.ten, loai=hh.loai, don_vi=hh.don_vi,
        gia_ban=hh.gia_ban or Decimal(0),
        so_luong=hh.ton.so_luong if hh.ton else Decimal(0),
        ton_min=hh.ton.ton_min if hh.ton else Decimal(0),
        ton_max=hh.ton.ton_max if hh.ton else None,
    )


# ----- XEM: danh sách hàng hóa kèm tồn -----
@router.get("/hang-hoa", response_model=list[HangHoaRa])
def ds_hang_hoa(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return [_ra(hh) for hh in db.query(HangHoa).order_by(HangHoa.id).all()]


# ----- THAO_TAC: tạo hàng hóa mới (kèm bản ghi tồn) -----
@router.post("/hang-hoa", response_model=HangHoaRa, status_code=201)
def tao_hang_hoa(
    data: HangHoaVao,
    db: Session = Depends(get_db),
    nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC")),
):
    hh = HangHoa(ma=data.ma, ten=data.ten, loai=data.loai, don_vi=data.don_vi, gia_ban=data.gia_ban)
    db.add(hh)
    db.flush()  # lấy hh.id
    db.add(TonKho(hang_hoa_id=hh.id, so_luong=0, ton_min=data.ton_min, ton_max=data.ton_max))
    ghi_audit(db, nd.id, "TAO", "hang_hoa", hh.id, moi={"ten": data.ten, "loai": data.loai})
    db.commit()
    db.refresh(hh)
    return _ra(hh)


# ----- THAO_TAC: sửa thông tin hàng hóa + ngưỡng tồn min/max + giá -----
@router.put("/hang-hoa/{hh_id}", response_model=HangHoaRa)
def sua_hang_hoa(
    hh_id: int,
    data: HangHoaSua,
    db: Session = Depends(get_db),
    nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC")),
):
    hh = db.get(HangHoa, hh_id)
    if hh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hàng hóa")
    if data.ten is not None:
        hh.ten = data.ten
    if data.loai is not None:
        hh.loai = data.loai
    if data.don_vi is not None:
        hh.don_vi = data.don_vi
    if data.gia_ban is not None:
        hh.gia_ban = data.gia_ban
    ton = hh.ton or db.query(TonKho).filter_by(hang_hoa_id=hh_id).first()
    if ton is None:
        ton = TonKho(hang_hoa_id=hh_id, so_luong=0, ton_min=0)
        db.add(ton)
    if data.ton_min is not None:
        ton.ton_min = data.ton_min
    if data.ton_max is not None:
        ton.ton_max = data.ton_max
    ghi_audit(db, nd.id, "SUA", "hang_hoa", hh.id,
              moi=data.model_dump(exclude_none=True, mode="json"))
    db.commit()
    db.refresh(hh)
    return _ra(hh)


# ----- XEM: phiếu kho -----
@router.get("/phieu", response_model=list[PhieuKhoRa])
def ds_phieu(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(PhieuKho).order_by(PhieuKho.id.desc()).all()


# ----- XEM: chi tiết một phiếu (kèm dòng hàng) -----
@router.get("/phieu/{phieu_id}")
def chi_tiet_phieu(phieu_id: int, db: Session = Depends(get_db),
                   _=Depends(yeu_cau(MODULE, "XEM"))):
    p = db.get(PhieuKho, phieu_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiếu")
    dong = []
    for ct in p.chi_tiet:
        hh = db.get(HangHoa, ct.hang_hoa_id)
        dong.append({"hang_hoa_id": ct.hang_hoa_id,
                     "ma": hh.ma if hh else None, "ten": hh.ten if hh else None,
                     "don_vi": hh.don_vi if hh else None,
                     "so_luong": float(ct.so_luong)})
    return {"id": p.id, "so": p.so, "loai": p.loai, "ngay": str(p.ngay),
            "don_hang_id": p.don_hang_id, "don_mua_id": p.don_mua_id, "chi_tiet": dong}


# ----- THAO_TAC: lập phiếu nhập/xuất (giao dịch nguyên tử + tự sinh yêu cầu mua) -----
@router.post("/phieu", response_model=PhieuKhoRa, status_code=201)
def lap_phieu(
    data: PhieuKhoVao,
    db: Session = Depends(get_db),
    nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC")),
):
    phieu = PhieuKho(loai=data.loai, so=data.so, ngay=date.today(),
                     nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(phieu)
    db.flush()
    if not phieu.so:
        phieu.so = f"{data.loai}-{date.today():%Y%m%d}-{phieu.id}"

    sinh_yeu_cau = []
    for ct in data.chi_tiet:
        db.add(PhieuKhoCt(phieu_kho_id=phieu.id, hang_hoa_id=ct.hang_hoa_id, so_luong=ct.so_luong))
        if data.loai == "NHAP":
            nhap_ton(db, ct.hang_hoa_id, ct.so_luong)
        elif xuat_ton(db, ct.hang_hoa_id, ct.so_luong):  # tự sinh yêu cầu mua nếu < min
            sinh_yeu_cau.append(ct.hang_hoa_id)

    ghi_audit(db, nd.id, "TAO", "phieu_kho", phieu.id,
              moi={"loai": data.loai, "so_dong": len(data.chi_tiet), "yeu_cau_mua": sinh_yeu_cau})
    db.commit()
    db.refresh(phieu)
    return phieu


# ----- DUYỆT: điều chỉnh tồn thủ công (kiểm kê) -> cần mức cao hơn -----
@router.post("/ton-kho/dieu-chinh")
def dieu_chinh_ton(
    data: DieuChinhVao,
    db: Session = Depends(get_db),
    nd: NguoiDung = Depends(yeu_cau(MODULE, "DUYET")),
):
    ton = db.query(TonKho).filter_by(hang_hoa_id=data.hang_hoa_id).with_for_update().first()
    if ton is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tồn")
    cu = float(ton.so_luong)
    ton.so_luong = data.so_luong_moi
    ghi_audit(db, nd.id, "DUYET", "ton_kho", ton.id,
              cu={"so_luong": cu}, moi={"so_luong": float(data.so_luong_moi), "ly_do": data.ly_do})
    db.commit()
    return {"hang_hoa_id": data.hang_hoa_id, "so_luong_cu": cu, "so_luong_moi": float(data.so_luong_moi)}


# ----- XEM: tổng quan kho (KPI) -----
@router.get("/tong-quan")
def tong_quan(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    so_mat_hang = 0
    duoi_min = 0
    gia_tri = Decimal(0)
    for hh in db.query(HangHoa).all():
        so_mat_hang += 1
        sl = hh.ton.so_luong if hh.ton else Decimal(0)
        tm = hh.ton.ton_min if hh.ton else Decimal(0)
        gia_tri += sl * (hh.gia_ban or Decimal(0))
        if sl < tm:
            duoi_min += 1
    so_phieu = db.query(func.count(PhieuKho.id)).scalar()
    yeu_cau_moi = db.query(func.count(YeuCauMua.id)).filter(YeuCauMua.trang_thai == "MOI").scalar()
    return {"so_mat_hang": so_mat_hang, "duoi_min": duoi_min,
            "gia_tri_ton": float(gia_tri), "so_phieu": so_phieu or 0,
            "yeu_cau_mua_moi": yeu_cau_moi or 0}
