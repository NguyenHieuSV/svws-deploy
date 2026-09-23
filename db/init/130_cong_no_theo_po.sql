-- 130: Cong no phai tra theo PO — mot PO mot cong no; de nghi luy ke khong thap hon so da tra that.
-- (a) De nghi thanh toan (luy ke) thap hon so DA TRA tren so cong no -> nang len bang so da tra (khong vuot tong PO)
UPDATE don_mua dm
   SET de_nghi_tt = LEAST(x.da, COALESCE(dm.tong_tien, 0))
  FROM (SELECT don_mua_id, MAX(COALESCE(da_thanh_toan, 0)) AS da
          FROM cong_no WHERE loai = 'PHAI_TRA' AND don_mua_id IS NOT NULL GROUP BY don_mua_id) x
 WHERE x.don_mua_id = dm.id AND COALESCE(dm.de_nghi_tt, 0) < x.da;
-- (b) PO DA DUYET, chua tra du, chua co dong cong no -> tao dong nghia vu (so_tien = tong PO; da tra = moc cu neu co)
INSERT INTO cong_no (loai, nha_cung_cap_id, don_mua_id, so_tien, tien_thue, da_thanh_toan, han, trang_thai, so_ct)
SELECT 'PHAI_TRA'::loai_cong_no, dm.nha_cung_cap_id, dm.id, dm.tong_tien, 0, t.da, dm.ngay_tt_tiep,
       CASE WHEN dm.tong_tien > 0 AND t.da >= dm.tong_tien THEN 'DA_TRA'
            WHEN t.da > 0 THEN 'TRA_MOT_PHAN' ELSE 'CHUA_TRA' END,
       NULLIF(LEFT(dm.so_hoa_don, 60), '')
  FROM don_mua dm
  CROSS JOIN LATERAL (
       SELECT LEAST(COALESCE(dm.da_duyet_tt,
                             CASE WHEN EXISTS (SELECT 1 FROM lenh_chi_bank l WHERE l.don_mua_id = dm.id)
                                  THEN 0 ELSE COALESCE(dm.de_nghi_tt, 0) END),
                    COALESCE(dm.tong_tien, 0)) AS da) t
 WHERE dm.trang_thai = 'DA_DUYET' AND COALESCE(dm.tong_tien, 0) > 0 AND COALESCE(dm.tt_du, FALSE) = FALSE
   AND NOT EXISTS (SELECT 1 FROM cong_no c WHERE c.don_mua_id = dm.id);
-- (c) Dong cong no TRUNG cua cung mot PO (chua tra dong nao, khong hoa don, khong chung tu, khong lien ket) -> xoa
DELETE FROM cong_no c
 WHERE c.don_mua_id IS NOT NULL AND c.loai = 'PHAI_TRA'
   AND COALESCE(c.da_thanh_toan, 0) = 0 AND c.hoa_don_id IS NULL AND NULLIF(c.so_ct, '') IS NULL
   AND (SELECT COUNT(*) FROM cong_no c2 WHERE c2.don_mua_id = c.don_mua_id) > 1
   AND (SELECT SUM(c2.so_tien) FROM cong_no c2 WHERE c2.don_mua_id = c.don_mua_id)
       > (SELECT COALESCE(d.tong_tien, 0) FROM don_mua d WHERE d.id = c.don_mua_id)
   AND NOT EXISTS (SELECT 1 FROM thanh_toan tt WHERE tt.cong_no_id = c.id)
   AND NOT EXISTS (SELECT 1 FROM lenh_chi_bank l WHERE l.cong_no_id = c.id)
   AND NOT EXISTS (SELECT 1 FROM phieu_thu_chi p WHERE p.cong_no_id = c.id)
   AND NOT EXISTS (SELECT 1 FROM chi_ngoai_lenh g WHERE g.cong_no_id = c.id);
