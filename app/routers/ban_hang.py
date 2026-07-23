"""
Module BÁN HÀNG — lát cắt dọc thứ tư, minh họa LIÊN THÔNG rõ nhất:
  báo giá -> duyệt (han_muc 'bao_gia') -> đơn hàng -> XUẤT KHO (gọi kho_service)
  -> lập HÓA ĐƠN (BAN) + CÔNG NỢ (PHẢI THU) [bàn giao Kế toán].
"""
from decimal import Decimal
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..database import get_db
from ..rbac import yeu_cau, kiem_han_muc, chi_vai_tro
from ..deps import nhan_vien_id_cua
from ..audit import ghi_audit
from ..kho_service import xuat_ton
from ..models import (NguoiDung, KhachHang, HangHoa, BaoGia, BaoGiaCt, BaoGiaForm,
                      DonHang, DonHangCt, PhieuKho, PhieuKhoCt, HoaDon, CongNo, TonKho)
from ..schemas import (KhachHangVao, KhachHangSua, KhachHangRa, BaoGiaVao, BaoGiaRa,
                       BaoGiaFormVao, BaoGiaFormRa, DonHangRa)

router = APIRouter(prefix="/ban-hang", tags=["ban_hang"])
MODULE = "ban_hang"
LOAI_DUYET = "bao_gia"   # khớp seed han_muc_duyet (TP_KD 100tr · CEO vô hạn)
THUE_SUAT = Decimal("0.08")


# ----- Khách hàng -----
def _lien_he_phu_sach(ds):
    """Chuẩn hóa danh sách người liên hệ phụ → list[dict], bỏ dòng trống hoàn toàn."""
    out = []
    for lh in (ds or []):
        d = lh.model_dump() if hasattr(lh, "model_dump") else dict(lh)
        ten = (d.get("ten") or "").strip()
        email = (d.get("email") or "").strip()
        dt = (d.get("dien_thoai") or "").strip()
        if ten or email or dt:
            out.append({"ten": ten or None, "email": email or None, "dien_thoai": dt or None})
    return out


@router.get("/khach-hang", response_model=list[KhachHangRa])
def ds_kh(q: str | None = None, db: Session = Depends(get_db),
          _=Depends(yeu_cau(MODULE, "XEM"))):
    qr = db.query(KhachHang)
    if q:
        like = f"%{q.strip()}%"
        qr = qr.filter(KhachHang.ten.ilike(like))
    return qr.order_by(KhachHang.ten).limit(50).all()


