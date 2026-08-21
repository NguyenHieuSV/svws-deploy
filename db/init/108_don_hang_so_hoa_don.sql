-- 108: so hoa don xuat cho khach, luu tren don hang ban (theo doi cong no)
ALTER TABLE don_hang ADD COLUMN IF NOT EXISTS so_hoa_don VARCHAR(60);
