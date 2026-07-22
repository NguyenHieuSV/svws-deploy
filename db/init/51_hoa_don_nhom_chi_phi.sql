-- 51: Nhóm chi phí cho hóa đơn (AI phân loại + gợi ý hồ sơ pháp lý)
ALTER TABLE hoa_don ADD COLUMN IF NOT EXISTS nhom_chi_phi VARCHAR(20);
