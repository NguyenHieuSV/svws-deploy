"""📋 KIỂM SOÁT BÁO GIÁ ↔ DỰ TOÁN (anh Hiếu chốt 28/10/2026).

  ① Báo giá phải có DỰ TOÁN cùng mã (Dự toán hàng bán, hoặc BOQ dự án), có ≥ 1 dòng và MỌI dòng có số lượng
     đều có đơn giá → mới TRÌNH DUYỆT / DUYỆT / GỬI KHÁCH được. Thiếu → người thường bị chặn, CEO được vượt
     sau khi xác nhận (ghi audit). Nút «+ Tạo báo giá» TRỐNG chỉ CEO dùng; người khác tạo từ dự toán.
  ② Báo giá lưu liên kết dự toán gốc (noi_dung.du_toan_id / du_toan_ma). Lúc DUYỆT: so TỔNG báo giá (chưa VAT)
     với TỔNG dự toán (giá vốn, chưa VAT) → biên < ngưỡng (mặc định 15%) hoặc báo giá không có dòng giá để so
     (báo giá theo file) → cờ 📉, chỉ CEO duyệt (phải xác nhận).
  ③ Tạo báo giá từ dự toán: đơn giá bán GỢI Ý = giá dự toán × (1 + biên gợi ý, mặc định 20%), làm tròn nghìn.
"""
from sqlalchemy.orm import Session

from .config import settings


def bien_toi_thieu() -> float:
    try:
        return float(settings.bg_bien_toi_thieu)
    except (TypeError, ValueError):
        return 15.0


def bien_goi_y() -> float:
    try:
        return float(settings.bg_bien_goi_y)
    except (TypeError, ValueError):
        return 20.0


def _tr(v) -> str:
    return f"{float(v or 0) / 1e6:,.1f} tr".replace(",", "X").replace(".", ",").replace("X", ".")


def _pt(b) -> str:
    return f"{float(b):.1f}".replace(".", ",")


def tim_du_toan(db: Session, bgf) -> dict | None:
    """Dự toán gốc của báo giá: liên kết đã lưu → Dự toán hàng bán cùng mã → BOQ dự án cùng mã (kể cả mã khác thứ tự).
    → {loai DTB|BOQ, id, ma, so_dong, dong_thieu_gia[], tong} hoặc None."""
    from .du_toan_ks import tim_da_theo_ma, tim_dtb_theo_ma
    from .models import DuAnDuToan, DuToanBan, DuToanBanMuc
    nd = bgf.noi_dung or {}
    ma = str(bgf.so or nd.get("so") or "").strip()
    dt = None
    if nd.get("du_toan_id"):
        try:
            dt = db.get(DuToanBan, int(nd["du_toan_id"]))
        except (TypeError, ValueError):
            dt = None
    if dt is None and ma:
        ds = tim_dtb_theo_ma(db, ma)
        dt = ds[0] if ds else None
    if dt is not None:
        rows = [(m.id, m.ten, float(m.so_luong or 0), float(m.don_gia or 0))
                for m in db.query(DuToanBanMuc).filter_by(du_toan_id=dt.id).all()]
        loai, did, dma = "DTB", dt.id, dt.ma
        gia_uoc = bool(getattr(dt, "gia_uoc", False))           # mig 162: giá vốn ƯỚC (tạo ngược) chưa rà
    else:
        das = tim_da_theo_ma(db, ma) if ma else []
        if not das:
            return None
        da = das[0]
        rows = [(x.id, x.ten, float(x.so_luong or 0), float(x.don_gia or 0))
                for x in db.query(DuAnDuToan).filter_by(du_an_id=da.id).all()]
        loai, did, dma = "BOQ", da.id, da.ma
        gia_uoc = False
    co_sl = [r for r in rows if r[2] > 0]
    # dòng báo giá đánh dấu «không chào» (khong_chao) → trừ khỏi tổng dự toán dùng để so biên
    bo = {int(it.get("dt_muc_id")) for it in (nd.get("items") or [])
          if (it.get("khong_chao") or it.get("tuy_chon")) and it.get("dt_muc_id") not in (None, "")}
    tong = sum(r[2] * r[3] for r in co_sl if r[0] not in bo)
    # dòng NGOÀI dự toán (nhân viên tự thêm) có chi phí dự kiến → cộng vào giá vốn khi so biên
    ngoai = [it for it in (nd.get("items") or []) if it.get("ngoai_du_toan") and not it.get("khong_chao")
             and not it.get("tuy_chon") and float(it.get("so_luong") or 0) > 0]
    tong += sum(float(it.get("so_luong") or 0) * float(it.get("gia_von") or 0) for it in ngoai)
    return {"loai": loai, "id": did, "ma": dma, "so_dong": len(co_sl), "gia_uoc": gia_uoc,
            "dong_thieu_gia": [r[1] for r in co_sl if r[3] <= 0 and r[0] not in bo],
            "tong": tong, "so_bo": len(bo),
            "dong": [{"id": r[0], "ten": r[1], "so_luong": r[2], "don_gia": r[3]} for r in rows],
            "ngoai_du_toan": [{"ten": it.get("ten") or "", "so_luong": float(it.get("so_luong") or 0),
                               "gia_von": float(it.get("gia_von") or 0), "don_gia": float(it.get("don_gia") or 0)}
                              for it in ngoai],
            "ngoai_chua_uoc": [it.get("ten") or "" for it in ngoai if float(it.get("gia_von") or 0) <= 0]}


