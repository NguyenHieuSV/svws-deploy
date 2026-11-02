"""Mở file thiết kế HTML (chuẩn 3D Design) trên máy khác bằng đường link.

Mỗi dự án là một thư mục `static/thiet-ke/<khoa>/` chứa các file .html (mỗi Rev một file).
`<khoa>` là chuỗi ngẫu nhiên khó đoán — ai có link mới mở được, không có trang liệt kê.

- GET /thiet-ke/<khoa>          → bản MỚI NHẤT trong thư mục (link cố định gửi khách, lên Rev không đổi link)
- GET /thiet-ke/<khoa>/<ten>    → đúng một file (giữ link của từng Rev)

Thêm/cập nhật: chép file .html vào thư mục rồi commit + push (GitHub Desktop), Render tự build lại.
Xem static/thiet-ke/README.md.
"""
import os
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(tags=["Thiết kế (link xem)"])

_GOC = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", "static", "thiet-ke"))
_KHOA = re.compile(r"^[A-Za-z0-9-]{12,64}$")
_TEN = re.compile(r"^[A-Za-z0-9._-]{1,120}\.html$")
# no-cache: luôn hỏi lại server → mở link là thấy bản mới ngay sau deploy; không cho máy tìm kiếm lập chỉ mục.
_HEADERS = {"Cache-Control": "no-cache", "X-Robots-Tag": "noindex, nofollow", "Referrer-Policy": "no-referrer"}


def _thu_muc(khoa: str) -> str:
    if not _KHOA.match(khoa):
        raise HTTPException(404, "Không có thiết kế này")
    d = os.path.realpath(os.path.join(_GOC, khoa))
    if os.path.dirname(d) != _GOC or not os.path.isdir(d):
        raise HTTPException(404, "Không có thiết kế này")
    return d


def _tra_file(d: str, ten: str) -> FileResponse:
    p = os.path.realpath(os.path.join(d, ten))
    if os.path.dirname(p) != d or not os.path.isfile(p):
        raise HTTPException(404, "Không có file này")
    return FileResponse(p, media_type="text/html; charset=utf-8", headers=_HEADERS)


def _khoa_rev(ten: str):
    """Khoá sắp xếp theo Rev ở cuối tên (…_RevA < …_RevB < …_RevZ < …_RevAA); không có Rev thì theo tên."""
    m = re.search(r"_Rev([A-Za-z]+)\.html$", ten)
    r = m.group(1).upper() if m else ""
    return (len(r), r, ten)


def ban_moi_nhat(d: str) -> str | None:
    """File .html có Rev lớn nhất trong thư mục. Không dựa vào giờ sửa file vì Render dựng lại
    từ git thì mọi file cùng một giờ."""
    ds = [f for f in os.listdir(d) if _TEN.match(f)]
    return max(ds, key=_khoa_rev) if ds else None


@router.api_route("/thiet-ke/{khoa}", methods=["GET", "HEAD"], include_in_schema=False)
def mo_moi_nhat(khoa: str):
    d = _thu_muc(khoa)
    ten = ban_moi_nhat(d)
    if not ten:
        raise HTTPException(404, "Thư mục chưa có file thiết kế")
    return _tra_file(d, ten)


@router.api_route("/thiet-ke/{khoa}/{ten}", methods=["GET", "HEAD"], include_in_schema=False)
def mo_file(khoa: str, ten: str):
    if not _TEN.match(ten):
        raise HTTPException(404, "Không có file này")
    return _tra_file(_thu_muc(khoa), ten)
