"""
📋 Báo cáo CEO bản tuần (04/11/2026, app/bao_cao_ceo.py): kỳ tuần ISO + tuần trước, tiền vào/ra theo thanh toán công nợ,
đơn chốt trong kỳ (bỏ đầu tư + mã nội bộ), ba tầng ghép từ số liệu từng phần, tin Chat, nơi gửi.
tuan(db) trên SQLite thiếu bảng vẫn trả đủ cấu trúc — phần hỏng ghi vào `loi`, không ném lỗi.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import bao_cao_ceo as bc
from app import models as m

HOM_NAY = date(2026, 11, 4)          # thứ Tư


def test_ky_tuan():
    k = bc.ky_tuan(HOM_NAY)
    assert (k["tu"], k["den"], k["nhan"]) == (date(2026, 11, 2), date(2026, 11, 8), "Tuần 45/2026")
    assert (k["truoc_tu"], k["truoc_den"], k["truoc_nhan"]) == (date(2026, 10, 26), date(2026, 11, 1), "Tuần 44/2026")
    assert k["den_hieu_luc"] == HOM_NAY and k["hien_tai"] and k["lui"] == 0
    k1 = bc.ky_tuan(HOM_NAY, 1)
    assert k1["tu"] == date(2026, 10, 26) and k1["den_hieu_luc"] == date(2026, 11, 1) and not k1["hien_tai"] and k1["lui"] == 1
    assert bc.ky_tuan(date(2026, 11, 2))["tu"] == date(2026, 11, 2)            # thứ Hai → tuần của chính nó
    assert bc.ky_tuan(HOM_NAY, -3)["lui"] == 0                                   # lùi âm → tuần này


def test_tr():
    assert bc._tr(1_234_567_890) == "1,23 tỷ" and bc._tr(450_000_000) == "450 tr" and bc._tr(12_500) == "12.500 đ"
    assert bc._tr(-2_000_000_000) == "-2,00 tỷ" and bc._tr(None) == "0 đ"


def _db():
    e = create_engine("sqlite://")
    for t in (m.CongNo, m.ThanhToan, m.DonHang, m.LaiLoRecord):
        t.__table__.create(e)
    return sessionmaker(e)()


def test_thu_chi_va_don_trong_ky():
    s = _db()
    s.add(m.CongNo(id=1, loai="PHAI_THU", so_tien=Decimal(100e6), da_thanh_toan=Decimal(30e6)))
    s.add(m.CongNo(id=2, loai="PHAI_TRA", so_tien=Decimal(50e6), da_thanh_toan=Decimal(20e6)))
    s.add_all([m.ThanhToan(id=1, cong_no_id=1, so_tien=Decimal(20e6), ngay=date(2026, 11, 3)),
               m.ThanhToan(id=2, cong_no_id=1, so_tien=Decimal(10e6), ngay=date(2026, 10, 28)),      # tuần trước
               m.ThanhToan(id=3, cong_no_id=2, so_tien=Decimal(20e6), ngay=date(2026, 11, 2))])
    s.add(m.DonHang(id=1, so="DA-A-1126", khach_hang_id=1, ngay=date(2026, 11, 3), tong_tien=Decimal(80e6)))
    s.add(m.DonHang(id=2, so="OP-SV-1126", khach_hang_id=1, ngay=date(2026, 11, 3), tong_tien=Decimal(5e6)))       # nội bộ → bỏ
    s.add(m.DonHang(id=3, so="DV-X-1026", khach_hang_id=1, ngay=date(2026, 10, 30), tong_tien=Decimal(40e6)))      # tuần trước
    s.add(m.DonHang(id=4, so="DV-COA-NT-2024", khach_hang_id=1, ngay=date(2026, 11, 2), tong_tien=Decimal(9e6),
                    loai_don="DAU_TU"))                                                                          # đầu tư → bỏ
    s.commit()
    k = bc.ky_tuan(HOM_NAY)
    assert bc._thu_chi(s, k["tu"], k["den"]) == (20e6, 20e6)
    assert bc._thu_chi(s, k["truoc_tu"], k["truoc_den"]) == (10e6, 0)
    assert bc._don_trong_ky(s, k["tu"], k["den"]) == (1, 80e6)
    assert bc._don_trong_ky(s, k["truoc_tu"], k["truoc_den"]) == (1, 40e6)


def test_tuan_sqlite_thieu_bang_van_ra_cau_truc():
    r = bc.tuan(_db(), HOM_NAY)
    assert r["ky"]["nhan"] == "Tuần 45/2026" and r["ky"]["tu"] == "2026-11-02" and r["ky"]["hom_nay"] == "2026-11-04"
    assert len(r["chi_so"]) == 12 and [x["ma"] for x in r["chi_so"]][:3] == ["tien_hien_co", "tien_vao", "tien_ra"]
    assert [k["ma"] for k in r["khoi"]] == ["thuong_mai", "cung_ung", "dich_vu", "tai_chinh", "noi_bo", "tuan_thu"]
    assert isinstance(r["quyet"], list) and r["loi"]                                 # thiếu bảng → ghi lỗi, không ném
    nd = bc.noi_dung_tuan(r)
    assert nd.startswith("📋 *BÁO CÁO TUẦN CEO* — Tuần 45/2026 (02/11 → 08/11, số liệu đến 04/11/2026)")
    assert "phần chưa tính được" in nd and nd.endswith("in PDF")


def _d_mau():
    return {"tien": {"ngan_hang": 1.2e9, "tien_mat": 50e6, "hien_co": 1.25e9, "vao": 300e6, "ra": 200e6, "vao_truoc": 250e6,
                     "ra_truoc": 400e6, "lenh_cho_chi": 100e6, "tra_30": 150e6, "phai_chi_30": 250e6, "thu_30": 500e6, "n_thu_30": 4},
            "lai": {"don_n": 3, "don_gt": 900e6, "don_n_truoc": 1, "don_gt_truoc": 100e6, "lai_gop": 2e9, "lai_lo": 1.5e9,
                    "lai_lo_truoc": 1.4e9, "bien": 23.5, "chi_nhan_su": 800e6, "so_lo": 2, "lo_tong": 120e6,
                    "lo_top": [{"nhom": "TM-A-0926", "lo": 100e6}], "so_bien_thap": 1, "so_chua_dt": 3, "nguong": 15.0,
                    "gia_uoc": ["DA-X-1026"], "ns_thang": "2026-10", "ns_thang_tong": 90e6},
            "no": {"phai_thu": 3e9, "phai_tra": 1e9, "qh_n": 5, "qh_tong": 700e6, "qh_60_n": 2, "qh_60_tong": 400e6,
                   "qh_top": [{"khach": "Coats", "tong": 300e6}], "tra_qh_n": 1, "tra_qh_tong": 50e6,
                   "dchd_n": 19, "dchd_con": 7.6e9, "dchd_qn_n": 12, "dchd_qn_tong": 13.4e9, "dchd_nguong": 30},
            "van_hanh": {"don_dang_n": 20, "don_dang_gt": 10e9, "du_an_n": 8, "du_an_gt": 9e9, "po_cho_n": 2, "po_cho_gt": 30e6,
                         "po_moi_n": 4, "po_moi_gt": 200e6, "po_moi_n_truoc": 2, "po_moi_gt_truoc": 50e6, "po_cho_nhan_n": 25,
                         "po_qh_n": 20, "po_qh_lau": 146, "tam_ung_mua": 80e6, "tam_ung_mua_n": 3, "ton_gia_tri": 500e6,
                         "ton_duoi_min": 4,
                         "treo": {"phieu_cho": 3, "phieu_cho_tong": 45e6, "lenh_cho": 2, "lenh_cho_tong": 60e6, "lenh_qua7": 1,
                                  "hd_chua_ht": 7, "hd_chua_ht_tong": 90e6, "hdc_cho": 5, "cn_thieu_hd": 0, "hd_ban_so_tam": 2},
                         "thue_n": 6, "thue_thang": 120e6, "thue_sap_het": 1, "bg_cho_duyet": 1, "bg_nhap": 4, "co_hoi_mo": 7},
            "con_nguoi": {"nv_n": 22, "nv_thu_viec": 2, "bc_phai": 40, "bc_da": 30, "bc_pct": 75, "bc_pct_truoc": 60,
                          "cham_n": 2, "cham_qua_han": 1, "cham_top": ["Nguyễn A: Lắp bơm"], "nhac_qua_han": 3, "giao_xong_tuan": 5},
            "tuan_thu": {"sao_luu_luc": "2026-11-04 02:00", "sao_luu_ok": True, "audit_n": 120, "audit_nguoi": 6,
                         "sao_ke_co": False, "sao_ke_thang": "10/2026"}}


def test_ba_tang_tu_so_lieu_mau():
    d = _d_mau()
    cs = {x["ma"]: x for x in bc.chi_so(d)}
    assert cs["tien_hien_co"]["gia_tri"] == 1.25e9 and cs["tien_hien_co"]["phu"] == "ngân hàng 1,20 tỷ · quỹ tiền mặt 50 tr"
    assert cs["tien_vao"]["ky_truoc"] == 250e6 and cs["lai_lo"]["phu"] == "lãi gộp 2,00 tỷ · biên 23,5%"
    assert cs["ma_lo"]["gia_tri"] == 2 and cs["ma_lo"]["phu"].startswith("lỗ 120 tr · 1 nhóm biên dưới 15% · 3 nhóm")
    assert cs["nhan_su"]["gia_tri"] == 75 and cs["nhan_su"]["ky_truoc"] == 60
    assert cs["nhan_su"]["mo"] == {"page": "working_time", "tab": "report"}
    q = bc.viec_can_quyet(d)
    assert [x["ten"] for x in q][:4] == ["Công nợ phải thu quá 60 ngày", "Nhóm mã đang lỗ", "Lệnh chi đã duyệt chờ ✔ Đã chi",
                                          "Phiếu thu chi chờ duyệt"]                             # Cao trước, tiền lớn trước
    assert all(x["muc"] == "Cao" for x in q[:4]) and q[2]["ghi_chu"] == "1 lệnh quá 7 ngày"
    ten = {x["ten"]: x for x in q}
    assert ten["Chưa có sao kê ngân hàng tháng 10/2026"]["muc"] == "Vừa" and not any("Sao lưu" in t for t in ten)
    assert ten["Việc giao đang chậm tiến độ"]["so"] == 2 and ten["Việc giao đang chậm tiến độ"]["ghi_chu"] == "Nguyễn A: Lắp bơm"
    assert "Khoản phải trả thiếu số hóa đơn" not in ten                                            # 0 → không liệt kê
    kh = {k["ma"]: k for k in bc.sau_khoi(d)}
    assert kh["tai_chinh"]["dong"][0] == "Tiền hiện có 1,25 tỷ (ngân hàng 1,20 tỷ · quỹ tiền mặt 50 tr)"
    assert kh["noi_bo"]["dong"][1] == "Báo cáo ngày: 30/40 lượt = 75% (tuần trước 60%)"
    assert kh["tuan_thu"]["dong"][1] == "Sao kê ngân hàng tháng 10/2026: chưa tải ⚠"
    r = {"ky": {k: (str(v) if isinstance(v, date) else v) for k, v in bc.ky_tuan(HOM_NAY).items()},
         "chi_so": bc.chi_so(d), "quyet": q, "khoi": bc.sau_khoi(d), "loi": []}
    nd = bc.noi_dung_tuan(r, "Hiếu")
    assert ("💰 *Tiền*: hiện có 1,25 tỷ · tuần này thu 300 tr (tuần trước 250 tr) · chi 200 tr (tuần trước 400 tr) · "
            "30 ngày tới phải thu 500 tr / phải chi 250 tr") in nd
    assert "👥 *Nhân sự*: báo cáo ngày 75% (tuần trước 60%) · 30/40 lượt" in nd
    assert f"✅ *Cần CEO quyết* ({len(q)} việc):" in nd
    assert "– [Cao] Công nợ phải thu quá 60 ngày: *2* · 400 tr — Coats 300 tr" in nd
    assert nd.endswith("_(gửi tay bởi Hiếu)_") and "phần chưa tính được" not in nd


def test_gui_tuan(monkeypatch):
    from app import chat_gateway
    from app.config import settings
    gui = []
    monkeypatch.setattr(chat_gateway, "gui_webhook_rieng", lambda url, nd: gui.append((url, nd)) or {"da_gui": True})
    monkeypatch.setattr(bc, "tuan", lambda db: {"ky": {"nhan": "Tuần 45/2026", "tu": "2026-11-02", "den": "2026-11-08",
                                                       "hom_nay": "2026-11-04"},
                                               "chi_so": bc.chi_so(_d_mau()), "quyet": [], "khoi": [], "loi": []})
    monkeypatch.setattr(settings, "gchat_webhook_ceo", "")
    monkeypatch.setattr(settings, "gchat_webhook_duyet_chi", "https://dc")
    kq = bc.gui_tuan(None, "TAY", "Hiếu")
    assert kq["da_gui"] and kq["nhom"] == "nhóm Duyệt chi" and kq["ky"] == "Tuần 45/2026" and gui[0][0] == "https://dc"
    assert "Không có việc nào treo" in gui[0][1] and gui[0][1].endswith("_(gửi tay bởi Hiếu)_")
    monkeypatch.setattr(settings, "gchat_webhook_ceo", "https://ceo")
    assert bc.gui_tuan(None)["nhom"] == "nhóm riêng CEO" and gui[1][0] == "https://ceo" and "gửi tay" not in gui[1][1]
    monkeypatch.setattr(settings, "gchat_webhook_ceo", "")
    monkeypatch.setattr(settings, "gchat_webhook_duyet_chi", "")
    kq = bc.gui_tuan(None)
    assert not kq["da_gui"] and "GCHAT_WEBHOOK_CEO" in kq["ly_do"] and len(gui) == 2
