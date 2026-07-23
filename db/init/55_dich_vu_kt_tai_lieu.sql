-- 55: Tài liệu hướng dẫn kỹ thuật theo LOẠI dịch vụ (file upload hoặc link)
CREATE TABLE IF NOT EXISTS dich_vu_kt_tai_lieu (
  id          BIGSERIAL PRIMARY KEY,
  loai_dv     VARCHAR(30),                 -- gắn theo loại dịch vụ (CIP/SITE_SURVEY/...); NULL = dùng chung
  ten         VARCHAR(255) NOT NULL,
  duong_dan   TEXT,                         -- tham chiếu file (r2:<key> hoặc đường dẫn) nếu upload
  url         TEXT,                          -- link ngoài nếu gắn URL
  kich_thuoc  BIGINT DEFAULT 0,
  ghi_chu     TEXT,
  nguoi_tao   VARCHAR(120),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
