"""Đọc file SAO KÊ ngân hàng dạng bảng (Excel .xlsx / CSV / TXT) THẲNG bằng máy — không qua AI:
đủ mọi dòng, đúng từng đồng, không giới hạn 300 dòng, không tốn phí. Tự tìm dòng tiêu đề (cột Ngày · Diễn giải ·
Ghi nợ / Tiền ra · Ghi có / Tiền vào · Số dư, hoặc một cột Số tiền + cột Loại / dấu). Không nhận diện được thì trả None
để nơi gọi nhờ AI đọc như cũ (PDF / ảnh luôn đi qua AI)."""
import csv
import io
import re
import unicodedata
from datetime import date, datetime

TU_KHOA = {
    "dien_giai": ("dien giai", "noi dung giao dich", "noi dung", "mo ta", "description", "narrative", "remark", "chi tiet giao dich", "content"),
    "so_du": ("so du cuoi", "so du sau gd", "so du", "balance", "running balance"),
    "tien_ra": ("ghi no", "phat sinh no", "tien ra", "so tien ghi no", "debit", "withdrawal", "rut tien", "chi"),
    "tien_vao": ("ghi co", "phat sinh co", "tien vao", "so tien ghi co", "credit", "deposit", "nop tien", "thu"),
    "so_tien": ("so tien giao dich", "so tien", "amount", "gia tri"),
    "loai": ("loai giao dich", "loai gd", "dr/cr", "no/co", "loai", "type"),
    "ngay": ("ngay giao dich", "ngay hieu luc", "ngay hach toan", "ngay gd", "transaction date", "value date", "txn date", "ngay", "date"),
}
_THU_TU = ("dien_giai", "so_du", "tien_ra", "tien_vao", "so_tien", "loai", "ngay")


def _kd(s) -> str:
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.replace("đ", "d").replace("Đ", "D").lower()).strip()


def _tim_tieu_de(o: list) -> dict | None:
    """Ô của một dòng → {field: chỉ số cột} nếu dòng này là tiêu đề bảng giao dịch."""
    map_ = {}
    for idx, cell in enumerate(o):
        t = _kd(cell)
        if not t or len(t) > 40:
            continue
        for f in _THU_TU:
            if f in map_:
                continue
            if any(t == k or t.startswith(k + " ") or t.startswith(k + "(") or (len(k) >= 6 and k in t) for k in TU_KHOA[f]):
                map_[f] = idx
                break
    if "ngay" not in map_:
        return None
    if not (("tien_ra" in map_ or "tien_vao" in map_) or "so_tien" in map_):
        return None
    return map_


def _ngay(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v or "").strip()
    if not s:
        return None
    m = re.search(r"(?<!\d)(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})(?!\d)", s)       # 2026-08-01 (xét trước, kẻo 26-08-01 bị hiểu nhầm)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = re.search(r"(?<!\d)(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4}|\d{2})(?!\d)", s)  # 01/08/2026 · 01-08-26
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        try:
            return date(y, mo, d)
        except ValueError:
            return None
    return None


def _so(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s:
        return 0.0
    am = s.startswith("(") and s.endswith(")") or s.startswith("-")
    s = re.sub(r"[^\d,.\-]", "", s)
    if not s:
        return 0.0
    # 1.234.567 / 1,234,567 / 1.234.567,00 / 1,234,567.00 / 1234567.5
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):          # 1.234.567,00 → phần thập phân sau dấu phẩy
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        phan = s.split(",")
        s = s.replace(",", "") if (len(phan) > 2 or len(phan[-1]) == 3) else s.replace(",", ".")
    elif s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[-1]) == 3):
        s = s.replace(".", "")
    try:
        x = float(s)
    except ValueError:
        return 0.0
    return -abs(x) if am else x


def _bang_tu_o(cac_dong: list[list]) -> tuple[list[dict], dict] | None:
    """Danh sách dòng (mỗi dòng là list ô) → (giao dịch, meta) hoặc None khi không thấy tiêu đề."""
    tieu_de, i_td = None, -1
    for i, o in enumerate(cac_dong[:60]):
        m = _tim_tieu_de(o)
        if m:
            tieu_de, i_td = m, i
            break
    if tieu_de is None:
        return None
    ra = []
    dau = tieu_de.get("loai")
    for o in cac_dong[i_td + 1:]:
        def lay(f):
            i2 = tieu_de.get(f)
            return o[i2] if (i2 is not None and i2 < len(o)) else None
        ng = _ngay(lay("ngay"))
        dg = str(lay("dien_giai") or "").strip()
        vao = _so(lay("tien_vao")) if "tien_vao" in tieu_de else 0.0
        ra_ = _so(lay("tien_ra")) if "tien_ra" in tieu_de else 0.0
        if "so_tien" in tieu_de and not vao and not ra_:
            st = _so(lay("so_tien"))
            lo = _kd(lay("loai")) if dau is not None else ""
            if st < 0 or lo.startswith(("no", "d", "-", "debit", "ra", "chi", "withdraw")):
                ra_ = abs(st)
            elif st > 0:
                vao = st
        vao, ra_ = abs(vao), abs(ra_)
        if ng is None:
            # dòng nối tiếp diễn giải (ngân hàng xuống dòng nội dung) → ghép vào dòng trước
            if ra and dg and not vao and not ra_:
                ra[-1]["dien_giai"] = (ra[-1]["dien_giai"] + " " + dg).strip()[:400]
            continue
        if not vao and not ra_:
            continue                       # số dư đầu kỳ / dòng tổng
        sd = lay("so_du")
        ra.append({"ngay": ng, "dien_giai": dg[:400], "tien_vao": vao, "tien_ra": ra_,
                   "so_du": _so(sd) if (sd not in (None, "")) else None})
    meta = {"cach": "MAY", "dong_tieu_de": i_td + 1, "cot": tieu_de}
    return ra, meta


def doc_xlsx(data: bytes):
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    try:
        tot = None
        for ws in wb.worksheets:
            cac = []
            for row in ws.iter_rows(values_only=True):
                cac.append(list(row))
                if len(cac) >= 20000:
                    break
            kq = _bang_tu_o(cac)
            if kq and (tot is None or len(kq[0]) > len(tot[0])):
                kq[1]["sheet"] = ws.title
                tot = kq
        return tot
    finally:
        wb.close()


def doc_csv(data: bytes):
    txt = None
    for enc in ("utf-8-sig", "utf-16", "cp1258", "cp1252"):
        try:
            txt = data.decode(enc)
            break
        except Exception:
            continue
    if txt is None:
        return None
    mau = txt[:5000]
    try:
        dialect = csv.Sniffer().sniff(mau, delimiters=",;\t|")
    except Exception:
        dialect = csv.excel
    cac = [list(r) for r in csv.reader(io.StringIO(txt), dialect)]
    return _bang_tu_o(cac)


def doc_bang(data: bytes, content_type: str, filename: str):
    """Excel / CSV / TXT → (giao dịch, meta) hoặc None (không phải bảng, hoặc không nhận diện được cột)."""
    fn = (filename or "").lower()
    ct = (content_type or "").lower()
    try:
        if fn.endswith((".xlsx", ".xlsm")) or ct == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            return doc_xlsx(data)
        if fn.endswith((".csv", ".txt")) or ct in ("text/csv", "text/plain"):
            return doc_csv(data)
    except Exception:
        return None
    return None
