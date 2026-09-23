-- 129: Lenh chi PO ghi ro SO TIEN DOT (phan thuc chi cua lenh) — tach khoi luy ke de nghi.
--      so_tien = luy ke de nghi (giu nguyen), so_tien_dot = phan chi them = de nghi − da tra that (so cong no).
ALTER TABLE lenh_chi_bank ADD COLUMN IF NOT EXISTS so_tien_dot NUMERIC(18,0);
-- Lenh CHO DUYET cua PO ma so de nghi = DUNG so DA TRA tren so cong no (de nghi lai coc/dot cu, PO chua co lenh nao da chi)
-- -> dot = 0: duyet duoc nhung KHONG chi them (tranh tra coc lan hai).
UPDATE lenh_chi_bank l
   SET so_tien_dot = 0,
       ghi_chu = LEFT(COALESCE(l.ghi_chu || ' | ', '') || 'So de nghi = so da tra (coc/dot cu) - khong chi them (va 23/09/2026)', 200)
  FROM cong_no cn
 WHERE cn.don_mua_id = l.don_mua_id
   AND l.trang_thai = 'CHO_DUYET' AND l.so_tien_dot IS NULL
   AND l.so_tien > 0 AND l.so_tien = COALESCE(cn.da_thanh_toan, 0)
   AND NOT EXISTS (SELECT 1 FROM lenh_chi_bank l2 WHERE l2.don_mua_id = l.don_mua_id AND l2.trang_thai = 'DA_CHI');
