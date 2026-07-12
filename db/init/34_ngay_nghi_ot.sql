-- Working time & Overtime: theo dõi ngày nghỉ (phép/không phép/lễ/việc riêng)
-- và giờ tăng ca (ngày thường/cuối tuần/lễ) từng ngày cho từng nhân viên
CREATE TABLE IF NOT EXISTS ngay_nghi_ot (
    id BIGSERIAL PRIMARY KEY,
    nhan_vien_id BIGINT NOT NULL REFERENCES nhan_vien(id) ON DELETE CASCADE,
    ngay DATE NOT NULL,
    loai TEXT NOT NULL,               -- NGHI_PHEP | KHONG_PHEP | NGHI_LE | VIEC_RIENG_CO_LUONG
                                      -- | VIEC_RIENG_KHONG_LUONG | NGHI_BU | OT_THUONG | OT_CUOI_TUAN | OT_LE
    so_gio NUMERIC(5,2) DEFAULT 0,    -- giờ tăng ca (loại OT_*)
    so_ngay NUMERIC(4,2) DEFAULT 0,   -- số ngày nghỉ (0.5 hoặc 1 cho mỗi dòng/ngày)
    ghi_chu VARCHAR(300),
    nguoi_tao BIGINT REFERENCES nhan_vien(id)
);
CREATE INDEX IF NOT EXISTS idx_nnot_nv_ngay ON ngay_nghi_ot(nhan_vien_id, ngay);
CREATE INDEX IF NOT EXISTS idx_nnot_ngay ON ngay_nghi_ot(ngay);
