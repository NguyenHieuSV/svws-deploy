"""
💰 Cột «Đã thu từ khách» ở Kế toán › Lãi/lỗ theo mã (01/11/2026): chi_phi_ma tách nguồn ĐÃ THU —
đã thu trên công nợ khách · cọc ghi trên đơn (chỉ khi CHƯA có công nợ) · phiếu tạm ứng đã duyệt chưa cấn trừ.
Quy tắc cũ giữ nguyên: cọc trên đơn và phiếu tạm ứng là hai đường ghi CÙNG một khoản tiền → lấy số lớn hơn, không cộng dồn.
"""
from decimal import Decimal

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import models as m
from app.lai_lo_ma import chi_phi_ma


def _session():
    eng = create_engine("sqlite://")
    for t in (m.DonHang, m.DonHangCt, m.DonMua, m.DonMuaCt, m.CongNo, m.HoaDon, m.ChiPhiVanHanh, m.PhieuThuChi):
        t.__table__.create(eng)
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]
    return s


def _dh(s, so, coc=0):
    dh = m.DonHang(so=so, khach_hang_id=1, tong_tien=Decimal(100_000_000), tien_thue=Decimal(8_000_000),
                   thanh_toan_coc=Decimal(coc))
    s.add(dh)
    s.flush()
    return dh


def _tam_ung(s, dh, tien, can=0, tt="DA_DUYET"):
    s.add(m.PhieuThuChi(loai="THU", quy_id=1, so_tien=Decimal(tien), da_can_tru=Decimal(can), don_hang_id=dh.id,
                        la_tam_ung=True, trang_thai=tt))


def test_coc_tren_don_khi_chua_co_cong_no():
    s = _session()
    dh = _dh(s, "DA-A-0126-WAF", coc=60_000_000)
    s.commit()
    cp = chi_phi_ma(s, dh)
    assert cp["da_thu"] == 60e6 and cp["da_thu_coc_don"] == 60e6 and cp["da_thu_tam_ung"] == 0 and cp["da_thu_cong_no"] == 0
    assert cp["con_phai_thu"] == 48e6                                   # 108 tr gồm VAT − 60 tr cọc


def test_phieu_tam_ung_lon_hon_coc_thi_tinh_phieu():
    s = _session()
    dh = _dh(s, "DA-B-0126", coc=60_000_000)
    _tam_ung(s, dh, 70_000_000)
    s.commit()
    cp = chi_phi_ma(s, dh)
    assert cp["da_thu"] == 70e6 and cp["da_thu_tam_ung"] == 70e6 and cp["da_thu_coc_don"] == 0   # cùng khoản tiền, lấy số lớn


def test_co_cong_no_thi_coc_khong_tinh_rieng():
    s = _session()
    dh = _dh(s, "DA-C-0126", coc=60_000_000)
    s.add(m.CongNo(loai="PHAI_THU", don_hang_id=dh.id, khach_hang_id=1, so_tien=Decimal(108_000_000),
                   da_thanh_toan=Decimal(30_000_000)))
    _tam_ung(s, dh, 10_000_000, can=4_000_000)
    s.commit()
    cp = chi_phi_ma(s, dh)
    assert cp["da_thu_cong_no"] == 30e6 and cp["da_thu_tam_ung"] == 6e6 and cp["da_thu_coc_don"] == 0
    assert cp["da_thu"] == 36e6 and cp["con_phai_thu"] == 72e6


def test_phieu_chua_duyet_khong_tinh():
    s = _session()
    dh = _dh(s, "DA-D-0126")
    _tam_ung(s, dh, 50_000_000, tt="CHO_DUYET")
    s.commit()
    cp = chi_phi_ma(s, dh)
    assert cp["da_thu"] == 0 and cp["da_thu_tam_ung"] == 0 and cp["da_thu_coc_don"] == 0 and cp["con_phai_thu"] == 108e6