def luu_phien_ban(db: Session, bgf, nd_id, gui_den: str | None) -> dict:
    """Mỗi lần ✉️ gửi khách: lưu bản chụp Rev.A / B / C… kèm tổng chính, tổng tùy chọn, giá vốn, biên."""
    from .bao_gia_pdf import tinh_bao_gia, tinh_tuy_chon
    from .models import BaoGiaPhienBan
    from .nhac_viec_service import gio_hien_tai
    so_cu = db.query(BaoGiaPhienBan).filter(BaoGiaPhienBan.bao_gia_form_id == bgf.id).count()
    rev = chr(65 + so_cu) if so_cu < 26 else f"Z{so_cu - 25}"
    nd = bgf.noi_dung or {}
    k = kiem_tra(db, bgf)
    sub, _v, tong = tinh_bao_gia(nd)
    von = float((k["du_toan"] or {}).get("tong") or 0)
    pb = BaoGiaPhienBan(bao_gia_form_id=bgf.id, rev=rev, so=bgf.so or nd.get("so"), noi_dung=nd,
                        tong_chua_vat=round(sub), tong_gom_vat=round(tong), tong_tuy_chon=round(tinh_tuy_chon(nd)),
                        gia_von=round(von), bien=k["bien"], gui_den=(gui_den or "")[:300] or None, nguoi_gui=nd_id,
                        gui_luc=gio_hien_tai())
    db.add(pb); db.flush()
    return {"rev": rev, "id": pb.id, "tong_chua_vat": float(pb.tong_chua_vat), "bien": k["bien"]}


def ds_phien_ban(db: Session, bgf_id: int) -> list:
    from .models import BaoGiaPhienBan
    out = []
    for p in db.query(BaoGiaPhienBan).filter(BaoGiaPhienBan.bao_gia_form_id == bgf_id).order_by(BaoGiaPhienBan.id).all():
        out.append({"id": p.id, "rev": p.rev, "so": p.so, "tong_chua_vat": float(p.tong_chua_vat or 0),
                    "tong_gom_vat": float(p.tong_gom_vat or 0), "tong_tuy_chon": float(p.tong_tuy_chon or 0),
                    "gia_von": float(p.gia_von or 0), "bien": float(p.bien) if p.bien is not None else None,
                    "gui_den": p.gui_den, "gui_luc": p.gui_luc.strftime("%d/%m/%Y %H:%M") if p.gui_luc else None,
                    "so_dong": len([it for it in (p.noi_dung or {}).get("items") or [] if not it.get("khong_chao")])})
    return out


def so_sanh_lan_truoc(db: Session, bgf) -> dict | None:
    """Bản hiện tại so với lần gửi khách gần nhất: chênh tổng, chênh biên, dòng thêm / bớt / đổi giá."""
    from .bao_gia_pdf import tinh_bao_gia
    ds = ds_phien_ban(db, bgf.id)
    if not ds:
        return None
    from .models import BaoGiaPhienBan
    p = db.get(BaoGiaPhienBan, ds[-1]["id"])
    cu = {str(it.get("dt_muc_id") or ("#" + str(it.get("ten") or ""))): it
          for it in (p.noi_dung or {}).get("items") or [] if not it.get("khong_chao")}
    moi = {str(it.get("dt_muc_id") or ("#" + str(it.get("ten") or ""))): it
           for it in (bgf.noi_dung or {}).get("items") or [] if not it.get("khong_chao")}
    them = [moi[k].get("ten") or "" for k in moi if k not in cu]
    bot = [cu[k].get("ten") or "" for k in cu if k not in moi]
    doi = [{"ten": moi[k].get("ten") or "", "cu": float(cu[k].get("don_gia") or 0), "moi": float(moi[k].get("don_gia") or 0)}
           for k in moi if k in cu and abs(float(cu[k].get("don_gia") or 0) - float(moi[k].get("don_gia") or 0)) > 0.5]
    k = kiem_tra(db, bgf)
    sub = float(tinh_bao_gia(bgf.noi_dung or {})[0])
    return {"rev": ds[-1]["rev"], "gui_luc": ds[-1]["gui_luc"], "tong_truoc": ds[-1]["tong_chua_vat"], "tong_nay": sub,
            "chenh_tong": sub - ds[-1]["tong_chua_vat"], "bien_truoc": ds[-1]["bien"], "bien_nay": k["bien"],
            "them": them, "bot": bot, "doi_gia": doi, "so_phien_ban": len(ds)}


