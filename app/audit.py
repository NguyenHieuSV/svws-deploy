from .models import AuditLog


def ghi_audit(db, nguoi_dung_id, hanh_dong, bang, ban_ghi_id, cu=None, moi=None):
    """Ghi vết mọi thao tác tạo/sửa/xóa/duyệt. Gọi trước khi commit."""
    db.add(AuditLog(
        nguoi_dung_id=nguoi_dung_id, hanh_dong=hanh_dong,
        bang=bang, ban_ghi_id=ban_ghi_id, gia_tri_cu=cu, gia_tri_moi=moi,
    ))
