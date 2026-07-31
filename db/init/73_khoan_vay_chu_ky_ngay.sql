-- Chu kỳ trả nợ vay tính theo NGÀY (thay cho tháng); khoản vay cũ quy đổi = tháng x 30
ALTER TABLE khoan_vay ADD COLUMN IF NOT EXISTS chu_ky_ngay integer;
UPDATE khoan_vay SET chu_ky_ngay = GREATEST(1, chu_ky_thang * 30) WHERE chu_ky_ngay IS NULL;
