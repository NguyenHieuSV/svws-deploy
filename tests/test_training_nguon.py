"""
Test H2 — nguồn đăng ký (UTM), mã giới thiệu, báo cáo nguồn + sources.csv (T102 · PR-3).
Chạy trên SQLite và Postgres. Mỗi test dùng utm_campaign/nguồn riêng để không lẫn dữ liệu test khác.
"""
import csv
import datetime as dt
import io
import uuid

from sqlmodel import Session, select

from tests.test_training_dong_y import KEY, _sv, c  # noqa: F401  (c là fixture)
from tests.test_training_ky_su import _ks, _id_of
import training
from training import TrnRefCode, TrnResult, TrnSignupMeta, TrnStudent


def _approve_login_sv(c, b):
    sid = [x for x in c.get(f"/training/api/students?key={KEY}").json()["students"] if x["email"] == b["email"]][0]["id"]
    c.post("/training/api/students/action", json={"key": KEY, "id": sid, "action": "approve"})
    lg = c.post("/training/api/student/login", json={"id": b["email"], "password": b["password"]}).json()
    return sid, lg


def _src(c, **q):
    qs = "&".join(f"{k}={v}" for k, v in q.items())
    r = c.get(f"/training/api/sources?key={KEY}&{qs}")
    assert r.status_code == 200, r.text
    return r.json()


def _ref_of(c, tok):
    return c.get(f"/training/api/me?token={tok}").json()["ref_code"]


# ---------------- mã giới thiệu ----------------
def test_ma_gioi_thieu_sinh_khi_kich_hoat(c):
    b = _sv()
    c.post("/training/api/student/register", json=b)
    sid = [x for x in c.get(f"/training/api/students?key={KEY}").json()["students"] if x["email"] == b["email"]][0]["id"]
    with Session(c.engine) as s:                                   # chưa kích hoạt -> chưa có mã
        assert not s.exec(select(TrnRefCode).where(TrnRefCode.account_type == "student", TrnRefCode.account_id == sid)).all()
    c.post("/training/api/students/action", json={"key": KEY, "id": sid, "action": "approve"})
    with Session(c.engine) as s:
        rc = s.exec(select(TrnRefCode).where(TrnRefCode.account_type == "student", TrnRefCode.account_id == sid)).one()
    assert len(rc.code) == 6 and set(rc.code) <= set(training.REF_ALPHABET) and not set(rc.code) & set("0O1I")
    lg = c.post("/training/api/student/login", json={"id": b["email"], "password": b["password"]}).json()
    assert _ref_of(c, lg["token"]) == rc.code                      # ổn định, không sinh lại


def test_tai_khoan_cu_co_ma_o_lan_dang_nhap_dau(c):
    with Session(c.engine) as s:
        salt = "s"
        sv = TrnStudent(full_name="Cũ Không Mã", phone="0912000" + uuid.uuid4().hex[:3].translate(str.maketrans("abcdef", "123456")),
                        email=f"cu{uuid.uuid4().hex[:8]}@gmail.com", school="X", course="K", salt=salt,
                        pw_hash=training.hash_pw("matkhau1", salt), status="active", student_code=f"SVU-C{uuid.uuid4().hex[:4]}")
        s.add(sv); s.commit(); s.refresh(sv); email = sv.email
    tok = c.post("/training/api/student/login", json={"id": email, "password": "matkhau1"}).json()["token"]
    assert len(_ref_of(c, tok)) == 6


def test_link_ngan_chuyen_sang_trang_dang_ky(c):
    r = c.get("/training/r/ab7k2q", follow_redirects=False)
    assert r.status_code == 302 and r.headers["location"] == "/training/register?ref=AB7K2Q"
    r = c.get("/training/r/<script>", follow_redirects=False)
    assert r.headers["location"] == "/training/register?ref=SCRIPT"


