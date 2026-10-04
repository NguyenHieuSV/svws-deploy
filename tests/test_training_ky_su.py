"""
Test H1 — đăng ký kỹ sư / kỹ thuật viên nhà máy (T102 · PR-2).
Chạy trên CẢ SQLite và Postgres (khi `make db-up`) như test_training_dong_y.py.
"""
import uuid

import pytest
from sqlmodel import Session, select

# nạp trước: đặt DATABASE_URL rồi mới import training; dùng lại fixture `c` (SQLite + Postgres)
from tests.test_training_dong_y import KEY, _consents, _dang_ky_duyet_dang_nhap, _phone, _sv, c  # noqa: F401
import training                                                                                 # noqa: E402
from training import TrnConsent, TrnEngineer, TrnResult, TrnStaff, TrnStudent                   # noqa: E402


def _ks(**kw):
    b = {"full_name": "Phạm Kỹ Sư", "phone": _phone(), "email": f"ks{uuid.uuid4().hex[:10]}@nhamay-abc.vn",
         "company": "Công ty TNHH Nhà Máy ABC", "industrial_zone": "KCN Nhơn Trạch 1", "province": "Đồng Nai",
         "job_title": "Trưởng ca vận hành", "role_group": "van_hanh", "password": "matkhau1", "agree_terms": True}
    b.update(kw)
    return b


def _id_ks(c, email):
    return [x for x in c.get(f"/training/api/engineers?key={KEY}").json()["engineers"] if x["email"] == email][0]


def _ks_duyet_dang_nhap(c, **kw):
    b = _ks(**kw)
    r = c.post("/training/api/engineer/register", json=b)
    assert r.status_code == 200, r.text
    x = _id_ks(c, b["email"])
    assert c.post("/training/api/engineers/action", json={"key": KEY, "id": x["id"], "action": "approve"}).json() == {"ok": True}
    lg = c.post("/training/api/engineer/login", json={"id": b["email"], "password": b["password"]})
    assert lg.status_code == 200, lg.text
    return b, x["id"], lg.json()


def test_email_doanh_nghiep_nhan_otp_va_dang_nhap_duoc(c, monkeypatch):
    gui = []
    monkeypatch.setattr(training, "OTP_MODE", True)
    monkeypatch.setattr(training, "send_otp", lambda email, code: gui.append((email, code)) or True)
    b = _ks()
    r = c.post("/training/api/engineer/register", json=b)
    assert r.status_code == 200 and r.json()["mode"] == "otp"
    assert gui and gui[0][0] == b["email"]
    # chưa xác minh -> chưa đăng nhập được
    assert c.post("/training/api/engineer/login", json={"id": b["email"], "password": b["password"]}).status_code == 403
    assert c.post("/training/api/engineer/verify", json={"email": b["email"], "otp": "000000" if gui[0][1] != "000000" else "111111"}).status_code == 422
    assert c.post("/training/api/engineer/verify", json={"email": b["email"], "otp": gui[0][1]}).status_code == 200
    lg = c.post("/training/api/engineer/login", json={"id": b["phone"], "password": b["password"]})   # đăng nhập bằng SĐT
    assert lg.status_code == 200
    d = lg.json()
    assert d["eng_code"].startswith("ENG-") and d["need_consent"] is False
    x = _id_ks(c, b["email"])
    assert x["work_email"] is True and x["status"] == "active" and x["role_group"] == "Vận hành"
    assert (x["company"], x["industrial_zone"], x["province"]) == (b["company"], b["industrial_zone"], "Đồng Nai")


@pytest.mark.parametrize("dom", ["gmail.com", "Yahoo.com", "outlook.com", "hotmail.com", "icloud.com"])
def test_email_mien_phi_chuyen_cho_duyet(c, monkeypatch, dom):
    monkeypatch.setattr(training, "OTP_MODE", True)
    monkeypatch.setattr(training, "send_otp", lambda email, code: pytest.fail("không được gửi OTP cho email cá nhân"))
    b = _ks(email=f"ks{uuid.uuid4().hex[:8]}@{dom}")
    r = c.post("/training/api/engineer/register", json=b)
    assert r.status_code == 200 and r.json()["mode"] == "manual" and "email cá nhân" in r.json()["message"]
    x = _id_ks(c, b["email"].lower())
    assert x["work_email"] is False and x["status"] == "pending"
    assert c.post("/training/api/engineer/login", json={"id": b["email"], "password": b["password"]}).status_code == 403


def test_email_doanh_nghiep_khi_chua_co_smtp_thi_cho_duyet(c):
    b = _ks()                                  # OTP_MODE tắt trong fixture
    assert c.post("/training/api/engineer/register", json=b).json()["mode"] == "manual"
    x = _id_ks(c, b["email"])
    assert x["work_email"] is True and x["status"] == "pending"


