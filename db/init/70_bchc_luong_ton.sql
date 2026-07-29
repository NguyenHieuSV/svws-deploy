-- Báo cáo Hóa chất - Vật tư theo LƯỢNG TỒN (SL dùng = tồn liền trước - tồn cùng dòng)
ALTER TABLE ct_bcvh_chi_tieu ADD COLUMN IF NOT EXISTS loai varchar(20) DEFAULT 'KY_THUAT';
ALTER TABLE ct_bcvh_chi_tieu ADD COLUMN IF NOT EXISTS don_vi varchar(20);
ALTER TABLE ct_bao_cao_vh   ADD COLUMN IF NOT EXISTS luong_ton numeric(15,3);
