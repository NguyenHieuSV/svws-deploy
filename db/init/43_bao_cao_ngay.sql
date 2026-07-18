-- 43_bao_cao_ngay.sql — Báo cáo công việc hằng ngày (Daily Report)
-- Mỗi nhân viên tự báo cáo công việc mỗi ngày; quản lý (quyền nhan_su XEM) xem toàn bộ.
CREATE TABLE IF NOT EXISTS bao_cao_ngay (
    id            BIGSERIAL PRIMARY KEY,
    nhan_vien_id  BIGINT NOT NULL REFERENCES nhan_vien(id) ON DELETE CASCADE,
    ngay          DATE   NOT NULL,
    da_lam        TEXT   NOT NULL DEFAULT '',   -- Công việc đã làm hôm nay
    ket_qua       TEXT   NOT NULL DEFAULT '',   -- Kết quả / tiến độ
    kho_khan      TEXT,                          -- Khó khăn / vướng mắc (cần hỗ trợ)
    ke_hoach      TEXT,                          -- Kế hoạch ngày làm việc tiếp theo
    so_gio        NUMERIC(5,2) DEFAULT 0,        -- Số giờ làm việc trong ngày
    ma_lien_quan  VARCHAR(120),                  -- Mã dự án / đơn hàng / công việc liên quan
    tao_luc       TIMESTAMPTZ NOT NULL DEFAULT now(),
    cap_nhat_luc  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (nhan_vien_id, ngay)                  -- mỗi người 1 báo cáo / ngày (upsert)
);
CREATE INDEX IF NOT EXISTS idx_bao_cao_ngay_ngay ON bao_cao_ngay (ngay);
CREATE INDEX IF NOT EXISTS idx_bao_cao_ngay_nv   ON bao_cao_ngay (nhan_vien_id, ngay);