def test_trung_email_hoac_sdt_voi_bat_ky_bang_tai_khoan_nao(c):
    sv = _sv()
    assert c.post("/training/api/student/register", json=sv).status_code == 200
    with Session(c.engine) as s:
        nv = TrnStaff(emp_code=f"SV{uuid.uuid4().hex[:5]}", full_name="Nhân Viên A",
                      email=f"nv{uuid.uuid4().hex[:8]}@svws.vn", salt="x", pw_hash="x", status="active")
        s.add(nv); s.commit()
        nv_email = nv.email
    for kw in ({"email": sv["email"]}, {"phone": sv["phone"]}, {"email": nv_email}):
        r = c.post("/training/api/engineer/register", json=_ks(**kw))
        assert r.status_code == 409 and "đã đăng ký" in r.json()["detail"], kw
    ks = _ks()
    assert c.post("/training/api/engineer/register", json=ks).status_code == 200
    assert c.post("/training/api/engineer/register", json=_ks(email=ks["email"])).status_code == 409
    # chiều ngược lại: sinh viên trùng email/SĐT kỹ sư cũng bị chặn
    assert c.post("/training/api/student/register", json=_sv(email=ks["email"])).status_code == 409
    assert c.post("/training/api/student/register", json=_sv(phone=ks["phone"])).status_code == 409


def test_kiem_tra_du_lieu_dau_vao(c):
    for kw, msg in (({"agree_terms": False}, "Điều khoản"), ({"company": " "}, "công ty"),
                    ({"province": "Hà Tây"}, "tỉnh"), ({"role_group": "giam_doc"}, "Nhóm"),
                    ({"phone": "0123"}, "điện thoại"), ({"email": "a@mailinator.com"}, "một lần"),
                    ({"full_name": "An"}, "họ và tên")):
        r = c.post("/training/api/engineer/register", json=_ks(**kw))
        assert r.status_code == 422 and msg.lower() in r.json()["detail"].lower(), (kw, r.text)
    assert len(training.PROVINCES) == len(set(training.PROVINCES)) == 34
    # trường tùy chọn để trống vẫn đăng ký được
    r = c.post("/training/api/engineer/register", json=_ks(industrial_zone="", province="", job_title="", role_group=""))
    assert r.status_code == 200


def test_lam_test_xong_admin_thay_diem_ma_eng(c):
    b, eid, lg = _ks_duyet_dang_nhap(c)
    tok, code = lg["token"], lg["eng_code"]
    assert c.post("/training/api/results", json={"token": tok, "code": "NT03", "pct": 90, "kq": "ĐẠT"}).json() == {"ok": True}
    sm = c.get(f"/training/api/summary?key={KEY}").json()
    row = [x for x in sm["summary"] if x["emp_code"] == code]
    assert row and row[0]["name"] == b["full_name"] and row[0]["best_pct"] == 90
    assert sm["engineers_active"] >= 1 and "engineers_pending" in sm
    assert code in c.get(f"/training/api/results.csv?key={KEY}").text
    me = c.get(f"/training/api/me?token={tok}").json()
    assert me["account_type"] == "engineer" and me["code"] == code and me["share_company"] is False


def test_ma_eng_tang_dan_khong_trung_sau_khi_xoa(c):
    """Xóa đúng tài khoản MỚI NHẤT rồi đăng ký tiếp — mã không được cấp lại (cả mã SVU- của sinh viên)."""
    b1, _, l1 = _ks_duyet_dang_nhap(c)
    b2, _, l2 = _ks_duyet_dang_nhap(c)
    n1, n2 = int(l1["eng_code"][4:]), int(l2["eng_code"][4:])
    assert n2 == n1 + 1
    c.post("/training/api/results", json={"token": l2["token"], "code": "NC01", "pct": 50})
    assert c.post("/training/api/me/delete", json={"token": l2["token"], "password": b2["password"]}).status_code == 200
    _, _, l3 = _ks_duyet_dang_nhap(c)
    assert l3["eng_code"] not in (l1["eng_code"], l2["eng_code"])


def test_admin_loc_theo_cong_ty_va_kcn_va_thao_tac(c):
    tag = uuid.uuid4().hex[:6]
    for co, kz in ((f"Nhà Máy Bia {tag}", "KCN Amata"), (f"nhà máy bia {tag}", "KCN Nhơn Trạch 1"), (f"Dệt {tag}", "KCN Amata")):
        assert c.post("/training/api/engineer/register", json=_ks(company=co, industrial_zone=kz)).status_code == 200
    ds = lambda q: c.get(f"/training/api/engineers?key={KEY}&{q}").json()["engineers"]  # noqa: E731
    assert len(ds(f"company=BIA%20{tag}")) == 2                      # không phân biệt hoa thường
    assert len(ds(f"company={tag}&zone=amata")) == 2
    assert len(ds(f"company=d%E1%BB%87t%20{tag}&zone=nh%C6%A1n")) == 0
    x = ds(f"company=D%E1%BB%87t%20{tag}")[0]
    assert c.post("/training/api/engineers/action", json={"key": KEY, "id": x["id"], "action": "block"}).status_code == 200
    assert ds(f"company=D%E1%BB%87t%20{tag}")[0]["status"] == "blocked"
    assert c.post("/training/api/engineers/action", json={"key": KEY, "id": x["id"], "action": "delete"}).status_code == 200
    assert ds(f"company=D%E1%BB%87t%20{tag}") == []
    assert c.get("/training/api/engineers?key=sai").status_code == 403
    assert c.post("/training/api/engineers/action", json={"key": "sai", "id": 1, "action": "block"}).status_code == 403