# ---------------- ghi nguồn đăng ký ----------------
def test_dang_ky_ghi_utm_cat_80_ky_tu_va_bo_qua_ma_sai(c):
    camp = "Challenge-K1 " + "x" * 100
    b = _sv(utm_source=" Facebook ", utm_medium="group", utm_campaign=camp, utm_content="Bài ghim A",
            landing_path="/training/register?utm_source=facebook", ref="KHONGCO")
    assert c.post("/training/api/student/register", json=b).status_code == 200     # mã sai: không báo lỗi
    sid = [x for x in c.get(f"/training/api/students?key={KEY}").json()["students"] if x["email"] == b["email"]][0]["id"]
    with Session(c.engine) as s:
        m = s.exec(select(TrnSignupMeta).where(TrnSignupMeta.account_type == "student", TrnSignupMeta.account_id == sid)).one()
    assert (m.utm_source, m.utm_medium, m.utm_content) == ("facebook", "group", "Bài ghim A")
    assert m.utm_campaign == camp.lower()[:80] and len(m.utm_campaign) == 80
    assert (m.ref_code_used, m.referrer_type, m.referrer_id) == ("", "", 0)


def test_dang_ky_khong_tham_so_van_chay(c):
    b = _sv()
    assert c.post("/training/api/student/register", json=b).status_code == 200
    k = _ks()
    assert c.post("/training/api/engineer/register", json=k).status_code == 200


# ---------------- báo cáo ----------------
def test_bao_cao_nguon_chien_dich_va_kpi_7_ngay(c, monkeypatch):
    tag = uuid.uuid4().hex[:8]
    src, camp = f"linkedin{tag}", f"camp-{tag}"
    # người giới thiệu là NHÂN VIÊN: vẫn được tính trong top
    loc = "nv" + tag
    monkeypatch.setattr(training, "EMP_DOMAINS", ["svws.test"])
    nv = c.post("/training/api/staff/login", json={"id": f"{loc}@svws.test", "password": loc}).json()
    ref = _ref_of(c, nv["token"])
    # 3 người được mời: A hoàn thành trong 7 ngày, B hoàn thành sau 7 ngày, K (kỹ sư) chưa hoàn thành
    a, bb = _sv(utm_source=src, utm_campaign=camp, ref=ref), _sv(utm_source=src, utm_campaign=camp, ref=ref)
    k = _ks(utm_source=src, utm_campaign=camp, ref=ref.lower())
    for x in (a, bb):
        c.post("/training/api/student/register", json=x)
    c.post("/training/api/engineer/register", json=k)
    _, la = _approve_login_sv(c, a)
    sid_b, lb = _approve_login_sv(c, bb)
    c.post("/training/api/results", json={"token": la["token"], "code": "NC01", "pct": 80})
    c.post("/training/api/results", json={"token": lb["token"], "code": "NC01", "pct": 95})
    c.post("/training/api/results", json={"token": lb["token"], "code": "NC02", "pct": 79})
    with Session(c.engine) as s:                                   # B đăng ký từ 10 ngày trước
        st = s.get(TrnStudent, sid_b); st.created = st.created - dt.timedelta(days=10); s.add(st); s.commit()
    # nhân viên cũng đăng ký qua link cùng nguồn -> KHÔNG được đếm
    c.post("/training/api/staff/register", json={"emp_code": "SV" + tag[:4].upper(), "full_name": "Nhân Viên Test",
                                                 "email": f"nv{tag}@svws.vn", "password": "matkhau1",
                                                 "agree_terms": True, "utm_source": src, "utm_campaign": camp})
    rep = _src(c)
    rows = [x for x in rep["by_source_week"] if x["utm_source"] == src]
    tot = {k2: sum(x[k2] for x in rows) for k2 in ("registered", "activated", "completed", "completed_7d")}
    assert tot == {"registered": 3, "activated": 2, "completed": 2, "completed_7d": 1}
    assert len({x["week"] for x in rows}) == 2                     # B rơi vào tuần khác (10 ngày trước)
    assert all(x["week"].count("-W") == 1 for x in rows)
    cr = [x for x in rep["by_campaign"] if x["utm_campaign"] == camp][0]
    assert (cr["registered"], cr["completed"], cr["completed_7d"]) == (3, 2, 1)
    top = [x for x in rep["top_referrers"] if x["ref_code"] == ref][0]
    assert (top["referrer_type"], top["referrer_code"]) == ("staff", loc.upper())
    assert (top["invited"], top["activated"], top["completed"], top["completed_7d"]) == (3, 2, 2, 1)
    assert rep["pass_pct"] == 80 and rep["kpi_days"] == 7 and len(rep["top_referrers"]) <= 20
    # lọc theo ngày: hôm nay -> chỉ A và K (B đăng ký 10 ngày trước)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=7)).date().isoformat()
    rows_today = [x for x in _src(c, **{"from": today, "to": today})["by_source_week"] if x["utm_source"] == src]
    assert sum(x["registered"] for x in rows_today) == 2
    assert c.get(f"/training/api/sources?key={KEY}&from=04-10-2026").status_code == 422
    assert c.get("/training/api/sources?key=sai").status_code == 403


