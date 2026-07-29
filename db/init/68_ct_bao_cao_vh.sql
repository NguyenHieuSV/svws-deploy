-- Báo cáo vận hành của dự án cho thuê: KY_THUAT | HOA_CHAT_VT
CREATE TABLE IF NOT EXISTS ct_bao_cao_vh (
  id         bigserial PRIMARY KEY,
  tai_san_id bigint NOT NULL REFERENCES tai_san_cho_thue(id) ON DELETE CASCADE,
  loai       varchar(20) NOT NULL DEFAULT 'KY_THUAT',
  ngay       date DEFAULT CURRENT_DATE,
  noi_dung   text NOT NULL,
  thong_so   text,
  so_luong   numeric(15,3),
  don_vi     varchar(20),
  ghi_chu    text,
  nguoi_tao  bigint REFERENCES nhan_vien(id)
);
CREATE INDEX IF NOT EXISTS idx_ct_bcvh_ts ON ct_bao_cao_vh(tai_san_id, loai);