def tao_du_toan_tu_bao_gia(db: Session, bgf, nd) -> dict:
    """📋 Dựng DỰ TOÁN HÀNG BÁN từ chính các dòng báo giá (dọn 47 báo giá cũ thiếu dự toán, 28/10/2026).
    Giá vốn tạm = giá bán × (1 − sàn biên nhóm) (nhân viên sửa lại sau); dòng tùy chọn / không chào bỏ qua.
    Báo giá được nối du_toan_id + dt_muc_id + gia_von để từ đây tính biên như báo giá tạo từ dự toán."""
    from datetime import date as _d
    from decimal import Decimal
    from fastapi import HTTPException, status
    from sqlalchemy import func
    from .audit import ghi_audit
    from .ma_code import bat_buoc as _bb_ma
    from .models import DuToanBan, DuToanBanMuc, HangHoa, KhachHang, NhaCungCap, SanPhamNcc
    nd_ = bgf.noi_dung or {}
    ma = str(bgf.so or nd_.get("so") or "").strip()
    if not ma:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Báo giá chưa có số — nhập số báo giá (mã) trước")
    if tim_du_toan(db, bgf) is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Mã {ma} đã có dự toán — mở báo giá để nối / cập nhật")
    its = [it for it in (nd_.get("items") or []) if str(it.get("ten") or "").strip() and not it.get("khong_chao")
           and not it.get("tuy_chon") and float(it.get("so_luong") or 0) > 0]
    if not its:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Báo giá không có dòng sản phẩm (báo giá theo file đính kèm) — lập dự toán tay ở Bán hàng → Dự toán hàng bán")
    ma = _bb_ma(ma[:30], nd, True, nhan="Mã dự toán")
    if db.query(DuToanBan).filter(func.lower(DuToanBan.ma) == ma.lower()).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Mã hàng bán '{ma}' đã có dự toán")
    kh_ten = db.query(KhachHang.ten).filter(KhachHang.id == bgf.khach_hang_id).scalar() if getattr(bgf, "khach_hang_id", None) else None
    try:
        ngay = _d.fromisoformat(str(nd_.get("ngay") or "")[:10])
    except ValueError:
        ngay = _d.today()
    d = DuToanBan(ma=ma, khach_hang=(kh_ten or nd_.get("khach_ten") or None),
                  mo_ta=(str(nd_.get("tieu_de") or "")[:300] or None) and f"Tạo ngược từ báo giá {ma} — {str(nd_.get('tieu_de') or '')[:200]}",
                  ngay=ngay, nguoi_tao="Tạo ngược từ báo giá")
    db.add(d); db.flush()
    san = san_bien()
    cpc = san["chi_phi_chung"] / 100
    so_dong, co_von, so_uoc = 0, 0, 0
    for it in its:
        ten = str(it.get("ten")).strip()[:250]
        gia_ban = float(it.get("don_gia") or 0)
        von = float(it.get("gia_von") or 0)
        uoc = von <= 0 and gia_ban > 0                        # không có giá vốn thật → ƯỚC ngược từ sàn biên
        if uoc:
            nhom = (it.get("nhom") or "VAT_TU").upper()
            von = gia_ban * (1 - san.get(nhom, san["VAT_TU"]) / 100) / (1 + cpc)   # ước ngược từ sàn biên
            von = round(von / 1000) * 1000
            so_uoc += 1
        hh_id = db.query(HangHoa.id).filter(func.lower(func.trim(HangHoa.ten)) == ten.lower()).scalar()   # chỉ lấy id (không nạp quan hệ)
        # 29/10/2026: mang theo thông tin sản phẩm của dòng báo giá (mã SP · spec · NSX · NCC · liên kết danh mục nếu còn)
        ncc_id = (int(it["nha_cung_cap_id"]) if str(it.get("nha_cung_cap_id") or "").isdigit()
                  and db.get(NhaCungCap, int(it["nha_cung_cap_id"])) is not None else None)
        sp_id = (int(it["san_pham_ncc_id"]) if str(it.get("san_pham_ncc_id") or "").isdigit()
                 and db.get(SanPhamNcc, int(it["san_pham_ncc_id"])) is not None else None)
        m = DuToanBanMuc(du_toan_id=d.id, ten=ten, quy_cach=(str(it.get("mo_ta") or "")[:2000] or None),
                         don_vi=(str(it.get("don_vi") or "")[:40] or None), so_luong=Decimal(str(it.get("so_luong") or 1)),
                         don_gia=Decimal(str(round(von))), hang_hoa_id=hh_id,
                         ma_sp=(str(it.get("ma_sp") or "").strip()[:60] or None), spec=(str(it.get("spec") or "").strip()[:2000] or None),
                         nha_san_xuat=(str(it.get("nha_san_xuat") or "").strip()[:150] or None),
                         ncc_ten=(str(it.get("ncc_ten") or "").strip()[:200] or None), nha_cung_cap_id=ncc_id, san_pham_ncc_id=sp_id,
                         ghi_chu="Giá vốn ƯỚC từ giá bán − sàn biên (tạo ngược từ báo giá) — cần rà lại" if uoc else None)
        db.add(m); db.flush()
        it["dt_muc_id"] = m.id
        if float(it.get("gia_von") or 0) <= 0:
            it["gia_von"] = round(von)
        it.pop("ngoai_du_toan", None)
        so_dong += 1
        co_von += 1 if von > 0 else 0
    d.gia_uoc = so_uoc > 0                                     # mig 162: cờ «giá vốn ước» → biên chỉ tạm, lúc duyệt chỉ CEO
    nd_["du_toan_id"], nd_["du_toan_ma"] = d.id, d.ma
    nd_.setdefault("bien_nhom", {k: san[k] for k in ("THIET_BI", "VAT_TU", "NHAN_CONG")})
    nd_.setdefault("chi_phi_chung", san["chi_phi_chung"])
    bgf.noi_dung = dict(nd_)
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(bgf, "noi_dung")                 # JSONB: báo rõ đã đổi để SQLAlchemy ghi xuống DB
    ghi_audit(db, nd.id, "TAO_TU_BAO_GIA", "du_toan_ban", d.id, moi={"bao_gia": bgf.id, "ma": ma, "so_dong": so_dong})
    db.commit()
    return {"du_toan_id": d.id, "ma": d.ma, "so_dong": so_dong, "co_von": co_von, "so_uoc": so_uoc}


