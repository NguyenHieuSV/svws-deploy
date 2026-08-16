-- 95: Hóa đơn đầu vào — thêm loại chi phí cho form đầy đủ
ALTER TABLE ct_hoa_don_dau_vao ADD COLUMN IF NOT EXISTS loai_chi_phi VARCHAR(16) DEFAULT 'VAT_TU';
