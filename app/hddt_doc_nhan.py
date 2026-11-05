"""📧 ĐỌC THƯ CỔNG HÓA ĐƠN ĐIỆN TỬ THEO NHÃN — bộ đọc xác định, chạy TRƯỚC AI (anh Hiếu 05/11/2026).

Thư EasyInvoice / Softdreams (hoadon-noreply@easyinvoice.vn, @softdreams.vn), MISA meInvoice, VNPT, Viettel… báo một hóa đơn
đã phát hành luôn có các nhãn cố định: «Ký hiệu mẫu số hóa đơn», «Số hóa đơn», «Ngày hóa đơn», «Tiền thuế», «Tổng tiền thanh
toán», «Mã của cơ quan thuế», «Mã tra cứu», «Mã số thuế» bên bán / bên mua. Đọc thẳng theo nhãn thì không còn:
  • đọc nhầm mã số thuế 10 số thành số tiền (bản thật 05/11: 13/27 dòng EasyInvoice ghi tiền 3,7 tỷ = MST 3701728378);
  • bỏ trống tiền / ngày (6/27 dòng, kể cả hóa đơn 226, 227 của Cơ khí Tuấn Tài);
  • bắt nhầm link quảng cáo EasyPIT ở cuối thư làm link tra cứu.
Có số hóa đơn + tổng tiền (hoặc tiền thuế) → `du=True`: nơi gọi dùng số liệu nhãn, chỉ nhờ AI khi thiếu.
"""
import re
import unicodedata
from datetime import date

_MST = r"\d{10}(?:-\d{3})?|\d{13}"
_LINK_BO = ("easy-pit", "softdreams.vn", "facebook.", "zalo.", "youtube.", "google.", "play.google", "apps.apple")
_LINK_UU_TIEN = re.compile(r"tra-?cuu|tracuu|invoice|hoa-?don|hddt|/hd\b|\bhd\.", re.I)


