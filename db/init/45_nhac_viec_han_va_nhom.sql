-- 45_nhac_viec_han_va_nhom.sql
-- (1) han_hoan_thanh: hạn PHẢI HOÀN THÀNH công việc (khác thoi_diem = lúc nhắc)
-- (2) nhom: mã lô khi "Nhắc tất cả" — mỗi nhân viên 1 dòng riêng để tự đánh dấu xong,
--     các dòng cùng một lần nhắc chia sẻ cùng giá trị nhom để gom nhóm khi hiển thị.
ALTER TABLE nhac_viec ADD COLUMN IF NOT EXISTS han_hoan_thanh TIMESTAMP;
ALTER TABLE nhac_viec ADD COLUMN IF NOT EXISTS nhom VARCHAR(60);
CREATE INDEX IF NOT EXISTS idx_nhac_viec_nhom ON nhac_viec (nhom);
