-- Vai trò mới: Trưởng Phòng Quản lý nội bộ (TP_QLNB)
INSERT INTO vai_tro (ma, ten) VALUES ('TP_QLNB', 'Trưởng P. Quản lý nội bộ')
ON CONFLICT (ma) DO UPDATE SET ten = EXCLUDED.ten;

-- Quyền mặc định (CEO chỉnh tiếp trong ma trận Phân quyền nếu cần):
-- quản nhân sự + xem các phân hệ vận hành; không đụng tài chính/cấu hình.
INSERT INTO phan_quyen (vai_tro_id, module, muc)
SELECT vt.id, v.module, v.muc::muc_quyen
FROM (VALUES
  ('TP_QLNB','nhan_su','DUYET'),
  ('TP_QLNB','dashboard','XEM'),
  ('TP_QLNB','tai_lieu','THAO_TAC'),
  ('TP_QLNB','kho','XEM'),
  ('TP_QLNB','ncc','XEM'),
  ('TP_QLNB','ban_hang','XEM'),
  ('TP_QLNB','ke_toan','XEM'),
  ('TP_QLNB','du_an','XEM'),
  ('TP_QLNB','cho_thue','XEM'),
  ('TP_QLNB','crm','XEM'),
  ('TP_QLNB','dich_vu_kt','XEM')
) AS v(ma, module, muc)
JOIN vai_tro vt ON vt.ma = v.ma
WHERE NOT EXISTS (SELECT 1 FROM phan_quyen p
                  WHERE p.vai_tro_id = vt.id AND p.module = v.module);
