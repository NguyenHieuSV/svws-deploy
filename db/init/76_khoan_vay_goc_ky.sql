-- Khế ước vay: số tiền GỐC trả cố định mỗi kỳ (VD 10.600.000đ/tháng);
-- kỳ cuối tự trả phần còn lại. NULL = chia gốc đều theo số kỳ như cũ.
ALTER TABLE khoan_vay ADD COLUMN IF NOT EXISTS goc_ky NUMERIC(18,0);
