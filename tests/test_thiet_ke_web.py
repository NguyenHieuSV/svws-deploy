"""Link xem file thiết kế HTML: /thiet-ke/<khoa>[/<ten>].
Chỉ lắp router này vào app riêng nên KHÔNG cần CSDL (app.main nối Postgres ngay khi import)."""
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import thiet_ke_web

_app = FastAPI()
_app.include_router(thiet_ke_web.router)
client = TestClient(_app)


@pytest.fixture()
def goc_tam(tmp_path, monkeypatch):
    goc = tmp_path / "thiet-ke"
    d = goc / "duan-abcdef123456"
    d.mkdir(parents=True)
    (d / "MA-THU_RevA.html").write_text("<html>A</html>", encoding="utf-8")
    (d / "MA-THU_RevB.html").write_text("<html>B</html>", encoding="utf-8")
    (d / "ghi-chu.txt").write_text("khong phuc vu", encoding="utf-8")
    (goc / "bi-mat.html").write_text("ngoai thu muc", encoding="utf-8")
    monkeypatch.setattr(thiet_ke_web, "_GOC", os.path.realpath(goc))
    return goc


def test_link_co_dinh_mo_rev_moi_nhat(goc_tam):
    r = client.get("/thiet-ke/duan-abcdef123456")
    assert r.status_code == 200 and r.text == "<html>B</html>"
    assert r.headers["content-type"].startswith("text/html")
    assert "noindex" in r.headers["x-robots-tag"]


def test_mo_dung_mot_rev(goc_tam):
    assert client.get("/thiet-ke/duan-abcdef123456/MA-THU_RevA.html").text == "<html>A</html>"


def test_chan_file_khong_phai_html_va_khoa_sai(goc_tam):
    assert client.get("/thiet-ke/duan-abcdef123456/ghi-chu.txt").status_code == 404
    assert client.get("/thiet-ke/khong-co-thu-muc-nay").status_code == 404
    assert client.get("/thiet-ke/ngan").status_code == 404
    assert client.get("/thiet-ke/duan-abcdef123456/..%2Fbi-mat.html").status_code == 404


def test_thu_tu_rev():
    ks = ["X_RevB.html", "X_RevAA.html", "X_RevA.html", "X_RevZ.html"]
    assert sorted(ks, key=thiet_ke_web._khoa_rev) == ["X_RevA.html", "X_RevB.html", "X_RevZ.html", "X_RevAA.html"]


def test_file_that_trong_repo_mo_duoc():
    r = client.get("/thiet-ke/agt1500-aLLkZoPFmYs")
    assert r.status_code == 200
    assert "SVWS-DV-AGT-1500WW-1026" in r.text[:20000]
