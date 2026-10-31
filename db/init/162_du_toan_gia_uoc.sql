-- 162 — ⚠ GIÁ VỐN ƯỚC (anh Hiếu 31/10/2026, mục 2 rà logic): dự toán tạo ngược từ báo giá có giá vốn = giá bán − sàn biên,
--       là số ƯỚC. Cờ du_toan_ban.gia_uoc giữ cho tới khi người dùng sửa giá hết các dòng ƯỚC hoặc bấm «✓ Đã rà giá vốn».
--       Khi còn cờ: biên báo giá chỉ tạm tính (lúc duyệt chỉ CEO qua), biên chào ghi lên đơn hàng mang cờ gia_von_chao_uoc
--       → Kiểm soát lợi nhuận không so «chào → thực» với số ước; bản tuần 📉 liệt kê các mã chưa rà.
ALTER TABLE du_toan_ban ADD COLUMN IF NOT EXISTS gia_uoc BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE don_hang    ADD COLUMN IF NOT EXISTS gia_von_chao_uoc BOOLEAN NOT NULL DEFAULT FALSE;

-- dữ liệu cũ: dự toán còn dòng ghi chú «Giá vốn ƯỚC …» (tạo ngược 28/10/2026) → cờ
UPDATE du_toan_ban d SET gia_uoc = TRUE
 WHERE EXISTS (SELECT 1 FROM du_toan_ban_muc m WHERE m.du_toan_id = d.id AND m.ghi_chu LIKE 'Giá vốn ƯỚC%');

-- đơn hàng đã ghi biên chào theo dự toán ước → đánh dấu để không so biên
UPDATE don_hang h SET gia_von_chao_uoc = TRUE
 WHERE h.du_toan_ma IS NOT NULL
   AND EXISTS (SELECT 1 FROM du_toan_ban d WHERE d.gia_uoc AND lower(d.ma) = lower(h.du_toan_ma));
