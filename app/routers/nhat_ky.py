"""📜 Nhật ký hệ thống (rà app 31/10/2026, mục C5; làm 01/11/2026).

CEO / ADMIN tra lại bảng `audit_log` — nơi app ghi vết mọi thao tác (dự toán, duyệt PO, vượt cổng biên, nhắc tuần, sao lưu…):
  • lọc theo bảng, hành động, người, bản ghi, khoảng ngày (giờ Việt Nam) và chuỗi trong giá trị cũ / mới
    (vd gõ mã đơn hàng «TM-SIC-1026» để thấy mọi vết có nhắc tới mã đó);
  • 100 dòng / trang, mới nhất lên trên; kèm tên người (hồ sơ nhân viên, thiếu thì email tài khoản) và giờ đã đổi sang VN;
  • danh sách bảng / hành động / người có trong dữ liệu để dựng ô chọn; xuất Excel theo cùng bộ lọc.
Chỉ ĐỌC — không ghi gì vào CSDL. Không có migration.
"""
import io
import json
from datetime import date, datetime, timedelta, timezone
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import Text, cast, func, or_
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import AuditLog, NguoiDung, NhanVien
from ..rbac import chi_vai_tro

router = APIRouter(prefix="/nhat-ky", tags=["nhat_ky"])

MOI_TRANG = 100            # số dòng mỗi trang
TOI_DA_EXCEL = 20000       # trần số dòng một file Excel
HE_THONG = "⚙ Hệ thống (tự động)"   # nguoi_dung_id NULL: scheduler, sao lưu, nhắc tuần…


# ---------------------------------------------------------------- giờ Việt Nam
def _tz_vn():
    return timezone(timedelta(hours=settings.tz_offset_gio))


def sang_gio_vn(t: datetime | None) -> datetime | None:
    """Cột TIMESTAMPTZ trả về có múi giờ → đổi sang VN. Giá trị naive (SQLite khi test) coi là UTC."""
    if t is None:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return t.astimezone(_tz_vn())


def _bay_gio_vn() -> datetime:
    return datetime.now(timezone.utc).astimezone(_tz_vn())


def doc_ngay(s: str | None, ten: str) -> date | None:
    """Ô ngày trên giao diện gửi YYYY-MM-DD; chấp nhận cả dd/mm/yyyy gõ tay."""
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise HTTPException(422,
                        f"Ngày «{ten}» không hợp lệ: {s} (dùng YYYY-MM-DD hoặc dd/mm/yyyy)")


def _moc_utc(d: date, cuoi_ngay: bool = False) -> datetime:
    """0h ngày d (hoặc 0h ngày hôm sau nếu cuoi_ngay) THEO GIỜ VN → thời điểm UTC để so với cột thoi_gian."""
    if cuoi_ngay:
        d = d + timedelta(days=1)
    return datetime(d.year, d.month, d.day, tzinfo=_tz_vn()).astimezone(timezone.utc)


# ---------------------------------------------------------------- bộ lọc
def _thoat_like(q: str) -> str:
    return q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def dieu_kien(bang=None, hanh_dong=None, nguoi_dung_id=None, ban_ghi_id=None, tu=None, den=None, q=None) -> list:
    """Điều kiện SQL theo bộ lọc. nguoi_dung_id = 0 nghĩa là «hệ thống» (cột NULL)."""
    if tu and den and tu > den:
        raise HTTPException(422, "Khoảng ngày ngược: «từ» phải không sau «đến»")
    dk = []
    if bang:
        dk.append(AuditLog.bang == bang)
    if hanh_dong:
        dk.append(AuditLog.hanh_dong == hanh_dong)
    if nguoi_dung_id is not None:
        dk.append(AuditLog.nguoi_dung_id.is_(None) if nguoi_dung_id == 0 else AuditLog.nguoi_dung_id == nguoi_dung_id)
    if ban_ghi_id is not None:
        dk.append(AuditLog.ban_ghi_id == ban_ghi_id)
    if tu:
        dk.append(AuditLog.thoi_gian >= _moc_utc(tu))
    if den:
        dk.append(AuditLog.thoi_gian < _moc_utc(den, cuoi_ngay=True))
    q = (q or "").strip()
    if q:
        mau = f"%{_thoat_like(q)}%"
        dk.append(or_(cast(AuditLog.gia_tri_cu, Text).ilike(mau, escape="\\"),
                      cast(AuditLog.gia_tri_moi, Text).ilike(mau, escape="\\")))
    return dk


# ---------------------------------------------------------------- tên người
def ten_nguoi(db: Session, ids) -> dict:
    """{nguoi_dung_id: tên}: họ tên trong hồ sơ nhân viên, thiếu thì email tài khoản."""
    ids = {int(i) for i in ids if i is not None}
    if not ids:
        return {}
    ten = {uid: email for uid, email in db.query(NguoiDung.id, NguoiDung.email).filter(NguoiDung.id.in_(ids)).all()}
    # nhiều hồ sơ cùng tài khoản (hiếm): xếp id giảm để hồ sơ id nhỏ nhất ghi sau cùng → thắng
    for uid, ho_ten in (db.query(NhanVien.nguoi_dung_id, NhanVien.ho_ten)
                        .filter(NhanVien.nguoi_dung_id.in_(ids)).order_by(NhanVien.id.desc()).all()):
        if ho_ten:
            ten[uid] = ho_ten
    return ten


