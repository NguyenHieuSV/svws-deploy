"""
Test H1 — đăng ký kỹ sư / kỹ thuật viên nhà máy (T102 · PR-2). Chạy trên SQLite và Postgres.
Không gửi email thật: send_otp được thay bằng hàm giả khi cần thử luồng OTP.
"""
import uuid

import pytest
from sqlmodel import Session, select

from tests.test_training_dong_y import KEY, _phone, _sv, c  # noqa: F401  (c là fixture)
import training
from training import TrnConsent, TrnEngineer, TrnResult
from training_tinh import PROVINCES, canon_province, _OLD_TO_NEW


def _ks(**kw):
    b = {"full_name": "Phạm Kỹ Sư", "phone": _phone(), "email": f"ks{uuid.uuid4().hex[:10]}@nhamay-abc.vn",
         "company": "Công ty Nước Sạch ABC", "industrial_zone": "KCN Nhơn Trạch 1", "province": "Đồng Nai",
         "job_title": "Kỹ sư vận hành", "role_group": "VAN_HANH", "password": "matkhau1", "agree_terms": True}
    b.update(kw)
    return b


def _id_of(c, email):
    return [x for x in c.get(f"/training/api/engineers?key={KEY}").json()["engineers"] if x["email"] == email][0]


# ---------------- 34 tỉnh/thành ----------------
def test_danh_sach_34_tinh_va_doi_ten_tinh_cu():
    assert len(PROVINCES) == 34 and len(set(PROVINCES)) == 34
    assert len(PROVINCES) + len(_OLD_TO_NEW) == 63            # 63 tỉnh cũ = 34 giữ/hợp nhất + 29 đã nhập
    assert all(canon_province(p) == p for p in PROVINCES)
    assert all(canon_province(old) == new and new in PROVINCES for old, new in _OLD_TO_NEW.items())
    for text, want in [("Bình Dương", "TP. Hồ Chí Minh"), ("tinh ba ria vung tau", "TP. Hồ Chí Minh"),
                       ("Thành phố Hồ Chí Minh", "TP. Hồ Chí Minh"), ("TP HCM", "TP. Hồ Chí Minh"),
                       ("Thừa Thiên Huế", "Huế"), ("hà giang", "Tuyên Quang"), ("Tỉnh Hoà Bình", "Phú Thọ"),
                       ("Quảng Nam", "Đà Nẵng"), ("Long An", "Tây Ninh"), (" KIÊN GIANG ", "An Giang")]:
        assert canon_province(text) == want, text
    assert canon_province("Atlantis") is None and canon_province("") is None


# ---------------- đăng ký / kích hoạt ----------------
def test_email_doanh_nghiep_co_smtp_nhan_otp_va_dang_nhap(c, monkeypatch):
    sent = {}
    monkeypatch.setattr(training, "OTP_MODE", True)
    monkeypatch.setattr(training, "send_otp", lambda e, code: sent.update({e: code}) or True)
    b = _ks()
    r = c.post("/training/api/engineer/register", json=b)
    assert r.status_code == 200 and r.json()["mode"] == "otp"
    assert c.post("/training/api/engineer/verify", json={"email": b["email"], "otp": "000000x"}).status_code == 422
    assert c.post("/training/api/engineer/verify", json={"email": b["email"], "otp": sent[b["email"]]}).status_code == 200
    lg = c.post("/training/api/engineer/login", json={"id": b["phone"], "password": b["password"]})
    assert lg.status_code == 200, lg.text
    code = lg.json()["eng_code"]
    assert code.startswith("ENG-") and lg.json()["need_consent"] is False
    # làm test xong thấy điểm trong admin với mã ENG-xxxx
    assert c.post("/training/api/results", json={"token": lg.json()["token"], "code": "NT05", "pct": 88, "kq": "ĐẠT"}).json() == {"ok": True}
    summ = c.get(f"/training/api/summary?key={KEY}").json()
    assert any(x["emp_code"] == code and x["best_pct"] == 88 for x in summ["summary"])
    assert summ["engineers_active"] >= 1


def test_email_mien_phi_cho_duyet_va_admin_thay_nhan(c, monkeypatch):
    monkeypatch.setattr(training, "OTP_MODE", True)
    monkeypatch.setattr(training, "send_otp", lambda e, code: pytest.fail("không được gửi OTP cho email miễn phí"))
    b = _ks(email=f"ks{uuid.uuid4().hex[:8]}@gmail.com")
    r = c.post("/training/api/engineer/register", json=b)
    assert r.status_code == 200 and r.json()["mode"] == "manual"
    x = _id_of(c, b["email"])
    assert x["status"] == "pending" and x["work_email"] is False
    assert c.post("/training/api/engineer/login", json={"id": b["email"], "password": b["password"]}).status_code == 403
    assert c.post("/training/api/engineers/action", json={"key": KEY, "id": x["id"], "action": "approve"}).status_code == 200
    assert c.post("/training/api/engineer/login", json={"id": b["email"], "password": b["password"]}).status_code == 200


def test_chua_co_smtp_thi_email_doanh_nghiep_cung_cho_duyet(c):
    b = _ks()                                   # OTP_MODE=False trong fixture
    assert c.post("/training/api/engineer/register", json=b).json()["mode"] == "manual"
    assert _id_of(c, b["email"])["work_email"] is True


def test_danh_sach_email_mien_phi_mac_dinh():
    for d in ("gmail.com", "yahoo.com.vn", "outlook.com", "icloud.com",
              "qq.com", "163.com", "126.com", "naver.com", "daum.net", "hanmail.net"):
        assert d in training.FREE_EMAIL_DOMAINS, d
    assert len(training.FREE_EMAIL_DOMAINS) == 23


