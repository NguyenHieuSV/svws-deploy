-- 146: NHAC TAI SAO KE THANG — tu ngay 7 hang thang chua thay sao ke thang truoc -> nhac nhom Duyet chi NH (1 lan/thang).
CREATE TABLE IF NOT EXISTS nhac_sao_ke_thang (
  thang VARCHAR(7) PRIMARY KEY,
  gui_luc TIMESTAMP,
  ket_qua JSONB
);
