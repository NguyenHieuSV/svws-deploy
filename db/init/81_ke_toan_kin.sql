-- 81: Khép kín kế toán lương
-- (1) Kinh phí công đoàn 2% (TK 3382) — DN nộp trên quỹ lương đóng BHXH
-- (2) Chế độ thử việc: không BHXH bắt buộc, TNCN khấu trừ 10% (cam kết 08 → tạm không khấu trừ)
-- (3) MST cá nhân đã có (ma_so_thue) + danh sách người phụ thuộc chi tiết
ALTER TABLE tham_so_luong ADD COLUMN IF NOT EXISTS tl_kpcd_dn NUMERIC(6,4) DEFAULT 0.02;
ALTER TABLE bang_luong    ADD COLUMN IF NOT EXISTS kpcd_dn NUMERIC(18,0) DEFAULT 0;
ALTER TABLE nhan_vien     ADD COLUMN IF NOT EXISTS loai_hop_dong VARCHAR(20) DEFAULT 'CHINH_THUC';
ALTER TABLE nhan_vien     ADD COLUMN IF NOT EXISTS cam_ket_08 BOOLEAN DEFAULT FALSE;
ALTER TABLE nhan_vien     ADD COLUMN IF NOT EXISTS phu_thuoc_chi_tiet TEXT;
