"""
Test H2 — nguồn đăng ký (UTM) + mã giới thiệu + báo cáo nguồn (T102 · PR-3).
Chạy trên CẢ SQLite và Postgres (khi `make db-up`) như test_training_dong_y.py.
"""
import datetime as dt
import re
import shutil
import subprocess
import uuid

import pytest
from sqlmodel import Session, select

# nạp trước: đặt DATABASE_URL rồi mới import training; dùng lại fixture `c` (SQLite + Postgres)
from tests.test_training_dong_y import KEY, _dang_ky_duyet_dang_nhap, _phone, _sv, c  # noqa: F401
from tests.test_training_ky_su import _ks, _ks_duyet_dang_nhap                      # noqa: E402
import training                                                                     # noqa: E402
from training import TrnRefCode, TrnSignupMeta, TrnStudent                          # noqa: E402

CAMP = "test-" + uuid.uuid4().hex[:6]       # chiến dịch riêng mỗi lần chạy — Postgres dùng chung DB


def _meta(c, atype, aid):
    with Session(c.engine) as s:
        return s.exec(select(TrnSignupMeta).where(TrnSignupMeta.account_type == atype,
                                                  TrnSignupMeta.account_id == aid)).all()


def _sources(c, **q):
    qs = "&".join(f"{k}={v}" for k, v in q.items())
    r = c.get(f"/training/api/sources?key={KEY}&{qs}")
    assert r.status_code == 200, r.text
    return r.json()


def _camp(d, camp):
    return [x for x in d["by_campaign"] if x["utm_campaign"] == camp]


def test_dang_ky_qua_link_utm_admin_thay_dung_nguon(c):
    camp = CAMP + "-fb"
    b, sid, lg = _dang_ky_duyet_dang_nhap(c, utm_source="Facebook", utm_medium="group", utm_campaign=camp,
                                          utm_content="bai-1", landing_path="/training/register")
    m = _meta(c, "student", sid)
    assert [(x.utm_source, x.utm_medium, x.utm_campaign, x.utm_content, x.landing_path, x.referrer_id) for x in m] == [
        ("facebook", "group", camp, "bai-1", "/training/register", None)]          # utm viết thường
    # một người chưa kích hoạt cùng chiến dịch
    assert c.post("/training/api/student/register", json=_sv(utm_source="facebook", utm_campaign=camp)).status_code == 200
    d = _sources(c)
    assert _camp(d, camp) == [{"utm_campaign": camp, "registered": 2, "activated": 1}]
    y, w, _ = dt.date.today().isocalendar()
    row = [x for x in d["by_source_week"] if x["utm_source"] == "facebook" and x["week"] == "%d-W%02d" % (y, w)]
    assert row and row[0]["registered"] >= 2 and row[0]["activated"] >= 1


def test_link_ngan_redirect_va_nguoi_gioi_thieu_duoc_cong(c):
    b, sid, lg = _dang_ky_duyet_dang_nhap(c)
    me = c.get(f"/training/api/me?token={lg['token']}").json()
    ref = me["ref_code"]
    assert len(ref) == 6 and not set(ref) & set("0O1I") and me["ref_link"] == "/training/r/" + ref
    # link ngắn -> 302 sang trang đăng ký kèm ref (giữ utm nếu có)
    r = c.get(f"/training/r/{ref.lower()}?utm_source=zalo&x=1", follow_redirects=False)
    assert r.status_code == 302 and r.headers["location"] == f"/training/register?utm_source=zalo&ref={ref}"
    camp = CAMP + "-ref"
    # người được mời: 1 sinh viên đã hoàn thành 1 chuyên đề, 1 kỹ sư chưa kích hoạt
    b2, sid2, lg2 = _dang_ky_duyet_dang_nhap(c, ref=ref.lower(), utm_campaign=camp)
    c.post("/training/api/results", json={"token": lg2["token"], "code": "NC01", "pct": 90, "kq": "ĐẠT"})
    assert c.post("/training/api/engineer/register", json=_ks(ref=ref, utm_campaign=camp)).status_code == 200
    m = _meta(c, "student", sid2)[0]
    assert (m.ref_code_used, m.referrer_type, m.referrer_id) == (ref, "student", sid)
    top = [x for x in _sources(c)["top_referrers"] if x["ref_code"] == ref]
    assert top == [{"account_type": "student", "code": lg["student_code"], "name": b["full_name"], "ref_code": ref,
                    "invited": 2, "activated": 1, "completed": 1}]


