"""
Bán hàng — MỞ RỘNG:
  (1) Lưu trữ tệp PO / Hợp đồng đính kèm đơn hàng.
  (2) Email chào hàng (nội dung PHẢI được duyệt) + ĐÍNH KÈM tệp khi gửi.
Gửi qua email_gateway; địa chỉ gửi = settings.email_from (sv-sales@watersolutions.company).
"""
import os, uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..config import settings
from ..rbac import yeu_cau
from ..deps import nhan_vien_id_cua
from ..audit import ghi_audit
from ..email_gateway import lay_email_provider
from ..inbound_gateway import lay_inbound_provider
from ..ai_gateway import lay_ai_provider
from ..models import (NguoiDung, DonHang, KhachHang, TepDinhKem, ChienDichEmail, EmailLog, LienLac, CongViec, CoHoi, BaoGia, DonMua, DonMuaCt)
from ..schemas import (TepRa, ChienDichVao, ChienDichRa, GuiEmailKHVao, GhiLienLacVao, LienLacRa, GanKhachVao, TrangThaiCVVao, GiaiDoanVao)

router = APIRouter(prefix="/ban-hang", tags=["ban_hang"])
MODULE = "ban_hang"
LOAI_TEP = {"PO", "HOP_DONG", "KHAC"}


async def _luu_tep(file: UploadFile, doi_tuong: str, doi_tuong_id: int):
    """Lưu tệp tải lên vào storage_dir/<doi_tuong>/<id>/, trả (đường dẫn, kích thước)."""
    thu_muc = os.path.join(settings.storage_dir, doi_tuong.lower(), str(doi_tuong_id))
    os.makedirs(thu_muc, exist_ok=True)
    safe = f"{uuid.uuid4().hex}_{os.path.basename(file.filename or 'file')}"
    duong_dan = os.path.join(thu_muc, safe)
    data = await file.read()
    with open(duong_dan, "wb") as f:
        f.write(data)
    return duong_dan, len(data)


