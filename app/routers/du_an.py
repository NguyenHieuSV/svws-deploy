"""
Module DỰ ÁN — lát cắt dọc thứ ba.
Điểm đặc thù:
  • Dự toán vs chi phí thực tế (cảnh báo vượt ngân sách).
  • Duyệt chi phí 3 CẤP theo han_muc 'chi_phi_du_an' (TP_DA 5tr · KTT 50tr · CEO vô hạn).
  • NỐI FORECAST CAL: nhập dự toán từ export, và endpoint đối chiếu thực tế/dự toán
    theo hạng mục để Forecast Cal cập nhật catalog giá (vòng phản hồi).
"""
import os, json, uuid
from decimal import Decimal
from datetime import date
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..config import settings
from ..rbac import yeu_cau, kiem_han_muc
from ..audit import ghi_audit
from ..deps import nhan_vien_id_cua
from ..models import (NguoiDung, NhanVien, DuAn, DuToanCt, DuAnChiPhi, NghiemThu,
                      DuAnThietKe, DuAnMoc, DuAnAnToan, DuAnNhatKy, DuAnTaiLieu,
                      DuAnKpi, DuAnBaoCao, DuAnChiTieu)
from ..schemas import (DuAnVao, DuAnRa, NhapDuToanVao, ChiPhiVao, ChiPhiRa, NghiemThuVao,
                       DuAnThongTinVao, ThietKeVao, MocVao, MocSuaVao, AnToanVao,
                       NhatKyVao, TaiLieuMetaVao, KpiVao, BaoCaoVao, ChiTieuVao, NapChiTieuVao, PhanTichVao)

router = APIRouter(prefix="/du-an", tags=["du_an"])
MODULE = "du_an"
LOAI_DUYET = "chi_phi_du_an"  # khớp seed han_muc_duyet (TP_DA/KTT/CEO)


