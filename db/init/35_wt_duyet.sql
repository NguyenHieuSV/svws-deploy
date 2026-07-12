-- Working time & Overtime: luồng nhân viên ĐĂNG KÝ tăng ca → quản lý DUYỆT
-- (Đ107 BLLĐ 2019: tăng ca phải có sự đồng ý — đăng ký, duyệt xong mới tính vào kiểm soát)
ALTER TABLE ngay_nghi_ot ADD COLUMN IF NOT EXISTS trang_thai TEXT NOT NULL DEFAULT 'DA_DUYET';
ALTER TABLE ngay_nghi_ot ADD COLUMN IF NOT EXISTS nguoi_duyet BIGINT REFERENCES nhan_vien(id);
ALTER TABLE ngay_nghi_ot ADD COLUMN IF NOT EXISTS ly_do_tu_choi VARCHAR(300);
CREATE INDEX IF NOT EXISTS idx_nnot_tt ON ngay_nghi_ot(trang_thai);
