-- ============================================================
-- Mở rộng cho module Dự án (chạy SAU SVWS_schema.sql)
--   - breakdown dự toán nhập từ Forecast Cal
--   - phân loại hạng mục cho chi phí thực tế (để đối chiếu)
-- ============================================================
ALTER TABLE du_an_chi_phi ADD COLUMN IF NOT EXISTS hang_muc VARCHAR(60);

CREATE TABLE IF NOT EXISTS du_toan_ct (
    id          BIGSERIAL PRIMARY KEY,
    du_an_id    BIGINT NOT NULL REFERENCES du_an(id) ON DELETE CASCADE,
    hang_muc    VARCHAR(60),
    mo_ta       VARCHAR(200),
    so_luong    NUMERIC(15,3) NOT NULL DEFAULT 1,
    don_gia     NUMERIC(18,0) NOT NULL DEFAULT 0,
    thanh_tien  NUMERIC(18,0) NOT NULL DEFAULT 0,
    nguon       VARCHAR(40) DEFAULT 'FORECAST_CAL'
);
CREATE INDEX IF NOT EXISTS idx_du_toan_ct_du_an   ON du_toan_ct(du_an_id);
CREATE INDEX IF NOT EXISTS idx_du_an_chi_phi_du_an ON du_an_chi_phi(du_an_id);