# ---------------- 🧾 đơn hàng nhớ báo giá lúc chốt (28/10/2026) ----------------
TRANG_THAI_CHOT = ("DA_GUI", "DA_DUYET", "DA_XUAT")      # báo giá được nối với đơn hàng cùng mã


def so_lieu_chot(db: Session, bgf) -> dict:
    """Số liệu báo giá để ghi lên đơn hàng lúc chốt: dự toán gốc, Rev gửi khách gần nhất, tổng chưa VAT, giá vốn, biên."""
    from .bao_gia_pdf import tinh_bao_gia
    from .models import BaoGiaPhienBan
    k = kiem_tra(db, bgf)
    dt = k["du_toan"] or {}
    sub, _v, tong = tinh_bao_gia(bgf.noi_dung or {})
    pb = (db.query(BaoGiaPhienBan.rev).filter(BaoGiaPhienBan.bao_gia_form_id == bgf.id)
          .order_by(BaoGiaPhienBan.id.desc()).first())
    return {"du_toan_ma": dt.get("ma"), "rev": pb[0] if pb else None, "tong_chao": round(float(sub)),
            "tong_gom_vat": round(float(tong)), "gia_von_chao": round(float(dt.get("tong") or 0)) if dt else None,
            "bien_chao": k["bien"], "gia_von_chao_uoc": bool(k.get("gia_uoc"))}


BIEN_CHAO_TRAN = 999.0       # |biên| lớn hơn mức này (báo giá 19.000 đ so dự toán 153 tr…) = dữ liệu sai → không ghi biên


def ghi_chot_len_don(db: Session, dh, bgf, nguon: str = "TAO_DON") -> dict:
    """Ghi số liệu lúc chào lên đơn hàng (không commit). Biên vô lý (ngoài ±BIEN_CHAO_TRAN) → để trống, không so."""
    from .nhac_viec_service import gio_hien_tai
    s = so_lieu_chot(db, bgf)
    b = s["bien_chao"]
    if b is not None and abs(float(b)) > BIEN_CHAO_TRAN:
        s["bien_chao"], s["bien_bo_qua"] = None, b             # cột NUMERIC(6,2) không chứa nổi, và số cũng vô nghĩa
    dh.bao_gia_form_id = bgf.id
    dh.du_toan_ma = (str(s["du_toan_ma"])[:50] if s["du_toan_ma"] else None)
    dh.bao_gia_rev = s["rev"]
    dh.tong_chao = s["tong_chao"]
    dh.gia_von_chao = s["gia_von_chao"]
    dh.bien_chao = s["bien_chao"]
    dh.gia_von_chao_uoc = bool(s.get("gia_von_chao_uoc"))      # mig 162
    dh.chot_luc = gio_hien_tai()
    s["nguon"] = nguon
    return s


def tim_bgf_theo_ma(db: Session, ma, trang_thai=TRANG_THAI_CHOT):
    """Báo giá gửi khách (không phải hợp đồng) cùng số — ưu tiên đã gửi khách > đã duyệt > đã xuất PDF, mới nhất."""
    from sqlalchemy import func
    from .models import BaoGiaForm
    s = str(ma or "").strip()
    if not s:
        return None
    uu = {"DA_GUI": 0, "DA_DUYET": 1, "DA_XUAT": 2, "CHO_DUYET": 3, "NHAP": 4, "TU_CHOI": 5}
    ds = [b for b in db.query(BaoGiaForm).filter(func.lower(func.trim(BaoGiaForm.so)) == s.lower()).all()
          if (b.noi_dung or {}).get("loai") != "HOP_DONG" and (not trang_thai or b.trang_thai in trang_thai)]
    ds.sort(key=lambda b: (uu.get(b.trang_thai, 9), -b.id))
    return ds[0] if ds else None


