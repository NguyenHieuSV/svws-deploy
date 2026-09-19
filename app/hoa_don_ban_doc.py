"""Đọc FILE hóa đơn BÁN đã xuất cho khách → số · ký hiệu · ngày · người mua · tiền trước thuế / thuế / tổng,
rồi KHỚP với hóa đơn bán đang có trong hệ thống (thường đang mang số tạm = mã đơn).

- XML hóa đơn điện tử (NĐ123 / TT78): đọc THẲNG theo thẻ chuẩn (SHDon, NLap, TgTCThue…) — không cần AI, không sai số.
- PDF / ảnh: AI đọc (ai_gateway.doc_hoa_don_ban_tep)."""
import re
import unicodedata
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

GIOI_HAN = 8 * 1024 * 1024          # 8 MB / file
LECH = 1000                         # sai số làm tròn cho phép (đ)


def _so(x) -> float:
    try:
        return float(str(x if x is not None else 0).replace(",", "").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


def _ten_the(e) -> str:
    return e.tag.rsplit("}", 1)[-1] if isinstance(e.tag, str) else ""


def _con(goc, ten):
    """Phần tử ĐẦU TIÊN (duyệt sâu) mang tên thẻ `ten` — bỏ qua namespace."""
    if goc is None:
        return None
    for e in goc.iter():
        if _ten_the(e) == ten:
            return e
    return None


def _chu(goc, ten):
    e = _con(goc, ten)
    return (e.text or "").strip() if e is not None and e.text else None


def la_xml(data: bytes, content_type: str | None, filename: str | None) -> bool:
    fn, ct = (filename or "").lower(), (content_type or "").lower()
    return fn.endswith(".xml") or ct in ("application/xml", "text/xml") or data[:200].lstrip(b"\xef\xbb\xbf \r\n\t").startswith(b"<")


def doc_xml(data: bytes) -> dict | None:
    """XML hóa đơn điện tử chuẩn → dict; không phải hóa đơn chuẩn (thiếu SHDon) → None."""
    dau = data[:4000].decode("utf-8", errors="replace").upper()
    if "<!DOCTYPE" in dau or "<!ENTITY" in dau:
        raise ValueError("File XML có khai báo DTD / ENTITY — không phải hóa đơn điện tử chuẩn, không đọc")
    try:
        goc = ET.fromstring(data)
    except ET.ParseError as e:
        raise ValueError(f"File XML hỏng, không đọc được ({e})")
    so = _chu(goc, "SHDon")
    if not so:
        return None
    ngay = (_chu(goc, "NLap") or "")[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", ngay):
        ngay = None
    mua, ban, tt = _con(goc, "NMua"), _con(goc, "NBan"), _con(goc, "TToan")
    truoc, thue, tong = _so(_chu(tt, "TgTCThue")), _so(_chu(tt, "TgTThue")), _so(_chu(tt, "TgTTTBSo"))
    if not tong:
        tong = truoc + thue
    if not truoc and tong:
        truoc = tong - thue
    hang = [(_chu(h, "THHDVu") or "") for h in goc.iter() if _ten_the(h) == "HHDVu"]
    toan_van = " ".join((e.text or "").strip() for e in goc.iter() if e.text and e.text.strip())[:30000]
    return {"so_hoa_don": so.lstrip("0") or so, "ky_hieu": _chu(goc, "KHHDon"), "mau_so": _chu(goc, "KHMSHDon"),
            "ngay": ngay, "ten_nguoi_mua": _chu(mua, "Ten") or _chu(mua, "HVTNMHang"), "mst_nguoi_mua": _chu(mua, "MST"),
            "ten_nguoi_ban": _chu(ban, "Ten"), "mst_nguoi_ban": _chu(ban, "MST"),
            "tien_truoc_thue": truoc, "tien_thue": thue, "so_tien": tong,
            "thue_suat": _chu(tt, "TSuat") or _chu(goc, "TSuat"),
            "mo_ta": " · ".join([x for x in hang if x][:4])[:300] or None, "_toan_van": toan_van}


_BO_TU = re.compile(r"\b(cong ty|cty|tnhh|co phan|cp|mtv|mot thanh vien|trach nhiem huu han|llc|co|ltd|limited|company|"
                    r"jsc|corp|corporation|inc|chi nhanh|viet nam|vietnam|vn)\b")


def _khong_dau(s) -> str:
    s = unicodedata.normalize("NFD", str(s or "").lower().replace("đ", "d"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def ten_chuan(s) -> str:
    s = re.sub(r"[^a-z0-9 ]+", " ", _khong_dau(s))
    return re.sub(r"\s+", " ", _BO_TU.sub(" ", s)).strip()


def _cung_khach(tt: dict, hd: dict) -> float:
    mst_f, mst_h = re.sub(r"\D", "", tt.get("mst_nguoi_mua") or ""), re.sub(r"\D", "", hd.get("kh_mst") or "")
    if mst_f and mst_h and mst_f[:10] == mst_h[:10]:
        return 2.0
    a, b = ten_chuan(tt.get("ten_nguoi_mua")), ten_chuan(hd.get("kh_ten"))
    if not a or not b:
        return 0.0
    if a == b or (len(a) >= 5 and a in b) or (len(b) >= 5 and b in a) or SequenceMatcher(None, a, b).ratio() >= 0.8:
        return 1.5
    return 0.0


def khop(tt: dict, hds: list[dict], so_hd_chuan) -> tuple[list[dict], int | None]:
    """Xếp hạng hóa đơn bán ứng viên cho 1 file. hds: [{id, so, ma_ban, kh_ten, kh_mst, truoc, thue, tong, cn_so_tien,
    da_hach_toan, so_tam}]. Trả (≤4 ứng viên kèm lý do, id tự chọn | None). Tự chọn khi đủ chắc: cùng số HĐ · hoặc có mã
    đơn trong file · hoặc cùng tiền + cùng khách — và bỏ xa ứng viên thứ hai."""
    van = _khong_dau((tt.get("_toan_van") or "") + " " + (tt.get("mo_ta") or ""))
    khoa = so_hd_chuan(tt.get("so_hoa_don"))
    f_truoc, f_tong = _so(tt.get("tien_truoc_thue")), _so(tt.get("so_tien"))
    uv = []
    for h in hds:
        diem, ly_do = 0.0, []
        if khoa and not h.get("so_tam") and so_hd_chuan(h.get("so")) == khoa:
            diem += 5; ly_do.append("đã mang số này")
        ma = _khong_dau(h.get("ma_ban") or "").strip()
        if len(ma) >= 6 and ma in van:
            diem += 4; ly_do.append("mã đơn có trong file")
        if f_tong and (abs(f_tong - _so(h.get("tong"))) <= LECH or abs(f_tong - _so(h.get("cn_so_tien"))) <= LECH):
            diem += 3; ly_do.append("cùng tổng tiền")
        elif f_truoc and abs(f_truoc - _so(h.get("truoc"))) <= LECH:
            diem += 2.5; ly_do.append("cùng tiền trước thuế")
        if not diem:
            continue
        k = _cung_khach(tt, h)
        if k:
            diem += k; ly_do.append("cùng MST" if k >= 2 else "cùng tên khách")
        if h.get("so_tam"):
            diem += 0.5
        uv.append({**{x: h.get(x) for x in ("id", "so", "ma_ban", "kh_ten", "truoc", "thue", "tong", "cn_so_tien",
                                            "da_hach_toan", "so_tam")}, "diem": round(diem, 1), "ly_do": ly_do})
    uv.sort(key=lambda x: (-x["diem"], -(x["id"] or 0)))
    uv = uv[:4]
    chon = None
    if uv and uv[0]["diem"] >= 4 and (len(uv) == 1 or uv[0]["diem"] - uv[1]["diem"] >= 1):
        chon = uv[0]["id"]
    return uv, chon
