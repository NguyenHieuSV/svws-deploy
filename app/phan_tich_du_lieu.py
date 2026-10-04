"""
📊 PHÂN TÍCH DỮ LIỆU — Overall Financial (chỉ CEO).
Gom số liệu THẬT đã có ở các module (bán hàng · lương · chi phí · sổ quỹ · công nợ · quy trình) thành 6 ĐỀ MỤC, mỗi đề mục có
biểu đồ + NHẬN XÉT + ĐỀ XUẤT viết theo 4 góc nhìn: TC tài chính · BH bán hàng · QT quản trị · DL dữ liệu.
Chỉ ĐỌC — không ghi gì. Mỗi đề mục tính độc lập: một đề mục lỗi không làm hỏng cả tab.
Nguồn số: Lãi/Lỗ Record (_tinh_lai_lo_tong) · hóa đơn bán · PO · bảng lương · sổ cái tiền TK 111/112 · sổ công nợ.
"""
from datetime import date, timedelta
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from .models import (HoaDon, DonHang, DonMua, KhachHang, NhaCungCap, CongNo, ButToan, TaiKhoanQuy, BaoGia, CoHoi,
                     ChiCoDinh, LenhChiBank, ChiNgoaiLenh, DuToanBan, DuAn)

MAU = {"TM": "#0284c7", "DV": "#ea580c", "DA": "#7c3aed", "KHAC": "#64748b"}      # cùng màu tab Doanh thu theo mảng
MAU_THU, MAU_CHI, MAU_BA, MAU_XAM = "#0284c7", "#ea580c", "#7c3aed", "#64748b"
MANG_TEN = {"TM": "Thương mại", "DV": "Dịch vụ", "DA": "Dự án", "KHAC": "Khác"}
TUOI_NO = [("CHUA_HAN", "Chưa đến hạn"), ("QH_30", "Quá hạn 1–30 ngày"), ("QH_60", "Quá hạn 31–60"),
           ("QH_90", "Quá hạn 61–90"), ("QH_90P", "Quá hạn trên 90"), ("KHONG_HAN", "Chưa đặt hạn")]


def _f(x) -> float:
    return float(x or 0)


def _g(v) -> str:
    """Tiền gọn tiếng Việt: 1,23 tỷ · 456,7 tr · 12.000 đ."""
    v = _f(v)
    a = abs(v)
    if a >= 1e9:
        return f"{v / 1e9:.2f}".replace(".", ",") + " tỷ"
    if a >= 1e6:
        return f"{v / 1e6:.1f}".replace(".", ",") + " tr"
    return f"{v:,.0f}".replace(",", ".") + " đ"


def _pt(a, b, n=1):
    return round(_f(a) / _f(b) * 100, n) if _f(b) else None


def _p(v) -> str:
    return "—" if v is None else (f"{v:.1f}".replace(".", ",") + "%")


def _mm(k: str) -> str:
    return f"{k[5:7]}/{k[2:4]}"


def _months(hom_nay: date, n: int = 12) -> list:
    out = []
    for i in range(n - 1, -1, -1):
        y, m = hom_nay.year, hom_nay.month - i
        while m <= 0:
            y, m = y - 1, m + 12
        out.append(f"{y}-{m:02d}")
    return out


def _nx(goc, muc, nd):
    return {"goc": goc, "muc": muc, "nd": nd}


def _dx(goc, uu_tien, viec, vi_sao=""):
    return {"goc": goc, "uu_tien": uu_tien, "viec": viec, "vi_sao": vi_sao}


