-- 164 — 💾 Nhật ký SAO LƯU CSDL (anh Hiếu 31/10/2026, mục C1 rà app): mỗi ngày app tự đóng gói toàn bộ bảng thành
--       file ZIP (manifest + schema db/init + CSV từng bảng + pg_dump nếu có) lên kho tệp R2/B2 (app/sao_luu_service.py).
--       Mốc «hôm nay đã sao lưu» nằm ở bảng này nên khởi động lại máy chủ không chạy trùng.
CREATE TABLE IF NOT EXISTS sao_luu_log (
    id            BIGSERIAL PRIMARY KEY,
    ten_file      VARCHAR(120) NOT NULL,
    duong_dan     VARCHAR(400),                 -- tham chiếu kho tệp (r2:<key>) — NULL khi đã dọn
    kich_thuoc    BIGINT,
    so_bang       INTEGER,
    so_dong       BIGINT,
    bat_dau       TIMESTAMP NOT NULL,           -- giờ VN
    ket_thuc      TIMESTAMP,
    trang_thai    VARCHAR(16) NOT NULL DEFAULT 'DANG_CHAY',   -- DANG_CHAY | THANH_CONG | LOI | DA_XOA
    nguon         VARCHAR(16) NOT NULL DEFAULT 'TU_DONG',     -- TU_DONG | TAY
    nguoi_dung_id BIGINT,
    loi           TEXT,
    ghi_chu       TEXT
);
CREATE INDEX IF NOT EXISTS ix_sao_luu_log_bat_dau ON sao_luu_log (bat_dau DESC);
