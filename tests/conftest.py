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
