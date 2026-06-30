"""
Module TRÍCH LẬP QUỸ — phân biệt quỹ trích TRƯỚC thuế (được trừ) và SAU thuế
(không được trừ), tự hạch toán đúng tài khoản, theo dõi số dư và cảnh báo trần
theo Luật Thuế TNDN 2025: Quỹ KH&CN ≤ 20% thu nhập tính thuế; chi phúc lợi ≤ 1
tháng lương bình quân. Thuộc quyền module 'ke_toan'.
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
from ..models import NguoiDung, QuyTrichLap, GiaoDichQuy, ButToan, KyLuong
from ..schemas import TrichQuyVao, SuDungQuyVao

router = APIRouter(prefix="/quy-trich-lap", tags=["quy_trich_lap"])
MODULE = "ke_toan"
TL_KHCN = Decimal("0.20")   # trần Quỹ KH&CN: 20% thu nhập tính thuế (Luật TNDN 2025)


def _f(x):
    return float(x or 0)


def _nam_cua(ky):
    return ky[:4]


def _tong(db, ma, loai, nam):
    return _f(db.query(func.coalesce(func.sum(GiaoDichQuy.so_tien), 0))
              .filter(GiaoDichQuy.ma_quy == ma, GiaoDichQuy.loai == loai,
                      GiaoDichQuy.ky.like(nam + "%")).scalar())


def _quy_dict(db, q, nam):
    return {"ma": q.ma, "ten": q.ten, "ban_chat": q.ban_chat,
            "duoc_tru": q.ban_chat == "TRUOC_THUE",
            "tk_no": q.tk_no, "tk_co": q.tk_co, "gioi_han": q.gioi_han,
            "so_du": _f(q.so_du),
            "trich_nam": _tong(db, q.ma, "TRICH_LAP", nam),
            "su_dung_nam": _tong(db, q.ma, "SU_DUNG", nam)}


def _loi_nhuan_nam(db, nam):
    d1, d2 = date(int(nam), 1, 1), date(int(nam), 12, 31)
    def ps(tk, no=True):
        col = ButToan.tk_no if no else ButToan.tk_co
        return _f(db.query(func.coalesce(func.sum(ButToan.so_tien), 0))
                  .filter(col == tk, ButToan.ngay >= d1, ButToan.ngay <= d2).scalar())
    dt = ps("511", no=False)
    gv = ps("632", no=True)
    cp = sum(ps(t, no=True) for t in ("641", "642", "627"))
    return dt - gv - cp


def _luong_thang_bq(db, nam):
    tong = _f(db.query(func.coalesce(func.sum(KyLuong.tong_thu_nhap), 0))
              .filter(KyLuong.thang.like(nam + "%")).scalar())
    return tong / 12.0 if tong else 0.0


def _canh_bao(db, nam, thu_nhap_tinh_thue=None):
    cb = []
    # KH&CN ≤ 20% thu nhập tính thuế
    tntt = thu_nhap_tinh_thue if thu_nhap_tinh_thue is not None else max(0.0, _loi_nhuan_nam(db, nam))
    tran_khcn = round(tntt * float(TL_KHCN))
    trich_khcn = _tong(db, "KHCN", "TRICH_LAP", nam)
    if trich_khcn > tran_khcn:
        cb.append({"ma": "KHCN_20", "muc_do": "CAO", "tieu_de": "Quỹ KH&CN vượt trần 20%",
                   "chi_tiet": f"Đã trích {trich_khcn:,.0f}đ > trần 20% thu nhập tính thuế ({tran_khcn:,.0f}đ). Phần vượt không được trừ.",
                   "goi_y": "Giảm mức trích về ≤ 20% thu nhập tính thuế, hoặc loại phần vượt khi quyết toán."})
    # Chi phúc lợi ≤ 1 tháng lương bình quân
    luong_bq = _luong_thang_bq(db, nam)
    chi_pl = _tong(db, "PHUC_LOI", "SU_DUNG", nam)
    if luong_bq > 0 and chi_pl > luong_bq:
        cb.append({"ma": "PHUC_LOI", "muc_do": "TRUNG", "tieu_de": "Chi phúc lợi vượt 1 tháng lương bình quân",
                   "chi_tiet": f"Đã chi phúc lợi {chi_pl:,.0f}đ > trần 1 tháng lương bình quân ({luong_bq:,.0f}đ). Phần vượt không được trừ.",
                   "goi_y": "Phần chi phúc lợi vượt 1 tháng lương bình quân cần loại khỏi chi phí được trừ."})
    return {"nam": nam, "thu_nhap_tinh_thue": tntt, "tran_khcn": tran_khcn, "trich_khcn": trich_khcn,
            "luong_thang_bq": luong_bq, "chi_phuc_loi": chi_pl, "canh_bao": cb}


@router.get("/danh-muc")
def danh_muc(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    nam = str(date.today().year)
    return [_quy_dict(db, q, nam) for q in db.query(QuyTrichLap)
            .filter(QuyTrichLap.hoat_dong.is_(True)).order_by(QuyTrichLap.ban_chat, QuyTrichLap.ma).all()]


@router.get("")
def tong_quan(nam: str | None = None, db: Session = Depends(get_db),
              _=Depends(yeu_cau(MODULE, "XEM"))):
    nam = nam or str(date.today().year)
    quy = [_quy_dict(db, q, nam) for q in db.query(QuyTrichLap)
           .filter(QuyTrichLap.hoat_dong.is_(True)).order_by(QuyTrichLap.ban_chat, QuyTrichLap.ma).all()]
    return {"nam": nam,
            "tong_truoc_thue": sum(q["so_du"] for q in quy if q["duoc_tru"]),
            "tong_sau_thue": sum(q["so_du"] for q in quy if not q["duoc_tru"]),
            "quy": quy}


@router.get("/canh-bao")
def canh_bao(nam: str | None = None, thu_nhap_tinh_thue: float | None = None,
             db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return _canh_bao(db, nam or str(date.today().year), thu_nhap_tinh_thue)


@router.get("/{ma}/lich-su")
def lich_su(ma: str, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    rows = db.query(GiaoDichQuy).filter_by(ma_quy=ma).order_by(GiaoDichQuy.id.desc()).all()
    return [{"id": r.id, "loai": r.loai, "ky": r.ky, "ngay": str(r.ngay),
             "so_tien": _f(r.so_tien), "dien_giai": r.dien_giai} for r in rows]


@router.post("/trich")
def trich_lap(data: TrichQuyVao, db: Session = Depends(get_db),
              nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    q = db.get(QuyTrichLap, data.ma_quy)
    if q is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy quỹ")
    ngay = data.ngay or date.today()
    bt = ButToan(tk_no=q.tk_no, tk_co=q.tk_co, so_tien=Decimal(data.so_tien), ngay=ngay,
                 nguon="QUY", dien_giai=f"Trích lập {q.ten} kỳ {data.ky}")
    db.add(bt); db.flush()
    gd = GiaoDichQuy(ma_quy=q.ma, loai="TRICH_LAP", ky=data.ky, ngay=ngay,
                     so_tien=Decimal(data.so_tien), dien_giai=data.dien_giai,
                     but_toan_id=bt.id, nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(gd)
    q.so_du = Decimal(q.so_du) + Decimal(data.so_tien)
    ghi_audit(db, nd.id, "TRICH_LAP", "quy_trich_lap", None,
              moi={"quy": q.ma, "so_tien": _f(data.so_tien)})
    db.commit()
    nam = _nam_cua(data.ky)
    return {"quy": _quy_dict(db, q, nam), "canh_bao": _canh_bao(db, nam)["canh_bao"],
            "ban_chat": q.ban_chat, "duoc_tru": q.ban_chat == "TRUOC_THUE",
            "but_toan": {"no": q.tk_no, "co": q.tk_co, "so_tien": _f(data.so_tien)}}


@router.post("/su-dung")
def su_dung(data: SuDungQuyVao, db: Session = Depends(get_db),
            nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    q = db.get(QuyTrichLap, data.ma_quy)
    if q is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy quỹ")
    if Decimal(data.so_tien) > Decimal(q.so_du):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Số dư quỹ ({_f(q.so_du):,.0f}đ) không đủ để sử dụng {_f(data.so_tien):,.0f}đ.")
    ngay = data.ngay or date.today()
    # Dự phòng: hoàn nhập (Nợ tk_co dự phòng / Có tk_no chi phí). Quỹ khác: chi tiền (Nợ tk_co quỹ / Có 111).
    if q.ma.startswith("DP_"):
        tk_no, tk_co, dg = q.tk_co, q.tk_no, f"Hoàn nhập {q.ten} kỳ {data.ky}"
    else:
        tk_no, tk_co, dg = q.tk_co, "111", f"Chi từ {q.ten} kỳ {data.ky}"
    bt = ButToan(tk_no=tk_no, tk_co=tk_co, so_tien=Decimal(data.so_tien), ngay=ngay,
                 nguon="QUY", dien_giai=dg)
    db.add(bt); db.flush()
    db.add(GiaoDichQuy(ma_quy=q.ma, loai="SU_DUNG", ky=data.ky, ngay=ngay,
                       so_tien=Decimal(data.so_tien), dien_giai=data.dien_giai,
                       but_toan_id=bt.id, nguoi_tao=nhan_vien_id_cua(db, nd.id)))
    q.so_du = Decimal(q.so_du) - Decimal(data.so_tien)
    ghi_audit(db, nd.id, "SU_DUNG", "quy_trich_lap", None, moi={"quy": q.ma, "so_tien": _f(data.so_tien)})
    db.commit()
    nam = _nam_cua(data.ky)
    return {"quy": _quy_dict(db, q, nam), "canh_bao": _canh_bao(db, nam)["canh_bao"]}
