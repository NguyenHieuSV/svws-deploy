-- 151 — Hồ sơ lương: NGÀY BẮT ĐẦU THỬ VIỆC của nhân viên (19/10/2026). Chỉ để lưu / in hồ sơ (HĐ thử việc tự điền «từ ngày»);
-- không đổi cách tính lương. Trống = nhân viên không qua thử việc hoặc chưa nhập.
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS ngay_bat_dau_thu_viec DATE;