# ====================================================================================================
#  THU THẬP SỐ LIỆU
# ====================================================================================================
def _thu_thap(db: Session, hom_nay: date) -> dict:
    from .routers.tai_chinh import _tinh_lai_lo_tong, _mang_cua
    months = _months(hom_nay, 12)
    d0 = date(int(months[0][:4]), int(months[0][5:7]), 1)
    D = {"hom_nay": hom_nay, "months": months, "thang_nay": months[-1]}
    t = _tinh_lai_lo_tong(db)
    D["t"] = t
    so_dh = {i: (s or "").strip() for (i, s) in db.query(DonHang.id, DonHang.so).all()}
    dh_kh = {i: k for (i, k) in db.query(DonHang.id, DonHang.khach_hang_id).all()}
    kh_ten = {i: n for (i, n) in db.query(KhachHang.id, KhachHang.ten).all()}
    ncc_ten = {i: n for (i, n) in db.query(NhaCungCap.id, NhaCungCap.ten).all()}

    # ---- hóa đơn BÁN theo tháng × mảng, theo khách ----
    hd_thang = {m: {"TM": 0.0, "DV": 0.0, "DA": 0.0, "KHAC": 0.0} for m in months}
    kh_dt, so_hd, hd_90 = {}, 0, 0.0
    moc90 = hom_nay - timedelta(days=90)
    for hd in db.query(HoaDon).filter(HoaDon.loai == "BAN", HoaDon.ngay >= d0).all():
        k = str(hd.ngay)[:7]
        if k not in hd_thang:
            continue
        v = _f(hd.tong_tien)
        hd_thang[k][_mang_cua(so_dh.get(hd.don_hang_id) if hd.don_hang_id else None)] += v
        kid = hd.khach_hang_id or dh_kh.get(hd.don_hang_id)
        kh_dt[kid] = kh_dt.get(kid, 0.0) + v
        so_hd += 1
        if hd.ngay and hd.ngay >= moc90:
            hd_90 += v
    D["hd_thang"], D["so_hd"], D["hd_90"] = hd_thang, so_hd, hd_90
    D["hd_tong"] = {m: sum(hd_thang[m].values()) for m in months}
    D["top_kh"] = sorted(((kh_ten.get(k) or "(chưa gắn khách)", v) for k, v in kh_dt.items() if v > 0), key=lambda x: -x[1])

    # ---- đơn bán mới theo tháng ----
    don_thang = {m: {"so": 0, "gia_tri": 0.0} for m in months}
    for (ngay, tt, th, loai) in db.query(DonHang.ngay, DonHang.tong_tien, DonHang.tien_thue, DonHang.loai_don).filter(DonHang.ngay >= d0).all():
        k = str(ngay)[:7]
        if k in don_thang and (loai or "THUONG") != "DAU_TU":
            don_thang[k]["so"] += 1
            don_thang[k]["gia_tri"] += _f(tt) + _f(th)
    D["don_thang"] = don_thang

    # ---- lãi theo mảng + mã lỗ (cùng công thức Lãi/Lỗ Record) ----
    mang = {k: {"dt": 0.0, "cp": 0.0, "so_ma": 0} for k in MANG_TEN}
    ma_lo, cho_dt, theo_nhom = [], [], {}
    for x in t.get("theo_ma") or []:
        if x.get("la_dau_tu"):
            continue
        s = mang[_mang_cua(x.get("ma_ban"))]
        s["dt"] += _f(x.get("doanh_thu")); s["cp"] += _f(x.get("tong_chi_phi")); s["so_ma"] += 1
        # đọc theo NHÓM gốc + tháng: đuôi -01/-02 sau MMYY là các hóa đơn / đợt của cùng một đơn tháng
        g = theo_nhom.setdefault(x.get("nhom") or x.get("ma_ban"), {"dt": 0.0, "cp": 0.0})
        g["dt"] += _f(x.get("doanh_thu")); g["cp"] += _f(x.get("tong_chi_phi"))
    for k, g in theo_nhom.items():
        if g["dt"] > 0 and g["cp"] - g["dt"] >= 1e6:          # lỗ dưới 1 triệu coi như hòa vốn (chênh lệch làm tròn)
            ma_lo.append((k, g["dt"], g["dt"] - g["cp"]))
        elif g["dt"] == 0 and g["cp"] > 0:
            cho_dt.append((k, g["cp"]))
    D["mang"] = mang
    D["ma_lo"] = sorted(ma_lo, key=lambda x: x[2])
    D["cho_dt"] = sorted(cho_dt, key=lambda x: -x[1])

    # ---- báo giá · cơ hội ----
    bg = {}
    for (tt, n, s) in db.query(BaoGia.trang_thai, func.count(BaoGia.id), func.coalesce(func.sum(BaoGia.tong_tien), 0)).group_by(BaoGia.trang_thai).all():
        bg[str(tt)] = {"so": int(n), "gia_tri": _f(s)}
    D["bao_gia"] = bg
    D["bg_co_don"] = int(db.query(func.count(func.distinct(DonHang.bao_gia_id))).filter(DonHang.bao_gia_id.isnot(None)).scalar() or 0)
    ch = {}
    for (gd, n, s) in db.query(CoHoi.giai_doan, func.count(CoHoi.id), func.coalesce(func.sum(CoHoi.gia_tri_dk), 0)).group_by(CoHoi.giai_doan).all():
        ch[str(gd)] = {"so": int(n), "gia_tri": _f(s)}
    D["co_hoi"] = ch

    # ---- PO đã duyệt theo tháng, theo NCC ----
    po_thang, ncc_po, po_90 = {m: 0.0 for m in months}, {}, 0.0
    po_nam = {"tong": 0, "co_ma": 0, "da_duyet": 0, "co_hd": 0, "cho_duyet": 0}
    for (ngay, tong, tt, nid, dh, mb, shd) in db.query(DonMua.ngay, DonMua.tong_tien, DonMua.trang_thai, DonMua.nha_cung_cap_id,
                                                        DonMua.don_hang_id, DonMua.ma_ban, DonMua.so_hoa_don).filter(DonMua.ngay >= d0).all():
        tt = str(tt)
        if tt == "TU_CHOI":
            continue
        po_nam["tong"] += 1
        if dh or (mb or "").strip():
            po_nam["co_ma"] += 1
        if tt == "CHO_DUYET":
            po_nam["cho_duyet"] += 1
        if tt != "DA_DUYET":
            continue
        po_nam["da_duyet"] += 1
        if (shd or "").strip():
            po_nam["co_hd"] += 1
        k = str(ngay)[:7]
        if k in po_thang:
            po_thang[k] += _f(tong)
        ncc_po[nid] = ncc_po.get(nid, 0.0) + _f(tong)
        if ngay and ngay >= moc90:
            po_90 += _f(tong)
    D["po_thang"], D["po_nam"], D["po_90"] = po_thang, po_nam, po_90
    D["top_ncc"] = sorted(((ncc_ten.get(k) or "(không rõ NCC)", v) for k, v in ncc_po.items() if v > 0), key=lambda x: -x[1])

    # ---- nhân sự theo tháng (chỉ có trong năm hiện tại — cùng nguồn Lãi/Lỗ) ----
    D["ns"] = t.get("nhan_su") or {}
    D["ns_thang"] = {x["thang"]: x for x in (D["ns"].get("theo_thang") or [])}

    # ---- tiền vào / ra theo tháng: sổ cái TK 111 · 112 (bỏ chuyển quỹ nội bộ) ----
    def la_tien(tk):
        return str(tk or "").startswith(("111", "112"))
    cash = {m: {"vao": 0.0, "ra": 0.0} for m in months}
    for (ngay, no, co, st) in db.query(ButToan.ngay, ButToan.tk_no, ButToan.tk_co, ButToan.so_tien).filter(
            ButToan.ngay >= d0, or_(ButToan.tk_no.like("111%"), ButToan.tk_no.like("112%"),
                                    ButToan.tk_co.like("111%"), ButToan.tk_co.like("112%"))).all():
        a, b = la_tien(no), la_tien(co)
        k = str(ngay)[:7]
        if (a and b) or k not in cash:
            continue
        cash[k]["vao" if a else "ra"] += _f(st)
    D["cash"] = cash
    D["quy"] = [{"ten": q.ten, "so_du": _f(q.so_du)} for q in db.query(TaiKhoanQuy).filter(TaiKhoanQuy.hoat_dong.is_(True)).all()]

    # ---- công nợ: tuổi nợ · top · lịch 8 tuần ----
    tuoi = {"PHAI_THU": {k: 0.0 for k, _ in TUOI_NO}, "PHAI_TRA": {k: 0.0 for k, _ in TUOI_NO}}
    dem = {"PHAI_THU": {"so": 0, "khong_han": 0}, "PHAI_TRA": {"so": 0, "khong_han": 0}}
    no_kh, no_ncc = {}, {}
    tuan = [{"tu": hom_nay + timedelta(days=i * 7), "thu": 0.0, "chi": 0.0} for i in range(8)]
    for c in db.query(CongNo).all():
        con = _f(c.so_tien) - _f(c.da_thanh_toan)
        loai = str(c.loai)
        if con <= 0.5 or loai not in tuoi:
            continue
        dem[loai]["so"] += 1
        if c.han is None:
            b = "KHONG_HAN"
            dem[loai]["khong_han"] += 1
        else:
            tre = (hom_nay - c.han).days
            b = "CHUA_HAN" if tre <= 0 else "QH_30" if tre <= 30 else "QH_60" if tre <= 60 else "QH_90" if tre <= 90 else "QH_90P"
            wi = 0 if tre > 0 else (c.han - hom_nay).days // 7
            if wi < 8:
                tuan[wi]["thu" if loai == "PHAI_THU" else "chi"] += con
        tuoi[loai][b] += con
        if loai == "PHAI_THU":
            no_kh[c.khach_hang_id] = no_kh.get(c.khach_hang_id, 0.0) + con
        else:
            no_ncc[c.nha_cung_cap_id] = no_ncc.get(c.nha_cung_cap_id, 0.0) + con
    D["tuoi"], D["dem_cn"], D["tuan"] = tuoi, dem, tuan
    D["top_no_kh"] = sorted(((kh_ten.get(k) or "(chưa gắn khách)", v) for k, v in no_kh.items()), key=lambda x: -x[1])
    D["top_no_ncc"] = sorted(((ncc_ten.get(k) or "(không rõ NCC)", v) for k, v in no_ncc.items()), key=lambda x: -x[1])

    # ---- quy trình · chất lượng dữ liệu ----
    q = {}
    q["hd_ban"] = int(db.query(func.count(HoaDon.id)).filter(HoaDon.loai == "BAN", HoaDon.ngay >= d0).scalar() or 0)
    q["hd_ban_da_gui"] = int(db.query(func.count(HoaDon.id)).filter(HoaDon.loai == "BAN", HoaDon.ngay >= d0,
                                                                   HoaDon.gui_khach_luc.isnot(None)).scalar() or 0)
    q["kh"] = int(db.query(func.count(KhachHang.id)).scalar() or 0)
    q["kh_co_phu_trach"] = int(db.query(func.count(KhachHang.id)).filter(KhachHang.nguoi_phu_trach.isnot(None)).scalar() or 0)
    q["chi_co_dinh"] = int(db.query(func.count(ChiCoDinh.id)).filter(ChiCoDinh.dang_ap_dung.is_(True)).scalar() or 0)
    lc = db.query(func.count(LenhChiBank.id), func.coalesce(func.sum(LenhChiBank.so_tien), 0)).filter(LenhChiBank.trang_thai == "CHO_DUYET").first()
    q["lenh_cho"], q["lenh_cho_tien"] = int(lc[0] or 0), _f(lc[1])
    nl = db.query(func.count(ChiNgoaiLenh.id), func.coalesce(func.sum(ChiNgoaiLenh.so_tien), 0)).filter(ChiNgoaiLenh.ngay >= moc90).first()
    q["ngoai_lenh"], q["ngoai_lenh_tien"] = int(nl[0] or 0), _f(nl[1])
    # đơn bán 90 ngày gần nhất (TM · DA · DV) đã có dự toán?
    from .ma_code import nhom, phan_tich as _ptm
    co_dt = {str(m).strip().lower() for (m,) in db.query(DuToanBan.ma).all() if m}
    nhom_dt = {nhom(m) for m in co_dt} | {nhom(m) for (m,) in db.query(DuAn.ma).all() if m}
    nhom_dt.discard(None); nhom_dt.discard("")
    from .du_toan_ks import NGAY_AP_DUNG
    D["ngay_dt"] = f"{NGAY_AP_DUNG:%d/%m/%Y}"
    cu_ma, cu_nhom = set(), set()                  # mã / nhóm đã đặt ra từ ngày áp dụng trở về trước → miễn (CEO chốt 18/09/2026)
    for (so,) in db.query(DonHang.so).filter(DonHang.so.isnot(None), DonHang.ngay <= NGAY_AP_DUNG).all():
        cu_ma.add(so.strip().lower())
        if nhom(so):
            cu_nhom.add(nhom(so))
    don_xet = don_co = 0
    for (so, ngay, loai) in db.query(DonHang.so, DonHang.ngay, DonHang.loai_don).filter(DonHang.ngay > NGAY_AP_DUNG).all():
        so = (so or "").strip()
        if not so or (loai or "THUONG") == "DAU_TU" or (_ptm(so).get("loai") or "") not in ("TM", "DA", "DV"):
            continue
        if so.lower() in cu_ma or (nhom(so) and nhom(so) in cu_nhom):
            continue
        don_xet += 1
        if so.lower() in co_dt or (nhom(so) and nhom(so) in nhom_dt):
            don_co += 1
    q["don_xet_dt"], q["don_co_dt"] = don_xet, don_co
    try:
        from .routers.ke_toan_quy import _don_chua_hoa_don
        q["don_chua_hd"] = len(_don_chua_hoa_don(db))
    except Exception:
        db.rollback()
        q["don_chua_hd"] = None
    try:
        from .tam_ung_mua import tam_ung_mua_hang
        tu = tam_ung_mua_hang(db)
        q["tam_ung"], q["tam_ung_po"] = _f(tu.get("tong")), int(tu.get("so_po") or 0)
    except Exception:
        db.rollback()
        q["tam_ung"], q["tam_ung_po"] = 0.0, 0
    D["q"] = q

    # ---- chỉ giữ các tháng từ tháng đầu tiên có số liệu (tối thiểu 6 tháng gần nhất) ----
    def co_so(m):
        return (D["hd_tong"][m] or po_thang[m] or cash[m]["vao"] or cash[m]["ra"] or don_thang[m]["so"]
                or _f((D["ns_thang"].get(m) or {}).get("tong")))
    i0 = next((i for i, m in enumerate(months) if co_so(m)), len(months) - 6)
    D["mh"] = months[min(i0, len(months) - 6):]
    return D


