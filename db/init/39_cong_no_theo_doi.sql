-- Sales theo dõi công nợ khách: ngày thanh toán tiếp theo + ghi chú
-- (nhắc tự động khi còn ≤ 7 ngày tới ngày thanh toán tiếp theo)
ALTER TABLE cong_no
    ADD COLUMN IF NOT EXISTS ngay_tt_tiep DATE,
    ADD COLUMN IF NOT EXISTS ghi_chu VARCHAR(300);
