"""
KẾ TOÁN — Quản lý tiền mặt (quỹ/sổ quỹ) + Phiếu thu/chi có DUYỆT NHIỀU CẤP,
tự hạch toán kép vào sổ cái, cấn trừ công nợ, và TRUY VẾT theo MÃ HÀNG BÁN.

Luồng phiếu: NHAP -> CHO_DUYET -> DA_DUYET (theo hạn mức loại 'thu_chi') / TU_CHOI / HUY.
Chỉ phiếu ĐÃ DUYỆT mới: chuyển tiền quỹ + sinh bút toán + cấn trừ công nợ.
"""
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..rbac import yeu_cau, kiem_han_muc
from ..audit import ghi_audit
from ..deps import nhan_vien_id_cua
from ..models import (NguoiDung, TaiKhoanQuy, PhieuThuChi, ButToan, CongNo,
                      DonHang, DonMua, KhachHang, NhaCungCap, HoaDon)
from ..schemas import QuyVao, PhieuVao, DuyetPhieuVao, HoaDonVao, DatCocVao
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


# ---------- QUỸ TIỀN ----------
@router.get("/quy")
def ds_quy(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    return [_quy_dict(q) for q in db.query(TaiKhoanQuy).order_by(TaiKhoanQuy.id).all()]


@router.post("/quy", status_code=201)
def tao_quy(data: QuyVao, db: Session = Depends(get_db),
            nd: NguoiDung = Depends(yeu_cau(MODULE, "THAO_TAC"))):
    ma = data.ma or ("Q" + str(int(date.today().strftime("%y%m%d"))))
    if db.query(TaiKhoanQuy).filter_by(ma=ma).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mã quỹ đã tồn tại")
    q = TaiKhoanQuy(ma=ma, ten=data.ten, loai=data.loai, so_tk=data.so_tk,
                    tk_ke_toan=data.tk_ke_toan, so_du_dau=data.so_du_dau, so_du=data.so_du_dau)
    db.add(q); db.flush()
    ghi_audit(db, nd.id, "TAO", "tai_khoan_quy", q.id, moi={"ma": ma})
    db.commit(); db.refresh(q)
    return _quy_dict(q)


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
    quy = db.get(TaiKhoanQuy, p.quy_id)
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
    p.trang_thai = "HUY"
    ghi_audit(db, nd.id, "HUY", "phieu_thu_chi", p.id)
    db.commit(); db.refresh(p)
    return _phieu_dict(db, p)


# ---------- TỔNG QUAN ----------
@router.get("/tong-quan")
def tong_quan(db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    tong_quy = _f(db.query(func.coalesce(func.sum(TaiKhoanQuy.so_du), 0)).scalar())
    pt = _f(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
            .filter(CongNo.loai == "PHAI_THU").scalar())
    ptr = _f(db.query(func.coalesce(func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
             .filter(CongNo.loai == "PHAI_TRA").scalar())
    cho_duyet = db.query(func.count(PhieuThuChi.id)).filter(PhieuThuChi.trang_thai == "CHO_DUYET").scalar()
    return {"tong_quy": tong_quy, "phai_thu": pt, "phai_tra": ptr,
            "phieu_cho_duyet": int(cho_duyet or 0),
            "quy": [_quy_dict(q) for q in db.query(TaiKhoanQuy).order_by(TaiKhoanQuy.id).all()]}


# ---------- THỐNG KÊ THU–CHI (dòng tiền) ----------
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
            "don_hang_id": hd.don_hang_id, "ma_ban": _ma_ban(db, hd.don_hang_id),
            "tien_truoc_thue": _f(hd.tien_truoc_thue), "tien_thue": _f(hd.tien_thue),
            "tong_tien": _f(hd.tong_tien), "tk_chi_phi": hd.tk_chi_phi,
            "dien_giai": hd.dien_giai, "da_hach_toan": bool(hd.da_hach_toan),
            "trang_thai": hd.trang_thai, "hddt_trang_thai": hd.hddt_trang_thai,
            "hddt_ma_tra_cuu": hd.hddt_ma_tra_cuu, "cong_no": _cong_no_cua_hd(db, hd.id)}


@router.get("/hoa-don")
def ds_hoa_don(loai: str | None = None, db: Session = Depends(get_db),
               _=Depends(yeu_cau(MODULE, "XEM"))):
    q = db.query(HoaDon)
    if loai:
        q = q.filter(HoaDon.loai == loai)
    return [_hd_dict(db, h) for h in q.order_by(HoaDon.id.desc()).all()]


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
                tk_chi_phi=data.tk_chi_phi, dien_giai=data.dien_giai,
                hddt_trang_thai="CHUA_PHAT_HANH" if data.loai == "BAN" else None,
                trang_thai="GHI_NHAN")
    db.add(hd); db.flush()
    hd.so = data.so or f"{'HDB' if data.loai == 'BAN' else 'HDM'}-{date.today():%Y%m%d}-{hd.id}"
    # sinh công nợ
    cn = None
    if data.tao_cong_no:
        from datetime import timedelta
        han = date.today() + timedelta(days=int(data.han_ngay or 30))
        if data.loai == "BAN":
            cn = CongNo(loai="PHAI_THU", hoa_don_id=hd.id, khach_hang_id=kh_id,
                        so_tien=tong, da_thanh_toan=0, han=han, trang_thai="CHUA_THU")
        else:
            cn = CongNo(loai="PHAI_TRA", hoa_don_id=hd.id, nha_cung_cap_id=data.nha_cung_cap_id,
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
                .order_by(PhieuThuChi.id).all())
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
    doanh_thu = _f(dh.tong_tien)
    gia_von = _f(db.query(func.coalesce(func.sum(DonMua.tong_tien), 0))
                 .filter(DonMua.don_hang_id == dh.id).scalar())
    chi_phi = _f(db.query(func.coalesce(func.sum(PhieuThuChi.so_tien), 0))
                 .filter(PhieuThuChi.don_hang_id == dh.id, PhieuThuChi.loai == "CHI",
                         PhieuThuChi.trang_thai == "DA_DUYET",
                         PhieuThuChi.la_tam_ung.is_(False),
                         func.coalesce(PhieuThuChi.tk_doi_ung, "") != "331").scalar())
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
            "loi_nhuan": loi_nhuan,
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
