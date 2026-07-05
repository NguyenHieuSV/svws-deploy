"""
Cấu hình hệ thống — phân quyền truy cập tab 'Overall Operation' (module dieu_hanh).

Cơ chế: dùng đúng RBAC sẵn có (bảng phan_quyen). 'CEO duyệt vị trí' = CEO cấp/thu hồi
quyền module 'dieu_hanh' (mức XEM) cho từng vai trò. Khi vai trò có 'dieu_hanh' thì
/auth/quyen-cua-toi trả về -> UI hiện tab. Bên trong tab, mỗi lối tắt vẫn theo quyền
module đích của vai trò (không nới quyền).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import NguoiDung, VaiTro, PhanQuyen
from ..rbac import yeu_cau, chi_vai_tro
from ..audit import ghi_audit
from ..security import bam_mat_khau

router = APIRouter(prefix="/cau-hinh", tags=["cau_hinh"])

MODULE = "dieu_hanh"


class DuyetVaiTro(BaseModel):
    vai_tro: str
    cho_phep: bool


@router.get("/vai-tro-dieu-hanh")
def danh_sach_vai_tro(
    nd: NguoiDung = Depends(yeu_cau(MODULE, "QUAN_TRI")),
    db: Session = Depends(get_db),
):
    """Liệt kê mọi vị trí + trạng thái được truy cập Overall Operation (chỉ CEO/Quản trị)."""
    vai_tros = db.query(VaiTro).order_by(VaiTro.id).all()
    co = {pq.vai_tro_id for pq in db.query(PhanQuyen).filter_by(module=MODULE).all()}
    return [
        {"ma": v.ma, "ten": v.ten, "co_quyen": (v.ma == "CEO") or (v.id in co)}
        for v in vai_tros
    ]


@router.post("/dieu-hanh/duyet")
def duyet_vai_tro(
    payload: DuyetVaiTro,
    nd: NguoiDung = Depends(yeu_cau(MODULE, "QUAN_TRI")),
    db: Session = Depends(get_db),
):
    """CEO cấp/thu hồi quyền truy cập Overall Operation cho 1 vị trí."""
    if nd.vai_tro.ma != "CEO":
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Chỉ CEO được duyệt quyền truy cập Overall Operation.")
    vt = db.query(VaiTro).filter_by(ma=payload.vai_tro).first()
    if not vt:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy vị trí.")
    if vt.ma == "CEO":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "CEO luôn có quyền — không thể thay đổi.")
    pq = db.query(PhanQuyen).filter_by(vai_tro_id=vt.id, module=MODULE).first()
    if payload.cho_phep:
        if pq:
            pq.muc = "XEM"
        else:
            db.add(PhanQuyen(vai_tro_id=vt.id, module=MODULE, muc="XEM"))
    else:
        if pq:
            db.delete(pq)
    ghi_audit(db, nd.id, "DUYET", "phan_quyen", vt.id,
              moi={"module": MODULE, "vai_tro": vt.ma, "cho_phep": payload.cho_phep})
    db.commit()
    return {"vai_tro": vt.ma, "co_quyen": payload.cho_phep}


# ============================================================
# MA TRẬN PHÂN QUYỀN ĐẦY ĐỦ — CEO đặt: vị trí × module × mức
#   mức: KHONG (không truy cập) / XEM / THAO_TAC (đề xuất) / DUYET / QUAN_TRI
# ============================================================
MUC_HOP_LE = {"KHONG", "XEM", "THAO_TAC", "DUYET", "QUAN_TRI"}


class DatQuyen(BaseModel):
    vai_tro: str
    module: str
    muc: str


@router.get("/ma-tran-quyen")
def ma_tran_quyen(
    nd: NguoiDung = Depends(yeu_cau(MODULE, "QUAN_TRI")),
    db: Session = Depends(get_db),
):
    """Toàn bộ ma trận phân quyền (chỉ CEO/Quản trị) để dựng bảng điều chỉnh."""
    vts = db.query(VaiTro).order_by(VaiTro.id).all()
    mt: dict[int, dict[str, str]] = {}
    for pq in db.query(PhanQuyen).all():
        mt.setdefault(pq.vai_tro_id, {})[pq.module] = pq.muc
    return {
        "vai_tro": [{"ma": v.ma, "ten": v.ten} for v in vts],
        "ma_tran": {v.ma: mt.get(v.id, {}) for v in vts},
    }


@router.post("/phan-quyen")
def dat_quyen(
    p: DatQuyen,
    nd: NguoiDung = Depends(yeu_cau(MODULE, "QUAN_TRI")),
    db: Session = Depends(get_db),
):
    """CEO đặt mức quyền của 1 vị trí cho 1 module (KHONG = thu hồi truy cập)."""
    if nd.vai_tro.ma != "CEO":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ CEO được phân quyền.")
    if p.muc not in MUC_HOP_LE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mức quyền không hợp lệ.")
    vt = db.query(VaiTro).filter_by(ma=p.vai_tro).first()
    if not vt:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy vị trí.")
    # Chống tự khóa: CEO phải giữ Quản trị ở 'dieu_hanh' để không mất bảng phân quyền
    if vt.ma == "CEO" and p.module == "dieu_hanh" and p.muc != "QUAN_TRI":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "CEO phải giữ 'Quản trị' ở Overall Operation (tránh tự khóa bảng phân quyền).")
    pq = db.query(PhanQuyen).filter_by(vai_tro_id=vt.id, module=p.module).first()
    if p.muc == "KHONG":
        if pq:
            db.delete(pq)
    else:
        if pq:
            pq.muc = p.muc
        else:
            db.add(PhanQuyen(vai_tro_id=vt.id, module=p.module, muc=p.muc))
    ghi_audit(db, nd.id, "SUA", "phan_quyen", vt.id,
              moi={"vai_tro": vt.ma, "module": p.module, "muc": p.muc})
    db.commit()
    return {"vai_tro": vt.ma, "module": p.module, "muc": p.muc}


# ============================================================
# QUẢN LÝ NGƯỜI DÙNG — chỉ CEO và ADMIN (tạo tài khoản, đổi vai
# trò, khóa/mở, đặt lại mật khẩu). Mật khẩu KHÔNG ghi vào audit.
# ============================================================
TRANG_THAI_HOP_LE = {"HOAT_DONG", "KHOA"}


def _nd_ra(u: NguoiDung) -> dict:
    return {"id": u.id, "email": u.email, "vai_tro": u.vai_tro.ma,
            "ten_vai_tro": u.vai_tro.ten, "trang_thai": u.trang_thai}


@router.get("/vai-tro")
def danh_sach_vi_tri(
    nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Danh sách vị trí để chọn khi tạo/sửa người dùng."""
    return [{"ma": v.ma, "ten": v.ten} for v in db.query(VaiTro).order_by(VaiTro.id).all()]


