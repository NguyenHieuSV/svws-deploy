-- 150 — TRAINING: bài BẮT BUỘC + hạn hoàn thành + NHẮC NHÂN VIÊN chưa thi / chưa đạt (19/10/2026).
--   trn_bai.bat_buoc / han_hoan_thanh / vai_tro_ap_dung (mã vai trò, cách nhau dấu phẩy; trống = mọi nhân viên có tài khoản) / nhac_tu_dong.
--   trn_nhac: nhật ký MỌI lần nhắc (tay hay tự động) — để không nhắn dồn, đếm số lần, và người quản lý biết ai đã được nhắc khi nào.
ALTER TABLE trn_bai ADD COLUMN IF NOT EXISTS bat_buoc       BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE trn_bai ADD COLUMN IF NOT EXISTS han_hoan_thanh DATE;
ALTER TABLE trn_bai ADD COLUMN IF NOT EXISTS vai_tro_ap_dung TEXT;
ALTER TABLE trn_bai ADD COLUMN IF NOT EXISTS nhac_tu_dong   BOOLEAN NOT NULL DEFAULT TRUE;

CREATE TABLE IF NOT EXISTS trn_nhac (
    id            BIGSERIAL PRIMARY KEY,
    bai_id        BIGINT NOT NULL REFERENCES trn_bai(id) ON DELETE CASCADE,
    nhan_vien_id  BIGINT NOT NULL REFERENCES nhan_vien(id) ON DELETE CASCADE,
    nguon         VARCHAR(10) NOT NULL DEFAULT 'TAY',      -- TAY (người quản lý bấm Nhắc) | TU_DONG (8h sáng)
    ket_qua       VARCHAR(10) NOT NULL DEFAULT 'OK',       -- OK | LOI
    loi           TEXT,
    nguoi_gui     BIGINT REFERENCES nguoi_dung(id) ON DELETE SET NULL,
    tao_luc       TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_trn_nhac_bai_nv ON trn_nhac(bai_id, nhan_vien_id, tao_luc);
