-- 47_chat_dm.sql — ghi nhớ phòng nhắn riêng (DM) giữa bot và từng người.
-- Khi người dùng nhắn cho bot lần đầu, Google gửi sự kiện tới /google-chat/events;
-- ta lưu lại space (phòng) + email + user_id để LẦN SAU gửi chủ động THẲNG vào phòng,
-- khỏi phải tra cứu người dùng qua email (thao tác mà Service Account không hỗ trợ).
CREATE TABLE IF NOT EXISTS chat_dm (
    user_id      VARCHAR(80) PRIMARY KEY,       -- "users/1234567890"
    google_email VARCHAR(200),                  -- email hiển thị trong sự kiện (nếu có)
    ten_hthi     VARCHAR(200),                  -- displayName
    space_name   VARCHAR(120),                  -- "spaces/AAAA..." phòng nhắn riêng
    cap_nhat     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_chat_dm_email ON chat_dm (google_email);