# ====================================================================================================
#  6 ĐỀ MỤC
# ====================================================================================================
def _muc_ban_hang(D) -> dict:
    mh, hd, tong = D["mh"], D["hd_thang"], D["hd_tong"]
    nx, dx = [], []
    tong_ky = sum(tong[m] for m in mh)
    co_dt = [m for m in mh if tong[m] > 0]
    cd = {k: sum(hd[m][k] for m in mh) for k in MANG_TEN}
    bd = [{"loai": "cot", "chong": True, "tieu_de": "Doanh thu hóa đơn bán theo tháng, chia theo mảng (gồm VAT)",
           "nhan": [_mm(m) for m in mh],
           "chuoi": [{"ten": MANG_TEN[k], "mau": MAU[k], "gt": [hd[m][k] for m in mh]} for k in MANG_TEN if cd[k] > 0]}]
    # --- nhịp doanh thu ---
    if not co_dt:
        nx.append(_nx("DL", "CANH_BAO", "Chưa có hóa đơn bán nào trong 12 tháng gần nhất trên hệ thống, nên chưa phân tích được nhịp bán hàng."))
    else:
        bq = tong_ky / len(co_dt)
        dinh = max(co_dt, key=lambda m: tong[m])
        nx.append(_nx("BH", "TOT", f"Doanh thu hóa đơn {len(co_dt)} tháng có số liệu đạt {_g(tong_ky)}, bình quân {_g(bq)}/tháng; "
                                    f"tháng cao nhất là {_mm(dinh)} với {_g(tong[dinh])}."))
        tron = [m for m in co_dt if m != D["thang_nay"]]          # tháng đã trọn
        if len(tron) >= 2:
            a, b = tron[-1], tron[-2]
            tg = _pt(tong[a] - tong[b], tong[b])
            if tg is not None:
                nx.append(_nx("BH", "TOT" if tg >= 0 else "LUU_Y",
                              f"Tháng {_mm(a)} đạt {_g(tong[a])}, {'tăng' if tg >= 0 else 'giảm'} {_p(abs(tg))} so với tháng {_mm(b)} ({_g(tong[b])})."))
            vals = [tong[m] for m in tron]
            if min(vals) > 0 and max(vals) / min(vals) >= 2:
                nx.append(_nx("TC", "LUU_Y", f"Doanh thu dao động mạnh giữa các tháng (thấp nhất {_g(min(vals))}, cao nhất {_g(max(vals))}). "
                                             "Doanh thu phụ thuộc vào vài đơn lớn nên khó dự báo dòng tiền."))
                dx.append(_dx("BH", "TRUNG", "Tăng tỷ trọng doanh thu lặp lại hàng tháng: hợp đồng dịch vụ vận hành, cho thuê, bán nước theo m³, cung cấp hóa chất định kỳ.",
                              "Doanh thu định kỳ giúp san phẳng các tháng thấp và dễ lập kế hoạch tiền."))
        if tong_ky > 0:
            lon = max(cd, key=lambda k: cd[k])
            nx.append(_nx("BH", "TOT", "Cơ cấu doanh thu hóa đơn theo mảng: " + " · ".join(
                f"{MANG_TEN[k]} {_p(_pt(cd[k], tong_ky))}" for k in MANG_TEN if cd[k] / tong_ky >= 0.0005) + f". Mảng lớn nhất là {MANG_TEN[lon]}."))
    # --- tập trung khách hàng ---
    top = D["top_kh"]
    tk = sum(v for _, v in top)
    if top and tk > 0:
        bd.append({"loai": "thanh", "tieu_de": "Khách hàng lớn nhất theo doanh thu hóa đơn 12 tháng (gồm VAT)", "mau": MAU_THU,
                   "dong": [{"nhan": n, "gt": v, "phu": _p(_pt(v, tk))} for n, v in top[:8]]})
        t1, t3 = _pt(top[0][1], tk), _pt(sum(v for _, v in top[:3]), tk)
        muc = "CANH_BAO" if t1 >= 40 else "LUU_Y" if (t1 >= 25 or t3 >= 70) else "TOT"
        nx.append(_nx("BH", muc, f"Có {len(top)} khách hàng phát sinh hóa đơn. Khách lớn nhất ({top[0][0]}) chiếm {_p(t1)} doanh thu, "
                                 f"3 khách lớn nhất chiếm {_p(t3)}."))
        if muc != "TOT":
            dx.append(_dx("BH", "CAO" if muc == "CANH_BAO" else "TRUNG",
                          "Giảm phụ thuộc vào nhóm khách lớn: giao chỉ tiêu mở khách hàng mới theo quý và chăm sóc lại nhóm khách cỡ vừa.",
                          f"Mất một khách trong nhóm đầu có thể làm doanh thu giảm tới {_p(t1)}."))
    # --- biên lãi theo mảng ---
    mg = D["mang"]
    dong = []
    dt_all = sum(v["dt"] for v in mg.values())
    for k in ("TM", "DV", "DA"):
        s = mg[k]
        if s["dt"] > 0 and s["dt"] >= 0.01 * dt_all:
            dong.append({"nhan": MANG_TEN[k], "gt": _pt(s["dt"] - s["cp"], s["dt"]), "phu": f"DT {_g(s['dt'])} · lãi {_g(s['dt'] - s['cp'])}", "mau": MAU[k]})
    if dong:
        bd.append({"loai": "thanh", "tieu_de": "Tỷ suất lãi theo mảng (lãi ÷ doanh thu theo mã, lũy kế)", "don_vi": "%", "dong": dong})
        thap = min(dong, key=lambda x: x["gt"])
        cao = max(dong, key=lambda x: x["gt"])
        nx.append(_nx("TC", "LUU_Y" if thap["gt"] < 15 else "TOT",
                      f"Mảng {cao['nhan']} có tỷ suất lãi cao nhất ({_p(cao['gt'])}); mảng {thap['nhan']} thấp nhất ({_p(thap['gt'])})."))
        if thap["gt"] < 15:
            dx.append(_dx("TC", "TRUNG", f"Rà lại giá bán và giá mua của mảng {thap['nhan']}: đặt mức lãi tối thiểu khi báo giá và bắt buộc lập dự toán trước khi chốt đơn.",
                          f"Tỷ suất lãi {_p(thap['gt'])} dễ bị ăn mòn bởi chi phí vận chuyển, bảo hành và chậm thanh toán."))
    lo = D["ma_lo"]
    if lo:
        nx.append(_nx("TC", "CANH_BAO", f"Có {len(lo)} mã (gộp theo nhóm gốc + tháng) đang lỗ, tổng lỗ {_g(-sum(x[2] for x in lo))}. Lỗ nhiều nhất: "
                                         + "; ".join(f"{m} ({_g(l)})" for m, _, l in lo[:3]) + "."))
        dx.append(_dx("QT", "CAO", "Họp rà từng mã lỗ với người phụ trách: xác định lỗ thật hay do ghi thiếu doanh thu, ghi nhầm mã chi phí.",
                      "Mã lỗ thật cần rút kinh nghiệm báo giá; mã lỗ do dữ liệu cần sửa để Lãi/Lỗ phản ánh đúng."))
    cho = D["cho_dt"]
    if cho:
        nx.append(_nx("DL", "LUU_Y", f"{len(cho)} mã (gộp theo nhóm gốc + tháng) đã có chi phí nhưng chưa có doanh thu, tổng chi {_g(sum(v for _, v in cho))}. "
                                      "Đây có thể là đơn đang thực hiện, hoặc mã chưa lập đơn bán."))
    # --- phễu bán hàng ---
    bg = D["bao_gia"]
    n_bg = sum(v["so"] for v in bg.values())
    if n_bg:
        tl = _pt(D["bg_co_don"], n_bg)
        cho_bg = sum(v["so"] for k, v in bg.items() if k in ("NHAP", "CHO_DUYET"))
        nx.append(_nx("BH", "TOT" if (tl or 0) >= 30 else "LUU_Y",
                      f"Hệ thống có {n_bg} báo giá, trong đó {D['bg_co_don']} báo giá đã thành đơn hàng (tỷ lệ chốt {_p(tl)}); {cho_bg} báo giá còn nháp hoặc chờ duyệt."))
        if (tl or 0) < 30:
            dx.append(_dx("BH", "TRUNG", "Theo dõi lý do thua của từng báo giá và hẹn ngày gọi lại khách trong vòng 7 ngày sau khi gửi.",
                          "Tỷ lệ chốt thấp thường do thiếu theo đuổi sau báo giá, không phải do giá."))
    else:
        nx.append(_nx("DL", "LUU_Y", "Chưa có báo giá nào được lập trên hệ thống nên chưa đo được tỷ lệ chốt đơn."))
        dx.append(_dx("BH", "TRUNG", "Lập báo giá trên hệ thống thay vì file rời, để đo tỷ lệ chốt và giá trị phễu bán hàng.", ""))
    ch = D["co_hoi"]
    if ch:
        mo = {k: v for k, v in ch.items() if k not in ("THANG", "THUA", "DONG", "HUY")}
        nx.append(_nx("BH", "TOT", f"Phễu cơ hội (CRM) có {sum(v['so'] for v in ch.values())} cơ hội, {sum(v['so'] for v in mo.values())} cơ hội đang mở "
                                    f"với giá trị dự kiến {_g(sum(v['gia_tri'] for v in mo.values()))}."))
    return {"ma": "BAN_HANG", "ten": "Bán hàng và khách hàng", "icon": "🤝", "bieu_do": bd, "nhan_xet": nx, "de_xuat": dx,
            "so_lieu": {"doanh_thu_hoa_don_ky": tong_ky, "theo_thang": {m: tong[m] for m in mh}, "co_cau_mang": cd,
                        "top_khach": top[:5], "lai_theo_mang": {k: {"doanh_thu": v["dt"], "chi_phi": v["cp"]} for k, v in mg.items() if v["dt"] or v["cp"]},
                        "so_ma_lo": len(lo), "tong_lo": sum(x[2] for x in lo), "bao_gia": bg, "bao_gia_thanh_don": D["bg_co_don"]}}


