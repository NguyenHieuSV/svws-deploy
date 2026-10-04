"""
Test H6 — đồng ý xử lý dữ liệu, trang chính sách, Tài khoản của tôi, xóa tài khoản (T102 · PR-1).
Chạy trên CẢ SQLite (luôn có) và Postgres (khi `make db-up`) theo yêu cầu kiểm thử chung của spec.
Không gửi email: OTP_MODE tắt nên đăng ký mới luôn chờ admin duyệt.
"""
import os
import uuid
import random

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://svws:svws@localhost:5432/svws")


def _pg_ok(url):
    try:
        from sqlalchemy import create_engine
        create_engine(url).connect().close()
        return True
    except Exception:
        return False


_PG_URL = os.environ["DATABASE_URL"]
_HAS_PG = _PG_URL.startswith("postgres") and _pg_ok(_PG_URL)
if not _HAS_PG and "training" not in __import__("sys").modules:
    import tempfile
    os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "import.db")  # chỉ để import

from fastapi import FastAPI                        # noqa: E402
from fastapi.testclient import TestClient          # noqa: E402
from sqlmodel import SQLModel, Session, create_engine, select  # noqa: E402
import training                                    # noqa: E402
from training import TrnConsent, TrnResult, TrnStaff, TrnStudent  # noqa: E402

KEY = "khoa-test"


