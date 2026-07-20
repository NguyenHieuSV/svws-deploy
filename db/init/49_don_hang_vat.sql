-- 49_don_hang_vat.sql — VAT theo dòng cho ĐƠN HÀNG BÁN (đối xứng đơn mua).
-- Trước đây đơn bán chỉ lưu tổng chưa VAT; VAT áp phẳng 8% khi xuất kho.
-- Nay: VAT theo từng dòng (mỗi mặt hàng một mức %); tong_tien GIỮ nghĩa "tiền hàng
-- chưa VAT", thêm tien_thue = tổng VAT; khi xuất kho dùng tien_thue thật thay 8% phẳng.
ALTER TABLE don_hang_ct ADD COLUMN IF NOT EXISTS thue_suat NUMERIC(5,2) NOT NULL DEFAULT 0;
ALTER TABLE don_hang ADD COLUMN IF NOT EXISTS tien_thue NUMERIC(18,0) NOT NULL DEFAULT 0;
-- Đơn cũ: giữ đúng hành vi VAT 8% (mức đã áp phẳng trước đây) — lưu lại tường minh.
UPDATE don_hang_ct SET thue_suat = 8 WHERE thue_suat = 0;
UPDATE don_hang SET tien_thue = ROUND(tong_tien * 0.08) WHERE tien_thue = 0;