def _muc_nhan_su(D) -> dict:
    ns, nst, tong = D["ns"], D["ns_thang"], D["hd_tong"]
    mh = [m for m in D["mh"] if m in nst]
    nx, dx, bd = [], [], []
    co = [m for m in mh if _f(nst[m].get("tong")) > 0]
    if not co:
        nx.append(_nx("DL", "CANH_BAO", "Chưa có bảng lương hay khoản thuê ngoài nào trong năm trên hệ thống, nên chi phí nhân sự chưa được tính vào Lãi/Lỗ."))
        dx.append(_dx("QT", "CAO", "Lập bảng lương hàng tháng trên hệ thống (mục Nhân sự) để Lãi/Lỗ trừ đúng chi phí con người.", ""))
        return {"ma": "NHAN_SU", "ten": "Tiền lương và nhân sự", "icon": "👥", "bieu_do": bd, "nhan_xet": nx, "de_xuat": dx, "so_lieu": {}}
    bd.append({"loai": "cot", "chong": True, "tieu_de": "Chi phí nhân sự theo tháng (lương + bảo hiểm phần công ty · thuê ngoài · dự phòng)",
               "nhan": [_mm(m) for m in mh],
               "chuoi": [c for c in [{"ten": "Lương + BH công ty", "mau": MAU_THU, "gt": [_f(nst[m]["luong"]) for m in mh]},
                                     {"ten": "Thuê ngoài đã chi", "mau": MAU_CHI, "gt": [_f(nst[m]["thue_ngoai"]) for m in mh]},
                                     {"ten": "Dự phòng (chi cố định «lương»)", "mau": MAU_BA, "gt": [_f(nst[m]["du_phong"]) for m in mh]}]
                         if any(c["gt"])]})
    tl = [(m, _pt(nst[m]["tong"], tong[m])) for m in co if tong.get(m, 0) > 0]
    if tl:
        bd.append({"loai": "cot", "tieu_de": "Chi phí nhân sự so với doanh thu hóa đơn cùng tháng", "don_vi": "%",
                   "nhan": [_mm(m) for m, _ in tl], "chuoi": [{"ten": "Nhân sự ÷ doanh thu", "mau": MAU_BA, "gt": [v for _, v in tl]}]})
    tong_ns = sum(_f(nst[m]["tong"]) for m in co)
    bq = tong_ns / len(co)
    nv = [int(nst[m]["so_nv"]) for m in co if nst[m]["so_nv"]]
    nx.append(_nx("TC", "TOT", f"Chi phí nhân sự {len(co)} tháng có số liệu là {_g(tong_ns)}, bình quân {_g(bq)}/tháng"
                               + (f" cho khoảng {round(sum(nv) / len(nv))} người (≈ {_g(bq / (sum(nv) / len(nv)))}/người/tháng, gồm bảo hiểm phần công ty)." if nv else ".")))
    if tl:
        tb = sum(v for _, v in tl) / len(tl)
        muc = "CANH_BAO" if tb >= 30 else "LUU_Y" if tb >= 18 else "TOT"
        nx.append(_nx("TC", muc, f"Chi phí nhân sự bằng bình quân {_p(tb)} doanh thu hóa đơn; tháng cao nhất {_p(max(v for _, v in tl))}, thấp nhất {_p(min(v for _, v in tl))}."))
        if nv:
            ds = [tong[m] / nst[m]["so_nv"] for m in co if nst[m]["so_nv"] and tong.get(m, 0) > 0]
            if ds:
                nx.append(_nx("QT", "TOT", f"Năng suất: doanh thu hóa đơn bình quân {_g(sum(ds) / len(ds))}/người/tháng."))
        if muc != "TOT":
            dx.append(_dx("QT", "TRUNG", "Đặt chỉ tiêu doanh thu trên đầu người theo phòng và xem lại cơ cấu nhân sự gián tiếp.",
                          f"Tỷ lệ nhân sự trên doanh thu {_p(tb)} cao so với doanh nghiệp kỹ thuật – thương mại cùng quy mô."))
    if len(nv) >= 2 and nv[-1] != nv[0]:
        nx.append(_nx("QT", "LUU_Y", f"Số người trong bảng lương giảm từ {nv[0]} xuống {nv[-1]}." if nv[-1] < nv[0]
                      else f"Số người trong bảng lương tăng từ {nv[0]} lên {nv[-1]}."))
    tn = sum(_f(nst[m]["thue_ngoai"]) for m in co)
    if tn > 0:
        nx.append(_nx("TC", "TOT", f"Thuê ngoài đã chi {_g(tn)}, bằng {_p(_pt(tn, tong_ns))} tổng chi phí nhân sự."))
    cho = [m for m in co if nst[m].get("cho_duyet")]
    if cho:
        nx.append(_nx("QT", "LUU_Y", f"Bảng lương tháng {', '.join(_mm(m) for m in cho)} còn dòng chờ duyệt; số trong Lãi/Lỗ là tạm tính."))
        dx.append(_dx("QT", "TRUNG", "Duyệt dứt điểm bảng lương các tháng còn treo để chốt chi phí và bút toán lương.", ""))
    thieu = [m for m in mh if m not in co and m != D["thang_nay"]]
    if thieu:
        nx.append(_nx("DL", "LUU_Y", f"Các tháng {', '.join(_mm(m) for m in thieu)} không có bảng lương trên hệ thống, nên Lãi/Lỗ các tháng này chưa trừ chi phí nhân sự."))
        dx.append(_dx("DL", "TRUNG", "Nhập bổ sung bảng lương các tháng còn thiếu, hoặc khai khoản Chi cố định «lương» để hệ thống tạm tính.",
                      "Thiếu lương làm lãi lũy kế cao hơn thực tế."))
    if D["thang_nay"] in nst and not _f(nst[D["thang_nay"]].get("tong")):
        nx.append(_nx("DL", "TOT", f"Tháng {_mm(D['thang_nay'])} chưa lập bảng lương; đây là bình thường khi tháng chưa kết thúc."))
    dx.append(_dx("TC", "THAP", "Lập ngân sách lương cả năm và so thực tế hàng tháng, kèm quỹ thưởng gắn với lãi theo mã.",
                  "Lương là khoản chi cố định lớn nhất sau giá vốn; có ngân sách thì dễ quyết định tuyển thêm hay thuê ngoài."))
    return {"ma": "NHAN_SU", "ten": "Tiền lương và nhân sự", "icon": "👥", "bieu_do": bd, "nhan_xet": nx, "de_xuat": dx,
            "so_lieu": {"tong_nhan_su": tong_ns, "binh_quan_thang": bq, "so_nguoi_theo_thang": {m: nst[m]["so_nv"] for m in co},
                        "ty_le_tren_doanh_thu": {m: v for m, v in tl}, "thue_ngoai": tn}}