def test_danh_sach_email_mien_phi_doc_tu_bien_moi_truong(c, monkeypatch):
    monkeypatch.setattr(training, "FREE_EMAIL_DOMAINS", {"congty-rieng.vn"})
    b = _ks(email=f"a{uuid.uuid4().hex[:8]}@congty-rieng.vn")
    c.post("/training/api/engineer/register", json=b)
    assert _id_of(c, b["email"])["work_email"] is False


def test_trung_email_hoac_sdt_voi_bat_ky_bang_tai_khoan_nao(c):
    sv = _sv()
    assert c.post("/training/api/student/register", json=sv).status_code == 200
    for kw in ({"email": sv["email"]}, {"phone": sv["phone"]}):
        r = c.post("/training/api/engineer/register", json=_ks(**kw))
        assert r.status_code == 409 and "đã đăng ký" in r.json()["detail"]
    b = _ks()
    assert c.post("/training/api/engineer/register", json=b).status_code == 200
    assert c.post("/training/api/engineer/register", json=_ks(phone=b["phone"])).status_code == 409


def test_tinh_cu_tu_doi_ten_tinh_la_bao_loi_thieu_dong_y(c):
    b = _ks(province="Bình Dương")
    assert c.post("/training/api/engineer/register", json=b).status_code == 200
    assert _id_of(c, b["email"])["province"] == "TP. Hồ Chí Minh"
    assert c.post("/training/api/engineer/register", json=_ks(province="Atlantis")).status_code == 422
    assert c.post("/training/api/engineer/register", json=_ks(province="")).status_code == 422
    assert c.post("/training/api/engineer/register", json=_ks(company=" ")).status_code == 422
    assert c.post("/training/api/engineer/register", json=_ks(agree_terms=False)).status_code == 422


def test_dong_y_chia_se_voi_cong_ty(c):
    b = _ks(share_company=True, marketing=False)
    c.post("/training/api/engineer/register", json=b)
    x = _id_of(c, b["email"])
    c.post("/training/api/engineers/action", json={"key": KEY, "id": x["id"], "action": "approve"})
    tok = c.post("/training/api/engineer/login", json={"id": b["email"], "password": b["password"]}).json()["token"]
    me = c.get(f"/training/api/me?token={tok}").json()
    assert me["account_type"] == "engineer" and me["share_company"] is True and me["marketing"] is False
    c.post("/training/api/me/consent", json={"token": tok, "terms": True, "share_company": False})
    assert c.get(f"/training/api/me?token={tok}").json()["share_company"] is False
    with Session(c.engine) as s:
        rows = s.exec(select(TrnConsent).where(TrnConsent.account_type == "engineer", TrnConsent.account_id == x["id"])
                      .order_by(TrnConsent.id)).all()
    assert [(r.purpose, r.granted) for r in rows] == [
        ("terms", True), ("marketing", False), ("share_company", True), ("share_company", False)]


def test_admin_loc_theo_cong_ty_va_kcn(c):
    tag = uuid.uuid4().hex[:6]
    a = _ks(company=f"Nhà máy Giấy {tag}", industrial_zone="KCN Hiệp Phước")
    b = _ks(company=f"Nhà máy Bia {tag}", industrial_zone="KCN Nhơn Trạch 2")
    for x in (a, b):
        c.post("/training/api/engineer/register", json=x)
    by_co = c.get(f"/training/api/engineers?key={KEY}&company=giấy {tag}").json()["engineers"]
    assert [x["email"] for x in by_co] == [a["email"]]
    by_kz = c.get(f"/training/api/engineers?key={KEY}&company={tag}&zone=nhơn trạch").json()["engineers"]
    assert [x["email"] for x in by_kz] == [b["email"]]
    assert by_kz[0]["role_group"] == "Vận hành"
    assert c.get("/training/api/engineers?key=sai").status_code == 403


def test_xoa_tai_khoan_ky_su(c):
    b = _ks()
    c.post("/training/api/engineer/register", json=b)
    x = _id_of(c, b["email"])
    c.post("/training/api/engineers/action", json={"key": KEY, "id": x["id"], "action": "approve"})
    lg = c.post("/training/api/engineer/login", json={"id": b["email"], "password": b["password"]}).json()
    c.post("/training/api/results", json={"token": lg["token"], "code": "KT02", "pct": 81})
    assert c.post("/training/api/me/delete", json={"token": lg["token"], "password": b["password"]}).status_code == 200
    with Session(c.engine) as s:
        assert s.get(TrnEngineer, x["id"]) is None
        anon = s.exec(select(TrnResult).where(TrnResult.emp_code == training._anon_code(lg["eng_code"]))).all()
        assert [r.name for r in anon] == ["Đã xóa"]


def test_ma_ky_su_tang_dan(c):
    codes = []
    for _ in range(2):
        b = _ks(); c.post("/training/api/engineer/register", json=b)
        codes.append(_id_of(c, b["email"])["eng_code"])
    assert int(codes[1][4:]) == int(codes[0][4:]) + 1


def test_trang_dang_ky_co_tab_ky_su_va_34_tinh(c):
    html = c.get("/training/register").text
    assert "id=tK" in html and "id=k_pv" in html and "<!--PROVINCE_OPTIONS-->" not in html
    assert html.count('<option value="') == 34 + len(training.ROLE_GROUPS) + 2   # + 2 dòng "— chọn —"
    sel = html[html.index("<select id=k_pv>"):]
    assert sel[:sel.index("</select>")].count('<option value="') == 34 + 1
    assert "<input id=k_pv" not in html                   # tỉnh/thành không gõ tự do