def _ten(uid, ten: dict) -> str:
    if uid is None:
        return HE_THONG
    return ten.get(uid) or f"Tài khoản #{uid}"


# ---------------------------------------------------------------- truy vấn
def bo_loc(db: Session) -> dict:
    """Bảng / hành động / người CÓ TRONG dữ liệu (một lượt GROUP BY) để dựng ô chọn; cap = cặp (bảng, hành động) kèm số dòng
    cho giao diện thu hẹp ô «hành động» theo bảng đã chọn."""
    rows = (db.query(AuditLog.bang, AuditLog.hanh_dong, AuditLog.nguoi_dung_id, func.count())
            .group_by(AuditLog.bang, AuditLog.hanh_dong, AuditLog.nguoi_dung_id).all())
    cap, nguoi = {}, {}
    for b, h, u, n in rows:
        cap[(b, h)] = cap.get((b, h), 0) + n
        nguoi[u] = nguoi.get(u, 0) + n
    ten = ten_nguoi(db, nguoi)
    ds_nguoi = [{"id": u or 0, "ten": _ten(u, ten), "so": n} for u, n in nguoi.items()]
    return {"bang": sorted({b for b, _ in cap}),
            "hanh_dong": sorted({h for _, h in cap}),
            "cap": [{"bang": b, "hanh_dong": h, "so": n} for (b, h), n in sorted(cap.items())],
            "nguoi": sorted(ds_nguoi, key=lambda x: (-x["so"], x["ten"]))}


def _dong(r: AuditLog, ten: dict) -> dict:
    t = sang_gio_vn(r.thoi_gian)
    return {"id": r.id, "thoi_gian": t.strftime("%d/%m/%Y %H:%M:%S") if t else None,
            "thoi_gian_iso": t.isoformat() if t else None,
            "nguoi_dung_id": r.nguoi_dung_id, "nguoi": _ten(r.nguoi_dung_id, ten),
            "hanh_dong": r.hanh_dong, "bang": r.bang, "ban_ghi_id": r.ban_ghi_id,
            "gia_tri_cu": r.gia_tri_cu, "gia_tri_moi": r.gia_tri_moi}


def truy_van(db: Session, *, trang: int = 1, kem_bo_loc: bool = True, **loc) -> dict:
    """Một trang nhật ký theo bộ lọc, mới nhất lên trên."""
    dk = dieu_kien(**loc)
    tong = db.query(func.count(AuditLog.id)).filter(*dk).scalar() or 0
    so_trang = max(1, ceil(tong / MOI_TRANG))
    trang = min(max(1, int(trang or 1)), so_trang)
    rows = (db.query(AuditLog).filter(*dk).order_by(AuditLog.thoi_gian.desc(), AuditLog.id.desc())
            .offset((trang - 1) * MOI_TRANG).limit(MOI_TRANG).all())
    ten = ten_nguoi(db, [r.nguoi_dung_id for r in rows])
    kq = {"tong": tong, "trang": trang, "so_trang": so_trang, "moi_trang": MOI_TRANG, "dong": [_dong(r, ten) for r in rows]}
    if kem_bo_loc:
        kq["bo_loc"] = bo_loc(db)
    return kq


# ---------------------------------------------------------------- Excel
def _json_text(v) -> str | None:
    if v is None:
        return None
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)
    return s if len(s) <= 32000 else s[:31990] + "…"      # ô Excel tối đa 32.767 ký tự


def mo_ta_bo_loc(ten_nguoi_chon: str | None = None, **loc) -> str:
    phan = []
    if loc.get("bang"):
        phan.append(f"bảng {loc['bang']}")
    if loc.get("hanh_dong"):
        phan.append(f"hành động {loc['hanh_dong']}")
    if loc.get("nguoi_dung_id") is not None:
        phan.append("người: " + (ten_nguoi_chon or (HE_THONG if loc["nguoi_dung_id"] == 0 else f"tài khoản #{loc['nguoi_dung_id']}")))
    if loc.get("ban_ghi_id") is not None:
        phan.append(f"bản ghi #{loc['ban_ghi_id']}")
    if loc.get("tu") or loc.get("den"):
        phan.append("từ " + (loc["tu"].strftime("%d/%m/%Y") if loc.get("tu") else "đầu")
                    + " đến " + (loc["den"].strftime("%d/%m/%Y") if loc.get("den") else "nay"))
    if (loc.get("q") or "").strip():
        phan.append(f"tìm «{loc['q'].strip()}»")
    return " · ".join(phan) if phan else "toàn bộ"