def noi_bao_gia_theo_ma(db: Session, dh) -> dict | None:
    """Đơn lập tay / AI đọc PO mang mã trùng số báo giá gửi khách → nối + ghi số liệu lúc chốt. Không ném lỗi."""
    try:
        if getattr(dh, "bao_gia_form_id", None):
            return None
        bgf = tim_bgf_theo_ma(db, dh.so)
        if bgf is None:
            return None
        return ghi_chot_len_don(db, dh, bgf, "THEO_MA")
    except Exception as e:                                               # noqa: BLE001
        print(f"[BG_CHOT] đơn {getattr(dh, 'id', '?')}: {type(e).__name__}: {e}")
        return None


def tao_don_tu_bao_gia_form(db: Session, bgf, nd, ep: bool = False) -> dict:
    """🧾 «→ Tạo đơn hàng» từ BÁO GIÁ GỬI KHÁCH đã duyệt / đã gửi: đơn bán cùng mã, dòng = dòng báo giá (bỏ không chào /
    tùy chọn), hàng chưa có trong kho tự thêm (SAN_PHAM, tồn 0), VAT theo từng dòng; ghi dự toán · Rev · tổng · biên lúc chào.
    Đã có đơn cùng mã lập tay → chỉ nối báo giá vào đơn đó (không tạo trùng). CEO/ADMIN ep=True cho báo giá mới xuất PDF."""
    from datetime import date as _d
    from decimal import Decimal
    from fastapi import HTTPException, status
    from sqlalchemy import func
    from .audit import ghi_audit
    from .models import DonHang, DonHangCt, HangHoa, KhachHang, TonKho
    nd_ = bgf.noi_dung or {}
    if nd_.get("loai") == "HOP_DONG":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Đây là hợp đồng, không phải báo giá")
    tt = bgf.trang_thai
    if tt not in ("DA_DUYET", "DA_GUI") and not (ep and la_qtv(nd) and tt == "DA_XUAT"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Báo giá đang ở trạng thái {tt} — phải được DUYỆT (và gửi khách) trước khi tạo đơn hàng")
    ma = str(bgf.so or nd_.get("so") or "").strip()
    if not ma:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Báo giá chưa có số — nhập số báo giá (mã) trước")
    cu = db.query(DonHang).filter(DonHang.bao_gia_form_id == bgf.id).first()
    if cu is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Báo giá đã có đơn hàng {cu.so or ('#' + str(cu.id))}")
    trung = db.query(DonHang).filter(func.lower(func.trim(DonHang.so)) == ma.lower()).first()
    if trung is not None:                                   # đơn cùng mã lập tay trước đó → nối, không tạo trùng
        s = ghi_chot_len_don(db, trung, bgf, "NOI_DON_CO_SAN")
        ghi_audit(db, nd.id, "NOI_BAO_GIA", "don_hang", trung.id,
                  moi={"bao_gia_form": bgf.id, "rev": s["rev"], "tong_chao": s["tong_chao"], "bien_chao": s["bien_chao"],
                       "du_toan_ma": s["du_toan_ma"]})
        db.commit()
        return {"don_hang_id": trung.id, "so": trung.so, "da_co": True, "so_dong": 0, "hang_moi": [], **s}
    kh_id = getattr(bgf, "khach_hang_id", None)
    if not kh_id:
        ten_kh = str(nd_.get("khach_ten") or "").strip()
        kh = (db.query(KhachHang).filter(func.lower(func.trim(KhachHang.ten)) == ten_kh.lower()).first()
              if ten_kh else None)
        if kh is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "Báo giá chưa gắn khách hàng trong danh mục — mở báo giá chọn khách rồi tạo lại")
        kh_id = kh.id
    its = [it for it in (nd_.get("items") or []) if str(it.get("ten") or "").strip() and not it.get("khong_chao")
           and not it.get("tuy_chon") and float(it.get("so_luong") or 0) > 0]
    if not its:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Báo giá không có dòng sản phẩm (báo giá theo file đính kèm) — lập đơn hàng tay ở tab Đơn hàng")
    vat_md = nd_.get("vat_pct")
    lines, hang_moi = [], []
    th, tth = Decimal(0), Decimal(0)
    for it in its:
        ten = str(it.get("ten")).strip()[:200]
        hh = db.query(HangHoa).filter(func.lower(func.trim(HangHoa.ten)) == ten.lower()).first()
        if hh is None:
            hh = HangHoa(ten=ten, loai="SAN_PHAM", don_vi=(str(it.get("don_vi") or "")[:20] or None),
                         gia_ban=Decimal(str(it.get("don_gia") or 0)))
            db.add(hh); db.flush()
            if db.query(TonKho).filter_by(hang_hoa_id=hh.id).first() is None:
                db.add(TonKho(hang_hoa_id=hh.id, so_luong=0))
            hang_moi.append(ten)
        sl, dg = Decimal(str(it.get("so_luong") or 1)), Decimal(str(it.get("don_gia") or 0))
        p = it.get("vat_pct")
        p = vat_md if p in (None, "") else p
        ts = Decimal(str(p if p not in (None, "") else 8))
        line = (sl * dg).quantize(Decimal(1))
        th += line
        tth += (line * ts / Decimal(100)).quantize(Decimal(1))     # VAT làm tròn từng dòng (như đơn lập tay)
        lines.append((hh.id, sl, dg, ts))
    dh = DonHang(so=ma[:30], khach_hang_id=kh_id, ngay=_d.today(), tong_tien=th, tien_thue=tth, trang_thai="MOI")
    db.add(dh); db.flush()
    for hh_id, sl, dg, ts in lines:
        db.add(DonHangCt(don_hang_id=dh.id, hang_hoa_id=hh_id, so_luong=sl, don_gia=dg, thue_suat=ts))
    s = ghi_chot_len_don(db, dh, bgf, "TAO_DON")
    ghi_audit(db, nd.id, "TAO", "don_hang", dh.id,
              moi={"tu_bao_gia_form": bgf.id, "so_dong": len(lines), "tong_tien": float(th), "tien_thue": float(tth),
                   "hang_moi": hang_moi[:20], "rev": s["rev"], "bien_chao": s["bien_chao"], "du_toan_ma": s["du_toan_ma"]})
    db.commit()
    return {"don_hang_id": dh.id, "so": dh.so, "da_co": False, "so_dong": len(lines), "hang_moi": hang_moi[:10], **s}


