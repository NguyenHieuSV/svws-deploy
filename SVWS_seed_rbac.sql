-- ============================================================
-- SVWS — Seed phân quyền (RBAC) sinh từ ma trận chuẩn
-- Chạy SAU SVWS_schema.sql. Idempotent: chạy lại an toàn.
-- Quy ước: chỉ ghi quyền ĐƯỢC CẤP; vắng mặt = KHONG (không truy cập).
-- ============================================================
BEGIN;

-- 1) Vai trò
INSERT INTO vai_tro (ma, ten) VALUES
  ('CEO', 'Giám đốc'),
  ('TP_KD', 'Trưởng P. Kinh doanh'),
  ('NV_KD', 'Nhân viên Kinh doanh'),
  ('NV_CRM', 'NV Chăm sóc KH / CRM'),
  ('TP_CU', 'Trưởng P. Cung ứng & Kho'),
  ('NV_MUA', 'NV Mua hàng / NCC'),
  ('THUKHO', 'Thủ kho'),
  ('KTT', 'Kế toán trưởng'),
  ('NV_KT', 'NV Kế toán (kiêm Tài chính)'),
  ('TP_DA', 'Trưởng dự án'),
  ('NV_DA', 'NV Dự án (giám sát thực địa)'),
  ('NV_THUE', 'NV Dịch vụ cho thuê'),
  ('NV_HCNS', 'NV Hành chính - Nhân sự'),
  ('ADMIN', 'Admin / IT hệ thống')
ON CONFLICT (ma) DO UPDATE SET ten = EXCLUDED.ten;