def _muc_chi_phi(D) -> dict:
    t, mh = D["t"], D["mh"]
    nx, dx, bd = [], [], []
    dt = _f(t.get("doanh_thu"))
    co_cau = [("Giá vốn theo mã", _f(t.get("chi_phi_don"))), ("Nhân sự", _f(t.get("chi_nhan_su"))),
              ("Chi cố định", _f(t.get("chi_phi_khac"))), ("Hóa đơn mua ngoài PO", _f(t.get("chi_phi_hd_mua"))),
              ("Vận hành (mã OP)", _f(t.get("chi_phi_op"))), ("Chi chưa phân mã", _f(t.get("chi_chua_ma"))),
              ("Khấu hao cho thuê", _f(t.get("khau_hao_cho_thue")))]
    tong_cp = sum(v for _, v in co_cau)
    bd.append({"loai": "thanh", "tieu_de": "Cơ cấu chi phí lũy kế (cùng công thức Lãi/Lỗ Record)", "mau": MAU_CHI,
               "dong": [{"nhan": n, "gt": v, "phu": (_p(_pt(v, dt)) + " doanh thu") if dt else ""} for n, v in sorted(co_cau, key=lambda x: -x[1]) if v > 0]})
    nst, po = D["ns_thang"], D["po_thang"]
    bd.append({"loai": "duong", "tieu_de": "Doanh thu hóa đơn · PO mua đã duyệt · nhân sự theo tháng", "nhan": [_mm(m) for m in mh],
               "chuoi": [{"ten": "Doanh thu hóa đơn", "mau": MAU_THU, "gt": [D["hd_tong"][m] for m in mh]},
                         {"ten": "PO mua đã duyệt", "mau": MAU_CHI, "gt": [po[m] for m in mh]},
                         {"ten": "Nhân sự", "mau": MAU_BA, "gt": [_f((nst.get(m) or {}).get("tong")) for m in mh]}]})
    gv = _pt(t.get("chi_phi_don"), dt)
    lg = _pt(t.get("lai_gop"), dt)
    ll = _pt(t.get("lai_lo"), dt)
    if dt:
        nx.append(_nx("TC", "TOT" if (lg or 0) >= 20 else "LUU_Y",
                      f"Lũy kế: doanh thu theo mã {_g(dt)}, giá vốn {_g(t.get('chi_phi_don'))} (bằng {_p(gv)} doanh thu), lãi gộp {_g(t.get('lai_gop'))} (biên {_p(lg)})."))
        nx.append(_nx("TC", "TOT" if _f(t.get("lai_lo")) >= 0 else "CANH_BAO",
                      f"Sau khi trừ nhân sự, chi cố định, chi chưa phân mã và khấu hao, lãi/lỗ lũy kế là {_g(t.get('lai_lo'))} (biên {_p(ll)})."))
    dth = sum(D["hd_tong"][m] for m in mh)
    if dt and dth and abs(dt - dth) / max(dt, dth) > 0.1:
        nx.append(_nx("DL", "LUU_Y", f"Doanh thu theo mã ({_g(dt)}) và doanh thu hóa đơn 12 tháng ({_g(dth)}) là hai cách đo khác nhau: số theo mã lấy giá trị "
                                      "đơn bán của mọi mã đang có trên hệ thống, số hóa đơn chỉ gồm hóa đơn bán đã ghi ở Kế toán. "
                                      "Chênh lệch lớn cho thấy còn đơn chưa xuất hóa đơn hoặc hóa đơn chưa nhập đủ."))
    if D["q"]["chi_co_dinh"] == 0:
        nx.append(_nx("DL", "CANH_BAO", "Chưa khai khoản Chi cố định nào (thuê văn phòng, điện nước, phần mềm, xe, lãi vay…). "
                                         "Lãi/Lỗ hiện chưa trừ các khoản này nên đang cao hơn thực tế."))
        dx.append(_dx("TC", "CAO", "Khai danh sách Chi cố định hàng tháng ở Overall Financial để Lãi/Lỗ và dự báo dòng tiền trừ đủ chi phí vận hành công ty.",
                      "Thiếu chi cố định thì mọi chỉ số lãi và số tháng tiền mặt đều bị đẹp giả."))
    cm = _f(t.get("chi_chua_ma"))
    if cm > 0:
        nx.append(_nx("DL", "LUU_Y", f"Còn {_g(cm)} chi phí chưa phân vào mã nào" + (f" và {t.get('so_ma_le')} mã lẻ chưa có đơn bán." if t.get("so_ma_le") else ".")))
        dx.append(_dx("QT", "TRUNG", "Gắn mã cho các PO và công nợ chưa phân mã; mã mua về để dự trữ thì ghi mã KHO.",
                      "Chi phí không mang mã không vào được lãi/lỗ của đơn nào, người phụ trách đơn không thấy để kiểm soát."))
    if _f(t.get("chi_kho")) > 0:
        nx.append(_nx("TC", "TOT", f"Mua dự trữ kho {_g(t.get('chi_kho'))} được theo dõi là tồn kho, không trừ vào lãi/lỗ."))
    top = D["top_ncc"]
    tn = sum(v for _, v in top)
    if top and tn > 0:
        bd.append({"loai": "thanh", "tieu_de": "Nhà cung cấp lớn nhất theo giá trị PO đã duyệt 12 tháng", "mau": MAU_CHI,
                   "dong": [{"nhan": n, "gt": v, "phu": _p(_pt(v, tn))} for n, v in top[:8]]})
        t1, t5 = _pt(top[0][1], tn), _pt(sum(v for _, v in top[:5]), tn)
        nx.append(_nx("QT", "LUU_Y" if t1 >= 30 else "TOT", f"Mua hàng từ {len(top)} nhà cung cấp, tổng PO đã duyệt {_g(tn)}. "
                                                              f"Nhà cung cấp lớn nhất ({top[0][0]}) chiếm {_p(t1)}, 5 nhà lớn nhất chiếm {_p(t5)}."))
        dx.append(_dx("QT", "TRUNG", "Đàm phán giá khung và điều khoản trả chậm 30–45 ngày với 5 nhà cung cấp lớn nhất; mỗi nhóm hàng chính giữ ít nhất 2 nguồn.",
                      f"5 nhà cung cấp đầu chiếm {_p(t5)} giá trị mua, giảm 2–3% giá ở nhóm này tác động thẳng vào lãi gộp."))
    vuot = [m for m in mh if D["hd_tong"][m] > 0 and po[m] > D["hd_tong"][m]]
    if vuot:
        nx.append(_nx("TC", "LUU_Y", f"Tháng {', '.join(_mm(m) for m in vuot)} giá trị PO mua lớn hơn doanh thu hóa đơn cùng tháng: tiền ra trước, doanh thu về sau."))
    return {"ma": "CHI_PHI", "ten": "Cơ cấu chi phí và mua hàng", "icon": "🧾", "bieu_do": bd, "nhan_xet": nx, "de_xuat": dx,
            "so_lieu": {"doanh_thu_theo_ma": dt, "co_cau": dict(co_cau), "tong_chi_phi": tong_cp, "lai_gop": _f(t.get("lai_gop")),
                        "lai_lo": _f(t.get("lai_lo")), "bien_lai_gop_pct": lg, "top_ncc": top[:5], "so_khoan_chi_co_dinh": D["q"]["chi_co_dinh"]}}


