-- 169 — 📧 Hàng chờ hóa đơn mua từ email: đọc thư cổng HĐĐT THEO NHÃN (EasyInvoice / Softdreams, MISA, VNPT…) — anh Hiếu 05/11/2026.
--       Lưu thêm ký hiệu mẫu số · MST bên bán (khớp hồ sơ NCC theo MST) · mã cơ quan thuế · nguồn đọc (NHAN | AI | REGEX)
--       · dòng trùng (cùng NCC + số hóa đơn đến từ 2 thư của cổng) → BO_QUA và trỏ về dòng giữ lại.
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS ky_hieu      VARCHAR(20);
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS ncc_mst      VARCHAR(20);
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS ma_cqt       VARCHAR(40);
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS nguon_doc    VARCHAR(12);
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS trung_voi_id BIGINT;