# ============ (1) TỆP PO / HỢP ĐỒNG (đơn hàng) ============
@router.post("/don-hang/{dh_id}/tep", response_model=TepRa, status_code=201)
async def tai_len_tep(dh_id: int, file: UploadFile = File(...), loai: str = Form("KHAC"),
                      db: Session = Depends(get_db),
                      nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.get(DonHang, dh_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn hàng")
    loai = loai.upper()
    if loai not in LOAI_TEP:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"loai phải thuộc {LOAI_TEP}")
    duong_dan, kich_thuoc = await _luu_tep(file, "DON_HANG", dh_id)
    tep = TepDinhKem(doi_tuong="DON_HANG", doi_tuong_id=dh_id, loai=loai,
                     ten_file=file.filename or os.path.basename(duong_dan), duong_dan=duong_dan,
                     kich_thuoc=kich_thuoc, content_type=file.content_type,
                     nguoi_tai_len=nhan_vien_id_cua(db, nd.id))
    db.add(tep); db.flush()
    ghi_audit(db, nd.id, "TAO", "tep_dinh_kem", tep.id, moi={"don_hang": dh_id, "loai": loai})
    db.commit(); db.refresh(tep)
    return tep


@router.get("/don-hang/{dh_id}/tep", response_model=list[TepRa])
def ds_tep(dh_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(TepDinhKem).filter_by(doi_tuong="DON_HANG", doi_tuong_id=dh_id) \
             .order_by(TepDinhKem.id).all()


@router.get("/tep/{tep_id}/tai-ve")
def tai_ve(tep_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    tep = db.get(TepDinhKem, tep_id)
    if tep is None or not os.path.exists(tep.duong_dan):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tệp")
    return FileResponse(tep.duong_dan, filename=tep.ten_file,
                        media_type=tep.content_type or "application/octet-stream")


# ============ (2) EMAIL CHÀO HÀNG (CÓ DUYỆT + ĐÍNH KÈM) ============
@router.post("/chien-dich", response_model=ChienDichRa, status_code=201)
def tao_chien_dich(data: ChienDichVao, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    kh_ids = ",".join(str(i) for i in data.khach_hang_ids) if data.khach_hang_ids else None
    cd = ChienDichEmail(ten=data.ten, tieu_de=data.tieu_de, noi_dung=data.noi_dung,
                        bo_loc_abc=data.bo_loc_abc, khach_hang_ids=kh_ids,
                        trang_thai="CHO_DUYET", nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(cd); db.flush()
    ghi_audit(db, nd.id, "TAO", "chien_dich_email", cd.id, moi={"ten": data.ten})
    db.commit(); db.refresh(cd)
    return cd


@router.get("/chien-dich", response_model=list[ChienDichRa])
def ds_chien_dich(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(ChienDichEmail).order_by(ChienDichEmail.id.desc()).all()


# Đính kèm tệp gửi cùng email (trước khi gửi)
@router.post("/chien-dich/{cd_id}/tep", response_model=TepRa, status_code=201)
async def tai_len_tep_cd(cd_id: int, file: UploadFile = File(...),
                         db: Session = Depends(get_db),
                         nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    cd = db.get(ChienDichEmail, cd_id)
    if cd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy chiến dịch")
    if cd.trang_thai == "DA_GUI":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chiến dịch đã gửi — không đính kèm thêm")
    duong_dan, kich_thuoc = await _luu_tep(file, "CHIEN_DICH", cd_id)
    tep = TepDinhKem(doi_tuong="CHIEN_DICH", doi_tuong_id=cd_id, loai="KHAC",
                     ten_file=file.filename or os.path.basename(duong_dan), duong_dan=duong_dan,
                     kich_thuoc=kich_thuoc, content_type=file.content_type,
                     nguoi_tai_len=nhan_vien_id_cua(db, nd.id))
    db.add(tep); db.flush()
    ghi_audit(db, nd.id, "TAO", "tep_dinh_kem", tep.id, moi={"chien_dich": cd_id})
    db.commit(); db.refresh(tep)
    return tep


@router.get("/chien-dich/{cd_id}/tep", response_model=list[TepRa])
def ds_tep_cd(cd_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(TepDinhKem).filter_by(doi_tuong="CHIEN_DICH", doi_tuong_id=cd_id) \
             .order_by(TepDinhKem.id).all()


# Duyệt NỘI DUNG — chỉ cấp DUYỆT (TP_KD/CEO)
@router.post("/chien-dich/{cd_id}/duyet", response_model=ChienDichRa)
def duyet_chien_dich(cd_id: int, db: Session = Depends(get_db),
                     nd: NguoiDung = Depends(yeu_cau(MODULE, "DUYET"))):
    cd = db.get(ChienDichEmail, cd_id)
    if cd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy chiến dịch")
    if cd.trang_thai not in ("CHO_DUYET", "TU_CHOI"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Chiến dịch đang ở {cd.trang_thai}")
    cd.trang_thai = "DA_DUYET"
    cd.nguoi_duyet = nhan_vien_id_cua(db, nd.id)
    ghi_audit(db, nd.id, "DUYET", "chien_dich_email", cd.id, moi={"trang_thai": "DA_DUYET"})
    db.commit(); db.refresh(cd)
    return cd


# Gửi — chỉ khi nội dung ĐÃ DUYỆT; đính kèm các tệp của chiến dịch
@router.post("/chien-dich/{cd_id}/gui")
def gui_chien_dich(cd_id: int, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    cd = db.get(ChienDichEmail, cd_id)
    if cd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy chiến dịch")
    if cd.trang_thai != "DA_DUYET":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nội dung chưa được duyệt — không thể gửi.")
    teps = db.query(TepDinhKem).filter_by(doi_tuong="CHIEN_DICH", doi_tuong_id=cd.id).all()
    dinh_kem = [{"ten_file": t.ten_file, "duong_dan": t.duong_dan, "content_type": t.content_type}
                for t in teps]
    q = db.query(KhachHang).filter(KhachHang.khong_nhan_email.is_(False))  # bỏ KH đã hủy nhận
    if cd.khach_hang_ids:                       # ưu tiên: danh sách KH cụ thể
        ids = [int(x) for x in cd.khach_hang_ids.split(",") if x.strip()]
        q = q.filter(KhachHang.id.in_(ids))
    elif cd.bo_loc_abc:
        q = q.filter(KhachHang.phan_loai_abc == cd.bo_loc_abc)
    provider = lay_email_provider()
    dem = {"GUI_OK": 0, "LOI": 0, "BO_QUA": 0}
    for kh in q.all():
        if not kh.email:
            db.add(EmailLog(chien_dich_id=cd.id, khach_hang_id=kh.id, email=None,
                            trang_thai="BO_QUA", ghi_chu="KH chưa có email"))
            dem["BO_QUA"] += 1; continue
        tieu_de = cd.tieu_de.replace("{ten_kh}", kh.ten)
        noi_dung = cd.noi_dung.replace("{ten_kh}", kh.ten)
        kq = provider.gui(kh.email, tieu_de, noi_dung, dinh_kem)
        db.add(EmailLog(chien_dich_id=cd.id, khach_hang_id=kh.id, email=kh.email,
                        trang_thai=kq["trang_thai"], ghi_chu=kq.get("ghi_chu")))
        db.add(LienLac(khach_hang_id=kh.id, kenh="EMAIL", huong="DI", tieu_de=tieu_de,
                       noi_dung=f"[Chiến dịch] {cd.ten}", gui_tu=settings.email_from,
                       nguoi_xu_ly=nhan_vien_id_cua(db, nd.id), trang_thai=kq["trang_thai"]))
        dem[kq["trang_thai"]] = dem.get(kq["trang_thai"], 0) + 1
    cd.trang_thai = "DA_GUI"
    ghi_audit(db, nd.id, "GUI", "chien_dich_email", cd.id, moi={**dem, "so_tep": len(dinh_kem)})
    db.commit()
    return {"chien_dich_id": cd.id, "provider": provider.ten, "gui_tu": settings.email_from,
            "so_tep_dinh_kem": len(dinh_kem), "ket_qua": dem, "trang_thai": "DA_GUI"}


@router.get("/chien-dich/{cd_id}/ket-qua")
def ket_qua_gui(cd_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    rows = db.query(EmailLog).filter_by(chien_dich_id=cd_id).order_by(EmailLog.id).all()
    return {"chien_dich_id": cd_id, "gui_tu": settings.email_from, "so_email": len(rows),
            "chi_tiet": [{"khach_hang_id": r.khach_hang_id, "email": r.email,
                          "trang_thai": r.trang_thai, "ghi_chu": r.ghi_chu} for r in rows]}


# ============ (3) LIÊN LẠC KHÁCH HÀNG — gửi email 1:1 QUA HỆ THỐNG ============
# Thay cho mail cá nhân: nhân viên gửi từ địa chỉ công ty, mọi thư đều được ghi nhật ký.
@router.post("/khach-hang/{kh_id}/gui-email")
def gui_email_kh(kh_id: int, data: GuiEmailKHVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    kh = db.get(KhachHang, kh_id)
    if kh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khách hàng")
    if not kh.email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Khách hàng chưa có email — cập nhật email trong hồ sơ trước.")
    provider = lay_email_provider()
    kq = provider.gui(kh.email, data.tieu_de, data.noi_dung, None)
    ll = LienLac(khach_hang_id=kh_id, kenh="EMAIL", huong="DI", tieu_de=data.tieu_de,
                 noi_dung=data.noi_dung, lien_quan_loai=data.lien_quan_loai,
                 lien_quan_id=data.lien_quan_id, gui_tu=settings.email_from,
                 nguoi_xu_ly=nhan_vien_id_cua(db, nd.id), trang_thai=kq["trang_thai"])
    db.add(ll); db.flush()
    ghi_audit(db, nd.id, "GUI_EMAIL", "khach_hang", kh_id,
              moi={"tieu_de": data.tieu_de, "gui_tu": settings.email_from, "trang_thai": kq["trang_thai"]})
    db.commit()
    return {"khach_hang_id": kh_id, "gui_tu": settings.email_from, "den": kh.email,
            "trang_thai": kq["trang_thai"], "lien_lac_id": ll.id}


# Ghi nhận liên lạc thủ công (cuộc gọi / gặp mặt / ghi chú) -> mọi tương tác đều ở 1 nơi
@router.post("/khach-hang/{kh_id}/lien-lac", response_model=LienLacRa, status_code=201)
def ghi_lien_lac(kh_id: int, data: GhiLienLacVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.get(KhachHang, kh_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khách hàng")
    ll = LienLac(khach_hang_id=kh_id, kenh=data.kenh, huong=data.huong, noi_dung=data.noi_dung,
                 nguoi_xu_ly=nhan_vien_id_cua(db, nd.id), trang_thai="GHI_NHAN")
    db.add(ll); db.flush()
    ghi_audit(db, nd.id, "TAO", "lien_lac", ll.id, moi={"kenh": data.kenh})
    db.commit(); db.refresh(ll)
    return ll


# Dòng thời gian liên lạc của một khách hàng
@router.get("/khach-hang/{kh_id}/lien-lac", response_model=list[LienLacRa])
def ds_lien_lac(kh_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(LienLac).filter_by(khach_hang_id=kh_id)              .order_by(LienLac.id.desc()).all()


# ============ (4) HỘP THƯ PHẢN HỒI — thu thư trả lời vào hệ thống (Giai đoạn 1) ============
def _xu_ly_thu_den(db: Session, msg: dict):
    """Tạo bản ghi liên lạc chiều NHẬN từ một thư đến; khớp KH theo email; chống trùng theo Message-ID."""
    mid = msg.get("message_id")
    if mid and db.query(LienLac).filter_by(message_id=mid).first():
        return None  # đã thu trước đó
    tu = (msg.get("tu_email") or "").strip()
    kh = db.query(KhachHang).filter(func.lower(KhachHang.email) == tu.lower()).first() if tu else None
    ll = LienLac(khach_hang_id=kh.id if kh else None, kenh="EMAIL", huong="DEN",
                 tieu_de=msg.get("tieu_de"), noi_dung=msg.get("noi_dung"),
                 tu_email=tu or None, message_id=mid, trang_thai="NHAN", da_xu_ly=False)
    db.add(ll)
    return ll


_SLA_GIO = {"CAO": 4, "TRUNG": 24, "THAP": 48}
_SALES_YDINH = {"QUAN_TAM", "HOI_KY_THUAT", "HEN_GAP"}
_ACK = ("SVWS xác nhận đã nhận được email của Quý công ty. Bộ phận phụ trách sẽ "
        "phản hồi chi tiết trong thời gian sớm nhất. Trân trọng cảm ơn.")


def _auto_ack(db: Session, ll: LienLac, kh) -> bool:
    """Tự gửi 1 email XÁC NHẬN ĐÃ NHẬN (nội dung cố định) cho nhóm ý định an toàn — nếu được bật."""
    if not (settings.auto_tra_loi and kh and kh.email and not kh.khong_nhan_email):
        return False
    an_toan = {x.strip() for x in settings.auto_tra_loi_ydinh.split(",") if x.strip()}
    if ll.ai_y_dinh not in an_toan:
        return False
    kq = lay_email_provider().gui(kh.email, "Đã nhận email của Quý công ty", _ACK, None)
    db.add(LienLac(khach_hang_id=kh.id, kenh="EMAIL", huong="DI",
                   tieu_de="Đã nhận email của Quý công ty", noi_dung=_ACK,
                   gui_tu=settings.email_from, trang_thai=kq["trang_thai"]))
    return True


def _phan_tich_xu_ly(db: Session, nd: NguoiDung, ll: LienLac, ai):
    """Phân loại 1 thư; tự xử lý hủy-nhận/vắng-mặt/spam; hoặc tạo việc(SLA) + cơ hội + nháp báo giá + tự xác nhận."""
    kq = ai.phan_loai(ll.tieu_de, ll.noi_dung)
    ll.ai_y_dinh = kq.get("y_dinh"); ll.ai_khan = kq.get("khan")
    ll.ai_tom_tat = kq.get("tom_tat"); ll.ai_tra_loi = kq.get("tra_loi")
    y = ll.ai_y_dinh
    base = {"tu_xu_ly": None, "cong_viec": None, "co_hoi": None, "bao_gia": None, "auto_ack": False}
    if y == "HUY_NHAN":
        if ll.khach_hang_id:
            kh = db.get(KhachHang, ll.khach_hang_id)
            if kh: kh.khong_nhan_email = True
        ll.da_xu_ly = True
        return {**base, "tu_xu_ly": "HUY_NHAN"}
    if y in ("VANG_MAT", "SPAM"):
        ll.da_xu_ly = True
        return {**base, "tu_xu_ly": y}
    kh = db.get(KhachHang, ll.khach_hang_id) if ll.khach_hang_id else None
    pt = kh.nguoi_phu_trach if kh else None
    # 1) Công việc kèm SLA (idempotent theo thư)
    if not db.query(CongViec).filter_by(lien_lac_id=ll.id).first():
        gio = _SLA_GIO.get(ll.ai_khan, 24)
        db.add(CongViec(lien_lac_id=ll.id, khach_hang_id=ll.khach_hang_id, loai=y,
                        tieu_de=f"[{y}] {(ll.tieu_de or '').strip()[:120]}", mo_ta=ll.ai_tom_tat,
                        nguoi_phu_trach=pt, uu_tien=ll.ai_khan or "TRUNG",
                        han_xu_ly=datetime.now(timezone.utc) + timedelta(hours=gio), trang_thai="MO"))
        base["cong_viec"] = "moi"
    else:
        base["cong_viec"] = "da_co"
    # 2) Cơ hội (pipeline) + nháp báo giá cho ý định bán hàng
    if y in _SALES_YDINH:
        ch = db.query(CoHoi).filter_by(lien_lac_id=ll.id).first()
        if not ch:
            ch = CoHoi(khach_hang_id=ll.khach_hang_id, lien_lac_id=ll.id, nguon="EMAIL",
                       tieu_de=(ll.tieu_de or "Cơ hội từ phản hồi")[:300], giai_doan="QUAN_TAM",
                       gia_tri_dk=0, nguoi_phu_trach=pt)
            db.add(ch); db.flush(); base["co_hoi"] = "moi"
            if y == "QUAN_TAM" and ll.khach_hang_id:   # nháp báo giá để NV hoàn thiện
                bg = BaoGia(so=None, khach_hang_id=ll.khach_hang_id, nguoi_tao=pt,
                            tong_tien=0, trang_thai="NHAP")
                db.add(bg); db.flush(); bg.so = f"BG-N{bg.id}"
                ch.bao_gia_id = bg.id; base["bao_gia"] = "nhap"
        else:
            base["co_hoi"] = "da_co"
    # 3) Tự gửi xác nhận đã nhận (an toàn, cấu hình)
    base["auto_ack"] = _auto_ack(db, ll, kh)
    return base


@router.post("/dong-bo-phan-hoi")
def dong_bo_phan_hoi(db: Session = Depends(get_db),
                     nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Kéo thư mới, AI phân loại, tự xử lý / giao việc(SLA) / tạo cơ hội + nháp báo giá / tự xác nhận."""
    provider = lay_inbound_provider()
    ai = lay_ai_provider()
    moi = gan = tu_xl = tao_cv = tao_ch = tao_bg = ack = 0
    for msg in provider.lay_thu_moi():
        ll = _xu_ly_thu_den(db, msg)
        if ll is None:
            continue
        moi += 1
        if ll.khach_hang_id:
            gan += 1
        db.flush()
        kq = _phan_tich_xu_ly(db, nd, ll, ai)
        tu_xl += 1 if kq["tu_xu_ly"] else 0
        tao_cv += 1 if kq["cong_viec"] == "moi" else 0
        tao_ch += 1 if kq["co_hoi"] == "moi" else 0
        tao_bg += 1 if kq["bao_gia"] == "nhap" else 0
        ack += 1 if kq["auto_ack"] else 0
    if moi:
        ghi_audit(db, nd.id, "DONG_BO", "lien_lac", 0,
                  moi={"so_thu_moi": moi, "tu_xu_ly": tu_xl, "cong_viec": tao_cv,
                       "co_hoi": tao_ch, "bao_gia": tao_bg, "auto_ack": ack})
        db.commit()
    return {"provider": provider.ten, "ai": ai.ten, "so_thu_moi": moi, "da_gan_khach": gan,
            "tu_xu_ly": tu_xl, "cong_viec_moi": tao_cv, "co_hoi_moi": tao_ch,
            "bao_gia_nhap": tao_bg, "auto_ack": ack}


@router.post("/phan-hoi/{ll_id}/phan-tich")
def phan_tich_lai(ll_id: int, db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Chạy lại phân loại AI cho 1 thư (ví dụ sau khi vừa gắn khách để giao đúng người)."""
    ll = db.get(LienLac, ll_id)
    if ll is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thư")
    kq = _phan_tich_xu_ly(db, nd, ll, lay_ai_provider())
    db.commit()
    return {"id": ll.id, "y_dinh": ll.ai_y_dinh, "khan": ll.ai_khan,
            "tom_tat": ll.ai_tom_tat, "tra_loi": ll.ai_tra_loi, **kq}


@router.get("/cong-viec")
def ds_cong_viec(cua_toi: bool = False, qua_han: bool = False, mo: bool = True,
                 db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "XEM"))):
    """Hàng đợi công việc từ thư phản hồi (kèm SLA, leo thang khi quá hạn)."""
    q = db.query(CongViec)
    if mo:
        q = q.filter(CongViec.trang_thai != "XONG")
    if cua_toi:
        q = q.filter(CongViec.nguoi_phu_trach == nhan_vien_id_cua(db, nd.id))
    now = datetime.now(timezone.utc)
    rows = q.order_by(CongViec.han_xu_ly.asc().nullslast()).limit(200).all()
    out = []
    for r in rows:
        han = r.han_xu_ly
        is_qh = bool(han and r.trang_thai != "XONG" and han < now)
        if qua_han and not is_qh:
            continue
        ten = None
        if r.khach_hang_id:
            kh = db.get(KhachHang, r.khach_hang_id)
            ten = kh.ten if kh else None
        out.append({"id": r.id, "loai": r.loai, "tieu_de": r.tieu_de, "mo_ta": r.mo_ta,
                    "khach_hang_id": r.khach_hang_id, "khach_ten": ten, "uu_tien": r.uu_tien,
                    "han_xu_ly": han, "trang_thai": r.trang_thai, "qua_han": is_qh,
                    "nguoi_phu_trach": r.nguoi_phu_trach})
    return out


@router.post("/cong-viec/{cv_id}/trang-thai")
def cap_nhat_cong_viec(cv_id: int, data: TrangThaiCVVao, db: Session = Depends(get_db),
                       nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    cv = db.get(CongViec, cv_id)
    if cv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy công việc")
    cv.trang_thai = data.trang_thai
    cv.hoan_thanh_luc = datetime.now(timezone.utc) if data.trang_thai == "XONG" else None
    ghi_audit(db, nd.id, "CAP_NHAT", "cong_viec", cv.id, moi={"trang_thai": data.trang_thai})
    db.commit()
    return {"id": cv.id, "trang_thai": cv.trang_thai}


@router.get("/phan-hoi")
def ds_phan_hoi(chua_xu_ly: bool | None = None, db: Session = Depends(get_db),
                _=Depends(yeu_cau(MODULE, "XEM"))):
    """Hộp thư phản hồi: các thư chiều NHẬN, mới nhất trước."""
    q = db.query(LienLac).filter_by(kenh="EMAIL", huong="DEN")
    if chua_xu_ly is True:
        q = q.filter(LienLac.da_xu_ly.is_(False))
    rows = q.order_by(LienLac.id.desc()).limit(200).all()
    out = []
    for r in rows:
        ten = None
        if r.khach_hang_id:
            kh = db.get(KhachHang, r.khach_hang_id)
            ten = kh.ten if kh else None
        out.append({"id": r.id, "tu_email": r.tu_email, "khach_hang_id": r.khach_hang_id,
                    "khach_ten": ten, "tieu_de": r.tieu_de, "noi_dung": r.noi_dung,
                    "da_xu_ly": r.da_xu_ly, "thoi_diem": r.thoi_diem,
                    "ai_y_dinh": r.ai_y_dinh, "ai_khan": r.ai_khan,
                    "ai_tom_tat": r.ai_tom_tat, "ai_tra_loi": r.ai_tra_loi})
    return out


@router.post("/phan-hoi/{ll_id}/gan-khach")
def gan_khach_phan_hoi(ll_id: int, data: GanKhachVao, db: Session = Depends(get_db),
                       nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Gắn một thư chưa khớp vào đúng khách hàng (đưa vào dòng thời gian của khách)."""
    ll = db.get(LienLac, ll_id)
    if ll is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thư")
    if db.get(KhachHang, data.khach_hang_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khách hàng")
    ll.khach_hang_id = data.khach_hang_id
    ghi_audit(db, nd.id, "GAN_KHACH", "lien_lac", ll.id, moi={"khach_hang_id": data.khach_hang_id})
    db.commit()
    return {"id": ll.id, "khach_hang_id": ll.khach_hang_id}


@router.post("/phan-hoi/{ll_id}/danh-dau")
def danh_dau_xu_ly(ll_id: int, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Đánh dấu thư phản hồi đã xử lý xong."""
    ll = db.get(LienLac, ll_id)
    if ll is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thư")
    ll.da_xu_ly = True
    ghi_audit(db, nd.id, "XU_LY", "lien_lac", ll.id, moi={"da_xu_ly": True})
    db.commit()
    return {"id": ll.id, "da_xu_ly": True}


# ============ (5) CƠ HỘI (PIPELINE CRM) + DASHBOARD (Giai đoạn 3) ============
_GIAI_DOAN = ["MOI", "QUAN_TAM", "BAO_GIA", "DAM_PHAN", "THANG", "THUA"]


@router.get("/co-hoi")
def ds_co_hoi(giai_doan: str | None = None, cua_toi: bool = False,
              db: Session = Depends(get_db), nd: NguoiDung = Depends(yeu_cau(MODULE, "XEM"))):
    """Danh sách cơ hội bán hàng (pipeline)."""
    q = db.query(CoHoi)
    if giai_doan:
        q = q.filter(CoHoi.giai_doan == giai_doan)
    if cua_toi:
        q = q.filter(CoHoi.nguoi_phu_trach == nhan_vien_id_cua(db, nd.id))
    out = []
    for r in q.order_by(CoHoi.updated_at.desc()).limit(300).all():
        kh = db.get(KhachHang, r.khach_hang_id) if r.khach_hang_id else None
        out.append({"id": r.id, "khach_hang_id": r.khach_hang_id,
                    "khach_ten": kh.ten if kh else None, "tieu_de": r.tieu_de,
                    "giai_doan": r.giai_doan, "gia_tri_dk": float(r.gia_tri_dk or 0),
                    "bao_gia_id": r.bao_gia_id, "don_hang_id": r.don_hang_id,
                    "nguon": r.nguon, "nguoi_phu_trach": r.nguoi_phu_trach})
    return out


@router.post("/co-hoi/{ch_id}/giai-doan")
def chuyen_giai_doan(ch_id: int, data: GiaiDoanVao, db: Session = Depends(get_db),
                     nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Chuyển cơ hội sang giai đoạn khác trong pipeline (THẮNG/THUA sẽ đóng cơ hội)."""
    ch = db.get(CoHoi, ch_id)
    if ch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy cơ hội")
    ch.giai_doan = data.giai_doan
    if data.gia_tri_dk is not None:
        ch.gia_tri_dk = data.gia_tri_dk
    if data.ly_do_thua is not None:
        ch.ly_do_thua = data.ly_do_thua
    ch.updated_at = datetime.now(timezone.utc)
    ch.closed_at = datetime.now(timezone.utc) if data.giai_doan in ("THANG", "THUA") else None
    ghi_audit(db, nd.id, "CHUYEN_GD", "co_hoi", ch.id, moi={"giai_doan": data.giai_doan})
    db.commit()
    return {"id": ch.id, "giai_doan": ch.giai_doan, "gia_tri_dk": float(ch.gia_tri_dk or 0)}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Phễu chuyển đổi (phản hồi quan tâm → cơ hội → báo giá → đơn) + chỉ số SLA công việc."""
    now = datetime.now(timezone.utc)
    ph = db.query(func.count(LienLac.id)).filter(
        LienLac.huong == "DEN", LienLac.ai_y_dinh == "QUAN_TAM").scalar() or 0
    n_ch = db.query(func.count(CoHoi.id)).scalar() or 0
    n_bg = db.query(func.count(BaoGia.id)).scalar() or 0
    n_dh = db.query(func.count(DonHang.id)).scalar() or 0
    doanh_thu = float(db.query(func.coalesce(func.sum(DonHang.tong_tien), 0)).scalar() or 0)
    cv_mo = db.query(func.count(CongViec.id)).filter(CongViec.trang_thai != "XONG").scalar() or 0
    cv_qh = db.query(func.count(CongViec.id)).filter(
        CongViec.trang_thai != "XONG", CongViec.han_xu_ly < now).scalar() or 0
    xong = db.query(CongViec.created_at, CongViec.hoan_thanh_luc, CongViec.han_xu_ly).filter(
        CongViec.trang_thai == "XONG").all()
    n_xong = len(xong); dung = 0; tong_gio = 0.0; dem = 0
    for cr, ht, han in xong:
        if ht and han and ht <= han:
            dung += 1
        if ht and cr:
            tong_gio += (ht - cr).total_seconds() / 3600; dem += 1
    gd = {k: v for k, v in db.query(CoHoi.giai_doan, func.count(CoHoi.id)).group_by(CoHoi.giai_doan).all()}
    pct = lambda a, b: round(a / b * 100, 1) if b else 0.0
    return {
        "pheu": {"phan_hoi_quan_tam": ph, "co_hoi": n_ch, "bao_gia": n_bg, "don_hang": n_dh},
        "ty_le": {"ph_to_cohoi": pct(n_ch, ph), "cohoi_to_baogia": pct(n_bg, n_ch),
                  "baogia_to_donhang": pct(n_dh, n_bg)},
        "doanh_thu_don": doanh_thu,
        "cong_viec": {"mo": cv_mo, "qua_han": cv_qh, "xong": n_xong, "dung_han": dung,
                      "ty_le_dung_han": pct(dung, n_xong), "gio_xu_ly_tb": round(tong_gio / dem, 1) if dem else 0.0},
        "co_hoi_theo_giai_doan": {g: gd.get(g, 0) for g in _GIAI_DOAN},
    }



# ============ (6) LÃI/LỖ theo mã đơn Bán hàng (liên kết Mua hàng) ============
@router.get("/don-hang/{dh_id}/lai-lo")
def lai_lo_don(dh_id: int, db: Session = Depends(get_db),
               _=Depends(yeu_cau(MODULE, "XEM"))):
    """Lãi/lỗ trên 1 mã đơn bán: doanh thu − giá vốn.
    Giá vốn THỰC NHẬN (theo SL đã nhận) và giá vốn CAM KẾT (tổng PO liên kết)."""
    dh = db.get(DonHang, dh_id)
    if dh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn hàng")
    pos = db.query(DonMua).filter(DonMua.don_hang_id == dh_id,
                                  DonMua.trang_thai != "TU_CHOI").all()
    gia_von_cam_ket = sum(float(p.tong_tien or 0) for p in pos)
    po_ids = [p.id for p in pos]
    gia_von_thuc = 0.0
    if po_ids:
        for ct in db.query(DonMuaCt).filter(DonMuaCt.don_mua_id.in_(po_ids)).all():
            gia_von_thuc += float(ct.so_luong_nhan or 0) * float(ct.don_gia or 0)
    doanh_thu = float(dh.tong_tien or 0)
    rate = lambda v: round((doanh_thu - v) / doanh_thu * 100, 1) if doanh_thu else 0.0
    return {"don_hang_id": dh.id, "so": dh.so, "doanh_thu": doanh_thu,
            "gia_von_thuc": gia_von_thuc, "gia_von_cam_ket": gia_von_cam_ket,
            "lai_lo_thuc": doanh_thu - gia_von_thuc, "lai_lo_dukien": doanh_thu - gia_von_cam_ket,
            "ty_suat_thuc": rate(gia_von_thuc), "ty_suat_dukien": rate(gia_von_cam_ket),
            "so_po": len(pos),
            "danh_sach_po": [{"id": p.id, "so": p.so, "nha_cung_cap_id": p.nha_cung_cap_id,
                              "tong_tien": float(p.tong_tien or 0), "trang_thai": p.trang_thai,
                              "trang_thai_nhan": p.trang_thai_nhan} for p in pos]}
