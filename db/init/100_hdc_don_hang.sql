-- 100: Hoa don cho — gan ma don hang truoc khi ghi vao Hoa don MUA
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS don_hang_id BIGINT;
