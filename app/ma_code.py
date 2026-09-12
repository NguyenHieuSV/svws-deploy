"""
QUY TẮC MÃ dùng chung toàn hệ thống — đơn bán · báo giá · dự toán hàng bán · dự án
· mã chuỗi trên PO / đề xuất / công nợ nhập ngoài · chi phí vận hành.

    LOẠI-KHÁCH[-ĐỊA ĐIỂM]-MMYY[-SỐ][-HẠNG MỤC]        VD: DV-COA-NT-0926-01 · TM-SIC-0726-02-LOC

  • LOẠI      TM (thương mại) · DA (dự án) · DV (dịch vụ vận hành) · OP (chi phí vận hành DN)
  • ký tự     chỉ A–Z, 0–9 và dấu gạch '-' — không dấu tiếng Việt, khoảng trắng, ngoặc, chấm
  • MMYY      tháng phát sinh: 01–12 + 2 số năm (0926 = 09/2026) — bắt buộc
  • hậu tố    tự do, nối bằng '-': -01, -02, -BT, -LOC …   · tối đa 30 ký tự
  • KHO       từ khóa riêng cho PO mua dự trữ (không phải mã bán hàng)
  Mã MẸ dự án cho thuê: LOẠI-KHÁCH[-ĐỊA]-YYYY (DV-COA-RO-2024) — mã tháng sinh ra từ nó.

MỘT bộ đọc duy nhất cho: chặn mua trùng · định mức tháng · gom nhóm gốc+tháng · gợi ý mã · đổi tháng.
"""
import re
import unicodedata
from fastapi import HTTPException, status

LOAI = ("TM", "DA", "DV", "OP")
MA_KHO = "KHO"
DAI_MAX = 30
_MMYY = re.compile(r"^(0[1-9]|1[0-2])\d{2}$")
_YYYY = re.compile(r"^20\d{2}$")
QUY_TAC = "LOẠI-KHÁCH-MMYY[-SỐ][-HẠNG MỤC], chỉ A–Z 0–9 và '-' (VD DV-COA-NT-0926-01)"


def khong_dau(s) -> str:
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D")


def chuan_hoa(ma) -> str:
    """Đề nghị mã đúng quy luật từ mã gõ tay: bỏ dấu, viết hoa, '(1)'→'-1', khoảng trắng/chấm → '-'."""
    s = khong_dau(ma).upper().strip()
    s = re.sub(r"[()\[\]{}]", "-", s)
    s = re.sub(r"[^A-Z0-9-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s


def phan_tich(ma) -> dict:
    """Đọc mã → {loai, khach, thang (MMYY), nam (YYYY mã mẹ), goc (LOẠI-KHÁCH-MMYY),
    goc_khong_thang, hau_to[], kieu: THANG | NAM | None}."""
    s = str(ma or "").strip()
    r = {"ma": s, "loai": None, "khach": None, "thang": None, "nam": None, "goc": None,
         "goc_khong_thang": None, "hau_to": [], "kieu": None}
    if not s:
        return r
    parts = [p.strip() for p in s.upper().split("-")]
    if parts and parts[0] in LOAI:
        r["loai"] = parts[0]
    for i, p in enumerate(parts):
        if i and _MMYY.match(p):
            r.update(thang=p, kieu="THANG", goc="-".join(parts[:i + 1]),
                     goc_khong_thang="-".join(parts[:i]), khach="-".join(parts[1:i]) or None,
                     hau_to=[x for x in parts[i + 1:] if x])
            return r
    for i, p in enumerate(parts):
        if i and _YYYY.match(p):
            r.update(nam=p, kieu="NAM", goc_khong_thang="-".join(parts[:i]),
                     khach="-".join(parts[1:i]) or None, hau_to=[x for x in parts[i + 1:] if x])
            return r
    return r


def kiem_tra(ma, bat_buoc_thang=True, cho_phep_nam=False):
    """→ (hợp lệ, [lỗi], mã gợi ý). KHO luôn hợp lệ (từ khóa mua dự trữ)."""
    s = str(ma or "").strip()
    if not s:
        return False, ["mã trống"], ""
    if s.upper() == MA_KHO:
        return True, [], MA_KHO
    loi = []
    if re.search(r"\s", s):
        loi.append("có khoảng trắng")
    if re.search(r"[()\[\]{}]", s):
        loi.append("có dấu ngoặc")
    if "." in s:
        loi.append("có dấu chấm")
    if khong_dau(s) != s:
        loi.append("có dấu tiếng Việt")
    if re.search(r"[^A-Z0-9\-\s().\[\]{}]", khong_dau(s).upper()):
        loi.append("có ký tự lạ")
    if s != s.upper():
        loi.append("có chữ thường")
    if len(s) > DAI_MAX:
        loi.append(f"dài quá {DAI_MAX} ký tự")
    p = phan_tich(s)
    if p["loai"] is None:
        loi.append("không bắt đầu bằng TM/DA/DV/OP")
    if p["thang"] is None:
        if cho_phep_nam and p["nam"]:
            pass
        elif bat_buoc_thang:
            loi.append("thiếu tháng MMYY (VD 0926)")
    elif not p["khach"]:
        loi.append("thiếu tên khách/dự án giữa LOẠI và tháng")
    return (not loi), loi, chuan_hoa(s)


def la_qtv(nd) -> bool:
    return getattr(getattr(nd, "vai_tro", None), "ma", None) in ("CEO", "ADMIN")


def bat_buoc(ma, nd=None, ep=False, bat_buoc_thang=True, cho_phep_nam=False, nhan="Mã"):
    """Chặn mã sai quy luật (409) — CEO/ADMIN gửi ep=True thì lưu ngoại lệ."""
    s = str(ma or "").strip()
    ok, loi, gy = kiem_tra(s, bat_buoc_thang, cho_phep_nam)
    if ok or (ep and la_qtv(nd)):
        return s
    raise HTTPException(status.HTTP_409_CONFLICT,
                        f"⛔ MÃ SAI QUY LUẬT: {nhan} '{s}' {', '.join(loi)}. "
                        f"Quy tắc: {QUY_TAC}. Gợi ý: {gy or '—'} [goi_y={gy}]")


def goc_thang(ma):
    """('DV-COA-NT', '0826') từ 'DV-COA-NT-0826-02-1' / 'DV-D12-0926-BT'; không có tháng → (None, None)."""
    p = phan_tich(ma)
    return (p["goc_khong_thang"], p["thang"]) if p["thang"] else (None, None)


def nhom(ma):
    """'DV-COA-NT-0826-02 (1)' → 'DV-COA-NT-0826' — khóa gom nhóm gốc + tháng; không có tháng → None."""
    return phan_tich(ma)["goc"]


def doi_thang(ma, ngay):
    """Đổi đuôi tháng theo ngày: DV-X-0626 + 08/2026 → DV-X-0826 (giữ nguyên hậu tố)."""
    p = phan_tich(ma)
    if not p["thang"] or not ngay:
        return ma
    parts = str(ma or "").strip().split("-")
    for i, x in enumerate(parts):
        if i and _MMYY.match(x.strip()):
            parts[i] = f"{ngay:%m%y}"
            break
    return "-".join(parts)