def test_sources_csv_rieng_csv_diem_giu_nguyen(c):
    tag = uuid.uuid4().hex[:8]
    c.post("/training/api/student/register", json=_sv(utm_source=f"zalo{tag}", utm_campaign=f"oa-{tag}"))
    r = c.get(f"/training/api/sources.csv?key={KEY}")
    assert r.status_code == 200 and "nguon_dang_ky" in r.headers["content-disposition"]
    rows = list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))
    assert rows[0][:2] == ["Bảng", "Nguồn / chiến dịch / người giới thiệu"]
    assert any(x[0] == "Nguồn × tuần" and x[1] == f"zalo{tag}" for x in rows)
    assert any(x[0] == "Chiến dịch" and x[1] == f"oa-{tag}" for x in rows)
    assert rows[-1][0] == "Tổng"
    res = c.get(f"/training/api/results.csv?key={KEY}").content.decode("utf-8-sig").splitlines()[0]
    assert res == "Thời điểm (server UTC),Mã,Họ tên,Nhóm,Mã bài,Công nghệ,Điểm,%,Kết quả,Giờ máy học viên"


# ---------------- dọn khi xóa tài khoản ----------------
def test_xoa_tai_khoan_don_nguon_va_ma_gioi_thieu(c):
    tag = uuid.uuid4().hex[:8]
    inv = _sv(); c.post("/training/api/student/register", json=inv)
    sid_inv, li = _approve_login_sv(c, inv)
    ref = _ref_of(c, li["token"])
    guest = _sv(utm_source=f"tiktok{tag}", ref=ref); c.post("/training/api/student/register", json=guest)
    sid_g, lg = _approve_login_sv(c, guest)
    # người mời tự xóa: mã giới thiệu + nguồn của họ bị xóa; người được mời giữ dòng nhưng không còn liên kết
    assert c.post("/training/api/me/delete", json={"token": li["token"], "password": inv["password"]}).status_code == 200
    with Session(c.engine) as s:
        assert not s.exec(select(TrnRefCode).where(TrnRefCode.code == ref)).all()
        assert not s.exec(select(TrnSignupMeta).where(TrnSignupMeta.account_type == "student",
                                                      TrnSignupMeta.account_id == sid_inv)).all()
        mg = s.exec(select(TrnSignupMeta).where(TrnSignupMeta.account_type == "student",
                                                TrnSignupMeta.account_id == sid_g)).one()
        assert (mg.referrer_type, mg.referrer_id, mg.ref_code_used) == ("deleted", 0, ref)
    top = [x for x in _src(c)["top_referrers"] if x["ref_code"] == ref]
    assert top and top[0]["referrer_name"] == "(tài khoản đã xóa)" and top[0]["invited"] == 1
    # admin xóa người được mời: dọn y như vậy
    assert c.post("/training/api/students/action", json={"key": KEY, "id": sid_g, "action": "delete"}).status_code == 200
    with Session(c.engine) as s:
        assert not s.exec(select(TrnSignupMeta).where(TrnSignupMeta.account_type == "student",
                                                      TrnSignupMeta.account_id == sid_g)).all()
        assert not s.exec(select(TrnRefCode).where(TrnRefCode.account_type == "student",
                                                   TrnRefCode.account_id == sid_g)).all()
    assert not [x for x in _src(c)["by_source_week"] if x["utm_source"] == f"tiktok{tag}"]


def test_ky_su_xoa_cung_don_nguon(c):
    k = _ks(utm_source="workshop"); c.post("/training/api/engineer/register", json=k)
    eid = _id_of(c, k["email"])["id"]
    c.post("/training/api/engineers/action", json={"key": KEY, "id": eid, "action": "delete"})
    with Session(c.engine) as s:
        assert not s.exec(select(TrnSignupMeta).where(TrnSignupMeta.account_type == "engineer",
                                                      TrnSignupMeta.account_id == eid)).all()


def test_trang_dang_ky_giu_tham_so_trong_session_storage(c):
    html = c.get("/training/register").text
    assert "sessionStorage" in html and "svws_trn_src" in html and "Object.assign(b,srcGet())" in html


