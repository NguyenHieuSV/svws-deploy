# SVWS Design Registry — Hướng dẫn triển khai (Mức 3)

Module "Chuẩn 3D Design & Sổ đăng ký thiết kế" gắn vào backend FastAPI + PostgreSQL
hiện có của SVWS (repo `svws-deploy`, chạy trên Render).

## 1. Nội dung thư mục

```
svws_registry/
├── registry.py            # Router FastAPI + SQLModel (toàn bộ backend)
├── registry_seed.json     # Dữ liệu khởi tạo: Rev.E (28 yêu cầu + 8 thiết kế + logo)
├── static/
│   └── registry.html      # Giao diện app (single-file, IBM Plex navy-cyan)
└── README.md
```

## 2. Cài đặt (3 bước)

**Bước 1 — Copy thư mục** `svws_registry/` vào gốc repo `svws-deploy`
(ngang hàng với `main.py`). Thêm file rỗng `svws_registry/__init__.py` nếu muốn
import kiểu package (không bắt buộc nếu để `registry.py` tự chứa).

**Bước 2 — Sửa `main.py`**, thêm:

```python
from svws_registry import registry

app.include_router(registry.router)

@app.on_event("startup")
def _init_registry():
    registry.init_db()   # tạo bảng + nạp seed Rev.E nếu DB trống
```

Nếu app đang dùng lifespan thay cho on_event thì gọi `registry.init_db()`
trong lifespan startup.

**Bước 3 — Render → Environment**, thêm biến:

```
ANTHROPIC_API_KEY = sk-ant-...     (bắt buộc cho nút AI)
ANTHROPIC_MODEL   = claude-sonnet-5   (tùy chọn, đây là mặc định)
```

`DATABASE_URL` dùng chung biến sẵn có của app (Render tự cấp).
`requirements.txt`: fastapi, sqlmodel, httpx — repo hiện tại đã có đủ
(httpx nếu thiếu thì thêm `httpx>=0.24`).

Push code → Render tự deploy. Mở:

```
https://svws-app-iit7.onrender.com/registry
```

## 3. Bảng dữ liệu tạo mới (không đụng bảng hiện có)

| Bảng | Vai trò |
|---|---|
| `svws_registry_doc` | 1 dòng duy nhất — nguồn chuẩn hiện hành (JSONB) |
| `svws_registry_revision` | Snapshot mỗi lần lưu (tối đa 300 bản) — lịch sử & khôi phục |

## 4. API

| Method | Đường dẫn | Chức năng |
|---|---|---|
| GET | `/registry` | Giao diện app |
| GET | `/registry/api` | Lấy toàn bộ tài liệu |
| PUT | `/registry/api` | Lưu (kèm `base_updated_at` chống ghi đè — trả `conflict:true` nếu người khác vừa lưu) |
| GET | `/registry/api/history` | Danh sách các lần lưu (ai, lúc nào) |
| GET | `/registry/api/history/{id}` | Xem 1 bản snapshot |
| POST | `/registry/api/restore/{id}` | Khôi phục về bản cũ |
| POST | `/registry/api/ai` | AI phân tích phiếu thiết kế (server gọi Anthropic — key không lộ ra trình duyệt) |

## 5. Quy trình sử dụng

1. Kỹ sư mở `/registry`, nhập tên (ghi vào lịch sử), thêm yêu cầu mới → nhãn cam "ĐỀ XUẤT MỚI"
2. Giám đốc bấm nhãn để duyệt → xanh "CHUẨN HIỆN HÀNH"
3. Tab "Các thiết kế": lập phiếu → 🤖 AI hỏi thông tin thiếu → trả lời → ghép đề bài → Copy dán cho Claude tạo tool
4. Nút 🕘 Lịch sử: xem ai sửa gì lúc nào, khôi phục khi cần
5. Xuất/Nhập JSON: đồng bộ 2 chiều với bản HTML offline (định dạng Rev.E y hệt)

## 6. Bảo mật (nên làm)

App hiện mở cho ai có link. Nếu backend đã có auth (VD dependency
`get_current_user`), khóa lại bằng cách sửa 1 dòng trong `registry.py`:

```python
router = APIRouter(prefix="/registry", tags=["SVWS Design Registry"],
                   dependencies=[Depends(get_current_user)])
```

(import dependency từ module auth hiện có của app).

## 7. Nâng cấp về sau (đã chừa sẵn đường)

- Lưu file tool HTML do AI tạo vào Backblaze B2, gắn link vào phiếu thiết kế
- Đẩy công đoạn thi công A→B (Tab 5 của các tool) sang app quản lý dự án để giao việc
- Endpoint AI thứ hai: tạo thẳng tool HTML phía server (job nền, vì thời gian tạo dài)
