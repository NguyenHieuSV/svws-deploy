"""
BẢNG GIÁ ĐẦU VÀO tự học từ mua thật — dùng chung cho Kho · Dự toán hàng bán · BOQ dự án.

Nguồn (theo thứ tự tin cậy):
  • dòng PO ĐÃ DUYỆT (bỏ chờ duyệt / từ chối) — giá mua gần nhất, bình quân 3 lần gần nhất
  • báo giá NCC còn hiệu lực — ưu tiên khi MỚI HƠN lần mua gần nhất
  • giá vốn đã học (hang_hoa.gia_von — ghi khi nhận hàng PO)
Hóa đơn / thanh toán chỉ có tổng tiền, không có đơn giá theo mặt hàng nên KHÔNG dùng làm nguồn.
"""
from datetime import date
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .models import HangHoa, DonMua, DonMuaCt, NhaCungCap, BaoGiaNcc, DonHang


def _f(v) -> float:
    return float(v or 0)


def bang_gia(db: Session, hang_hoa_ids=None) -> dict:
    """{hang_hoa_id: {ten, don_vi, gia_gan_nhat, ngay_gan_nhat, ncc_gan_nhat, so_po_gan_nhat,
    gia_tb_3, so_lan_mua, bao_gia{...}|None, gia_von, gia_de_xuat, nguon, lich_su[≤5]}}"""
    ids = list(hang_hoa_ids) if hang_hoa_ids else None
    ncc_ten = {i: t for (i, t) in db.query(NhaCungCap.id, NhaCungCap.ten).all()}
    q = (db.query(DonMuaCt, DonMua).join(DonMua, DonMuaCt.don_mua_id == DonMua.id)
         .filter(DonMua.trang_thai == "DA_DUYET", DonMuaCt.don_gia > 0)
         .order_by(DonMua.ngay.desc(), DonMua.id.desc()))
    if ids:
        q = q.filter(DonMuaCt.hang_hoa_id.in_(ids))
    out, dem = {}, {}
    for ct, dm in q.all():
        o = out.setdefault(ct.hang_hoa_id, {"lich_su": []})
        dem[ct.hang_hoa_id] = dem.get(ct.hang_hoa_id, 0) + 1
        if len(o["lich_su"]) >= 5:
            continue
        o["lich_su"].append({"don_gia": _f(ct.don_gia), "so_luong": _f(ct.so_luong),
                             "ngay": str(dm.ngay or "")[:10], "so_po": dm.so, "don_mua_id": dm.id,
                             "ncc": ncc_ten.get(dm.nha_cung_cap_id),
                             "da_nhan": _f(ct.so_luong_nhan) > 0})
    hom_nay = date.today()
    qb = db.query(BaoGiaNcc).order_by(BaoGiaNcc.id.desc())
    if ids:
        qb = qb.filter(BaoGiaNcc.hang_hoa_id.in_(ids))
    for bg in qb.all():
        if bg.hieu_luc_den is not None and bg.hieu_luc_den < hom_nay:
            continue
        if _f(bg.don_gia) <= 0:
            continue
        o = out.setdefault(bg.hang_hoa_id, {"lich_su": []})
        if o.get("bao_gia"):
            continue
        o["bao_gia"] = {"don_gia": _f(bg.don_gia), "ngay": str(bg.ngay or "")[:10],
                        "hieu_luc_den": str(bg.hieu_luc_den) if bg.hieu_luc_den else None,
                        "ncc": ncc_ten.get(bg.nha_cung_cap_id)}
    qh = db.query(HangHoa.id, HangHoa.gia_von, HangHoa.ten, HangHoa.don_vi)
    if ids:
        qh = qh.filter(HangHoa.id.in_(ids))
    for hid, gv, ten, dv in qh.all():
        o = out.get(hid)
        if o is None:
            if not gv:
                continue
            o = out.setdefault(hid, {"lich_su": []})
        o["gia_von"] = _f(gv) if gv else None
        o["ten"], o["don_vi"] = ten, dv
    for hid, o in out.items():
        ls = o["lich_su"]
        gan = ls[0] if ls else None
        o.setdefault("gia_von", None)
        o["gia_gan_nhat"] = gan["don_gia"] if gan else None
        o["ngay_gan_nhat"] = gan["ngay"] if gan else None
        o["ncc_gan_nhat"] = gan["ncc"] if gan else None
        o["so_po_gan_nhat"] = gan["so_po"] if gan else None
        ba = ls[:3]
        o["gia_tb_3"] = round(sum(x["don_gia"] for x in ba) / len(ba)) if ba else None
        o["so_lan_mua"] = dem.get(hid, 0)
        bg = o.get("bao_gia")
        if bg and (gan is None or bg["ngay"] >= gan["ngay"]):
            o["gia_de_xuat"] = bg["don_gia"]
            o["nguon"] = f"báo giá {bg['ncc'] or ''} ({bg['ngay']})".strip()
        elif gan:
            o["gia_de_xuat"] = gan["don_gia"]
            o["nguon"] = f"mua {gan['ngay']} · {gan['so_po']} · {gan['ncc'] or ''}".strip(" ·")
        elif o.get("gia_von"):
            o["gia_de_xuat"] = o["gia_von"]
            o["nguon"] = "giá vốn đã học khi nhận hàng"
        else:
            o["gia_de_xuat"], o["nguon"] = None, None
        o.setdefault("bao_gia", None)
    return out


