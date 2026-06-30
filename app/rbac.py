"""
TRÁI TIM CỦA PHÂN QUYỀN — đọc bảng phan_quyen để chặn/cho phép theo vai trò.
Đây là khuôn mẫu dùng lại cho MỌI module: chỉ cần Depends(yeu_cau("<module>", "<mức>")).
RBAC là dữ liệu (bảng phan_quyen), không hard-code trong route.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import get_db
from .deps import lay_nguoi_dung_hien_tai
from .models import NguoiDung, PhanQuyen

# Thứ bậc mức quyền: cao hơn bao hàm thấp hơn
THU_BAC = {"KHONG": 0, "XEM": 1, "THAO_TAC": 2, "DUYET": 3, "QUAN_TRI": 4}


def muc_cua(db: Session, vai_tro_id: int, module: str) -> str:
    pq = db.query(PhanQuyen).filter_by(vai_tro_id=vai_tro_id, module=module).first()
    return pq.muc if pq else "KHONG"


def yeu_cau(module: str, muc_toi_thieu: str):
    """Factory tạo dependency kiểm quyền cho 1 (module, mức tối thiểu)."""
    nguong = THU_BAC[muc_toi_thieu]

    def kiem_tra(
        nguoi_dung: NguoiDung = Depends(lay_nguoi_dung_hien_tai),
        db: Session = Depends(get_db),
    ) -> NguoiDung:
        muc = muc_cua(db, nguoi_dung.vai_tro_id, module)
        if THU_BAC.get(muc, 0) < nguong:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Vai trò '{nguoi_dung.vai_tro.ma}' không đủ quyền "
                       f"(cần {muc_toi_thieu} ở module '{module}', hiện có '{muc}').",
            )
        return nguoi_dung

    return kiem_tra


# ---------- Phê duyệt theo HẠN MỨC TIỀN (đọc bảng han_muc_duyet) ----------
# Mô hình "trần" (ceiling): vai trò duyệt được nếu số tiền <= nguong_den
# (NULL = không giới hạn). Vai trò cấp cao (trần lớn hơn) bao hàm cấp thấp.
from .models import HanMucDuyet  # noqa: E402


def co_the_duyet(db: Session, vai_tro_id: int, loai: str, so_tien) -> bool:
    hm = db.query(HanMucDuyet).filter_by(loai=loai, vai_tro_id=vai_tro_id).first()
    if hm is None:
        return False
    return hm.nguong_den is None or so_tien <= hm.nguong_den


def kiem_han_muc(db: Session, nguoi_dung: NguoiDung, loai: str, so_tien) -> None:
    """Raise 403 nếu vai trò không có thẩm quyền hoặc vượt trần duyệt.
    THẨM QUYỀN DUYỆT do bảng han_muc_duyet quyết định (không phải mức module)."""
    hm = db.query(HanMucDuyet).filter_by(loai=loai, vai_tro_id=nguoi_dung.vai_tro_id).first()
    if hm is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Vai trò '{nguoi_dung.vai_tro.ma}' không có thẩm quyền duyệt loại '{loai}'.",
        )
    if hm.nguong_den is not None and so_tien > hm.nguong_den:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Số tiền {so_tien:.0f} vượt trần duyệt {hm.nguong_den:.0f} của vai trò "
            f"'{nguoi_dung.vai_tro.ma}'. Cần trình cấp cao hơn.",
        )


# ---------- Primitive thứ ba: cổng theo VAI TRÒ CỤ THỂ (quy trình tuần tự) ----------
# Dùng cho các bước gắn đúng một/ vài vai trò (vd: KTT duyệt lương, CEO ký), không phải
# theo mức module hay hạn mức tiền.
def chi_vai_tro(*ma_vai_tro: str):
    cho_phep = set(ma_vai_tro)

    def kiem_tra(nguoi_dung: NguoiDung = Depends(lay_nguoi_dung_hien_tai)) -> NguoiDung:
        if nguoi_dung.vai_tro.ma not in cho_phep:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Bước này chỉ dành cho vai trò: {', '.join(sorted(cho_phep))}.",
            )
        return nguoi_dung

    return kiem_tra
