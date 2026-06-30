# CLAUDE.md — Hướng dẫn cho Claude Code (và người mới)

Backend hợp nhất cho Song Việt Water Solutions (SVWS). **FastAPI + SQLAlchemy 2.0 + PostgreSQL**,
kiến trúc *modular monolith*: một CSDL, nhiều module, dùng chung phân quyền & dữ liệu.

## Chạy nhanh
```bash
make db-up      # PostgreSQL qua docker, tự nạp schema+seed lần đầu (db/init/01..05)
make setup      # venv + cài thư viện
make seed       # 13 user demo, mật khẩu: matkhau123
make run        # http://localhost:8000/docs
make test       # pytest đầu-cuối (cần DB chạy)
```
Không dùng docker: tự tạo DB `svws`, chạy lần lượt `SVWS_schema.sql`, `SVWS_seed_rbac.sql`,
`SVWS_schema_duan_ext.sql`, `SVWS_schema_nhansu_ext.sql`, `SVWS_schema_crm_ext.sql`.

## Bố cục
```
app/
  models.py        ORM khớp các file SQL (nguồn sự thật của schema là *.sql)
  rbac.py          ★ 3 primitive phân quyền (xem dưới)
  kho_service.py   xuất/nhập tồn dùng chung
  hach_toan.py     bút toán kép VAS
  hddt_gateway.py  cổng HĐĐT thay-thế-được (MISA/VNPT/Viettel)
  audit.py         ghi audit_log
  routers/         mỗi module 1 file: kho, ncc, du_an, ban_hang, ke_toan,
                   tai_chinh, nhan_su, cho_thue, crm
```

## 3 primitive phân quyền — LUÔN dùng lại, KHÔNG hard-code quyền trong route
- `yeu_cau(module, "XEM|THAO_TAC|DUYET|QUAN_TRI")` — theo bảng `phan_quyen`.
- `kiem_han_muc(db, nguoi_dung, loai, so_tien)` — trần tiền theo `han_muc_duyet` (PO/chi phí DA/báo giá).
- `chi_vai_tro("KTT","CEO")` — bước gắn đúng vai trò (duyệt lương).

## Công thức thêm MODULE mới
1. Thêm bảng vào file `.sql` (nguồn sự thật) + model tương ứng trong `models.py`.
2. Tạo `routers/<module>.py`, đặt `MODULE = "<khoá>"` (khớp cột `phan_quyen.module`).
3. Mỗi endpoint: `Depends(yeu_cau(MODULE, "<mức>"))`; thao tác tiền dùng `kiem_han_muc`.
4. Ghi `ghi_audit(...)` trước mọi `db.commit()` có thay đổi dữ liệu.
5. `include_router` trong `main.py`. Thêm quyền cho vai trò vào `SVWS_seed_rbac.sql`.
6. Viết test trong `tests/`.

## Quy ước
- Định danh bảng/cột: ASCII snake_case tiếng Việt không dấu (`khach_hang`, `chi_phi_thuc_te`).
- Tiền: `NUMERIC(18,0)` VND. Giao dịch nhiều bước → một transaction (commit cuối).
- Trạng thái duyệt dùng enum `trang_thai_duyet`.

## Còn phải làm (ưu tiên)
1. Scheduler chạy nền: `cho-thue/chay-thu-phi-dinh-ky`, nhắc hết hạn/quá hạn, dashboard 8h.
2. Thay `FakeProvider` HĐĐT bằng SDK thật; thuế suất theo mặt hàng; trần BHXH; prorate lương theo công.
3. Frontend Next.js (PWA) đọc `phan_quyen` để ẩn/hiện module theo vai trò.
4. Module phụ: Quản lý tài liệu (bản vẽ/HĐ có phiên bản), Dashboard CEO real-time.