# ----- XEM: danh sách dự án -----
@router.get("", response_model=list[DuAnRa])
def ds_du_an(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(DuAn).order_by(DuAn.id).all()


# ----- THAO_TAC: tạo dự án -----
@router.post("", response_model=DuAnRa, status_code=201)
def tao_du_an(data: DuAnVao, db: Session = Depends(get_db),
              nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    da = DuAn(ma=data.ma, ten=data.ten, khach_hang_id=data.khach_hang_id,
              qcvn=data.qcvn, deadline=data.deadline, du_toan=0, chi_phi_thuc_te=0,
              trang_thai="MOI")
    db.add(da)
    db.flush()
    ghi_audit(db, nd.id, "TAO", "du_an", da.id, moi={"ten": data.ten})
    db.commit()
    db.refresh(da)
    return da


# ----- THAO_TAC: nhập dự toán từ FORECAST CAL (thay thế breakdown cũ) -----
@router.post("/{da_id}/nhap-du-toan-forecast", response_model=DuAnRa)
def nhap_du_toan_forecast(da_id: int, data: NhapDuToanVao, db: Session = Depends(get_db),
                          nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    da = db.get(DuAn, da_id)
    if da is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án")
    db.query(DuToanCt).filter_by(du_an_id=da_id).delete()
    tong = Decimal(0)
    for ln in data.lines:
        tt = (ln.so_luong or 0) * (ln.don_gia or 0)
        tong += tt
        db.add(DuToanCt(du_an_id=da_id, hang_muc=ln.hang_muc, mo_ta=ln.mo_ta,
                        so_luong=ln.so_luong, don_gia=ln.don_gia, thanh_tien=tt,
                        nguon=data.nguon))
    da.du_toan = tong
    if da.trang_thai == "MOI":
        da.trang_thai = "DANG_CHAY"
    ghi_audit(db, nd.id, "SUA", "du_an", da_id,
              moi={"du_toan": float(tong), "so_dong": len(data.lines), "nguon": data.nguon})
    db.commit()
    db.refresh(da)
    return da


# ----- THAO_TAC: ghi nhận chi phí thực tế (chờ duyệt). NV_DA ghi được. -----
@router.post("/{da_id}/chi-phi", response_model=ChiPhiRa, status_code=201)
def ghi_chi_phi(da_id: int, data: ChiPhiVao, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    da = db.get(DuAn, da_id)
    if da is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án")
    cp = DuAnChiPhi(du_an_id=da_id, hang_muc=data.hang_muc, mo_ta=data.mo_ta,
                    so_tien=data.so_tien, trang_thai="CHO_DUYET", ngay=date.today())
    db.add(cp)
    db.flush()
    ghi_audit(db, nd.id, "TAO", "du_an_chi_phi", cp.id,
              moi={"so_tien": float(data.so_tien), "trang_thai": "CHO_DUYET"})
    db.commit()
    db.refresh(cp)
    return cp


# ----- DUYỆT chi phí: XEM module + thẩm quyền theo han_muc (3 cấp) -----
@router.post("/chi-phi/{cp_id}/duyet")
def duyet_chi_phi(cp_id: int, db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "XEM"))):  # quyền duyệt do han_muc
    cp = db.get(DuAnChiPhi, cp_id)
    if cp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy chi phí")
    if cp.trang_thai != "CHO_DUYET":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Chi phí đang ở {cp.trang_thai}")
    # ★ thẩm quyền + trần theo từng cấp: TP_DA 5tr, KTT 50tr, CEO vô hạn
    kiem_han_muc(db, nd, LOAI_DUYET, cp.so_tien)
    cp.trang_thai = "DA_DUYET"
    da = db.get(DuAn, cp.du_an_id)
    da.chi_phi_thuc_te = (da.chi_phi_thuc_te or 0) + cp.so_tien
    # TỰ ĐỘNG: vượt dự toán -> cảnh báo
    vuot = da.du_toan and da.chi_phi_thuc_te > da.du_toan
    ghi_audit(db, nd.id, "DUYET", "du_an_chi_phi", cp.id,
              moi={"chi_phi_thuc_te": float(da.chi_phi_thuc_te), "vuot_du_toan": bool(vuot)})
    db.commit()
    return {
        "chi_phi_id": cp.id, "trang_thai": "DA_DUYET",
        "chi_phi_thuc_te": float(da.chi_phi_thuc_te), "du_toan": float(da.du_toan or 0),
        "vuot_du_toan": bool(vuot),
        "canh_bao": "VƯỢT DỰ TOÁN — cảnh báo Giám đốc" if vuot else None,
    }


# ----- XEM: ĐỐI CHIẾU dự toán (Forecast Cal) vs thực tế theo hạng mục -----
# Đây là dữ liệu Forecast Cal nạp lại để cập nhật catalog giá (vòng phản hồi).
@router.get("/{da_id}/doi-chieu-forecast")
def doi_chieu_forecast(da_id: int, db: Session = Depends(get_db),
                       _=Depends(yeu_cau(MODULE, "XEM"))):
    da = db.get(DuAn, da_id)
    if da is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án")
    dt = defaultdict(Decimal)
    for r in db.query(DuToanCt).filter_by(du_an_id=da_id).all():
        dt[r.hang_muc or "(khác)"] += r.thanh_tien or 0
    tt = defaultdict(Decimal)
    for r in db.query(DuAnChiPhi).filter_by(du_an_id=da_id, trang_thai="DA_DUYET").all():
        tt[r.hang_muc or "(khác)"] += r.so_tien or 0
    rows = []
    for hm in sorted(set(dt) | set(tt)):
        d, t = dt.get(hm, Decimal(0)), tt.get(hm, Decimal(0))
        rows.append({
            "hang_muc": hm, "du_toan": float(d), "thuc_te": float(t),
            "chenh_lech": float(t - d),
            "ty_le_thuc_te_tren_du_toan": round(float(t / d), 3) if d else None,
        })
    return {
        "du_an_id": da_id, "nguon_du_toan": "FORECAST_CAL",
        "tong_du_toan": float(da.du_toan or 0), "tong_thuc_te": float(da.chi_phi_thuc_te or 0),
        "theo_hang_muc": rows,
        "ghi_chu": "Forecast Cal dùng cột chenh_lech/ty_le để hiệu chỉnh catalog giá.",
    }


# ----- DUYỆT: nghiệm thu (QCVN/B8) -----
@router.post("/{da_id}/nghiem-thu")
def nghiem_thu(da_id: int, data: NghiemThuVao, db: Session = Depends(get_db),
               nd: NguoiDung = Depends(yeu_cau(MODULE, "DUYET"))):
    da = db.get(DuAn, da_id)
    if da is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án")
    db.add(NghiemThu(du_an_id=da_id, ket_qua_qcvn=data.ket_qua_qcvn, khach_ky=data.khach_ky))
    da.trang_thai = "HOAN_THANH" if data.khach_ky else "NGHIEM_THU"
    ghi_audit(db, nd.id, "DUYET", "nghiem_thu", da_id,
              moi={"qcvn": data.ket_qua_qcvn, "khach_ky": data.khach_ky})
    db.commit()
    return {"du_an_id": da_id, "trang_thai": da.trang_thai, "ket_qua_qcvn": data.ket_qua_qcvn}


# ==================== DỰ ÁN MỞ RỘNG ====================
def _f(x):
    return float(x or 0)


def _da_404(db, da_id):
    da = db.get(DuAn, da_id)
    if da is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án")
    return da


def _ten_nv(db, nid):
    if not nid:
        return None
    nv = db.get(NhanVien, nid)
    return nv.ho_ten if nv else None


def _nguoi(db, nd):
    return _ten_nv(db, nhan_vien_id_cua(db, nd.id)) or nd.email


def _tinh_tien_do(db, da_id):
    """% tiến độ tổng = Σ(trọng số × %)/Σ trọng số — tính trên dữ liệu mốc thực tế."""
    mocs = db.query(DuAnMoc).filter_by(du_an_id=da_id).all()
    if not mocs:
        td = 0.0
    else:
        tts = sum(_f(m.trong_so) for m in mocs)
        if tts > 0:
            td = sum(_f(m.trong_so) * _f(m.phan_tram) for m in mocs) / tts
        else:
            td = sum(_f(m.phan_tram) for m in mocs) / len(mocs)
    da = db.get(DuAn, da_id)
    if da:
        da.tien_do = round(td, 2)
    return round(td, 2)


def _thong_so_ra(tk):
    if not tk or not tk.thong_so:
        return []
    try:
        return json.loads(tk.thong_so)
    except Exception:
        return tk.thong_so


# ----- Thông tin dự án -----
@router.get("/{da_id}/chi-tiet")
def chi_tiet(da_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    da = _da_404(db, da_id)
    tk = db.get(DuAnThietKe, da_id)
    cnt = lambda M: db.query(func.count()).select_from(M).filter(M.du_an_id == da_id).scalar()
    at_mo = db.query(func.count()).select_from(DuAnAnToan).filter(
        DuAnAnToan.du_an_id == da_id, DuAnAnToan.trang_thai != "DA_KIEM_SOAT").scalar()
    return {
        "id": da.id, "ma": da.ma, "ten": da.ten, "khach_hang_id": da.khach_hang_id,
        "truong_du_an": da.truong_du_an, "truong_du_an_ten": _ten_nv(db, da.truong_du_an),
        "chu_dau_tu": da.chu_dau_tu, "dia_diem": da.dia_diem, "loai_du_an": da.loai_du_an,
        "cong_suat": da.cong_suat, "gia_tri_hop_dong": _f(da.gia_tri_hop_dong), "qcvn": da.qcvn,
        "ngay_bat_dau": str(da.ngay_bat_dau) if da.ngay_bat_dau else None,
        "ngay_kt_ke_hoach": str(da.ngay_kt_ke_hoach) if da.ngay_kt_ke_hoach else None,
        "ngay_kt_thuc_te": str(da.ngay_kt_thuc_te) if da.ngay_kt_thuc_te else None,
        "deadline": str(da.deadline) if da.deadline else None,
        "trang_thai": da.trang_thai, "mo_ta": da.mo_ta, "tien_do": _f(da.tien_do),
        "tieu_chuan_dau_ra": da.tieu_chuan_dau_ra,
        "du_toan": _f(da.du_toan), "chi_phi_thuc_te": _f(da.chi_phi_thuc_te),
        "con_lai_du_toan": _f(da.du_toan) - _f(da.chi_phi_thuc_te),
        "thiet_ke": ({"cong_nghe": tk.cong_nghe, "cong_suat_tk": tk.cong_suat_tk,
                      "tieu_chuan": tk.tieu_chuan, "thong_so": _thong_so_ra(tk),
                      "nguoi_thiet_ke": tk.nguoi_thiet_ke,
                      "ngay_duyet": str(tk.ngay_duyet) if tk.ngay_duyet else None,
                      "phien_ban": tk.phien_ban, "trang_thai": tk.trang_thai,
                      "ghi_chu": tk.ghi_chu} if tk else None),
        "so_moc": cnt(DuAnMoc), "so_an_toan_mo": at_mo, "so_tai_lieu": cnt(DuAnTaiLieu),
        "so_kpi": cnt(DuAnKpi), "so_nhat_ky": cnt(DuAnNhatKy),
    }


@router.put("/{da_id}/thong-tin")
def cap_nhat_thong_tin(da_id: int, data: DuAnThongTinVao, db: Session = Depends(get_db),
                       nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    da = _da_404(db, da_id)
    for k in ("ten", "ma", "khach_hang_id", "truong_du_an", "chu_dau_tu", "dia_diem",
              "loai_du_an", "cong_suat", "gia_tri_hop_dong", "qcvn", "ngay_bat_dau",
              "ngay_kt_ke_hoach", "ngay_kt_thuc_te", "deadline", "trang_thai", "mo_ta",
              "tieu_chuan_dau_ra"):
        v = getattr(data, k)
        if v is not None:
            setattr(da, k, v)
    ghi_audit(db, nd.id, "CAP_NHAT", "du_an", da_id, moi={"thong_tin": True})
    db.commit()
    return chi_tiet(da_id, db, nd)


# ----- Thiết kế -----
@router.put("/{da_id}/thiet-ke")
def luu_thiet_ke(da_id: int, data: ThietKeVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    _da_404(db, da_id)
    tk = db.get(DuAnThietKe, da_id)
    if tk is None:
        tk = DuAnThietKe(du_an_id=da_id)
        db.add(tk)
    for k in ("cong_nghe", "cong_suat_tk", "tieu_chuan", "nguoi_thiet_ke",
              "ngay_duyet", "phien_ban", "trang_thai", "ghi_chu"):
        v = getattr(data, k)
        if v is not None:
            setattr(tk, k, v)
    if data.thong_so is not None:
        tk.thong_so = json.dumps(data.thong_so, ensure_ascii=False) if isinstance(data.thong_so, list) else data.thong_so
    ghi_audit(db, nd.id, "CAP_NHAT", "du_an_thiet_ke", da_id, moi={"thiet_ke": True})
    db.commit()
    return chi_tiet(da_id, db, nd)["thiet_ke"]


# ----- Tiến độ (mốc) -----
def _moc_ra(m):
    return {"id": m.id, "thu_tu": m.thu_tu, "ten": m.ten, "giai_doan": m.giai_doan,
            "ngay_bd_kh": str(m.ngay_bd_kh) if m.ngay_bd_kh else None,
            "ngay_kt_kh": str(m.ngay_kt_kh) if m.ngay_kt_kh else None,
            "ngay_kt_tt": str(m.ngay_kt_tt) if m.ngay_kt_tt else None,
            "trong_so": _f(m.trong_so), "phan_tram": _f(m.phan_tram),
            "trang_thai": m.trang_thai, "phu_trach": m.phu_trach, "ghi_chu": m.ghi_chu}


@router.get("/{da_id}/moc")
def ds_moc(da_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    ms = db.query(DuAnMoc).filter_by(du_an_id=da_id).order_by(DuAnMoc.thu_tu, DuAnMoc.id).all()
    return {"tien_do": _f(db.get(DuAn, da_id).tien_do), "moc": [_moc_ra(m) for m in ms]}


@router.post("/{da_id}/moc")
def them_moc(da_id: int, data: MocVao, db: Session = Depends(get_db),
             nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    _da_404(db, da_id)
    m = DuAnMoc(du_an_id=da_id, ten=data.ten,
                thu_tu=data.thu_tu or 0, giai_doan=data.giai_doan,
                ngay_bd_kh=data.ngay_bd_kh, ngay_kt_kh=data.ngay_kt_kh, ngay_kt_tt=data.ngay_kt_tt,
                trong_so=data.trong_so if data.trong_so is not None else 1,
                phan_tram=data.phan_tram or 0, trang_thai=data.trang_thai or "CHUA_BAT_DAU",
                phu_trach=data.phu_trach, ghi_chu=data.ghi_chu)
    db.add(m); db.flush()
    td = _tinh_tien_do(db, da_id)
    db.commit()
    return {"moc": _moc_ra(m), "tien_do": td}


@router.put("/moc/{moc_id}")
def sua_moc(moc_id: int, data: MocSuaVao, db: Session = Depends(get_db),
            nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    m = db.get(DuAnMoc, moc_id)
    if m is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy mốc")
    for k in ("thu_tu", "ten", "giai_doan", "ngay_bd_kh", "ngay_kt_kh", "ngay_kt_tt",
              "trong_so", "phan_tram", "trang_thai", "phu_trach", "ghi_chu"):
        v = getattr(data, k)
        if v is not None:
            setattr(m, k, v)
    # tự cập nhật trạng thái khi đạt 100%
    if data.phan_tram is not None and _f(m.phan_tram) >= 100 and m.trang_thai != "HOAN_THANH":
        m.trang_thai = "HOAN_THANH"
    td = _tinh_tien_do(db, m.du_an_id)
    db.commit()
    return {"moc": _moc_ra(m), "tien_do": td}


@router.delete("/moc/{moc_id}")
def xoa_moc(moc_id: int, db: Session = Depends(get_db),
            nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    m = db.get(DuAnMoc, moc_id)
    if m is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy mốc")
    da_id = m.du_an_id
    db.delete(m); db.flush()
    td = _tinh_tien_do(db, da_id)
    db.commit()
    return {"da_xoa": True, "tien_do": td}


# ----- Đánh giá an toàn -----
def _at_ra(a):
    return {"id": a.id, "hang_muc": a.hang_muc, "moi_nguy": a.moi_nguy, "muc_rui_ro": a.muc_rui_ro,
            "bien_phap": a.bien_phap, "phu_trach": a.phu_trach,
            "han": str(a.han) if a.han else None, "trang_thai": a.trang_thai,
            "nguoi_danh_gia": a.nguoi_danh_gia,
            "ngay_danh_gia": str(a.ngay_danh_gia) if a.ngay_danh_gia else None}


@router.get("/{da_id}/an-toan")
def ds_an_toan(da_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    rs = db.query(DuAnAnToan).filter_by(du_an_id=da_id).order_by(DuAnAnToan.id.desc()).all()
    theo_muc = {"CAO": 0, "TRUNG": 0, "THAP": 0}
    for a in rs:
        theo_muc[a.muc_rui_ro] = theo_muc.get(a.muc_rui_ro, 0) + 1
    return {"tong": len(rs), "mo": sum(1 for a in rs if a.trang_thai != "DA_KIEM_SOAT"),
            "theo_muc_rui_ro": theo_muc, "danh_sach": [_at_ra(a) for a in rs]}


@router.post("/{da_id}/an-toan")
def them_an_toan(da_id: int, data: AnToanVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    _da_404(db, da_id)
    a = DuAnAnToan(du_an_id=da_id, hang_muc=data.hang_muc, moi_nguy=data.moi_nguy,
                   muc_rui_ro=data.muc_rui_ro or "TRUNG", bien_phap=data.bien_phap,
                   phu_trach=data.phu_trach, han=data.han, trang_thai=data.trang_thai or "MO",
                   nguoi_danh_gia=data.nguoi_danh_gia or _nguoi(db, nd),
                   ngay_danh_gia=data.ngay_danh_gia or date.today())
    db.add(a); db.commit()
    return _at_ra(a)


@router.put("/an-toan/{at_id}")
def sua_an_toan(at_id: int, data: AnToanVao, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    a = db.get(DuAnAnToan, at_id)
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đánh giá")
    for k in ("hang_muc", "moi_nguy", "muc_rui_ro", "bien_phap", "phu_trach", "han",
              "trang_thai", "nguoi_danh_gia", "ngay_danh_gia"):
        v = getattr(data, k)
        if v is not None:
            setattr(a, k, v)
    db.commit()
    return _at_ra(a)


# ----- Triển khai: nhật ký thi công -----
@router.get("/{da_id}/nhat-ky")
def ds_nhat_ky(da_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    rs = db.query(DuAnNhatKy).filter_by(du_an_id=da_id).order_by(DuAnNhatKy.ngay.desc(), DuAnNhatKy.id.desc()).all()
    return [{"id": r.id, "ngay": str(r.ngay), "noi_dung": r.noi_dung, "nhan_luc": r.nhan_luc,
             "thiet_bi": r.thiet_bi, "thoi_tiet": r.thoi_tiet, "van_de": r.van_de,
             "nguoi_ghi": r.nguoi_ghi} for r in rs]


@router.post("/{da_id}/nhat-ky")
def them_nhat_ky(da_id: int, data: NhatKyVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    _da_404(db, da_id)
    r = DuAnNhatKy(du_an_id=da_id, ngay=data.ngay or date.today(), noi_dung=data.noi_dung,
                   nhan_luc=data.nhan_luc, thiet_bi=data.thiet_bi, thoi_tiet=data.thoi_tiet,
                   van_de=data.van_de, nguoi_ghi=data.nguoi_ghi or _nguoi(db, nd))
    db.add(r); db.commit()
    return {"id": r.id, "ngay": str(r.ngay)}


# ----- Tài liệu -----
LOAI_TL = {"THIET_BI", "VAT_TU", "BAN_VE", "BB_GIAO_NHAN", "BAN_GIAO", "NGHIEM_THU", "KHAC"}


def _tl_ra(t):
    return {"id": t.id, "loai": t.loai, "ten": t.ten, "ma_so": t.ma_so, "phien_ban": t.phien_ban,
            "ngay": str(t.ngay) if t.ngay else None, "co_file": bool(t.duong_dan),
            "kich_thuoc": t.kich_thuoc, "trang_thai": t.trang_thai,
            "nguoi_tao": t.nguoi_tao, "ghi_chu": t.ghi_chu}


@router.get("/{da_id}/tai-lieu")
def ds_tai_lieu(da_id: int, loai: str | None = None, db: Session = Depends(get_db),
                _=Depends(yeu_cau(MODULE, "XEM"))):
    q = db.query(DuAnTaiLieu).filter_by(du_an_id=da_id)
    if loai:
        q = q.filter(DuAnTaiLieu.loai == loai)
    rs = q.order_by(DuAnTaiLieu.loai, DuAnTaiLieu.id.desc()).all()
    theo_loai = defaultdict(int)
    for t in db.query(DuAnTaiLieu).filter_by(du_an_id=da_id).all():
        theo_loai[t.loai] += 1
    return {"theo_loai": dict(theo_loai), "danh_sach": [_tl_ra(t) for t in rs]}


@router.post("/{da_id}/tai-lieu")
async def them_tai_lieu(da_id: int, ten: str = Form(...), loai: str = Form("KHAC"),
                        ma_so: str = Form(None), phien_ban: str = Form(None),
                        ghi_chu: str = Form(None), file: UploadFile = File(None),
                        db: Session = Depends(get_db),
                        nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    _da_404(db, da_id)
    if loai not in LOAI_TL:
        loai = "KHAC"
    duong_dan, kt = None, 0
    if file is not None:
        base = (getattr(settings, "storage_dir", None) or os.environ.get("STORAGE_DIR") or "/tmp")
        thu_muc = os.path.join(base, "du_an", str(da_id))
        os.makedirs(thu_muc, exist_ok=True)
        safe = f"{uuid.uuid4().hex}_{os.path.basename(file.filename or 'file')}"
        duong_dan = os.path.join(thu_muc, safe)
        data = await file.read()
        with open(duong_dan, "wb") as f:
            f.write(data)
        kt = len(data)
    t = DuAnTaiLieu(du_an_id=da_id, loai=loai, ten=ten, ma_so=ma_so, phien_ban=phien_ban,
                    ngay=date.today(), duong_dan=duong_dan, kich_thuoc=kt,
                    nguoi_tao=_nguoi(db, nd), ghi_chu=ghi_chu)
    db.add(t); db.commit()
    ghi_audit(db, nd.id, "TAO", "du_an_tai_lieu", t.id, moi={"ten": ten, "loai": loai})
    return _tl_ra(t)


@router.put("/tai-lieu/{tl_id}")
def sua_tai_lieu(tl_id: int, data: TaiLieuMetaVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    t = db.get(DuAnTaiLieu, tl_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài liệu")
    for k in ("loai", "ten", "ma_so", "phien_ban", "ngay", "trang_thai", "ghi_chu"):
        v = getattr(data, k)
        if v is not None:
            setattr(t, k, v)
    db.commit()
    return _tl_ra(t)


@router.delete("/tai-lieu/{tl_id}")
def xoa_tai_lieu(tl_id: int, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    t = db.get(DuAnTaiLieu, tl_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài liệu")
    if t.duong_dan and os.path.exists(t.duong_dan):
        try:
            os.remove(t.duong_dan)
        except OSError:
            pass
    db.delete(t); db.commit()
    return {"da_xoa": True}


@router.get("/tai-lieu/{tl_id}/tai-ve")
def tai_ve(tl_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    t = db.get(DuAnTaiLieu, tl_id)
    if t is None or not t.duong_dan or not os.path.exists(t.duong_dan):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không có tệp đính kèm")
    return FileResponse(t.duong_dan, filename=os.path.basename(t.duong_dan).split("_", 1)[-1])


# ----- KPI -----
def _kpi_dat(k):
    if k.thuc_te is None or k.muc_tieu is None:
        return None
    mt, tt = _f(k.muc_tieu), _f(k.thuc_te)
    if (k.chieu or "CAO") == "CAO":
        return round(tt / mt * 100, 1) if mt else None
    # THAP: càng thấp càng tốt
    if tt == 0:
        return 100.0 if tt <= mt else None
    return round(mt / tt * 100, 1)


def _kpi_ra(k):
    return {"id": k.id, "ten": k.ten, "don_vi": k.don_vi, "chieu": k.chieu,
            "muc_tieu": _f(k.muc_tieu), "thuc_te": _f(k.thuc_te), "trong_so": _f(k.trong_so),
            "ky": k.ky, "ghi_chu": k.ghi_chu, "dat_phan_tram": _kpi_dat(k)}


@router.get("/{da_id}/kpi")
def ds_kpi(da_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    rs = db.query(DuAnKpi).filter_by(du_an_id=da_id).order_by(DuAnKpi.id).all()
    dats = [(_f(k.trong_so), _kpi_dat(k)) for k in rs]
    co = [(w, d) for w, d in dats if d is not None]
    tong_w = sum(w for w, _ in co)
    binh_quan = round(sum(w * d for w, d in co) / tong_w, 1) if tong_w else None
    return {"binh_quan_dat": binh_quan, "danh_sach": [_kpi_ra(k) for k in rs]}


@router.post("/{da_id}/kpi")
def them_kpi(da_id: int, data: KpiVao, db: Session = Depends(get_db),
             nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    _da_404(db, da_id)
    k = DuAnKpi(du_an_id=da_id, ten=data.ten, don_vi=data.don_vi, chieu=data.chieu or "CAO",
                muc_tieu=data.muc_tieu, thuc_te=data.thuc_te,
                trong_so=data.trong_so if data.trong_so is not None else 1,
                ky=data.ky, ghi_chu=data.ghi_chu)
    db.add(k); db.commit()
    return _kpi_ra(k)


@router.put("/kpi/{kpi_id}")
def sua_kpi(kpi_id: int, data: KpiVao, db: Session = Depends(get_db),
            nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    k = db.get(DuAnKpi, kpi_id)
    if k is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy KPI")
    for f in ("ten", "don_vi", "chieu", "muc_tieu", "thuc_te", "trong_so", "ky", "ghi_chu"):
        v = getattr(data, f)
        if v is not None:
            setattr(k, f, v)
    db.commit()
    return _kpi_ra(k)


@router.delete("/kpi/{kpi_id}")
def xoa_kpi(kpi_id: int, db: Session = Depends(get_db),
            nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    k = db.get(DuAnKpi, kpi_id)
    if k is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy KPI")
    db.delete(k); db.commit()
    return {"da_xoa": True}


# ----- Báo cáo -----
@router.get("/{da_id}/bao-cao-tong-hop")
def bao_cao_tong_hop(da_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Tổng hợp LIVE từ dữ liệu thực: tiến độ, mốc, an toàn, tài liệu, KPI, ngân sách."""
    da = _da_404(db, da_id)
    ms = db.query(DuAnMoc).filter_by(du_an_id=da_id).all()
    moc_tt = defaultdict(int)
    for m in ms:
        moc_tt[m.trang_thai] += 1
    at = ds_an_toan(da_id, db)
    tl = ds_tai_lieu(da_id, None, db)
    kpi = ds_kpi(da_id, db)
    return {
        "du_an": {"ma": da.ma, "ten": da.ten, "trang_thai": da.trang_thai, "tien_do": _f(da.tien_do)},
        "tien_do": _f(da.tien_do),
        "moc": {"tong": len(ms), "theo_trang_thai": dict(moc_tt)},
        "an_toan": {"tong": at["tong"], "mo": at["mo"], "theo_muc_rui_ro": at["theo_muc_rui_ro"]},
        "tai_lieu": {"tong": sum(tl["theo_loai"].values()), "theo_loai": tl["theo_loai"]},
        "kpi": {"binh_quan_dat": kpi["binh_quan_dat"], "so_kpi": len(kpi["danh_sach"])},
        "ngan_sach": {"du_toan": _f(da.du_toan), "chi_phi_thuc_te": _f(da.chi_phi_thuc_te),
                      "con_lai": _f(da.du_toan) - _f(da.chi_phi_thuc_te),
                      "vuot": _f(da.chi_phi_thuc_te) > _f(da.du_toan) > 0},
    }


@router.get("/{da_id}/bao-cao")
def ds_bao_cao(da_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    rs = db.query(DuAnBaoCao).filter_by(du_an_id=da_id).order_by(DuAnBaoCao.id.desc()).all()
    return [{"id": r.id, "ky": r.ky, "tieu_de": r.tieu_de, "tien_do": _f(r.tien_do),
             "noi_dung": r.noi_dung, "van_de": r.van_de, "ngay": str(r.ngay) if r.ngay else None,
             "nguoi_tao": r.nguoi_tao} for r in rs]


@router.post("/{da_id}/bao-cao")
def lap_bao_cao(da_id: int, data: BaoCaoVao, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    da = _da_404(db, da_id)
    r = DuAnBaoCao(du_an_id=da_id, ky=data.ky, tieu_de=data.tieu_de, noi_dung=data.noi_dung,
                   van_de=data.van_de, tien_do=da.tien_do, ngay=date.today(),
                   nguoi_tao=_nguoi(db, nd))   # chốt % tiến độ thực tại thời điểm lập
    db.add(r); db.commit()
    return {"id": r.id, "tien_do": _f(r.tien_do)}


# ----- Chỉ tiêu chất lượng (đầu vào / giới hạn đầu ra) -----
def _ct_ra(c):
    vao = _f(c.gia_tri_vao) if c.gia_tri_vao is not None else None
    ra = _f(c.gioi_han_ra) if c.gioi_han_ra is not None else None
    # % cần xử lý = (vào - ra)/vào — chỉ tính khi có đủ 2 số thực anh nhập
    can_xl = round((vao - ra) / vao * 100, 1) if (vao and ra is not None and vao > ra) else None
    return {"id": c.id, "thu_tu": c.thu_tu, "ten": c.ten, "don_vi": c.don_vi,
            "gia_tri_vao": vao, "gioi_han_ra": ra, "ghi_chu": c.ghi_chu, "can_xu_ly": can_xl}


@router.get("/{da_id}/chi-tieu")
def ds_chi_tieu(da_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    da = _da_404(db, da_id)
    rs = db.query(DuAnChiTieu).filter_by(du_an_id=da_id).order_by(DuAnChiTieu.thu_tu, DuAnChiTieu.id).all()
    return {"tieu_chuan_dau_ra": da.tieu_chuan_dau_ra, "danh_sach": [_ct_ra(c) for c in rs]}


@router.post("/{da_id}/chi-tieu")
def them_chi_tieu(da_id: int, data: ChiTieuVao, db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    _da_404(db, da_id)
    if not data.ten:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Thiếu tên chỉ tiêu")
    c = DuAnChiTieu(du_an_id=da_id, thu_tu=data.thu_tu or 0, ten=data.ten, don_vi=data.don_vi,
                    gia_tri_vao=data.gia_tri_vao, gioi_han_ra=data.gioi_han_ra, ghi_chu=data.ghi_chu)
    db.add(c); db.commit()
    return _ct_ra(c)


@router.put("/chi-tieu/{ct_id}")
def sua_chi_tieu(ct_id: int, data: ChiTieuVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    c = db.get(DuAnChiTieu, ct_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy chỉ tiêu")
    for k in ("thu_tu", "ten", "don_vi", "gia_tri_vao", "gioi_han_ra", "ghi_chu"):
        v = getattr(data, k)
        if v is not None:
            setattr(c, k, v)
    db.commit()
    return _ct_ra(c)


@router.delete("/chi-tieu/{ct_id}")
def xoa_chi_tieu(ct_id: int, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    c = db.get(DuAnChiTieu, ct_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy chỉ tiêu")
    db.delete(c); db.commit()
    return {"da_xoa": True}


@router.post("/{da_id}/chi-tieu/nap-mau")
def nap_mau_chi_tieu(da_id: int, data: NapChiTieuVao, db: Session = Depends(get_db),
                     nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Nạp danh mục TÊN chỉ tiêu + đơn vị theo tiêu chuẩn (KHÔNG kèm giá trị giới hạn —
    giá trị do người dùng nhập theo cột áp dụng). Bỏ qua chỉ tiêu trùng tên đã có."""
    _da_404(db, da_id)
    da_co = {(c.ten or "").strip().lower()
             for c in db.query(DuAnChiTieu).filter_by(du_an_id=da_id).all()}
    base = db.query(func.coalesce(func.max(DuAnChiTieu.thu_tu), 0)).filter(
        DuAnChiTieu.du_an_id == da_id).scalar() or 0
    them, bo_qua = 0, 0
    for it in data.danh_sach:
        ten = (it.ten or "").strip()
        if not ten:
            continue
        if ten.lower() in da_co:
            bo_qua += 1
            continue
        base += 1
        db.add(DuAnChiTieu(du_an_id=da_id, thu_tu=base, ten=ten, don_vi=it.don_vi,
                           gia_tri_vao=None, gioi_han_ra=it.gioi_han_ra, ghi_chu=it.ghi_chu))
        da_co.add(ten.lower())
        them += 1
    db.commit()
    return {"them": them, "bo_qua": bo_qua}


@router.post("/{da_id}/phan-tich-ai")
def phan_tich_ai(da_id: int, data: PhanTichVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "XEM"))):
    """Agent AI phân tích mô tả + dữ liệu chất lượng thực → gợi ý nguyên lý thiết kế.
    Dùng mô tả gửi kèm (nếu có, để phân tích cả phần chưa lưu), nếu không thì lấy mô tả đã lưu."""
    from ..ai_gateway import phan_tich_thiet_ke
    da = _da_404(db, da_id)
    cts = db.query(DuAnChiTieu).filter_by(du_an_id=da_id).order_by(DuAnChiTieu.thu_tu, DuAnChiTieu.id).all()
    info = {
        "mo_ta": data.mo_ta if data.mo_ta is not None else da.mo_ta,
        "loai_du_an": da.loai_du_an, "cong_suat": da.cong_suat,
        "tieu_chuan_dau_ra": da.tieu_chuan_dau_ra,
        "chi_tieu": [_ct_ra(c) for c in cts],
    }
    return phan_tich_thiet_ke(info)
