"""
KẾ TOÁN — Quản lý tiền mặt (quỹ/sổ quỹ) + Phiếu thu/chi có DUYỆT NHIỀU CẤP,
tự hạch toán kép vào sổ cái, cấn trừ công nợ, và TRUY VẾT theo MÃ HÀNG BÁN.

Luồng phiếu: NHAP -> CHO_DUYET -> DA_DUYET (theo hạn mức loại 'thu_chi') / TU_CHOI / HUY.
Chỉ phiếu ĐÃ DUYỆT mới: chuyển tiền quỹ + sinh bút toán + cấn trừ công nợ.
"""
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..rbac import yeu_cau, kiem_han_muc, chi_vai_tro
from ..audit import ghi_audit
from ..deps import nhan_vien_id_cua
from ..models import (NguoiDung, TaiKhoanQuy, PhieuThuChi, ButToan, CongNo,
                      DonHang, DonMua, KhachHang, NhaCungCap, HoaDon)
from ..schemas import QuyVao, PhieuVao, DuyetPhieuVao, HoaDonVao, DatCocVao, DoanNhomVao
from ..hach_toan import hach_toan_hoa_don_ban, hach_toan_hoa_don_mua

router = APIRouter(prefix="/ke-toan", tags=["ke_toan_quy"])
MODULE = "ke_toan"
LOAI_DUYET = "thu_chi"

# Tên một số tài khoản để hiển thị cân đối phát sinh
TEN_TK = {
    "111": "Tiền mặt", "112": "Tiền gửi ngân hàng", "131": "Phải thu khách hàng",
    "331": "Phải trả người bán", "333": "Thuế phải nộp", "3331": "Thuế GTGT đầu ra",
    "511": "Doanh thu bán hàng", "632": "Giá vốn hàng bán", "642": "Chi phí QLDN",
    "627": "Chi phí sản xuất chung", "641": "Chi phí bán hàng", "711": "Thu nhập khác",
    "334": "Phải trả người lao động",
}


def _f(x):
    return float(x or 0)


# ---------- helpers ----------
def _quy_dict(q: TaiKhoanQuy):
    return {"id": q.id, "ma": q.ma, "ten": q.ten, "loai": q.loai, "so_tk": q.so_tk,
            "tk_ke_toan": q.tk_ke_toan, "so_du_dau": _f(q.so_du_dau), "so_du": _f(q.so_du)}


def _ten_doi_tac(db, p: PhieuThuChi):
    if p.khach_hang_id:
        kh = db.get(KhachHang, p.khach_hang_id)
        return kh.ten if kh else f"KH #{p.khach_hang_id}"
    if p.nha_cung_cap_id:
        nc = db.get(NhaCungCap, p.nha_cung_cap_id)
        return nc.ten if nc else f"NCC #{p.nha_cung_cap_id}"
    return None


def _ma_ban(db, don_hang_id):
    if not don_hang_id:
        return None
    dh = db.get(DonHang, don_hang_id)
    return (dh.so or f"DH-{dh.id}") if dh else None


def _phieu_dict(db, p: PhieuThuChi):
    q = db.get(TaiKhoanQuy, p.quy_id)
    return {"id": p.id, "so": p.so, "loai": p.loai, "ngay": str(p.ngay) if p.ngay else None,
            "quy_id": p.quy_id, "ten_quy": q.ten if q else None,
            "doi_tac_loai": p.doi_tac_loai, "ten_doi_tac": _ten_doi_tac(db, p),
            "khach_hang_id": p.khach_hang_id, "nha_cung_cap_id": p.nha_cung_cap_id,
            "so_tien": _f(p.so_tien), "dien_giai": p.dien_giai,
            "don_hang_id": p.don_hang_id, "ma_ban": _ma_ban(db, p.don_hang_id),
            "cong_no_id": p.cong_no_id, "tk_doi_ung": p.tk_doi_ung,
            "trang_thai": p.trang_thai, "but_toan_id": p.but_toan_id, "ghi_chu": p.ghi_chu,
            "la_tam_ung": bool(p.la_tam_ung), "da_can_tru": _f(p.da_can_tru),
            "con_lai_tam_ung": _f(p.so_tien) - _f(p.da_can_tru) if p.la_tam_ung else 0}


def _snapshot_so_quy(db, su_kien: str):
    """Ghi thêm số dư các quỹ tại thời điểm biến động vào MỘT file lũy kế
    So_quy_bien_dong.csv (Kho tệp dùng chung, nhóm "Sổ quỹ — CEO snapshot").
    Thời điểm là một cột; khối dòng mới nhất nằm TRÊN CÙNG. Lỗi snapshot không
    được làm hỏng nghiệp vụ chính."""
    try:
        from ..models import TepDinhKem
        from .. import luu_tru
        from ..nhac_viec_service import gio_hien_tai
        luc = gio_hien_tai()
        TEN = "So_quy_bien_dong.csv"
        HEADER = "\ufeffThời điểm,Sự kiện,Mã quỹ,Tên quỹ,Loại,Số dư đầu kỳ,Số dư tại thời điểm"

        def _c(v):
            return '"' + str(v if v is not None else "").replace('"', '""') + '"'

        ts = luc.strftime("%Y-%m-%d %H:%M:%S")
        moi = []
        tong = 0.0
        for q in db.query(TaiKhoanQuy).order_by(TaiKhoanQuy.id).all():
            tong += _f(q.so_du)
            moi.append(",".join([ts, _c(su_kien), _c(q.ma), _c(q.ten), _c(q.loai),
                                 str(_f(q.so_du_dau)), str(_f(q.so_du))]))
        moi.append(",".join([ts, _c(su_kien), "TONG", _c("TỔNG TẤT CẢ QUỸ"), "", "", str(tong)]))

        cu = []
        t_cu = db.query(TepDinhKem).filter_by(doi_tuong="SO_QUY", ten_file=TEN).first()
        if t_cu is not None:
            try:
                lines = luu_tru.doc(t_cu.duong_dan).decode("utf-8").splitlines()
                cu = [l for l in lines[1:] if l.strip()][:20000]   # giữ tối đa 20.000 dòng gần nhất
            except Exception:
                cu = []
            luu_tru.xoa(t_cu.duong_dan)
            db.delete(t_cu)
            db.flush()
        data = "\n".join([HEADER] + moi + cu).encode("utf-8")
        ref = luu_tru.luu(data, "so_quy", "bien_dong", TEN, "text/csv")
        t = TepDinhKem(doi_tuong="SO_QUY", doi_tuong_id=0, loai=(su_kien or "SNAPSHOT")[:20],
                       ten_file=TEN, duong_dan=ref, kich_thuoc=len(data), content_type="text/csv")
        db.add(t)
        return t
    except Exception:
        return None


