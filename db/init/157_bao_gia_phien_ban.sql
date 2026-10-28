-- 157 — PHIÊN BẢN báo giá gửi khách (28/10/2026): mỗi lần ✉️ gửi khách lưu một bản Rev.A, Rev.B… kèm tổng, giá vốn, biên,
-- để khi khách so các lần chào, mình tra lại được; người duyệt thấy bảng so sánh với lần chào trước.
CREATE TABLE IF NOT EXISTS bao_gia_phien_ban (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  bao_gia_form_id BIGINT NOT NULL REFERENCES bao_gia_form(id) ON DELETE CASCADE,
  rev VARCHAR(8) NOT NULL,                      -- A, B, C…
  so VARCHAR(50),
  noi_dung JSONB NOT NULL,                      -- bản chụp nội dung lúc gửi
  tong_chua_vat NUMERIC(18,0) DEFAULT 0,
  tong_gom_vat NUMERIC(18,0) DEFAULT 0,
  tong_tuy_chon NUMERIC(18,0) DEFAULT 0,
  gia_von NUMERIC(18,0) DEFAULT 0,
  bien NUMERIC(6,2),
  gui_den VARCHAR(300),
  nguoi_gui BIGINT REFERENCES nguoi_dung(id) ON DELETE SET NULL,
  gui_luc TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_bgpb_form ON bao_gia_phien_ban (bao_gia_form_id, id);
