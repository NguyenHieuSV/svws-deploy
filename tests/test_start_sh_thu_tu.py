"""
start.sh phải nạp db/init/*.sql theo THỨ TỰ SỐ của tiền tố (19_ trước 126_). Theo thứ tự chữ thì 100_…
chạy ngay sau 09_, khi bảng nó cần chưa có -> DB mới tạo bị lỗi. Không cần DB: chạy đúng lệnh liệt kê
trong start.sh rồi kiểm thứ tự.
"""
import os
import re
import subprocess

ROOT = os.path.join(os.path.dirname(__file__), "..")


def _thu_tu_trong_start_sh():
    with open(os.path.join(ROOT, "start.sh"), encoding="utf-8") as f:
        m = re.search(r"for f in \$\((ls db/init/\*\.sql[^)]*)\); do", f.read())
    assert m, "không tìm thấy vòng nạp migration trong start.sh"
    out = subprocess.run(["bash", "-c", m.group(1)], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [os.path.basename(x) for x in out.split()]


def test_nap_migration_theo_thu_tu_so():
    files = _thu_tu_trong_start_sh()
    assert len(files) == len([x for x in os.listdir(os.path.join(ROOT, "db/init")) if x.endswith(".sql")])
    so = [int(x.split("_", 1)[0]) for x in files]
    assert so == sorted(so), "thứ tự sai: " + ", ".join(files[i] for i in range(1, len(so)) if so[i] < so[i - 1])
    assert files.index("19_cho_thue_ops.sql") < files.index("126_hd_cho_thue.sql")
    assert files.index("99_hdc_tra_cuu.sql") < files.index("100_hdc_don_hang.sql")