def test_ma_gioi_thieu_khong_ton_tai_thi_bo_qua(c):
    b, sid, lg = _dang_ky_duyet_dang_nhap(c, ref="ZZZZZZ")
    m = _meta(c, "student", sid)[0]
    assert (m.ref_code_used, m.referrer_type, m.referrer_id) == ("ZZZZZZ", "", None)


def test_dang_ky_khong_tham_so_van_chay_va_cat_80_ky_tu(c):
    b, sid, lg = _dang_ky_duyet_dang_nhap(c)                 # không gửi trường nguồn nào
    m = _meta(c, "student", sid)
    assert len(m) == 1 and m[0].utm_source == "" and m[0].referrer_id is None
    dai = "x" * 300
    r = c.post("/training/api/student/register", json=_sv(utm_source=dai, utm_campaign=dai, landing_path=dai, ref=dai))
    assert r.status_code == 200
    with Session(c.engine) as s:
        sv = s.exec(select(TrnStudent).order_by(TrnStudent.id.desc())).first()
        m = s.exec(select(TrnSignupMeta).where(TrnSignupMeta.account_type == "student",
                                               TrnSignupMeta.account_id == sv.id)).one()
    assert len(m.utm_source) == len(m.utm_campaign) == len(m.landing_path) == len(m.ref_code_used) == 80


def test_ma_gioi_thieu_sinh_khi_kich_hoat_khong_trung(c, monkeypatch):
    # chờ duyệt -> chưa có mã; duyệt -> có mã
    b = _sv()
    c.post("/training/api/student/register", json=b)
    with Session(c.engine) as s:
        sid = s.exec(select(TrnStudent).where(TrnStudent.email == b["email"])).one().id
        assert not s.exec(select(TrnRefCode).where(TrnRefCode.account_type == "student", TrnRefCode.account_id == sid)).all()
    c.post("/training/api/students/action", json={"key": KEY, "id": sid, "action": "approve"})
    with Session(c.engine) as s:
        assert len(s.exec(select(TrnRefCode).where(TrnRefCode.account_type == "student", TrnRefCode.account_id == sid)).all()) == 1
    # OTP: kích hoạt khi xác minh
    gui = []
    monkeypatch.setattr(training, "OTP_MODE", True)
    monkeypatch.setattr(training, "send_otp", lambda email, code: gui.append(code) or True)
    k = _ks()
    c.post("/training/api/engineer/register", json=k)
    c.post("/training/api/engineer/verify", json={"email": k["email"], "otp": gui[0]})
    lg = c.post("/training/api/engineer/login", json={"id": k["email"], "password": k["password"]}).json()
    assert len(c.get(f"/training/api/me?token={lg['token']}").json()["ref_code"]) == 6
    # nhân viên tự tạo qua đăng nhập cũng có mã; đăng nhập lại không sinh thêm
    monkeypatch.setattr(training, "EMP_DOMAINS", ["svws.test"])
    local = "nv" + uuid.uuid4().hex[:8]
    for _ in range(2):
        tok = c.post("/training/api/staff/login", json={"id": f"{local}@svws.test", "password": local}).json()["token"]
    ref1 = c.get(f"/training/api/me?token={tok}").json()["ref_code"]
    assert ref1 == c.get(f"/training/api/me?token={tok}").json()["ref_code"]
    with Session(c.engine) as s:
        codes = s.exec(select(TrnRefCode.code)).all()
    assert len(codes) == len(set(codes))
    # bảng chữ cái không có ký tự dễ nhầm
    assert not set(training.REF_ALPHABET) & set("0O1I")


def test_xoa_tai_khoan_xoa_nguon_va_ma_gioi_thieu(c):
    b, sid, lg = _dang_ky_duyet_dang_nhap(c, utm_source="linkedin")
    ref = c.get(f"/training/api/me?token={lg['token']}").json()["ref_code"]
    b2, sid2, lg2 = _dang_ky_duyet_dang_nhap(c, ref=ref)
    ex = c.get(f"/training/api/me/export?token={lg['token']}").json()
    assert ex["ref_code"] == ref and ex["signup_source"][0]["utm_source"] == "linkedin"
    assert c.post("/training/api/me/delete", json={"token": lg["token"], "password": b["password"]}).status_code == 200
    assert _meta(c, "student", sid) == []
    with Session(c.engine) as s:
        assert not s.exec(select(TrnRefCode).where(TrnRefCode.code == ref)).all()
    m2 = _meta(c, "student", sid2)[0]                          # người được mời: còn dòng, mất liên kết
    assert (m2.referrer_type, m2.referrer_id, m2.ref_code_used) == ("", None, ref)
    assert not [x for x in _sources(c)["top_referrers"] if x["ref_code"] == ref]


