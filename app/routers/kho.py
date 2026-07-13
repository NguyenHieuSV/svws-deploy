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
from ..rbac import yeu_cau, chi_vai_tro
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


# ----- XEM: PO đã xác nhận đặt hàng đang CHỜ NHẬP KHO -----
@router.get("/cho-nhap")
def ds_cho_nhap(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Danh sách đơn đặt hàng (PO) đã xác nhận với NCC nhưng chưa nhận đủ hàng —
    thủ kho bấm Tạo phiếu nhập, dữ liệu PO tự điền vào phiếu nhập kho."""
    from ..models import DonMua, DonMuaCt, NhaCungCap
    out = []
    q = (db.query(DonMua)
         .filter(DonMua.da_dat_hang.is_(True), DonMua.trang_thai == "DA_DUYET",
                 DonMua.trang_thai_nhan != "DU")
         .order_by(DonMua.id.desc()))
    for dm in q.all():
        ncc = db.get(NhaCungCap, dm.nha_cung_cap_id)
        ct = []
        for c in db.query(DonMuaCt).filter_by(don_mua_id=dm.id).all():
            con = float(c.so_luong or 0) - float(c.so_luong_nhan or 0)
            if con <= 0:
                continue
            hh = db.get(HangHoa, c.hang_hoa_id)
            ct.append({"don_mua_ct_id": c.id, "hang_hoa_id": c.hang_hoa_id,
                       "ten": hh.ten if hh else f"HH #{c.hang_hoa_id}",
                       "don_vi": hh.don_vi if hh else None,
                       "so_luong": float(c.so_luong or 0),
                       "da_nhan": float(c.so_luong_nhan or 0),
                       "con_lai": con, "don_gia": float(c.don_gia or 0)})
        out.append({"id": dm.id, "so": dm.so or f"PO-{dm.id}",
                    "ncc": ncc.ten if ncc else None,
                    "ngay_dat_hang": str(dm.ngay_dat_hang or dm.ngay or "")[:10],
                    "ngay_hen_giao": str(dm.ngay_hen_giao) if dm.ngay_hen_giao else None,
                    "tong_tien": float(dm.tong_tien or 0), "chi_tiet": ct})
    return out


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


# ----- DUYET: xóa hàng hóa (chỉ khi chưa phát sinh chứng từ, tồn = 0) -----
@router.delete("/hang-hoa/{hh_id}")
def xoa_hang_hoa(hh_id: int, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """Xóa hàng hóa khỏi danh mục. Chặn khi còn tồn kho hoặc đã xuất hiện trong
    báo giá, đơn hàng, đơn mua, phiếu kho, đề xuất mua, báo giá NCC, định mức,
    tài sản cho thuê (giữ vết chứng từ)."""
    from sqlalchemy import text as _sql
    from sqlalchemy.exc import IntegrityError
    hh = db.get(HangHoa, hh_id)
    if hh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hàng hóa")
    ton = db.query(TonKho).filter_by(hang_hoa_id=hh_id).first()
    if ton and (ton.so_luong or 0) > 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"'{hh.ten}' còn tồn kho {ton.so_luong} — xuất hết hoặc điều chỉnh tồn về 0 trước khi xóa.")
    refs = [("dòng báo giá", "bao_gia_ct"), ("dòng đơn hàng", "don_hang_ct"),
            ("dòng đơn mua", "don_mua_ct"), ("dòng phiếu kho", "phieu_kho_ct"),
            ("dòng đề xuất mua", "yeu_cau_mua_ct"), ("báo giá NCC", "bao_gia_ncc"),
            ("định mức tiêu hao", "dinh_muc_tieu_hao"), ("tài sản cho thuê", "tai_san_cho_thue")]
    ban = []
    for ten_ref, bang in refs:
        try:
            n = db.execute(_sql(f"SELECT COUNT(*) FROM {bang} WHERE hang_hoa_id = :i"),
                           {"i": hh_id}).scalar() or 0
        except Exception:
            n = 0
        if n:
            ban.append(f"{n} {ten_ref}")
    if ban:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"'{hh.ten}' đang gắn với {', '.join(ban)} — không thể xóa để giữ vết chứng từ.")
    ten_cu, ma_cu = hh.ten, hh.ma
    if ton:
        db.delete(ton)
    try:
        db.delete(hh)
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"'{ten_cu}' còn dữ liệu liên kết ở phân hệ khác nên không thể xóa.")
    ghi_audit(db, nd.id, "XOA", "hang_hoa", hh_id, cu={"ma": ma_cu, "ten": ten_cu})
    db.commit()
    return {"ok": True, "ten": ten_cu}


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
