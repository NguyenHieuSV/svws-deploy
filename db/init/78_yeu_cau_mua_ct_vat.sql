-- Dong de xuat mua: thue suat VAT (%) de tinh Thanh tien / VAT / Tong cong
ALTER TABLE yeu_cau_mua_ct ADD COLUMN IF NOT EXISTS thue_suat NUMERIC(5,2) DEFAULT 0;
