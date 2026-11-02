# File thiết kế HTML mở bằng link (chuẩn 3D Design)

Mỗi dự án là một thư mục con có tên ngẫu nhiên (khoá), ví dụ `agt1500-aLLkZoPFmYs/`.
Ai có link mới mở được; máy chủ không có trang liệt kê các thư mục.

| Link | Mở ra |
|---|---|
| `https://svws-app-iit7.onrender.com/thiet-ke/<khoá>` | Bản Rev mới nhất trong thư mục (link cố định để gửi khách) |
| `https://svws-app-iit7.onrender.com/thiet-ke/<khoá>/<tên file>.html` | Đúng một Rev |

## Đưa Rev mới lên
1. Chép file `.html` mới vào đúng thư mục dự án, đặt tên theo mẫu `<Mã thiết kế>_Rev<x>.html`
   (vd `SVWS-DV-AGT-1500WW-1026_RevB.html`). Giữ file Rev cũ nếu cần đối chiếu.
2. GitHub Desktop: commit + push lên `main` (hoặc PR). Render tự build lại sau vài phút.
3. Link cố định tự trỏ sang Rev lớn nhất (RevA < RevB < … < RevZ < RevAA).

## Thêm dự án mới
Tạo thư mục mới, tên = `<mã ngắn>-<chuỗi ngẫu nhiên ≥ 8 ký tự>` (chỉ chữ, số, dấu `-`; tổng 12–64 ký tự).
Không dùng tên dễ đoán vì link là cách bảo vệ duy nhất.

## Lưu ý
- File có báo giá (Tab 14) và đơn giá BOQ: tắt "Hiển thị giá" ở Tab 12 trước khi xuất file gửi Chủ đầu tư nếu không muốn lộ giá.
- Muốn thu hồi link: xoá thư mục (hoặc đổi tên thư mục) rồi push.
