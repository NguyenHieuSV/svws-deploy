-- 92: Lệnh chi từ CÔNG NỢ PHẢI TRẢ — nút 💳 Thanh toán cũng phải qua Duyệt chi Ngân Hàng
ALTER TABLE lenh_chi_bank ADD COLUMN IF NOT EXISTS cong_no_id BIGINT REFERENCES cong_no(id);
ALTER TABLE lenh_chi_bank ADD COLUMN IF NOT EXISTS hinh_thuc VARCHAR(30);
ALTER TABLE lenh_chi_bank ADD COLUMN IF NOT EXISTS ngay_tt DATE;
