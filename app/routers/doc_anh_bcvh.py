"""
Cho thuê — ĐỌC ẢNH HIỆN TRƯỜNG → BÁO CÁO VẬN HÀNH (Kỹ thuật · Hóa chất-Vật tư · Khối lượng).

NVVH chụp ảnh máy đo / đồng hồ / áp kế / HMI / sổ nhật ký / phiếu giao hóa chất trên điện thoại
(trang /chup-anh). Endpoint này CHỈ ĐỌC: AI trích số liệu, khớp tên theo danh mục chỉ tiêu của dự án
và gắn cảnh báo (lệch so với lần trước, số 0 đầu, chỉ số đồng hồ giảm, phiếu nhập đã ghi…).
Người dùng sửa / xác nhận trên trang rồi LƯU qua các endpoint sẵn có:
  POST /cho-thue/tai-san/{id}/bao-cao-kt · /bao-cao-hc · /bao-cao-kl
và ảnh gốc lưu vào Tài liệu dự án qua POST /cho-thue/du-an/{id}/tai-lieu.
Module RBAC 'cho_thue' (THAO_TAC).
"""
import json
import re
import unicodedata
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from .. import ai_gateway
from ..database import get_db
from ..models import CtBaoCaoVh, CtBcvhChiTieu, KhachHang, TaiSanChoThue
from ..rbac import yeu_cau

router = APIRouter(prefix="/cho-thue", tags=["cho_thue_doc_anh"])
MODULE = "cho_thue"
TOI_DA_ANH = 10
LECH_CANH_BAO = 0.5          # lệch > 50% so với lần đo trước → cảnh báo


def _chuan(s) -> str:
    """So khớp tên không phân biệt hoa thường / dấu / khoảng trắng."""
    s = unicodedata.normalize("NFD", str(s or "").lower().replace("đ", "d"))
    return re.sub(r"\s+", " ", "".join(c for c in s if unicodedata.category(c) != "Mn")).strip()


