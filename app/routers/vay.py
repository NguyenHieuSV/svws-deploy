"""
Module QUẢN LÝ TIỀN VAY — khế ước vay, lãi vay, lịch trả gốc/lãi theo kỳ, đáo hạn.
Hạch toán tự động: nhận tiền (Nợ 111/112 / Có 341); trả nợ (Nợ 341 gốc + Nợ 635 lãi / Có 111/112).
Cập nhật số dư quỹ tương ứng để đồng bộ với báo cáo tiền & dòng tiền.
Thuộc quyền module 'tai_chinh'.
"""
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..rbac import yeu_cau
from ..deps import nhan_vien_id_cua
from ..audit import ghi_audit
from ..models import NguoiDung, KhoanVay, LichTraNo, ButToan, TaiKhoanQuy
from ..schemas import KhoanVayVao
from ..vay_service import sinh_lich, them_thang

router = APIRouter(prefix="/vay", tags=["vay"])
MODULE = "tai_chinh"


def _f(x):
    return float(x or 0)


def _quy_theo_tk(db, tk):
    return db.query(TaiKhoanQuy).filter(TaiKhoanQuy.tk_ke_toan == tk,
                                        TaiKhoanQuy.hoat_dong.is_(True)).first()


def _vay_dict(db, v: KhoanVay):
    today = date.today()
    lich = db.query(LichTraNo).filter_by(khoan_vay_id=v.id).order_by(LichTraNo.ky).all()
    chua = [l for l in lich if not l.da_tra]
    qua_han = [l for l in chua if l.ngay_den_han < today]
    sap = chua[0] if chua else None
    lai_con = sum(_f(l.lai_phai_tra) for l in chua)
    return {
        "id": v.id, "so": v.so, "ben_cho_vay": v.ben_cho_vay, "loai": v.loai,
        "so_tien_goc": _f(v.so_tien_goc), "lai_suat_nam": _f(v.lai_suat_nam),
        "phuong_thuc": v.phuong_thuc, "ngay_nhan": str(v.ngay_nhan),
        "so_ky": v.so_ky, "chu_ky_thang": v.chu_ky_thang,
        "ngay_dao_han": str(v.ngay_dao_han) if v.ngay_dao_han else None,
        "tk_tien": v.tk_tien, "con_lai_goc": _f(v.con_lai_goc), "trang_thai": v.trang_thai,
        "lai_con_phai_tra": lai_con, "so_ky_chua_tra": len(chua), "so_ky_qua_han": len(qua_han),
        "ky_sap_toi": ({"ky": sap.ky, "ngay_den_han": str(sap.ngay_den_han),
                        "goc": _f(sap.goc_phai_tra), "lai": _f(sap.lai_phai_tra),
                        "tong": _f(sap.tong_phai_tra),
                        "qua_han": sap.ngay_den_han < today} if sap else None),
        "ghi_chu": v.ghi_chu,
    }


