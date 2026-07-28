-- Đơn vị tính giá thuê của tài sản/dự án cho thuê: VND/tháng hoặc VND/m3
ALTER TABLE tai_san_cho_thue ADD COLUMN IF NOT EXISTS don_vi_gia varchar(20) DEFAULT 'VND/THANG';
