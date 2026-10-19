-- 152 — TRAINING: đối tượng của bài chọn theo TỪNG NHÂN VIÊN (19/10/2026).
-- trn_bai.nhan_vien_ap_dung = id nhân viên cách nhau dấu phẩy; trống = xét tiếp vai_tro_ap_dung, rồi tất cả nhân viên đang làm việc.
ALTER TABLE trn_bai ADD COLUMN IF NOT EXISTS nhan_vien_ap_dung TEXT;