@router.get("/nguoi-dung")
def danh_sach_nguoi_dung(
    nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN")),
    db: Session = Depends(get_db),
):
    return [_nd_ra(u) for u in db.query(NguoiDung).order_by(NguoiDung.id).all()]


class TaoNguoiDung(BaseModel):
    email: str
    mat_khau: str
    vai_tro: str


@router.post("/nguoi-dung")
def tao_nguoi_dung(
    p: TaoNguoiDung,
    nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN")),
    db: Session = Depends(get_db),
):
    email = p.email.strip().lower()
    if "@" not in email or len(email) < 5:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email không hợp lệ.")
    if len(p.mat_khau) < 6:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mật khẩu tối thiểu 6 ký tự.")
    if db.query(NguoiDung).filter_by(email=email).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Email '{email}' đã tồn tại.")
    vt = db.query(VaiTro).filter_by(ma=p.vai_tro).first()
    if not vt:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy vị trí.")
    u = NguoiDung(email=email, mat_khau_hash=bam_mat_khau(p.mat_khau),
                  vai_tro_id=vt.id, trang_thai="HOAT_DONG")
    db.add(u)
    db.flush()
    ghi_audit(db, nd.id, "TAO", "nguoi_dung", u.id,
              moi={"email": email, "vai_tro": vt.ma})
    db.commit()
    db.refresh(u)
    return _nd_ra(u)