@router.post("/khach-hang", response_model=KhachHangRa, status_code=201)
def tao_kh(data: KhachHangVao, db: Session = Depends(get_db),
           nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    phu = _lien_he_phu_sach(data.lien_he_phu)
    kh = KhachHang(ma=data.ma, ten=data.ten, ma_so_thue=data.ma_so_thue,
                   dien_thoai=data.dien_thoai, nguoi_lien_he=data.nguoi_lien_he,
                   email=data.email, phan_loai_abc=data.phan_loai_abc,
                   lien_he_phu=phu, nguoi_phu_trach=nhan_vien_id_cua(db, nd.id))
    db.add(kh); db.flush()
    ghi_audit(db, nd.id, "TAO", "khach_hang", kh.id, moi={"ten": data.ten})
    db.commit(); db.refresh(kh)
    return kh


@router.patch("/khach-hang/{kh_id}", response_model=KhachHangRa)
def sua_kh(kh_id: int, data: KhachHangSua, db: Session = Depends(get_db),
           nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    kh = db.get(KhachHang, kh_id)
    if kh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khách hàng")
    doi = data.model_dump(exclude_unset=True)
    if not doi:
        return kh
    if "lien_he_phu" in doi:
        doi["lien_he_phu"] = _lien_he_phu_sach(data.lien_he_phu)
    if "ma" in doi and doi["ma"]:
        trung = db.query(KhachHang).filter(KhachHang.ma == doi["ma"],
                                           KhachHang.id != kh.id).first()
        if trung:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Mã '{doi['ma']}' đã dùng cho khách khác")
    cu = {t: getattr(kh, t) for t in doi}
    for t, v in doi.items():
        setattr(kh, t, v)
    ghi_audit(db, nd.id, "SUA", "khach_hang", kh.id, cu=cu, moi=doi)
    db.commit(); db.refresh(kh)
    return kh


@router.delete("/khach-hang/{kh_id}")
def xoa_kh(kh_id: int, db: Session = Depends(get_db),
           nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """Xóa khách hàng CHƯA có chứng từ thật. Báo giá nháp / nhật ký email /
    CRM tự gỡ theo; báo giá chính thức, đơn hàng, công nợ, dự án... thì chặn
    và trả lỗi liệt kê rõ đang vướng gì."""
    from sqlalchemy import text as _sql
    kh = db.get(KhachHang, kh_id)
    if kh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khách hàng")
    ten_cu, ma_cu = kh.ten, kh.ma
    refs = [("báo giá", "bao_gia"), ("đơn hàng", "don_hang"), ("công nợ", "cong_no"),
            ("dự án", "du_an"), ("hợp đồng thuê", "hop_dong_thue"),
            ("phiếu thu/chi", "phieu_thu_chi"), ("tài sản cho thuê", "tai_san_cho_thue")]
    ban = []
    for ten_ref, bang in refs:
        try:
            n = db.execute(_sql(f"SELECT COUNT(*) FROM {bang} WHERE khach_hang_id = :i"),
                           {"i": kh_id}).scalar() or 0
        except Exception:
            n = 0
        if n:
            ban.append(f"{n} {ten_ref}")
    if ban:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Khách '{ten_cu}' đang gắn với {', '.join(ban)} — không thể xóa để giữ vết kế toán. "
            "Chỉ xóa được khách chưa phát sinh chứng từ.")
    try:
        db.delete(kh)
        db.flush()
        ghi_audit(db, nd.id, "XOA", "khach_hang", kh_id,
                  cu={"ten": ten_cu, "ma": ma_cu})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Khách '{ten_cu}' còn dữ liệu liên kết ở phân hệ khác nên không thể xóa.")
    return {"ok": True, "ten": ten_cu}


# ----- CÔNG NỢ KHÁCH HÀNG (sales theo dõi thu hồi) -----
@router.get("/don-hang-co-po")
def ds_don_hang_co_po(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Đơn hàng bán ĐÃ CÓ tệp PO khách / hợp đồng đính kèm — nguồn cho droplist
    Mã đơn hàng ở tab Công nợ (khớp bảng 'Danh sách đơn hàng bán đã có PO/HĐ')."""
    from ..models import TepDinhKem
    ids = {t.doi_tuong_id for t in db.query(TepDinhKem)
           .filter(TepDinhKem.doi_tuong == "DON_HANG",
                   TepDinhKem.loai.in_(["PO", "HOP_DONG"])).all()}
    if not ids:
        return []
    out = []
    for o in (db.query(DonHang).filter(DonHang.id.in_(ids))
                .order_by(DonHang.id.desc()).all()):
        kh = db.get(KhachHang, o.khach_hang_id) if o.khach_hang_id else None
        out.append({"id": o.id, "so": o.so or f"DH-{o.id}",
                    "khach_ten": kh.ten if kh else None,
                    "ngay": str(o.ngay) if o.ngay else None,
                    "tong_tien": float(o.tong_tien or 0)})
    return out


@router.get("/cong-no-khach")
def ds_cong_no_khach(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Công nợ PHẢI THU của khách — cho sales theo dõi: ngày, mã hàng bán, khách,
    đã thanh toán, còn lại, ngày TT tiếp theo, ghi chú. Kèm cờ nhắc khi còn ≤7 ngày."""
    hom_nay = date.today()
    rows = (db.query(CongNo).filter(CongNo.loai == "PHAI_THU")
              .order_by(CongNo.id.desc()).limit(300).all())
    out = []
    for cn in rows:
        con_lai = float((cn.so_tien or 0) - (cn.da_thanh_toan or 0))
        if con_lai <= 0:
            continue                      # đã thu đủ thì không cần theo dõi
        hd = db.get(HoaDon, cn.hoa_don_id) if cn.hoa_don_id else None
        # Mã đơn hàng: ưu tiên đơn hàng sales đã gắn, nếu trống thì theo hóa đơn gốc
        dh_id = cn.don_hang_id or (hd.don_hang_id if hd else None)
        dh = db.get(DonHang, dh_id) if dh_id else None
        # Khách hàng lấy theo ĐƠN HÀNG (nguồn duy nhất), thiếu mới lùi về công nợ/hóa đơn
        kh_id = (dh.khach_hang_id if dh else None) or cn.khach_hang_id or (hd.khach_hang_id if hd else None)
        kh = db.get(KhachHang, kh_id) if kh_id else None
        moc = cn.ngay_tt_tiep or cn.han   # mốc nhắc: ưu tiên ngày TT tiếp theo
        con_ngay = (moc - hom_nay).days if moc else None
        out.append({
            "id": cn.id,
            "ngay": str(hd.ngay) if (hd and hd.ngay) else (str(dh.ngay) if (dh and dh.ngay) else None),
            "ma_ban": (dh.so if dh else None) or (f"DH-{dh.id}" if dh else None),
            "don_hang_id": dh.id if dh else None,
            "khach_ten": kh.ten if kh else None,
            "dien_giai": (hd.dien_giai if hd else None) or cn.ghi_chu,
            # Giá trị đơn hàng: lấy từ tab Đơn hàng & PO/Hợp đồng (thiếu đơn thì dùng công nợ)
            "gia_tri_don": float(dh.tong_tien or 0) if dh else None,
            # Tách VAT theo hóa đơn của khoản công nợ (chưa VAT / VAT / tổng)
            "tien_truoc_thue": float(hd.tien_truoc_thue or 0) if hd else float(cn.so_tien or 0),
            "tien_thue": float(hd.tien_thue or 0) if hd else 0,
            "tong": float(hd.tong_tien or 0) if hd else float(cn.so_tien or 0),
            "so_tien": float(cn.so_tien or 0),
            "da_thanh_toan": float(cn.da_thanh_toan or 0),
            "con_lai": con_lai,
            "han": str(cn.han) if cn.han else None,
            "ngay_tt_tiep": str(cn.ngay_tt_tiep) if cn.ngay_tt_tiep else None,
            "ghi_chu": cn.ghi_chu,
            "trang_thai": cn.trang_thai,
            "con_ngay": con_ngay,
            "qua_han": bool(moc and con_ngay is not None and con_ngay < 0),
            "sap_den_han": bool(moc and con_ngay is not None and 0 <= con_ngay <= 7),
        })
    out.sort(key=lambda x: (x["ngay_tt_tiep"] or x["han"] or "9999-12-31"))
    return out


from pydantic import BaseModel as _CNBase


class TaoCongNoVao(_CNBase):
    don_hang_id: int
    tien_truoc_thue: Decimal
    thue_suat: Decimal = Decimal(8)
    ngay_thanh_toan: date | None = None   # ngày của đợt thanh toán này
    so_tien: Decimal = Decimal(0)         # số tiền khách trả đợt này (0 = chỉ mở công nợ)
    ngay_tt_tiep: date | None = None
    ghi_chu: str | None = None


def _cong_no_cua_don(db: Session, dh_id: int):
    """Khoản phải thu của một đơn hàng (gắn trực tiếp hoặc qua hóa đơn bán)."""
    from sqlalchemy import or_ as _or
    hd_ids = [h.id for h in db.query(HoaDon).filter_by(don_hang_id=dh_id, loai="BAN").all()]
    dk = [CongNo.don_hang_id == dh_id]
    if hd_ids:
        dk.append(CongNo.hoa_don_id.in_(hd_ids))
    return (db.query(CongNo).filter(CongNo.loai == "PHAI_THU", _or(*dk))
              .order_by(CongNo.id.desc()).first())


@router.post("/cong-no", status_code=201)
def tao_cong_no_khach(data: TaoCongNoVao, db: Session = Depends(get_db),
                      nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Ghi nhận thanh toán theo ĐỢT cho một đơn hàng. Mỗi đơn chỉ MỘT khoản phải thu:
    lần đầu tạo công nợ (kèm hóa đơn bán nháp), các lần sau cộng dồn vào chính khoản đó."""
    from ..models import ThanhToan
    from ..hach_toan import hach_toan_thu_tien
    dh = db.get(DonHang, data.don_hang_id)
    if dh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn hàng bán")
    cn = _cong_no_cua_don(db, dh.id)
    hd_id = cn.hoa_don_id if cn else None
    if cn is None:                       # lần đầu: mở công nợ + hóa đơn bán nháp
        if data.tien_truoc_thue <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Giá trị chưa VAT phải lớn hơn 0")
        truoc = Decimal(data.tien_truoc_thue)
        thue = (truoc * Decimal(data.thue_suat or 0) / 100).quantize(Decimal("1"))
        tong = truoc + thue
        hd = HoaDon(loai="BAN", don_hang_id=dh.id, khach_hang_id=dh.khach_hang_id,
                    ngay=date.today(), tien_truoc_thue=truoc, tien_thue=thue, tong_tien=tong,
                    hddt_trang_thai="CHUA_PHAT_HANH", da_hach_toan=False, trang_thai="GHI_NHAN",
                    dien_giai=f"Công nợ đơn {dh.so or dh.id}")
        db.add(hd); db.flush()
        hd.so = f"HDB-{date.today():%Y%m%d}-{hd.id}"; hd_id = hd.id
        cn = CongNo(loai="PHAI_THU", hoa_don_id=hd.id, khach_hang_id=dh.khach_hang_id,
                    don_hang_id=dh.id, so_tien=tong, da_thanh_toan=0,
                    han=data.ngay_tt_tiep or (date.today() + timedelta(days=30)),
                    trang_thai="CHUA_THU")
        db.add(cn); db.flush()
    # ghi nhận đợt thanh toán (nếu có)
    tt = Decimal(data.so_tien or 0)
    if tt > 0:
        con_lai = Decimal(cn.so_tien) - Decimal(cn.da_thanh_toan)
        if tt > con_lai:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Số tiền {tt:,.0f} vượt số còn lại {con_lai:,.0f} của đơn này")
        db.add(ThanhToan(cong_no_id=cn.id, so_tien=tt,
                         ngay=data.ngay_thanh_toan or date.today(), hinh_thuc="CK"))
        cn.da_thanh_toan = Decimal(cn.da_thanh_toan) + tt
        cn.trang_thai = "THU_DU" if cn.da_thanh_toan >= cn.so_tien else "THU_MOT_PHAN"
        hach_toan_thu_tien(db, cn, tt, tien_mat=False)   # Nợ 112 / Có 131
    if data.ngay_tt_tiep is not None:
        cn.ngay_tt_tiep = data.ngay_tt_tiep
    if data.ghi_chu is not None:
        cn.ghi_chu = (data.ghi_chu or "").strip() or None
    ghi_audit(db, nd.id, "THANH_TOAN" if tt > 0 else "TAO", "cong_no", cn.id,
              moi={"don_hang_id": dh.id, "hoa_don_id": hd_id, "so_tien_dot": float(tt),
                   "da_thanh_toan": float(cn.da_thanh_toan), "trang_thai": cn.trang_thai})
    db.commit()
    return {"id": cn.id, "hoa_don_id": hd_id, "so_tien": float(cn.so_tien),
            "da_thanh_toan": float(cn.da_thanh_toan),
            "con_lai": float(Decimal(cn.so_tien) - Decimal(cn.da_thanh_toan)),
            "trang_thai": cn.trang_thai}


# ===================== AI UPLOAD CÔNG NỢ (chỉ CEO/ADMIN) =====================
def _match_khach(db: Session, ten: str):
    """Khớp khách hàng theo tên (không phân biệt hoa thường, đã trim)."""
    t = (ten or "").strip()
    if not t:
        return None
    from sqlalchemy import func as _f
    return db.query(KhachHang).filter(_f.lower(KhachHang.ten) == t.lower()).first()


@router.post("/cong-no/ai-doc")
async def ai_doc_cong_no(file: UploadFile = File(...), db: Session = Depends(get_db),
                         nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """AI đọc file Excel/CSV/Sheet công nợ, tự dò cột, trả về BẢN XEM TRƯỚC (chưa lưu)."""
    from ..ai_gateway import doc_cong_no_file
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File trống")
    rows = doc_cong_no_file(data, file.content_type, file.filename)
    for r in rows:
        kh = _match_khach(db, r.get("khach_hang"))
        r["khach_hang_id"] = kh.id if kh else None
        r["khop_kh"] = bool(kh)
    return {"so_dong": len(rows), "rows": rows,
            "so_khop": sum(1 for r in rows if r["khop_kh"])}


class AiNhapCongNoVao(_CNBase):
    rows: list[dict]


@router.post("/cong-no/ai-nhap")
def ai_nhap_cong_no(data: AiNhapCongNoVao, db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """Nhập các dòng công nợ đã xác nhận thành CongNo PHẢI THU (khớp/tạo khách hàng)."""
    tao = 0
    for r in data.rows:
        ten = str(r.get("khach_hang") or "").strip()
        st = Decimal(str(_int0(r.get("so_tien"))))
        if st <= 0:
            continue
        kh_id = r.get("khach_hang_id")
        if not kh_id and ten:
            kh = _match_khach(db, ten)
            if kh is None:
                kh = KhachHang(ten=ten[:200])
                db.add(kh); db.flush()
            kh_id = kh.id
        dtt = Decimal(str(_int0(r.get("da_thanh_toan"))))
        if dtt > st:
            dtt = st
        han = None
        h = str(r.get("han") or "").strip()
        if h:
            try:
                han = date.fromisoformat(h)
            except Exception:
                han = None
        gc = []
        if r.get("so_hoa_don"):
            gc.append("HĐ " + str(r["so_hoa_don"]).strip())
        if r.get("dien_giai"):
            gc.append(str(r["dien_giai"]).strip())
        ghi_chu = (" · ".join(gc))[:300] or None
        tt = "THU_DU" if dtt >= st else ("THU_MOT_PHAN" if dtt > 0 else "CHUA_THU")
        db.add(CongNo(loai="PHAI_THU", khach_hang_id=kh_id, so_tien=st, da_thanh_toan=dtt,
                      han=han, trang_thai=tt, ghi_chu=ghi_chu))
        tao += 1
    ghi_audit(db, nd.id, "TAO", "cong_no", 0, moi={"ai_upload_so_dong": tao})
    db.commit()
    return {"da_tao": tao}


def _int0(x) -> int:
    try:
        return int(round(float(x)))
    except Exception:
        return 0


class TheoDoiCongNoVao(_CNBase):
    ngay_tt_tiep: date | None = None
    ghi_chu: str | None = None
    don_hang_id: int | None = None
    doi_don_hang: bool = False          # True = áp dụng don_hang_id (kể cả gỡ về None)


@router.put("/cong-no/{cn_id}/theo-doi")
def cap_nhat_theo_doi_cong_no(cn_id: int, data: TheoDoiCongNoVao, db: Session = Depends(get_db),
                              nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Sales cập nhật ngày thanh toán tiếp theo, ghi chú và mã đơn hàng bán gắn kèm."""
    cn = db.get(CongNo, cn_id)
    if cn is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy công nợ")
    if cn.loai != "PHAI_THU":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Chỉ theo dõi được công nợ phải thu của khách hàng")
    cu = {"ngay_tt_tiep": str(cn.ngay_tt_tiep) if cn.ngay_tt_tiep else None,
          "ghi_chu": cn.ghi_chu, "don_hang_id": cn.don_hang_id}
    cn.ngay_tt_tiep = data.ngay_tt_tiep
    cn.ghi_chu = (data.ghi_chu or "").strip() or None
    if data.doi_don_hang:
        if data.don_hang_id and db.get(DonHang, data.don_hang_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn hàng bán")
        cn.don_hang_id = data.don_hang_id
    ghi_audit(db, nd.id, "CAP_NHAT", "cong_no", cn.id, cu=cu,
              moi={"ngay_tt_tiep": str(cn.ngay_tt_tiep) if cn.ngay_tt_tiep else None,
                   "ghi_chu": cn.ghi_chu, "don_hang_id": cn.don_hang_id})
    db.commit()
    return {"id": cn.id, "ngay_tt_tiep": str(cn.ngay_tt_tiep) if cn.ngay_tt_tiep else None,
            "ghi_chu": cn.ghi_chu, "don_hang_id": cn.don_hang_id}


@router.get("/cong-no/{cn_id}/dot-thanh-toan")
def ds_dot_thu(cn_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Lịch sử các đợt khách đã thanh toán cho một khoản phải thu."""
    from ..models import ThanhToan
    rows = (db.query(ThanhToan).filter_by(cong_no_id=cn_id)
              .order_by(ThanhToan.ngay, ThanhToan.id).all())
    return [{"id": r.id, "ngay": str(r.ngay) if r.ngay else None,
             "so_tien": float(r.so_tien or 0), "hinh_thuc": r.hinh_thuc} for r in rows]


class ThuDotVao(_CNBase):
    so_tien: Decimal = Decimal(0)
    ngay_thanh_toan: date | None = None
    ngay_tt_tiep: date | None = None
    ghi_chu: str | None = None


def _bt_dieu_chinh_thu(db: Session, cn, delta: Decimal, ly_do: str):
    """Bút toán điều chỉnh khi sửa/xóa đợt thu: tăng → Nợ112/Có131, giảm → đảo lại."""
    from ..models import ButToan
    from ..hach_toan import TK
    if delta > 0:
        db.add(ButToan(tk_no=TK["TIEN_NH"], tk_co=TK["PHAI_THU"], so_tien=delta,
                       hoa_don_id=cn.hoa_don_id, dien_giai=f"{ly_do} (tăng) công nợ {cn.id}"))
    elif delta < 0:
        db.add(ButToan(tk_no=TK["PHAI_THU"], tk_co=TK["TIEN_NH"], so_tien=-delta,
                       hoa_don_id=cn.hoa_don_id, dien_giai=f"{ly_do} (giảm) công nợ {cn.id}"))


def _cap_nhat_tt_cong_no(cn, da: Decimal):
    cn.da_thanh_toan = da
    cn.trang_thai = "THU_DU" if da >= Decimal(cn.so_tien or 0) else ("THU_MOT_PHAN" if da > 0 else "CHUA_THU")


@router.post("/cong-no/{cn_id}/thu-dot")
def thu_dot_cong_no(cn_id: int, data: ThuDotVao, db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Ghi nhận MỘT ĐỢT khách thanh toán cho khoản phải thu (lưu lại thành 1 dòng lịch sử)."""
    from ..models import ThanhToan
    from ..hach_toan import hach_toan_thu_tien
    cn = db.get(CongNo, cn_id)
    if cn is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy công nợ")
    if cn.loai != "PHAI_THU":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Công nợ này không phải khoản phải thu")
    tt = Decimal(data.so_tien or 0)
    if tt < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Số tiền không hợp lệ")
    if tt > 0:
        con_lai = Decimal(cn.so_tien or 0) - Decimal(cn.da_thanh_toan or 0)
        if tt > con_lai:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Số tiền {tt:,.0f} vượt số còn lại {con_lai:,.0f}")
        db.add(ThanhToan(cong_no_id=cn.id, so_tien=tt,
                         ngay=data.ngay_thanh_toan or date.today(), hinh_thuc="CK"))
        _cap_nhat_tt_cong_no(cn, Decimal(cn.da_thanh_toan or 0) + tt)
        hach_toan_thu_tien(db, cn, tt, tien_mat=False)   # Nợ 112 / Có 131
    if data.ngay_tt_tiep is not None:
        cn.ngay_tt_tiep = data.ngay_tt_tiep
    if data.ghi_chu is not None:
        cn.ghi_chu = (data.ghi_chu or "").strip() or None
    ghi_audit(db, nd.id, "THU_TIEN" if tt > 0 else "CAP_NHAT", "cong_no", cn.id,
              moi={"so_tien_dot": float(tt), "da_thanh_toan": float(cn.da_thanh_toan),
                   "trang_thai": cn.trang_thai})
    db.commit()
    return {"id": cn.id, "da_thanh_toan": float(cn.da_thanh_toan),
            "con_lai": float(Decimal(cn.so_tien or 0) - Decimal(cn.da_thanh_toan or 0)),
            "trang_thai": cn.trang_thai}


class SuaDotThuVao(_CNBase):
    ngay: date | None = None
    so_tien: Decimal | None = None


@router.put("/dot-thu/{tt_id}")
def sua_dot_thu(tt_id: int, data: SuaDotThuVao, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """Sửa một đợt thu đã ghi (ghi nhầm) — chỉ CEO/ADMIN. Sinh bút toán điều chỉnh."""
    from ..models import ThanhToan
    t = db.get(ThanhToan, tt_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đợt thanh toán")
    cn = db.get(CongNo, t.cong_no_id)
    if cn is None or cn.loai != "PHAI_THU":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Đợt này không thuộc công nợ phải thu")
    cu = {"ngay": str(t.ngay) if t.ngay else None, "so_tien": float(t.so_tien or 0)}
    moi_tien = Decimal(data.so_tien) if data.so_tien is not None else Decimal(t.so_tien or 0)
    if moi_tien < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Số tiền không hợp lệ")
    delta = moi_tien - Decimal(t.so_tien or 0)
    da = Decimal(cn.da_thanh_toan or 0) + delta
    if da < 0 or da > Decimal(cn.so_tien or 0):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Sửa xong tổng đã thu ({da:,.0f}) phải nằm trong 0–{float(cn.so_tien or 0):,.0f}")
    if data.ngay is not None:
        t.ngay = data.ngay
    t.so_tien = moi_tien
    _cap_nhat_tt_cong_no(cn, da)
    _bt_dieu_chinh_thu(db, cn, delta, "Sửa đợt thu")
    ghi_audit(db, nd.id, "SUA_DOT_THU", "cong_no", cn.id, cu=cu,
              moi={"dot_id": t.id, "so_tien": float(moi_tien), "da_thanh_toan": float(da)})
    db.commit()
    return {"ok": True, "da_thanh_toan": float(da),
            "con_lai": float(Decimal(cn.so_tien or 0) - da)}


@router.delete("/dot-thu/{tt_id}")
def xoa_dot_thu(tt_id: int, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """Xóa một đợt thu ghi nhầm — chỉ CEO/ADMIN. Sinh bút toán đảo tương ứng."""
    from ..models import ThanhToan
    t = db.get(ThanhToan, tt_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đợt thanh toán")
    cn = db.get(CongNo, t.cong_no_id)
    if cn is None or cn.loai != "PHAI_THU":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Đợt này không thuộc công nợ phải thu")
    cu = {"ngay": str(t.ngay) if t.ngay else None, "so_tien": float(t.so_tien or 0)}
    da = Decimal(cn.da_thanh_toan or 0) - Decimal(t.so_tien or 0)
    if da < 0:
        da = Decimal(0)
    _bt_dieu_chinh_thu(db, cn, -Decimal(t.so_tien or 0), "Xóa đợt thu")
    db.delete(t)
    db.flush()
    _cap_nhat_tt_cong_no(cn, da)
    ghi_audit(db, nd.id, "XOA_DOT_THU", "cong_no", cn.id, cu=cu,
              moi={"da_thanh_toan": float(da)})
    db.commit()
    return {"da_xoa": True, "da_thanh_toan": float(da),
            "con_lai": float(Decimal(cn.so_tien or 0) - da)}


@router.delete("/cong-no/{cn_id}")
def xoa_cong_no_khach(cn_id: int, db: Session = Depends(get_db),
                      nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """Xóa công nợ phải thu ghi nhầm. Chặn khi đã có tiền thu thật hoặc công nợ
    sinh từ hóa đơn bán (phải hủy hóa đơn ở Kế toán để gỡ kèm) — giữ vết kế toán."""
    from ..models import ThanhToan, PhieuThuChi
    cn = db.get(CongNo, cn_id)
    if cn is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy công nợ")
    if cn.loai != "PHAI_THU":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Công nợ này không phải khoản phải thu")
    co_tien = (float(cn.da_thanh_toan or 0) > 0
               or db.query(ThanhToan).filter_by(cong_no_id=cn.id).first() is not None
               or db.query(PhieuThuChi).filter_by(cong_no_id=cn.id).first() is not None)
    if co_tien:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Công nợ này đã có tiền thu thật (lần thu đã ghi / phiếu thu gắn kèm) "
                            "— không thể xóa để giữ vết kế toán.")
    if cn.hoa_don_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Công nợ này sinh từ hóa đơn bán — hãy xóa/hủy hóa đơn đó ở mục "
                            "Kế toán → Hóa đơn, công nợ sẽ được gỡ kèm theo.")
    ghi_audit(db, nd.id, "XOA", "cong_no", cn.id,
              cu={"loai": cn.loai, "khach_hang_id": cn.khach_hang_id,
                  "so_tien": float(cn.so_tien or 0),
                  "han": str(cn.han) if cn.han else None})
    db.delete(cn)
    db.commit()
    return {"da_xoa": True}


# ----- Dịch nội dung hợp đồng VN -> EN (AI) -----
from pydantic import BaseModel as _BM
from ..ai_gateway import dich_vn_sang_en


class DichVao(_BM):
    texts: list[str]


@router.post("/hop-dong/dich")
def dich_hop_dong(p: DichVao, nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if not p.texts:
        return {"texts": []}
    if len(p.texts) > 40 or sum(len(t) for t in p.texts) > 30000:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nội dung quá dài để dịch một lần.")
    kq = dich_vn_sang_en(p.texts)
    if kq is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Máy chủ chưa cấu hình ANTHROPIC_API_KEY nên không dịch tự động được. "
                            "Thêm biến môi trường này trong Render → svws-app → Environment.")
    return {"texts": kq}


# ----- DUYET: xóa đơn hàng (chỉ đơn chưa phát sinh kho/kế toán) -----
@router.delete("/don-hang/{dh_id}")
def xoa_don_hang(dh_id: int, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """Xóa đơn hàng cùng dòng hàng và tệp đính kèm. Chặn khi đơn đã xuất kho,
    có hóa đơn, phiếu thu/chi hoặc bút toán liên quan (giữ vết kế toán)."""
    from sqlalchemy import text as _sql
    from sqlalchemy.exc import IntegrityError
    from ..models import TepDinhKem
    from ..luu_tru import xoa as _xoa_tep
    dh = db.get(DonHang, dh_id)
    if dh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn hàng")
    refs = [("phiếu kho (đã xuất hàng)", "phieu_kho"), ("hóa đơn", "hoa_don"),
            ("phiếu thu/chi", "phieu_thu_chi"), ("bút toán", "but_toan")]
    ban = []
    for ten_ref, bang in refs:
        try:
            n = db.execute(_sql(f"SELECT COUNT(*) FROM {bang} WHERE don_hang_id = :i"),
                           {"i": dh_id}).scalar() or 0
        except Exception:
            n = 0
        if n:
            ban.append(f"{n} {ten_ref}")
    if ban:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Đơn hàng '{dh.so or dh_id}' đang gắn với {', '.join(ban)} — không thể xóa để giữ vết kế toán.")
    so_cu = dh.so
    teps = db.query(TepDinhKem).filter_by(doi_tuong="DON_HANG", doi_tuong_id=dh_id).all()
    for t in teps:
        _xoa_tep(t.duong_dan)
        db.delete(t)
    try:
        db.delete(dh)
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Đơn hàng '{so_cu}' còn dữ liệu liên kết ở phân hệ khác nên không thể xóa.")
    ghi_audit(db, nd.id, "XOA", "don_hang", dh_id, cu={"so": so_cu, "so_tep": len(teps)})
    db.commit()
    return {"ok": True, "so": so_cu}


# ----- Báo giá soạn theo mẫu (lưu tạm & xuất PDF) -----
@router.get("/bao-gia-form", response_model=list[BaoGiaFormRa])
def ds_bao_gia_form(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(BaoGiaForm).order_by(BaoGiaForm.id.desc()).limit(200).all()


@router.post("/bao-gia-form", response_model=BaoGiaFormRa, status_code=201)
def tao_bao_gia_form(data: BaoGiaFormVao, db: Session = Depends(get_db),
                     nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    bgf = BaoGiaForm(so=data.so, khach_hang_id=data.khach_hang_id,
                     noi_dung=data.noi_dung, trang_thai=data.trang_thai or "NHAP",
                     nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(bgf); db.flush()
    ghi_audit(db, nd.id, "TAO", "bao_gia_form", bgf.id, moi={"so": data.so})
    db.commit(); db.refresh(bgf)
    return bgf


@router.patch("/bao-gia-form/{bgf_id}", response_model=BaoGiaFormRa)
def sua_bao_gia_form(bgf_id: int, data: BaoGiaFormVao, db: Session = Depends(get_db),
                     nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    bgf = db.get(BaoGiaForm, bgf_id)
    if bgf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá nháp")
    bgf.so = data.so
    bgf.khach_hang_id = data.khach_hang_id
    bgf.noi_dung = data.noi_dung
    if data.trang_thai:
        bgf.trang_thai = data.trang_thai
    # Sửa lại nội dung (lưu về nháp/xuất PDF) => HỦY phê duyệt cũ, phải trình duyệt lại
    if (data.trang_thai or "") in ("NHAP", "DA_XUAT", ""):
        bgf.nguoi_duyet = None
        bgf.ly_do_tu_choi = None
        if bgf.trang_thai in ("DA_DUYET", "CHO_DUYET"):
            bgf.trang_thai = "NHAP"
    ghi_audit(db, nd.id, "SUA", "bao_gia_form", bgf.id, moi={"so": data.so})
    db.commit(); db.refresh(bgf)
    return bgf


def _bgf_tong(bgf: "BaoGiaForm") -> Decimal:
    from ..bao_gia_pdf import tinh_bao_gia
    try:
        _s, _v, tong = tinh_bao_gia(bgf.noi_dung or {})
        return Decimal(str(round(tong)))
    except Exception:
        return Decimal(0)


@router.post("/bao-gia-form/{bgf_id}/trinh-duyet", response_model=BaoGiaFormRa)
def trinh_duyet_bao_gia_form(bgf_id: int, db: Session = Depends(get_db),
                             nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Người soạn TRÌNH DUYỆT báo giá gửi khách — vào hàng chờ duyệt."""
    bgf = db.get(BaoGiaForm, bgf_id)
    if bgf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá")
    if bgf.trang_thai not in ("NHAP", "DA_XUAT", "TU_CHOI"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Báo giá đang ở trạng thái {bgf.trang_thai} — không trình duyệt được.")
    bgf.trang_thai = "CHO_DUYET"
    bgf.ly_do_tu_choi = None
    ghi_audit(db, nd.id, "TRINH_DUYET", "bao_gia_form", bgf.id, moi={"trang_thai": "CHO_DUYET"})
    db.commit(); db.refresh(bgf)
    return bgf


@router.post("/bao-gia-form/{bgf_id}/duyet", response_model=BaoGiaFormRa)
def duyet_bao_gia_form(bgf_id: int, db: Session = Depends(get_db),
                       nd: NguoiDung = Depends(yeu_cau(MODULE, "XEM"))):
    """DUYỆT báo giá gửi khách — thẩm quyền theo hạn mức (như báo giá nội bộ)."""
    bgf = db.get(BaoGiaForm, bgf_id)
    if bgf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá")
    if bgf.trang_thai != "CHO_DUYET":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Báo giá đang ở {bgf.trang_thai} — chỉ duyệt được khi đang chờ duyệt.")
    kiem_han_muc(db, nd, LOAI_DUYET, _bgf_tong(bgf))
    bgf.trang_thai = "DA_DUYET"
    bgf.nguoi_duyet = nhan_vien_id_cua(db, nd.id)
    bgf.ly_do_tu_choi = None
    ghi_audit(db, nd.id, "DUYET", "bao_gia_form", bgf.id, moi={"trang_thai": "DA_DUYET"})
    db.commit(); db.refresh(bgf)
    return bgf


class TuChoiBgfVao(_BM):
    ly_do: str | None = None


@router.post("/bao-gia-form/{bgf_id}/tu-choi", response_model=BaoGiaFormRa)
def tu_choi_bao_gia_form(bgf_id: int, data: TuChoiBgfVao = TuChoiBgfVao(),
                         db: Session = Depends(get_db),
                         nd: NguoiDung = Depends(yeu_cau(MODULE, "XEM"))):
    """TỪ CHỐI báo giá gửi khách — quay lại để người soạn sửa & trình lại."""
    bgf = db.get(BaoGiaForm, bgf_id)
    if bgf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá")
    if bgf.trang_thai != "CHO_DUYET":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Báo giá đang ở {bgf.trang_thai} — chỉ từ chối được khi đang chờ duyệt.")
    # người từ chối cũng cần thẩm quyền duyệt loại báo giá
    kiem_han_muc(db, nd, LOAI_DUYET, _bgf_tong(bgf))
    bgf.trang_thai = "TU_CHOI"
    bgf.nguoi_duyet = nhan_vien_id_cua(db, nd.id)
    bgf.ly_do_tu_choi = (data.ly_do or "").strip()[:300] or None
    ghi_audit(db, nd.id, "TU_CHOI", "bao_gia_form", bgf.id, moi={"ly_do": bgf.ly_do_tu_choi})
    db.commit(); db.refresh(bgf)
    return bgf


class GuiBaoGiaVao(_BM):
    den: str
    tieu_de: str | None = None
    loi_nhan: str | None = None
    noi_dung: str | None = None   # bản thư đã xem trước/chỉnh sửa; trống → soạn theo mẫu


def _soan_thu_bao_gia(bgf: BaoGiaForm, loi_nhan: str | None, ten_file: str | None,
                      co_dinh_kem: bool = True):
    """Soạn tiêu đề + nội dung thư báo giá theo văn phong thương mại chuẩn công ty."""
    from ..config import settings as _st
    from ..bao_gia_pdf import tinh_bao_gia
    d = bgf.noi_dung or {}
    so = d.get("so") or bgf.so or f"BG-{bgf.id}"
    _sub, _vat, tong = tinh_bao_gia(d)
    mn = lambda n: f"{round(n):,}".replace(",", ".")
    khach = d.get("khach_ten") or "Quý công ty"
    mo_dau = (loi_nhan or "").strip() or (
        f"Công ty TNHH Giải pháp Kỹ thuật Sóng Việt trân trọng cảm ơn sự quan tâm của {khach}. "
        f"Chúng tôi hân hạnh gửi đến Quý công ty báo giá cho hạng mục nêu dưới đây.")
    L = [f"Kính gửi {khach},", "", mo_dau, "", "THÔNG TIN BÁO GIÁ:",
         f"   •  Số báo giá: {so} — ngày {d.get('ngay') or ''}"]
    if d.get("tieu_de"):
        L.append(f"   •  Hạng mục: {d.get('tieu_de')}")
    if tong > 0:
        L.append(f"   •  Tổng giá trị (đã gồm VAT): {mn(tong)} VND")
    if d.get("hieu_luc"):
        L.append(f"   •  Hiệu lực báo giá: {d.get('hieu_luc')}")
    if co_dinh_kem and ten_file:
        L.append(f"   •  Chi tiết đầy đủ: vui lòng xem tệp đính kèm ({ten_file}).")
    L += ["",
          "Kính mong Quý công ty xem xét. Nếu cần trao đổi thêm về thông số kỹ thuật, "
          "tiến độ cung cấp hoặc điều khoản thương mại, xin vui lòng liên hệ chúng tôi "
          "theo thông tin bên dưới — chúng tôi luôn sẵn sàng hỗ trợ.",
          "",
          "Trân trọng,",
          "",
          (d.get("nguoi_bg") or "Bộ phận Kinh doanh"),
          "CÔNG TY TNHH GIẢI PHÁP KỸ THUẬT SÓNG VIỆT — \"We Have Solutions\"",
          f"Email: {_st.email_from} · Điện thoại: {_st.cong_ty_tel}",
          f"Địa chỉ: {_st.cong_ty_dia_chi} · Website: {_st.cong_ty_website}"]
    tieu_de = f"[Sóng Việt] Báo giá {so}" + (f" — {khach}" if d.get("khach_ten") else "")
    return tieu_de, "\n".join(L)


def _bgf_tinh(d: dict):
    sub = 0.0; vat = 0.0
    for it in (d.get("items") or []):
        tt = float(it.get("so_luong") or 0) * float(it.get("don_gia") or 0)
        sub += tt
        p = it.get("vat_pct")
        p = float(d.get("vat_pct") or 0) if p in (None, "") else float(p)
        vat += tt * p / 100
    return sub, vat, sub + vat


@router.post("/bao-gia-form/{bgf_id}/gui-email")
def gui_bao_gia_email(bgf_id: int, data: GuiBaoGiaVao, db: Session = Depends(get_db),
                      nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Gửi báo giá cho khách: tự sinh PDF báo giá đính kèm, thư văn phong chuyên nghiệp.
    Gửi từ settings.email_from (sv-sales@watersolutions.company)."""
    import os as _os, re as _re, tempfile as _tmp
    from ..email_gateway import lay_email_provider
    from ..config import settings as _st
    from ..bao_gia_pdf import tao_bao_gia_pdf, tinh_bao_gia
    bgf = db.get(BaoGiaForm, bgf_id)
    if bgf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá")
    if bgf.trang_thai not in ("DA_DUYET", "DA_GUI"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Báo giá chưa được DUYỆT — hãy bấm “Trình duyệt” và chờ duyệt "
                            "trước khi gửi cho khách.")
    if "@" not in (data.den or ""):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email người nhận không hợp lệ")
    d = bgf.noi_dung or {}
    so = d.get("so") or bgf.so or f"BG-{bgf.id}"

    # 1) Đính kèm: ưu tiên file báo giá/proposal đã tải lên; không có thì tự sinh PDF
    from ..models import TepDinhKem as _Tep
    tep_prop = db.query(_Tep).filter_by(doi_tuong="BAO_GIA_FORM",
                                        doi_tuong_id=bgf.id, loai="PROPOSAL").first()
    ten_file = "Bao_gia_" + _re.sub(r"[^A-Za-z0-9._-]", "-", so) + ".pdf"
    pdf_path = _os.path.join(_tmp.gettempdir(), f"bgf_{bgf.id}_{ten_file}")
    dinh_kem = []
    if tep_prop is not None:
        from ..luu_tru import doc as _doc
        try:
            raw = _doc(tep_prop.duong_dan)
            ten_file = tep_prop.ten_file or ten_file
            pdf_path = _os.path.join(_tmp.gettempdir(),
                                     f"bgf_{bgf.id}_" + _re.sub(r"[^A-Za-z0-9._ -]", "-", ten_file))
            with open(pdf_path, "wb") as f:
                f.write(raw)
            dinh_kem = [{"duong_dan": pdf_path, "ten_file": ten_file}]
        except Exception:
            dinh_kem = []
    else:
        try:
            tao_bao_gia_pdf(pdf_path, d,
                            font_path=_st.pdf_font_path, font_bold_path=_st.pdf_font_bold_path)
            dinh_kem = [{"duong_dan": pdf_path, "ten_file": ten_file}]
        except Exception:
            dinh_kem = []   # không chặn việc gửi thư nếu sinh PDF lỗi

    # 2) Nội dung thư — dùng bản đã xem trước/chỉnh sửa nếu có, không thì soạn theo mẫu
    tieu_de_md, thu_md = _soan_thu_bao_gia(bgf, data.loi_nhan, ten_file, bool(dinh_kem))
    noi_dung_thu = (data.noi_dung or "").strip() or thu_md
    tieu_de = data.tieu_de or tieu_de_md

    cc = (_st.email_cc_bao_gia or "").strip()
    if cc and cc.lower() == data.den.strip().lower():
        cc = ""   # người nhận chính là địa chỉ CC → khỏi CC trùng
    try:
        kq = lay_email_provider().gui(data.den.strip(), tieu_de, noi_dung_thu,
                                      dinh_kem=dinh_kem, cc=cc or None)
    finally:
        try:
            if dinh_kem:
                _os.remove(pdf_path)
        except OSError:
            pass
    if kq.get("trang_thai") == "LOI":
        raise HTTPException(status.HTTP_502_BAD_GATEWAY,
                            "Gửi email thất bại: " + (kq.get("ghi_chu") or "lỗi SMTP"))
    bgf.trang_thai = "DA_GUI"
    # Lưu bản PDF vừa gửi vào kho tệp dùng chung (bỏ qua nếu đã có file proposal riêng)
    if tep_prop is None:
        try:
            _luu_pdf_bao_gia(db, nd, bgf)
        except Exception:
            pass
    ghi_audit(db, nd.id, "GUI", "bao_gia_form", bgf.id,
              moi={"den": data.den, "gui_tu": kq.get("gui_tu"), "pdf": bool(dinh_kem)})
    db.commit()
    return {"gui_tu": kq.get("gui_tu"), "den": data.den, "cc": cc or None,
            "pdf_dinh_kem": bool(dinh_kem),
            "trang_thai": kq.get("trang_thai"), "ghi_chu": kq.get("ghi_chu")}


class XemTruocEmailVao(_BM):
    loi_nhan: str | None = None


@router.post("/bao-gia-form/{bgf_id}/email-preview")
def xem_truoc_email_bao_gia(bgf_id: int, data: XemTruocEmailVao, db: Session = Depends(get_db),
                            _=Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Soạn trước tiêu đề + nội dung thư báo giá (KHÔNG gửi) để người dùng xem và chỉnh."""
    import re as _re
    from ..models import TepDinhKem as _Tep
    bgf = db.get(BaoGiaForm, bgf_id)
    if bgf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá")
    d = bgf.noi_dung or {}
    so = d.get("so") or bgf.so or f"BG-{bgf.id}"
    tep_prop = db.query(_Tep).filter_by(doi_tuong="BAO_GIA_FORM",
                                        doi_tuong_id=bgf.id, loai="PROPOSAL").first()
    ten_file = (tep_prop.ten_file if tep_prop is not None
                else "Bao_gia_" + _re.sub(r"[^A-Za-z0-9._-]", "-", so) + ".pdf")
    tieu_de, thu = _soan_thu_bao_gia(bgf, data.loi_nhan, ten_file, True)
    return {"tieu_de": tieu_de, "noi_dung": thu, "dinh_kem_ten": ten_file,
            "tu_proposal": tep_prop is not None}


def _luu_pdf_bao_gia(db: Session, nd: NguoiDung, bgf: BaoGiaForm):
    """Sinh PDF báo giá và lưu vào KHO TỆP DÙNG CHUNG trên máy chủ (R2/đĩa).
    Mỗi báo giá giữ đúng một bản PDF mới nhất — lưu lại sẽ thay bản cũ."""
    import os as _os, re as _re, tempfile as _tmp
    from ..config import settings as _st
    from ..bao_gia_pdf import tao_bao_gia_pdf
    from ..luu_tru import luu as _luu, xoa as _xoa
    from ..models import TepDinhKem
    d = bgf.noi_dung or {}
    so = d.get("so") or bgf.so or f"BG-{bgf.id}"
    ten_file = "Bao_gia_" + _re.sub(r"[^A-Za-z0-9._-]", "-", so) + ".pdf"
    pdf_path = _os.path.join(_tmp.gettempdir(), f"kho_{bgf.id}_{ten_file}")
    tao_bao_gia_pdf(pdf_path, d,
                    font_path=_st.pdf_font_path, font_bold_path=_st.pdf_font_bold_path)
    with open(pdf_path, "rb") as f:
        data = f.read()
    try:
        _os.remove(pdf_path)
    except OSError:
        pass
    for t in db.query(TepDinhKem).filter_by(doi_tuong="BAO_GIA_FORM",
                                            doi_tuong_id=bgf.id, loai="PDF").all():
        _xoa(t.duong_dan)
        db.delete(t)
    ref = _luu(data, "bao_gia_form", bgf.id, ten_file, "application/pdf")
    tep = TepDinhKem(doi_tuong="BAO_GIA_FORM", doi_tuong_id=bgf.id, loai="PDF",
                     ten_file=ten_file, duong_dan=ref, kich_thuoc=len(data),
                     content_type="application/pdf", nguoi_tai_len=nhan_vien_id_cua(db, nd.id))
    db.add(tep)
    db.flush()
    return tep


@router.post("/bao-gia-form/{bgf_id}/luu-pdf")
def luu_pdf_kho(bgf_id: int, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Sinh PDF báo giá và lưu vào kho tệp dùng chung — mọi người tải cùng một bản."""
    bgf = db.get(BaoGiaForm, bgf_id)
    if bgf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá")
    if (bgf.noi_dung or {}).get("loai") == "HOP_DONG":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Hợp đồng xuất PDF từ trình duyệt — lưu bản ký lên Đơn hàng & PO/Hợp đồng.")
    try:
        tep = _luu_pdf_bao_gia(db, nd, bgf)
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            f"Không sinh được PDF: {e}")
    ghi_audit(db, nd.id, "LUU_PDF", "bao_gia_form", bgf.id, moi={"ten_file": tep.ten_file})
    db.commit()
    return {"ok": True, "tep_id": tep.id, "ten_file": tep.ten_file, "kich_thuoc": tep.kich_thuoc}


# ----- Đính kèm file báo giá/Proposal soạn sẵn (thay cho bảng chi tiết SP/DV) -----
@router.post("/bao-gia-form/{bgf_id}/dinh-kem")
def tai_dinh_kem_bao_gia(bgf_id: int, file: UploadFile = File(...),
                         db: Session = Depends(get_db),
                         nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Đính kèm file báo giá/proposal soạn sẵn (PDF/Word/Excel) vào báo giá —
    khi có file thì không cần dùng bảng chi tiết SP/DV. Mỗi báo giá 1 file, tải lại sẽ thay."""
    from ..luu_tru import luu as _luu, xoa as _xoa
    from ..models import TepDinhKem
    bgf = db.get(BaoGiaForm, bgf_id)
    if bgf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá")
    data = file.file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tệp rỗng")
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tệp quá lớn (tối đa 25MB)")
    for t in db.query(TepDinhKem).filter_by(doi_tuong="BAO_GIA_FORM",
                                            doi_tuong_id=bgf.id, loai="PROPOSAL").all():
        _xoa(t.duong_dan)
        db.delete(t)
    ref = _luu(data, "bao_gia_form", bgf.id, file.filename or "proposal",
               file.content_type or "application/octet-stream")
    tep = TepDinhKem(doi_tuong="BAO_GIA_FORM", doi_tuong_id=bgf.id, loai="PROPOSAL",
                     ten_file=file.filename or "proposal", duong_dan=ref, kich_thuoc=len(data),
                     content_type=file.content_type or "application/octet-stream",
                     nguoi_tai_len=nhan_vien_id_cua(db, nd.id))
    db.add(tep)
    db.flush()
    d = dict(bgf.noi_dung or {})
    d["dinh_kem_ten"] = tep.ten_file
    bgf.noi_dung = d
    ghi_audit(db, nd.id, "DINH_KEM", "bao_gia_form", bgf.id, moi={"ten_file": tep.ten_file})
    db.commit()
    return {"tep_id": tep.id, "ten_file": tep.ten_file, "kich_thuoc": tep.kich_thuoc}


@router.get("/bao-gia-form/{bgf_id}/dinh-kem")
def tai_ve_dinh_kem_bao_gia(bgf_id: int, db: Session = Depends(get_db),
                            _=Depends(yeu_cau(MODULE, "XEM"))):
    from ..luu_tru import phan_hoi_tai as _tai
    from ..models import TepDinhKem
    t = db.query(TepDinhKem).filter_by(doi_tuong="BAO_GIA_FORM",
                                       doi_tuong_id=bgf_id, loai="PROPOSAL").first()
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Báo giá chưa có file đính kèm")
    return _tai(t.duong_dan, t.ten_file, t.content_type)


@router.delete("/bao-gia-form/{bgf_id}/dinh-kem")
def go_dinh_kem_bao_gia(bgf_id: int, db: Session = Depends(get_db),
                        nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Gỡ file proposal khỏi báo giá (quay lại dùng bảng chi tiết SP/DV)."""
    from ..luu_tru import xoa as _xoa
    from ..models import TepDinhKem
    bgf = db.get(BaoGiaForm, bgf_id)
    if bgf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá")
    ts = db.query(TepDinhKem).filter_by(doi_tuong="BAO_GIA_FORM",
                                        doi_tuong_id=bgf_id, loai="PROPOSAL").all()
    if not ts:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Báo giá chưa có file đính kèm")
    ten = ts[0].ten_file
    for t in ts:
        _xoa(t.duong_dan)
        db.delete(t)
    d = dict(bgf.noi_dung or {})
    d.pop("dinh_kem_ten", None)
    bgf.noi_dung = d
    ghi_audit(db, nd.id, "GO_DINH_KEM", "bao_gia_form", bgf.id, cu={"ten_file": ten})
    db.commit()
    return {"da_go": True}


@router.get("/kho-tep")
def ds_kho_tep(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """KHO TỆP DÙNG CHUNG toàn app — mọi tệp đính kèm/PDF sinh ra đều liệt kê tại đây:
    báo giá PDF, PO/HĐ đơn hàng, tệp chiến dịch email, PO đơn mua, dự toán đề xuất,
    tài liệu cho thuê và tài liệu dự án."""
    from ..models import (TepDinhKem, ChienDichEmail, DonMua, YeuCauMua,
                          TaiSanChoThue, DuAnTaiLieu, DuAn, NhaCungCap)
    NHOM = {"BAO_GIA_FORM": "Báo giá (PDF)", "DON_HANG": "Đơn hàng — PO/HĐ",
            "CHIEN_DICH": "Email chào hàng", "DON_MUA": "Đơn mua NCC (PO)",
            "YEU_CAU_MUA": "Đề xuất mua — dự toán", "CHO_THUE_DA": "Cho thuê — tài liệu",
            "BAO_GIA_NCC_FILE": "Báo giá NCC — file", "NCC_HO_SO": "Hồ sơ NCC",
            "DU_AN_DU_TOAN": "Dự án — báo giá dự toán"}
    out = []
    for t in db.query(TepDinhKem).order_by(TepDinhKem.id.desc()).limit(500).all():
        ref = None
        if t.doi_tuong == "BAO_GIA_FORM":
            b = db.get(BaoGiaForm, t.doi_tuong_id)
            d = (b.noi_dung if b else None) or {}
            so = d.get("so") or (b.so if b else None)
            ref = (so or "") + (f" · {d.get('khach_ten')}" if d.get("khach_ten") else "")
        elif t.doi_tuong == "DON_HANG":
            o = db.get(DonHang, t.doi_tuong_id)
            ref = o.so if o else None
        elif t.doi_tuong == "CHIEN_DICH":
            c = db.get(ChienDichEmail, t.doi_tuong_id)
            ref = c.ten if c else None
        elif t.doi_tuong == "DON_MUA":
            p = db.get(DonMua, t.doi_tuong_id)
            ref = p.so if p else None
        elif t.doi_tuong == "YEU_CAU_MUA":
            y = db.get(YeuCauMua, t.doi_tuong_id)
            ref = f"Đề xuất #{t.doi_tuong_id}" + (f" · {y.cho_thue_ma}" if y and y.cho_thue_ma else "")
        elif t.doi_tuong == "CHO_THUE_DA":
            ts = db.get(TaiSanChoThue, t.doi_tuong_id)
            ref = f"{ts.ma} · {ts.ten}" if ts else None
        elif t.doi_tuong in ("BAO_GIA_NCC_FILE", "NCC_HO_SO"):
            nc = db.get(NhaCungCap, t.doi_tuong_id)
            ref = nc.ten if nc else None
        elif t.doi_tuong == "DU_AN_DU_TOAN":
            d_a = db.get(DuAn, t.doi_tuong_id)
            ref = (d_a.ma or d_a.ten) if d_a else None
        out.append({"nhom": NHOM.get(t.doi_tuong, t.doi_tuong), "ref": ref or f"#{t.doi_tuong_id}",
                    "ten_file": t.ten_file, "kich_thuoc": t.kich_thuoc,
                    "tao_luc": str(getattr(t, "created_at", "") or "")[:16],
                    "kind": "tep", "id": t.id})
    rows_da = (db.query(DuAnTaiLieu, DuAn)
               .outerjoin(DuAn, DuAnTaiLieu.du_an_id == DuAn.id)
               .filter(DuAnTaiLieu.duong_dan.isnot(None))
               .order_by(DuAnTaiLieu.id.desc()).limit(300).all())
    for tl, da in rows_da:
        out.append({"nhom": "Dự án — tài liệu",
                    "ref": ((da.ma or da.ten) if da else None) or f"DA #{tl.du_an_id}",
                    "ten_file": tl.ten, "kich_thuoc": tl.kich_thuoc,
                    "tao_luc": str(tl.ngay or "")[:16], "kind": "du_an", "id": tl.id})
    return out


@router.delete("/bao-gia-form/{bgf_id}")
def xoa_bao_gia_form(bgf_id: int, db: Session = Depends(get_db),
                     nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    bgf = db.get(BaoGiaForm, bgf_id)
    if bgf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá nháp")
    so_cu = bgf.so
    from ..models import TepDinhKem
    from ..luu_tru import xoa as _xoa_tep
    for t in db.query(TepDinhKem).filter_by(doi_tuong="BAO_GIA_FORM", doi_tuong_id=bgf_id).all():
        _xoa_tep(t.duong_dan)
        db.delete(t)
    db.delete(bgf)
    ghi_audit(db, nd.id, "XOA", "bao_gia_form", bgf_id, cu={"so": so_cu})
    db.commit()
    return {"ok": True}


# ----- Báo giá -----
@router.get("/bao-gia", response_model=list[BaoGiaRa])
def ds_bao_gia(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(BaoGia).order_by(BaoGia.id.desc()).all()


@router.post("/bao-gia", response_model=BaoGiaRa, status_code=201)
def tao_bao_gia(data: BaoGiaVao, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if db.get(KhachHang, data.khach_hang_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khách hàng")
    tong = sum(ct.so_luong * ct.don_gia for ct in data.chi_tiet)
    bg = BaoGia(so=data.so, khach_hang_id=data.khach_hang_id,
                nguoi_tao=nhan_vien_id_cua(db, nd.id), ngay=date.today(),
                tong_tien=tong, trang_thai="CHO_DUYET")
    db.add(bg); db.flush()
    if not bg.so:
        bg.so = f"BG-{date.today():%Y%m%d}-{bg.id}"
    for ct in data.chi_tiet:
        db.add(BaoGiaCt(bao_gia_id=bg.id, hang_hoa_id=ct.hang_hoa_id,
                        so_luong=ct.so_luong, don_gia=ct.don_gia))
    ghi_audit(db, nd.id, "TAO", "bao_gia", bg.id, moi={"tong_tien": float(tong)})
    db.commit(); db.refresh(bg)
    return bg


# ----- DUYỆT báo giá: XEM module + thẩm quyền theo han_muc (TP_KD 100tr / CEO ∞) -----
@router.post("/bao-gia/{bg_id}/duyet", response_model=BaoGiaRa)
def duyet_bao_gia(bg_id: int, db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "XEM"))):
    bg = db.get(BaoGia, bg_id)
    if bg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá")
    if bg.trang_thai != "CHO_DUYET":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Báo giá đang ở {bg.trang_thai}")
    kiem_han_muc(db, nd, LOAI_DUYET, bg.tong_tien)
    bg.trang_thai = "DA_DUYET"
    bg.nguoi_duyet = nhan_vien_id_cua(db, nd.id)
    ghi_audit(db, nd.id, "DUYET", "bao_gia", bg.id, moi={"trang_thai": "DA_DUYET"})
    db.commit(); db.refresh(bg)
    return bg


# ----- Tạo đơn hàng từ báo giá đã duyệt -----
@router.post("/bao-gia/{bg_id}/tao-don", response_model=DonHangRa, status_code=201)
def tao_don_tu_bao_gia(bg_id: int, db: Session = Depends(get_db),
                       nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    bg = db.get(BaoGia, bg_id)
    if bg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá")
    if bg.trang_thai != "DA_DUYET":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Báo giá chưa được duyệt")
    dh = DonHang(khach_hang_id=bg.khach_hang_id, bao_gia_id=bg.id, ngay=date.today(),
                 tong_tien=bg.tong_tien, trang_thai="MOI")
    db.add(dh); db.flush()
    dh.so = f"DH-{date.today():%Y%m%d}-{dh.id}"
    for ct in bg.chi_tiet:
        db.add(DonHangCt(don_hang_id=dh.id, hang_hoa_id=ct.hang_hoa_id,
                         so_luong=ct.so_luong, don_gia=ct.don_gia))
    ghi_audit(db, nd.id, "TAO", "don_hang", dh.id, moi={"tu_bao_gia": bg.id})
    db.commit(); db.refresh(dh)
    return dh


# ----- Cập nhật đơn hàng bán TRỰC TIẾP (khách gửi PO không qua báo giá) -----
from pydantic import BaseModel as _DHBase


class DonHangCtTrucTiepVao(_DHBase):
    ten: str
    hang_hoa_id: int | None = None   # có id thì dùng thẳng, không thì khớp/tạo theo tên
    don_vi: str | None = None
    so_luong: Decimal
    don_gia: Decimal
    thue_suat: Decimal = Decimal(8)   # VAT % của dòng (mặc định 8%)


def _tinh_don_hang(lines):
    """lines: list (hang_hoa_id, so_luong, don_gia, thue_suat).
    Trả (tien_hang, tien_thue). VAT làm tròn theo TỪNG DÒNG (chuẩn VAS)."""
    th, tt = Decimal(0), Decimal(0)
    for _id, sl, dg, ts in lines:
        line = (Decimal(str(sl)) * Decimal(str(dg))).quantize(Decimal(1))
        th += line
        tt += (line * Decimal(str(ts or 0)) / Decimal(100)).quantize(Decimal(1))
    return th, tt


class DonHangTrucTiepVao(_DHBase):
    khach_hang_id: int
    so: str | None = None            # bỏ trống → tự tạo DH-YYYYMMDD-id
    ngay: date | None = None
    chi_tiet: list[DonHangCtTrucTiepVao]


@router.post("/don-hang", response_model=DonHangRa, status_code=201)
def tao_don_hang_truc_tiep(data: DonHangTrucTiepVao, db: Session = Depends(get_db),
                           nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Tạo đơn hàng bán trực tiếp từ PO/HĐ khách gửi (không qua báo giá nội bộ).
    Sản phẩm chưa có trong kho được tự thêm (SAN_PHAM, tồn 0) để mã đơn bán
    liên thông được sang Mua hàng / Kho / Dự án / Cho thuê."""
    kh = db.get(KhachHang, data.khach_hang_id)
    if kh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khách hàng")
    if not data.chi_tiet:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Đơn hàng cần ít nhất 1 dòng sản phẩm")
    so = (data.so or "").strip() or None
    if so and db.query(DonHang).filter_by(so=so).first() is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Mã đơn hàng '{so}' đã tồn tại — chọn mã khác hoặc bỏ trống để tự tạo.")
    lines = []
    hang_moi = []
    for it in data.chi_tiet:
        ten = (it.ten or "").strip()
        if it.so_luong <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Số lượng của '{ten}' phải lớn hơn 0")
        if it.don_gia < 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Đơn giá của '{ten}' không được âm")
        hh = db.get(HangHoa, it.hang_hoa_id) if it.hang_hoa_id else None
        if hh is None and ten:
            hh = db.query(HangHoa).filter(HangHoa.ten.ilike(ten)).first()
        if hh is None:
            if not ten:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dòng sản phẩm thiếu tên")
            hh = HangHoa(ten=ten, loai="SAN_PHAM", don_vi=(it.don_vi or None), gia_ban=it.don_gia)
            db.add(hh)
            db.flush()
            if db.query(TonKho).filter_by(hang_hoa_id=hh.id).first() is None:
                db.add(TonKho(hang_hoa_id=hh.id, so_luong=0))
            hang_moi.append(hh.ten)
        elif it.don_vi and not hh.don_vi:
            hh.don_vi = it.don_vi
        lines.append((hh.id, it.so_luong, it.don_gia, it.thue_suat))
    tien_hang, tien_thue = _tinh_don_hang(lines)
    dh = DonHang(so=so, khach_hang_id=data.khach_hang_id,
                 ngay=data.ngay or date.today(), tong_tien=tien_hang,
                 tien_thue=tien_thue, trang_thai="MOI")
    db.add(dh)
    db.flush()
    if not dh.so:
        dh.so = f"DH-{date.today():%Y%m%d}-{dh.id}"
    for hh_id, sl, dg, ts in lines:
        db.add(DonHangCt(don_hang_id=dh.id, hang_hoa_id=hh_id, so_luong=sl, don_gia=dg, thue_suat=ts))
    ghi_audit(db, nd.id, "TAO", "don_hang", dh.id,
              moi={"truc_tiep": True, "tong_tien": float(tien_hang),
                   "tien_thue": float(tien_thue), "so_dong": len(lines),
                   "hang_moi": hang_moi[:20]})
    db.commit(); db.refresh(dh)
    return dh


@router.post("/don-hang/ai-tu-po")
async def tao_don_hang_tu_po_ai(file: UploadFile = File(...), db: Session = Depends(get_db),
                                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """AI đọc file PO/đơn đặt hàng KHÁCH gửi → tạo đơn hàng bán + đính kèm file PO
    (đơn tự vào bảng 'Danh sách đơn hàng bán đã có PO/HĐ'). Khớp khách theo MST rồi
    tên (chưa có → tạo mới 'cần kiểm chứng'); hàng chưa có tự thêm vào kho."""
    from ..ai_gateway import doc_po_khach_file
    from ..models import TepDinhKem
    from ..luu_tru import luu as _luu
    raw = await file.read()
    if not raw:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File PO rỗng")
    try:
        info = doc_po_khach_file(raw, file.content_type or "", file.filename or "po")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    kh_info = info.get("khach_hang") or {}
    ten_kh = (kh_info.get("ten") or "").strip()
    mst = (kh_info.get("ma_so_thue") or "").strip() or None
    # khớp khách: MST trước, rồi tên
    kh = None
    if mst:
        kh = db.query(KhachHang).filter(KhachHang.ma_so_thue == mst).first()
    if kh is None and ten_kh:
        kh = db.query(KhachHang).filter(KhachHang.ten.ilike(ten_kh)).first()
    kh_moi = False
    if kh is None:
        if not ten_kh:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "AI không đọc được tên khách hàng trong PO — hãy tạo đơn thủ công.")
        kh = KhachHang(ten=ten_kh, ma_so_thue=mst,
                       dien_thoai=kh_info.get("dien_thoai"), email=kh_info.get("email"))
        db.add(kh); db.flush(); kh_moi = True
    # số PO của khách (trùng trong hệ thống → để tự tạo mã)
    so = (info.get("so_po") or "").strip() or None
    if so and db.query(DonHang).filter_by(so=so).first() is not None:
        so = None
    # ngày PO
    ngay_dh = date.today()
    try:
        if info.get("ngay"):
            ngay_dh = date.fromisoformat(str(info["ngay"])[:10])
    except ValueError:
        ngay_dh = date.today()
    # dòng hàng (khớp/tạo hàng hóa; VAT mặc định 8% nếu PO không ghi)
    lines, hang_moi = [], []
    for it in info["chi_tiet"]:
        ten = (it.get("ten") or "").strip()
        hh = db.query(HangHoa).filter(HangHoa.ten.ilike(ten)).first() if ten else None
        if hh is None:
            hh = HangHoa(ten=ten, loai="SAN_PHAM", don_vi=(it.get("don_vi") or None),
                         gia_ban=it.get("don_gia") or 0)
            db.add(hh); db.flush()
            if db.query(TonKho).filter_by(hang_hoa_id=hh.id).first() is None:
                db.add(TonKho(hang_hoa_id=hh.id, so_luong=0))
            hang_moi.append(hh.ten)
        elif it.get("don_vi") and not hh.don_vi:
            hh.don_vi = it["don_vi"]
        sl = Decimal(str(it.get("so_luong") or 1))
        dg = Decimal(str(it.get("don_gia") or 0))
        ts = Decimal(str(it["thue_suat"] if it.get("thue_suat") is not None else 8))
        lines.append((hh.id, sl, dg, ts))
    tien_hang, tien_thue = _tinh_don_hang(lines)
    dh = DonHang(so=so, khach_hang_id=kh.id, ngay=ngay_dh, tong_tien=tien_hang,
                 tien_thue=tien_thue, trang_thai="MOI")
    db.add(dh); db.flush()
    if not dh.so:
        dh.so = f"DH-{date.today():%Y%m%d}-{dh.id}"
    for hh_id, sl, dg, ts in lines:
        db.add(DonHangCt(don_hang_id=dh.id, hang_hoa_id=hh_id, so_luong=sl, don_gia=dg, thue_suat=ts))
    # đính kèm chính file PO (loai=PO → đơn vào bảng "đã có PO/HĐ")
    duong_dan = _luu(raw, "don_hang", dh.id, file.filename or "PO", file.content_type)
    db.add(TepDinhKem(doi_tuong="DON_HANG", doi_tuong_id=dh.id, loai="PO",
                      ten_file=file.filename or f"PO-{dh.so}", duong_dan=duong_dan,
                      kich_thuoc=len(raw), content_type=file.content_type,
                      nguoi_tai_len=nhan_vien_id_cua(db, nd.id)))
    ghi_audit(db, nd.id, "AI_DOC_PO", "don_hang", dh.id,
              moi={"tu_file": file.filename, "khach": kh.ten, "khach_moi": kh_moi,
                   "so_dong": len(lines), "tong_tien": float(tien_hang), "tien_thue": float(tien_thue),
                   "hang_moi": len(hang_moi)})
    db.commit(); db.refresh(dh)
    return {"ok": True, "don_hang_id": dh.id, "so": dh.so, "khach": kh.ten, "khach_moi": kh_moi,
            "so_dong": len(lines), "tien_hang": float(tien_hang), "tien_thue": float(tien_thue),
            "tong_da_vat": float(tien_hang + tien_thue), "so_hang_moi": len(hang_moi),
            "hang_moi": hang_moi[:10]}


# ----- DUYET: xóa báo giá nội bộ (chặn khi đã sinh đơn hàng) -----
@router.delete("/bao-gia/{bg_id}")
def xoa_bao_gia(bg_id: int, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """Xóa báo giá nội bộ cùng dòng hàng. Chặn khi đã có đơn hàng tạo từ báo giá
    này (giữ vết bán hàng); cơ hội CRM liên quan chỉ bị gỡ liên kết."""
    from sqlalchemy.exc import IntegrityError
    bg = db.get(BaoGia, bg_id)
    if bg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo giá")
    so_don = db.query(DonHang).filter_by(bao_gia_id=bg_id).count()
    if so_don:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Báo giá '{bg.so or bg_id}' đã sinh {so_don} đơn hàng — không thể xóa để giữ vết bán hàng. "
            "Nếu cần, hãy xóa đơn hàng liên quan trước.")
    so_cu, tt_cu = bg.so, bg.trang_thai
    db.query(BaoGiaCt).filter_by(bao_gia_id=bg_id).delete()
    try:
        db.delete(bg)
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Báo giá '{so_cu}' còn dữ liệu liên kết ở phân hệ khác nên không thể xóa.")
    ghi_audit(db, nd.id, "XOA", "bao_gia", bg_id, cu={"so": so_cu, "trang_thai": tt_cu})
    db.commit()
    return {"ok": True, "so": so_cu}


@router.get("/don-hang", response_model=list[DonHangRa])
def ds_don_hang(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return db.query(DonHang).order_by(DonHang.id.desc()).all()


@router.get("/don-hang/{dh_id}/chi-tiet")
def chi_tiet_don_hang(dh_id: int, db: Session = Depends(get_db),
                      _=Depends(yeu_cau(MODULE, "XEM"))):
    """Chi tiết đơn hàng bán kèm dòng sản phẩm (tên, đơn vị) — phục vụ form sửa."""
    dh = db.get(DonHang, dh_id)
    if dh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn hàng")
    ct_out = []
    for ct in dh.chi_tiet:
        hh = db.get(HangHoa, ct.hang_hoa_id)
        ct_out.append({"hang_hoa_id": ct.hang_hoa_id, "ten": hh.ten if hh else f"HH #{ct.hang_hoa_id}",
                       "don_vi": hh.don_vi if hh else None,
                       "so_luong": float(ct.so_luong), "don_gia": float(ct.don_gia),
                       "thue_suat": float(ct.thue_suat or 0)})
    co_hd = db.query(HoaDon).filter_by(don_hang_id=dh_id).first() is not None
    return {"id": dh.id, "so": dh.so, "khach_hang_id": dh.khach_hang_id,
            "ngay": str(dh.ngay) if dh.ngay else None, "tong_tien": float(dh.tong_tien or 0),
            "tien_thue": float(dh.tien_thue or 0),
            "trang_thai": dh.trang_thai, "co_hoa_don": co_hd,
            # khóa sửa nội dung đơn (vẫn đổi được TRẠNG THÁI) khi đã xuất kho / có hóa đơn
            "khoa_sua": bool(dh.trang_thai == "DA_XUAT" or co_hd),
            "chi_tiet": ct_out}


_DH_TT_TAY = ("MOI", "DANG_THUC_HIEN", "HOAN_THANH")


class TrangThaiDonVao(_CNBase):
    trang_thai: str


@router.put("/don-hang/{dh_id}/trang-thai")
def doi_trang_thai_don_hang(dh_id: int, data: TrangThaiDonVao, db: Session = Depends(get_db),
                            nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Đổi trạng thái theo dõi của đơn hàng (Mới / Đang thực hiện / Hoàn thành).
    Cho phép cả khi đơn đã xuất kho hoặc đã có hóa đơn — đây là cờ theo dõi bán hàng,
    không phải số liệu kế toán. Không cho đặt tay 'DA_XUAT' (do luồng xuất kho quyết định)."""
    dh = db.get(DonHang, dh_id)
    if dh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn hàng")
    tt = (data.trang_thai or "").strip().upper()
    if tt not in _DH_TT_TAY:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Trạng thái phải là Mới / Đang thực hiện / Hoàn thành. "
                            "Trạng thái 'Đã xuất kho' do luồng xuất kho tự đặt.")
    cu = dh.trang_thai
    dh.trang_thai = tt
    ghi_audit(db, nd.id, "CAP_NHAT", "don_hang", dh.id,
              cu={"trang_thai": cu}, moi={"trang_thai": tt})
    db.commit()
    return {"id": dh.id, "trang_thai": dh.trang_thai}


@router.put("/don-hang/{dh_id}", response_model=DonHangRa)
def sua_don_hang(dh_id: int, data: DonHangTrucTiepVao, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """Sửa đơn hàng bán (ngày, mã, khách, dòng sản phẩm). Chặn khi đã xuất kho
    hoặc đã lập hóa đơn — giữ vết kho & kế toán."""
    dh = db.get(DonHang, dh_id)
    if dh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn hàng")
    if dh.trang_thai == "DA_XUAT":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Đơn đã xuất kho — không sửa được để giữ vết kho/kế toán. "
                            "Cần điều chỉnh hãy lập đơn bổ sung hoặc liên hệ CEO/ADMIN xử lý chứng từ.")
    if db.query(HoaDon).filter_by(don_hang_id=dh_id).first() is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Đơn đã lập hóa đơn — không sửa được; xử lý hóa đơn ở mục Kế toán trước.")
    kh = db.get(KhachHang, data.khach_hang_id)
    if kh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy khách hàng")
    if not data.chi_tiet:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Đơn hàng cần ít nhất 1 dòng sản phẩm")
    so = (data.so or "").strip() or None
    if so and db.query(DonHang).filter(DonHang.so == so, DonHang.id != dh_id).first() is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Mã đơn hàng '{so}' đã tồn tại")
    lines = []
    for it in data.chi_tiet:
        ten = (it.ten or "").strip()
        if it.so_luong <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Số lượng của '{ten}' phải lớn hơn 0")
        if it.don_gia < 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Đơn giá của '{ten}' không được âm")
        hh = db.get(HangHoa, it.hang_hoa_id) if it.hang_hoa_id else None
        if hh is None and ten:
            hh = db.query(HangHoa).filter(HangHoa.ten.ilike(ten)).first()
        if hh is None:
            if not ten:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dòng sản phẩm thiếu tên")
            hh = HangHoa(ten=ten, loai="SAN_PHAM", don_vi=(it.don_vi or None), gia_ban=it.don_gia)
            db.add(hh)
            db.flush()
            if db.query(TonKho).filter_by(hang_hoa_id=hh.id).first() is None:
                db.add(TonKho(hang_hoa_id=hh.id, so_luong=0))
        lines.append((hh.id, it.so_luong, it.don_gia, it.thue_suat))
    cu = {"so": dh.so, "khach_hang_id": dh.khach_hang_id,
          "tong_tien": float(dh.tong_tien or 0), "so_dong": len(dh.chi_tiet)}
    tien_hang, tien_thue = _tinh_don_hang(lines)
    dh.chi_tiet = [DonHangCt(hang_hoa_id=hid, so_luong=sl, don_gia=dg, thue_suat=ts)
                   for hid, sl, dg, ts in lines]
    dh.khach_hang_id = data.khach_hang_id
    if so:
        dh.so = so
    if data.ngay:
        dh.ngay = data.ngay
    dh.tong_tien = tien_hang
    dh.tien_thue = tien_thue
    ghi_audit(db, nd.id, "CAP_NHAT", "don_hang", dh.id, cu=cu,
              moi={"so": dh.so, "khach_hang_id": dh.khach_hang_id,
                   "tong_tien": float(tien_hang), "tien_thue": float(tien_thue),
                   "so_dong": len(lines)})
    db.commit(); db.refresh(dh)
    return dh


# ----- XUẤT KHO: liên thông Kho + tạo Hóa đơn + Công nợ (giao dịch nguyên tử) -----
@router.post("/don-hang/{dh_id}/xuat-kho")
def xuat_kho_don_hang(dh_id: int, db: Session = Depends(get_db),
                      nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    dh = db.get(DonHang, dh_id)
    if dh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn hàng")
    if dh.trang_thai == "DA_XUAT":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Đơn đã xuất kho")

    # 1) Phiếu xuất + trừ tồn qua service dùng chung (tự sinh yêu cầu mua nếu < min)
    phieu = PhieuKho(loai="XUAT", don_hang_id=dh.id, ngay=date.today(),
                     nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(phieu); db.flush()
    phieu.so = f"PX-{date.today():%Y%m%d}-{phieu.id}"
    canh_bao_ton = []
    for ct in dh.chi_tiet:
        db.add(PhieuKhoCt(phieu_kho_id=phieu.id, hang_hoa_id=ct.hang_hoa_id, so_luong=ct.so_luong))
        if xuat_ton(db, ct.hang_hoa_id, ct.so_luong):
            canh_bao_ton.append(ct.hang_hoa_id)

    # 2) Hóa đơn BAN (chừa sẵn chỗ nối HĐĐT) + 3) Công nợ phải thu (bàn giao Kế toán)
    # VAT theo từng dòng của đơn (dh.tien_thue). Đơn cũ chưa có VAT theo dòng thì
    # tien_thue đã được backfill = 8% (migration 49), vẫn giữ đúng hành vi trước đây.
    truoc_thue = Decimal(dh.tong_tien or 0)
    thue = Decimal(dh.tien_thue or 0)
    if thue == 0 and truoc_thue > 0:            # dữ liệu chưa có VAT → mặc định 8% như cũ
        thue = (truoc_thue * THUE_SUAT).quantize(Decimal("1"))
    hd = HoaDon(loai="BAN", don_hang_id=dh.id, ngay=date.today(),
                tien_truoc_thue=truoc_thue, tien_thue=thue, tong_tien=truoc_thue + thue,
                hddt_provider=None, hddt_trang_thai="CHUA_PHAT_HANH")
    db.add(hd); db.flush()
    cn = CongNo(loai="PHAI_THU", hoa_don_id=hd.id, khach_hang_id=dh.khach_hang_id,
                so_tien=hd.tong_tien, da_thanh_toan=0,
                han=date.today() + timedelta(days=30), trang_thai="CHUA_THU")
    db.add(cn)
    dh.trang_thai = "DA_XUAT"
    ghi_audit(db, nd.id, "XUAT", "don_hang", dh.id,
              moi={"phieu_xuat": phieu.id, "hoa_don": hd.id, "cong_no": float(hd.tong_tien)})
    db.commit()
    return {
        "don_hang_id": dh.id, "phieu_xuat": phieu.so,
        "hoa_don_id": hd.id, "tong_tien_hoa_don": float(hd.tong_tien),
        "cong_no_phai_thu": float(hd.tong_tien), "han_thu": str(cn.han),
        "canh_bao_ton_duoi_min": canh_bao_ton or None,
        "ghi_chu": "Hóa đơn chờ phát hành HĐĐT ở module Kế toán.",
    }