def test_dong_y_chia_se_voi_cong_ty(c):
    b, eid, lg = _ks_duyet_dang_nhap(c, marketing=False, share_company=True)
    assert lg["share_company"] is True and lg["marketing"] is False
    assert [(r.purpose, r.granted) for r in _consents(c, "engineer", eid)] == [
        ("terms", True), ("marketing", False), ("share_company", True)]
    tok = lg["token"]
    r = c.post("/training/api/me/consent", json={"token": tok, "terms": True, "share_company": False})
    assert r.json()["share_company"] is False
    assert [r.purpose for r in _consents(c, "engineer", eid)][-1] == "share_company"
    # sinh viên gửi share_company -> bị bỏ qua, không có khóa này
    _, sid, l2 = _dang_ky_duyet_dang_nhap(c)
    r = c.post("/training/api/me/consent", json={"token": l2["token"], "terms": True, "share_company": True})
    assert "share_company" not in r.json()
    assert "share_company" not in [x.purpose for x in _consents(c, "student", sid)]


def test_tai_va_xoa_du_lieu_ky_su(c):
    b, eid, lg = _ks_duyet_dang_nhap(c, share_company=True)
    tok, code = lg["token"], lg["eng_code"]
    c.post("/training/api/results", json={"token": tok, "code": "KT02", "pct": 60, "kq": "CHƯA ĐẠT"})
    d = c.get(f"/training/api/me/export?token={tok}").json()
    assert d["account"]["account_type"] == "engineer" and d["account"]["company"] == b["company"]
    assert not ({"pw_hash", "salt", "token", "otp_code"} & set(d["account"]))
    assert [x["code"] for x in d["results"]] == ["KT02"]
    assert c.post("/training/api/me/delete", json={"token": tok, "password": b["password"]}).status_code == 200
    with Session(c.engine) as s:
        assert s.get(TrnEngineer, eid) is None
        assert not s.exec(select(TrnResult).where(TrnResult.emp_code == code)).all()
        assert s.exec(select(TrnResult).where(TrnResult.emp_code == training._anon_code(code))).first().name == "Đã xóa"
        assert not s.exec(select(TrnConsent).where(TrnConsent.account_type == "engineer", TrnConsent.account_id == eid)).all()


def test_tai_khoan_sinh_vien_va_nhan_vien_cu_van_binh_thuong(c, monkeypatch):
    b, sid, lg = _dang_ky_duyet_dang_nhap(c)
    assert c.post("/training/api/results", json={"token": lg["token"], "code": "NC01", "pct": 80, "kq": "ĐẠT"}).json() == {"ok": True}
    monkeypatch.setattr(training, "EMP_DOMAINS", ["svws.test"])
    local = "nv" + uuid.uuid4().hex[:8]
    nv = c.post("/training/api/staff/login", json={"id": f"{local}@svws.test", "password": local})
    assert nv.status_code == 200
    assert c.post("/training/api/results", json={"token": nv.json()["token"], "code": "NC02", "pct": 70}).json() == {"ok": True}
    with Session(c.engine) as s:
        assert s.exec(select(TrnResult).where(TrnResult.emp_code == lg["student_code"])).first().pct == 80
        assert s.exec(select(TrnResult).where(TrnResult.emp_code == local.upper())).first().pct == 70
        assert s.exec(select(TrnStudent).where(TrnStudent.id == sid)).first().status == "active"


def test_trang_dang_ky_va_admin_co_ky_su(c):
    reg = c.get("/training/register").text
    assert "id=tK" in reg and "/training/api/engineer/register" in reg and "id=c_share" in reg
    assert "c_share checked" not in reg                 # ô tùy chọn không tick sẵn
    assert reg.count("<option>") == 34 and "__PROVINCE_OPTS__" not in reg and "__ROLE_OPTS__" not in reg
    assert 'value="utility">Quản lý Utility/Facility' in reg
    adm = c.get("/training/admin").text
    assert "/training/api/engineers?key=" in adm and "email cá nhân" in adm and "engineers_active" in adm
    app_html = open(training.HTML_PATH, encoding="utf-8").read()
    assert "/engineer/login" in app_html and "d.eng_code" in app_html and "share_company" in app_html


def test_ma_sinh_vien_khong_cap_lai_khi_xoa_tai_khoan_moi_nhat(c):
    _dang_ky_duyet_dang_nhap(c)
    b2, _, l2 = _dang_ky_duyet_dang_nhap(c)
    c.post("/training/api/results", json={"token": l2["token"], "code": "NC01", "pct": 50})
    assert c.post("/training/api/me/delete", json={"token": l2["token"], "password": b2["password"]}).status_code == 200
    _, _, l3 = _dang_ky_duyet_dang_nhap(c)
    assert l3["student_code"] != l2["student_code"]
