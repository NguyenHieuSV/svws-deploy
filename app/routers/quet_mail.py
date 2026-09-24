"""📬 API Tự quét thư hàng tuần: cấu hình · chạy ngay · gửi tin thử · nhật ký · tổng quan hàng chờ."""
from datetime import timedelta
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..rbac import yeu_cau, chi_vai_tro
from ..models import NguoiDung
from ..audit import ghi_audit
from ..config import settings
from .. import quet_mail_service as qm

router = APIRouter(prefix="/quet-mail", tags=["quet-mail"])


def _lich_dict(r):
    return {"id": r.id, "nguon": r.nguon, "bat_dau": str(r.bat_dau)[:16] if r.bat_dau else None,
            "ket_thuc": str(r.ket_thuc)[:16] if r.ket_thuc else None, "trang_thai": r.trang_thai,
            "ket_qua": r.ket_qua or {}}


def _trang_thai(db):
    from ..models import LichQuetMail
    from ..nhac_viec_service import gio_hien_tai
    c = qm.cau_hinh(db)
    bay_gio = gio_hien_tai()
    moc = qm.moc_gan_nhat(c, bay_gio)
    cuoi = qm.lan_chay_cuoi(db)
    da_chay_tuan = cuoi is not None and cuoi.bat_dau >= moc
    lan_toi = (moc + timedelta(days=7)) if da_chay_tuan else moc
    return {"bat": bool(c.bat), "thu": int(c.thu or 0), "thu_ten": qm.THU[int(c.thu or 0) % 7], "gio": int(c.gio or 0),
            "so_ngay": int(c.so_ngay or 8),
            "webhook_rieng": bool((settings.gchat_webhook_quet_mail or "").strip()),
            "moc_gan_nhat": str(moc)[:16], "da_chay_tuan_nay": da_chay_tuan,
            "lan_toi": str(lan_toi)[:16], "den_han_chua_chay": (bool(c.bat) and not da_chay_tuan),
            "dang_chay": qm.dang_chay(db),
            "lich": [_lich_dict(r) for r in db.query(LichQuetMail).order_by(LichQuetMail.id.desc()).limit(12).all()]}


@router.get("/cau-hinh")
def xem_cau_hinh(db: Session = Depends(get_db), _=Depends(yeu_cau("ncc", "XEM"))):
    return _trang_thai(db)


class CauHinhVao(BaseModel):
    bat: bool = True
    thu: int = 0
    gio: int = 6
    so_ngay: int = 8


@router.post("/cau-hinh")
def luu_cau_hinh(data: CauHinhVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT", "TP_QLNB"))):
    from ..nhac_viec_service import gio_hien_tai
    if not (0 <= data.thu <= 6 and 0 <= data.gio <= 23 and 1 <= data.so_ngay <= 60):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Thứ 0–6, giờ 0–23, số ngày 1–60")
    c = qm.cau_hinh(db)
    cu = {"bat": c.bat, "thu": c.thu, "gio": c.gio, "so_ngay": c.so_ngay}
    c.bat, c.thu, c.gio, c.so_ngay, c.cap_nhat = data.bat, data.thu, data.gio, data.so_ngay, gio_hien_tai()
    ghi_audit(db, nd.id, "QUET_MAIL_CAU_HINH", "cau_hinh_quet_mail", 1, cu=cu, moi=data.model_dump())
    db.commit()
    return _trang_thai(db)


@router.post("/chay-ngay")
def chay_ngay(db: Session = Depends(get_db), nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT", "TP_QLNB"))):
    """▶ Chạy ngay (luồng nền) — xem tiến độ ở nhật ký; AI đọc thư mất vài phút."""
    if qm.dang_chay(db):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Đang có một lần quét chạy dở — chờ xong rồi bấm lại.")
    if not qm.chay_nen("TAY", nd.id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Đang có một lần quét chạy — chờ xong rồi bấm lại.")
    ghi_audit(db, nd.id, "QUET_MAIL_CHAY_TAY", "lich_quet_mail", None, moi={})
    db.commit()
    return {"ok": True, "dang_chay": True}


@router.post("/gui-thu")
def gui_thu(db: Session = Depends(get_db), nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT"))):
    """Tin nhắn thử vào group riêng (GCHAT_WEBHOOK_QUET_MAIL)."""
    url = (settings.gchat_webhook_quet_mail or "").strip()
    if not url:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Chưa cấu hình GCHAT_WEBHOOK_QUET_MAIL — đặt biến môi trường trên Render (webhook group riêng) rồi deploy lại.")
    from ..chat_gateway import gui_webhook_rieng
    ten = getattr(nd, "ho_ten", None) or nd.email
    return gui_webhook_rieng(url, f"🔔 SVWS — tin thử từ 📬 Tự quét thư hàng tuần. Người gửi: {ten}. "
                                  "Thấy tin này trong group nghĩa là cấu hình ĐÃ ĐÚNG ✅")


@router.get("/tong-quan")
def tong_quan(db: Session = Depends(get_db), _=Depends(yeu_cau("ncc", "XEM"))):
    """Dòng «Việc cần chú ý»: hàng chờ hóa đơn / báo giá + lần quét cuối."""
    from ..models import KtHoaDonCho, BgEmailCho
    cuoi = qm.lan_chay_cuoi(db)
    return {"cho": {"hoa_don": db.query(KtHoaDonCho).filter_by(trang_thai="CHO_XAC_NHAN").count(),
                    "bao_gia": db.query(BgEmailCho).filter_by(trang_thai="CHO_XAC_NHAN").count()},
            "lan_cuoi": _lich_dict(cuoi) if cuoi else None}
