-- Báo cáo kỹ thuật: thêm Vị trí; bộ CHỈ TIÊU MẪU lưu theo từng dự án cho thuê
ALTER TABLE ct_bao_cao_vh ADD COLUMN IF NOT EXISTS vi_tri varchar(150);
CREATE TABLE IF NOT EXISTS ct_bcvh_chi_tieu (
  id         bigserial PRIMARY KEY,
  tai_san_id bigint NOT NULL REFERENCES tai_san_cho_thue(id) ON DELETE CASCADE,
  vi_tri     varchar(150),
  chi_tieu   varchar(250) NOT NULL,
  thu_tu     int DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_ct_bcvh_ct_ts ON ct_bcvh_chi_tieu(tai_san_id);
