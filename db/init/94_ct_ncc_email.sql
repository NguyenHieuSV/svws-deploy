-- 94: Danh bạ email NCC theo dự án cho thuê — quét hóa đơn đầu vào chỉ đọc thư từ các email đã khai
CREATE TABLE IF NOT EXISTS ct_ncc_email (
  id BIGSERIAL PRIMARY KEY,
  tai_san_id BIGINT REFERENCES tai_san_cho_thue(id) ON DELETE CASCADE,
  email VARCHAR(160) NOT NULL,
  ten_ncc VARCHAR(200),
  hoa_chat_vat_tu VARCHAR(300),
  tao_luc TIMESTAMP
);