# ---------- QUỸ TIỀN ----------
@router.get("/quy")
def ds_quy(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return [_quy_dict(q) for q in db.query(TaiKhoanQuy).order_by(TaiKhoanQuy.id).all()]


@router.post("/quy", status_code=201)
def tao_quy(data: QuyVao, db: Session = Depends(get_db),
            nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if data.ma:
        # Người dùng tự nhập mã → mã trùng là lỗi thật.
        ma = data.ma
        if db.query(TaiKhoanQuy).filter_by(ma=ma).first():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mã quỹ đã tồn tại")
    else:
        # Tự sinh mã theo ngày; nếu đã có quỹ tạo trong cùng ngày thì thêm hậu tố
        # -2, -3… để không bao giờ trùng (trước đây tạo quỹ thứ 2 cùng ngày bị lỗi).
        base = "Q" + date.today().strftime("%y%m%d")
        ma = base
        seq = 1
        while db.query(TaiKhoanQuy).filter_by(ma=ma).first():
            seq += 1
            ma = f"{base}-{seq}"
    q = TaiKhoanQuy(ma=ma, ten=data.ten, loai=data.loai, so_tk=data.so_tk,
                    tk_ke_toan=data.tk_ke_toan, so_du_dau=data.so_du_dau, so_du=data.so_du_dau)
    db.add(q); db.flush()
    ghi_audit(db, nd.id, "TAO", "tai_khoan_quy", q.id, moi={"ma": ma})
    _snapshot_so_quy(db, "TAO QUY " + ma)
    db.commit(); db.refresh(q)
    return _quy_dict(q)


@router.put("/quy/{quy_id}")
def sua_quy(quy_id: int, data: QuyVao, db: Session = Depends(get_db),
            nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT"))):
    """Sửa quỹ: tên, loại, số TK, TK kế toán, số dư đầu — số dư hiện tại tự điều
    chỉnh theo chênh lệch số dư đầu (các phiếu đã duyệt giữ nguyên)."""
    q = db.get(TaiKhoanQuy, quy_id)
    if q is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy quỹ")
    if data.loai not in ("TIEN_MAT", "NGAN_HANG"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Loại phải là TIEN_MAT hoặc NGAN_HANG")
    if not (data.ten or "").strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nhập tên quỹ")
    cu = {"ten": q.ten, "loai": q.loai, "so_tk": q.so_tk,
          "so_du_dau": _f(q.so_du_dau), "so_du": _f(q.so_du)}
    delta = Decimal(data.so_du_dau or 0) - Decimal(q.so_du_dau or 0)
    q.ten = data.ten.strip()[:120]
    q.loai = data.loai
    q.so_tk = (data.so_tk or "").strip()[:40] or None
    q.tk_ke_toan = data.tk_ke_toan or ("112" if data.loai == "NGAN_HANG" else "111")
    q.so_du_dau = Decimal(data.so_du_dau or 0)
    q.so_du = Decimal(q.so_du or 0) + delta
    ghi_audit(db, nd.id, "SUA", "tai_khoan_quy", q.id, cu=cu,
              moi={"ten": q.ten, "loai": q.loai, "so_tk": q.so_tk,
                   "so_du_dau": _f(q.so_du_dau), "so_du": _f(q.so_du)})
    _snapshot_so_quy(db, "SUA QUY " + (q.ma or ""))
    db.commit(); db.refresh(q)
    return _quy_dict(q)


@router.post("/so-quy-snapshot")
def chup_so_quy(db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "XEM"))):
    """CEO bấm chụp thủ công một bản snapshot sổ quỹ ngay bây giờ."""
    t = _snapshot_so_quy(db, "THU CONG")
    if t is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Không chụp được snapshot")
    ghi_audit(db, nd.id, "SNAPSHOT", "so_quy", 0, moi={"tep": t.ten_file})
    db.commit()
    return {"ok": True, "tep": t.ten_file}


@router.get("/quy/{quy_id}/so-quy")
def so_quy(quy_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Sổ quỹ: số dư đầu + các phiếu ĐÃ DUYỆT (thu +, chi −) với số dư lũy kế."""
    q = db.get(TaiKhoanQuy, quy_id)
    if q is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy quỹ")
    ps = (db.query(PhieuThuChi)
          .filter(PhieuThuChi.quy_id == quy_id, PhieuThuChi.trang_thai == "DA_DUYET")
          .order_by(PhieuThuChi.ngay, PhieuThuChi.id).all())
    dong = []
    sd = Decimal(q.so_du_dau or 0)
    for p in ps:
        delta = Decimal(p.so_tien) if p.loai == "THU" else -Decimal(p.so_tien)
        sd += delta
        dong.append({"id": p.id, "so": p.so, "ngay": str(p.ngay), "loai": p.loai,
                     "dien_giai": p.dien_giai or "", "ten_doi_tac": _ten_doi_tac(db, p),
                     "ma_ban": _ma_ban(db, p.don_hang_id),
                     "thu": _f(p.so_tien) if p.loai == "THU" else 0,
                     "chi": _f(p.so_tien) if p.loai == "CHI" else 0,
                     "so_du": _f(sd)})
    return {"quy": _quy_dict(q), "so_du_dau": _f(q.so_du_dau), "so_du_cuoi": _f(sd), "dong": dong}


# ---------- CÔNG NỢ ĐANG MỞ (để cấn trừ khi lập phiếu) ----------
@router.get("/cong-no-mo")
def cong_no_mo(loai: str | None = None, db: Session = Depends(get_db),
               _=Depends(yeu_cau(MODULE, "XEM"))):
    """Danh sách công nợ CHƯA tất toán, kèm tên đối tác — dùng cho ô cấn trừ phiếu.
    loai = PHAI_THU (nợ khách hàng) | PHAI_TRA (nợ nhà cung cấp)."""
    q = db.query(CongNo).filter(CongNo.so_tien > CongNo.da_thanh_toan)
    if loai:
        q = q.filter(CongNo.loai == loai)
    today = date.today()
    out = []
    for cn in q.order_by(CongNo.han, CongNo.id).all():
        con = float(cn.so_tien) - float(cn.da_thanh_toan)
        if cn.loai == "PHAI_THU":
            kh = db.get(KhachHang, cn.khach_hang_id) if cn.khach_hang_id else None
            ten, dtl, dtid = (kh.ten if kh else "Khách lẻ"), "KH", cn.khach_hang_id
        else:
            nc = db.get(NhaCungCap, cn.nha_cung_cap_id) if cn.nha_cung_cap_id else None
            ten, dtl, dtid = (nc.ten if nc else "NCC"), "NCC", cn.nha_cung_cap_id
        out.append({"id": cn.id, "loai": cn.loai, "doi_tac_loai": dtl, "doi_tac_id": dtid,
                    "ten_doi_tac": ten, "so_tien": _f(cn.so_tien),
                    "da_thanh_toan": _f(cn.da_thanh_toan), "con_lai": con,
                    "han": str(cn.han) if cn.han else None,
                    "qua_han": bool(cn.han and cn.han < today and con > 0)})
    return out


# ---------- PHIẾU THU / CHI ----------
@router.get("/phieu")
def ds_phieu(trang_thai: str | None = None, loai: str | None = None,
             don_hang_id: int | None = None, db: Session = Depends(get_db),
             _=Depends(yeu_cau(MODULE, "XEM"))):
    q = db.query(PhieuThuChi)
    if trang_thai:
        q = q.filter(PhieuThuChi.trang_thai == trang_thai)
    if loai:
        q = q.filter(PhieuThuChi.loai == loai)
    if don_hang_id:
        q = q.filter(PhieuThuChi.don_hang_id == don_hang_id)
    return [_phieu_dict(db, p) for p in q.order_by(PhieuThuChi.id.desc()).all()]


@router.post("/phieu", status_code=201)
def tao_phieu(data: PhieuVao, db: Session = Depends(get_db),
              nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if data.loai not in ("THU", "CHI"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Loại phiếu phải là THU hoặc CHI")
    quy = db.get(TaiKhoanQuy, data.quy_id)
    if quy is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy quỹ")
    # kiểm tra cấn trừ công nợ (đúng loại + không vượt số còn lại)
    kh_id, ncc_id = data.khach_hang_id, data.nha_cung_cap_id
    # TỰ LIÊN KẾT: phiếu THU gắn mã hàng bán mà chưa chọn khách → lấy khách của đơn hàng
    if data.loai == "THU" and not kh_id and data.don_hang_id and not data.la_tam_ung:
        _dh0 = db.get(DonHang, data.don_hang_id)
        if _dh0 is not None:
            kh_id = _dh0.khach_hang_id
    if data.la_tam_ung:
        # TẠM ỨNG / TRẢ TRƯỚC: chưa có hóa đơn → bắt buộc gắn mã hàng bán, không cấn trừ công nợ
        if not data.don_hang_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "Khoản tạm ứng/trả trước phải gắn mã hàng bán (đơn hàng).")
        dh = db.get(DonHang, data.don_hang_id)
        if data.loai == "THU":
            kh_id = kh_id or (dh.khach_hang_id if dh else None)
            if not kh_id:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tạm ứng thu cần khách hàng (theo đơn hàng).")
        else:
            if not ncc_id:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Trả trước cần nhà cung cấp.")
        data.cong_no_id = None
    if data.cong_no_id:
        cn = db.get(CongNo, data.cong_no_id)
        if cn is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy công nợ")
        if data.loai == "THU" and cn.loai != "PHAI_THU":
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "Phiếu THU chỉ cấn trừ công nợ PHẢI THU (của khách hàng).")
        if data.loai == "CHI" and cn.loai != "PHAI_TRA":
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "Phiếu CHI chỉ cấn trừ công nợ PHẢI TRẢ (cho nhà cung cấp).")
        con_lai = Decimal(cn.so_tien) - Decimal(cn.da_thanh_toan)
        if con_lai <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Khoản công nợ này đã tất toán.")
        if data.so_tien > con_lai:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Vượt số công nợ còn lại ({con_lai:.0f})")
        # tự gán đối tác theo công nợ để hồ sơ phiếu khớp đối tác
        kh_id = kh_id or cn.khach_hang_id
        ncc_id = ncc_id or cn.nha_cung_cap_id
    doi_tac = data.doi_tac_loai or ("KH" if kh_id else ("NCC" if ncc_id else "KHAC"))
    p = PhieuThuChi(loai=data.loai, quy_id=data.quy_id, ngay=data.ngay or date.today(),
                    doi_tac_loai=doi_tac, khach_hang_id=kh_id,
                    nha_cung_cap_id=ncc_id, so_tien=data.so_tien,
                    dien_giai=data.dien_giai, don_hang_id=data.don_hang_id,
                    cong_no_id=data.cong_no_id, tk_doi_ung=data.tk_doi_ung,
                    trang_thai="CHO_DUYET" if data.trinh_luon else "NHAP",
                    nguoi_tao=nhan_vien_id_cua(db, nd.id), ghi_chu=data.ghi_chu,
                    la_tam_ung=bool(data.la_tam_ung))
    db.add(p); db.flush()
    p.so = f"{'PT' if p.loai == 'THU' else 'PC'}-{date.today():%Y%m%d}-{p.id}"
    ghi_audit(db, nd.id, "TAO", "phieu_thu_chi", p.id, moi={"so": p.so, "so_tien": _f(p.so_tien)})
    db.commit(); db.refresh(p)
    return _phieu_dict(db, p)


@router.post("/phieu/{pid}/trinh")
def trinh_phieu(pid: int, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    p = db.get(PhieuThuChi, pid)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiếu")
    if p.trang_thai != "NHAP":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chỉ trình được phiếu ở trạng thái NHÁP")
    p.trang_thai = "CHO_DUYET"
    ghi_audit(db, nd.id, "TRINH", "phieu_thu_chi", p.id)
    db.commit(); db.refresh(p)
    return _phieu_dict(db, p)


def _hach_toan_phieu(db, p: PhieuThuChi):
    quy = db.query(TaiKhoanQuy).filter_by(id=p.quy_id).with_for_update().first()
    # ✅ KIỂM LẠI TẠI THỜI ĐIỂM DUYỆT (khóa hàng chống race / chống cấn vượt):
    if p.cong_no_id:
        cn0k = db.query(CongNo).filter_by(id=p.cong_no_id).with_for_update().first()
        if cn0k is not None:
            con_lai0 = Decimal(cn0k.so_tien or 0) - Decimal(cn0k.da_thanh_toan or 0)
            if Decimal(p.so_tien) > con_lai0:
                raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                    f"Phiếu {p.so or p.id}: số tiền vượt phần còn lại hiện tại của công nợ "
                                    f"({float(con_lai0):,.0f}đ) — khoản này có thể đã được thu/chi ở phiếu/lệnh khác")
    if p.loai == "CHI" and Decimal(quy.so_du or 0) < Decimal(p.so_tien):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Số dư quỹ '{quy.ten}' ({float(quy.so_du or 0):,.0f}đ) không đủ chi "
                            f"{float(p.so_tien):,.0f}đ — nạp/điều chuyển quỹ trước khi duyệt")
    if p.tk_doi_ung:
        tk_du = p.tk_doi_ung
    elif p.la_tam_ung:
        tk_du = "131" if p.loai == "THU" else "331"   # KH trả trước / trả trước NCC
    elif p.cong_no_id:
        cn0 = db.get(CongNo, p.cong_no_id)
        tk_du = "131" if (cn0 and cn0.loai == "PHAI_THU") else "331"
    elif p.loai == "THU":
        tk_du = "131" if p.khach_hang_id else "711"
    else:
        tk_du = "331" if p.nha_cung_cap_id else "642"
    if p.loai == "THU":
        tk_no, tk_co = quy.tk_ke_toan, tk_du
        quy.so_du = Decimal(quy.so_du) + Decimal(p.so_tien)
    else:
        tk_no, tk_co = tk_du, quy.tk_ke_toan
        quy.so_du = Decimal(quy.so_du) - Decimal(p.so_tien)
    bt = ButToan(ngay=p.ngay, tk_no=tk_no, tk_co=tk_co, so_tien=p.so_tien,
                 dien_giai=p.dien_giai or (("Thu" if p.loai == "THU" else "Chi") + f" {p.so}"),
                 don_hang_id=p.don_hang_id, quy_id=quy.id, nguon="PHIEU", nguon_id=p.id)
    db.add(bt); db.flush()
    p.but_toan_id = bt.id
    # cấn trừ công nợ
    if p.cong_no_id:
        cn = db.get(CongNo, p.cong_no_id)
        if cn is not None:
            cn.da_thanh_toan = Decimal(cn.da_thanh_toan) + Decimal(p.so_tien)
            du = Decimal(cn.da_thanh_toan) >= Decimal(cn.so_tien)
            if cn.loai == "PHAI_THU":
                cn.trang_thai = "THU_DU" if du else "THU_MOT_PHAN"
            else:
                cn.trang_thai = "DA_TRA" if du else "TRA_MOT_PHAN"
    return bt


@router.post("/phieu/{pid}/duyet")
def duyet_phieu(pid: int, data: DuyetPhieuVao = DuyetPhieuVao(),
                db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "DUYET"))):
    p = db.query(PhieuThuChi).filter_by(id=pid).with_for_update().first()
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiếu")
    if p.trang_thai not in ("CHO_DUYET", "NHAP"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Phiếu không ở trạng thái chờ duyệt")
    # DUYỆT THEO HẠN MỨC NHIỀU CẤP (bảng han_muc_duyet, loại 'thu_chi')
    kiem_han_muc(db, nd, LOAI_DUYET, Decimal(p.so_tien))
    bt = _hach_toan_phieu(db, p)
    p.trang_thai = "DA_DUYET"
    p.nguoi_duyet = nhan_vien_id_cua(db, nd.id)
    p.ngay_duyet = date.today()
    if data.ghi_chu:
        p.ghi_chu = (p.ghi_chu or "") + f" | Duyệt: {data.ghi_chu}"
    ghi_audit(db, nd.id, "DUYET", "phieu_thu_chi", p.id,
              moi={"but_toan": bt.id, "tk_no": bt.tk_no, "tk_co": bt.tk_co})
    _snapshot_so_quy(db, "DUYET " + (p.so or f"PC-{p.id}"))
    from ..fin_snapshot import snapshot_financial
    snapshot_financial(db, "DUYET " + (p.so or f"PC-{p.id}"))
    db.commit(); db.refresh(p)
    return _phieu_dict(db, p)


@router.post("/phieu/{pid}/tu-choi")
def tu_choi_phieu(pid: int, data: DuyetPhieuVao = DuyetPhieuVao(),
                  db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "DUYET"))):
    p = db.get(PhieuThuChi, pid)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiếu")
    if p.trang_thai not in ("CHO_DUYET", "NHAP"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Phiếu không ở trạng thái chờ duyệt")
    p.trang_thai = "TU_CHOI"
    if data.ghi_chu:
        p.ghi_chu = (p.ghi_chu or "") + f" | Từ chối: {data.ghi_chu}"
    ghi_audit(db, nd.id, "TU_CHOI", "phieu_thu_chi", p.id)
    db.commit(); db.refresh(p)
    return _phieu_dict(db, p)


@router.post("/phieu/{pid}/huy")
def huy_phieu(pid: int, db: Session = Depends(get_db),
              nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    p = db.get(PhieuThuChi, pid)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiếu")
    if p.trang_thai not in ("NHAP", "CHO_DUYET"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chỉ hủy được phiếu NHÁP/CHỜ DUYỆT")
    nv_toi = nhan_vien_id_cua(db, nd.id)
    if nd.vai_tro not in ("CEO", "ADMIN", "KTT") and getattr(p, "nguoi_tao", None) not in (None, nv_toi):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Chỉ người lập phiếu (hoặc KTT/CEO/ADMIN) mới hủy được phiếu này")
    p.trang_thai = "HUY"
    ghi_audit(db, nd.id, "HUY", "phieu_thu_chi", p.id)
    db.commit(); db.refresh(p)
    return _phieu_dict(db, p)


# ---------- DUYET: xóa phiếu thu/chi (chỉ phiếu CHƯA DUYỆT) ----------
@router.delete("/phieu/{pid}")
def xoa_phieu(pid: int, db: Session = Depends(get_db),
              nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    p = db.get(PhieuThuChi, pid)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiếu")
    if p.trang_thai == "DA_DUYET":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Phiếu '{p.so or pid}' ĐÃ DUYỆT (đã chuyển tiền quỹ, sinh bút toán) — không thể xóa để giữ vết kế toán.")
    so_cu = p.so
    ghi_audit(db, nd.id, "XOA", "phieu_thu_chi", pid,
              cu={"so": so_cu, "loai": p.loai, "so_tien": _f(p.so_tien), "trang_thai": p.trang_thai})
    db.delete(p)
    db.commit()
    return {"ok": True, "so": so_cu}


# ---------- DUYET: xóa quỹ (chỉ quỹ chưa có phiếu/bút toán) ----------
@router.delete("/quy/{quy_id}")
def xoa_quy(quy_id: int, db: Session = Depends(get_db),
            nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    q = db.get(TaiKhoanQuy, quy_id)
    if q is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy quỹ")
    so_phieu = db.query(func.count(PhieuThuChi.id)).filter_by(quy_id=quy_id).scalar() or 0
    so_bt = db.query(func.count(ButToan.id)).filter_by(quy_id=quy_id).scalar() or 0
    if so_phieu or so_bt:
        chi_tiet = ", ".join(x for x in
                             ([f"{so_phieu} phiếu thu/chi"] if so_phieu else []) +
                             ([f"{so_bt} bút toán"] if so_bt else []))
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Quỹ '{q.ten}' đang gắn với {chi_tiet} — không thể xóa để giữ vết kế toán.")
    ten_cu = q.ten
    ghi_audit(db, nd.id, "XOA", "tai_khoan_quy", quy_id,
              cu={"ma": q.ma, "ten": ten_cu, "so_du": _f(q.so_du)})
    db.delete(q)
    db.commit()
    return {"ok": True, "ten": ten_cu}


# ---------- DUYET: xóa hóa đơn (chưa phát hành HĐĐT, chưa thu/trả tiền) ----------
@router.delete("/hoa-don/{hd_id}")
def xoa_hoa_don(hd_id: int, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """Hủy hóa đơn ghi nhận nhầm: xóa kèm công nợ và bút toán do chính hóa đơn
    sinh ra. Chặn khi đã phát hành HĐĐT hoặc công nợ đã thu/trả một phần."""
    hd = db.get(HoaDon, hd_id)
    if hd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hóa đơn")
    if hd.hddt_trang_thai == "DA_PHAT_HANH":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Hóa đơn '{hd.so}' đã phát hành HĐĐT — không thể xóa. Cần lập hóa đơn điều chỉnh/thay thế theo quy định.")
    cns = db.query(CongNo).filter_by(hoa_don_id=hd_id).all()
    if any(_f(cn.da_thanh_toan) > 0 for cn in cns):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Công nợ của hóa đơn '{hd.so}' đã thu/trả một phần — không thể xóa để giữ vết kế toán.")
    cn_ids = [cn.id for cn in cns]
    if cn_ids:
        so_p = db.query(func.count(PhieuThuChi.id)).filter(PhieuThuChi.cong_no_id.in_(cn_ids)).scalar() or 0
        if so_p:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Hóa đơn '{hd.so}' có {so_p} phiếu thu/chi gắn công nợ — không thể xóa để giữ vết kế toán.")
    so_cu = hd.so
    so_bt = db.query(ButToan).filter_by(hoa_don_id=hd_id).delete()
    for cn in cns:
        db.delete(cn)
    ghi_audit(db, nd.id, "XOA", "hoa_don", hd_id,
              cu={"so": so_cu, "loai": hd.loai, "tong_tien": _f(hd.tong_tien),
                  "so_cong_no": len(cns), "so_but_toan": so_bt})
    db.delete(hd)
    db.commit()
    return {"ok": True, "so": so_cu}


# ---------- TỔNG QUAN ----------
@router.get("/tong-quan")
def tong_quan(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    tong_quy = _f(db.query(func.coalesce(func.sum(TaiKhoanQuy.so_du), 0)).scalar())
    pt = _f(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
            .filter(CongNo.loai == "PHAI_THU").scalar())
    ptr = _f(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
             .filter(CongNo.loai == "PHAI_TRA").scalar())
    cho_duyet = db.query(func.count(PhieuThuChi.id)).filter(PhieuThuChi.trang_thai == "CHO_DUYET").scalar()
    hd_chua_ht = db.query(func.count(HoaDon.id)).filter(HoaDon.da_hach_toan.is_(False)).scalar()
    hd_mua_chua_ht = db.query(func.count(HoaDon.id)) \
        .filter(HoaDon.da_hach_toan.is_(False), HoaDon.loai == "MUA").scalar()
    return {"tong_quy": tong_quy, "phai_thu": pt, "phai_tra": ptr,
            "phieu_cho_duyet": int(cho_duyet or 0),
            "hoa_don_chua_hach_toan": int(hd_chua_ht or 0),
            "hoa_don_mua_chua_hach_toan": int(hd_mua_chua_ht or 0),
            "quy": [_quy_dict(q) for q in db.query(TaiKhoanQuy).order_by(TaiKhoanQuy.id).all()]}


# ---------- THỐNG KÊ THU–CHI (dòng tiền) ----------
def _kd_vn(s: str) -> str:
    """Bỏ dấu tiếng Việt + thường hóa — để nhận diện diễn giải gõ có dấu lẫn không dấu."""
    import unicodedata
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


@router.get("/thong-ke-thu-chi")
def thong_ke_thu_chi(tu_ngay: str | None = None, den_ngay: str | None = None,
                     quy_id: int | None = None, don_hang_id: int | None = None,
                     db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Thống kê dòng tiền thu/chi (phiếu ĐÃ DUYỆT): theo kỳ (tháng), theo loại tài khoản
    đối ứng, theo quỹ, và theo mã hàng bán (kiểm soát tiền dự án)."""
    q = db.query(PhieuThuChi).filter(PhieuThuChi.trang_thai == "DA_DUYET")
    if tu_ngay:
        q = q.filter(PhieuThuChi.ngay >= tu_ngay)
    if den_ngay:
        q = q.filter(PhieuThuChi.ngay <= den_ngay)
    if quy_id:
        q = q.filter(PhieuThuChi.quy_id == quy_id)
    if don_hang_id:
        q = q.filter(PhieuThuChi.don_hang_id == don_hang_id)
    rows = q.all()

    tong_thu = tong_chi = 0.0
    thang, loai, quy, maban = {}, {}, {}, {}
    quy_ten = {x.id: x.ten for x in db.query(TaiKhoanQuy).all()}
    for p in rows:
        amt = _f(p.so_tien)
        bt = db.get(ButToan, p.but_toan_id) if p.but_toan_id else None
        off = (bt.tk_co if p.loai == "THU" else bt.tk_no) if bt else \
            (p.tk_doi_ung or ("131" if p.loai == "THU" else "642"))
        ky = p.ngay.strftime("%Y-%m") if p.ngay else "—"
        mb = _ma_ban(db, p.don_hang_id) or "(không gắn)"
        for d, k in ((thang, ky), (loai, off), (quy, p.quy_id), (maban, mb)):
            g = d.setdefault(k, {"thu": 0.0, "chi": 0.0})
            g["thu" if p.loai == "THU" else "chi"] += amt
        if p.loai == "THU":
            tong_thu += amt
        else:
            tong_chi += amt
        # 🔗 TỰ LIÊN KẾT chi tiết từng khoản: Đối tác (NCC/Khách) + Số hóa đơn
        import re as _re
        from ..models import CongNo as _CN, NhaCungCap as _NCC, KhachHang as _KH, DonHang as _DH
        cn0 = db.get(_CN, p.cong_no_id) if p.cong_no_id else None
        so_hd = cn0.so_ct if cn0 else None
        if not so_hd and p.dien_giai:                     # phiếu từ lệnh bank: số HĐ nằm trong diễn giải
            m2 = _re.search(r"HĐ\s*([A-Za-z0-9\-/\.]+)", p.dien_giai)
            if m2:
                so_hd = m2.group(1)
        doi_tac = None
        if p.loai == "CHI":
            _nid = p.nha_cung_cap_id or (cn0.nha_cung_cap_id if cn0 else None)
            if _nid:
                _x = db.get(_NCC, _nid)
                doi_tac = _x.ten if _x else None
        else:
            _kid = p.khach_hang_id or (cn0.khach_hang_id if cn0 else None)
            if not _kid and p.don_hang_id:
                _d2 = db.get(_DH, p.don_hang_id)
                _kid = _d2.khach_hang_id if _d2 else None
            if _kid:
                _x = db.get(_KH, _kid)
                doi_tac = _x.ten if _x else None
        canh_bao = None
        if doi_tac is None:
            # 🔁 TỰ NHẬN DIỆN giao dịch nội bộ (không có đối tác ngoài)
            _dg = _kd_vn(p.dien_giai or "")
            _qn = quy_ten.get(p.quy_id, "")
            if off == "113" or "chuyen tien noi bo" in _dg or "chuyen tien sang so quy" in _dg \
                    or "nhan tien chuyen" in _dg:
                doi_tac = f"🔁 Chuyển nội bộ ({_qn})"
                if off not in ("113", "111", "112"):
                    canh_bao = f"Chuyển nội bộ nên dùng TK 113 (tiền đang chuyển) — đang ghi TK {off}: làm phồng thu nhập/chi phí"
            elif ("rut tien" in _dg or "nop tien" in _dg) and "quy" in _dg:
                doi_tac = f"🏦 Nộp / rút tiền giữa quỹ ({_qn})"
                if off not in ("111", "112", "113"):
                    canh_bao = f"Nộp/rút giữa quỹ nên dùng TK 111/112 — đang ghi TK {off}: làm phồng thu nhập/chi phí"
            elif "phi chuyen" in _dg or "phi ngan hang" in _dg or "phi giao dich" in _dg:
                doi_tac = f"🏦 Phí ngân hàng ({_qn})"
        maban[mb].setdefault("ct", []).append({
            "pid": p.id,
            "ngay": str(p.ngay) if p.ngay else None, "so": p.so, "loai": p.loai,
            "so_tien": amt, "doi_tac": doi_tac, "so_hd": so_hd, "tk": off,
            "canh_bao": canh_bao, "dien_giai": (p.dien_giai or "")[:90]})

    def _net(d):
        return {k: {**v, "rong": v["thu"] - v["chi"]} for k, v in d.items()}

    theo_thang = [{"ky": k, **v, "rong": v["thu"] - v["chi"]}
                  for k, v in sorted(thang.items())]
    theo_loai = sorted([{"tk": k, "ten_tk": TEN_TK.get(k, ""), **v} for k, v in loai.items()],
                       key=lambda x: -(x["thu"] + x["chi"]))
    theo_quy = [{"quy": quy_ten.get(k, f"Quỹ {k}"), **v} for k, v in quy.items()]
    theo_ma_ban = sorted([{"ma_ban": k, **v, "rong": v["thu"] - v["chi"]}
                          for k, v in maban.items()], key=lambda x: -(x["thu"] + x["chi"]))
    return {"tu_ngay": tu_ngay, "den_ngay": den_ngay, "so_phieu": len(rows),
            "tong_thu": tong_thu, "tong_chi": tong_chi, "rong": tong_thu - tong_chi,
            "theo_thang": theo_thang, "theo_loai": theo_loai,
            "theo_quy": theo_quy, "theo_ma_ban": theo_ma_ban}


def _rut_link_tra_cuu(nd):
    """Tìm link tra cứu HĐĐT + mã tra cứu trong thân thư (MISA meInvoice/VNPT/Viettel…)."""
    import re as _re
    nd = nd or ""
    url = None
    for u in _re.findall(r"https?://[^\s<>\"')\]]+", nd):
        if _re.search(r"tra-?cuu|invoice|hoa-?don|hddt", u, _re.I):
            url = u.rstrip(".,;")[:300]
            break
    ma = None
    m2 = _re.search(r"m[ãa]\s*(?:s[ốo](?!\s*thu[ếe])|tra\s*c[ứu]u)\s*[:：]?\s*([A-Za-z0-9_\-]{6,30})",
                    nd, _re.I)
    if m2:
        ma = m2.group(1)[:40]
    return url, ma


def _rut_ngay_hd(nd):
    """Bắt 'Ngày: dd/mm/yyyy' trong thân thư thông báo HĐĐT."""
    import re as _re
    m2 = _re.search(r"Ng[àa]y[^0-9]{0,5}(\d{1,2})[/-](\d{1,2})[/-](\d{4})", nd or "", _re.I)
    if not m2:
        return None
    try:
        return date(int(m2.group(3)), int(m2.group(2)), int(m2.group(1)))
    except Exception:
        return None


# --- 🏢 Tự khớp hồ sơ NCC theo tên AI đọc / tên miền email ---
_DOMAIN_CHUNG = {"gmail.com", "googlemail.com", "yahoo.com", "yahoo.com.vn",
                 "hotmail.com", "outlook.com", "icloud.com", "watersolutions.company"}


def _ten_goc_ncc(s):
    """Chuẩn hóa tên NCC: bỏ dấu, bỏ từ pháp lý (Công ty CP/TNHH/SX-TM…) để so khớp."""
    import unicodedata
    import re as _re
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D").lower()
    s = _re.sub(r"[^a-z0-9 ]", " ", s)
    s = _re.sub(r"\b(trach nhiem huu han|mot thanh vien|cong ty|co phan|thuong mai|"
                r"san xuat|dich vu|xay dung|cty|tnhh|mtv|cp|sx|tm|dv|xd|va)\b", " ", s)
    return " ".join(s.split())


def _khop_ncc(ds_ncc, ten_ai, email=None):
    """Tìm NCC trong hồ sơ khớp tên AI đọc (đã bỏ dấu + từ pháp lý) hoặc tên miền
    email riêng của NCC. Trả về id hoặc None; ds_ncc = list NhaCungCap query sẵn."""
    dom = (email or "").split("@")[-1].strip().lower()
    if dom and "." in dom and dom not in _DOMAIN_CHUNG:
        for n in ds_ncc:
            if (n.email or "").split("@")[-1].strip().lower() == dom:
                return n.id
    goc = _ten_goc_ncc(ten_ai)
    if len(goc) < 4:
        return None
    tot, tot_diem = None, 0
    w1 = set(goc.split())
    for n in ds_ncc:
        g2 = _ten_goc_ncc(n.ten)
        if len(g2) < 4:
            continue
        if g2 == goc:
            return n.id
        w2 = set(g2.split())
        # khớp khi 1 tên chứa tên kia (chuỗi), hoặc tập từ tên ngắn nằm trọn trong tên dài
        khop = (g2 in goc) or (goc in g2) or (len(w1 & w2) >= 2 and (w1 <= w2 or w2 <= w1))
        if khop:
            diem = len(" ".join(w1 & w2))
            if diem > tot_diem:
                tot, tot_diem = n.id, diem
    return tot


# ============ 📥 HÓA ĐƠN MUA TỪ EMAIL — chờ xác nhận trước khi vào bảng Hóa đơn ============
@router.post("/hoa-don-cho/quet")
def quet_hoa_don_mua_email(tu_ngay: date | None = None, db: Session = Depends(get_db),
                           nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """🤖 Quét hộp thư công ty: thư hóa đơn của NCC (email trùng hồ sơ NCC / danh bạ dự án,
    hoặc tiêu đề có chữ hóa đơn/invoice) được AI đọc (cả PDF đính kèm) → hàng CHỜ XÁC NHẬN."""
    from ..inbound_gateway import lay_inbound_provider
    from ..ai_gateway import doc_hoa_don_email, doc_hoa_don_tep
    from ..models import KtHoaDonCho, NhaCungCap, CtNccEmail
    from ..nhac_viec_service import gio_hien_tai
    from .cho_thue_ops import _rut_hd_email
    from datetime import timedelta as _td
    import unicodedata

    def _kd2(s2):
        s2 = unicodedata.normalize("NFD", s2 or "")
        s2 = "".join(c for c in s2 if unicodedata.category(c) != "Mn")
        return s2.replace("đ", "d").replace("Đ", "D").lower()

    prov = lay_inbound_provider()
    moc = tu_ngay or (date.today() - _td(days=30))
    try:
        thu = prov.lay_thu(moc) if hasattr(prov, "lay_thu") else prov.lay_thu_moi()
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Không đọc được hộp thư ({prov.ten}): {str(e)[:150]}")
    ds_ncc = db.query(NhaCungCap).all()
    tin_cay = {}
    for n in ds_ncc:
        k = (n.email or "").strip().lower()
        if k and k not in tin_cay:
            tin_cay[k] = n.id
    them_email = {(e.email or "").strip().lower() for e in db.query(CtNccEmail).all()}
    them = trung = dung_ai = khong_khop = con_lai = 0
    GIOI_HAN = 25
    for m in thu:
        mid = (m.get("message_id") or "").strip()[:250] or None
        cu = db.query(KtHoaDonCho).filter_by(message_id=mid).first() if mid else None
        if cu is not None:
            # 🔗 bổ sung link tra cứu / ngày HĐ cho bản ghi cũ còn thiếu (không đụng số tiền)
            if cu.trang_thai == "CHO_XAC_NHAN":
                nd_cu = m.get("noi_dung") or ""
                if not getattr(cu, "link_tra_cuu", None):
                    l0, ma0 = _rut_link_tra_cuu(nd_cu)
                    if l0 or ma0:
                        cu.link_tra_cuu, cu.ma_tra_cuu = l0, ma0
                if cu.ngay_hd is None:
                    cu.ngay_hd = _rut_ngay_hd(nd_cu)
            trung += 1
            continue
        if them >= GIOI_HAN:
            con_lai += 1
            continue
        nguoi = (m.get("tu_email") or "").strip().lower()
        tieu_de = (m.get("tieu_de") or "")[:250]
        la_hd = "hoa don" in _kd2(tieu_de) or "invoice" in _kd2(tieu_de)
        if not (nguoi in tin_cay or nguoi in them_email or la_hd):
            khong_khop += 1
            continue
        nd_thu = m.get("noi_dung") or ""
        link_tc, ma_tc = _rut_link_tra_cuu(nd_thu)
        info = doc_hoa_don_email(tieu_de, nd_thu)
        if info:
            dung_ai += 1
        else:
            info = _rut_hd_email(tieu_de, nd_thu)
        if not float(info.get("so_tien") or 0):
            for tep in (m.get("dinh_kem") or []):
                info2 = doc_hoa_don_tep(tep.get("data") or b"", tep.get("content_type") or "",
                                        tep.get("ten_file") or "")
                if info2 and float(info2.get("so_tien") or 0):
                    for k in ("ncc_ten", "so_hoa_don", "ngay", "so_tien",
                              "tien_truoc_thue", "tien_thue", "mo_ta"):
                        if info2.get(k):
                            info[k] = info2[k]
                    break
        tong = float(info.get("so_tien") or 0)
        truoc = float(info.get("tien_truoc_thue") or 0)
        thue = float(info.get("tien_thue") or 0)
        vat_uoc = False
        if not truoc and tong:
            truoc = round(tong / 1.08)
            thue = tong - truoc
            vat_uoc = True
        ts = round(thue / truoc * 100) if truoc > 0 and thue > 0 else 8
        if not tong:
            tong = round(truoc * (1 + ts / 100)) if truoc else 0
        ngay_hd = None
        try:
            if info.get("ngay"):
                ngay_hd = date.fromisoformat(str(info["ngay"])[:10])
        except Exception:
            pass
        # 🏷 TÀI KHOẢN chi phí: AI phân loại; thiếu thì luật dự phòng theo từ khóa
        tk_ai = str(info.get("tk_chi_phi") or "")
        if tk_ai not in ("632", "642", "641", "627"):
            nd_kd = _kd2((str(info.get("mo_ta") or "") + " " + tieu_de))
            tk_ai = "632" if any(w in nd_kd for w in
                                 ("hoa chat", "vat tu", "thiet bi", "hang hoa", "vat lieu",
                                  "pac", "naoh", "polymer", "loc", "bom")) else "642"
        # 🏢 NCC: ưu tiên email trùng hồ sơ → khớp theo tên AI đọc / tên miền riêng
        ncc_id = tin_cay.get(nguoi) or _khop_ncc(ds_ncc, str(info.get("ncc_ten") or ""), nguoi)
        db.add(KtHoaDonCho(
            tk_chi_phi=tk_ai,
            nha_cung_cap_id=ncc_id,
            tu_email=(m.get("tu_email") or "")[:160] or None,
            ncc_ten=(str(info.get("ncc_ten") or "")[:200]) or None,
            so_hoa_don=(str(info.get("so_hoa_don") or "")[:60]) or None,
            ngay_hd=ngay_hd,
            tien_truoc_thue=Decimal(str(int(truoc))), thue_suat=Decimal(str(int(ts))),
            tong_tien=Decimal(str(int(tong))),
            mo_ta=((("⚠ VAT ước 8% từ tổng — kiểm tra lại · " if vat_uoc else "")
                    + str(info.get("mo_ta") or ""))[:300]) or None,
            link_tra_cuu=link_tc, ma_tra_cuu=ma_tc,
            tieu_de=tieu_de or None, message_id=mid, tao_luc=gio_hien_tai()))
        them += 1
    # 🔁 Khớp lại các hàng chờ cũ chưa gắn NCC (quét trước khi có tự khớp theo tên)
    for r0 in db.query(KtHoaDonCho).filter_by(trang_thai="CHO_XAC_NHAN").all():
        if r0.nha_cung_cap_id is None and (r0.ncc_ten or r0.tu_email):
            m0 = _khop_ncc(ds_ncc, r0.ncc_ten or "", r0.tu_email)
            if m0:
                r0.nha_cung_cap_id = m0
    db.commit()
    return {"ok": True, "che_do": prov.ten, "thu_moi": len(thu), "tu_ngay": str(moc),
            "da_them": them, "trung_bo_qua": trung, "ai": dung_ai,
            "khong_khop": khong_khop, "con_lai": con_lai}


@router.get("/hoa-don-cho")
def ds_hoa_don_cho(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    from ..models import KtHoaDonCho, NhaCungCap
    out = []
    ds_ncc = db.query(NhaCungCap).all()
    for r in db.query(KtHoaDonCho).order_by(KtHoaDonCho.id.desc()).limit(400).all():
        n = db.get(NhaCungCap, r.nha_cung_cap_id) if r.nha_cung_cap_id else None
        goi_y = None
        if r.nha_cung_cap_id is None and r.trang_thai == "CHO_XAC_NHAN":
            goi_y = _khop_ncc(ds_ncc, r.ncc_ten or "", r.tu_email)
        out.append({"id": r.id, "nha_cung_cap_id": r.nha_cung_cap_id,
                    "goi_y_ncc_id": goi_y,
                    "ncc_ho_so": n.ten if n else None,
                    "tu_email": r.tu_email, "ncc_ten": r.ncc_ten,
                    "so_hoa_don": r.so_hoa_don,
                    "ngay_hd": str(r.ngay_hd) if r.ngay_hd else None,
                    "tien_truoc_thue": float(r.tien_truoc_thue or 0),
                    "thue_suat": float(r.thue_suat or 8),
                    "tong_tien": float(r.tong_tien or 0),
                    "mo_ta": r.mo_ta, "tieu_de": r.tieu_de,
                    "tk_chi_phi": getattr(r, "tk_chi_phi", None),
                    "link_tra_cuu": getattr(r, "link_tra_cuu", None),
                    "ma_tra_cuu": getattr(r, "ma_tra_cuu", None),
                    "don_hang_id": getattr(r, "don_hang_id", None),
                    "hoa_don_id": r.hoa_don_id, "trang_thai": r.trang_thai})
    return out


@router.post("/hoa-don-cho/{hdc_id}/doc-tep")
def doc_tep_hoa_don_cho(hdc_id: int, file: UploadFile = File(...),
                        db: Session = Depends(get_db),
                        nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """📎 Kế toán tải file hóa đơn (PDF/XML/ảnh) lấy từ link tra cứu — AI đọc, điền tiền."""
    from ..models import KtHoaDonCho
    from ..ai_gateway import doc_hoa_don_tep
    r = db.get(KtHoaDonCho, hdc_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hóa đơn chờ")
    if r.trang_thai == "DA_GHI":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Hóa đơn đã ghi — không sửa được nữa")
    data = file.file.read()
    if not data or len(data) > 8 * 1024 * 1024:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File trống hoặc lớn hơn 8MB")
    info = doc_hoa_don_tep(data, file.content_type or "", file.filename or "")
    if not info:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "AI không đọc được file này — kiểm tra lại file hóa đơn")
    tong = float(info.get("so_tien") or 0)
    truoc = float(info.get("tien_truoc_thue") or 0)
    thue = float(info.get("tien_thue") or 0)
    if not truoc and tong:
        truoc = round(tong / 1.08)
        thue = tong - truoc
    ts = round(thue / truoc * 100) if truoc > 0 and thue > 0 else int(float(r.thue_suat or 8))
    if truoc > 0:
        r.tien_truoc_thue = Decimal(str(int(truoc)))
        r.thue_suat = Decimal(str(int(ts)))
        r.tong_tien = Decimal(str(int(tong))) if tong else Decimal(str(round(truoc * (1 + ts / 100))))
    if info.get("so_hoa_don") and not r.so_hoa_don:
        r.so_hoa_don = str(info["so_hoa_don"])[:60]
    if info.get("ncc_ten") and not r.ncc_ten:
        r.ncc_ten = str(info["ncc_ten"])[:200]
    if info.get("ngay"):
        try:
            r.ngay_hd = date.fromisoformat(str(info["ngay"])[:10])
        except Exception:
            pass
    if info.get("mo_ta") and not r.mo_ta:
        r.mo_ta = str(info["mo_ta"])[:300]
    tk2 = str(info.get("tk_chi_phi") or "")
    if tk2 in ("632", "642", "641", "627"):
        r.tk_chi_phi = tk2
    ghi_audit(db, nd.id, "AI_DOC_TEP_HDC", "kt_hoa_don_cho", r.id,
              moi={"file": file.filename, "truoc": truoc, "tong": float(r.tong_tien or 0)})
    db.commit()
    return {"ok": True, "doc_duoc_tien": truoc > 0,
            "tien_truoc_thue": float(r.tien_truoc_thue or 0),
            "thue_suat": float(r.thue_suat or 8), "tong_tien": float(r.tong_tien or 0),
            "so_hoa_don": r.so_hoa_don, "ngay_hd": str(r.ngay_hd) if r.ngay_hd else None}


@router.post("/hoa-don-cho/{hdc_id}/tao-ncc")
def tao_ncc_tu_hoa_don_cho(hdc_id: int, db: Session = Depends(get_db),
                           nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """➕ Tạo nhanh hồ sơ Nhà cung cấp từ tên AI đọc + email người gửi, gắn vào hóa đơn chờ."""
    from ..models import KtHoaDonCho, NhaCungCap
    r = db.get(KtHoaDonCho, hdc_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hóa đơn chờ")
    if r.nha_cung_cap_id:
        return {"ok": True, "nha_cung_cap_id": r.nha_cung_cap_id, "moi": False}
    ten = (r.ncc_ten or "").strip()
    if not ten:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "AI chưa đọc được tên NCC — vào mục Nhà cung cấp tạo hồ sơ thủ công")
    ds_ncc = db.query(NhaCungCap).all()
    m = _khop_ncc(ds_ncc, ten, r.tu_email)
    if m:
        r.nha_cung_cap_id = m
        db.commit()
        return {"ok": True, "nha_cung_cap_id": m, "moi": False}
    n = NhaCungCap(ten=ten[:200], email=(r.tu_email or "")[:120] or None,
                   ghi_chu=("Tạo tự động từ email hóa đơn " + (r.so_hoa_don or "")).strip())
    db.add(n)
    db.flush()
    r.nha_cung_cap_id = n.id
    ghi_audit(db, nd.id, "TAO_NCC_TU_EMAIL", "nha_cung_cap", n.id,
              moi={"ten": ten, "email": r.tu_email, "hoa_don_cho_id": r.id})
    db.commit()
    return {"ok": True, "nha_cung_cap_id": n.id, "moi": True}


from pydantic import BaseModel as _BM_hdc


class HdBanSua(_BM_hdc):
    don_hang_id: int | None = None      # 0 = bỏ gắn đơn hàng
    khach_hang_id: int | None = None    # chỉ đổi khi > 0
    dien_giai: str | None = None


class HdMuaSua(_BM_hdc):
    don_hang_id: int | None = None      # 0 = bỏ gắn đơn hàng
    tk_chi_phi: str | None = None
    dien_giai: str | None = None


class KtHdcSua(_BM_hdc):
    nha_cung_cap_id: int | None = None
    ncc_ten: str | None = None
    so_hoa_don: str | None = None
    ngay_hd: date | None = None
    tien_truoc_thue: Decimal | None = None
    thue_suat: Decimal | None = None
    mo_ta: str | None = None
    tk_chi_phi: str | None = None
    don_hang_id: int | None = None


@router.put("/hoa-don-cho/{h_id}")
def sua_hoa_don_cho(h_id: int, data: KtHdcSua, db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    from ..models import KtHoaDonCho
    r = db.get(KtHoaDonCho, h_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy")
    if r.trang_thai == "DA_GHI":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Đã ghi vào bảng Hóa đơn — không sửa được nữa")
    if data.nha_cung_cap_id is not None:
        r.nha_cung_cap_id = data.nha_cung_cap_id or None
    if data.ncc_ten is not None:
        r.ncc_ten = data.ncc_ten.strip()[:200] or None
    if data.so_hoa_don is not None:
        r.so_hoa_don = data.so_hoa_don.strip()[:60] or None
    if data.ngay_hd is not None:
        r.ngay_hd = data.ngay_hd
    if data.tien_truoc_thue is not None:
        r.tien_truoc_thue = data.tien_truoc_thue
    if data.thue_suat is not None:
        r.thue_suat = data.thue_suat
    if data.mo_ta is not None:
        r.mo_ta = data.mo_ta.strip()[:300] or None
    if data.tk_chi_phi is not None and data.tk_chi_phi in ("632", "642", "641", "627"):
        r.tk_chi_phi = data.tk_chi_phi
    if data.don_hang_id is not None:
        r.don_hang_id = data.don_hang_id or None
    r.tong_tien = (Decimal(r.tien_truoc_thue or 0) *
                   (1 + Decimal(r.thue_suat or 0) / 100)).quantize(Decimal("1"))
    ghi_audit(db, nd.id, "SUA_HD_CHO", "kt_hoa_don_cho", r.id,
              moi={"so_hoa_don": r.so_hoa_don, "truoc": float(r.tien_truoc_thue or 0),
                   "ts": float(r.thue_suat or 0), "ncc": r.nha_cung_cap_id})
    db.commit()
    return {"ok": True, "tong_tien": float(r.tong_tien)}


@router.post("/hoa-don-cho/{h_id}/ghi")
def ghi_hoa_don_cho(h_id: int, tao_cong_no: bool = True, hach_toan: bool = True,
                    bo_qua_trung: bool = False,
                    db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """XÁC NHẬN: chính thức tạo HÓA ĐƠN MUA (kèm công nợ + hạch toán như tạo tay).
    Có chốt CHỐNG GHI TRÙNG chi phí: (a) cùng email đã ghi bên Chi phí vận hành cho thuê;
    (b) đã có hóa đơn MUA cùng NCC cùng số tiền (thường là hóa đơn tự sinh khi nhận hàng PO)."""
    from ..models import KtHoaDonCho, HoaDon as _HD, CtHoaDonDauVao as _CT
    r = db.query(KtHoaDonCho).filter_by(id=h_id).with_for_update().first()
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy")
    if r.trang_thai == "DA_GHI":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Hóa đơn này đã ghi rồi")
    if not r.nha_cung_cap_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chọn nhà cung cấp (khớp hồ sơ NCC) trước khi ghi")
    if float(r.tien_truoc_thue or 0) <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tiền trước thuế phải lớn hơn 0")
    # trùng số hóa đơn CÙNG NCC → chặn cứng (2 NCC khác nhau trùng số là chuyện bình thường)
    if r.so_hoa_don and db.query(_HD).filter_by(so=r.so_hoa_don,
                                                nha_cung_cap_id=r.nha_cung_cap_id).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Số hóa đơn '{r.so_hoa_don}' của NCC này đã có trong bảng Hóa đơn — trùng.")
    # 🛡 CHỐNG GHI TRÙNG CHI PHÍ — kế toán xác nhận rõ ràng mới được bỏ qua
    if not bo_qua_trung:
        canh = []
        if r.message_id:
            ct = (db.query(_CT).filter_by(message_id=r.message_id)
                  .filter(_CT.trang_thai == "DA_GHI").first())
            if ct is not None:
                canh.append("email này ĐÃ GHI vào Chi phí vận hành dự án cho thuê "
                            f"(HĐ {ct.so_hoa_don or '—'}, {float(ct.so_tien or 0):,.0f}đ) — ghi tiếp sẽ đếm chi phí 2 lần")
        nghi = (db.query(_HD).filter(_HD.loai == "MUA",
                                     _HD.nha_cung_cap_id == r.nha_cung_cap_id,
                                     _HD.tong_tien == Decimal(str(int(float(r.tong_tien or 0)))))
                .order_by(_HD.id.desc()).first())
        if nghi is not None:
            canh.append(f"đã có hóa đơn MUA '{nghi.so}' cùng NCC cùng số tiền "
                        f"{float(nghi.tong_tien or 0):,.0f}đ (có thể là hóa đơn tự sinh khi nhận hàng PO)")
        if canh:
            raise HTTPException(status.HTTP_409_CONFLICT, "⚠TRÙNG: " + "; ".join(canh))
    data = HoaDonVao(loai="MUA", nha_cung_cap_id=r.nha_cung_cap_id,
                     so=r.so_hoa_don or None, ngay=r.ngay_hd,
                     don_hang_id=getattr(r, "don_hang_id", None),
                     tk_chi_phi=(getattr(r, "tk_chi_phi", None) or None),
                     tien_truoc_thue=Decimal(r.tien_truoc_thue or 0),
                     thue_suat=Decimal(r.thue_suat or 8),
                     dien_giai=(r.mo_ta or f"Hóa đơn email {r.tu_email or ''}")[:200] or None,
                     tao_cong_no=tao_cong_no, hach_toan_luon=hach_toan)
    r.trang_thai = "DA_GHI"          # đặt TRƯỚC khi tạo — cùng 1 commit với hóa đơn, hết khe hở ghi đúp
    kq = tao_hoa_don(data, db, nd)
    r.hoa_don_id = (kq or {}).get("id") if isinstance(kq, dict) else None
    ghi_audit(db, nd.id, "GHI_HD_EMAIL_MUA", "kt_hoa_don_cho", r.id,
              moi={"hoa_don_id": r.hoa_don_id, "tong": float(r.tong_tien or 0),
                   "bo_qua_canh_bao_trung": bool(bo_qua_trung)})
    db.commit()
    return {"ok": True, "hoa_don_id": r.hoa_don_id,
            "so": (kq or {}).get("so") if isinstance(kq, dict) else r.so_hoa_don}


@router.post("/hoa-don-cho/{h_id}/bo-qua")
def bo_qua_hoa_don_cho(h_id: int, db: Session = Depends(get_db),
                       nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    from ..models import KtHoaDonCho
    r = db.get(KtHoaDonCho, h_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy")
    if r.trang_thai == "DA_GHI":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Đã ghi — không bỏ qua được")
    r.trang_thai = "BO_QUA"
    ghi_audit(db, nd.id, "BO_QUA_HD_CHO", "kt_hoa_don_cho", r.id,
              cu={"so_hoa_don": r.so_hoa_don, "tong": float(r.tong_tien or 0),
                  "tu_email": r.tu_email})
    db.commit()
    return {"ok": True}


@router.delete("/hoa-don-cho/{h_id}")
def xoa_hoa_don_cho(h_id: int, db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    from ..models import KtHoaDonCho
    r = db.get(KtHoaDonCho, h_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy")
    ghi_audit(db, nd.id, "XOA", "kt_hoa_don_cho", h_id,
              cu={"tieu_de": r.tieu_de, "trang_thai": r.trang_thai})
    db.delete(r)
    db.commit()
    return {"ok": True}


@router.put("/phieu/{p_id}/tk-doi-ung")
def sua_tk_doi_ung(p_id: int, tk: str, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT"))):
    """Sửa TÀI KHOẢN ĐỐI ỨNG của một phiếu (kể cả ĐÃ DUYỆT) — chỉ đổi chân định khoản
    phi tiền mặt, KHÔNG đổi số tiền/quỹ nên số dư quỹ giữ nguyên. Bút toán sửa theo."""
    tk = (tk or "").strip()[:20]
    TK_HOP_LE = {"111", "112", "113", "131", "141", "211", "214", "242", "331", "334",
                 "338", "3383", "3384", "3385", "1331", "3331", "511", "515", "632",
                 "635", "641", "642", "627", "711", "811"}
    if tk not in TK_HOP_LE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Tài khoản '{tk}' không thuộc danh mục TK cho phép: "
                            + ", ".join(sorted(TK_HOP_LE)))
    p = db.get(PhieuThuChi, p_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiếu")
    cu = {"tk_doi_ung": p.tk_doi_ung}
    p.tk_doi_ung = tk
    if p.but_toan_id:
        bt = db.get(ButToan, p.but_toan_id)
        if bt is not None:
            cu["but_toan"] = {"tk_no": bt.tk_no, "tk_co": bt.tk_co}
            if p.loai == "THU":
                bt.tk_co = tk
            else:
                bt.tk_no = tk
    ghi_audit(db, nd.id, "SUA_TK_DOI_UNG", "phieu_thu_chi", p.id, cu=cu, moi={"tk": tk})
    db.commit()
    return {"ok": True, "so": p.so, "tk": tk}


# ---------- CÂN ĐỐI PHÁT SINH (trial balance) ----------
@router.get("/can-doi-phat-sinh")
def can_doi_phat_sinh(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    no = dict(db.query(ButToan.tk_no, func.sum(ButToan.so_tien)).group_by(ButToan.tk_no).all())
    co = dict(db.query(ButToan.tk_co, func.sum(ButToan.so_tien)).group_by(ButToan.tk_co).all())
    tks = sorted(set(list(no.keys()) + list(co.keys())))
    rows = [{"tk": tk, "ten_tk": TEN_TK.get(tk, ""), "ps_no": _f(no.get(tk, 0)),
             "ps_co": _f(co.get(tk, 0))} for tk in tks]
    return {"rows": rows, "tong_no": _f(sum(no.values())), "tong_co": _f(sum(co.values()))}


# ---------- HÓA ĐƠN MUA / BÁN ----------
def _cong_no_cua_hd(db, hd_id):
    cn = db.query(CongNo).filter(CongNo.hoa_don_id == hd_id).first()
    if cn is None:
        return None
    return {"id": cn.id, "loai": cn.loai, "so_tien": _f(cn.so_tien),
            "da_thanh_toan": _f(cn.da_thanh_toan),
            "con_lai": _f(cn.so_tien) - _f(cn.da_thanh_toan), "trang_thai": cn.trang_thai}


def _hd_dict(db, hd: HoaDon):
    if hd.khach_hang_id:
        kh = db.get(KhachHang, hd.khach_hang_id); ten = kh.ten if kh else None
    elif hd.nha_cung_cap_id:
        nc = db.get(NhaCungCap, hd.nha_cung_cap_id); ten = nc.ten if nc else None
    elif hd.don_hang_id:
        dh = db.get(DonHang, hd.don_hang_id)
        kh = db.get(KhachHang, dh.khach_hang_id) if dh and dh.khach_hang_id else None
        ten = kh.ten if kh else None
    else:
        ten = None
    return {"id": hd.id, "so": hd.so or f"HD-{hd.id}", "loai": hd.loai,
            "ngay": str(hd.ngay) if hd.ngay else None, "ten_doi_tac": ten,
            "khach_hang_id": hd.khach_hang_id, "nha_cung_cap_id": hd.nha_cung_cap_id,
            "don_hang_id": hd.don_hang_id, "ma_ban": _ma_ban(db, hd.don_hang_id),
            "tien_truoc_thue": _f(hd.tien_truoc_thue), "tien_thue": _f(hd.tien_thue),
            "tong_tien": _f(hd.tong_tien), "tk_chi_phi": hd.tk_chi_phi,
            "nhom_chi_phi": hd.nhom_chi_phi,
            "dien_giai": hd.dien_giai, "da_hach_toan": bool(hd.da_hach_toan),
            "trang_thai": hd.trang_thai, "hddt_trang_thai": hd.hddt_trang_thai,
            "hddt_ma_tra_cuu": hd.hddt_ma_tra_cuu, "cong_no": _cong_no_cua_hd(db, hd.id)}


@router.post("/chi-phi/doan-nhom")
def doan_nhom_chi_phi_hd(data: DoanNhomVao, _=Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """AI đoán 1 trong 12 nhóm chi phí từ diễn giải + đối tác + số tiền (cho hóa đơn mua)."""
    from ..ai_gateway import doan_nhom_chi_phi
    return doan_nhom_chi_phi(data.dien_giai, data.ten_doi_tac, data.so_tien)


@router.get("/hoa-don")
def ds_hoa_don(loai: str | None = None, db: Session = Depends(get_db),
               _=Depends(yeu_cau(MODULE, "XEM"))):
    from ..models import KtHoaDonCho
    tu_email = {r[0] for r in db.query(KtHoaDonCho.hoa_don_id)
                .filter(KtHoaDonCho.hoa_don_id.isnot(None)).all()}
    q = db.query(HoaDon)
    if loai:
        q = q.filter(HoaDon.loai == loai)
    out = []
    for h in q.order_by(HoaDon.id.desc()).all():
        d = _hd_dict(db, h)
        d["tu_email"] = h.id in tu_email
        out.append(d)
    return out


@router.put("/hoa-don/{hd_id}/sua-ban")
def sua_hoa_don_ban(hd_id: int, data: HdBanSua, db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """✏️ Sửa hóa đơn BÁN: khách hàng / mã đơn hàng / diễn giải — đồng bộ bút toán
    (don_hang_id) + công nợ (khach_hang_id). Khóa khi đã phát hành HĐĐT."""
    hd = db.get(HoaDon, hd_id)
    if hd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hóa đơn")
    if hd.loai != "BAN":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Endpoint này chỉ sửa hóa đơn BÁN")
    if hd.hddt_trang_thai == "DA_PHAT_HANH":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"'{hd.so}' đã phát hành HĐĐT — không sửa được, cần lập hóa đơn điều chỉnh/thay thế")
    cu = {"don_hang_id": hd.don_hang_id, "khach_hang_id": hd.khach_hang_id, "dien_giai": hd.dien_giai}
    if data.don_hang_id is not None:
        moi_dh = data.don_hang_id or None
        if moi_dh and db.get(DonHang, moi_dh) is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không tìm thấy đơn hàng")
        hd.don_hang_id = moi_dh
        for bt in db.query(ButToan).filter_by(hoa_don_id=hd.id).all():
            bt.don_hang_id = moi_dh
    if data.khach_hang_id and data.khach_hang_id != hd.khach_hang_id:
        if db.get(KhachHang, data.khach_hang_id) is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không tìm thấy khách hàng")
        cns = db.query(CongNo).filter_by(hoa_don_id=hd.id).all()
        if any(_f(cn.da_thanh_toan) > 0 for cn in cns):
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Công nợ của '{hd.so}' đã thu một phần — không đổi được khách hàng")
        hd.khach_hang_id = data.khach_hang_id
        for cn in cns:
            cn.khach_hang_id = data.khach_hang_id
    if data.dien_giai is not None and data.dien_giai.strip():
        hd.dien_giai = data.dien_giai.strip()[:300]
    ghi_audit(db, nd.id, "SUA_HD_BAN", "hoa_don", hd.id, cu=cu,
              moi={"don_hang_id": hd.don_hang_id, "khach_hang_id": hd.khach_hang_id})
    db.commit()
    return _hd_dict(db, hd)


@router.put("/hoa-don/{hd_id}/sua-mua")
def sua_hoa_don_mua(hd_id: int, data: HdMuaSua, db: Session = Depends(get_db),
                    nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """✏️ Sửa hóa đơn MUA: mã đơn hàng / TK chi phí / diễn giải.
    Bút toán đã sinh được đồng bộ theo (đổi don_hang_id + tài khoản Nợ chi phí)."""
    hd = db.get(HoaDon, hd_id)
    if hd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hóa đơn")
    if hd.loai != "MUA":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chỉ sửa được hóa đơn MUA")
    cu = {"don_hang_id": hd.don_hang_id, "tk_chi_phi": hd.tk_chi_phi, "dien_giai": hd.dien_giai}
    if data.don_hang_id is not None:
        moi_dh = data.don_hang_id or None
        if moi_dh and db.get(DonHang, moi_dh) is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không tìm thấy đơn hàng")
        hd.don_hang_id = moi_dh
        for bt in db.query(ButToan).filter_by(hoa_don_id=hd.id).all():
            bt.don_hang_id = moi_dh
    if data.tk_chi_phi is not None and data.tk_chi_phi in ("632", "642", "641", "627") \
            and hd.tk_chi_phi != data.tk_chi_phi:
        for bt in db.query(ButToan).filter_by(hoa_don_id=hd.id, tk_no=hd.tk_chi_phi or "642").all():
            bt.tk_no = data.tk_chi_phi
        hd.tk_chi_phi = data.tk_chi_phi
    if data.dien_giai is not None and data.dien_giai.strip():
        hd.dien_giai = data.dien_giai.strip()[:300]
    ghi_audit(db, nd.id, "SUA_HD_MUA", "hoa_don", hd.id, cu=cu,
              moi={"don_hang_id": hd.don_hang_id, "tk_chi_phi": hd.tk_chi_phi})
    db.commit()
    return _hd_dict(db, hd)


@router.post("/hoa-don/{hd_id}/tra-ve-cho")
def tra_hoa_don_ve_cho(hd_id: int, db: Session = Depends(get_db),
                       nd: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN", "KTT"))):
    """↩ Trả hóa đơn MUA (tạo từ email) về bảng chờ xác nhận: hủy hóa đơn + công nợ
    + bút toán (chỉ khi chưa thanh toán đồng nào) rồi mở lại hàng chờ để sửa/Ghi lại."""
    from ..models import KtHoaDonCho, LenhChiBank
    hd = db.get(HoaDon, hd_id)
    if hd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hóa đơn")
    if hd.loai != "MUA":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chỉ trả về được hóa đơn MUA")
    hdc = db.query(KtHoaDonCho).filter_by(hoa_don_id=hd_id).first()
    if hdc is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Hóa đơn này nhập tay, không tạo từ email — nếu ghi nhầm dùng nút 🗑 Xóa")
    cns = db.query(CongNo).filter_by(hoa_don_id=hd_id).all()
    if any(_f(cn.da_thanh_toan) > 0 for cn in cns):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Công nợ của '{hd.so}' đã trả một phần — không thể trả về để giữ vết kế toán")
    cn_ids = [cn.id for cn in cns]
    if cn_ids:
        so_p = db.query(func.count(PhieuThuChi.id)).filter(PhieuThuChi.cong_no_id.in_(cn_ids)).scalar() or 0
        if so_p:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"'{hd.so}' có {so_p} phiếu thu/chi gắn công nợ — không thể trả về")
        so_l = db.query(func.count(LenhChiBank.id)).filter(LenhChiBank.cong_no_id.in_(cn_ids)).scalar() or 0
        if so_l:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"'{hd.so}' có {so_l} lệnh chi ngân hàng gắn công nợ — hủy lệnh chi trước")
    so_cu = hd.so
    db.query(ButToan).filter_by(hoa_don_id=hd_id).delete()
    for cn in cns:
        db.delete(cn)
    hdc.trang_thai = "CHO_XAC_NHAN"
    hdc.hoa_don_id = None
    ghi_audit(db, nd.id, "TRA_VE_CHO", "hoa_don", hd_id,
              cu={"so": so_cu, "tong_tien": _f(hd.tong_tien), "so_cong_no": len(cns)})
    db.delete(hd)
    db.commit()
    return {"ok": True, "so": so_cu}


@router.post("/hoa-don", status_code=201)
def tao_hoa_don(data: HoaDonVao, db: Session = Depends(get_db),
                nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    if data.loai not in ("BAN", "MUA"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Loại hóa đơn phải là BAN hoặc MUA")
    if data.loai == "MUA" and not data.nha_cung_cap_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Hóa đơn mua cần nhà cung cấp")
    truoc = Decimal(data.tien_truoc_thue or 0)
    thue = (truoc * Decimal(data.thue_suat or 0) / 100).quantize(Decimal("1"))
    tong = truoc + thue
    kh_id = data.khach_hang_id
    if data.loai == "BAN" and not kh_id and data.don_hang_id:
        dh = db.get(DonHang, data.don_hang_id)
        kh_id = dh.khach_hang_id if dh else None
    hd = HoaDon(loai=data.loai, don_hang_id=data.don_hang_id, ngay=data.ngay or date.today(),
                tien_truoc_thue=truoc, tien_thue=thue, tong_tien=tong,
                khach_hang_id=kh_id, nha_cung_cap_id=data.nha_cung_cap_id,
                tk_chi_phi=data.tk_chi_phi,
                nhom_chi_phi=(data.nhom_chi_phi if data.loai == "MUA" else None),
                dien_giai=data.dien_giai,
                hddt_trang_thai="CHUA_PHAT_HANH" if data.loai == "BAN" else None,
                trang_thai="GHI_NHAN")
    db.add(hd); db.flush()
    hd.so = data.so or f"{'HDB' if data.loai == 'BAN' else 'HDM'}-{date.today():%Y%m%d}-{hd.id}"
    # sinh công nợ
    cn = None
    if data.tao_cong_no:
        from datetime import timedelta
        han = date.today() + timedelta(days=int(data.han_ngay or 30))
        # chép SỐ HÓA ĐƠN + ngày chứng từ sang công nợ — để không rơi nhầm vào
        # bảng "Phải trả chưa hóa đơn" và để đối chiếu thu-chi theo số HĐ
        if data.loai == "BAN":
            cn = CongNo(loai="PHAI_THU", hoa_don_id=hd.id, khach_hang_id=kh_id,
                        so_ct=(hd.so or None), ngay_ct=hd.ngay,
                        so_tien=tong, da_thanh_toan=0, han=han, trang_thai="CHUA_THU")
        else:
            cn = CongNo(loai="PHAI_TRA", hoa_don_id=hd.id, nha_cung_cap_id=data.nha_cung_cap_id,
                        so_ct=(hd.so or None), ngay_ct=hd.ngay,
                        so_tien=tong, da_thanh_toan=0, han=han, trang_thai="CHUA_TRA")
        db.add(cn); db.flush()
    # TỰ CẤN TRỪ TẠM ỨNG/TRẢ TRƯỚC cùng mã hàng bán vào công nợ vừa sinh
    da_cap_tru_tu_ung = Decimal(0)
    if cn is not None and data.don_hang_id:
        side = "THU" if data.loai == "BAN" else "CHI"
        advs = (db.query(PhieuThuChi)
                .filter(PhieuThuChi.don_hang_id == data.don_hang_id,
                        PhieuThuChi.la_tam_ung.is_(True), PhieuThuChi.loai == side,
                        PhieuThuChi.trang_thai == "DA_DUYET",
                        PhieuThuChi.so_tien > PhieuThuChi.da_can_tru)
                .order_by(PhieuThuChi.id).with_for_update().all())
        for adv in advs:
            con_cn = Decimal(cn.so_tien) - Decimal(cn.da_thanh_toan)
            if con_cn <= 0:
                break
            con_ung = Decimal(adv.so_tien) - Decimal(adv.da_can_tru)
            ap = min(con_ung, con_cn)
            if ap <= 0:
                continue
            adv.da_can_tru = Decimal(adv.da_can_tru) + ap
            cn.da_thanh_toan = Decimal(cn.da_thanh_toan) + ap
            da_cap_tru_tu_ung += ap
        if da_cap_tru_tu_ung > 0:
            du = Decimal(cn.da_thanh_toan) >= Decimal(cn.so_tien)
            if cn.loai == "PHAI_THU":
                cn.trang_thai = "THU_DU" if du else "THU_MOT_PHAN"
            else:
                cn.trang_thai = "DA_TRA" if du else "TRA_MOT_PHAN"
    # hạch toán doanh thu / chi phí + thuế
    if data.hach_toan_luon:
        (hach_toan_hoa_don_ban if data.loai == "BAN" else hach_toan_hoa_don_mua)(db, hd)
        hd.da_hach_toan = True; hd.trang_thai = "DA_HACH_TOAN"
    ghi_audit(db, nd.id, "TAO", "hoa_don", hd.id,
              moi={"so": hd.so, "loai": hd.loai, "tong_tien": _f(tong),
                   "tam_ung_cap_tru": _f(da_cap_tru_tu_ung)})
    db.commit(); db.refresh(hd)
    return _hd_dict(db, hd)


@router.post("/hoa-don/{hd_id}/hach-toan")
def hach_toan_hd(hd_id: int, db: Session = Depends(get_db),
                 nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    hd = db.get(HoaDon, hd_id)
    if hd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hóa đơn")
    if hd.da_hach_toan:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Hóa đơn đã hạch toán")
    (hach_toan_hoa_don_ban if hd.loai == "BAN" else hach_toan_hoa_don_mua)(db, hd)
    hd.da_hach_toan = True; hd.trang_thai = "DA_HACH_TOAN"
    ghi_audit(db, nd.id, "HACH_TOAN", "hoa_don", hd.id)
    db.commit(); db.refresh(hd)
    return _hd_dict(db, hd)


# ---------- TRUY VẾT THEO MÃ HÀNG BÁN ----------
def _lai_lo_1(db, dh: DonHang):
    doanh_thu = _f(dh.tong_tien) + _f(dh.tien_thue)   # GỒM VAT — cùng cơ sở với Lãi/Lỗ Record
    # ĐỒNG BỘ với bảng "Chi phí theo Mã Đơn hàng" (NCC → Kiểm soát):
    #   Giá vốn (Thanh toán mua) = đề nghị TT của các PO gắn mã đơn bán
    #   Chi phí khác (Công nợ phải trả) = công nợ phải trả CÒN LẠI của PO đó + khoản nhập ngoài khớp mã
    po_ids = [i for (i,) in db.query(DonMua.id).filter(DonMua.don_hang_id == dh.id).all()]
    gia_von = _f(db.query(func.coalesce(func.sum(func.coalesce(DonMua.da_duyet_tt, DonMua.de_nghi_tt)), 0))
                 .filter(DonMua.don_hang_id == dh.id).scalar())
    _con = func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0)
    cn_po = _f(db.query(_con).filter(CongNo.loai == "PHAI_TRA",
                                     CongNo.don_mua_id.in_(po_ids)).scalar()) if po_ids else 0.0
    cn_ngoai = 0.0
    if dh.so:
        cn_ngoai = _f(db.query(_con).filter(CongNo.loai == "PHAI_TRA", CongNo.don_mua_id.is_(None),
                                            func.lower(CongNo.ma_ban_ngoai) == dh.so.lower()).scalar())
    chi_phi = max(cn_po, 0.0) + max(cn_ngoai, 0.0)
    da_thu = _f(db.query(func.coalesce(func.sum(PhieuThuChi.so_tien), 0))
                .filter(PhieuThuChi.don_hang_id == dh.id, PhieuThuChi.loai == "THU",
                        PhieuThuChi.trang_thai == "DA_DUYET").scalar())
    # Tạm ứng/trả trước theo mã hàng bán
    tu_thu = _f(db.query(func.coalesce(func.sum(PhieuThuChi.so_tien), 0))
                .filter(PhieuThuChi.don_hang_id == dh.id, PhieuThuChi.loai == "THU",
                        PhieuThuChi.la_tam_ung.is_(True),
                        PhieuThuChi.trang_thai == "DA_DUYET").scalar())
    tu_thu_clt = _f(db.query(func.coalesce(func.sum(PhieuThuChi.so_tien - PhieuThuChi.da_can_tru), 0))
                    .filter(PhieuThuChi.don_hang_id == dh.id, PhieuThuChi.loai == "THU",
                            PhieuThuChi.la_tam_ung.is_(True),
                            PhieuThuChi.trang_thai == "DA_DUYET").scalar())
    tu_chi = _f(db.query(func.coalesce(func.sum(PhieuThuChi.so_tien), 0))
                .filter(PhieuThuChi.don_hang_id == dh.id, PhieuThuChi.loai == "CHI",
                        PhieuThuChi.la_tam_ung.is_(True),
                        PhieuThuChi.trang_thai == "DA_DUYET").scalar())
    tu_chi_clt = _f(db.query(func.coalesce(func.sum(PhieuThuChi.so_tien - PhieuThuChi.da_can_tru), 0))
                    .filter(PhieuThuChi.don_hang_id == dh.id, PhieuThuChi.loai == "CHI",
                            PhieuThuChi.la_tam_ung.is_(True),
                            PhieuThuChi.trang_thai == "DA_DUYET").scalar())
    hd_ban = _f(db.query(func.coalesce(func.sum(HoaDon.tong_tien), 0))
                .filter(HoaDon.don_hang_id == dh.id, HoaDon.loai == "BAN").scalar())
    loi_nhuan = doanh_thu - gia_von - chi_phi
    # Cam kết đặt cọc (khách hàng) vs đã ứng
    ty = float(dh.ty_le_dat_coc or 0)
    dc_dk = round(doanh_thu * ty / 100)
    if ty <= 0:
        coc_tt = "KHONG"
    elif tu_thu < dc_dk * 0.999:
        coc_tt = "THIEU"
    elif tu_thu > dc_dk * 1.001:
        coc_tt = "VUOT"
    else:
        coc_tt = "DU"
    return {"don_hang_id": dh.id, "ma_ban": dh.so or f"DH-{dh.id}",
            "doanh_thu": doanh_thu, "gia_von": gia_von, "chi_phi_khac": chi_phi,
            "thanh_toan_mua": gia_von, "cong_no_phai_tra": chi_phi,
            "tong_chi_phi": gia_von + chi_phi, "loi_nhuan": loi_nhuan,
            "ty_suat": round(loi_nhuan / doanh_thu * 100, 1) if doanh_thu else None,
            "da_thu": da_thu, "con_phai_thu": max(doanh_thu - da_thu, 0),
            "tam_ung_thu": tu_thu, "tam_ung_thu_con_lai": tu_thu_clt,
            "tam_ung_chi": tu_chi, "tam_ung_chi_con_lai": tu_chi_clt,
            "da_xuat_hd_ban": hd_ban,
            "ty_le_dat_coc": ty, "dat_coc_du_kien": dc_dk,
            "dat_coc_da_ung": tu_thu, "coc_trang_thai": coc_tt,
            "coc_chenh_lech": tu_thu - dc_dk}


@router.get("/tam-ung")
def ds_tam_ung(don_hang_id: int | None = None, loai: str | None = None,
               db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Danh sách khoản tạm ứng/trả trước (đã duyệt) kèm phần còn lại chưa cấn trừ vào hóa đơn."""
    q = db.query(PhieuThuChi).filter(PhieuThuChi.la_tam_ung.is_(True),
                                     PhieuThuChi.trang_thai == "DA_DUYET")
    if don_hang_id:
        q = q.filter(PhieuThuChi.don_hang_id == don_hang_id)
    if loai:
        q = q.filter(PhieuThuChi.loai == loai)
    return [_phieu_dict(db, p) for p in q.order_by(PhieuThuChi.id.desc()).all()]


@router.get("/lai-lo-ma-ban")
def lai_lo_ma_ban(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    dhs = db.query(DonHang).order_by(DonHang.id.desc()).all()
    return [_lai_lo_1(db, dh) for dh in dhs]


@router.put("/ma-ban/{don_hang_id}/dat-coc")
def dat_ty_le_coc(don_hang_id: int, data: DatCocVao, db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    dh = db.get(DonHang, don_hang_id)
    if dh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy mã hàng bán")
    dh.ty_le_dat_coc = Decimal(data.ty_le)
    ghi_audit(db, nd.id, "DAT_COC", "don_hang", dh.id, moi={"ty_le": float(data.ty_le)})
    db.commit()
    return _lai_lo_1(db, dh)


@router.get("/bao-cao-tra-truoc")
def bao_cao_tra_truoc(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Tổng hợp khoản trả trước CÒN TREO (chưa cấn trừ) theo từng khách/NCC,
    và tình trạng đặt cọc của các đơn có cam kết."""
    advs = (db.query(PhieuThuChi)
            .filter(PhieuThuChi.la_tam_ung.is_(True), PhieuThuChi.trang_thai == "DA_DUYET",
                    PhieuThuChi.so_tien > PhieuThuChi.da_can_tru).all())
    nhom = {}
    for p in advs:
        con = _f(p.so_tien) - _f(p.da_can_tru)
        if p.loai == "THU":
            key = ("KH", p.khach_hang_id)
            ten = (db.get(KhachHang, p.khach_hang_id).ten if p.khach_hang_id else "Khách lẻ")
        else:
            key = ("NCC", p.nha_cung_cap_id)
            ten = (db.get(NhaCungCap, p.nha_cung_cap_id).ten if p.nha_cung_cap_id else "NCC")
        g = nhom.setdefault(key, {"doi_tac_loai": key[0], "ten": ten, "so_khoan": 0, "con_treo": 0.0})
        g["so_khoan"] += 1; g["con_treo"] += con
    theo_doi_tac = sorted(nhom.values(), key=lambda x: -x["con_treo"])
    treo_thu = sum(g["con_treo"] for g in theo_doi_tac if g["doi_tac_loai"] == "KH")
    treo_chi = sum(g["con_treo"] for g in theo_doi_tac if g["doi_tac_loai"] == "NCC")
    # Đơn có cam kết đặt cọc
    theo_don = []
    for dh in db.query(DonHang).filter(DonHang.ty_le_dat_coc > 0).order_by(DonHang.id.desc()).all():
        r = _lai_lo_1(db, dh)
        theo_don.append({"don_hang_id": dh.id, "ma_ban": r["ma_ban"], "gia_tri": r["doanh_thu"],
                         "ty_le_dat_coc": r["ty_le_dat_coc"], "dat_coc_du_kien": r["dat_coc_du_kien"],
                         "dat_coc_da_ung": r["dat_coc_da_ung"], "coc_chenh_lech": r["coc_chenh_lech"],
                         "coc_trang_thai": r["coc_trang_thai"]})
    return {"theo_doi_tac": theo_doi_tac, "tong_treo_thu": treo_thu, "tong_treo_chi": treo_chi,
            "theo_don": theo_don}


@router.get("/the-ma-ban/{don_hang_id}")
def the_ma_ban(don_hang_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Thẻ truy vết liên tục theo MÃ HÀNG BÁN: doanh thu, giá vốn (PO), phiếu thu/chi, bút toán."""
    dh = db.get(DonHang, don_hang_id)
    if dh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy mã hàng bán")
    kh = db.get(KhachHang, dh.khach_hang_id) if dh.khach_hang_id else None
    pos = db.query(DonMua).filter(DonMua.don_hang_id == dh.id).all()
    phieus = (db.query(PhieuThuChi)
              .filter(PhieuThuChi.don_hang_id == dh.id)
              .order_by(PhieuThuChi.id).all())
    bts = (db.query(ButToan).filter(ButToan.don_hang_id == dh.id)
           .order_by(ButToan.id).all())
    return {
        "don_hang": {"id": dh.id, "so": dh.so or f"DH-{dh.id}", "ngay": str(dh.ngay),
                     "khach_hang": kh.ten if kh else None, "tong_tien": _f(dh.tong_tien),
                     "trang_thai": dh.trang_thai},
        "tom_tat": _lai_lo_1(db, dh),
        "don_mua": [{"id": p.id, "so": p.so, "tong_tien": _f(p.tong_tien),
                     "trang_thai": p.trang_thai} for p in pos],
        "phieu": [_phieu_dict(db, p) for p in phieus],
        "but_toan": [{"id": b.id, "ngay": str(b.ngay), "tk_no": b.tk_no, "tk_co": b.tk_co,
                      "so_tien": _f(b.so_tien), "dien_giai": b.dien_giai} for b in bts],
    }


# ============ 🏦 SAO KÊ — DANH MỤC THANH TOÁN (Kế toán → Thống kê thu-chi) ============
@router.post("/sao-ke", status_code=201)
def tai_sao_ke_kt(ngan_hang: str = "", file: UploadFile = File(...),
                  db: Session = Depends(get_db),
                  nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """📥 Kế toán tải file sao kê — dùng chung lõi AI đọc với Overall Financial."""
    from .tai_chinh import tai_sao_ke as _core
    return _core(ngan_hang=ngan_hang, file=file, db=db, nd=nd)


@router.get("/sao-ke-doi-chieu")
def sao_ke_doi_chieu(sk_id: int, db: Session = Depends(get_db),
                     _=Depends(yeu_cau(MODULE, "XEM"))):
    """DANH MỤC THANH TOÁN: từng dòng sao kê đối chiếu THEO NGÀY + số tiền với
    ① lệnh chi ĐÃ DUYỆT — chờ ngân hàng thực chi (tiền ra) và
    ② khoản THU công nợ bán hàng đã ghi (tiền vào) + gợi ý công nợ còn phải thu."""
    from datetime import timedelta as _td
    from ..models import (SaoKeBank, SaoKeDong, LenhChiBank, DonMua, DonHang, KhachHang)
    sk = db.get(SaoKeBank, sk_id)
    if sk is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sao kê")
    import traceback as _tb
    try:
        return _sao_ke_doi_chieu_lo(db, sk, sk_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            f"DBG {type(e).__name__}: {str(e)[:160]} | {_tb.format_exc().splitlines()[-3][:160]}")


def _sao_ke_doi_chieu_lo(db, sk, sk_id):
    from datetime import timedelta as _td
    from ..models import (SaoKeDong, LenhChiBank, DonMua, DonHang, KhachHang,
                          ThanhToan, CongNo, NhaCungCap)
    import itertools
    import unicodedata
    dongs = (db.query(SaoKeDong).filter_by(sao_ke_id=sk_id)
             .order_by(SaoKeDong.ngay, SaoKeDong.id).all())
    tu = (sk.tu_ngay or date.today()) - _td(days=5)
    den = (sk.den_ngay or date.today()) + _td(days=5)

    def _ma_dh(dh_id):
        dh = db.get(DonHang, dh_id) if dh_id else None
        return dh.so if dh else None

    def _kd(s2):
        s2 = unicodedata.normalize("NFD", s2 or "")
        s2 = "".join(c for c in s2 if unicodedata.category(c) != "Mn")
        return s2.replace("đ", "d").replace("Đ", "D").lower()

    def _phan_loai(dg):
        k = " " + _kd(dg) + " "
        if "chuyen noi bo" in k or " noi bo" in k:
            return "NOI_BO"
        if "rut tien" in k or "nhap quy" in k or "nop tien mat" in k:
            return "NOP_RUT"
        if "chi luong" in k or "luong thang" in k or "thanh toan luong" in k or "luong t" in k:
            return "LUONG"
        if "bhxh" in k or "bao hiem xa hoi" in k:
            return "BHXH"
        if "nop thue" in k or "thue gtgt" in k or "thue tndn" in k or "thue mon bai" in k:
            return "THUE"
        if (" phi " in k or k.strip().startswith("phi ") or "phi chuyen" in k
                or "phi phat hanh" in k or "phi quan ly" in k or "bao lanh" in k
                or "phi thuong nien" in k or "thu no tk" in k):
            return "PHI_NH"
        return None

    # ① lệnh ĐÃ DUYỆT chờ thực chi (số của ĐỢT) — hành động ✔ Đã chi
    ra_ung = []
    duyet_ids = {r.don_mua_id for r in db.query(LenhChiBank)
                 .filter(LenhChiBank.trang_thai == "DA_DUYET").all() if r.don_mua_id}
    for dm in db.query(DonMua).filter(DonMua.cho_lenh_bank.is_(True)).all():
        if dm.id not in duyet_ids:
            continue
        da_chi = float(db.query(func.coalesce(func.sum(LenhChiBank.so_tien), 0))
                       .filter(LenhChiBank.don_mua_id == dm.id,
                               LenhChiBank.trang_thai == "DA_CHI").scalar() or 0)
        so_dot = max(float(dm.lenh_bank_tien or 0) - da_chi, 0.0)
        if so_dot <= 0:
            continue
        ra_ung.append({"don_mua_id": dm.id, "so": dm.so or f"PO-{dm.id}",
                       "so_tien": so_dot, "ma_ban": _ma_dh(dm.don_hang_id),
                       "ngay": dm.lenh_bank_luc.date() if dm.lenh_bank_luc else None})
    # ② lệnh ĐÃ CHI trong kỳ — đã xử lý
    ra_dachi = []
    for r0 in db.query(LenhChiBank).filter(LenhChiBank.trang_thai == "DA_CHI").all():
        ng = r0.ngay_tt or (r0.chi_luc.date() if r0.chi_luc else None)
        if ng is None or ng < tu or ng > den:
            continue
        dm0 = db.get(DonMua, r0.don_mua_id) if r0.don_mua_id else None
        ra_dachi.append({"id": r0.id, "ngay": ng, "so_tien": float(r0.so_tien or 0),
                         "mo_ta": f"Lệnh đã chi — {dm0.so if dm0 else ('CN' + str(r0.cong_no_id or ''))}",
                         "ma_ban": _ma_dh(dm0.don_hang_id) if dm0 else None})
    # ③ phiếu thu-chi ĐÃ DUYỆT qua quỹ NGÂN HÀNG trong kỳ — đã xử lý
    quy_nh = {q.id for q in db.query(TaiKhoanQuy).filter(TaiKhoanQuy.loai == "NGAN_HANG").all()}
    phieu_ra, phieu_vao = [], []
    for p0 in db.query(PhieuThuChi).filter(PhieuThuChi.trang_thai == "DA_DUYET",
                                           PhieuThuChi.ngay >= tu, PhieuThuChi.ngay <= den).all():
        if p0.quy_id not in quy_nh:
            continue
        it0 = {"id": p0.id, "ngay": p0.ngay, "so_tien": float(p0.so_tien or 0),
               "mo_ta": f"Phiếu {p0.so or p0.id} — {(p0.dien_giai or '')[:45]}",
               "ma_ban": _ma_dh(p0.don_hang_id)}
        (phieu_ra if p0.loai == "CHI" else phieu_vao).append(it0)
    # ④ thu công nợ bán đã ghi
    vao_thu = []
    for tt, cn in (db.query(ThanhToan, CongNo).join(CongNo, ThanhToan.cong_no_id == CongNo.id)
                   .filter(CongNo.loai == "PHAI_THU",
                           ThanhToan.ngay >= tu, ThanhToan.ngay <= den).all()):
        kh = db.get(KhachHang, cn.khach_hang_id) if cn.khach_hang_id else None
        vao_thu.append({"thanh_toan_id": tt.id, "ngay": tt.ngay,
                        "so_tien": float(tt.so_tien or 0),
                        "ma_ban": _ma_dh(cn.don_hang_id) or cn.ma_ban_ngoai,
                        "khach": kh.ten if kh else None, "cong_no_id": cn.id})
    # ⑤ công nợ còn lại: PHẢI THU (gợi ý thu) + PHẢI TRẢ gom theo NCC (khớp tên + gộp)
    goi_y_cn = []
    for cn in db.query(CongNo).filter(CongNo.loai == "PHAI_THU").all():
        con = float(cn.so_tien or 0) - float(cn.da_thanh_toan or 0)
        if con <= 0:
            continue
        kh = db.get(KhachHang, cn.khach_hang_id) if cn.khach_hang_id else None
        goi_y_cn.append({"cong_no_id": cn.id, "con_lai": con,
                         "ma_ban": _ma_dh(cn.don_hang_id) or cn.ma_ban_ngoai,
                         "khach": kh.ten if kh else None})
    ds_ncc = db.query(NhaCungCap).all()
    cn_tra_ncc = {}
    for cn in db.query(CongNo).filter(CongNo.loai == "PHAI_TRA").all():
        con = float(cn.so_tien or 0) - float(cn.da_thanh_toan or 0)
        if con <= 0 or not cn.nha_cung_cap_id:
            continue
        cn_tra_ncc.setdefault(cn.nha_cung_cap_id, []).append(
            {"cong_no_id": cn.id, "con_lai": con, "so_ct": cn.so_ct})

    def _to_hop(khoans, target):
        """Tìm 1–3 khoản công nợ cộng lại ≈ target (sai số ≤ max(1000đ, 0.5%))."""
        eps = max(1000.0, target * 0.005)
        ks = khoans[:12]
        for r2 in (1, 2, 3):
            for combo in itertools.combinations(ks, r2):
                if abs(sum(c["con_lai"] for c in combo) - target) <= eps:
                    return list(combo)
        return None

    dung_ra, dung_vao, dung_dachi, dung_pra, dung_pvao = set(), set(), set(), set(), set()
    out = []
    for d in dongs:
        vao = float(d.tien_vao or 0)
        ra = float(d.tien_ra or 0)
        r = {"id": d.id, "ngay": str(d.ngay) if d.ngay else None, "dien_giai": d.dien_giai,
             "tien_vao": vao, "tien_ra": ra, "ghi_chu": getattr(d, "ghi_chu", None),
             "da_ghi": d.khop_loai in ("DA_CHI_SK", "GHI_THU_SK", "PHIEU_SK"),
             "khop_mo_ta": d.khop_mo_ta, "phan_loai": _phan_loai(d.dien_giai),
             "duyet_chi": None, "thu": None, "goi_y_thu": None, "goi_y_chi": None,
             "da_xu_ly": None, "ma_ban": None}

        def _lech(ng):
            try:
                return abs((ng - d.ngay).days) if (ng and d.ngay) else 99
            except Exception:
                return 99

        def _tim(pool, so, dung, gioi_han):
            best = None
            for u in pool:
                if u["id" if "id" in u else "thanh_toan_id"] in dung:
                    continue
                if abs(u["so_tien"] - so) > 0.5:
                    continue
                le = _lech(u.get("ngay"))
                if le > gioi_han:
                    continue
                if best is None or le < best[0]:
                    best = (le, u)
            return best[1] if best else None

        if ra > 0:
            u = None
            best = None
            for u0 in ra_ung:
                if u0["don_mua_id"] in dung_ra or abs(u0["so_tien"] - ra) > 0.5:
                    continue
                le = _lech(u0["ngay"])
                if u0["ngay"] is not None and le > 7:
                    continue
                if best is None or le < best[0]:
                    best = (le, u0)
            if best is not None:
                dung_ra.add(best[1]["don_mua_id"])
                r["duyet_chi"] = best[1]
                r["ma_ban"] = best[1]["ma_ban"]
            else:
                u = _tim(ra_dachi, ra, dung_dachi, 3)
                if u is None:
                    u = _tim(phieu_ra, ra, dung_pra, 3)
                    if u is not None:
                        dung_pra.add(u["id"])
                else:
                    dung_dachi.add(u["id"])
                if u is not None:
                    r["da_xu_ly"] = {"mo_ta": u["mo_ta"]}
                    r["ma_ban"] = u.get("ma_ban")
                elif r["phan_loai"] is None:
                    # 🔎 khớp theo TÊN NCC trong diễn giải + GỘP nhiều hóa đơn
                    ncc_id = _khop_ncc(ds_ncc, d.dien_giai or "")
                    if ncc_id and ncc_id in cn_tra_ncc:
                        combo = _to_hop(cn_tra_ncc[ncc_id], ra)
                        if combo:
                            nc0 = next((n for n in ds_ncc if n.id == ncc_id), None)
                            r["goi_y_chi"] = {"ncc_id": ncc_id,
                                              "ncc_ten": nc0.ten if nc0 else "",
                                              "cong_no_ids": [c["cong_no_id"] for c in combo],
                                              "so_hd": ", ".join(str(c["so_ct"] or ("CN" + str(c["cong_no_id"]))) for c in combo)[:80],
                                              "tong": sum(c["con_lai"] for c in combo)}
        elif vao > 0:
            best = None
            for u0 in vao_thu:
                if u0["thanh_toan_id"] in dung_vao or abs(u0["so_tien"] - vao) > 0.5:
                    continue
                le = _lech(u0["ngay"])
                if le > 3:
                    continue
                if best is None or le < best[0]:
                    best = (le, u0)
            if best is not None:
                dung_vao.add(best[1]["thanh_toan_id"])
                r["thu"] = best[1]
                r["ma_ban"] = best[1]["ma_ban"]
            else:
                u = _tim(phieu_vao, vao, dung_pvao, 3)
                if u is not None:
                    dung_pvao.add(u["id"])
                    r["da_xu_ly"] = {"mo_ta": u["mo_ta"]}
                    r["ma_ban"] = u.get("ma_ban")
                elif r["phan_loai"] is None:
                    gy = next((g for g in goi_y_cn if abs(g["con_lai"] - vao) <= 0.5), None)
                    if gy is not None:
                        r["goi_y_thu"] = gy
                        r["ma_ban"] = gy["ma_ban"]
        out.append(r)
    return {"id": sk.id, "ten_file": sk.ten_file, "ngan_hang": sk.ngan_hang,
            "tu_ngay": str(sk.tu_ngay) if sk.tu_ngay else None,
            "den_ngay": str(sk.den_ngay) if sk.den_ngay else None, "dong": out}


@router.put("/sao-ke-dong/{d_id}/ghi-chu")
def sao_ke_dong_ghi_chu(d_id: int, ghi_chu: str = "", db: Session = Depends(get_db),
                        nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    from ..models import SaoKeDong
    d = db.get(SaoKeDong, d_id)
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dòng sao kê")
    d.ghi_chu = (ghi_chu or "").strip()[:300] or None
    db.commit()
    return {"ok": True}


class SkGhiVao(_BM_hdc):
    quy_id: int
    don_mua_id: int | None = None
    cong_no_id: int | None = None
    sao_ke_dong_id: int | None = None
    so_tien: Decimal | None = None


@router.post("/sao-ke/ghi-chi")
def sao_ke_ghi_chi(data: SkGhiVao, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """✔ ĐÃ CHI: tạo PHIẾU CHI chờ duyệt (qua hạn mức + quỹ như mọi phiếu) + đánh dấu
    lệnh ngân hàng ĐÃ CHI + gắn vết vào dòng sao kê (nếu ghi từ Danh mục thanh toán)."""
    from ..models import DonMua, LenhChiBank, SaoKeDong
    from ..nhac_viec_service import gio_hien_tai
    if not data.don_mua_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Thiếu đơn mua")
    dm = db.get(DonMua, data.don_mua_id)
    if dm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn mua")
    so_tien = Decimal(str(int(float(data.so_tien or 0))))
    if so_tien <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Số tiền phải lớn hơn 0")
    d0 = db.get(SaoKeDong, data.sao_ke_dong_id) if data.sao_ke_dong_id else None
    cn = db.query(CongNo).filter_by(don_mua_id=dm.id).first()
    p = PhieuThuChi(loai="CHI", quy_id=data.quy_id, so_tien=so_tien,
                    ngay=(d0.ngay if (d0 is not None and d0.ngay) else date.today()),
                    dien_giai=(f"Chi ngân hàng theo sao kê — PO {dm.so or dm.id}")[:200],
                    nha_cung_cap_id=dm.nha_cung_cap_id, cong_no_id=(cn.id if cn else None),
                    don_hang_id=dm.don_hang_id, trang_thai="CHO_DUYET",
                    nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(p)
    db.flush()
    p.so = f"PC-{date.today():%Y%m%d}-{p.id}"
    dm.cho_lenh_bank = False
    lcb = (db.query(LenhChiBank).filter_by(don_mua_id=dm.id, trang_thai="DA_DUYET")
           .order_by(LenhChiBank.id.desc()).first())
    if lcb is not None:
        lcb.trang_thai = "DA_CHI"
        lcb.chi_luc = gio_hien_tai()
    if d0 is not None:
        d0.khop_loai = "DA_CHI_SK"
        d0.khop_id = p.id
        d0.khop_mo_ta = (f"Phiếu {p.so} — PO {dm.so or dm.id} (chờ duyệt phiếu)")[:300]
    ghi_audit(db, nd.id, "SAO_KE_GHI_CHI", "phieu_thu_chi", p.id,
              moi={"po": dm.so, "so_tien": float(so_tien), "quy_id": data.quy_id})
    db.commit()
    return {"ok": True, "phieu_so": p.so}


@router.post("/sao-ke/ghi-thu")
def sao_ke_ghi_thu(data: SkGhiVao, db: Session = Depends(get_db),
                   nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """✔ GHI THU: tạo PHIẾU THU cấn công nợ bán hàng (chờ duyệt) từ dòng sao kê tiền vào."""
    from ..models import SaoKeDong
    if not data.cong_no_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Thiếu công nợ")
    cn = db.query(CongNo).filter_by(id=data.cong_no_id).with_for_update().first()
    if cn is None or cn.loai != "PHAI_THU":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Công nợ không hợp lệ (phải là PHẢI THU)")
    so_tien = Decimal(str(int(float(data.so_tien or 0))))
    con_lai = Decimal(cn.so_tien or 0) - Decimal(cn.da_thanh_toan or 0)
    if so_tien <= 0 or so_tien > con_lai:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Số tiền phải > 0 và không vượt còn phải thu ({float(con_lai):,.0f}đ)")
    d0 = db.get(SaoKeDong, data.sao_ke_dong_id) if data.sao_ke_dong_id else None
    p = PhieuThuChi(loai="THU", quy_id=data.quy_id, so_tien=so_tien,
                    ngay=(d0.ngay if (d0 is not None and d0.ngay) else date.today()),
                    dien_giai=(f"Thu ngân hàng theo sao kê — công nợ #CN{cn.id}"
                               + (f" · HĐ {cn.so_ct}" if cn.so_ct else ""))[:200],
                    khach_hang_id=cn.khach_hang_id, cong_no_id=cn.id,
                    don_hang_id=cn.don_hang_id, trang_thai="CHO_DUYET",
                    nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(p)
    db.flush()
    p.so = f"PT-{date.today():%Y%m%d}-{p.id}"
    if d0 is not None:
        d0.khop_loai = "GHI_THU_SK"
        d0.khop_id = p.id
        d0.khop_mo_ta = (f"Phiếu {p.so} — thu công nợ #CN{cn.id} (chờ duyệt phiếu)")[:300]
    ghi_audit(db, nd.id, "SAO_KE_GHI_THU", "phieu_thu_chi", p.id,
              moi={"cong_no_id": cn.id, "so_tien": float(so_tien), "quy_id": data.quy_id})
    db.commit()
    return {"ok": True, "phieu_so": p.so}


class SkTaoPhieuVao(_BM_hdc):
    quy_id: int
    tk_doi_ung: str | None = None


@router.post("/sao-ke-dong/{d_id}/tao-phieu")
def sao_ke_tao_phieu(d_id: int, data: SkTaoPhieuVao, db: Session = Depends(get_db),
                     nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """➕ Tạo phiếu thu/chi từ 1 dòng sao kê CHƯA có trong app (nội bộ / phí / lương /
    khoản lịch sử...) — phiếu CHỜ DUYỆT, TK đối ứng chọn từ danh mục."""
    from ..models import SaoKeDong
    d = db.get(SaoKeDong, d_id)
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dòng sao kê")
    if d.khop_loai in ("DA_CHI_SK", "GHI_THU_SK", "PHIEU_SK"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dòng này đã được ghi phiếu rồi")
    vao = float(d.tien_vao or 0)
    ra = float(d.tien_ra or 0)
    so_tien = Decimal(str(int(vao or ra)))
    if so_tien <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dòng không có số tiền")
    tk = (data.tk_doi_ung or "").strip()[:20] or None
    TK_HOP_LE = {"111", "112", "113", "131", "141", "331", "334", "3331", "3334",
                 "3383", "3384", "3386", "411", "341", "515", "635", "642", "711", "811", "1331"}
    if tk and tk not in TK_HOP_LE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"TK '{tk}' không thuộc danh mục cho phép: " + ", ".join(sorted(TK_HOP_LE)))
    p = PhieuThuChi(loai=("THU" if vao > 0 else "CHI"), quy_id=data.quy_id, so_tien=so_tien,
                    ngay=(d.ngay or date.today()),
                    dien_giai=(f"[Sao kê] {(d.dien_giai or '')}")[:200],
                    tk_doi_ung=tk, trang_thai="CHO_DUYET",
                    nguoi_tao=nhan_vien_id_cua(db, nd.id))
    db.add(p)
    db.flush()
    p.so = f"{'PT' if vao > 0 else 'PC'}-{date.today():%Y%m%d}-{p.id}"
    d.khop_loai = "PHIEU_SK"
    d.khop_id = p.id
    d.khop_mo_ta = (f"Phiếu {p.so} (chờ duyệt)" + (f" · TK {tk}" if tk else ""))[:300]
    ghi_audit(db, nd.id, "SAO_KE_TAO_PHIEU", "phieu_thu_chi", p.id,
              moi={"sao_ke_dong": d.id, "so_tien": float(so_tien), "tk": tk})
    db.commit()
    return {"ok": True, "phieu_so": p.so}


class SkGhiGopVao(_BM_hdc):
    quy_id: int
    cong_no_ids: list[int]


@router.post("/sao-ke-dong/{d_id}/ghi-chi-gop")
def sao_ke_ghi_chi_gop(d_id: int, data: SkGhiGopVao, db: Session = Depends(get_db),
                       nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """✔ GHI CHI GỘP: 1 dòng sao kê trả NHIỀU hóa đơn — tạo mỗi công nợ 1 phiếu chi
    (số tiền = còn lại của khoản đó), tất cả CHỜ DUYỆT."""
    from ..models import SaoKeDong, NhaCungCap
    d = db.get(SaoKeDong, d_id)
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dòng sao kê")
    if d.khop_loai in ("DA_CHI_SK", "GHI_THU_SK", "PHIEU_SK"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dòng này đã được ghi rồi")
    ra = float(d.tien_ra or 0)
    if ra <= 0 or not data.cong_no_ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dòng phải là tiền ra và chọn ít nhất 1 công nợ")
    cns = [db.query(CongNo).filter_by(id=cid).with_for_update().first() for cid in data.cong_no_ids[:5]]
    cns = [c for c in cns if c is not None and c.loai == "PHAI_TRA"]
    if not cns:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không tìm thấy công nợ hợp lệ")
    tong_cn = sum(float(c.so_tien or 0) - float(c.da_thanh_toan or 0) for c in cns)
    if abs(tong_cn - ra) > max(1000.0, ra * 0.01):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Tổng còn lại các công nợ ({tong_cn:,.0f}đ) lệch quá 1% so với dòng sao kê ({ra:,.0f}đ)")
    so_phieu = []
    for c in cns:
        con = Decimal(str(int(float(c.so_tien or 0) - float(c.da_thanh_toan or 0))))
        if con <= 0:
            continue
        nc0 = db.get(NhaCungCap, c.nha_cung_cap_id) if c.nha_cung_cap_id else None
        p = PhieuThuChi(loai="CHI", quy_id=data.quy_id, so_tien=con,
                        ngay=(d.ngay or date.today()),
                        dien_giai=(f"[Sao kê gộp] trả {nc0.ten if nc0 else 'NCC'}"
                                   + (f" — HĐ {c.so_ct}" if c.so_ct else f" — CN{c.id}"))[:200],
                        nha_cung_cap_id=c.nha_cung_cap_id, cong_no_id=c.id,
                        don_hang_id=c.don_hang_id, trang_thai="CHO_DUYET",
                        nguoi_tao=nhan_vien_id_cua(db, nd.id))
        db.add(p)
        db.flush()
        p.so = f"PC-{date.today():%Y%m%d}-{p.id}"
        so_phieu.append(p.so)
    d.khop_loai = "PHIEU_SK"
    d.khop_mo_ta = (f"{len(so_phieu)} phiếu chi gộp: " + ", ".join(so_phieu) + " (chờ duyệt)")[:300]
    ghi_audit(db, nd.id, "SAO_KE_GHI_CHI_GOP", "sao_ke_dong", d.id,
              moi={"phieu": so_phieu, "tong": float(ra), "quy_id": data.quy_id})
    db.commit()
    return {"ok": True, "so_phieu": so_phieu}
