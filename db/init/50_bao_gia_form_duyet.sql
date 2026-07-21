-- 50_bao_gia_form_duyet.sql — thêm bước DUYỆT cho báo giá gửi khách (bao_gia_form).
-- Trước đây báo giá gửi khách gửi thẳng không qua duyệt. Nay: NHAP → CHO_DUYET →
-- DA_DUYET (mới được gửi) hoặc TU_CHOI; lưu người duyệt + lý do từ chối.
ALTER TABLE bao_gia_form ADD COLUMN IF NOT EXISTS nguoi_duyet BIGINT REFERENCES nhan_vien(id);
ALTER TABLE bao_gia_form ADD COLUMN IF NOT EXISTS ly_do_tu_choi VARCHAR(300);
