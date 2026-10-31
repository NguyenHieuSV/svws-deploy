# CLAUDE.md — Hướng dẫn cho Claude Code (và người mới)

Backend hợp nhất cho Song Việt Water Solutions (SVWS). **FastAPI + SQLAlchemy 2.0 + PostgreSQL**,
kiến trúc *modular monolith*: một CSDL, nhiều module, dùng chung phân quyền & dữ liệu.
Chạy thật tại https://svws-app-iit7.onrender.com (Render, Docker).

## Cách làm việc trong một phiên Claude Code
- Giao tiếp tiếng Việt; người giao việc là anh Hiếu (Giám đốc), xưng "anh", gọi Claude là "em".
- **Mỗi phiên = một việc = một branch = một PR.** Không gộp nhiều tính năng không liên quan vào một PR.
- Trước khi sửa: đọc file liên quan, nêu ngắn gọn sẽ đổi gì. Sau khi sửa: chạy test (`make test`
  nếu có DB; tối thiểu `python -c "import app.main"` để chắc app khởi động được) rồi mới commit.
- Mô tả PR bằng tiếng Việt: sửa gì, vì sao, cách kiểm tra, có migration mới hay không.
- Không commit bí mật (.env, API key, mật khẩu, file JSON service account). Biến môi trường
  khai báo trên Render → Environment, mẫu ghi vào `.env.example`.
- anh Hiếu dùng **Windows + GitHub Desktop**: không tạo 2 file chỉ khác chữ hoa/thường
  (Windows coi là một file). Giao diện training dùng đúng `static/training/index.html` (chữ thường).
- Không đưa file chạy thử / file nhị phân rác vào repo (vd `training.db`,
  `app/*.zip`); thêm vào `.gitignore` khi gặp.

## Chạy nhanh
```bash
make db-up      # PostgreSQL qua docker, tự nạp db/init/*.sql lần đầu
make setup      # venv + cài thư viện (requirements-dev.txt có pytest, httpx)
make seed       # 13 user demo, mật khẩu: matkhau123
make run        # http://localhost:8000/docs
make test       # pytest (test_e2e cần DB chạy, tự skip nếu không có DB)
```

## Triển khai (Render)
- `Dockerfile` → `start.sh`: áp dụng lần lượt `db/init/*.sql` chưa có trong bảng `_migrations`,
  tạo user demo (tắt bằng `SEED_DEMO=0`), quản trị tài khoản theo `DEMO_PASSWORD` / `ADMIN_*`,
  rồi chạy `uvicorn app.main:app`.
- Push lên `main` là Render tự build lại. Kiểm tra `/health` sau khi deploy.
- 💾 Sao lưu: `app/sao_luu_service.py` mỗi ngày (từ `SAO_LUU_GIO`, giờ VN) đóng gói toàn bộ bảng thành ZIP
  (manifest + schema db/init + CSV từng bảng + pg_dump nếu được) lên kho tệp R2/B2, nhật ký ở bảng `sao_luu_log`,
  panel Cấu hình → 💾 Sao lưu dữ liệu (CEO/ADMIN; tải file chỉ CEO). Khôi phục:
  `python -m scripts.khoi_phuc_sao_luu <zip> --database-url …` (tạo schema từ ZIP rồi nạp CSV).
- Tệp đính kèm: `app/luu_tru.py` lưu lên object storage S3-compatible (Backblaze B2) khi có
  `R2_ENDPOINT / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY / R2_BUCKET`; thiếu thì lưu đĩa cục bộ.
- Cấu hình chung đọc từ biến môi trường qua `app/config.py` (email, IMAP, AI, Google Chat webhook…).

## Migration (db/init)
- Mỗi thay đổi schema = **một file mới** `db/init/<số>_<ten>.sql`, số tiếp theo sau file lớn nhất.
  Không sửa file đã chạy trên production (tên file là khoá trong `_migrations`).
- Viết idempotent: `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`…
- **Thứ tự:** `start.sh` sắp file bằng `sort -V` (theo số: `99_` trước `100_`). Đừng đổi lại
  `sort` thường — khi đó `100_…` trở lên chạy trước `10_…`–`99_…` và CSDL mới sẽ lỗi
  (vd `100_hdc_don_hang.sql` ALTER bảng tạo ở `96_kt_hoa_don_cho.sql`).
- ⚠ `make db-up` nạp `db/init` qua `docker-entrypoint-initdb.d` của Postgres, vẫn sắp theo chữ
  → dựng DB dev mới bằng cách này có thể lỗi ở các file `100_` trở lên; chưa sửa trong PR này.
