-- 147 — BỎ BƯỚC "ĐỀ XUẤT MUA HÀNG" (CEO chốt 10/10/2026): PO lập thẳng từ Dự toán hàng bán · BOQ dự án · Cho thuê · Kho.
-- Bảng yeu_cau_mua / yeu_cau_mua_ct GIỮ NGUYÊN làm lịch sử (hồ sơ PO vẫn tra được "đề xuất gốc").
-- Việc chuyển 3 đề xuất đã duyệt thành PO chờ duyệt và đóng 7 đề xuất mới chạy bằng Python lúc khởi động
-- (app/bo_de_xuat_mua.py — một lần, có đánh dấu trong audit_log), vì cần cùng công thức tiền với PO lập tay.

-- 1) Dòng dự toán hàng bán / BOQ dự án khóa theo PO đã lập (thay cho yeu_cau_mua_id).
ALTER TABLE du_toan_ban_muc ADD COLUMN IF NOT EXISTS don_mua_id BIGINT REFERENCES don_mua(id) ON DELETE SET NULL;
ALTER TABLE du_an_du_toan  ADD COLUMN IF NOT EXISTS don_mua_id BIGINT REFERENCES don_mua(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_dtbm_don_mua ON du_toan_ban_muc(don_mua_id);
CREATE INDEX IF NOT EXISTS idx_dadt_don_mua ON du_an_du_toan(don_mua_id);

-- 2) Chuyển khóa từ đề xuất đã thành PO sang PO (dự toán hàng bán: cột yeu_cau_mua_id; BOQ dự án: nhãn trong ghi chú).
UPDATE du_toan_ban_muc m SET don_mua_id = y.don_mua_id
  FROM yeu_cau_mua y
 WHERE m.yeu_cau_mua_id = y.id AND y.don_mua_id IS NOT NULL AND m.don_mua_id IS NULL;

UPDATE du_an_du_toan x SET don_mua_id = y.don_mua_id
  FROM yeu_cau_mua y
 WHERE x.don_mua_id IS NULL
   AND x.ghi_chu ~ 'Đã đề xuất mua #[0-9]+'
   AND y.id = (substring(x.ghi_chu from 'Đã đề xuất mua #([0-9]+)'))::bigint
   AND y.don_mua_id IS NOT NULL;

-- Dòng BOQ đã có PO: đổi nhãn sang số PO; dòng chưa có PO: gỡ nhãn cũ để dòng mở lại cho 🛒 Tạo PO.
UPDATE du_an_du_toan x
   SET ghi_chu = NULLIF(btrim(regexp_replace(x.ghi_chu, 'Đã đề xuất mua #[0-9]+', 'Đã tạo PO ' || COALESCE(d.so, d.id::text), 'g')), '')
  FROM don_mua d
 WHERE x.don_mua_id = d.id AND x.ghi_chu ~ 'Đã đề xuất mua #';

UPDATE du_an_du_toan
   SET ghi_chu = NULLIF(btrim(regexp_replace(ghi_chu, '( · )?Đã đề xuất mua #[0-9]+', '', 'g')), '')
 WHERE ghi_chu ~ 'Đã đề xuất mua #' AND don_mua_id IS NULL;
