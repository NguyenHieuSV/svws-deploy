-- 148 — Đối soát sao kê theo NỘI DUNG CHUYỂN KHOẢN (10/10/2026): bảng gắn tay 1 dòng sao kê ↔ nhiều khoản app.
-- Nhãn ghi tay mới trên sao_ke_dong.khop_loai: GAN_TAY (có dòng ở bảng này) · BO_KHOP (kế toán xác nhận không khớp) ·
-- COC_SK (kế toán ghi nhận là cọc / trả trước; khop_id = phiếu thu tạm ứng nếu có).
CREATE TABLE IF NOT EXISTS sao_ke_khop (
    id            BIGSERIAL PRIMARY KEY,
    dong_id       BIGINT NOT NULL REFERENCES sao_ke_dong(id) ON DELETE CASCADE,
    loai          VARCHAR(20) NOT NULL,
    khoan_id      BIGINT,
    so_tien       NUMERIC(18,0) NOT NULL DEFAULT 0,
    ghi_chu       VARCHAR(300),
    nguoi_dung_id BIGINT REFERENCES nguoi_dung(id),
    tao_luc       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sao_ke_khop_dong ON sao_ke_khop(dong_id);
