-- Khế ước vay gắn Mã dự án (kiểm soát khoản vay phục vụ dự án nào)
ALTER TABLE khoan_vay ADD COLUMN IF NOT EXISTS du_an_id bigint REFERENCES du_an(id) ON DELETE SET NULL;
