"""
Rà soát lỗi mô-đun đào tạo T102 sau PR #5/#9/#10: mã người học trùng giữa các loại tài khoản, cấp mã đồng thời,
dữ liệu quá dài (Postgres báo 500), OTP bị dò, trùng email/SĐT giữa sinh viên và kỹ sư.
Chạy trên SQLite và Postgres như các test training khác.
"""
import threading
import time
import uuid

import pytest
from sqlmodel import Session, select

from tests.test_training_dong_y import KEY, _sv, c  # noqa: F401  (c là fixture)
from tests.test_training_ky_su import _ks
import training
from training import TrnCodeSeq, TrnResult, TrnStaff, TrnStudent


def _code4():
    return "%04d" % (uuid.uuid4().int % 10000)


def _nv(**kw):
    b = {"emp_code": "SV" + uuid.uuid4().hex[:6].upper(), "full_name": "Trần Thị Test",
         "email": f"nv{uuid.uuid4().hex[:8]}@svws.vn", "password": "matkhau1", "agree_terms": True}
    b.update(kw)
    return b


# ---------------- 1. mã nhân viên không được mạo danh mã SVU-/ENG-/DEL- ----------------
@pytest.mark.parametrize("ma", ["SVU-", "svu-", "ENG-", "DEL-"])
def test_ma_nhan_vien_khong_dung_tien_to_da_danh_rieng(c, ma):
    r = c.post("/training/api/staff/register", json=_nv(emp_code=ma + _code4()))
    assert r.status_code == 422, r.text


def test_xoa_nhan_vien_khong_an_danh_diem_cua_sinh_vien(c):
    """Trước đây: nhân viên tự đặt mã = mã sinh viên -> điểm dùng chung, xóa nhân viên làm mất điểm của sinh viên."""
    b = _sv()
    c.post("/training/api/student/register", json=b)
    sid = [x for x in c.get(f"/training/api/students?key={KEY}").json()["students"] if x["email"] == b["email"]][0]["id"]
    c.post("/training/api/students/action", json={"key": KEY, "id": sid, "action": "approve"})
    tok = c.post("/training/api/student/login", json={"id": b["email"], "password": b["password"]}).json()["token"]
    assert c.post("/training/api/results", json={"token": tok, "code": "NC01", "pct": 90}).status_code == 200
    with Session(c.engine) as s:
        code = s.get(TrnStudent, sid).student_code
    c.post("/training/api/staff/register", json=_nv(emp_code=code))          # bị chặn (422)
    with Session(c.engine) as s:
        for st in s.exec(select(TrnStaff).where(TrnStaff.emp_code == code)).all():
            training._purge_account(s, "staff", st)
        s.commit()
        assert s.exec(select(TrnResult).where(TrnResult.emp_code == code)).all(), "điểm sinh viên bị ẩn danh nhầm"


def test_nhan_vien_tu_tao_khong_trung_ma_va_khong_mao_danh(c, monkeypatch):
    dom = "svws-%s.test" % uuid.uuid4().hex[:6]
    monkeypatch.setattr(training, "EMP_DOMAINS", [dom])
    local = "nv" + uuid.uuid4().hex[:6]
    # người khác đã đăng ký (chờ duyệt) với mã = phần trước @ của email sắp tự tạo
    assert c.post("/training/api/staff/register", json=_nv(emp_code=local.upper(), email=f"khac{local}@{dom}")).status_code == 200
    r = c.post("/training/api/staff/login", json={"id": f"{local}@{dom}", "password": local})
    assert r.status_code == 200, r.text
    assert r.json()["emp_code"] != local.upper()
    with Session(c.engine) as s:
        codes = [x.emp_code for x in s.exec(select(TrnStaff).where(TrnStaff.emp_code.startswith(local.upper()))).all()]
    assert len(codes) == len(set(codes)) == 2
    # email bắt đầu bằng svu-… không được thành mã SVU-…
    lc = "svu-" + _code4()
    r = c.post("/training/api/staff/login", json={"id": f"{lc}@{dom}", "password": lc})
    assert r.status_code == 200, r.text
    assert not r.json()["emp_code"].startswith(("SVU-", "ENG-", "DEL-"))


# ---------------- 2. dữ liệu quá dài: 422 rõ ràng, không 500 trên Postgres ----------------
def test_dang_ky_truong_qua_dai_tra_422(c):
    dai = "Nguyễn " + "A" * 90
    for path, body in (("student", _sv(full_name=dai)), ("student", _sv(school="Trường " + "X" * 200)),
                       ("student", _sv(course="K" * 150)),
                       ("student", _sv(email="a" * 120 + "@hcmut.edu.vn")),
                       ("engineer", _ks(full_name=dai)), ("staff", _nv(full_name=dai)),
                       ("staff", _nv(emp_code="SV" + "9" * 40))):
        r = c.post(f"/training/api/{path}/register", json=body)
        assert r.status_code == 422, (path, r.status_code, r.text[:200])


