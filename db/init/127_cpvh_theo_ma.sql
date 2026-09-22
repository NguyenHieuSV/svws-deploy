-- 127: Chi phi van hanh cho thue GHI THEO MA HANG BAN THAT + noi voi PO / hoa don MUA (chong tinh chi phi 2 lan)
ALTER TABLE chi_phi_van_hanh ADD COLUMN IF NOT EXISTS don_hang_id BIGINT;
ALTER TABLE chi_phi_van_hanh ADD COLUMN IF NOT EXISTS don_mua_id BIGINT;
ALTER TABLE chi_phi_van_hanh ADD COLUMN IF NOT EXISTS hoa_don_id BIGINT;
ALTER TABLE chi_phi_van_hanh ADD COLUMN IF NOT EXISTS so_hoa_don VARCHAR(60);
ALTER TABLE chi_phi_van_hanh ADD COLUMN IF NOT EXISTS ncc_ten VARCHAR(200);
UPDATE chi_phi_van_hanh c SET so_hoa_don = h.so_hoa_don, ncc_ten = h.ncc_ten
  FROM ct_hoa_don_dau_vao h WHERE h.chi_phi_id = c.id AND c.so_hoa_don IS NULL;
