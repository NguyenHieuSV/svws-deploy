-- 167 — ✍️ Giao nhận tại site + DUYỆT xuất (anh Hiếu 01/11/2026, phần C): phiếu XUẤT cấp cho công trường
--       (có du_an_id) ghi NGƯỜI NHẬN và phải DUYỆT mới trừ tồn; biên bản cấp phát in được có bên giao/bên nhận.
--       trang_thai mặc định DA_DUYET để phiếu cũ và phiếu không gắn dự án giữ nguyên hành vi (không "chờ duyệt").
ALTER TABLE phieu_kho ADD COLUMN IF NOT EXISTS nguoi_nhan_id  BIGINT REFERENCES nhan_vien(id) ON DELETE SET NULL;
ALTER TABLE phieu_kho ADD COLUMN IF NOT EXISTS nguoi_giao_id  BIGINT REFERENCES nhan_vien(id) ON DELETE SET NULL;
ALTER TABLE phieu_kho ADD COLUMN IF NOT EXISTS trang_thai     VARCHAR(16) DEFAULT 'DA_DUYET';   -- MOI | DA_DUYET
ALTER TABLE phieu_kho ADD COLUMN IF NOT EXISTS nguoi_duyet_id BIGINT REFERENCES nhan_vien(id) ON DELETE SET NULL;
ALTER TABLE phieu_kho ADD COLUMN IF NOT EXISTS ngay_duyet     DATE;
ALTER TABLE phieu_kho ADD COLUMN IF NOT EXISTS ghi_chu        TEXT;
