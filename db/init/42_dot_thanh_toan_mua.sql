-- Lịch sử từng ĐỢT thanh toán của đơn mua (PO): giữ lại ngày + số tiền mỗi lần trả
-- để mở lại form Sửa thanh toán vẫn thấy dữ liệu cũ, tránh nhầm lẫn.
CREATE TABLE IF NOT EXISTS don_mua_dot_tt (
  id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  don_mua_id BIGINT NOT NULL REFERENCES don_mua(id) ON DELETE CASCADE,
  ngay       DATE NOT NULL DEFAULT CURRENT_DATE,
  so_tien    NUMERIC(18,0) NOT NULL,
  ghi_chu    VARCHAR(300),
  nguoi_tao  BIGINT REFERENCES nhan_vien(id),
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_dmdtt_don ON don_mua_dot_tt(don_mua_id);
