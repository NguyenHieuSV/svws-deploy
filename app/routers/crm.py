"""
Module CRM — lát cắt dọc thứ tám (khép bộ). Minh họa:
  • Hồ sơ KH 360°: tổng hợp LIÊN MODULE (báo giá, đơn hàng, công nợ).
  • Phân loại ABC TỰ ĐỘNG theo doanh số.
  • Chăm sóc sau bán: lên lịch +7/+30 ngày, nhắc đến hạn, ghi CSAT.
  • Khiếu nại với SLA 24h.
"""
from decimal import Decimal
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..rbac import yeu_cau
from ..deps import nhan_vien_id_cua
from ..audit import ghi_audit
from ..models import (NguoiDung, KhachHang, BaoGia, DonHang, CongNo, ChamSocKH)
from ..schemas import ChamSocVao, ChamSocRa, HoanThanhVao

router = APIRouter(prefix="/crm", tags=["crm"])
MODULE = "crm"
# Ngưỡng phân loại ABC theo doanh số luỹ kế (VND) — tham số, chỉnh tại đây
NGUONG_A = Decimal("500000000")
NGUONG_B = Decimal("100000000")


def xep_loai_abc(doanh_so: Decimal) -> str:
    if doanh_so >= NGUONG_A:
        return "A"
    if doanh_so >= NGUONG_B:
        return "B"
    return "C"


def _doanh_so_kh(db: Session, kh_id: int) -> Decimal:
    """Doanh số = tổng công nợ phải thu đã phát sinh (gồm bán hàng + cho thuê)."""
    return db.query(func.coalesce(func.sum(CongNo.so_tien), 0)) \
             .filter(CongNo.khach_hang_id == kh_id, CongNo.loai == "PHAI_THU").scalar() or Decimal(0)


# ----- Hồ sơ KH 360° (tổng hợp liên module) -----
@router.get("/khach-hang/{kh_id}")
def ho_so_360(kh_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    kh = db.get(KhachHang, kh_id)
    if kh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khách hàng")
    so_bao_gia = db.query(func.count(BaoGia.id)).filter_by(khach_hang_id=kh_id).scalar()
    so_don_hang = db.query(func.count(DonHang.id)).filter_by(khach_hang_id=kh_id).scalar()
    doanh_so = _doanh_so_kh(db, kh_id)
    con_phai_thu = db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0)) \
        .filter(CongNo.khach_hang_id == kh_id, CongNo.loai == "PHAI_THU",
                CongNo.trang_thai != "THU_DU").scalar()
    lich_su = db.query(ChamSocKH).filter_by(khach_hang_id=kh_id) \
        .order_by(ChamSocKH.id.desc()).limit(5).all()
    return {
        "khach_hang": {"id": kh.id, "ten": kh.ten, "phan_loai_abc": kh.phan_loai_abc},
        "so_bao_gia": so_bao_gia, "so_don_hang": so_don_hang,
        "doanh_so_luy_ke": float(doanh_so), "con_phai_thu": float(con_phai_thu),
        "cham_soc_gan_day": [{"loai": c.loai, "ngay_hen": str(c.ngay_hen),
                              "trang_thai": c.trang_thai, "csat": float(c.csat) if c.csat else None}
                             for c in lich_su],
    }


