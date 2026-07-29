-- Danh mục thiết bị / vật tư cấu thành của từng DỰ ÁN CHO THUÊ
CREATE TABLE IF NOT EXISTS ct_thiet_bi (
  id         bigserial PRIMARY KEY,
  tai_san_id bigint NOT NULL REFERENCES tai_san_cho_thue(id) ON DELETE CASCADE,
  ten        varchar(250) NOT NULL,
  thong_so   text,
  so_luong   numeric(15,3) DEFAULT 1,
  don_gia    numeric(18,0) DEFAULT 0,
  ghi_chu    text
);
CREATE INDEX IF NOT EXISTS idx_ct_thiet_bi_ts ON ct_thiet_bi(tai_san_id);