def test_loc_ngay_csv_va_quyen_admin(c):
    camp = CAMP + "-ngay"
    _dang_ky_duyet_dang_nhap(c, utm_source="workshop", utm_campaign=camp)
    hom_nay = (dt.datetime.utcnow() + dt.timedelta(hours=7)).date()
    assert _camp(_sources(c, **{"from": hom_nay.isoformat(), "to": hom_nay.isoformat()}), camp)
    assert not _camp(_sources(c, **{"from": (hom_nay + dt.timedelta(days=1)).isoformat()}), camp)
    assert not _camp(_sources(c, to=(hom_nay - dt.timedelta(days=1)).isoformat()), camp)
    assert c.get(f"/training/api/sources?key={KEY}&from=04-10-2026").status_code == 422
    assert c.get("/training/api/sources?key=sai").status_code == 403
    assert c.get("/training/api/sources.csv?key=sai").status_code == 403
    r = c.get(f"/training/api/sources.csv?key={KEY}")
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    assert "utm_campaign" in r.text and camp in r.text and "Top người giới thiệu" in r.text


def test_nhan_vien_khong_vao_bang_nguon_nhung_tai_khoan_cu_van_chay(c, monkeypatch):
    monkeypatch.setattr(training, "EMP_DOMAINS", [])
    camp = CAMP + "-nv"
    r = c.post("/training/api/staff/register", json={"emp_code": "SV" + uuid.uuid4().hex[:5], "full_name": "Lê Nhân Viên",
                                                    "email": f"nv{uuid.uuid4().hex[:8]}@svws.vn", "password": "matkhau1",
                                                    "agree_terms": True, "utm_campaign": camp})
    assert r.status_code == 200
    assert not _camp(_sources(c), camp)
    # tài khoản cũ (trước PR-3, không có dòng nguồn) vẫn đăng nhập + nộp điểm; đăng nhập thì có mã giới thiệu
    with Session(c.engine) as s:
        sv = TrnStudent(full_name="Cũ Trước PR3", phone=_phone(), email=f"cu{uuid.uuid4().hex[:8]}@gmail.com",
                        school="ĐH X", course="K20", salt="s", pw_hash=training.hash_pw("matkhau1", "s"),
                        status="active", student_code=f"SVU-T{uuid.uuid4().hex[:5]}")
        s.add(sv); s.commit(); s.refresh(sv)
        email = sv.email
    lg = c.post("/training/api/student/login", json={"id": email, "password": "matkhau1"}).json()
    c.post("/training/api/me/consent", json={"token": lg["token"], "terms": True})
    assert c.post("/training/api/results", json={"token": lg["token"], "code": "NT01", "pct": 85}).json() == {"ok": True}
    assert len(c.get(f"/training/api/me?token={lg['token']}").json()["ref_code"]) == 6


def test_giao_dien_co_nguon_va_link_gioi_thieu(c):
    reg = c.get("/training/register").text
    assert "svws_trn_src" in reg and "sessionStorage" in reg and "utm_campaign" in reg
    adm = c.get("/training/admin").text
    assert "/training/api/sources" in adm and "Top 20 người giới thiệu" in adm
    app_html = open(training.HTML_PATH, encoding="utf-8").read()
    assert "Sao chép link" in app_html and "d.ref_link" in app_html


def test_script_trang_dang_ky_va_admin_khong_loi_cu_phap(c, tmp_path):
    """JS nhúng trong chuỗi Python dễ hỏng (vd. '*/' trong chú thích) mà test API không phát hiện."""
    if not shutil.which("node"):
        pytest.skip("Cần node để kiểm cú pháp JS")
    for path in ("/training/register", "/training/admin"):
        js = "\n".join(re.findall(r"<script>(.*?)</script>", c.get(path).text, re.S))
        f = tmp_path / "x.js"
        f.write_text(js, encoding="utf-8")
        r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        assert r.returncode == 0, (path, r.stderr)