@pytest.fixture(params=["sqlite", "postgres"])
def c(request, monkeypatch, tmp_path):
    if request.param == "sqlite":
        eng = create_engine(f"sqlite:///{tmp_path}/trn.db", connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(eng)
    else:
        if not _HAS_PG:
            pytest.skip("Cần Postgres đang chạy (make db-up)")
        eng = create_engine(_PG_URL.replace("postgres://", "postgresql://", 1))
        SQLModel.metadata.create_all(eng)
    monkeypatch.setattr(training, "_engine", eng)
    monkeypatch.setattr(training, "ADMIN_KEY", KEY)
    monkeypatch.setattr(training, "OTP_MODE", False)
    monkeypatch.setattr(training, "EMP_DOMAINS", [])
    training._RL.clear()
    app = FastAPI()
    app.include_router(training.router)
    cl = TestClient(app)
    cl.engine = eng
    return cl


def _phone():
    while True:
        p = "09" + "".join(random.choice("0123456789") for _ in range(8))
        if training.valid_phone(p):
            return p


def _sv(**kw):
    b = {"full_name": "Nguyễn Văn Test", "phone": _phone(), "email": f"t{uuid.uuid4().hex[:10]}@hcmut.edu.vn",
         "school": "ĐH Bách khoa", "course": "K2023", "password": "matkhau1", "agree_terms": True}
    b.update(kw)
    return b


def _dang_ky_duyet_dang_nhap(c, **kw):
    b = _sv(**kw)
    r = c.post("/training/api/student/register", json=b)
    assert r.status_code == 200, r.text
    sid = [x for x in c.get(f"/training/api/students?key={KEY}").json()["students"] if x["email"] == b["email"]][0]["id"]
    assert c.post("/training/api/students/action", json={"key": KEY, "id": sid, "action": "approve"}).status_code == 200
    lg = c.post("/training/api/student/login", json={"id": b["email"], "password": b["password"]})
    assert lg.status_code == 200, lg.text
    return b, sid, lg.json()


def _consents(c, atype, aid):
    with Session(c.engine) as s:
        return s.exec(select(TrnConsent).where(TrnConsent.account_type == atype, TrnConsent.account_id == aid)
                      .order_by(TrnConsent.id)).all()


def test_khong_tick_o_bat_buoc_thi_khong_dang_ky_duoc(c):
    for body in (_sv(agree_terms=False), {k: v for k, v in _sv().items() if k != "agree_terms"}):
        r = c.post("/training/api/student/register", json=body)
        assert r.status_code == 422 and "Điều khoản" in r.json()["detail"]
    r = c.post("/training/api/staff/register", json={"emp_code": "SV999", "full_name": "Trần Thị Test",
                                                    "email": f"nv{uuid.uuid4().hex[:8]}@svws.vn", "password": "matkhau1"})
    assert r.status_code == 422


def test_dang_ky_moi_ghi_dong_y_va_khong_phai_hoi_lai(c):
    b, sid, lg = _dang_ky_duyet_dang_nhap(c, marketing=False)
    assert lg["need_consent"] is False and lg["marketing"] is False
    rows = _consents(c, "student", sid)
    assert [(r.purpose, r.granted, r.policy_version) for r in rows] == [
        ("terms", True, training.POLICY_VERSION), ("marketing", False, training.POLICY_VERSION)]
    assert rows[0].ip                                               # có ghi IP


def test_tai_khoan_cu_phai_dong_y_roi_van_nop_diem_duoc(c):
    """Tài khoản có từ trước PR-1 (không có dòng đồng ý): đăng nhập được, bị hỏi đồng ý, nộp điểm được."""
    with Session(c.engine) as s:
        salt = "abcd1234"
        sv = TrnStudent(full_name="Lê Cũ", phone=_phone(), email=f"cu{uuid.uuid4().hex[:8]}@gmail.com",
                        school="ĐH X", course="K20", salt=salt, pw_hash=training.hash_pw("matkhau1", salt),
                        status="active", student_code=f"SVU-T{uuid.uuid4().hex[:5]}")
        s.add(sv); s.commit(); s.refresh(sv)
        sid, email, code = sv.id, sv.email, sv.student_code
    lg = c.post("/training/api/student/login", json={"id": email, "password": "matkhau1"}).json()
    assert lg["need_consent"] is True
    tok = lg["token"]
    assert c.get(f"/training/api/me?token={tok}").json()["need_consent"] is True
    assert c.post("/training/api/me/consent", json={"token": tok, "terms": False}).status_code == 422
    r = c.post("/training/api/me/consent", json={"token": tok, "terms": True, "marketing": True})
    assert r.status_code == 200 and r.json()["need_consent"] is False and r.json()["marketing"] is True
    assert c.post("/training/api/results", json={"token": tok, "code": "NC01", "pct": 90, "kq": "ĐẠT"}).json() == {"ok": True}
    with Session(c.engine) as s:
        assert s.exec(select(TrnResult).where(TrnResult.emp_code == code)).first().pct == 90
    # chính sách đổi phiên bản -> phải đồng ý lại
    training_ver = training.POLICY_VERSION
    try:
        training.POLICY_VERSION = training_ver + "-v2"
        assert c.get(f"/training/api/me?token={tok}").json()["need_consent"] is True
    finally:
        training.POLICY_VERSION = training_ver
    assert [x.purpose for x in _consents(c, "student", sid)] == ["terms", "marketing"]


def test_nhan_vien_tu_tao_qua_dang_nhap_cung_phai_dong_y(c, monkeypatch):
    monkeypatch.setattr(training, "EMP_DOMAINS", ["svws.test"])
    local = "nv" + uuid.uuid4().hex[:8]
    lg = c.post("/training/api/staff/login", json={"id": f"{local}@svws.test", "password": local})
    assert lg.status_code == 200 and lg.json()["need_consent"] is True
    tok = lg.json()["token"]
    c.post("/training/api/me/consent", json={"token": tok, "terms": True})
    me = c.get(f"/training/api/me?token={tok}").json()
    assert me["account_type"] == "staff" and me["need_consent"] is False and me["marketing"] is False


def test_doi_lua_chon_chi_them_dong_khong_ghi_de(c):
    b, sid, lg = _dang_ky_duyet_dang_nhap(c, marketing=False)
    tok = lg["token"]
    for m in (True, True, False):                  # lặp lại cùng giá trị -> không thêm dòng
        c.post("/training/api/me/consent", json={"token": tok, "terms": True, "marketing": m})
    assert [(r.purpose, r.granted) for r in _consents(c, "student", sid)] == [
        ("terms", True), ("marketing", False), ("marketing", True), ("marketing", False)]
    assert c.get("/training/api/me?token=sai").status_code == 401


def test_tai_du_lieu_cua_toi(c):
    b, sid, lg = _dang_ky_duyet_dang_nhap(c, marketing=True)
    tok = lg["token"]
    c.post("/training/api/results", json={"token": tok, "code": "NT02", "pct": 70, "kq": "CHƯA ĐẠT"})
    r = c.get(f"/training/api/me/export?token={tok}")
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    d = r.json()
    assert set(d) >= {"account", "results", "certificates", "consents"}
    acc = d["account"]
    assert acc["email"] == b["email"] and acc["phone"] == b["phone"] and acc["school"] == b["school"]
    assert not ({"pw_hash", "salt", "token", "otp_code"} & set(acc))
    assert [x["code"] for x in d["results"]] == ["NT02"]
    assert [(x["purpose"], x["granted"]) for x in d["consents"]] == [("terms", True), ("marketing", True)]


def test_xoa_tai_khoan(c):
    b, sid, lg = _dang_ky_duyet_dang_nhap(c)
    tok, code = lg["token"], lg["student_code"]
    c.post("/training/api/results", json={"token": tok, "code": "KT01", "pct": 85, "kq": "ĐẠT"})
    assert c.post("/training/api/me/delete", json={"token": tok, "password": "sai"}).status_code == 401
    r = c.post("/training/api/me/delete", json={"token": tok, "password": b["password"]})
    assert r.status_code == 200
    # admin tìm theo email / SĐT không còn thấy
    sts = c.get(f"/training/api/students?key={KEY}").json()["students"]
    assert not [x for x in sts if x["email"] == b["email"] or x["phone"] == b["phone"]]
    with Session(c.engine) as s:
        assert s.get(TrnStudent, sid) is None
        assert not s.exec(select(TrnResult).where(TrnResult.emp_code == code)).all()
        anon = s.exec(select(TrnResult).where(TrnResult.emp_code == training._anon_code(code))).all()
        assert [(x.name, x.code, x.pct) for x in anon] == [("Đã xóa", "KT01", 85)]
    assert _consents(c, "student", sid) == []
    assert c.get(f"/training/api/me?token={tok}").status_code == 401
    assert c.post("/training/api/student/login", json={"id": b["email"], "password": b["password"]}).status_code == 401


def test_ma_sinh_vien_khong_trung_sau_khi_xoa(c):
    b1, _, l1 = _dang_ky_duyet_dang_nhap(c)
    b2, _, l2 = _dang_ky_duyet_dang_nhap(c)
    c.post("/training/api/me/delete", json={"token": l1["token"], "password": b1["password"]})
    b3, _, l3 = _dang_ky_duyet_dang_nhap(c)
    assert l3["student_code"] != l2["student_code"]


def test_trang_chinh_sach_va_form_dang_ky(c):
    for path in ("/training/privacy", "/training/terms"):
        r = c.get(path)
        assert r.status_code == 200 and training.POLICY_VERSION in r.text and "{{" not in r.text
    reg = c.get("/training/register").text
    assert 'id=c_terms' in reg and 'id=c_mkt' in reg and "/training/privacy" in reg
    assert "c_mkt checked" not in reg                  # ô tùy chọn không tick sẵn