def kd(s) -> str:
    """Bỏ dấu + chữ thường để so nhãn (không dùng cho giá trị cần giữ nguyên chữ)."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


def so_tien(s) -> int | None:
    """'10,476,000 VND' · '10.476.000' · '10 476 000,00 đ' · '9.700.000,5' → 10476000 / 9700000. Không có chữ số → None."""
    t = re.sub(r"[^\d.,]", "", str(s or "")).strip(".,")
    if not t or not re.search(r"\d", t):
        return None
    t = re.sub(r"[.,](\d{1,2})$", "", t)            # phần lẻ 1–2 số sau dấu → bỏ (tiền VND)
    t = re.sub(r"[.,]", "", t)
    try:
        return int(t)
    except ValueError:
        return None


def _bat(t: str, mau: str, nhom: int = 1):
    m = re.search(mau, t, re.I)
    return m.group(nhom).strip() if m else None


_NHAN_MST = r"(?:M[ÃãAa]\s*S[ỐốOo]\s*THU[ẾếEe]|MST)"          # «Mã số thuế» / «MST»


def cac_mst(t: str) -> list[str]:
    return [m.group(1) for m in re.finditer(rf"(?i){_NHAN_MST}\s*[:：]?\s*({_MST})", t or "")]


def _ten_mst(t: str) -> list[tuple[str, str, bool]]:
    """Các cặp (tên đơn vị, MST, là_bên_mua) theo thứ tự xuất hiện — tên giữ nguyên dấu."""
    out = []
    dau = r"(?:C[ÔO]NG TY|CTY|DOANH NGHI[ỆE]P|H[ỘO] KINH DOANH|H[ỢO]P T[ÁA]C X[ÃA]|HTX|CHI NH[ÁA]NH)"
    # tên không được "nuốt" một «CÔNG TY…» khác đứng sau (câu «CÔNG TY A vừa phát hành … đến Quý khách CÔNG TY B, Mã số thuế …»)
    mau = (rf"({dau}(?:(?!{dau})[^\n,;]){{3,150}}?)"
           rf"\s*,?\s*[\(\-–]?\s*{_NHAN_MST}\s*[:：]?\s*({_MST})")
    for m in re.finditer(mau, t or "", re.I):
        truoc = kd(t[max(0, m.start() - 40):m.start()]).replace("\n", " ")
        mua = bool(re.search(r"(?:den|toi|cho|gui)\s+quy\s+khach(?:\s+hang)?\s*[:：]?\s*$"
                             r"|(?:nguoi|ben|don vi)\s+mua\s*[:：]?\s*$|khach hang\s*[:：]\s*$", truoc))
        out.append((" ".join(m.group(1).split()), m.group(2), mua))
    return out


def link_tra_cuu(noi_dung: str) -> str | None:
    """Link tra cứu / tải PDF: ưu tiên URL có chữ tra cứu / hóa đơn / invoice, bỏ link quảng cáo và link chỉ là trang chủ."""
    urls = re.findall(r"https?://[^\s<>\"')\]]+", noi_dung or "")
    uu, con = [], []
    for u in urls:
        u = u.rstrip(".,;")
        low = u.lower()
        if any(b in low for b in _LINK_BO):
            continue
        duoi = re.sub(r"^https?://[^/]+", "", u)
        if duoi.strip("/") == "":                      # chỉ trang chủ (https://easyinvoice.vn/) → không phải link tra cứu
            continue
        (uu if _LINK_UU_TIEN.search(u) else con).append(u)
    for u in uu + con:
        return u[:300]
    return None


def doc_nhan(tieu_de: str, noi_dung: str) -> dict | None:
    """→ {ncc_ten, ncc_mst, nguoi_mua, nguoi_mua_mst, ky_hieu, so_hoa_don, ngay, so_tien, tien_thue, tien_truoc_thue,
    thue_suat, ma_cqt, ma_tra_cuu, link_tra_cuu, mo_ta, du}. None khi thư không có nhãn nào quen (không phải thư cổng HĐĐT)."""
    goc = f"{tieu_de or ''}\n{noi_dung or ''}"
    t = kd(goc)
    ky_hieu = _bat(t, r"ky hieu(?:\s*mau so)?(?:\s*hoa don)?\s*[:：]\s*([a-z0-9]{5,12})\b")
    so_hd = (_bat(t, r"(?<!mau )so hoa don\s*[:：]?\s*0*(\d{1,8})\b")
             or _bat(t, r"hoa don(?: dien tu| gtgt| gia tri gia tang)?\s*so\s*[:：]?\s*0*(\d{1,8})\b"))
    m_ng = re.search(r"ngay(?:\s*hoa don|\s*lap|\s*phat hanh)?\s*[:：]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})", t)
    ngay = None
    if m_ng:
        try:
            ngay = date(int(m_ng.group(3)), int(m_ng.group(2)), int(m_ng.group(1))).isoformat()
        except ValueError:
            ngay = None
    thue = so_tien(_bat(t, r"tien thue(?:\s*gtgt)?\s*[:：]?\s*([\d.,\s]{3,}?)(?:\s*(?:vnd|d\b|dong)|\n)"))
    tong = so_tien(_bat(t, r"tong(?:\s*cong)?\s*tien(?:\s*thanh toan)?\s*[:：]?\s*([\d.,\s]{3,}?)(?:\s*(?:vnd|d\b|dong)|\n)")
                   or _bat(t, r"tong thanh toan\s*[:：]?\s*([\d.,\s]{3,}?)(?:\s*(?:vnd|d\b|dong)|\n)"))
    truoc = so_tien(_bat(t, r"(?:cong tien hang|tien hang|tien truoc thue|tong tien chua thue|thanh tien)\s*[:：]?\s*"
                            r"([\d.,\s]{3,}?)(?:\s*(?:vnd|d\b|dong)|\n)"))
    ma_cqt = _bat(t, r"ma (?:cua )?co quan thue\s*[:：]?\s*([a-z0-9]{16,40})\b")
    ma_tc = _bat(t, r"ma tra cuu\s*[:：]?\s*([a-z0-9_\-]{6,30})\b")
    cap = _ten_mst(goc)
    ban = next(((ten, mst) for ten, mst, mua in cap if not mua), None)
    mua = next(((ten, mst) for ten, mst, mua in cap if mua), None)
    if ban is None and mua is None and not ky_hieu and not ma_tc and not ma_cqt:
        return None                                            # không có dấu hiệu thư cổng HĐĐT
    if tong is None and truoc is not None and thue is not None:
        tong = truoc + thue
    if truoc is None and tong is not None and thue is not None and tong >= thue:
        truoc = tong - thue
    thue_suat = round(thue / truoc * 100) if (truoc and thue is not None and truoc > 0) else None
    mo_ta = " · ".join(x for x in ((f"ký hiệu {ky_hieu.upper()}" if ky_hieu else ""),
                                   (f"mã CQT {ma_cqt.upper()}" if ma_cqt else "")) if x) or None
    return {"ncc_ten": ban[0] if ban else None, "ncc_mst": ban[1] if ban else None,
            "nguoi_mua": mua[0] if mua else None, "nguoi_mua_mst": mua[1] if mua else None,
            "ky_hieu": ky_hieu.upper() if ky_hieu else None, "so_hoa_don": so_hd, "ngay": ngay,
            "so_tien": tong, "tien_thue": thue, "tien_truoc_thue": truoc, "thue_suat": thue_suat,
            "ma_cqt": ma_cqt.upper() if ma_cqt else None, "ma_tra_cuu": ma_tc.upper() if ma_tc else None,
            "link_tra_cuu": link_tra_cuu(noi_dung), "mo_ta": mo_ta,
            "du": bool(so_hd and tong)}


def bo_mst_lam_tien(info: dict, noi_dung: str) -> dict:
    """AI / regex đọc nhầm MÃ SỐ THUẾ (10 hoặc 13 số) hay mã cơ quan thuế thành số tiền → xóa số tiền đó."""
    if not info:
        return info
    goc = noi_dung or ""
    mst = {m.replace("-", "") for m in cac_mst(goc)} | set(re.findall(r"\b\d{10}\b|\b\d{13}\b", goc))
    for k in ("so_tien", "tien_truoc_thue", "tien_thue"):
        v = info.get(k)
        try:
            n = int(float(v)) if v not in (None, "") else None
        except (TypeError, ValueError):
            n = None
        if n is not None and (str(n) in mst or n >= 10 ** 12):
            info[k] = None
    return info
