"""🪪 VỊ TRÍ / CHỨC DANH do CEO tự tạo (anh Hiếu 16/11/2026, mig 170).

Trước đây droplist «Vai trò» ở Cấu hình › Tạo người dùng chỉ có các vị trí seed sẵn (bảng vai_tro). Nay CEO thêm được vị trí
mới ngay trong app:
  • tên → app tự đặt MÃ (in hoa, không dấu, ≤ 20 ký tự; «Trưởng phòng…» → TP_…, «Nhân viên…» → NV_…), hoặc CEO tự gõ mã;
  • QUYỀN: chép từ một vị trí mẫu (không chép từ CEO / ADMIN) hoặc để trống rồi chấm ở bảng «Phân quyền theo vị trí»;
  • tự sinh khung «Mô tả công việc» (JD) trống để vị trí hiện ở trang KPI & mô tả công việc.
Vị trí seed sẵn (tu_tao = False) có MÃ dùng trong code (chi_vai_tro("KTT", "CEO")…) → không đổi tên, không xóa.
Vị trí tự tạo: đổi tên được; xóa được khi không còn tài khoản nào dùng và chưa có kỳ đánh giá KPI.
Các hàm ném ValueError (dữ liệu sai) / LookupError (không tìm thấy) — router đổi thành HTTP 400 / 404.
"""
import re
import unicodedata
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from .audit import ghi_audit
from .config import settings
from .models import DanhGiaKy, HanMucDuyet, KpiViTri, MoTaCongViec, NguoiDung, PhanQuyen, VaiTro

MA_TOI_DA = 20
KHONG_LAM_MAU = ("CEO", "ADMIN")          # không chép quyền từ hai vị trí này — muốn cấp thì CEO chấm tay ở ma trận
# cụm đầu tên → viết tắt quen dùng trong mã (so trên chữ không dấu, in hoa); cụm dài đứng trước
_VIET_TAT = (("PHO GIAM DOC", "PGD"), ("GIAM DOC", "GD"), ("TRUONG PHONG", "TP"), ("TRUONG P", "TP"), ("PHO PHONG", "PP"),
             ("TRUONG NHOM", "TN"), ("TRUONG BO PHAN", "TBP"), ("TRUONG DU AN", "TDA"), ("TRUONG", "T"),
             ("NHAN VIEN", "NV"), ("CHUYEN VIEN", "CV"), ("KY THUAT VIEN", "KTV"), ("KY SU", "KS"),
             ("KE TOAN", "KT"), ("TRO LY", "TL"), ("THU KY", "TK"), ("QUAN LY", "QL"), ("GIAM SAT", "GS"),
             ("CONG NHAN", "CN"), ("THUC TAP SINH", "TTS"), ("TAI XE", "TX"), ("BAO VE", "BV"))


def _bay_gio() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=settings.tz_offset_gio)


def khong_dau(s) -> str:
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D")