def _muc_dong_tien(D) -> dict:
    mh, cash, tong = D["mh"], D["cash"], D["hd_tong"]
    nx, dx, bd = [], [], []
    vao, ra = sum(cash[m]["vao"] for m in mh), sum(cash[m]["ra"] for m in mh)
    bd.append({"loai": "cot", "tieu_de": "Tiền vào và tiền ra theo tháng (sổ cái tiền mặt · ngân hàng, TK 111 · 112)", "nhan": [_mm(m) for m in mh],
               "chuoi": [{"ten": "Tiền vào", "mau": MAU_THU, "gt": [cash[m]["vao"] for m in mh]},
                         {"ten": "Tiền ra", "mau": MAU_CHI, "gt": [cash[m]["ra"] for m in mh]}]})
    lk, s = [], 0.0
    for m in mh:
        s += cash[m]["vao"] - cash[m]["ra"]
        lk.append(s)
    bd.append({"loai": "duong", "tieu_de": "Dòng tiền ròng lũy kế (tiền vào − tiền ra, cộng dồn)", "nhan": [_mm(m) for m in mh],
               "chuoi": [{"ten": "Dòng tiền ròng lũy kế", "mau": MAU_BA, "gt": lk}]})
    if vao == 0 and ra == 0:
        nx.append(_nx("DL", "CANH_BAO", "Sổ cái tiền (TK 111 · 112) chưa có phát sinh trong 12 tháng, nên chưa phân tích được dòng tiền thật."))
    else:
        nx.append(_nx("TC", "TOT" if vao >= ra else "CANH_BAO",
                      f"Trong kỳ, tiền vào {_g(vao)}, tiền ra {_g(ra)}, dòng tiền ròng {_g(vao - ra)}."))
        am = [m for m in mh if cash[m]["ra"] > cash[m]["vao"] and (cash[m]["ra"] or cash[m]["vao"])]
        if am:
            nx.append(_nx("TC", "LUU_Y", f"Có {len(am)} tháng tiền ra nhiều hơn tiền vào: {', '.join(_mm(m) for m in am)}."))
        dth = sum(tong[m] for m in mh)
        if dth > 0:
            tl = _pt(vao, dth)
            nx.append(_nx("TC", "LUU_Y" if tl < 80 else "TOT",
                          f"Tiền thu về bằng {_p(tl)} doanh thu hóa đơn cùng kỳ ({_g(dth)})."
                          + (" Doanh thu đang nằm lại ở công nợ phải thu." if tl < 80
                             else " Thu nhiều hơn hóa đơn vì có khoản thu của đơn xuất hóa đơn từ trước kỳ, tiền cọc, hoặc hóa đơn chưa nhập lên hệ thống." if tl > 110 else "")))
    quy = D["quy"]
    tq = sum(q["so_du"] for q in quy)
    am_q = [q for q in quy if q["so_du"] < 0]
    if not quy:
        nx.append(_nx("DL", "LUU_Y", "Chưa khai sổ quỹ tiền mặt hay tài khoản ngân hàng nào đang hoạt động."))
    elif am_q:
        nx.append(_nx("DL", "CANH_BAO", f"Số dư sổ quỹ trên hệ thống đang âm {_g(-sum(q['so_du'] for q in am_q))} ({', '.join(q['ten'] for q in am_q[:3])}). "
                                         "Tiền thật không thể âm: sổ quỹ đang thiếu số dư đầu kỳ hoặc thiếu phiếu thu."))
        dx.append(_dx("DL", "CAO", "Nhập số dư đầu kỳ cho từng quỹ và đối soát với sao kê ngân hàng mỗi tháng, đến khi số dư hệ thống khớp sao kê.",
                      "Số dư quỹ sai thì chỉ số thanh khoản và dự báo tiền mặt đều không dùng được."))
    else:
        nx.append(_nx("TC", "TOT", f"Số dư các quỹ trên hệ thống: {_g(tq)}."))
    dx.append(_dx("TC", "TRUNG", "Lập kế hoạch thu – chi theo tuần cho 8 tuần tới và rà mỗi sáng thứ Hai.",
                  "Lãi trên sổ không trả được lương và nhà cung cấp; tiền về đúng lúc mới trả được."))
    return {"ma": "DONG_TIEN", "ten": "Dòng tiền thực tế", "icon": "💵", "bieu_do": bd, "nhan_xet": nx, "de_xuat": dx,
            "so_lieu": {"tien_vao": vao, "tien_ra": ra, "rong": vao - ra, "theo_thang": {m: cash[m] for m in mh}, "so_du_quy": tq,
                        "so_quy_am": len(am_q)}}


