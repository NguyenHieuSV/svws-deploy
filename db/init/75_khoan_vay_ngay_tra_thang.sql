-- Khế ước vay: ngày trả cố định hàng tháng (VD: 26 = trả vào ngày 26 mỗi tháng).
-- NULL = lịch tính theo chu_ky_ngay như cũ.
ALTER TABLE khoan_vay ADD COLUMN IF NOT EXISTS ngay_tra_thang INT;
