-- 158 — ĐƠN HÀNG nhớ BÁO GIÁ lúc chốt (28/10/2026): khi «→ Tạo đơn hàng» từ báo giá gửi khách (hoặc đơn lập tay / AI đọc PO
-- mang cùng mã) ghi lại dự toán gốc, Rev đã gửi, tổng chào (chưa VAT), giá vốn dự toán và BIÊN LÚC CHÀO,
-- để Kiểm soát lợi nhuận theo mã so biên lúc chào với biên thực tế (PO đã duyệt + công nợ gắn mã).
ALTER TABLE don_hang ADD COLUMN IF NOT EXISTS bao_gia_form_id BIGINT REFERENCES bao_gia_form(id) ON DELETE SET NULL;
ALTER TABLE don_hang ADD COLUMN IF NOT EXISTS du_toan_ma   VARCHAR(50);
ALTER TABLE don_hang ADD COLUMN IF NOT EXISTS bao_gia_rev  VARCHAR(8);
ALTER TABLE don_hang ADD COLUMN IF NOT EXISTS tong_chao    NUMERIC(18,0);
ALTER TABLE don_hang ADD COLUMN IF NOT EXISTS gia_von_chao NUMERIC(18,0);
ALTER TABLE don_hang ADD COLUMN IF NOT EXISTS bien_chao    NUMERIC(6,2);
ALTER TABLE don_hang ADD COLUMN IF NOT EXISTS chot_luc     TIMESTAMP;
CREATE INDEX IF NOT EXISTS ix_don_hang_bgf ON don_hang (bao_gia_form_id);

-- Nối đơn hàng CŨ với báo giá gửi khách cùng số (chỉ nối, không ghi số liệu — CEO/Admin bấm «📝 Ghi biên chào cho đơn cũ»
-- ở Nhà cung cấp → Kiểm soát để ghi theo nội dung báo giá hiện tại). Ưu tiên bản đã gửi khách > đã duyệt > đã xuất PDF.
UPDATE don_hang d
   SET bao_gia_form_id = b.id
  FROM (SELECT DISTINCT ON (lower(trim(so))) id, lower(trim(so)) AS so_l
          FROM bao_gia_form
         WHERE so IS NOT NULL AND trim(so) <> ''
           AND trang_thai IN ('DA_GUI', 'DA_DUYET', 'DA_XUAT')
           AND coalesce(noi_dung->>'loai', '') <> 'HOP_DONG'
         ORDER BY lower(trim(so)),
                  CASE trang_thai WHEN 'DA_GUI' THEN 0 WHEN 'DA_DUYET' THEN 1 ELSE 2 END, id DESC) b
 WHERE d.bao_gia_form_id IS NULL AND d.so IS NOT NULL AND lower(trim(d.so)) = b.so_l;