def ten_chuan(s) -> str:
    """Tên để so trùng: bỏ dấu, chữ thường, gộp khoảng trắng, bỏ ký tự lạ."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", khong_dau(s).lower()).split())


def ma_tu_ten(ten) -> str:
    """Đặt mã từ tên: «Trưởng phòng Kỹ thuật» → TP_KY_THUAT · «Kỹ sư vận hành» → KS_VAN_HANH · quá 20 ký tự thì phần sau
    lấy chữ cái đầu («Trưởng phòng Kỹ thuật Công nghệ» → TP_KTCN). Không ra được gì (tên toàn ký hiệu) → VI_TRI."""
    tu = re.sub(r"[^A-Z0-9]+", " ", khong_dau(ten).upper()).split()
    if not tu:
        return "VI_TRI"
    chuoi = " ".join(tu)
    dau = ""
    for cum, vt in _VIET_TAT:
        if chuoi == cum or chuoi.startswith(cum + " "):
            dau, tu = vt, chuoi[len(cum):].split()
            break
    day_du = "_".join(([dau] if dau else []) + tu)
    if len(day_du) <= MA_TOI_DA:
        ma = day_du
    else:
        chu_dau = "".join(w[0] for w in tu)
        ma = (f"{dau}_{chu_dau}" if dau and chu_dau else (dau or chu_dau))[:MA_TOI_DA]
    ma = ma.strip("_") or "VI_TRI"
    return ma if ma[0].isalpha() else ("VT_" + ma)[:MA_TOI_DA]


def ma_hop_le(ma) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Z0-9_]{1,19}", str(ma or "")))


def _ma_chua_dung(db: Session, ma: str) -> str:
    """Mã đã có → thêm _2, _3… (cắt bớt cho vừa 20 ký tự)."""
    da_co = {m.upper() for (m,) in db.query(VaiTro.ma).all()}
    if ma not in da_co:
        return ma
    for i in range(2, 100):
        duoi = f"_{i}"
        thu = ma[:MA_TOI_DA - len(duoi)].rstrip("_") + duoi
        if thu not in da_co:
            return thu
    raise ValueError("Không đặt được mã cho vị trí này — hãy tự nhập mã.")


def _dem_theo_vai_tro(db: Session) -> tuple[dict, dict, dict, set, set]:
    nd = dict(db.query(NguoiDung.vai_tro_id, func.count(NguoiDung.id)).group_by(NguoiDung.vai_tro_id).all())
    pq = dict(db.query(PhanQuyen.vai_tro_id, func.count(PhanQuyen.id)).group_by(PhanQuyen.vai_tro_id).all())
    kpi = dict(db.query(KpiViTri.vai_tro, func.count(KpiViTri.id)).group_by(KpiViTri.vai_tro).all())
    dg = {m for (m,) in db.query(DanhGiaKy.vai_tro).filter(DanhGiaKy.vai_tro.isnot(None)).distinct().all()}
    jd = {m for (m,) in db.query(MoTaCongViec.vai_tro).all()}
    return nd, pq, kpi, dg, jd


def _ra(v: VaiTro, nd: dict, pq: dict, kpi: dict, dg: set, jd: set) -> dict:
    so_nd = int(nd.get(v.id, 0))
    tu_tao = bool(getattr(v, "tu_tao", False))
    return {"ma": v.ma, "ten": v.ten, "tu_tao": tu_tao, "ghi_chu": getattr(v, "ghi_chu", None),
            "tao_luc": v.tao_luc.isoformat(timespec="minutes") if getattr(v, "tao_luc", None) else None,
            "so_nguoi_dung": so_nd, "so_quyen": int(pq.get(v.id, 0)), "so_kpi": int(kpi.get(v.ma, 0)),
            "co_danh_gia": v.ma in dg, "co_jd": v.ma in jd,
            "lam_mau_duoc": v.ma not in KHONG_LAM_MAU,
            "sua_duoc": tu_tao, "xoa_duoc": tu_tao and so_nd == 0 and v.ma not in dg}


def danh_sach(db: Session) -> list[dict]:
    """Mọi vị trí (theo id) kèm số tài khoản đang dùng, số module có quyền, số KPI — cho bảng ở Cấu hình."""
    nd, pq, kpi, dg, jd = _dem_theo_vai_tro(db)
    return [_ra(v, nd, pq, kpi, dg, jd) for v in db.query(VaiTro).order_by(VaiTro.id).all()]


def mot(db: Session, v: VaiTro) -> dict:
    nd, pq, kpi, dg, jd = _dem_theo_vai_tro(db)
    return _ra(v, nd, pq, kpi, dg, jd)


def ten_vai_tro(db: Session) -> list[dict]:
    """Mã → tên cho MỌI người đã đăng nhập (dựng nhãn / gợi ý chức danh ở Hồ sơ lương) — không kèm số liệu."""
    return [{"ma": v.ma, "ten": v.ten, "tu_tao": bool(getattr(v, "tu_tao", False))}
            for v in db.query(VaiTro).order_by(VaiTro.id).all()]


def _kiem_ten(db: Session, ten, bo_qua_id=None) -> str:
    ten = " ".join(str(ten or "").split())
    if len(ten) < 2:
        raise ValueError("Nhập tên vị trí / chức danh (ít nhất 2 ký tự).")
    if len(ten) > 120:
        raise ValueError("Tên vị trí tối đa 120 ký tự.")
    chuan = ten_chuan(ten)
    for v in db.query(VaiTro).all():
        if v.id != bo_qua_id and ten_chuan(v.ten) == chuan:
            raise ValueError(f"Đã có vị trí «{v.ten}» (mã {v.ma}) — không tạo trùng tên.")
    return ten


def tao(db: Session, nguoi_dung_id, ten, ma=None, sao_chep_tu=None, ghi_chu=None) -> dict:
    """Tạo vị trí mới (+ chép quyền từ vị trí mẫu, + khung JD). Chưa commit — nơi gọi commit."""
    ten = _kiem_ten(db, ten)
    ma = str(ma or "").strip().upper()
    if ma:
        ma = re.sub(r"[\s\-]+", "_", khong_dau(ma))
        if not ma_hop_le(ma):
            raise ValueError("Mã vị trí: 2–20 ký tự, chỉ chữ in hoa không dấu, số và dấu gạch dưới, bắt đầu bằng chữ (vd KS_VAN_HANH).")
        if db.query(VaiTro).filter(func.upper(VaiTro.ma) == ma).first() is not None:
            raise ValueError(f"Mã «{ma}» đã có — chọn mã khác hoặc để trống cho app tự đặt.")
    else:
        ma = _ma_chua_dung(db, ma_tu_ten(ten))
    mau = None
    sao_chep_tu = str(sao_chep_tu or "").strip().upper()
    if sao_chep_tu:
        if sao_chep_tu in KHONG_LAM_MAU:
            raise ValueError("Không chép quyền từ CEO / ADMIN. Hãy chọn vị trí khác làm mẫu, hoặc để trống rồi chấm quyền ở bảng «Phân quyền theo vị trí».")
        mau = db.query(VaiTro).filter_by(ma=sao_chep_tu).first()
        if mau is None:
            raise LookupError("Không tìm thấy vị trí mẫu để chép quyền.")
    v = VaiTro(ma=ma, ten=ten, tu_tao=True, ghi_chu=(" ".join(str(ghi_chu or "").split())[:300] or None), tao_luc=_bay_gio())
    db.add(v)
    db.flush()
    so_quyen = 0
    if mau is not None:
        for pq in db.query(PhanQuyen).filter_by(vai_tro_id=mau.id).all():
            if pq.muc and pq.muc != "KHONG":
                db.add(PhanQuyen(vai_tro_id=v.id, module=pq.module, muc=pq.muc))
                so_quyen += 1
    if db.query(MoTaCongViec).filter_by(vai_tro=ma).first() is None:        # khung JD trống → vị trí hiện ở trang KPI & mô tả CV
        db.add(MoTaCongViec(vai_tro=ma, chuc_danh=ten[:150]))
    db.flush()
    ghi_audit(db, nguoi_dung_id, "TAO", "vai_tro", v.id,
              moi={"ma": ma, "ten": ten, "sao_chep_tu": mau.ma if mau else None, "so_quyen": so_quyen, "ghi_chu": v.ghi_chu})
    return {**mot(db, v), "sao_chep_tu": mau.ma if mau else None, "sao_chep_ten": mau.ten if mau else None,
            "so_quyen_chep": so_quyen}


def _tim(db: Session, ma) -> VaiTro:
    v = db.query(VaiTro).filter_by(ma=str(ma or "").strip().upper()).first()
    if v is None:
        raise LookupError("Không tìm thấy vị trí.")
    return v


def sua(db: Session, nguoi_dung_id, ma, ten=None, ghi_chu=None) -> dict:
    """Đổi tên / ghi chú vị trí TỰ TẠO (mã giữ nguyên — tài khoản và quyền không đổi)."""
    v = _tim(db, ma)
    if not getattr(v, "tu_tao", False):
        raise ValueError(f"«{v.ten}» là vị trí có sẵn của hệ thống — không đổi tên. Cần tên khác thì tạo vị trí mới.")
    cu = {"ten": v.ten, "ghi_chu": v.ghi_chu}
    if ten is not None:
        ten_moi = _kiem_ten(db, ten, bo_qua_id=v.id)
        jd = db.query(MoTaCongViec).filter_by(vai_tro=v.ma).first()
        if jd is not None and (jd.chuc_danh or "") == (v.ten or "")[:150]:      # JD còn mang tên cũ → đổi theo
            jd.chuc_danh = ten_moi[:150]
        v.ten = ten_moi
    if ghi_chu is not None:
        v.ghi_chu = " ".join(str(ghi_chu).split())[:300] or None
    ghi_audit(db, nguoi_dung_id, "SUA", "vai_tro", v.id, cu=cu, moi={"ma": v.ma, "ten": v.ten, "ghi_chu": v.ghi_chu})
    db.flush()
    return mot(db, v)


def xoa(db: Session, nguoi_dung_id, ma) -> dict:
    """Xóa vị trí TỰ TẠO khi không còn tài khoản dùng và chưa có kỳ đánh giá KPI; kèm quyền, hạn mức, KPI, JD của vị trí."""
    v = _tim(db, ma)
    if not getattr(v, "tu_tao", False):
        raise ValueError(f"«{v.ten}» là vị trí có sẵn của hệ thống — không xóa được.")
    dung = db.query(NguoiDung.email).filter(NguoiDung.vai_tro_id == v.id).order_by(NguoiDung.id).all()
    if dung:
        ds = ", ".join(e for (e,) in dung[:5]) + (f" … (+{len(dung) - 5})" if len(dung) > 5 else "")
        raise ValueError(f"Còn {len(dung)} tài khoản đang ở vị trí «{v.ten}»: {ds}. Chuyển họ sang vị trí khác (✏️ Sửa) rồi mới xóa.")
    if db.query(DanhGiaKy.id).filter(DanhGiaKy.vai_tro == v.ma).first() is not None:
        raise ValueError(f"Vị trí «{v.ten}» đã có kỳ đánh giá KPI — giữ lại để không mất lịch sử đánh giá.")
    so_pq = db.query(PhanQuyen).filter_by(vai_tro_id=v.id).delete(synchronize_session=False)
    so_hm = db.query(HanMucDuyet).filter_by(vai_tro_id=v.id).delete(synchronize_session=False)
    so_kpi = db.query(KpiViTri).filter_by(vai_tro=v.ma).delete(synchronize_session=False)
    so_jd = db.query(MoTaCongViec).filter_by(vai_tro=v.ma).delete(synchronize_session=False)
    kq = {"ok": True, "ma": v.ma, "ten": v.ten, "so_quyen": so_pq, "so_han_muc": so_hm, "so_kpi": so_kpi, "so_jd": so_jd}
    ghi_audit(db, nguoi_dung_id, "XOA", "vai_tro", v.id, cu={k: kq[k] for k in ("ma", "ten", "so_quyen", "so_han_muc", "so_kpi", "so_jd")})
    db.delete(v)
    db.flush()
    return kq