@router.post("", status_code=201)
def tao_khoan_vay(data: KhoanVayVao, db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    rows = sinh_lich(data.so_tien_goc, data.lai_suat_nam, data.so_ky,
                     data.chu_ky_thang, data.ngay_nhan, data.phuong_thuc)
    dao_han = rows[-1]["ngay_den_han"] if rows else them_thang(data.ngay_nhan, data.so_ky * data.chu_ky_thang)
    v = KhoanVay(so=data.so, ben_cho_vay=data.ben_cho_vay, loai=data.loai,
                 so_tien_goc=Decimal(data.so_tien_goc), lai_suat_nam=Decimal(data.lai_suat_nam),
                 phuong_thuc=data.phuong_thuc, ngay_nhan=data.ngay_nhan, so_ky=data.so_ky,
                 chu_ky_thang=data.chu_ky_thang, ngay_dao_han=dao_han, tk_tien=data.tk_tien,
                 con_lai_goc=Decimal(data.so_tien_goc), trang_thai="DANG_VAY", ghi_chu=data.ghi_chu)
    db.add(v); db.flush()
    for r in rows:
        db.add(LichTraNo(khoan_vay_id=v.id, **r))
    # Hạch toán nhận tiền vay: Nợ 111/112 / Có 341
    db.add(ButToan(tk_no=data.tk_tien, tk_co="341", so_tien=Decimal(data.so_tien_goc),
                   ngay=data.ngay_nhan, nguon="VAY", nguon_id=v.id,
                   dien_giai=f"Nhận tiền vay {data.ben_cho_vay}"))
    quy = _quy_theo_tk(db, data.tk_tien)
    if quy:
        quy.so_du = Decimal(quy.so_du) + Decimal(data.so_tien_goc)
    ghi_audit(db, nd.id, "TAO", "khoan_vay", v.id,
              moi={"ben": data.ben_cho_vay, "goc": float(data.so_tien_goc)})
    db.commit()
    return _vay_dict(db, v)


@router.get("")
def ds_khoan_vay(trang_thai: str | None = None, db: Session = Depends(get_db),
                 _=Depends(yeu_cau(MODULE, "XEM"))):
    q = db.query(KhoanVay)
    if trang_thai:
        q = q.filter(KhoanVay.trang_thai == trang_thai)
    return [_vay_dict(db, v) for v in q.order_by(KhoanVay.id.desc()).all()]


@router.get("/tong-quan")
def tong_quan_vay(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    today = date.today()
    vays = db.query(KhoanVay).filter_by(trang_thai="DANG_VAY").all()
    du_no = sum(_f(v.con_lai_goc) for v in vays)
    du_no_nh = sum(_f(v.con_lai_goc) for v in vays if v.loai == "NGAN_HAN")
    du_no_dh = sum(_f(v.con_lai_goc) for v in vays if v.loai == "DAI_HAN")
    chua = db.query(LichTraNo).join(KhoanVay).filter(
        LichTraNo.da_tra.is_(False), KhoanVay.trang_thai == "DANG_VAY").all()
    qua_han = [l for l in chua if l.ngay_den_han < today]
    return {"so_khoan": len(vays), "du_no_goc": du_no, "du_no_ngan_han": du_no_nh,
            "du_no_dai_han": du_no_dh,
            "lai_con_phai_tra": sum(_f(l.lai_phai_tra) for l in chua),
            "so_ky_qua_han": len(qua_han),
            "goc_qua_han": sum(_f(l.goc_phai_tra) for l in qua_han),
            "lai_qua_han": sum(_f(l.lai_phai_tra) for l in qua_han)}


@router.get("/sap-toi")
def lich_sap_toi(so_ngay: int = 30, db: Session = Depends(get_db),
                 _=Depends(yeu_cau(MODULE, "XEM"))):
    today = date.today()
    han = them_thang(today, 0)
    from datetime import timedelta
    moc = today + timedelta(days=so_ngay)
    rows = (db.query(LichTraNo, KhoanVay).join(KhoanVay)
            .filter(LichTraNo.da_tra.is_(False), KhoanVay.trang_thai == "DANG_VAY",
                    LichTraNo.ngay_den_han <= moc)
            .order_by(LichTraNo.ngay_den_han).all())
    ds = []
    for l, v in rows:
        ds.append({"khoan_vay_id": v.id, "so": v.so, "ben_cho_vay": v.ben_cho_vay,
                   "ky": l.ky, "ngay_den_han": str(l.ngay_den_han),
                   "goc": _f(l.goc_phai_tra), "lai": _f(l.lai_phai_tra),
                   "tong": _f(l.tong_phai_tra), "qua_han": l.ngay_den_han < today})
    return {"so_ngay": so_ngay, "so_ky": len(ds), "danh_sach": ds,
            "tong_phai_tra": sum(x["tong"] for x in ds)}


@router.get("/{vay_id}")
def chi_tiet_vay(vay_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    v = db.get(KhoanVay, vay_id)
    if v is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khoản vay")
    lich = db.query(LichTraNo).filter_by(khoan_vay_id=vay_id).order_by(LichTraNo.ky).all()
    today = date.today()
    return {**_vay_dict(db, v), "lich": [
        {"ky": l.ky, "ngay_den_han": str(l.ngay_den_han), "du_no_dau": _f(l.du_no_dau),
         "goc_phai_tra": _f(l.goc_phai_tra), "lai_phai_tra": _f(l.lai_phai_tra),
         "tong_phai_tra": _f(l.tong_phai_tra), "du_no_cuoi": _f(l.du_no_cuoi),
         "da_tra": bool(l.da_tra), "ngay_tra": str(l.ngay_tra) if l.ngay_tra else None,
         "qua_han": (not l.da_tra) and l.ngay_den_han < today} for l in lich]}


@router.post("/{vay_id}/tra-ky/{ky}")
def tra_ky(vay_id: int, ky: int, db: Session = Depends(get_db),
           nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    v = db.get(KhoanVay, vay_id)
    if v is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khoản vay")
    l = db.query(LichTraNo).filter_by(khoan_vay_id=vay_id, ky=ky).first()
    if l is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy kỳ trả nợ")
    if l.da_tra:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kỳ này đã trả.")
    # Hạch toán: Nợ 341 (gốc) / Có tiền ; Nợ 635 (lãi) / Có tiền
    if l.goc_phai_tra:
        db.add(ButToan(tk_no="341", tk_co=v.tk_tien, so_tien=l.goc_phai_tra, ngay=date.today(),
                       nguon="VAY", nguon_id=v.id, dien_giai=f"Trả gốc vay {v.ben_cho_vay} kỳ {ky}"))
    if l.lai_phai_tra:
        db.add(ButToan(tk_no="635", tk_co=v.tk_tien, so_tien=l.lai_phai_tra, ngay=date.today(),
                       nguon="VAY", nguon_id=v.id, dien_giai=f"Lãi vay {v.ben_cho_vay} kỳ {ky}"))
    quy = _quy_theo_tk(db, v.tk_tien)
    if quy:
        quy.so_du = Decimal(quy.so_du) - Decimal(l.tong_phai_tra)
    l.da_tra = True
    l.ngay_tra = date.today()
    v.con_lai_goc = Decimal(v.con_lai_goc) - Decimal(l.goc_phai_tra)
    con = db.query(LichTraNo).filter_by(khoan_vay_id=vay_id, da_tra=False).count()
    if con == 0 or Decimal(v.con_lai_goc) <= 0:
        v.trang_thai = "DA_TAT_TOAN"
    ghi_audit(db, nd.id, "THAO_TAC", "lich_tra_no", l.id,
              moi={"ky": ky, "goc": _f(l.goc_phai_tra), "lai": _f(l.lai_phai_tra)})
    db.commit()
    return _vay_dict(db, v)
