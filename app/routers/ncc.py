"""
Module NHÀ CUNG CẤP & MUA HÀNG — lát cắt dọc thứ hai.
Điểm mới so với Kho: PHÊ DUYỆT THEO HẠN MỨC TIỀN (đọc bảng han_muc_duyet).
Khuôn phân quyền vẫn dùng lại y nguyên: yeu_cau("ncc", "<mức>").
"""
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..rbac import yeu_cau, kiem_han_muc
from ..deps import nhan_vien_id_cua
from ..audit import ghi_audit
from ..models import (NguoiDung, NhaCungCap, DonMua, DonMuaCt, DanhGiaNcc, YeuCauMua, YeuCauMuaCt,
                      TonKho, PhieuKho, PhieuKhoCt, CongNo, ThanhToan, HangHoa, BaoGiaNcc, Rfq, RfqLog)
from ..schemas import (NccVao, NccRa, DanhGiaVao, DonMuaVao, DonMuaRa, YeuCauMuaRa,
                       NhanHangVao, DonMuaChiTietRa, ThuTienVao,
                       YeuCauMuaVao, YeuCauMuaItemVao, TaoPoTuDeXuatVao, LyDoVao, BaoGiaVao, BaoGiaRa,
                       RfqVao, GuiRfqVao, RfqRa, RfqLogRa, RfqNoiDungVao,
                       PoNoiDungVao, GuiPoVao, PoPdfVao)
from ..kho_service import nhap_ton
from ..ai_gateway import goi_y_ncc_ai, tim_ncc_web
from ..config import settings
from ..email_gateway import lay_email_provider
from ..po_pdf import tao_po_pdf
import os
from fastapi.responses import FileResponse

router = APIRouter(prefix="/ncc", tags=["ncc"])
MODULE = "ncc"
LOAI_DUYET = "po"  # khớp seed han_muc_duyet


def gui_email_ncc(db: Session, don_mua: DonMua) -> bool:
    """PO được duyệt -> gửi email xác nhận tới NCC từ 1 đầu mối email_from_ncc."""
    ncc = db.get(NhaCungCap, don_mua.nha_cung_cap_id)
    if ncc is None or not ncc.email:
        return False
    tieu_de, than = _noi_dung_po(db, don_mua, None)
    kq = lay_email_provider().gui(ncc.email, tieu_de, than, None, gui_tu=settings.email_from_ncc)
    return kq.get("trang_thai") == "GUI_OK"