def _so(v):
    """Rút số từ chuỗi kết quả ('7.2', '45 ppm', 'pH 6,8'); None nếu không có."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(v))
    return float(m.group(0).replace(",", ".")) if m else None


def _ngay(v, mac_dinh: str) -> str:
    v = str(v or "")[:10]
    return v if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) else mac_dinh


def _tin_cay(v) -> str:
    return v if v in ("cao", "tb", "thap") else "tb"


def _khop(ten: str, ds: list[str]) -> str | None:
    k = _chuan(ten)
    for x in ds:
        if _chuan(x) == k:
            return x
    return None


def _cb(muc: str, noi_dung: str) -> dict:
    return {"muc": muc, "noi_dung": noi_dung}


def _cb_tin_cay(r: dict, out: list):
    if r["tin_cay"] == "thap":
        out.append(_cb("bad", "AI không chắc" + (f": {r['ly_do']}" if r.get("ly_do") else ".")))
    elif r["tin_cay"] == "tb":
        out.append(_cb("warn", "Nên xem lại" + (f": {r['ly_do']}" if r.get("ly_do") else ".")))


def _mau_du_an(db: Session, ts: TaiSanChoThue) -> dict:
    ct = (db.query(CtBcvhChiTieu).filter_by(tai_san_id=ts.id)
          .order_by(CtBcvhChiTieu.thu_tu, CtBcvhChiTieu.id).all())
    kh = db.get(KhachHang, ts.khach_hang_id) if ts.khach_hang_id else None
    return {
        "ten_du_an": ts.ten_du_an or ts.ma, "khach_hang": kh.ten if kh else None,
        "ky_thuat": [{"vi_tri": c.vi_tri, "chi_tieu": c.chi_tieu, "don_vi": c.don_vi}
                     for c in ct if (c.loai or "KY_THUAT") == "KY_THUAT"],
        "hoa_chat": [{"ten": c.chi_tieu, "don_vi": c.don_vi} for c in ct if c.loai == "HOA_CHAT_VT"],
        "khoi_luong": [{"he_thong": c.chi_tieu, "don_vi": c.don_vi} for c in ct if c.loai == "KHOI_LUONG"],
    }


@router.get("/tai-san/{ts_id}/mau-bcvh")
def mau_bcvh(ts_id: int, db: Session = Depends(get_db), _=Depends(yeu_cau(MODULE, "XEM"))):
    """Danh mục vị trí / chỉ tiêu / hóa chất / hệ thống của dự án (cho trang chụp ảnh gợi ý)."""
    ts = db.get(TaiSanChoThue, ts_id)
    if ts is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án cho thuê")
    return _mau_du_an(db, ts)


@router.post("/tai-san/{ts_id}/doc-anh")
async def doc_anh(ts_id: int,
                  files: list[UploadFile] = File(...),
                  ngay: str | None = Form(None),
                  goi_y: str = Form("[]"),
                  ngay_chup: str = Form("[]"),
                  db: Session = Depends(get_db),
                  _=Depends(yeu_cau(MODULE, "THAO_TAC"))):
    """AI đọc 1–10 ảnh hiện trường → đề xuất dòng cho 3 bảng BCVH (CHƯA lưu)."""
    ts = db.get(TaiSanChoThue, ts_id)
    if ts is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dự án cho thuê")
    if not files:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chưa có ảnh nào")
    if len(files) > TOI_DA_ANH:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Tối đa {TOI_DA_ANH} ảnh mỗi lần đọc")
    ngay_bc = _ngay(ngay, date.today().isoformat())
    try:
        ds_goi_y = [str(x or "") for x in json.loads(goi_y or "[]")][:TOI_DA_ANH]
    except Exception:
        ds_goi_y = []
    try:   # ngày giờ chụp từng ảnh (trang đọc EXIF trước khi thu nhỏ) — "YYYY-MM-DD HH:MM" hoặc ""
        ds_ngay_chup = [(str(x or "") if re.fullmatch(r"\d{4}-\d{2}-\d{2}( \d{2}:\d{2})?", str(x or "")) else "")
                        for x in json.loads(ngay_chup or "[]")][:TOI_DA_ANH]
    except Exception:
        ds_ngay_chup = []
    anh = [(await f.read(), f.content_type or "", f.filename or f"anh{i + 1}.jpg")
           for i, f in enumerate(files)]
    mau = _mau_du_an(db, ts)
    try:
        kq = await run_in_threadpool(ai_gateway.doc_anh_bcvh, anh, mau, ngay_bc, ds_goi_y, ds_ngay_chup)
    except ValueError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))
    return hau_xu_ly(db, ts_id, mau, kq, ngay_bc, len(anh), ds_ngay_chup)


def hau_xu_ly(db: Session, ts_id: int, mau: dict, kq: dict, ngay_bc: str, so_anh: int,
              ngay_chup: list[str] | None = None) -> dict:
    """Chuẩn hoá tên theo danh mục + gắn cảnh báo so với dữ liệu đã ghi. Tách riêng để test không cần AI."""
    ds_vt = sorted({c["vi_tri"] for c in mau["ky_thuat"] if c.get("vi_tri")})
    ds_ct = sorted({c["chi_tieu"] for c in mau["ky_thuat"]})
    dv_ct = {_chuan(c["chi_tieu"]): c.get("don_vi") for c in mau["ky_thuat"]}
    ds_hc = [c["ten"] for c in mau["hoa_chat"]]
    dv_hc = {_chuan(c["ten"]): c.get("don_vi") for c in mau["hoa_chat"]}
    ds_kl = [c["he_thong"] for c in mau["khoi_luong"]]
    dv_kl = {_chuan(c["he_thong"]): c.get("don_vi") for c in mau["khoi_luong"]}

    cu = (db.query(CtBaoCaoVh).filter(CtBaoCaoVh.tai_san_id == ts_id)
          .order_by(CtBaoCaoVh.ngay.desc(), CtBaoCaoVh.id.desc()).limit(2000).all())

    def _truoc(loai, ten, ngay, vi_tri=None, co_ton=False):
        for r in cu:
            if r.loai != loai or _chuan(r.noi_dung) != _chuan(ten):
                continue
            if vi_tri is not None and _chuan(r.vi_tri) != _chuan(vi_tri):
                continue
            if r.ngay and str(r.ngay) > ngay:
                continue
            if co_ton and r.luong_ton is None:
                continue
            return r
        return None

    def _anh_so(v):
        try:
            n = int(v)
            return n if 1 <= n <= so_anh else None
        except (TypeError, ValueError):
            return None

    ngay_chup = ngay_chup or []

    def _ngay_anh(n):
        """Ngày chụp (YYYY-MM-DD) của ảnh số n, "" nếu không rõ."""
        return (ngay_chup[n - 1][:10] if n and n <= len(ngay_chup) and ngay_chup[n - 1] else "")

    def _ngay_dong(x, n):
        # ưu tiên ngày AI đọc trong ảnh; không có thì ngày chụp của chính ảnh đó; cuối cùng ngày báo cáo
        return _ngay(x.get("ngay"), _ngay_anh(n) or ngay_bc)

    def _cb_ngay(r, cb):
        nc = _ngay_anh(r["anh"])
        if nc and r["ngay"] != nc:
            cb.append(_cb("info", f"Ngày trên ảnh ({r['ngay'][8:10]}/{r['ngay'][5:7]}) khác ngày chụp "
                                  f"({nc[8:10]}/{nc[5:7]}) — kiểm tra đồng hồ máy đo / ngày ghi sổ."))

    # ---- Kỹ thuật ----
    ky_thuat = []
    for x in kq.get("ky_thuat") or []:
        n_anh = _anh_so(x.get("anh"))
        r = {"anh": n_anh, "ngay": _ngay_dong(x, n_anh),
             "vi_tri": str(x.get("vi_tri") or "").strip(), "chi_tieu": str(x.get("chi_tieu") or "").strip(),
             "ket_qua": "" if x.get("ket_qua") is None else str(x.get("ket_qua")).strip(),
             "don_vi": str(x.get("don_vi") or "").strip(), "ghi_chu": str(x.get("ghi_chu") or "").strip(),
             "tin_cay": _tin_cay(x.get("tin_cay")), "ly_do": str(x.get("ly_do") or "").strip()}
        if not r["chi_tieu"]:
            continue
        r["vi_tri"] = _khop(r["vi_tri"], ds_vt) or r["vi_tri"]
        khop_ct = _khop(r["chi_tieu"], ds_ct)
        r["trong_mau"] = bool(khop_ct)
        if khop_ct:
            r["chi_tieu"] = khop_ct
            r["don_vi"] = r["don_vi"] or (dv_ct.get(_chuan(khop_ct)) or "")
        cb = []
        _cb_tin_cay(r, cb)
        _cb_ngay(r, cb)
        if not r["ket_qua"]:
            cb.append(_cb("warn", "Chưa có giá trị — dòng trống sẽ không được lưu."))
        if ds_vt and not r["vi_tri"]:
            cb.append(_cb("warn", "Chưa chọn vị trí."))
        if ds_ct and not khop_ct:
            cb.append(_cb("info", "Chỉ tiêu chưa có trong danh mục của dự án."))
        if re.match(r"^0\d", r["ket_qua"]):
            cb.append(_cb("warn", "Số bắt đầu bằng 0 — kiểm tra có thiếu chữ số không."))
        truoc = _truoc("KY_THUAT", r["chi_tieu"], r["ngay"], r["vi_tri"])
        r["lan_truoc"] = {"ngay": str(truoc.ngay), "ket_qua": truoc.thong_so} if truoc else None
        v, vt = _so(r["ket_qua"]), _so(truoc.thong_so) if truoc else None
        if v is not None and vt:
            lech = (v - vt) / abs(vt)
            if abs(lech) > LECH_CANH_BAO:
                cb.append(_cb("warn", f"Lệch {lech:+.0%} so với lần trước ({truoc.thong_so} ngày {truoc.ngay:%d/%m/%Y})."))
        r["canh_bao"] = cb
        ky_thuat.append(r)

    # ---- Hóa chất - vật tư ----
    hoa_chat = []
    for x in kq.get("hoa_chat") or []:
        n_anh = _anh_so(x.get("anh"))
        r = {"anh": n_anh, "ngay": _ngay_dong(x, n_anh),
             "ten": str(x.get("ten") or "").strip(), "luong_nhap": _so(x.get("luong_nhap")),
             "luong_ton": _so(x.get("luong_ton")), "don_vi": str(x.get("don_vi") or "").strip(),
             "ghi_chu": str(x.get("ghi_chu") or "").strip(),
             "tin_cay": _tin_cay(x.get("tin_cay")), "ly_do": str(x.get("ly_do") or "").strip()}
        if not r["ten"]:
            continue
        khop = _khop(r["ten"], ds_hc)
        r["trong_mau"] = bool(khop)
        if khop:
            r["ten"] = khop
            r["don_vi"] = r["don_vi"] or (dv_hc.get(_chuan(khop)) or "")
        cb = []
        _cb_tin_cay(r, cb)
        truoc = _truoc("HOA_CHAT_VT", r["ten"], r["ngay"], co_ton=True)
        r["ton_truoc"] = ({"ngay": str(truoc.ngay), "luong_ton": float(truoc.luong_ton)} if truoc else None)
        if r["luong_ton"] is None:
            cb.append(_cb("warn", "Nhập TỒN CUỐI NGÀY (đã gồm hàng vừa nhập) — bảng hóa chất cần tồn để tính SL dùng."))
        if ds_hc and not khop:
            cb.append(_cb("info", "Hóa chất chưa có trong danh mục của dự án."))
        if r["luong_nhap"] is not None:
            for c in cu:
                if (c.loai == "HOA_CHAT_VT" and str(c.ngay) == r["ngay"] and _chuan(c.noi_dung) == _chuan(r["ten"])
                        and c.luong_nhap is not None and abs(float(c.luong_nhap) - r["luong_nhap"]) < 1e-6):
                    cb.append(_cb("bad", f"Ngày {c.ngay:%d/%m/%Y} đã ghi nhập {float(c.luong_nhap):,.0f} {c.don_vi or ''} "
                                         f"cho {c.noi_dung} — có thể trùng phiếu.".replace(",", ".")))
                    break
        r["canh_bao"] = cb
        hoa_chat.append(r)

    # ---- Khối lượng ----
    khoi_luong = []
    for x in kq.get("khoi_luong") or []:
        n_anh = _anh_so(x.get("anh"))
        r = {"anh": n_anh, "ngay": _ngay_dong(x, n_anh),
             "he_thong": str(x.get("he_thong") or "").strip(), "chi_so": _so(x.get("chi_so")),
             "don_vi": str(x.get("don_vi") or "").strip() or "m3", "ghi_chu": str(x.get("ghi_chu") or "").strip(),
             "tin_cay": _tin_cay(x.get("tin_cay")), "ly_do": str(x.get("ly_do") or "").strip()}
        khop = _khop(r["he_thong"], ds_kl)
        r["trong_mau"] = bool(khop)
        if khop:
            r["he_thong"] = khop
            r["don_vi"] = dv_kl.get(_chuan(khop)) or r["don_vi"]
        cb = []
        _cb_tin_cay(r, cb)
        _cb_ngay(r, cb)
        if not r["he_thong"]:
            cb.append(_cb("warn", "Chọn hệ thống (đồng hồ) cho chỉ số này."))
        elif ds_kl and not khop:
            cb.append(_cb("info", "Hệ thống chưa có trong danh mục của dự án."))
        truoc = _truoc("KHOI_LUONG", r["he_thong"], r["ngay"], co_ton=True) if r["he_thong"] else None
        r["lan_truoc"] = {"ngay": str(truoc.ngay), "chi_so": float(truoc.luong_ton)} if truoc else None
        if truoc and r["chi_so"] is not None and r["chi_so"] < float(truoc.luong_ton):
            cb.append(_cb("bad", f"Chỉ số NHỎ HƠN lần ghi trước ({float(truoc.luong_ton):g} ngày {truoc.ngay:%d/%m/%Y}) "
                                 "— khối lượng sẽ âm. Kiểm tra lại số."))
        r["canh_bao"] = cb
        khoi_luong.append(r)

    anh = []
    for a in kq.get("anh") or []:
        n = _anh_so(a.get("so"))
        if n:
            loai = a.get("loai") if a.get("loai") in ai_gateway.LOAI_ANH_BCVH else "khac"
            anh.append({"so": n, "loai": loai, "mo_ta": str(a.get("mo_ta") or "")[:200],
                        "ngay_chup": ngay_chup[n - 1] if n <= len(ngay_chup) else ""})
    return {"ngay": ngay_bc, "anh": anh, "ky_thuat": ky_thuat, "hoa_chat": hoa_chat,
            "khoi_luong": khoi_luong, "mau": mau}