# ---------------- "đã kích hoạt" theo mốc kích hoạt ----------------
def _meta(c, atype, aid):
    with Session(c.engine) as s:
        return s.exec(select(TrnSignupMeta).where(TrnSignupMeta.account_type == atype,
                                                  TrnSignupMeta.account_id == aid)).one()


def test_moc_kich_hoat_ghi_khi_otp_va_khi_admin_duyet(c, monkeypatch):
    # OTP (kỹ sư email doanh nghiệp)
    sent = {}
    monkeypatch.setattr(training, "OTP_MODE", True)
    monkeypatch.setattr(training, "send_otp", lambda e, code: sent.update({e: code}) or True)
    k = _ks(); c.post("/training/api/engineer/register", json=k)
    eid = _id_of(c, k["email"])["id"]
    assert _meta(c, "engineer", eid).activated_at is None
    c.post("/training/api/engineer/verify", json={"email": k["email"], "otp": sent[k["email"]]})
    assert _meta(c, "engineer", eid).activated_at is not None
    # admin duyệt (sinh viên); khóa rồi duyệt lại -> giữ mốc LẦN ĐẦU
    monkeypatch.setattr(training, "OTP_MODE", False)
    b = _sv(); c.post("/training/api/student/register", json=b)
    sid, _ = _approve_login_sv(c, b)
    first = _meta(c, "student", sid).activated_at
    assert first is not None
    for act in ("block", "approve"):
        c.post("/training/api/students/action", json={"key": KEY, "id": sid, "action": act})
    assert _meta(c, "student", sid).activated_at == first


def test_bi_khoa_sau_khi_kich_hoat_van_tinh_va_loc_theo_moc(c):
    tag = uuid.uuid4().hex[:8]
    src = f"youtube{tag}"
    a, p = _sv(utm_source=src), _sv(utm_source=src)          # a: kích hoạt rồi bị khóa; p: còn chờ duyệt
    for x in (a, p):
        c.post("/training/api/student/register", json=x)
    sid_a, _ = _approve_login_sv(c, a)
    c.post("/training/api/students/action", json={"key": KEY, "id": sid_a, "action": "block"})
    rows = [x for x in _src(c)["by_source_week"] if x["utm_source"] == src]
    assert (sum(x["registered"] for x in rows), sum(x["activated"] for x in rows)) == (2, 1)
    # đăng ký 10 ngày trước, kích hoạt 2 ngày trước: lọc tới 5 ngày trước -> đã đăng ký nhưng CHƯA kích hoạt
    now = dt.datetime.utcnow()
    with Session(c.engine) as s:
        st = s.get(TrnStudent, sid_a); st.created = now - dt.timedelta(days=10); s.add(st)
        m = s.exec(select(TrnSignupMeta).where(TrnSignupMeta.account_type == "student",
                                               TrnSignupMeta.account_id == sid_a)).one()
        m.activated_at = now - dt.timedelta(days=2); s.add(m); s.commit()
    to = (now + dt.timedelta(hours=7) - dt.timedelta(days=5)).date().isoformat()
    rows = [x for x in _src(c, to=to)["by_source_week"] if x["utm_source"] == src]
    assert (sum(x["registered"] for x in rows), sum(x["activated"] for x in rows)) == (1, 0)


def test_tai_khoan_co_truoc_khi_co_bang_nguon_lay_ngay_tao_neu_dang_active(c):
    def unknown():
        rows = [x for x in _src(c)["by_source_week"] if x["utm_source"].startswith("(không rõ")]
        return sum(x["registered"] for x in rows), sum(x["activated"] for x in rows)
    r0, a0 = unknown()
    with Session(c.engine) as s:                     # tài khoản cũ: KHÔNG có dòng trn_signup_meta
        for status in ("active", "pending", "blocked"):
            salt = "s"
            s.add(TrnStudent(full_name="Cũ " + status, phone="0913" + str(uuid.uuid4().int)[:6],
                             email=f"old{status}{uuid.uuid4().hex[:6]}@gmail.com", school="X", course="K", salt=salt,
                             pw_hash=training.hash_pw("matkhau1", salt), status=status,
                             student_code=f"SVU-O{uuid.uuid4().hex[:4]}"))
        s.commit()
    r1, a1 = unknown()
    assert (r1 - r0, a1 - a0) == (3, 1)              # chỉ tài khoản đang active được tính là đã kích hoạt
