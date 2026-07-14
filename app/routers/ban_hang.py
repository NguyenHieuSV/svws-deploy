"""
Module BÁN HÀNG — lát cắt dọc thứ tư, minh họa LIÊN THÔNG rõ nhất:
  báo giá -> duyệt (han_muc 'bao_gia') -> đơn hàng -> XUẤT KHO (gọi kho_service)
  -> lập HÓA ĐƠN (BAN) + CÔNG NỢ (PHẢI THU) [bàn giao Kế toán].
"""
from decimal import Decimal
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
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
    kh = KhachHang(ma=data.ma, ten=data.ten, ma_so_thue=data.ma_so_thue,
                   dien_thoai=data.dien_thoai, nguoi_lien_he=data.nguoi_lien_he,
                   email=data.email, phan_loai_abc=data.phan_loai_abc,
                   nguoi_phu_trach=nhan_vien_id_cua(db, nd.id))
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
    ghi_audit(db, nd.id, "SUA", "bao_gia_form", bgf.id, moi={"so": data.so})
    db.commit(); db.refresh(bgf)
    return bgf


class GuiBaoGiaVao(_BM):
    den: str
    tieu_de: str | None = None
    loi_nhan: str | None = None


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
    if "@" not in (data.den or ""):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email người nhận không hợp lệ")
    d = bgf.noi_dung or {}
    so = d.get("so") or bgf.so or f"BG-{bgf.id}"
    sub, vat, tong = tinh_bao_gia(d)
    mn = lambda n: f"{round(n):,}".replace(",", ".")

    # 1) Sinh PDF báo giá đính kèm
    ten_file = "Bao_gia_" + _re.sub(r"[^A-Za-z0-9._-]", "-", so) + ".pdf"
    pdf_path = _os.path.join(_tmp.gettempdir(), f"bgf_{bgf.id}_{ten_file}")
    dinh_kem = []
    try:
        tao_bao_gia_pdf(pdf_path, d,
                        font_path=_st.pdf_font_path, font_bold_path=_st.pdf_font_bold_path)
        dinh_kem = [{"duong_dan": pdf_path, "ten_file": ten_file}]
    except Exception:
        dinh_kem = []   # không chặn việc gửi thư nếu sinh PDF lỗi

    # 2) Nội dung thư — văn phong thương mại chuyên nghiệp
    khach = d.get("khach_ten") or "Quý công ty"
    mo_dau = (data.loi_nhan or "").strip() or (
        f"Công ty TNHH Giải pháp Kỹ thuật Sóng Việt trân trọng cảm ơn sự quan tâm của {khach}. "
        f"Chúng tôi hân hạnh gửi đến Quý công ty báo giá cho hạng mục nêu dưới đây.")
    L = [f"Kính gửi {khach},", "", mo_dau, "", "THÔNG TIN BÁO GIÁ:",
         f"   •  Số báo giá: {so} — ngày {d.get('ngay') or ''}"]
    if d.get("tieu_de"):
        L.append(f"   •  Hạng mục: {d.get('tieu_de')}")
    L.append(f"   •  Tổng giá trị (đã gồm VAT): {mn(tong)} VND")
    if d.get("hieu_luc"):
        L.append(f"   •  Hiệu lực báo giá: {d.get('hieu_luc')}")
    if dinh_kem:
        L.append(f"   •  Chi tiết đầy đủ: vui lòng xem tệp PDF đính kèm ({ten_file}).")
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
    tieu_de = data.tieu_de or f"[Sóng Việt] Báo giá {so}" + (f" — {khach}" if d.get("khach_ten") else "")

    try:
        kq = lay_email_provider().gui(data.den.strip(), tieu_de, "\n".join(L), dinh_kem=dinh_kem)
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
    # Lưu bản PDF vừa gửi vào kho tệp dùng chung trên máy chủ
    try:
        _luu_pdf_bao_gia(db, nd, bgf)
    except Exception:
        pass
    ghi_audit(db, nd.id, "GUI", "bao_gia_form", bgf.id,
              moi={"den": data.den, "gui_tu": kq.get("gui_tu"), "pdf": bool(dinh_kem)})
    db.commit()
    return {"gui_tu": kq.get("gui_tu"), "den": data.den, "pdf_dinh_kem": bool(dinh_kem),
            "trang_thai": kq.get("trang_thai"), "ghi_chu": kq.get("ghi_chu")}


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
        lines.append((hh.id, it.so_luong, it.don_gia))
    tong = sum(sl * dg for _, sl, dg in lines)
    dh = DonHang(so=so, khach_hang_id=data.khach_hang_id,
                 ngay=data.ngay or date.today(), tong_tien=tong, trang_thai="MOI")
    db.add(dh)
    db.flush()
    if not dh.so:
        dh.so = f"DH-{date.today():%Y%m%d}-{dh.id}"
    for hh_id, sl, dg in lines:
        db.add(DonHangCt(don_hang_id=dh.id, hang_hoa_id=hh_id, so_luong=sl, don_gia=dg))
    ghi_audit(db, nd.id, "TAO", "don_hang", dh.id,
              moi={"truc_tiep": True, "tong_tien": float(tong), "so_dong": len(lines),
                   "hang_moi": hang_moi[:20]})
    db.commit(); db.refresh(dh)
    return dh


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
    truoc_thue = dh.tong_tien
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