def _muc_cong_no(D) -> dict:
    tuoi, dem, q = D["tuoi"], D["dem_cn"], D["q"]
    nx, dx, bd = [], [], []
    thu, tra = sum(tuoi["PHAI_THU"].values()), sum(tuoi["PHAI_TRA"].values())
    qh = lambda d: sum(v for k, v in d.items() if k.startswith("QH_"))
    thu_qh, tra_qh = qh(tuoi["PHAI_THU"]), qh(tuoi["PHAI_TRA"])
    bd.append({"loai": "cot", "tieu_de": "Tuổi nợ: phải thu khách hàng và phải trả nhà cung cấp", "nhan": [n for _, n in TUOI_NO],
               "chuoi": [{"ten": "Phải thu", "mau": MAU_THU, "gt": [tuoi["PHAI_THU"][k] for k, _ in TUOI_NO]},
                         {"ten": "Phải trả", "mau": MAU_CHI, "gt": [tuoi["PHAI_TRA"][k] for k, _ in TUOI_NO]}]})
    tuan = D["tuan"]
    bd.append({"loai": "cot", "tieu_de": "8 tuần tới: tiền phải thu đến hạn và phải trả đến hạn (khoản quá hạn dồn vào tuần 1)",
               "nhan": [f"{w['tu'].day:02d}/{w['tu'].month:02d}" for w in tuan],
               "chuoi": [{"ten": "Thu đến hạn", "mau": MAU_THU, "gt": [w["thu"] for w in tuan]},
                         {"ten": "Chi đến hạn", "mau": MAU_CHI, "gt": [w["chi"] for w in tuan]}]})
    top = D["top_no_kh"]
    if top:
        bd.append({"loai": "thanh", "tieu_de": "Khách hàng còn nợ nhiều nhất", "mau": MAU_THU,
                   "dong": [{"nhan": n, "gt": v, "phu": _p(_pt(v, thu))} for n, v in top[:8]]})
    nx.append(_nx("TC", "TOT", f"Còn phải thu {_g(thu)} ({dem['PHAI_THU']['so']} khoản), còn phải trả {_g(tra)} ({dem['PHAI_TRA']['so']} khoản). "
                               f"Chênh lệch phải thu trừ phải trả là {_g(thu - tra)}."))
    if thu > 0:
        tl = _pt(thu_qh, thu)
        muc = "CANH_BAO" if tl >= 30 else "LUU_Y" if tl >= 10 else "TOT"
        nx.append(_nx("TC", muc, f"Phải thu quá hạn {_g(thu_qh)}, bằng {_p(tl)} tổng phải thu"
                                 + (f"; riêng quá hạn trên 90 ngày là {_g(tuoi['PHAI_THU']['QH_90P'])}." if tuoi["PHAI_THU"]["QH_90P"] > 0
                                    else "; chưa có khoản nào quá hạn trên 90 ngày.")))
        if muc != "TOT" and top:
            dx.append(_dx("BH", "CAO" if muc == "CANH_BAO" else "TRUNG",
                          f"Phân công người gọi thu nợ theo danh sách khách nợ lớn nhất, bắt đầu từ {top[0][0]} ({_g(top[0][1])}); chốt ngày trả cụ thể và ghi vào hệ thống.",
                          "Nợ càng già càng khó thu; khoản trên 90 ngày cần CEO vào cuộc."))
    if tra > 0 and tra_qh > 0:
        nx.append(_nx("QT", "LUU_Y" if _pt(tra_qh, tra) < 30 else "CANH_BAO",
                      f"Phải trả nhà cung cấp quá hạn {_g(tra_qh)}, bằng {_p(_pt(tra_qh, tra))} tổng phải trả. Trả chậm kéo dài ảnh hưởng uy tín và giá mua."))
        dx.append(_dx("TC", "TRUNG", "Xếp lịch trả nhà cung cấp theo mức quan trọng với tiến độ đơn hàng, thương lượng gia hạn bằng văn bản với các khoản chưa trả kịp.", ""))
    dso = round(thu / (D["hd_90"] / 90), 0) if D["hd_90"] > 0 else None
    dpo = round(tra / (D["po_90"] / 90), 0) if D["po_90"] > 0 else None
    if dso is not None and dpo is not None:
        muc = "CANH_BAO" if dso - dpo > 30 else "LUU_Y" if dso > dpo else "TOT"
        nx.append(_nx("TC", muc, f"Kỳ thu tiền bình quân khoảng {dso:.0f} ngày, kỳ trả tiền bình quân khoảng {dpo:.0f} ngày (tính trên 90 ngày gần nhất). "
                                 + ("Công ty đang trả nhà cung cấp nhanh hơn thu của khách, tức đang ứng vốn cho khách." if dso > dpo
                                    else "Hai kỳ đang cân bằng." if dso == dpo
                                    else "Công ty thu của khách nhanh hơn trả nhà cung cấp, vốn lưu động đang thuận lợi.")))
        if dso > dpo:
            dx.append(_dx("TC", "CAO" if muc == "CANH_BAO" else "TRUNG",
                          "Rút ngắn khoảng trống vốn: đơn mới thu cọc 30–50% khi ký, xuất hóa đơn ngay khi giao, và đàm phán nhà cung cấp trả sau khi khách thanh toán.",
                          f"Mỗi ngày rút ngắn kỳ thu tiền giải phóng khoảng {_g(D['hd_90'] / 90)} tiền mặt."))
    kh_thu, kh_tra = dem["PHAI_THU"]["khong_han"], dem["PHAI_TRA"]["khong_han"]
    if kh_thu or kh_tra:
        nx.append(_nx("DL", "LUU_Y", f"{kh_thu} khoản phải thu ({_g(tuoi['PHAI_THU']['KHONG_HAN'])}) và {kh_tra} khoản phải trả ({_g(tuoi['PHAI_TRA']['KHONG_HAN'])}) "
                                      "chưa đặt hạn thanh toán, nên không vào được lịch thu chi theo tuần."))
        dx.append(_dx("DL", "TRUNG", "Bổ sung hạn thanh toán cho các khoản công nợ chưa có hạn, lấy theo điều khoản hợp đồng hoặc hóa đơn.",
                      "Không có hạn thì hệ thống không nhắc nợ và không dự báo được tuần nào thiếu tiền."))
    lk, s, am = [], 0.0, None
    for i, w in enumerate(tuan):
        s += w["thu"] - w["chi"]
        lk.append(s)
        if s < 0 and am is None:
            am = i
    if am is not None:
        nx.append(_nx("TC", "CANH_BAO", f"Theo các khoản đã có hạn, từ tuần bắt đầu {tuan[am]['tu'].day:02d}/{tuan[am]['tu'].month:02d} tiền phải trả lũy kế vượt tiền phải thu lũy kế "
                                         f"(thiếu {_g(-lk[am])}), chưa tính lương và chi cố định."))
        dx.append(_dx("TC", "CAO", "Ưu tiên thu các khoản đến hạn trước tuần thiếu hụt và giãn các khoản chi chưa gấp; chuẩn bị hạn mức tín dụng ngắn hạn dự phòng.", ""))
    if q["tam_ung"] > 0:
        nx.append(_nx("QT", "LUU_Y", f"Đã tạm ứng cho nhà cung cấp {_g(q['tam_ung'])} ở {q['tam_ung_po']} PO chưa nhận hàng. Đây là tiền đã ra nhưng chưa thành hàng hay chi phí."))
    if q["lenh_cho"]:
        nx.append(_nx("QT", "TOT", f"Đang có {q['lenh_cho']} lệnh chi chờ duyệt, tổng {_g(q['lenh_cho_tien'])}."))
    return {"ma": "CONG_NO", "ten": "Quản lý dòng tiền: công nợ và vốn lưu động", "icon": "⏳", "bieu_do": bd, "nhan_xet": nx, "de_xuat": dx,
            "so_lieu": {"phai_thu": thu, "phai_thu_qua_han": thu_qh, "phai_tra": tra, "phai_tra_qua_han": tra_qh,
                        "tuoi_no_phai_thu": tuoi["PHAI_THU"], "tuoi_no_phai_tra": tuoi["PHAI_TRA"], "ky_thu_tien_ngay": dso, "ky_tra_tien_ngay": dpo,
                        "top_khach_no": top[:5], "top_ncc_phai_tra": D["top_no_ncc"][:5], "tam_ung_ncc": q["tam_ung"]}}