def xuat_excel(db: Session, **loc) -> bytes:
    """Excel một sheet theo cùng bộ lọc (tối đa TOI_DA_EXCEL dòng mới nhất)."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    dk = dieu_kien(**loc)
    rows = (db.query(AuditLog).filter(*dk).order_by(AuditLog.thoi_gian.desc(), AuditLog.id.desc())
            .limit(TOI_DA_EXCEL).all())
    ten = ten_nguoi(db, [r.nguoi_dung_id for r in rows] + [loc.get("nguoi_dung_id")])
    tong = db.query(func.count(AuditLog.id)).filter(*dk).scalar() or 0

    wb = Workbook()
    ws = wb.active
    ws.title = "Nhật ký"
    fill = PatternFill("solid", fgColor="E3EDF6")
    thin = Side(style="thin", color="C9D3DD")
    bdr = Border(left=thin, right=thin, top=thin, bottom=thin)
    ws["A1"] = f"SVWS — NHẬT KÝ HỆ THỐNG — xuất lúc {_bay_gio_vn():%d/%m/%Y %H:%M} (giờ VN)"
    ws["A1"].font = Font(bold=True, size=13)
    nguoi_chon = ten.get(loc.get("nguoi_dung_id")) if loc.get("nguoi_dung_id") else None
    ws["A2"] = (f"Bộ lọc: {mo_ta_bo_loc(nguoi_chon, **loc)} — {len(rows):,} dòng"
                + (f" (trong {tong:,} dòng khớp; chỉ xuất {TOI_DA_EXCEL:,} dòng mới nhất)" if tong > len(rows) else "")).replace(",", ".")
    ws["A2"].font = Font(italic=True, color="555555")
    cot = ["STT", "Thời gian (VN)", "Người", "Tài khoản #", "Hành động", "Bảng", "Bản ghi #", "Giá trị cũ", "Giá trị mới"]
    rong = [6, 19, 24, 11, 18, 22, 11, 60, 60]
    for i, (c, w) in enumerate(zip(cot, rong), 1):
        cell = ws.cell(row=4, column=i, value=c)
        cell.font = Font(bold=True)
        cell.fill = fill
        cell.border = bdr
        cell.alignment = Alignment(vertical="center", horizontal="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = w
    for i, r in enumerate(rows, 1):
        t = sang_gio_vn(r.thoi_gian)
        vals = [i, t.strftime("%d/%m/%Y %H:%M:%S") if t else None, _ten(r.nguoi_dung_id, ten), r.nguoi_dung_id,
                r.hanh_dong, r.bang, r.ban_ghi_id, _json_text(r.gia_tri_cu), _json_text(r.gia_tri_moi)]
        for j, v in enumerate(vals, 1):
            cell = ws.cell(row=4 + i, column=j, value=v)
            cell.border = bdr
            cell.alignment = Alignment(vertical="top", wrap_text=j >= 8)
    ws.freeze_panes = "A5"
    if rows:
        ws.auto_filter.ref = f"A4:{get_column_letter(len(cot))}{4 + len(rows)}"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------- API (chỉ CEO / ADMIN)
def _loc_tu_query(bang, hanh_dong, nguoi_dung_id, ban_ghi_id, tu, den, q) -> dict:
    return dict(bang=(bang or "").strip() or None, hanh_dong=(hanh_dong or "").strip() or None,
                nguoi_dung_id=nguoi_dung_id, ban_ghi_id=ban_ghi_id,
                tu=doc_ngay(tu, "từ"), den=doc_ngay(den, "đến"), q=(q or "").strip() or None)


@router.get("")
def xem_nhat_ky(bang: str | None = None, hanh_dong: str | None = None,
                nguoi_dung_id: int | None = Query(None, ge=0, description="0 = hệ thống (tự động)"),
                ban_ghi_id: int | None = None, tu: str | None = None, den: str | None = None,
                q: str | None = Query(None, max_length=200, description="chuỗi trong giá trị cũ / mới, vd mã đơn hàng"),
                trang: int = Query(1, ge=1), kem_bo_loc: int = Query(1, description="1 = trả kèm danh sách bảng / hành động / người"),
                db: Session = Depends(get_db), _: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """📜 Một trang nhật ký (100 dòng, mới nhất lên trên) + danh sách bảng / hành động / người để dựng ô chọn."""
    return truy_van(db, trang=trang, kem_bo_loc=bool(kem_bo_loc),
                    **_loc_tu_query(bang, hanh_dong, nguoi_dung_id, ban_ghi_id, tu, den, q))


@router.get("/xuat")
def xuat_nhat_ky(bang: str | None = None, hanh_dong: str | None = None,
                 nguoi_dung_id: int | None = Query(None, ge=0), ban_ghi_id: int | None = None,
                 tu: str | None = None, den: str | None = None, q: str | None = Query(None, max_length=200),
                 db: Session = Depends(get_db), _: NguoiDung = Depends(chi_vai_tro("CEO", "ADMIN"))):
    """📥 Excel theo cùng bộ lọc (tối đa 20.000 dòng mới nhất)."""
    data = xuat_excel(db, **_loc_tu_query(bang, hanh_dong, nguoi_dung_id, ban_ghi_id, tu, den, q))
    ten = f"Nhat-ky-he-thong-{_bay_gio_vn():%Y%m%d-%H%M}.xlsx"
    return Response(content=data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{ten}"', "Cache-Control": "no-store"})