def dt_doi_gia(du_toan: dict | None, noi_dung: dict) -> list:
    """Dòng báo giá có dt_muc_id mà giá vốn / SL lưu trong báo giá khác dự toán HIỆN TẠI → [{ten, cu, moi, sl_cu, sl_moi}]
    (dự toán đổi sau khi lập báo giá — ví dụ mua được rẻ hơn)."""
    if not du_toan:
        return []
    hien = {d["id"]: d for d in du_toan.get("dong") or []}
    out = []
    for it in noi_dung.get("items") or []:
        mid = it.get("dt_muc_id")
        if mid in (None, "") or it.get("khong_chao"):
            continue
        d = hien.get(int(mid))
        if d is None:
            out.append({"ten": it.get("ten") or "", "cu": float(it.get("gia_von") or 0), "moi": None,
                        "sl_cu": float(it.get("so_luong") or 0), "sl_moi": None})
            continue
        cu, moi = float(it.get("gia_von") or 0), d["don_gia"]
        if abs(cu - moi) > 0.5 or abs(float(it.get("so_luong") or 0) - d["so_luong"]) > 1e-6:
            out.append({"ten": it.get("ten") or "", "cu": cu, "moi": moi,
                        "sl_cu": float(it.get("so_luong") or 0), "sl_moi": d["so_luong"]})
    return out


def kiem_tra(db: Session, bgf) -> dict:
    """Kết quả kiểm soát của một báo giá (dùng cho cổng trình duyệt / duyệt / gửi và nhãn trên danh sách)."""
    from .bao_gia_pdf import tinh_bao_gia
    dt = tim_du_toan(db, bgf)
    ma = str(bgf.so or (bgf.noi_dung or {}).get("so") or "").strip()
    thieu = None
    if dt is None:
        thieu = f"Báo giá {ma or '(chưa có số)'} CHƯA CÓ DỰ TOÁN cùng mã (Dự toán hàng bán / BOQ dự án)."
    elif dt["so_dong"] == 0:
        thieu = f"Dự toán {dt['ma']} chưa có dòng sản phẩm nào."
    elif dt["dong_thieu_gia"]:
        n = len(dt["dong_thieu_gia"])
        thieu = (f"Dự toán {dt['ma']} còn {n} dòng CHƯA CÓ ĐƠN GIÁ (vd: {', '.join(dt['dong_thieu_gia'][:3])}"
                 + ("…" if n > 3 else "") + ").")
    try:
        nd_ = dict(bgf.noi_dung or {})
        nd_["items"] = [it for it in (nd_.get("items") or []) if not it.get("khong_chao")]
        tong_bg = float(tinh_bao_gia(nd_)[0])             # tinh_bao_gia đã bỏ dòng tùy chọn
    except Exception:                                                    # noqa: BLE001
        tong_bg = 0.0
    bien, ly_do_bien = None, None
    ng = bien_toi_thieu()
    if dt is not None and not thieu:
        if tong_bg <= 0:
            ly_do_bien = (f"Báo giá không có dòng giá để so với dự toán {dt['ma']} ({_tr(dt['tong'])}) — "
                          "báo giá theo file đính kèm / chưa nhập đơn giá.")
        else:
            bien = round((tong_bg - dt["tong"]) / tong_bg * 100, 1)
            if bien < ng:
                ly_do_bien = (f"Tổng báo giá {_tr(tong_bg)} (chưa VAT) so với dự toán {dt['ma']} {_tr(dt['tong'])} → "
                              + (f"LỖ {_tr(dt['tong'] - tong_bg)} (biên {_pt(bien)}%)" if bien < 0
                                 else f"biên chỉ {_pt(bien)}% < ngưỡng {ng:g}%") + ".")
    gia_uoc = bool((dt or {}).get("gia_uoc")) and not thieu
    canh_bao_uoc = ((f"Dự toán {dt['ma']} có GIÁ VỐN ƯỚC (tạo ngược từ báo giá = giá bán − sàn biên, chưa rà)"
                     + (f" — biên {_pt(bien)}% chỉ là tạm tính" if bien is not None else "") + ".") if gia_uoc else None)
    return {"du_toan": dt, "thieu_du_toan": thieu, "tong_bg": tong_bg, "bien": bien, "nguong": ng,
            "canh_bao_bien": ly_do_bien, "gia_uoc": gia_uoc, "canh_bao_uoc": canh_bao_uoc,
            "ngoai_du_toan": (dt or {}).get("ngoai_du_toan") or [], "ngoai_chua_uoc": (dt or {}).get("ngoai_chua_uoc") or [],
            "so_bo": (dt or {}).get("so_bo") or 0, "dt_doi_gia": dt_doi_gia(dt, bgf.noi_dung or {})}