def hang_hoa_theo_ten(db: Session, tens) -> dict:
    """{tên viết thường: hang_hoa_id} cho các tên đã có trong danh mục kho."""
    tens = {str(t or "").strip().lower() for t in tens if str(t or "").strip()}
    if not tens:
        return {}
    out = {}
    for hid, ten in db.query(HangHoa.id, HangHoa.ten).filter(
            func.lower(func.trim(HangHoa.ten)).in_(list(tens))).all():
        out.setdefault(str(ten or "").strip().lower(), hid)
    return out


def gia_thuc_theo_ma(db: Session, ma: str, hang_hoa_ids=None) -> dict:
    """Giá MUA THẬT của từng mặt hàng dưới một mã (dự toán / dự án): dòng PO (không từ chối)
    gắn đơn bán cùng số hoặc mang mã chuỗi đó — lấy PO mới nhất, kèm tổng SL đã mua."""
    ma = str(ma or "").strip().lower()
    if not ma:
        return {}
    dk = func.lower(func.trim(DonMua.ma_ban)) == ma
    dh_ids = [i for (i,) in db.query(DonHang.id).filter(func.lower(func.trim(DonHang.so)) == ma).all()]
    if dh_ids:
        dk = or_(dk, DonMua.don_hang_id.in_(dh_ids))
    q = (db.query(DonMuaCt, DonMua).join(DonMua, DonMuaCt.don_mua_id == DonMua.id)
         .filter(dk, DonMua.trang_thai != "TU_CHOI")
         .order_by(DonMua.id.desc()))
    if hang_hoa_ids:
        q = q.filter(DonMuaCt.hang_hoa_id.in_(list(hang_hoa_ids)))
    out = {}
    for ct, dm in q.all():
        o = out.get(ct.hang_hoa_id)
        if o is None:
            o = out[ct.hang_hoa_id] = {"don_gia": _f(ct.don_gia), "so_po": dm.so, "don_mua_id": dm.id,
                                       "ngay": str(dm.ngay or "")[:10], "trang_thai": dm.trang_thai,
                                       "so_luong": 0.0, "so_po_khac": 0}
        else:
            o["so_po_khac"] += 1
        o["so_luong"] += _f(ct.so_luong)
    return out


def goi_y_cap_nhat(db: Session, dong, ma_theo_doi=None):
    """dong = [(id, ten, hang_hoa_id|None, don_gia_hien_tai, khoa: bool)] → danh sách gợi ý
    {id, ten, hang_hoa_id, don_gia_cu, don_gia_moi, nguon, chenh, ty_le, khoa, co_gia}."""
    ten_map = hang_hoa_theo_ten(db, [t for (_, t, h, _, _) in dong if not h])
    ids = set()
    for (_, t, h, _, _) in dong:
        h2 = h or ten_map.get(str(t or "").strip().lower())
        if h2:
            ids.add(h2)
    bg = bang_gia(db, ids) if ids else {}
    out = []
    for (mid, ten, hid, cu, khoa) in dong:
        h2 = hid or ten_map.get(str(ten or "").strip().lower())
        g = bg.get(h2) if h2 else None
        moi = g["gia_de_xuat"] if g else None
        cu = _f(cu)
        r = {"id": mid, "ten": ten, "hang_hoa_id": h2, "don_gia_cu": cu, "don_gia_moi": moi,
             "nguon": (g or {}).get("nguon"), "khoa": bool(khoa),
             "co_gia": moi is not None,
             "chenh": (moi - cu) if moi is not None else None,
             "ty_le": (round((moi - cu) / cu * 100, 1) if (moi is not None and cu) else None)}
        out.append(r)
    return out