- Hiện có 2 file cùng số `73_` (`73_khoan_vay_chu_ky_ngay`, `73_vai_tro_tp_qlnb`) — không đổi tên
  (đã ghi trong `_migrations`); file mới luôn lấy số lớn nhất + 1.
- Các file `SVWS_schema*.sql` ở gốc là bản gốc ban đầu; nguồn thật hiện nay là `db/init/`.

## Bố cục
```
app/
  main.py          lắp ráp app: include_router + các hook startup (scheduler, registry…)
  models.py        ORM khớp các file SQL
  rbac.py          ★ 3 primitive phân quyền (xem dưới)
  kho_service.py   xuất/nhập tồn dùng chung
  hach_toan.py     bút toán kép VAS
  hddt_gateway.py  cổng HĐĐT thay-thế-được (MISA/VNPT/Viettel)
  ai_gateway.py    cổng AI (Fake offline / Anthropic khi AI_PROVIDER=ANTHROPIC)
  chat_gateway.py  gửi Google Chat (webhook / app)
  scheduler.py     luồng nền trong tiến trình web (bản tin nhắc việc đầu ngày)
  luu_tru.py       lưu tệp: B2/S3 hoặc đĩa
  audit.py         ghi audit_log
  routers/         mỗi module 1 file: auth, kho, ncc, du_an, ban_hang(+_ext), ke_toan(+_quy),
                   tai_chinh, nhan_su(+_kpi), cho_thue(+_ops), crm, vay, quy_trich_lap,
                   cau_hinh, dich_vu_kt, quet_mail, doc_anh_bcvh
training.py        module Đào tạo /training (SQLModel, tự chứa) — giao diện static/training/index.html
svws_registry/     module Design Registry /registry (chuẩn 3D Design & sổ đăng ký thiết kế, gọi Claude API phía server)
static/            pwa/ (manifest, service worker), chup-anh.html, training/
svws_app.html      giao diện chính; huong_dan.html; so_tay_quy_che.docx → quy_che_toan_van.json
                   (sinh bằng scripts/tach_quy_che.py)
```
Hai module `training.py` và `svws_registry/` dùng SQLModel và tự tạo bảng khi khởi động
(không qua `db/init`); khi sửa giao diện training nhớ tăng version Service Worker.

## 3 primitive phân quyền — LUÔN dùng lại, KHÔNG hard-code quyền trong route
- `yeu_cau(module, "XEM|THAO_TAC|DUYET|QUAN_TRI")` — theo bảng `phan_quyen`.
- `kiem_han_muc(db, nguoi_dung, loai, so_tien)` — trần tiền theo `han_muc_duyet` (PO/chi phí DA/báo giá).
- `chi_vai_tro("KTT","CEO")` — bước gắn đúng vai trò (duyệt lương).

## Công thức thêm MODULE mới
1. Thêm migration `db/init/<số>_<ten>.sql` + model tương ứng trong `models.py`.
2. Tạo `routers/<module>.py`, đặt `MODULE = "<khoá>"` (khớp cột `phan_quyen.module`).
3. Mỗi endpoint: `Depends(yeu_cau(MODULE, "<mức>"))`; thao tác tiền dùng `kiem_han_muc`.
4. Ghi `ghi_audit(...)` trước mọi `db.commit()` có thay đổi dữ liệu.
5. `include_router` trong `main.py`. Thêm quyền cho vai trò bằng migration (seed RBAC).
6. Viết test trong `tests/`.
7. Hook startup mới phải bọc `try/except` và chỉ `print` lỗi — KHÔNG được chặn app khởi động.

## Quy ước
- Định danh bảng/cột: ASCII snake_case tiếng Việt không dấu (`khach_hang`, `chi_phi_thuc_te`).
- Tiền: `NUMERIC(18,0)` VND. Giao dịch nhiều bước → một transaction (commit cuối).
- Trạng thái duyệt dùng enum `trang_thai_duyet`.
- Giờ hệ thống tính theo Việt Nam (UTC+7, `tz_offset_gio`).
- Giao diện tiếng Việt; logo SVWS dùng đúng file gốc (base64), không vẽ lại bằng CSS/SVG.

## Còn phải làm (ưu tiên — rà lại khi bắt đầu phiên)
1. Scheduler: đã có bản tin nhắc việc; còn `cho-thue/chay-thu-phi-dinh-ky`, nhắc hết hạn/quá hạn.
2. Thay `FakeProvider` HĐĐT bằng SDK thật; thuế suất theo mặt hàng; trần BHXH; prorate lương theo công.
3. Frontend Next.js (PWA) đọc `phan_quyen` để ẩn/hiện module theo vai trò.
4. Module phụ: Quản lý tài liệu (bản vẽ/HĐ có phiên bản), Dashboard CEO real-time.
