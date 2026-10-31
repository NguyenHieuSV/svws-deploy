-- 163 — 🏷 BOQ dự án lên ngang Dự toán hàng bán (anh Hiếu 31/10/2026, mục 5 rà logic): dòng BOQ có nhà cung cấp ·
--       mã SP · spec · nhà sản xuất · liên kết danh mục Sản phẩm NCC (cùng form, cùng tìm danh mục, cùng ghi ngược có kiểm
--       soát, cùng mẫu BOQ 12 cột). Mục 4 (audit mọi thay đổi dòng dự toán) ghi vào audit_log, không cần cột mới.
ALTER TABLE du_an_du_toan ADD COLUMN IF NOT EXISTS nha_cung_cap_id BIGINT REFERENCES nha_cung_cap(id) ON DELETE SET NULL;
ALTER TABLE du_an_du_toan ADD COLUMN IF NOT EXISTS ncc_ten         VARCHAR(200);
ALTER TABLE du_an_du_toan ADD COLUMN IF NOT EXISTS ma_sp           VARCHAR(60);
ALTER TABLE du_an_du_toan ADD COLUMN IF NOT EXISTS spec            TEXT;
ALTER TABLE du_an_du_toan ADD COLUMN IF NOT EXISTS nha_san_xuat    VARCHAR(150);
ALTER TABLE du_an_du_toan ADD COLUMN IF NOT EXISTS san_pham_ncc_id BIGINT;
ALTER TABLE du_an_du_toan ALTER COLUMN quy_cach TYPE TEXT;           -- mẫu BOQ / AI ghi quy cách dài hơn 300 ký tự