def test_nop_diem_truong_qua_dai_va_pct_ngoai_khoang(c):
    b = _sv()
    c.post("/training/api/student/register", json=b)
    sid = [x for x in c.get(f"/training/api/students?key={KEY}").json()["students"] if x["email"] == b["email"]][0]["id"]
    c.post("/training/api/students/action", json={"key": KEY, "id": sid, "action": "approve"})
    tok = c.post("/training/api/student/login", json={"id": b["email"], "password": b["password"]}).json()["token"]
    r = c.post("/training/api/results", json={"token": tok, "code": "C" * 50, "tech": "T" * 500, "dm": "D" * 300,
                                              "score": "9" * 30, "kq": "K" * 30, "d": "x" * 80, "pct": 5000})
    assert r.status_code == 200, r.text[:300]
    with Session(c.engine) as s:
        code = s.get(TrnStudent, sid).student_code
        rr = s.exec(select(TrnResult).where(TrnResult.emp_code == code)).one()
    assert rr.pct == 100 and len(rr.code) == 20 and len(rr.tech) == 200
    assert c.post("/training/api/results", json={"token": tok, "code": "NC02", "pct": -7}).status_code == 200
    with Session(c.engine) as s:
        assert s.exec(select(TrnResult).where(TrnResult.emp_code == code, TrnResult.code == "NC02")).one().pct == 0


# ---------------- 3. OTP: chặn dò mã ----------------
def test_otp_sai_qua_5_lan_thi_huy_ma(c, monkeypatch):
    monkeypatch.setattr(training, "OTP_MODE", True)
    monkeypatch.setattr(training, "send_otp", lambda email, code: True)
    training._OTP_FAILS.clear()
    b = _sv()
    assert c.post("/training/api/student/register", json=b).json()["mode"] == "otp"
    with Session(c.engine) as s:
        otp = s.exec(select(TrnStudent).where(TrnStudent.email == b["email"])).one().otp_code
    sai = "%06d" % ((int(otp) + 1) % 1000000)
    for _ in range(training.OTP_MAX_FAILS):
        assert c.post("/training/api/student/verify", json={"email": b["email"], "otp": sai}).status_code == 422
    r = c.post("/training/api/student/verify", json={"email": b["email"], "otp": otp})
    assert r.status_code != 200, "mã đúng vẫn dùng được sau khi đã dò sai quá giới hạn"
    with Session(c.engine) as s:
        assert s.exec(select(TrnStudent).where(TrnStudent.email == b["email"])).one().status == "pending"


def test_otp_sai_vai_lan_roi_dung_van_kich_hoat(c, monkeypatch):
    monkeypatch.setattr(training, "OTP_MODE", True)
    monkeypatch.setattr(training, "send_otp", lambda email, code: True)
    training._OTP_FAILS.clear()
    b = _ks()
    assert c.post("/training/api/engineer/register", json=b).json()["mode"] == "otp"
    with Session(c.engine) as s:
        otp = s.exec(select(training.TrnEngineer).where(training.TrnEngineer.email == b["email"])).one().otp_code
    sai = "%06d" % ((int(otp) + 1) % 1000000)
    for _ in range(training.OTP_MAX_FAILS - 1):
        assert c.post("/training/api/engineer/verify", json={"email": b["email"], "otp": sai}).status_code == 422
    assert c.post("/training/api/engineer/verify", json={"email": b["email"], "otp": otp}).status_code == 200


# ---------------- 4. trùng email/SĐT giữa sinh viên và kỹ sư ----------------
def test_sinh_vien_khong_dang_ky_trung_email_hoac_sdt_ky_su(c):
    k = _ks()
    assert c.post("/training/api/engineer/register", json=k).status_code == 200
    assert c.post("/training/api/student/register", json=_sv(email=k["email"])).status_code == 409
    assert c.post("/training/api/student/register", json=_sv(phone=k["phone"])).status_code == 409


# ---------------- 5. cấp mã đồng thời khi chưa có dòng trn_code_seq ----------------
def test_cap_ma_dong_thoi_lan_dau_khong_loi(c):
    if c.engine.dialect.name != "postgresql":
        pytest.skip("Chỉ Postgres mới có 2 giao dịch chạy song song thật")
    prefix = "T%s-" % uuid.uuid4().hex[:5].upper()      # tiền tố mới -> chưa có dòng seq
    out, err = {}, {}
    sa = Session(c.engine)
    out["a"] = training._next_code(sa, prefix, TrnStudent.student_code)
    sa.flush()                                           # giao dịch A giữ dòng seq, chưa commit

    def b():
        try:
            with Session(c.engine) as sb:
                out["b"] = training._next_code(sb, prefix, TrnStudent.student_code)
                sb.commit()
        except Exception as e:                           # noqa: BLE001
            err["b"] = e

    t = threading.Thread(target=b); t.start()
    time.sleep(0.5)
    sa.commit(); sa.close()
    t.join(10)
    assert not err, repr(err.get("b"))
    assert out == {"a": prefix + "0001", "b": prefix + "0002"}
    with Session(c.engine) as s:
        assert s.get(TrnCodeSeq, prefix).last == 2