class SuaNguoiDung(BaseModel):
    email: str | None = None
    vai_tro: str | None = None
    trang_thai: str | None = None


@router.patch("/nguoi-dung/{nguoi_dung_id}")
def sua_nguoi_dung(
    nguoi_dung_id: int,
    p: SuaNguoiDung,
    nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN")),
    db: Session = Depends(get_db),
):
    u = db.get(NguoiDung, nguoi_dung_id)
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy người dùng.")
    cu = {"email": u.email, "vai_tro": u.vai_tro.ma, "trang_thai": u.trang_thai}
    if p.email is not None:
        email = p.email.strip().lower()
        if "@" not in email or len(email) < 5:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email không hợp lệ.")
        trung = db.query(NguoiDung).filter(NguoiDung.email == email,
                                           NguoiDung.id != u.id).first()
        if trung:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Email '{email}' đã tồn tại.")
        u.email = email
    if p.vai_tro is not None:
        if u.id == nd.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "Không thể tự đổi vai trò của chính mình.")
        vt = db.query(VaiTro).filter_by(ma=p.vai_tro).first()
        if not vt:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy vị trí.")
        u.vai_tro_id = vt.id
    if p.trang_thai is not None:
        if p.trang_thai not in TRANG_THAI_HOP_LE:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Trạng thái không hợp lệ.")
        if u.id == nd.id and p.trang_thai == "KHOA":
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "Không thể tự khóa tài khoản của chính mình.")
        u.trang_thai = p.trang_thai
    ghi_audit(db, nd.id, "SUA", "nguoi_dung", u.id, cu=cu,
              moi={"email": p.email, "vai_tro": p.vai_tro, "trang_thai": p.trang_thai})
    db.commit()
    db.refresh(u)
    return _nd_ra(u)


@router.delete("/nguoi-dung/{nguoi_dung_id}")
def xoa_nguoi_dung(
    nguoi_dung_id: int,
    nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Xóa vĩnh viễn tài khoản. Nếu tài khoản đã có dữ liệu liên quan
    (audit, phiếu, hồ sơ...) thì không xóa được — hãy dùng Khóa."""
    u = db.get(NguoiDung, nguoi_dung_id)
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy người dùng.")
    if u.id == nd.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Không thể tự xóa tài khoản của chính mình.")
    email_cu, vai_tro_cu = u.email, u.vai_tro.ma
    try:
        db.delete(u)
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Tài khoản '{email_cu}' đã có dữ liệu liên quan trong hệ thống "
            "(chứng từ, nhật ký...) nên không thể xóa. Hãy dùng 'Khóa' thay thế.")
    ghi_audit(db, nd.id, "XOA", "nguoi_dung", nguoi_dung_id,
              cu={"email": email_cu, "vai_tro": vai_tro_cu})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Tài khoản '{email_cu}' đã có dữ liệu liên quan trong hệ thống "
            "(chứng từ, nhật ký...) nên không thể xóa. Hãy dùng 'Khóa' thay thế.")
    return {"ok": True, "email": email_cu}


class DatLaiMatKhau(BaseModel):
    mat_khau_moi: str


@router.post("/nguoi-dung/{nguoi_dung_id}/dat-lai-mat-khau")
def dat_lai_mat_khau(
    nguoi_dung_id: int,
    p: DatLaiMatKhau,
    nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN")),
    db: Session = Depends(get_db),
):
    if len(p.mat_khau_moi) < 6:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mật khẩu tối thiểu 6 ký tự.")
    u = db.get(NguoiDung, nguoi_dung_id)
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy người dùng.")
    u.mat_khau_hash = bam_mat_khau(p.mat_khau_moi)
    ghi_audit(db, nd.id, "SUA", "nguoi_dung", u.id,
              moi={"dat_lai_mat_khau": True})
    db.commit()
    return {"ok": True, "email": u.email}