# ================= 🔗 KHỚP TÊN VỚI KHO — gợi ý mặt hàng gần giống =================
import re as _re
import unicodedata as _ud
from difflib import SequenceMatcher as _SM

_TU_BO = {"cai", "bo", "chiec", "m", "kg", "lit", "the", "and", "va", "of", "cho", "loai", "type"}


def _khong_dau(s: str) -> str:
    s = _ud.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if _ud.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D")


def _chuan(s: str) -> str:
    s = _khong_dau(s).lower()
    s = _re.sub(r"[^a-z0-9\.\-/ ]+", " ", s)
    return _re.sub(r"\s+", " ", s).strip()


def _tokens(s: str) -> set:
    return {t for t in _re.split(r"[\s/\-]+", _chuan(s)) if t and t not in _TU_BO}


def diem_giong(a: str, b: str) -> float:
    """0..1 — kết hợp độ giống chuỗi và độ trùng từ (không phân biệt dấu / hoa thường)."""
    ca, cb = _chuan(a), _chuan(b)
    if not ca or not cb:
        return 0.0
    if ca == cb:
        return 1.0
    r = _SM(None, ca, cb).ratio()
    ta, tb = _tokens(a), _tokens(b)
    j = (len(ta & tb) / len(ta | tb)) if (ta and tb) else 0.0
    bao = 0.85 if (ca in cb or cb in ca) else 0.0   # tên này nằm trọn trong tên kia
    return max(r, j, bao)


def ung_vien_kho(db: Session, tens, n=3, nguong=0.45):
    """{tên gốc: [{hang_hoa_id, ten, don_vi, diem, chinh_xac}]} — tối đa n ứng viên / tên."""
    kho = [(hid, ten, dv) for (hid, ten, dv) in db.query(HangHoa.id, HangHoa.ten, HangHoa.don_vi).all()
           if ten and ten.strip()]
    out = {}
    for t0 in tens:
        t = str(t0 or "").strip()
        if not t:
            out[t0] = []
            continue
        cs = []
        for hid, ten, dv in kho:
            d = diem_giong(t, ten)
            if d >= nguong:
                cs.append({"hang_hoa_id": hid, "ten": ten, "don_vi": dv, "diem": round(d, 3),
                           "chinh_xac": _chuan(t) == _chuan(ten)})
        cs.sort(key=lambda c: (-c["chinh_xac"], -c["diem"], c["ten"]))
        out[t0] = cs[:n]
    return out


def goi_y_khop_kho(db: Session, dong):
    """dong = [(id, ten, hang_hoa_id|None, don_gia, khoa)] → [{id, ten, hang_hoa_id, da_khop, khoa,
    don_gia, ung_vien:[{... + gia_de_xuat, nguon}]}] — ứng viên kèm giá đầu vào để chọn nhanh."""
    chua = [t for (_, t, h, _, _) in dong if not h]
    uv = ung_vien_kho(db, chua) if chua else {}
    ids = {c["hang_hoa_id"] for cs in uv.values() for c in cs}
    bg = bang_gia(db, ids) if ids else {}
    out = []
    for (mid, ten, hid, dg, khoa) in dong:
        cs = []
        if not hid:
            for c in uv.get(ten, []):
                gg = bg.get(c["hang_hoa_id"])
                cs.append(dict(c, gia_de_xuat=(gg["gia_de_xuat"] if gg else None),
                               nguon=(gg["nguon"] if gg else None)))
        out.append({"id": mid, "ten": ten, "hang_hoa_id": hid, "da_khop": bool(hid),
                    "khoa": bool(khoa), "don_gia": _f(dg), "ung_vien": cs})
    return out