MAU_DIEU_KHOAN = {
    "TM": {"ten": "Thương mại (bán thiết bị / vật tư)", "hieu_luc": "30 days from quotation date",
           "tt": "100% payment within 30 days after delivery and invoice", "giao": "2-4 weeks after order placement",
           "dia_diem": "Delivered to customer's site (DAP)", "bao_hanh": "12 months from delivery"},
    "DA": {"ten": "Dự án (thiết kế – cung cấp – lắp đặt)", "hieu_luc": "45 days from quotation date",
           "tt": "40% deposit upon order, 50% upon delivery notification, 10% after commissioning and acceptance",
           "giao": "8-10 weeks after order placement", "dia_diem": "Installed at customer's site",
           "bao_hanh": "12 months from acceptance or 18 months from delivery, whichever comes first"},
    "DV": {"ten": "Dịch vụ vận hành / bảo trì", "hieu_luc": "30 days from quotation date",
           "tt": "Monthly, within 15 days after invoice", "giao": "As per service schedule",
           "dia_diem": "Customer's site", "bao_hanh": "Service quality guaranteed as per SLA"},
}


def mau_dieu_khoan_theo_ma(ma: str) -> str:
    loai = str(ma or "").strip().upper().split("-")[0]
    return loai if loai in MAU_DIEU_KHOAN else "TM"


def la_ceo(nd) -> bool:
    return (getattr(getattr(nd, "vai_tro", None), "ma", None) or "").upper() == "CEO"


def la_qtv(nd) -> bool:
    """CEO / ADMIN — được chỉnh giá bán DƯỚI sàn biên (anh Hiếu 28/10/2026)."""
    return (getattr(getattr(nd, "vai_tro", None), "ma", None) or "").upper() in ("CEO", "ADMIN")


def san_bien() -> dict:
    """Sàn biên theo nhóm (%) + chi phí chung — nhân viên không được đặt giá bán dưới sàn."""
    def _f(v, mac):
        try:
            return float(v)
        except (TypeError, ValueError):
            return mac
    return {"THIET_BI": _f(settings.bg_bien_thiet_bi, 15.0), "VAT_TU": _f(settings.bg_bien_vat_tu, 25.0),
            "NHAN_CONG": _f(settings.bg_bien_nhan_cong, 30.0), "chi_phi_chung": _f(settings.bg_chi_phi_chung, 5.0)}


def dong_duoi_san(noi_dung: dict) -> list:
    """Các dòng có giá vốn mà biên (trên giá bán, sau chi phí chung) < sàn của nhóm → [{ten, nhom, bien, san}].
    Dòng không có giá vốn (chưa ước) không xét."""
    nd = noi_dung or {}
    san = san_bien()
    cpc = nd.get("chi_phi_chung")
    cpc = san["chi_phi_chung"] if cpc in (None, "") else float(cpc)
    out = []
    for it in nd.get("items") or []:
        von = float(it.get("gia_von") or 0)
        gia = float(it.get("don_gia") or 0)
        if von <= 0 or float(it.get("so_luong") or 0) <= 0:
            continue
        nhom = (it.get("nhom") or "VAT_TU").upper()
        s = san.get(nhom, san["VAT_TU"])
        v = von * (1 + cpc / 100)
        bien = (gia - v) / gia * 100 if gia > 0 else -100.0
        if bien + 1e-9 < s:
            out.append({"ten": it.get("ten") or "", "nhom": nhom, "bien": round(bien, 1), "san": s})
    return out


def chan_duoi_san(noi_dung: dict, nd) -> None:
    """Lưu / trình duyệt báo giá: có dòng dưới sàn mà không phải CEO / Admin → 403."""
    from fastapi import HTTPException, status
    if la_qtv(nd):
        return
    ds = dong_duoi_san(noi_dung)
    if ds:
        vd = "; ".join(f"«{x['ten'][:40]}» {_pt(x['bien'])}% < sàn {x['san']:g}%" for x in ds[:3])
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            f"🔒 {len(ds)} dòng có giá bán DƯỚI SÀN biên ({vd}{'…' if len(ds) > 3 else ''}). "
                            "Nhân viên chỉ chỉnh giá từ sàn trở lên — muốn thấp hơn, nhờ CEO / Admin sửa.")


