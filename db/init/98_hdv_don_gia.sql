-- 98: Hóa đơn đầu vào — AI trích thêm số lượng / đơn vị / đơn giá mặt hàng chính
ALTER TABLE ct_hoa_don_dau_vao ADD COLUMN IF NOT EXISTS so_luong NUMERIC(15,3);
ALTER TABLE ct_hoa_don_dau_vao ADD COLUMN IF NOT EXISTS don_vi_hang VARCHAR(20);
ALTER TABLE ct_hoa_don_dau_vao ADD COLUMN IF NOT EXISTS don_gia NUMERIC(18,2);
