-- Lượng nhập trong ngày của hóa chất - vật tư: SL dùng = tồn trước + lượng nhập - tồn nay
ALTER TABLE ct_bao_cao_vh ADD COLUMN IF NOT EXISTS luong_nhap numeric(15,3);