def _muc_quan_tri(D) -> dict:
    q, po, dem, ns = D["q"], D["po_nam"], D["dem_cn"], D["ns"]
    nx, dx = [], []
    chi_so = []

    def them(nhan, tu, mau, ghi=""):
        if mau:
            chi_so.append({"nhan": nhan, "gt": _pt(tu, mau), "phu": f"{tu}/{mau}" + (f" · {ghi}" if ghi else "")})

    them("PO gắn mã đơn bán", po["co_ma"], po["tong"])
    them("PO đã duyệt có số hóa đơn đầu vào", po["co_hd"], po["da_duyet"])
    nhan_dt = f"Đơn bán mới sau {D['ngay_dt']} có dự toán"
    them(nhan_dt, q["don_co_dt"], q["don_xet_dt"])
    them("Phải thu đã đặt hạn thanh toán", dem["PHAI_THU"]["so"] - dem["PHAI_THU"]["khong_han"], dem["PHAI_THU"]["so"])
    them("Phải trả đã đặt hạn thanh toán", dem["PHAI_TRA"]["so"] - dem["PHAI_TRA"]["khong_han"], dem["PHAI_TRA"]["so"])
    them("Hóa đơn bán đã ghi nhận gửi khách", q["hd_ban_da_gui"], q["hd_ban"])
    them("Khách hàng có người phụ trách", q["kh_co_phu_trach"], q["kh"])
    so_th = int(ns.get("so_thang_luong") or 0)
    them("Tháng có bảng lương đã duyệt xong", so_th - int(ns.get("so_thang_cho_duyet") or 0), so_th)
    chi_so.sort(key=lambda x: x["gt"])
    bd = [{"loai": "thanh", "tieu_de": "Mức tuân thủ quy trình và độ đầy đủ dữ liệu", "don_vi": "%", "max": 100, "mau": MAU_BA, "dong": chi_so}]
    yeu = [c for c in chi_so if c["gt"] < 60]
    tot = [c for c in chi_so if c["gt"] >= 90]
    if tot:
        nx.append(_nx("QT", "TOT", "Làm tốt: " + "; ".join(f"{c['nhan']} {_p(c['gt'])}" for c in tot) + "."))
    if yeu:
        nx.append(_nx("QT", "CANH_BAO", "Cần siết: " + "; ".join(f"{c['nhan']} {_p(c['gt'])}" for c in yeu) + "."))
    tb = [c for c in chi_so if 60 <= c["gt"] < 90]
    if tb:
        nx.append(_nx("QT", "LUU_Y", "Ở mức trung bình: " + "; ".join(f"{c['nhan']} {_p(c['gt'])}" for c in tb) + "."))
    ten = {c["nhan"]: c for c in chi_so}
    c = ten.get(nhan_dt)
    if c and c["gt"] < 80:
        dx.append(_dx("QT", "CAO", "Giữ đúng quy định: đơn TM · DA · DV mới phải có dự toán trước khi mua hàng; đơn chưa có dự toán thì chưa duyệt PO.",
                      f"Mới {_p(c['gt'])} đơn mới có dự toán ({c['phu']}): không có dự toán thì không biết đơn lãi hay lỗ cho tới khi làm xong."))
    c = ten.get("PO đã duyệt có số hóa đơn đầu vào")
    if c and c["gt"] < 80:
        dx.append(_dx("DL", "TRUNG", "Mỗi tuần kế toán rà danh sách PO đã duyệt chưa có hóa đơn đầu vào và đòi nhà cung cấp xuất hóa đơn.",
                      "Thiếu hóa đơn đầu vào là mất khấu trừ VAT và chi phí không được tính khi quyết toán thuế."))
    c = ten.get("Hóa đơn bán đã ghi nhận gửi khách")
    if c and c["gt"] < 80:
        dx.append(_dx("BH", "TRUNG", "Gửi hóa đơn cho khách ngay khi xuất và bấm ghi nhận đã gửi; hóa đơn chưa gửi thì khách chưa có căn cứ thanh toán.", ""))
    c = ten.get("Khách hàng có người phụ trách")
    if c and c["gt"] < 80:
        dx.append(_dx("BH", "THAP", "Gán người phụ trách cho từng khách hàng để có người chịu trách nhiệm chăm sóc và thu nợ.", ""))
    if q["don_chua_hd"]:
        nx.append(_nx("DL", "LUU_Y", f"{q['don_chua_hd']} đơn bán đã ở trạng thái xuất hóa đơn hoặc hoàn thành nhưng chưa có hóa đơn bán bên Kế toán, doanh thu chưa được ghi nhận."))
        dx.append(_dx("DL", "TRUNG", "Lập hóa đơn cho các đơn đã hoàn thành ở mục Kế toán, hoặc đánh dấu bỏ qua nếu đơn không xuất hóa đơn.", ""))
    if po["cho_duyet"]:
        nx.append(_nx("QT", "TOT", f"Đang có {po['cho_duyet']} PO chờ duyệt."))
    if q["ngoai_lenh"]:
        nx.append(_nx("QT", "LUU_Y", f"90 ngày qua có {q['ngoai_lenh']} lần ghi «đã trả nhà cung cấp» không qua Duyệt chi Ngân hàng, tổng {_g(q['ngoai_lenh_tien'])}."))
        dx.append(_dx("QT", "TRUNG", "Mọi khoản trả nhà cung cấp đi qua Duyệt chi Ngân hàng; chỉ sửa trực tiếp khi chữa sai và phải ghi lý do.",
                      "Chi ngoài quy trình duyệt là điểm hở kiểm soát lớn nhất về tiền."))
    else:
        nx.append(_nx("QT", "TOT", "90 ngày qua không có khoản trả nhà cung cấp nào ghi ngoài quy trình Duyệt chi Ngân hàng."))
    dx.append(_dx("QT", "THAP", "Mỗi tháng mở tab này một lần cùng kế toán trưởng và trưởng phòng: chốt 3 việc ưu tiên, giao người và hạn.",
                  "Số liệu chỉ có giá trị khi dẫn tới quyết định và có người chịu trách nhiệm."))
    return {"ma": "QUAN_TRI", "ten": "Phương thức quản lý: kỷ luật quy trình và dữ liệu", "icon": "🧭", "bieu_do": bd, "nhan_xet": nx, "de_xuat": dx,
            "so_lieu": {"chi_so_tuan_thu_pct": {c["nhan"]: c["gt"] for c in chi_so}, "po_cho_duyet": po["cho_duyet"],
                        "lenh_chi_cho_duyet": q["lenh_cho"], "chi_ngoai_lenh_90_ngay": q["ngoai_lenh"], "don_chua_xuat_hoa_don": q["don_chua_hd"]}}


# ====================================================================================================
#  TỔNG HỢP
# ====================================================================================================
def phan_tich(db: Session, hom_nay: date) -> dict:
    D = _thu_thap(db, hom_nay)
    muc = []
    for fn, ma, ten in ((_muc_ban_hang, "BAN_HANG", "Bán hàng và khách hàng"), (_muc_nhan_su, "NHAN_SU", "Tiền lương và nhân sự"),
                        (_muc_chi_phi, "CHI_PHI", "Cơ cấu chi phí và mua hàng"), (_muc_dong_tien, "DONG_TIEN", "Dòng tiền thực tế"),
                        (_muc_cong_no, "CONG_NO", "Quản lý dòng tiền: công nợ và vốn lưu động"),
                        (_muc_quan_tri, "QUAN_TRI", "Phương thức quản lý: kỷ luật quy trình và dữ liệu")):
        try:
            muc.append(fn(D))
        except Exception as e:                         # một đề mục lỗi không làm hỏng cả tab
            muc.append({"ma": ma, "ten": ten, "icon": "⚠", "bieu_do": [], "nhan_xet": [], "de_xuat": [], "so_lieu": {},
                        "loi": f"{type(e).__name__}: {str(e)[:200]}"})
    t, mh = D["t"], D["mh"]
    thu, tra = sum(D["tuoi"]["PHAI_THU"].values()), sum(D["tuoi"]["PHAI_TRA"].values())
    vao, ra = sum(D["cash"][m]["vao"] for m in mh), sum(D["cash"][m]["ra"] for m in mh)
    kpi = [{"k": "Doanh thu hóa đơn trong kỳ", "v": sum(D["hd_tong"][m] for m in mh), "sub": f"{D['so_hd']} hóa đơn bán, gồm VAT"},
           {"k": "Lãi/Lỗ lũy kế", "v": _f(t.get("lai_lo")), "sub": f"biên lãi gộp {_p(_pt(t.get('lai_gop'), t.get('doanh_thu')))}", "mau_theo_dau": True},
           {"k": "Chi phí nhân sự lũy kế", "v": _f(t.get("chi_nhan_su")), "sub": f"{int((D['ns'].get('so_thang_luong') or 0))} tháng có bảng lương"},
           {"k": "Dòng tiền ròng trong kỳ", "v": vao - ra, "sub": f"vào {_g(vao)} · ra {_g(ra)}", "mau_theo_dau": True},
           {"k": "Còn phải thu", "v": thu, "sub": f"quá hạn {_g(sum(v for k, v in D['tuoi']['PHAI_THU'].items() if k.startswith('QH_')))}"},
           {"k": "Còn phải trả", "v": tra, "sub": f"quá hạn {_g(sum(v for k, v in D['tuoi']['PHAI_TRA'].items() if k.startswith('QH_')))}"}]
    dem = {"CANH_BAO": 0, "LUU_Y": 0, "TOT": 0}
    uu = []
    thu_tu = {"CAO": 0, "TRUNG": 1, "THAP": 2}
    for m in muc:
        for n in m["nhan_xet"]:
            dem[n["muc"]] = dem.get(n["muc"], 0) + 1
        for d in m["de_xuat"]:
            uu.append(dict(d, muc=m["ten"]))
    uu.sort(key=lambda d: thu_tu.get(d["uu_tien"], 9))
    return {"ngay": str(hom_nay), "tu_thang": mh[0], "den_thang": mh[-1], "kpi": kpi, "dem": dem, "muc": muc,
            "uu_tien": [d for d in uu if d["uu_tien"] == "CAO"][:8] or uu[:5]}


def goi_ai(pt: dict) -> dict:
    """Gói số liệu gọn gửi AI: chỉ số tổng hợp + nhận xét tự động — KHÔNG có lương từng người, không có số tài khoản."""
    return {"cong_ty": "Sóng Việt Water Solutions — kỹ thuật xử lý nước: thương mại thiết bị, dịch vụ vận hành / cho thuê hệ thống, dự án",
            "ngay": pt["ngay"], "ky": f"{pt['tu_thang']} → {pt['den_thang']}", "don_vi": "VND",
            "chi_so_chinh": [{"ten": k["k"], "gia_tri": round(k["v"]), "ghi_chu": k["sub"]} for k in pt["kpi"]],
            "de_muc": [{"ten": m["ten"], "so_lieu": m.get("so_lieu") or {},
                        "nhan_xet_tu_dong": [n["nd"] for n in m["nhan_xet"] if n["muc"] != "TOT"][:8]} for m in pt["muc"]]}
