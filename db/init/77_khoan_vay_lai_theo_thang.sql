-- Khế ước vay: cách tính lãi THEO THÁNG (lãi kỳ = dư nợ x lãi năm / 12),
-- thay vì theo số ngày thực. FALSE/NULL = tính theo ngày như cũ.
ALTER TABLE khoan_vay ADD COLUMN IF NOT EXISTS lai_theo_thang BOOLEAN DEFAULT FALSE;