# ----- XEM: danh sách NCC -----
@router.get("/nha-cung-cap", response_model=list[NccRa])
def ds_ncc(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(NhaCungCap).order_by(NhaCungCap.id).all()


# ----- THAO_TAC: tạo NCC -----
@router.post("/nha-cung-cap", response_model=NccRa, status_code=201)
def tao_ncc(data: NccVao, db: Session = Depends(get_db),
            nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    ncc = NhaCungCap(ma=data.ma, ten=data.ten, ma_so_thue=data.ma_so_thue,
                     dien_thoai=data.dien_thoai, email=data.email, dia_chi=data.dia_chi,
                     han_muc_cong_no=data.han_muc_cong_no or 0,
                     nguoi_phu_trach=data.nguoi_phu_trach, ghi_chu=data.ghi_chu, diem_danh_gia=0)
    db.add(ncc)
    db.flush()
    ghi_audit(db, nd.id, "TAO", "nha_cung_cap", ncc.id, moi={"ten": data.ten})
    db.commit()
    db.refresh(ncc)
    return ncc


# ----- THAO_TAC: đánh giá NCC (cập nhật điểm trung bình; vi phạm nhiều -> blacklist) -----
@router.post("/nha-cung-cap/{ncc_id}/danh-gia", response_model=NccRa)
def danh_gia(ncc_id: int, data: DanhGiaVao, db: Session = Depends(get_db),
             nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    ncc = db.get(NhaCungCap, ncc_id)
    if ncc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy NCC")
    db.add(DanhGiaNcc(nha_cung_cap_id=ncc_id, don_mua_id=data.don_mua_id, diem=data.diem))
    db.flush()
    diems = [d.diem for d in db.query(DanhGiaNcc).filter_by(nha_cung_cap_id=ncc_id).all()]
    ncc.diem_danh_gia = round(sum(diems) / len(diems), 1)
    # TỰ ĐỘNG: điểm TB thấp + nhiều lần đánh giá kém -> blacklist
    kem = sum(1 for d in diems if d < 2)
    if ncc.diem_danh_gia < Decimal("2.0") and kem >= 2:
        ncc.blacklist = True
    ghi_audit(db, nd.id, "SUA", "nha_cung_cap", ncc_id,
              moi={"diem_tb": float(ncc.diem_danh_gia), "blacklist": ncc.blacklist})
    db.commit()
    db.refresh(ncc)
    return ncc


# ----- XEM: yêu cầu mua đang chờ (do module Kho tự sinh khi tồn < min) -----
def _ycm_dict(db, y):
    def _name(hid):
        hh = db.get(HangHoa, hid)
        return hh.ten if hh else f"HH #{hid}"
    lines = db.query(YeuCauMuaCt).filter(YeuCauMuaCt.yeu_cau_mua_id == y.id).all()
    def _ncc_name(nid):
        if not nid:
            return None
        nc = db.get(NhaCungCap, nid)
        return nc.ten if nc else f"NCC #{nid}"
    items = [{"id": l.id, "hang_hoa_id": l.hang_hoa_id, "ten_hh": _name(l.hang_hoa_id),
              "so_luong": float(l.so_luong),
              "don_gia": float(l.don_gia) if l.don_gia is not None else None,
              "ghi_chu": l.ghi_chu,
              "nha_cung_cap_id": l.nha_cung_cap_id, "ten_ncc": _ncc_name(l.nha_cung_cap_id)}
             for l in lines]
    return {"id": y.id, "hang_hoa_id": y.hang_hoa_id, "ten_hh": _name(y.hang_hoa_id),
            "so_luong": float(y.so_luong), "ly_do": y.ly_do, "trang_thai": y.trang_thai,
            "nha_cung_cap_id": y.nha_cung_cap_id, "don_hang_id": y.don_hang_id,
            "don_gia": float(y.don_gia) if y.don_gia is not None else None,
            "ngay_can": str(y.ngay_can) if y.ngay_can else None, "don_mua_id": y.don_mua_id,
            "ai_ncc_id": y.ai_ncc_id, "ai_goi_y": y.ai_goi_y,
            "dinh_kem_url": y.dinh_kem_url, "dinh_kem_file": y.dinh_kem_file,
            "so_dong": len(items) or 1, "items": items}


@router.get("/yeu-cau-mua")
def ds_yeu_cau_mua(trang_thai: str | None = None, db: Session = Depends(get_db),
                   _=Depends(yeu_cau(MODULE, "XEM"))):
    """ĐẦU MỐI ĐỀ XUẤT MUA: mọi đề xuất (thủ công + tự sinh khi tồn thấp) đổ về đây để xét duyệt."""
    q = db.query(YeuCauMua)
    if trang_thai:
        q = q.filter(YeuCauMua.trang_thai == trang_thai)
    return [_ycm_dict(db, y) for y in q.order_by(YeuCauMua.id.desc()).all()]


@router.get("/yeu-cau-mua/{ycm_id}")
def chi_tiet_yeu_cau_mua(ycm_id: int, db: Session = Depends(get_db),
                         _=Depends(yeu_cau(MODULE, "XEM"))):
    y = db.get(YeuCauMua, ycm_id)
    if y is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đề xuất")
    return _ycm_dict(db, y)


@router.post("/yeu-cau-mua/{ycm_id}/dinh-kem")
async def dinh_kem_de_xuat(ycm_id: int, file: UploadFile = File(...),
                           db: Session = Depends(get_db),
                           nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Đính kèm file dự toán (xlsx/csv/pdf...) cho đề xuất mua hàng."""
    y = db.get(YeuCauMua, ycm_id)
    if y is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đề xuất")
    base = (getattr(settings, "storage_dir", None) or os.environ.get("STORAGE_DIR") or "/tmp")
    thu_muc = os.path.join(base, "de_xuat")
    os.makedirs(thu_muc, exist_ok=True)
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in (file.filename or "dutoan"))
    fn = f"{ycm_id}_{safe}"
    with open(os.path.join(thu_muc, fn), "wb") as f:
        f.write(await file.read())
    y.dinh_kem_file = fn
    ghi_audit(db, nd.id, "DINH_KEM", "yeu_cau_mua", y.id, moi={"file": file.filename})
    db.commit()
    return {"dinh_kem_file": fn, "ten": file.filename}


@router.get("/yeu-cau-mua/{ycm_id}/dinh-kem")
def tai_dinh_kem(ycm_id: int, db: Session = Depends(get_db),
                 _=Depends(yeu_cau(MODULE, "XEM"))):
    y = db.get(YeuCauMua, ycm_id)
    if y is None or not y.dinh_kem_file:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không có tệp đính kèm")
    base = (getattr(settings, "storage_dir", None) or os.environ.get("STORAGE_DIR") or "/tmp")
    path = os.path.join(base, "de_xuat", y.dinh_kem_file)
    if not os.path.exists(path):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tệp không tồn tại")
    return FileResponse(path, filename=y.dinh_kem_file)


@router.post("/yeu-cau-mua", response_model=YeuCauMuaRa, status_code=201)
def tao_de_xuat(data: YeuCauMuaVao, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Tạo đề xuất mua (gắn Mã bán hàng + NCC đề xuất để dữ liệu liên tục)."""
    items = list(data.items or [])
    if not items and data.hang_hoa_id:
        items = [YeuCauMuaItemVao(hang_hoa_id=data.hang_hoa_id, so_luong=data.so_luong or 1,
                                  don_gia=data.don_gia, ghi_chu=data.ghi_chu)]
    if not items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cần ít nhất 1 sản phẩm trong đề xuất")
    primary = items[0]
    ycm = YeuCauMua(hang_hoa_id=primary.hang_hoa_id, so_luong=primary.so_luong, ly_do=data.ly_do,
                    nha_cung_cap_id=data.nha_cung_cap_id, don_hang_id=data.don_hang_id,
                    don_gia=primary.don_gia, ngay_can=data.ngay_can, ghi_chu=data.ghi_chu,
                    dinh_kem_url=data.dinh_kem_url,
                    nguoi_tao=nhan_vien_id_cua(db, nd.id), trang_thai="MOI")
    db.add(ycm); db.flush()
    for it in items:
        db.add(YeuCauMuaCt(yeu_cau_mua_id=ycm.id, hang_hoa_id=it.hang_hoa_id,
                           so_luong=it.so_luong, don_gia=it.don_gia, ghi_chu=it.ghi_chu,
                           nha_cung_cap_id=it.nha_cung_cap_id))
    ghi_audit(db, nd.id, "TAO", "yeu_cau_mua", ycm.id, moi={"so_dong": len(items)})
    db.commit(); db.refresh(ycm)
    return ycm


@router.post("/yeu-cau-mua/{ycm_id}/duyet", response_model=YeuCauMuaRa)
def duyet_de_xuat(ycm_id: int, db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "DUYET"))):
    """Xét duyệt đề xuất — 1 đầu mối (TP Cung ứng / CEO)."""
    ycm = db.get(YeuCauMua, ycm_id)
    if ycm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đề xuất")
    if ycm.trang_thai != "MOI":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Đề xuất đang ở trạng thái {ycm.trang_thai}")
    ycm.trang_thai = "DA_DUYET"; ycm.nguoi_duyet = nhan_vien_id_cua(db, nd.id)
    # Tự động chạy AI Sourcing ngay khi duyệt (nếu bật cấu hình)
    if settings.auto_tim_ncc:
        try:
            import json as _json
            hh = db.get(HangHoa, ycm.hang_hoa_id)
            ten = hh.ten if hh else f"HH #{ycm.hang_hoa_id}"
            xep = _xep_hang_ncc(db, ycm.hang_hoa_id, ycm.so_luong)
            ai = goi_y_ncc_ai(ten, float(ycm.so_luong), xep["danh_sach"])
            ycm.ai_ncc_id = ai.get("khuyen_nghi_ncc_id")
            ycm.ai_goi_y = _json.dumps({"ai": ai, "goi_y": xep}, ensure_ascii=False)
        except Exception:
            pass
    ghi_audit(db, nd.id, "DUYET", "yeu_cau_mua", ycm.id, moi={"trang_thai": "DA_DUYET"})
    db.commit(); db.refresh(ycm)
    return ycm


@router.post("/yeu-cau-mua/{ycm_id}/tu-choi", response_model=YeuCauMuaRa)
def tu_choi_de_xuat(ycm_id: int, data: LyDoVao, db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(yeu_cau(MODULE, "DUYET"))):
    ycm = db.get(YeuCauMua, ycm_id)
    if ycm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đề xuất")
    if ycm.trang_thai != "MOI":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Đề xuất đang ở trạng thái {ycm.trang_thai}")
    ycm.trang_thai = "TU_CHOI"; ycm.nguoi_duyet = nhan_vien_id_cua(db, nd.id)
    if data.ly_do:
        ycm.ghi_chu = (ycm.ghi_chu or "") + f" | Từ chối: {data.ly_do}"
    ghi_audit(db, nd.id, "TU_CHOI", "yeu_cau_mua", ycm.id, moi={"ly_do": data.ly_do})
    db.commit(); db.refresh(ycm)
    return ycm


@router.post("/yeu-cau-mua/{ycm_id}/tao-po", status_code=201)
def tao_po_tu_de_xuat(ycm_id: int, data: TaoPoTuDeXuatVao, db: Session = Depends(get_db),
                      nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Chuyển đề xuất ĐÃ DUYỆT thành PO tới NCC (giữ nguyên Mã bán hàng để tính giá vốn)."""
    ycm = db.get(YeuCauMua, ycm_id)
    if ycm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đề xuất")
    if ycm.trang_thai != "DA_DUYET":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Đề xuất phải ở trạng thái ĐÃ DUYỆT mới tạo PO")
    override_ncc = data.nha_cung_cap_id or ycm.nha_cung_cap_id
    override_gia = data.don_gia
    lines = db.query(YeuCauMuaCt).filter(YeuCauMuaCt.yeu_cau_mua_id == ycm.id).all()
    if not lines:
        lines = [YeuCauMuaCt(hang_hoa_id=ycm.hang_hoa_id, so_luong=ycm.so_luong,
                             don_gia=ycm.don_gia, nha_cung_cap_id=ycm.nha_cung_cap_id)]
    # gom dòng theo NCC (mỗi NCC -> 1 PO)
    nhom = {}
    for i, l in enumerate(lines):
        ncc = l.nha_cung_cap_id or override_ncc
        if not ncc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Thiếu nhà cung cấp cho mặt hàng #{l.hang_hoa_id}")
        g = l.don_gia
        if i == 0 and override_gia is not None:    # giá chọn ở panel áp cho dòng đầu
            g = override_gia
        if g is None:
            g = override_gia if override_gia is not None else ycm.don_gia
        if g is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Thiếu đơn giá cho mặt hàng #{l.hang_hoa_id}")
        nhom.setdefault(ncc, []).append((l.hang_hoa_id, l.so_luong, g))
    pos = []
    for ncc, items_g in nhom.items():
        tong = Decimal(0)
        for _, sl, g in items_g:
            tong += Decimal(sl) * Decimal(g)
        dm = DonMua(so=None, nha_cung_cap_id=ncc, don_hang_id=ycm.don_hang_id,
                    ngay=date.today(), ngay_hen_giao=data.ngay_hen_giao or ycm.ngay_can,
                    tong_tien=tong, trang_thai="CHO_DUYET")
        db.add(dm); db.flush(); dm.so = f"PO-{date.today():%Y%m%d}-{dm.id}"
        for hh, sl, g in items_g:
            db.add(DonMuaCt(don_mua_id=dm.id, hang_hoa_id=hh, so_luong=sl, don_gia=g))
        pos.append(dm)
    ycm.trang_thai = "DA_TAO_PO"; ycm.don_mua_id = pos[0].id
    ghi_audit(db, nd.id, "TAO_PO", "yeu_cau_mua", ycm.id,
              moi={"so_po": len(pos), "po": [p.so for p in pos]})
    db.commit()
    for p in pos:
        db.refresh(p)
    return {"so_po": len(pos), "po": [{"id": p.id, "so": p.so,
            "nha_cung_cap_id": p.nha_cung_cap_id, "tong_tien": float(p.tong_tien)} for p in pos]}


# ----- XEM: danh sách đơn mua -----
@router.get("/don-mua", response_model=list[DonMuaRa])
def ds_don_mua(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(DonMua).order_by(DonMua.id.desc()).all()


# ----- THAO_TAC: tạo đơn mua (nháp -> chờ duyệt). NV_MUA tạo được, chưa tự duyệt. -----
@router.post("/don-mua", response_model=DonMuaRa, status_code=201)
def tao_don_mua(data: DonMuaVao, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    ncc = db.get(NhaCungCap, data.nha_cung_cap_id)
    if ncc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy NCC")
    if ncc.blacklist:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "NCC đang trong blacklist")
    tong = sum(ct.so_luong * ct.don_gia for ct in data.chi_tiet)
    dm = DonMua(so=data.so, nha_cung_cap_id=data.nha_cung_cap_id,
                don_hang_id=data.don_hang_id, ngay_hen_giao=data.ngay_hen_giao,
                ngay=date.today(), tong_tien=tong, trang_thai="CHO_DUYET")
    db.add(dm)
    db.flush()
    if not dm.so:
        dm.so = f"PO-{date.today():%Y%m%d}-{dm.id}"
    for ct in data.chi_tiet:
        db.add(DonMuaCt(don_mua_id=dm.id, hang_hoa_id=ct.hang_hoa_id,
                        so_luong=ct.so_luong, don_gia=ct.don_gia))
    ghi_audit(db, nd.id, "TAO", "don_mua", dm.id,
              moi={"tong_tien": float(tong), "trang_thai": "CHO_DUYET"})
    db.commit()
    db.refresh(dm)
    return dm


# ----- DUYỆT (cần mức ncc=DUYET) + KIỂM HẠN MỨC TIỀN theo vai trò -----
@router.post("/don-mua/{dm_id}/duyet", response_model=DonMuaRa)
def duyet_don_mua(dm_id: int, db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "XEM"))):  # thấy được; quyền duyệt do han_muc
    dm = db.get(DonMua, dm_id)
    if dm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn mua")
    if dm.trang_thai != "CHO_DUYET":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Đơn đang ở trạng thái {dm.trang_thai}")
    # ★ Tầng thứ hai: số tiền có nằm trong hạn mức duyệt của vai trò không?
    kiem_han_muc(db, nd, LOAI_DUYET, dm.tong_tien)
    # ★ Tầng thứ ba: kiểm soát HẠN MỨC CÔNG NỢ của NCC (dư nợ + đơn này không vượt trần)
    ncc = db.get(NhaCungCap, dm.nha_cung_cap_id)
    han_muc = float(ncc.han_muc_cong_no or 0)
    if han_muc > 0:
        du_no = _du_no_ncc(db, dm.nha_cung_cap_id)
        if du_no + float(dm.tong_tien) > han_muc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                f"Vượt hạn mức công nợ NCC: dư nợ {du_no:,.0f} + đơn {float(dm.tong_tien):,.0f} "
                f"> hạn mức {han_muc:,.0f}. Cần thanh toán bớt hoặc nâng hạn mức.")
    dm.trang_thai = "DA_DUYET"
    dm.nguoi_duyet = nhan_vien_id_cua(db, nd.id)
    da_gui = gui_email_ncc(db, dm)  # gửi xác nhận PO từ đầu mối mua hàng
    ghi_audit(db, nd.id, "DUYET", "don_mua", dm.id,
              moi={"trang_thai": "DA_DUYET", "email_ncc": da_gui})
    db.commit()
    db.refresh(dm)
    return dm


# ============ Giai đoạn 1: NHẬN HÀNG (nhập kho) + CÔNG NỢ PHẢI TRẢ + GIÁ VỐN THỰC ============
@router.get("/don-mua/{dm_id}", response_model=DonMuaChiTietRa)
def chi_tiet_don_mua(dm_id: int, db: Session = Depends(get_db),
                     _=Depends(yeu_cau(MODULE, "XEM"))):
    """Chi tiết PO kèm số lượng đã nhận từng dòng (để biết còn phải nhận bao nhiêu)."""
    dm = db.get(DonMua, dm_id)
    if dm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn mua")
    return dm


def _bao_dam_ton(db: Session, hang_hoa_id: int):
    if db.query(TonKho).filter_by(hang_hoa_id=hang_hoa_id).first() is None:
        db.add(TonKho(hang_hoa_id=hang_hoa_id, so_luong=0))
        db.flush()


def _cham_diem_giao_hang(db: Session, dm: DonMua, dat_qc: bool = True) -> dict:
    """Chấm điểm 1 lần giao (0–5): đúng hạn (0–2) + QC (0–2) + đủ lượng (1). Cập nhật điểm TB NCC."""
    if dm.ngay_hen_giao and dm.ngay_giao_thuc:
        tre = (dm.ngay_giao_thuc - dm.ngay_hen_giao).days
        s_ot = 2.0 if tre <= 0 else max(0.0, 2.0 - 0.2 * tre)
    else:
        s_ot = 2.0
    s_qc = 2.0 if dat_qc else 0.0
    s_qty = 1.0  # đánh giá khi đã nhận ĐỦ
    diem = round(min(5.0, max(0.0, s_ot + s_qc + s_qty)), 1)
    db.add(DanhGiaNcc(nha_cung_cap_id=dm.nha_cung_cap_id, don_mua_id=dm.id, diem=Decimal(str(diem))))
    db.flush()
    ncc = db.get(NhaCungCap, dm.nha_cung_cap_id)
    diems = [float(d.diem) for d in db.query(DanhGiaNcc).filter_by(nha_cung_cap_id=dm.nha_cung_cap_id).all()]
    ncc.diem_danh_gia = round(sum(diems) / len(diems), 1) if diems else 0
    kem = sum(1 for d in diems if d < 2)
    if float(ncc.diem_danh_gia) < 2.0 and kem >= 2:
        ncc.blacklist = True
    return {"diem_giao_hang": diem, "diem_danh_gia_moi": float(ncc.diem_danh_gia),
            "so_lan_danh_gia": len(diems), "dung_han": s_ot >= 2.0, "dat_qc": dat_qc}


@router.post("/don-mua/{dm_id}/nhan-hang")
def nhan_hang(dm_id: int, data: NhanHangVao, db: Session = Depends(get_db),
              nd: NguoiDung = Depends(yeu_cau("kho", "THAO_TAC"))):
    """Nhận hàng theo PO: nhập kho, cập nhật SL đã nhận + trạng thái nhận + ngày giao thực,
    và (tùy chọn) sinh CÔNG NỢ PHẢI TRẢ theo giá trị thực nhận kèm hạn thanh toán."""
    dm = db.get(DonMua, dm_id)
    if dm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn mua")
    if dm.trang_thai != "DA_DUYET":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"PO chưa được duyệt (đang {dm.trang_thai}) — không thể nhận hàng.")
    cts = {ct.id: ct for ct in db.query(DonMuaCt).filter_by(don_mua_id=dm_id).all()}
    gia_tri_nhan = Decimal(0)
    pk = PhieuKho(loai="NHAP", don_mua_id=dm.id, nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(pk); db.flush()
    pk.so = f"PN-{date.today():%Y%m%d}-{pk.id}"
    for dong in data.chi_tiet:
        ct = cts.get(dong.don_mua_ct_id)
        if ct is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Dòng {dong.don_mua_ct_id} không thuộc PO này")
        con_lai = ct.so_luong - ct.so_luong_nhan
        if dong.so_luong > con_lai:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Dòng {ct.id}: nhận {dong.so_luong} vượt phần còn lại {con_lai}")
        ct.so_luong_nhan = ct.so_luong_nhan + dong.so_luong
        _bao_dam_ton(db, ct.hang_hoa_id)
        nhap_ton(db, ct.hang_hoa_id, dong.so_luong)
        db.add(PhieuKhoCt(phieu_kho_id=pk.id, hang_hoa_id=ct.hang_hoa_id, so_luong=dong.so_luong))
        gia_tri_nhan += dong.so_luong * ct.don_gia
    # cập nhật trạng thái nhận của PO
    da_du = all(c.so_luong_nhan >= c.so_luong for c in cts.values())
    co_nhan = any(c.so_luong_nhan > 0 for c in cts.values())
    dm.trang_thai_nhan = "DU" if da_du else ("MOT_PHAN" if co_nhan else "CHUA")
    dm.ngay_giao_thuc = date.today()
    # công nợ phải trả theo giá trị thực nhận
    cn_id = None
    if data.tao_cong_no and gia_tri_nhan > 0:
        cn = CongNo(loai="PHAI_TRA", nha_cung_cap_id=dm.nha_cung_cap_id, so_tien=gia_tri_nhan,
                    da_thanh_toan=0, han=data.han_thanh_toan, trang_thai="CHUA_TRA")
        db.add(cn); db.flush(); cn_id = cn.id
    # TỰ CHẤM ĐIỂM NCC khi đã nhận ĐỦ (đúng hạn + đủ lượng + QC)
    diem_ncc = None
    if da_du and settings.auto_cham_diem_ncc:
        try:
            diem_ncc = _cham_diem_giao_hang(db, dm, data.dat_qc)
        except Exception:
            diem_ncc = None
    ghi_audit(db, nd.id, "NHAN_HANG", "don_mua", dm.id,
              moi={"phieu_kho": pk.so, "gia_tri_nhan": float(gia_tri_nhan),
                   "trang_thai_nhan": dm.trang_thai_nhan, "cong_no_id": cn_id,
                   "diem_ncc": diem_ncc})
    db.commit()
    return {"don_mua_id": dm.id, "phieu_kho": pk.so, "gia_tri_nhan": float(gia_tri_nhan),
            "trang_thai_nhan": dm.trang_thai_nhan, "ngay_giao_thuc": str(dm.ngay_giao_thuc),
            "cong_no_id": cn_id, "danh_gia_ncc": diem_ncc}


@router.get("/nha-cung-cap/{ncc_id}/lich-su-danh-gia")
def lich_su_danh_gia(ncc_id: int, db: Session = Depends(get_db),
                     _=Depends(yeu_cau(MODULE, "XEM"))):
    """Lịch sử điểm đánh giá NCC (gồm các lần tự chấm sau giao hàng)."""
    rows = (db.query(DanhGiaNcc).filter_by(nha_cung_cap_id=ncc_id)
              .order_by(DanhGiaNcc.id.desc()).limit(50).all())
    ncc = db.get(NhaCungCap, ncc_id)
    return {"nha_cung_cap_id": ncc_id, "diem_danh_gia": float(ncc.diem_danh_gia) if ncc else None,
            "lich_su": [{"don_mua_id": d.don_mua_id, "diem": float(d.diem), "ngay": str(d.ngay)} for d in rows]}


@router.get("/cong-no")
def ds_cong_no(nha_cung_cap_id: int | None = None, chua_tra: bool = False,
               db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Công nợ PHẢI TRẢ cho NCC (kèm còn lại & cờ quá hạn)."""
    q = db.query(CongNo).filter(CongNo.loai == "PHAI_TRA")
    if nha_cung_cap_id:
        q = q.filter(CongNo.nha_cung_cap_id == nha_cung_cap_id)
    rows = q.order_by(CongNo.id.desc()).limit(300).all()
    out = []
    for r in rows:
        con_lai = float((r.so_tien or 0) - (r.da_thanh_toan or 0))
        if chua_tra and con_lai <= 0:
            continue
        qh = bool(r.han and con_lai > 0 and r.han < date.today())
        out.append({"id": r.id, "nha_cung_cap_id": r.nha_cung_cap_id,
                    "so_tien": float(r.so_tien or 0), "da_thanh_toan": float(r.da_thanh_toan or 0),
                    "con_lai": con_lai, "han": str(r.han) if r.han else None,
                    "trang_thai": r.trang_thai, "qua_han": qh})
    return out


# ============ Mua hàng — Giai đoạn 2: trễ hạn giao · tuổi nợ · kiểm soát hạn mức · thanh toán ============
def _du_no_ncc(db: Session, ncc_id: int) -> float:
    return float(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
                 .filter(CongNo.loai == "PHAI_TRA", CongNo.nha_cung_cap_id == ncc_id).scalar() or 0)


@router.get("/giao-hang/tre-han")
def giao_hang_tre_han(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """PO đã duyệt bị trễ giao: chưa nhận đủ mà quá hẹn, hoặc đã nhận nhưng trễ so với hẹn."""
    hom_nay = date.today()
    pos = db.query(DonMua).filter(DonMua.trang_thai == "DA_DUYET",
                                  DonMua.ngay_hen_giao.isnot(None)).all()
    ten = {n.id: n.ten for n in db.query(NhaCungCap).all()}
    out = []
    for p in pos:
        moc = p.ngay_giao_thuc or hom_nay
        tre = (moc - p.ngay_hen_giao).days
        chua_du = p.trang_thai_nhan != "DU"
        if tre > 0 and (chua_du or p.ngay_giao_thuc):
            out.append({"id": p.id, "so": p.so, "nha_cung_cap_id": p.nha_cung_cap_id,
                        "ten_ncc": ten.get(p.nha_cung_cap_id), "ngay_hen_giao": str(p.ngay_hen_giao),
                        "ngay_giao_thuc": str(p.ngay_giao_thuc) if p.ngay_giao_thuc else None,
                        "trang_thai_nhan": p.trang_thai_nhan, "so_ngay_tre": tre,
                        "da_nhan_xong": p.ngay_giao_thuc is not None and not chua_du})
    out.sort(key=lambda x: -x["so_ngay_tre"])
    return out


@router.get("/cong-no/tuoi-no")
def tuoi_no(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Tuổi nợ phải trả theo số ngày quá hạn: chưa đến hạn / 1–30 / 31–60 / 61–90 / >90."""
    hom_nay = date.today()
    ten = {n.id: n.ten for n in db.query(NhaCungCap).all()}
    buckets = {"chua_den_han": 0.0, "b_0_30": 0.0, "b_31_60": 0.0, "b_61_90": 0.0, "b_90p": 0.0}
    theo_ncc = {}
    for cn in db.query(CongNo).filter(CongNo.loai == "PHAI_TRA").all():
        con = float((cn.so_tien or 0) - (cn.da_thanh_toan or 0))
        if con <= 0:
            continue
        qua = (hom_nay - cn.han).days if cn.han else -1
        if qua <= 0:
            k = "chua_den_han"
        elif qua <= 30:
            k = "b_0_30"
        elif qua <= 60:
            k = "b_31_60"
        elif qua <= 90:
            k = "b_61_90"
        else:
            k = "b_90p"
        buckets[k] += con
        r = theo_ncc.setdefault(cn.nha_cung_cap_id,
                                {"nha_cung_cap_id": cn.nha_cung_cap_id,
                                 "ten": ten.get(cn.nha_cung_cap_id), "con_lai": 0.0, "qua_han": 0.0})
        r["con_lai"] += con
        if qua > 0:
            r["qua_han"] += con
    return {"buckets": buckets, "tong_con_lai": sum(buckets.values()),
            "qua_han": buckets["b_0_30"] + buckets["b_31_60"] + buckets["b_61_90"] + buckets["b_90p"],
            "theo_ncc": sorted(theo_ncc.values(), key=lambda x: -x["con_lai"])}


@router.get("/kiem-soat-cong-no")
def kiem_soat_cong_no(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Hạn mức công nợ vs dư nợ thực tế từng NCC (cảnh báo khi sắp/đã vượt)."""
    out = []
    for n in db.query(NhaCungCap).all():
        du_no = _du_no_ncc(db, n.id)
        han_muc = float(n.han_muc_cong_no or 0)
        if du_no == 0 and han_muc == 0:
            continue
        ty_le = round(du_no / han_muc * 100, 1) if han_muc > 0 else None
        out.append({"nha_cung_cap_id": n.id, "ten": n.ten, "han_muc": han_muc, "du_no": du_no,
                    "ty_le": ty_le, "vuot": han_muc > 0 and du_no > han_muc,
                    "sap_vuot": han_muc > 0 and ty_le is not None and 80 <= ty_le <= 100})
    return sorted(out, key=lambda x: -(x["ty_le"] or 0))


@router.post("/bao-gia", response_model=BaoGiaRa, status_code=201)
def tao_bao_gia(data: BaoGiaVao, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Nhập báo giá NCC (giá chào hiện tại) — engine AI sẽ ưu tiên giá này nếu còn hiệu lực."""
    bg = BaoGiaNcc(nha_cung_cap_id=data.nha_cung_cap_id, hang_hoa_id=data.hang_hoa_id,
                   don_gia=data.don_gia, so_luong_toi_thieu=data.so_luong_toi_thieu,
                   hieu_luc_den=data.hieu_luc_den, nguon=data.nguon,
                   dieu_kien=data.dieu_kien, ghi_chu=data.ghi_chu,
                   nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(bg); db.flush()
    ghi_audit(db, nd.id, "TAO", "bao_gia_ncc", bg.id,
              moi={"ncc": data.nha_cung_cap_id, "hang_hoa": data.hang_hoa_id, "gia": float(data.don_gia)})
    db.commit(); db.refresh(bg)
    return bg


@router.get("/bao-gia", response_model=list[BaoGiaRa])
def ds_bao_gia(hang_hoa_id: int | None = None, nha_cung_cap_id: int | None = None,
               con_hieu_luc: bool = False, db: Session = Depends(get_db),
               _=Depends(yeu_cau(MODULE, "XEM"))):
    q = db.query(BaoGiaNcc)
    if hang_hoa_id:
        q = q.filter(BaoGiaNcc.hang_hoa_id == hang_hoa_id)
    if nha_cung_cap_id:
        q = q.filter(BaoGiaNcc.nha_cung_cap_id == nha_cung_cap_id)
    rows = q.order_by(BaoGiaNcc.id.desc()).limit(300).all()
    if con_hieu_luc:
        rows = [r for r in rows if r.hieu_luc_den is None or r.hieu_luc_den >= date.today()]
    return rows


def _tieu_de_rfq(ten_hang: str) -> str:
    return f"[SVWS] Yêu cầu báo giá: {ten_hang}"


def _noi_dung_rfq(db, hang_hoa_id, so_luong, d):
    """Dựng tiêu đề + nội dung email hỏi giá chuyên nghiệp từ thông tin sản phẩm/điều kiện."""
    hh = db.get(HangHoa, hang_hoa_id)
    ten_hang = hh.ten if hh else f"HH #{hang_hoa_id}"
    ma_hang = getattr(hh, "ma", None)
    don_vi = (getattr(d, "don_vi", None) or (hh.don_vi if hh else None) or "-")
    han = getattr(d, "han_bao_gia", None)
    L = ["Kính gửi Quý Nhà cung cấp,", "",
         f"{settings.cong_ty_ten} trân trọng đề nghị Quý công ty báo giá cho nhu cầu mua sắm sau:",
         "", "THÔNG TIN HÀNG HÓA", f"- Tên hàng: {ten_hang}"]
    if ma_hang:
        L.append(f"- Mã hàng: {ma_hang}")
    if getattr(d, "quy_cach", None):
        L.append(f"- Quy cách / thông số: {d.quy_cach}")
    L.append(f"- Đơn vị tính: {don_vi}")
    L.append(f"- Số lượng: {so_luong}")
    L += ["", "YÊU CẦU GIAO HÀNG & THANH TOÁN",
          f"- Nơi giao: {getattr(d, 'noi_giao', None) or 'Theo thỏa thuận'}",
          f"- Thời gian giao mong muốn: {getattr(d, 'thoi_gian_giao', None) or 'Theo thỏa thuận'}",
          f"- Điều kiện thanh toán: {getattr(d, 'dieu_kien_thanh_toan', None) or 'Theo thỏa thuận'}"]
    if getattr(d, "yeu_cau_khac", None):
        L.append(f"- Yêu cầu khác: {d.yeu_cau_khac}")
    L += ["", "NỘI DUNG BÁO GIÁ CẦN CUNG CẤP",
          "1. Đơn giá (ghi rõ đã/chưa gồm VAT) và tổng giá trị.",
          "2. Thời hạn hiệu lực của báo giá.",
          "3. Thời gian giao hàng dự kiến.",
          "4. Điều kiện giao hàng và thanh toán.",
          "5. Chứng từ kèm theo (CO, CQ, catalogue...) nếu có.", ""]
    L.append(f"Vui lòng gửi báo giá{(' trước ngày ' + str(han)) if han else ''} về địa chỉ email {settings.email_from_ncc}.")
    L.append("Mọi trao đổi xin liên hệ Bộ phận Mua hàng theo email trên.")
    L += ["", "Trân trọng cảm ơn sự hợp tác của Quý công ty.", "",
          "------------------------------",
          settings.cong_ty_ten.upper(),
          f'"{settings.cong_ty_slogan}"',
          f"Địa chỉ: {settings.cong_ty_dia_chi}",
          f"Email: {settings.email_from_ncc}",
          "Bộ phận Mua hàng"]
    return _tieu_de_rfq(ten_hang), "\n".join(L)


def _tieu_de_than(db, hang_hoa_id, so_luong, data):
    """Ưu tiên nội dung đã biên tập (override); nếu không thì dựng theo mẫu."""
    if getattr(data, "noi_dung", None):
        hh = db.get(HangHoa, hang_hoa_id)
        ten = hh.ten if hh else f"HH #{hang_hoa_id}"
        return (getattr(data, "tieu_de", None) or _tieu_de_rfq(ten)), data.noi_dung
    return _noi_dung_rfq(db, hang_hoa_id, so_luong, data)


def _gui_rfq(db, nd, hang_hoa_id, so_luong, han_bao_gia, ncc_ids, tieu_de, than,
             yeu_cau_mua_id=None) -> dict:
    """Tạo RFQ và gửi tới các NCC qua 1 đầu mối email, ghi nhật ký từng NCC."""
    rfq = Rfq(hang_hoa_id=hang_hoa_id, so_luong=so_luong, han_bao_gia=han_bao_gia,
              yeu_cau_mua_id=yeu_cau_mua_id, noi_dung=than,
              gui_tu=settings.email_from_ncc, nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(rfq); db.flush()
    provider = lay_email_provider()
    logs = []
    for nid in ncc_ids:
        ncc = db.get(NhaCungCap, nid)
        if ncc is None:
            continue
        email = ncc.email
        if email:
            kq = provider.gui(email, tieu_de, than, None, gui_tu=settings.email_from_ncc)
            ok = kq.get("trang_thai") == "GUI_OK"; note = kq.get("ghi_chu")
        else:
            ok, note = False, "NCC chưa có email"
        db.add(RfqLog(rfq_id=rfq.id, nha_cung_cap_id=nid, email=email, da_gui=ok, ket_qua=note))
        logs.append((nid, ok, note))
    ghi_audit(db, nd.id, "GUI_RFQ", "rfq", rfq.id,
              moi={"hang_hoa": hang_hoa_id, "so_ncc": len(logs), "gui_tu": settings.email_from_ncc})
    db.commit()
    return {"rfq_id": rfq.id, "gui_tu": settings.email_from_ncc, "provider": provider.ten,
            "tieu_de": tieu_de,
            "da_gui": sum(1 for _, ok, _ in logs if ok), "tong": len(logs),
            "chi_tiet": [{"nha_cung_cap_id": n, "da_gui": ok, "ket_qua": note} for n, ok, note in logs]}


@router.post("/rfq")
def tao_rfq(data: RfqVao, db: Session = Depends(get_db),
            nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Gửi RFQ tới nhiều NCC từ 1 đầu mối email, có nhật ký."""
    tieu_de, than = _tieu_de_than(db, data.hang_hoa_id, data.so_luong, data)
    return _gui_rfq(db, nd, data.hang_hoa_id, data.so_luong, data.han_bao_gia,
                    data.nha_cung_cap_ids, tieu_de, than, data.yeu_cau_mua_id)


@router.post("/yeu-cau-mua/{ycm_id}/rfq-preview")
def rfq_preview(ycm_id: int, data: RfqNoiDungVao, db: Session = Depends(get_db),
                _=Depends(yeu_cau(MODULE, "XEM"))):
    """Xem trước email hỏi giá (không gửi) để biên tập trước khi gửi."""
    ycm = db.get(YeuCauMua, ycm_id)
    if ycm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đề xuất")
    hh = db.get(HangHoa, ycm.hang_hoa_id)
    tieu_de, than = _noi_dung_rfq(db, ycm.hang_hoa_id, ycm.so_luong, data)
    return {"tieu_de": tieu_de, "noi_dung": than,
            "ten_hang": hh.ten if hh else None, "don_vi": (hh.don_vi if hh else None),
            "so_luong": float(ycm.so_luong)}


@router.post("/yeu-cau-mua/{ycm_id}/gui-rfq")
def gui_rfq_tu_de_xuat(ycm_id: int, data: GuiRfqVao, db: Session = Depends(get_db),
                       nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Gửi RFQ cho đúng mặt hàng/số lượng của 1 đề xuất tới các NCC được chọn."""
    ycm = db.get(YeuCauMua, ycm_id)
    if ycm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đề xuất")
    tieu_de, than = _tieu_de_than(db, ycm.hang_hoa_id, ycm.so_luong, data)
    return _gui_rfq(db, nd, ycm.hang_hoa_id, ycm.so_luong, data.han_bao_gia,
                    data.nha_cung_cap_ids, tieu_de, than, ycm_id)


@router.get("/rfq", response_model=list[RfqRa])
def ds_rfq(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(Rfq).order_by(Rfq.id.desc()).limit(100).all()


@router.get("/rfq/{rfq_id}")
def chi_tiet_rfq(rfq_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    rfq = db.get(Rfq, rfq_id)
    if rfq is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy RFQ")
    logs = db.query(RfqLog).filter(RfqLog.rfq_id == rfq_id).all()
    return {"id": rfq.id, "hang_hoa_id": rfq.hang_hoa_id, "so_luong": float(rfq.so_luong),
            "han_bao_gia": str(rfq.han_bao_gia) if rfq.han_bao_gia else None,
            "gui_tu": rfq.gui_tu, "ngay": str(rfq.ngay), "noi_dung": rfq.noi_dung,
            "log": [{"nha_cung_cap_id": l.nha_cung_cap_id, "email": l.email,
                     "da_gui": l.da_gui, "ket_qua": l.ket_qua} for l in logs]}


def _po_tieu_de(dm) -> str:
    return f"[SVWS] Đơn đặt hàng {dm.so}"


def _noi_dung_po(db, dm, d=None):
    """Dựng tiêu đề + chứng từ PO chuyên nghiệp; đơn giá/điều kiện lấy từ dòng PO & báo giá NCC."""
    ncc = db.get(NhaCungCap, dm.nha_cung_cap_id)
    ten_ncc = ncc.ten if ncc else f"NCC #{dm.nha_cung_cap_id}"
    lines = db.query(DonMuaCt).filter(DonMuaCt.don_mua_id == dm.id).all()
    def _v(x):
        return f"{float(x or 0):,.0f}".replace(",", ".") + " ₫"
    L = [f"Kính gửi {ten_ncc},", "",
         f"{settings.cong_ty_ten} xác nhận đặt hàng theo đơn dưới đây:", "",
         "ĐƠN ĐẶT HÀNG (PO)", f"- Số PO: {dm.so}", f"- Ngày: {date.today()}",
         f"- Nhà cung cấp: {ten_ncc}"]
    bg_ref = None
    hom_nay = date.today()
    for ln in lines:
        bg = (db.query(BaoGiaNcc)
                .filter(BaoGiaNcc.hang_hoa_id == ln.hang_hoa_id,
                        BaoGiaNcc.nha_cung_cap_id == dm.nha_cung_cap_id)
                .order_by(BaoGiaNcc.id.desc()).first())
        if bg and (bg.hieu_luc_den is None or bg.hieu_luc_den >= hom_nay):
            bg_ref = bg
            break
    if bg_ref:
        hl = f", hiệu lực đến {bg_ref.hieu_luc_den}" if bg_ref.hieu_luc_den else ""
        L.append(f"- Tham chiếu báo giá ngày {bg_ref.ngay}{hl}")
    L += ["", "CHI TIẾT HÀNG HÓA"]
    tong = 0.0
    for i, ln in enumerate(lines, 1):
        hh = db.get(HangHoa, ln.hang_hoa_id)
        ten = hh.ten if hh else f"HH #{ln.hang_hoa_id}"
        dv = hh.don_vi if hh else ""
        tt = float(ln.so_luong) * float(ln.don_gia or 0)
        tong += tt
        L.append(f"{i}. {ten} | ĐVT: {dv} | SL: {float(ln.so_luong):g} | "
                 f"Đơn giá: {_v(ln.don_gia)} | Thành tiền: {_v(tt)}")
    L += [f"Tổng cộng (chưa gồm VAT): {_v(tong)}", "", "ĐIỀU KIỆN"]
    g = lambda k: (getattr(d, k, None) if d else None)
    ngay_hen = g("ngay_hen_giao") or dm.ngay_hen_giao
    L.append(f"- Nơi giao: {g('noi_giao') or settings.cong_ty_dia_chi}")
    L.append(f"- Ngày giao yêu cầu: {ngay_hen if ngay_hen else 'Theo thỏa thuận'}")
    L.append(f"- Điều kiện giao hàng: {g('dieu_kien_giao_hang') or 'Theo thỏa thuận'}")
    L.append(f"- Điều kiện thanh toán: {g('dieu_kien_thanh_toan') or 'Theo thỏa thuận'}")
    if g("ghi_chu"):
        L.append(f"- Ghi chú: {g('ghi_chu')}")
    L += ["", f"Đề nghị Quý công ty xác nhận đơn hàng và phản hồi về email {settings.email_from_ncc}.",
          "", "Trân trọng,", "------------------------------",
          settings.cong_ty_ten.upper(), f'"{settings.cong_ty_slogan}"',
          f"Địa chỉ: {settings.cong_ty_dia_chi}", f"Email: {settings.email_from_ncc}", "Bộ phận Mua hàng"]
    return _po_tieu_de(dm), "\n".join(L)


def _po_pdf_data(db, dm, d):
    ncc = db.get(NhaCungCap, dm.nha_cung_cap_id)
    lines = db.query(DonMuaCt).filter(DonMuaCt.don_mua_id == dm.id).all()
    specs = getattr(d, "specs", None) or []
    vat = float(getattr(d, "vat", 0) or 0)
    L = []
    for i, ln in enumerate(lines):
        hh = db.get(HangHoa, ln.hang_hoa_id)
        L.append({"ten": hh.ten if hh else f"HH#{ln.hang_hoa_id}",
                  "mo_ta": specs[i] if i < len(specs) else "",
                  "sl": float(ln.so_luong), "dvt": (hh.don_vi if hh else ""),
                  "don_gia": float(ln.don_gia or 0), "vat": vat})
    today = date.today().strftime("%d/%m/%Y")
    nlh = getattr(d, "nguoi_lien_he", None) or (getattr(ncc, "nguoi_phu_trach", None) if ncc else None) or ""
    return {
        "ma_yeu_cau": getattr(d, "ma_yeu_cau", None) or dm.so,
        "ngay": today, "hieu_luc_den": getattr(d, "hieu_luc_den", None) or "",
        "ncc_ten": ncc.ten if ncc else "", "ncc_email": ncc.email if ncc else "",
        "nguoi_lien_he": nlh, "lines": L,
        "thanh_toan": getattr(d, "dieu_kien_thanh_toan", None) or "Theo thỏa thuận",
        "thoi_gian_giao": getattr(d, "thoi_gian_giao", None) or "Theo thỏa thuận",
        "dia_diem_giao": getattr(d, "noi_giao", None) or settings.cong_ty_dia_chi,
        "nguoi_dat": getattr(d, "nguoi_dat", None) or "",
        "nguoi_duyet": getattr(d, "nguoi_duyet", None) or "",
    }


def _xuat_po_pdf(db, dm, d) -> str:
    base = (getattr(settings, "storage_dir", None) or os.environ.get("STORAGE_DIR") or "/tmp")
    thu_muc = os.path.join(base, "po")
    os.makedirs(thu_muc, exist_ok=True)
    ten_file = "PO_" + "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in (dm.so or str(dm.id))) + ".pdf"
    path = os.path.join(thu_muc, ten_file)
    cong_ty = {"ten": settings.cong_ty_ten, "dia_chi": settings.cong_ty_dia_chi,
               "tel": getattr(settings, "cong_ty_tel", ""), "email": getattr(settings, "cong_ty_email", ""),
               "website": getattr(settings, "cong_ty_website", "")}
    tao_po_pdf(path, _po_pdf_data(db, dm, d), cong_ty,
               font_path=getattr(settings, "pdf_font_path", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
               font_bold_path=getattr(settings, "pdf_font_bold_path", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
               chu_ky_path=getattr(settings, "pdf_chu_ky_path", "") or "",
               ky_so=bool(getattr(d, "ky_so", True)))
    return path


@router.post("/don-mua/{dm_id}/po-pdf")
def po_pdf(dm_id: int, data: PoPdfVao, db: Session = Depends(get_db),
           _=Depends(yeu_cau(MODULE, "XEM"))):
    """Xuất chứng từ PO dạng PDF (theo mẫu SVWS) để tải về / lưu lại."""
    dm = db.get(DonMua, dm_id)
    if dm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy PO")
    path = _xuat_po_pdf(db, dm, data)
    return FileResponse(path, media_type="application/pdf", filename=os.path.basename(path))


@router.post("/don-mua/{dm_id}/po-preview")
def po_preview(dm_id: int, data: PoNoiDungVao, db: Session = Depends(get_db),
               _=Depends(yeu_cau(MODULE, "XEM"))):
    """Xem trước chứng từ PO (không gửi)."""
    dm = db.get(DonMua, dm_id)
    if dm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy PO")
    ncc = db.get(NhaCungCap, dm.nha_cung_cap_id)
    tieu_de, than = _noi_dung_po(db, dm, data)
    tong = sum(float(l.so_luong) * float(l.don_gia or 0)
               for l in db.query(DonMuaCt).filter(DonMuaCt.don_mua_id == dm.id))
    return {"tieu_de": tieu_de, "noi_dung": than, "so": dm.so,
            "ten_ncc": ncc.ten if ncc else None, "email": ncc.email if ncc else None,
            "tong": tong, "trang_thai": dm.trang_thai,
            "ngay_hen_giao": str(dm.ngay_hen_giao) if dm.ngay_hen_giao else None}


@router.post("/don-mua/{dm_id}/gui-po")
def gui_po(dm_id: int, data: GuiPoVao, db: Session = Depends(get_db),
           nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Gửi chứng từ PO tới NCC qua 1 đầu mối email; cho chỉnh nội dung & điều kiện."""
    dm = db.get(DonMua, dm_id)
    if dm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy PO")
    ncc = db.get(NhaCungCap, dm.nha_cung_cap_id)
    if data.ngay_hen_giao:
        dm.ngay_hen_giao = data.ngay_hen_giao
    if data.noi_dung:
        tieu_de = data.tieu_de or _po_tieu_de(dm)
        than = data.noi_dung
    else:
        tieu_de, than = _noi_dung_po(db, dm, data)
    if ncc is None or not ncc.email:
        db.commit()
        return {"da_gui": False, "email": ncc.email if ncc else None,
                "ly_do": "NCC chưa có email", "tieu_de": tieu_de}
    dinh_kem = None
    co_pdf = False
    if getattr(data, "dinh_kem_pdf", True):
        try:
            ppath = _xuat_po_pdf(db, dm, data)
            dinh_kem = [{"duong_dan": ppath, "ten_file": os.path.basename(ppath)}]
            co_pdf = True
        except Exception:
            dinh_kem = None
    kq = lay_email_provider().gui(ncc.email, tieu_de, than, dinh_kem, gui_tu=settings.email_from_ncc)
    ok = kq.get("trang_thai") == "GUI_OK"
    ghi_audit(db, nd.id, "GUI_PO", "don_mua", dm.id,
              moi={"email": ncc.email, "da_gui": ok, "co_pdf": co_pdf, "gui_tu": settings.email_from_ncc})
    db.commit()
    return {"da_gui": ok, "email": ncc.email, "gui_tu": settings.email_from_ncc,
            "co_pdf": co_pdf, "tieu_de": tieu_de, "ket_qua": kq.get("ghi_chu")}


def _xep_hang_ncc(db: Session, hang_hoa_id: int, so_luong) -> dict:
    """Lõi xếp hạng NCC cho 1 mặt hàng (giá gần nhất + đánh giá + đúng hạn + hạn mức)."""
    # 1) Giá gần nhất của mặt hàng theo từng NCC (lấy theo PO mới nhất)
    gia_gan = {}
    q = (db.query(DonMuaCt, DonMua).join(DonMua, DonMuaCt.don_mua_id == DonMua.id)
           .filter(DonMuaCt.hang_hoa_id == hang_hoa_id).all())
    for ct, dm in q:
        cur = gia_gan.get(dm.nha_cung_cap_id)
        if cur is None or dm.id > cur[0]:
            gia_gan[dm.nha_cung_cap_id] = (dm.id, float(ct.don_gia))
    # 2) Tỷ lệ giao đúng hạn theo NCC (trên các PO đã giao)
    dung_han = {}
    for dm in db.query(DonMua).filter(DonMua.ngay_giao_thuc.isnot(None),
                                      DonMua.ngay_hen_giao.isnot(None)).all():
        t, d = dung_han.get(dm.nha_cung_cap_id, (0, 0))
        dung_han[dm.nha_cung_cap_id] = (t + 1, d + (1 if dm.ngay_giao_thuc <= dm.ngay_hen_giao else 0))
    # 3) BÁO GIÁ còn hiệu lực (giá chào hiện tại) — ưu tiên hơn giá lịch sử
    hom_nay = date.today()
    bao_gia = {}
    for bg in (db.query(BaoGiaNcc).filter(BaoGiaNcc.hang_hoa_id == hang_hoa_id).all()):
        if bg.hieu_luc_den is not None and bg.hieu_luc_den < hom_nay:
            continue
        cur = bao_gia.get(bg.nha_cung_cap_id)
        if cur is None or bg.id > cur[0]:
            bao_gia[bg.nha_cung_cap_id] = (bg.id, float(bg.don_gia), bg.hieu_luc_den)
    # giá dùng để chấm điểm: báo giá > lịch sử
    out = []
    sup_rows = db.query(NhaCungCap).all()
    gia_dung_map = {}
    for s in sup_rows:
        bg = bao_gia.get(s.id)
        gia_dung_map[s.id] = bg[1] if bg else gia_gan.get(s.id, (0, None))[1]
    gia_list = [v for v in gia_dung_map.values() if v]
    gia_min = min(gia_list) if gia_list else None
    for s in sup_rows:
        if s.blacklist:
            continue
        bg = bao_gia.get(s.id)
        gia_ls = gia_gan.get(s.id, (0, None))[1]
        gia_bg = bg[1] if bg else None
        gia = gia_bg if gia_bg is not None else gia_ls
        nguon_gia = "BAO_GIA" if gia_bg is not None else ("LICH_SU" if gia_ls is not None else None)
        hieu_luc = bg[2] if bg else None
        td = dung_han.get(s.id)
        ty_le_dh = round(td[1] / td[0], 3) if td and td[0] else None
        du_no = _du_no_ncc(db, s.id)
        han_muc = float(s.han_muc_cong_no or 0)
        gia_tri = float(so_luong) * gia if gia else None
        trong_han = (han_muc == 0) or (gia_tri is None) or (du_no + gia_tri <= han_muc)
        # chấm điểm (0–100): giá 40% · đánh giá 30% · đúng hạn 30%
        s_gia = (gia_min / gia) if (gia and gia_min) else 0.6
        s_dg = float(s.diem_danh_gia or 0) / 5
        s_dh = ty_le_dh if ty_le_dh is not None else 0.7
        diem = round(100 * (0.4 * s_gia + 0.3 * s_dg + 0.3 * s_dh), 1)
        if not trong_han:
            diem = round(diem - 30, 1)
        out.append({"nha_cung_cap_id": s.id, "ten": s.ten,
                    "gia_gan_nhat": gia, "gia_bao_gia": gia_bg, "gia_lich_su": gia_ls,
                    "gia_dung": gia, "nguon_gia": nguon_gia,
                    "hieu_luc_den": str(hieu_luc) if hieu_luc else None,
                    "diem_danh_gia": float(s.diem_danh_gia or 0),
                    "ty_le_dung_han": ty_le_dh, "du_no": du_no, "han_muc": han_muc,
                    "con_han_muc": (han_muc - du_no) if han_muc > 0 else None,
                    "trong_han_muc": trong_han, "diem_tong": diem, "khuyen_nghi": False})
    out.sort(key=lambda x: -x["diem_tong"])
    for x in out:
        if x["trong_han_muc"]:
            x["khuyen_nghi"] = True
            break
    best = next((x["nha_cung_cap_id"] for x in out if x["khuyen_nghi"]), None)
    return {"hang_hoa_id": hang_hoa_id, "goi_y_ncc_id": best, "danh_sach": out}


@router.get("/goi-y-ncc")
def goi_y_ncc(hang_hoa_id: int, so_luong: Decimal = Decimal(1),
              db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Tối ưu chọn NCC cho 1 mặt hàng (xếp hạng + khuyến nghị)."""
    return _xep_hang_ncc(db, hang_hoa_id, so_luong)


@router.post("/yeu-cau-mua/{ycm_id}/tim-ncc-ai")
def tim_ncc_ai(ycm_id: int, db: Session = Depends(get_db),
               _=Depends(yeu_cau(MODULE, "XEM"))):
    """AI Sourcing Agent: từ 1 đề xuất, xếp hạng NCC nội bộ + AI khuyến nghị/cảnh báo/gợi ý nguồn mới."""
    ycm = db.get(YeuCauMua, ycm_id)
    if ycm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đề xuất")
    hh = db.get(HangHoa, ycm.hang_hoa_id)
    ten_hang = hh.ten if hh else f"HH #{ycm.hang_hoa_id}"
    xep = _xep_hang_ncc(db, ycm.hang_hoa_id, ycm.so_luong)
    ai = goi_y_ncc_ai(ten_hang, float(ycm.so_luong), xep["danh_sach"])
    return {"yeu_cau_mua_id": ycm.id, "ten_hang": ten_hang, "goi_y": xep,
            "ai": ai, "provider": ai.get("nguon")}


@router.post("/yeu-cau-mua/{ycm_id}/tim-ncc-web")
def tim_ncc_web_ep(ycm_id: int, khu_vuc: str = "Việt Nam", db: Session = Depends(get_db),
                   _=Depends(yeu_cau(MODULE, "XEM"))):
    """Dò NCC mới trên web cho 1 đề xuất (kết quả CẦN KIỂM CHỨNG trước khi thêm vào hồ sơ)."""
    ycm = db.get(YeuCauMua, ycm_id)
    if ycm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đề xuất")
    hh = db.get(HangHoa, ycm.hang_hoa_id)
    ten = hh.ten if hh else f"HH #{ycm.hang_hoa_id}"
    return {"yeu_cau_mua_id": ycm.id, "ten_hang": ten, **tim_ncc_web(ten, khu_vuc)}


@router.post("/cong-no/{cn_id}/thanh-toan")
def thanh_toan_ncc(cn_id: int, data: ThuTienVao, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau("ke_toan", "THAO_TAC"))):
    """Ghi nhận THANH TOÁN cho NCC (giảm công nợ phải trả). Quyền: kế toán THAO_TAC."""
    cn = db.query(CongNo).filter_by(id=cn_id).with_for_update().first()
    if cn is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy công nợ")
    if cn.loai != "PHAI_TRA":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Công nợ này không phải khoản phải trả")
    con_lai = cn.so_tien - cn.da_thanh_toan
    if data.so_tien > con_lai:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Thanh toán {data.so_tien:,.0f} vượt còn lại {con_lai:,.0f}")
    db.add(ThanhToan(cong_no_id=cn.id, so_tien=data.so_tien, ngay=date.today(), hinh_thuc=data.hinh_thuc))
    cn.da_thanh_toan = cn.da_thanh_toan + data.so_tien
    cn.trang_thai = "DA_TRA" if cn.da_thanh_toan >= cn.so_tien else "TRA_MOT_PHAN"
    ghi_audit(db, nd.id, "THANH_TOAN", "cong_no", cn.id,
              moi={"so_tien": float(data.so_tien), "trang_thai": cn.trang_thai})
    db.commit()
    return {"id": cn.id, "da_thanh_toan": float(cn.da_thanh_toan),
            "con_lai": float(cn.so_tien - cn.da_thanh_toan), "trang_thai": cn.trang_thai}