def ngay_ap_dung():
    """Mốc bắt buộc dự toán (config bg_ap_dung_tu). Báo giá tạo trước mốc và đã DA_DUYET / DA_GUI → miễn cổng 📋
    (không chặn gửi lại cho khách) — vẫn hiện nhãn trên danh sách để biết."""
    from datetime import date as _d
    try:
        return _d.fromisoformat((settings.bg_ap_dung_tu or "").strip()) if (settings.bg_ap_dung_tu or "").strip() else None
    except ValueError:
        return None


def mien_truoc_moc(db: Session, bgf) -> bool:
    from datetime import date as _d
    from .models import AuditLog
    ad = ngay_ap_dung()
    if ad is None or getattr(bgf, "trang_thai", None) not in ("DA_DUYET", "DA_GUI"):
        return False
    nd = bgf.noi_dung or {}
    try:
        ngay = _d.fromisoformat(str(nd.get("ngay") or "")[:10])
    except ValueError:
        ngay = None
    if ngay is None:                                            # không có ngày trên báo giá → lấy ngày tạo trong audit
        al = (db.query(AuditLog.thoi_gian).filter(AuditLog.bang == "bao_gia_form", AuditLog.ban_ghi_id == bgf.id,
                                                   AuditLog.hanh_dong == "TAO").order_by(AuditLog.id).first())
        ngay = al[0].date() if al and al[0] else None
    return bool(ngay and ngay < ad)


def ban_nhap(bgf) -> bool:
    """🖨 Bản in / PDF có đóng dấu BẢN NHÁP không (31/10/2026, mục 1 rà logic): chỉ báo giá ĐÃ DUYỆT / ĐÃ GỬI mới in sạch.
    Ngoại lệ: «đã xuất PDF» từ TRƯỚC mốc bg_ap_dung_tu (gửi tay thời chưa có cổng) → in sạch để in lại cho khách; hợp đồng không dấu."""
    from datetime import date as _d
    tt = getattr(bgf, "trang_thai", None)
    nd = getattr(bgf, "noi_dung", None) or {}
    if tt in ("DA_DUYET", "DA_GUI") or nd.get("loai") == "HOP_DONG":
        return False
    if tt == "DA_XUAT":
        ad = ngay_ap_dung()
        try:
            ngay = _d.fromisoformat(str(nd.get("ngay") or "")[:10])
        except ValueError:
            ngay = None
        if ad is not None and ngay is not None and ngay < ad:
            return False
    return True


def cong(db: Session, bgf, nd, xac_nhan: bool, buoc: str, kiem_bien: bool = False) -> dict:
    """Cổng kiểm soát một bước (TRÌNH DUYỆT / DUYỆT / GỬI KHÁCH).
    Thiếu dự toán: người thường 400; CEO chưa xác nhận 409 (📋). Biên thấp (khi kiem_bien): người thường 403; CEO 409 (📉)."""
    from fastapi import HTTPException, status
    k = kiem_tra(db, bgf)
    van_de = []
    if k["thieu_du_toan"] and mien_truoc_moc(db, bgf):         # báo giá cũ đã duyệt / đã gửi → miễn, chỉ ghi vết
        k["mien_truoc_moc"] = True
        k["thieu_du_toan"] = None
    if k["thieu_du_toan"]:
        if not la_ceo(nd):
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"📋 {k['thieu_du_toan']} Báo giá phải lập từ dự toán có đủ dòng và đủ giá mới {buoc} được — "
                                "lập / hoàn thiện ở Bán hàng → Dự toán hàng bán (hoặc BOQ dự án) rồi làm lại. CEO được vượt.")
        van_de.append("📋 " + k["thieu_du_toan"])
    if k["ngoai_chua_uoc"]:
        ten = ", ".join(x[:40] for x in k["ngoai_chua_uoc"][:3]) + ("…" if len(k["ngoai_chua_uoc"]) > 3 else "")
        msg = f"➕ {len(k['ngoai_chua_uoc'])} dòng NGOÀI DỰ TOÁN chưa có chi phí dự kiến ({ten}) — nhập giá vốn ước để tính biên."
        if not la_ceo(nd):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, msg + " CEO được vượt.")
        van_de.append(msg)
    if kiem_bien and k["canh_bao_bien"]:
        if not la_ceo(nd):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"📉 {k['canh_bao_bien']} — chỉ CEO duyệt được báo giá này.")
        van_de.append("📉 " + k["canh_bao_bien"])
    if kiem_bien and k.get("gia_uoc"):                        # mig 162: giá vốn ƯỚC → biên chưa đáng tin, chỉ CEO duyệt
        if not la_ceo(nd):
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                f"⚠ {k['canh_bao_uoc']} Rà giá vốn ở Bán hàng → Dự toán hàng bán (sửa giá từng dòng hoặc "
                                "bấm ✓ Đã rà giá vốn) rồi duyệt, hoặc nhờ CEO duyệt.")
        van_de.append("⚠ " + k["canh_bao_uoc"])
    if van_de and not xac_nhan:
        raise HTTPException(status.HTTP_409_CONFLICT, " ".join(van_de))
    k["vuot"] = van_de
    return k