# ----- Phân loại ABC tự động cho toàn bộ KH -----
@router.post("/phan-loai-abc")
def phan_loai_abc(db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    kqs = {"A": 0, "B": 0, "C": 0}
    for kh in db.query(KhachHang).all():
        loai = xep_loai_abc(_doanh_so_kh(db, kh.id))
        kh.phan_loai_abc = loai
        kqs[loai] += 1
    ghi_audit(db, nd.id, "SUA", "khach_hang", None, moi={"phan_loai_abc": kqs})
    db.commit()
    return {"da_phan_loai": sum(kqs.values()), "theo_nhom": kqs}


# ----- Lên lịch chăm sóc sau bán (+7 / +30 ngày) từ một đơn hàng -----
@router.post("/len-lich-sau-ban/{don_hang_id}")
def len_lich_sau_ban(don_hang_id: int, db: Session = Depends(get_db),
                     nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    dh = db.get(DonHang, don_hang_id)
    if dh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn hàng")
    kh = db.get(KhachHang, dh.khach_hang_id)
    tasks = []
    for so_ngay in (7, 30):
        t = ChamSocKH(khach_hang_id=dh.khach_hang_id, loai="GOI",
                      noi_dung=f"Chăm sóc sau bán đơn {dh.so} (+{so_ngay} ngày)",
                      ngay_hen=dh.ngay + timedelta(days=so_ngay), trang_thai="CHO",
                      nguoi_phu_trach=kh.nguoi_phu_trach if kh else None)
        db.add(t); tasks.append(t)
    db.flush()
    ghi_audit(db, nd.id, "TAO", "cham_soc_kh", None,
              moi={"don_hang": don_hang_id, "so_task": len(tasks)})
    db.commit()
    return {"don_hang_id": don_hang_id, "so_lich_tao": len(tasks),
            "ngay_hen": [str(t.ngay_hen) for t in tasks]}


# ----- Tạo việc chăm sóc / khiếu nại thủ công -----
@router.post("/cham-soc", response_model=ChamSocRa, status_code=201)
def tao_cham_soc(data: ChamSocVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.get(KhachHang, data.khach_hang_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khách hàng")
    cs = ChamSocKH(khach_hang_id=data.khach_hang_id, loai=data.loai, noi_dung=data.noi_dung,
                   ngay_hen=data.ngay_hen or date.today(), trang_thai="CHO",
                   nguoi_phu_trach=nhan_vien_id_cua(db, nd.id))
    db.add(cs); db.flush()
    ghi_audit(db, nd.id, "TAO", "cham_soc_kh", cs.id, moi={"loai": data.loai})
    db.commit(); db.refresh(cs)
    return cs


# ----- Hoàn thành việc chăm sóc + ghi CSAT -----
@router.post("/cham-soc/{cs_id}/hoan-thanh", response_model=ChamSocRa)
def hoan_thanh(cs_id: int, data: HoanThanhVao, db: Session = Depends(get_db),
               nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    cs = db.get(ChamSocKH, cs_id)
    if cs is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy việc chăm sóc")
    cs.trang_thai = "HOAN_THANH"
    cs.ngay_thuc_hien = date.today()
    if data.csat is not None:
        cs.csat = data.csat
    if data.noi_dung:
        cs.noi_dung = data.noi_dung
    ghi_audit(db, nd.id, "SUA", "cham_soc_kh", cs.id,
              moi={"trang_thai": "HOAN_THANH", "csat": float(data.csat) if data.csat else None})
    db.commit(); db.refresh(cs)
    return cs


# ----- Nhắc việc chăm sóc đến hạn -----
@router.get("/cham-soc/den-han", response_model=list[ChamSocRa])
def den_han(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(ChamSocKH).filter(
        ChamSocKH.trang_thai == "CHO", ChamSocKH.ngay_hen <= date.today()
    ).order_by(ChamSocKH.ngay_hen).all()


# ----- Khiếu nại quá hạn SLA 24h (chưa xử lý sau 1 ngày) -----
@router.get("/khieu-nai/qua-han")
def khieu_nai_qua_han(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    moc = date.today() - timedelta(days=1)
    rows = db.query(ChamSocKH).filter(
        ChamSocKH.loai == "KHIEU_NAI", ChamSocKH.trang_thai == "CHO",
        func.date(ChamSocKH.created_at) <= moc,
    ).all()
    return {"so_khieu_nai_qua_han_24h": len(rows),
            "danh_sach": [{"id": r.id, "khach_hang_id": r.khach_hang_id,
                           "noi_dung": r.noi_dung} for r in rows]}


# ----- Tổng quan CRM (KPI một lần gọi) -----
@router.get("/tong-quan")
def tong_quan(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    abc = {"A": 0, "B": 0, "C": 0}
    chua_xep = 0
    for kh in db.query(KhachHang).all():
        if kh.phan_loai_abc in abc:
            abc[kh.phan_loai_abc] += 1
        else:
            chua_xep += 1
    den_han = db.query(func.count(ChamSocKH.id)).filter(
        ChamSocKH.trang_thai == "CHO", ChamSocKH.ngay_hen <= date.today()).scalar()
    moc = date.today() - timedelta(days=1)
    kn = db.query(func.count(ChamSocKH.id)).filter(
        ChamSocKH.loai == "KHIEU_NAI", ChamSocKH.trang_thai == "CHO",
        func.date(ChamSocKH.created_at) <= moc).scalar()
    csat = db.query(func.avg(ChamSocKH.csat)).filter(ChamSocKH.csat.isnot(None)).scalar()
    return {
        "so_kh": sum(abc.values()) + chua_xep,
        "abc": abc, "chua_xep": chua_xep,
        "den_han": den_han or 0, "khieu_nai_qua_han": kn or 0,
        "csat_tb": round(float(csat), 2) if csat else None,
    }
