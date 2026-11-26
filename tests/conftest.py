"""
Dùng chung cho mọi test: bảng có cột JSONB (PostgreSQL) dựng được trên SQLite trong bộ nhớ (JSONB → JSON).
Trước đây hook này nằm trong test_dao_tao.py nên chạy LẺ một file khác (vd pytest tests/test_bao_gia_phien_ban.py) bị lỗi
«can't render element of type JSONB»; đặt ở conftest để chạy file nào cũng được.
"""
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles


@compiles(JSONB, "sqlite")
def _jsonb_sqlite(t, c, **k):
    return "JSON"


import pytest


@pytest.fixture(autouse=True)
def _khong_goi_cong_hddt(monkeypatch):
    """Không test nào được gọi mạng thật tới cổng hóa đơn điện tử (app/hddt_tai_ve.py tự tải theo link / mã, mig 171):
    mặc định mọi lần tải đều «không kết nối được». Test của phần tự tải truyền `lay=` giả hoặc tự monkeypatch lại."""
    def _tat(url):
        raise ValueError("không kết nối được cổng (test tắt mạng)")
    import app.hddt_tai_ve as tv
    if not hasattr(tv, "_lay_http_goc"):
        tv._lay_http_goc = tv._lay_http            # bản thật — test kiểm chặn chuyển hướng gọi thẳng với opener giả
    monkeypatch.setattr(tv, "_lay_http", _tat)
    yield