-- 2) Ma trận quyền (vai trò × module). 87 quyền được cấp (các ô không liệt kê = KHONG)
INSERT INTO phan_quyen (vai_tro_id, module, muc)
SELECT vt.id, v.module, v.muc::muc_quyen
FROM (VALUES
  ('CEO','nhan_su','DUYET'),
  ('CEO','ban_hang','DUYET'),
  ('CEO','crm','DUYET'),
  ('CEO','ke_toan','DUYET'),
  ('CEO','tai_chinh','DUYET'),
  ('CEO','kho','DUYET'),
  ('CEO','ncc','DUYET'),
  ('CEO','du_an','DUYET'),
  ('CEO','cho_thue','DUYET'),
  ('CEO','tai_lieu','DUYET'),
  ('CEO','dashboard','DUYET'),
  ('CEO','cau_hinh','XEM'),
  ('TP_KD','ban_hang','DUYET'),
  ('TP_KD','crm','DUYET'),
  ('TP_KD','kho','XEM'),
  ('TP_KD','tai_lieu','THAO_TAC'),
  ('TP_KD','dashboard','XEM'),
  ('NV_KD','ban_hang','THAO_TAC'),
  ('NV_KD','crm','THAO_TAC'),
  ('NV_KD','kho','XEM'),
  ('NV_KD','tai_lieu','XEM'),
  ('NV_KD','dashboard','XEM'),
  ('NV_CRM','ban_hang','XEM'),
  ('NV_CRM','crm','THAO_TAC'),
  ('NV_CRM','tai_lieu','XEM'),
  ('NV_CRM','dashboard','XEM'),
  ('TP_CU','ban_hang','XEM'),
  ('TP_CU','kho','DUYET'),
  ('TP_CU','ncc','DUYET'),
  ('TP_CU','tai_lieu','THAO_TAC'),
  ('TP_CU','dashboard','XEM'),
  ('NV_MUA','kho','XEM'),
  ('NV_MUA','ncc','THAO_TAC'),
  ('NV_MUA','tai_lieu','XEM'),
  ('NV_MUA','dashboard','XEM'),
  ('THUKHO','kho','THAO_TAC'),
  ('THUKHO','ncc','XEM'),
  ('THUKHO','tai_lieu','XEM'),
  ('THUKHO','dashboard','XEM'),
  ('KTT','nhan_su','XEM'),
  ('KTT','ban_hang','XEM'),
  ('KTT','ke_toan','DUYET'),
  ('KTT','tai_chinh','DUYET'),
  ('KTT','kho','XEM'),
  ('KTT','ncc','XEM'),
  ('KTT','du_an','XEM'),
  ('KTT','cho_thue','XEM'),
  ('KTT','tai_lieu','XEM'),
  ('KTT','dashboard','XEM'),
  ('NV_KT','ban_hang','XEM'),
  ('NV_KT','ke_toan','THAO_TAC'),
  ('NV_KT','tai_chinh','THAO_TAC'),
  ('NV_KT','kho','XEM'),
  ('NV_KT','ncc','XEM'),
  ('NV_KT','du_an','XEM'),
  ('NV_KT','tai_lieu','XEM'),
  ('NV_KT','dashboard','XEM'),
  ('TP_DA','tai_chinh','XEM'),
  ('TP_DA','kho','XEM'),
  ('TP_DA','du_an','DUYET'),
  ('TP_DA','cho_thue','XEM'),
  ('TP_DA','tai_lieu','THAO_TAC'),
  ('TP_DA','dashboard','XEM'),
  ('NV_DA','kho','XEM'),
  ('NV_DA','du_an','THAO_TAC'),
  ('NV_DA','tai_lieu','THAO_TAC'),
  ('NV_DA','dashboard','XEM'),
  ('NV_THUE','crm','XEM'),
  ('NV_THUE','kho','THAO_TAC'),
  ('NV_THUE','cho_thue','THAO_TAC'),
  ('NV_THUE','tai_lieu','THAO_TAC'),
  ('NV_THUE','dashboard','XEM'),
  ('NV_HCNS','nhan_su','THAO_TAC'),
  ('NV_HCNS','tai_lieu','THAO_TAC'),
  ('NV_HCNS','dashboard','XEM'),
  ('ADMIN','nhan_su','XEM'),
  ('ADMIN','ban_hang','XEM'),
  ('ADMIN','crm','XEM'),
  ('ADMIN','ke_toan','XEM'),
  ('ADMIN','tai_chinh','XEM'),
  ('ADMIN','kho','XEM'),
  ('ADMIN','ncc','XEM'),
  ('ADMIN','du_an','XEM'),
  ('ADMIN','cho_thue','XEM'),
  ('ADMIN','tai_lieu','XEM'),
  ('ADMIN','dashboard','XEM'),
  ('ADMIN','cau_hinh','QUAN_TRI')
) AS v(ma, module, muc)
JOIN vai_tro vt ON vt.ma = v.ma
ON CONFLICT (vai_tro_id, module) DO UPDATE SET muc = EXCLUDED.muc;

-- 3) Hạn mức phê duyệt (ngưỡng tiền VND). Ngưỡng = tham số, chỉnh tại đây.
INSERT INTO han_muc_duyet (loai, vai_tro_id, nguong_tu, nguong_den)
SELECT v.loai, vt.id, v.tu, v.den
FROM (VALUES
  ('po','TP_CU',0,10000000),
  ('po','CEO',10000001,NULL::numeric),
  ('chi_phi_du_an','TP_DA',0,5000000),
  ('chi_phi_du_an','KTT',5000001,50000000),
  ('chi_phi_du_an','CEO',50000001,NULL::numeric),
  ('bao_gia','TP_KD',0,100000000),
  ('bao_gia','CEO',100000001,NULL::numeric)
) AS v(loai, ma, tu, den)
JOIN vai_tro vt ON vt.ma = v.ma
ON CONFLICT (loai, vai_tro_id) DO UPDATE SET nguong_tu = EXCLUDED.nguong_tu, nguong_den = EXCLUDED.nguong_den;

-- Ghi chú: hợp đồng cho thuê & thanh toán NCC theo doc chỉ ghi 'giá trị lớn → CEO'
-- (chưa có số cụ thể). Thêm dòng tương tự khi anh chốt ngưỡng, ví dụ:
--   ('hop_dong_thue','TP_DA',0,<nguong>), ('hop_dong_thue','CEO',<nguong+1>,NULL)

COMMIT;
