set search_path to thu_vien;

-- Sách
create index if not exists idx_sach_tieu_de on sach(tieu_de);
create index if not exists idx_sach_tac_gia on sach(tac_gia);
-- isbn đã unique -> không cần index thường
create index if not exists idx_sach_danh_muc on sach(danh_muc_id);

-- Bản sao
create index if not exists idx_ban_sao_sach_id on ban_sao_sach(sach_id);
-- ma_ban_sao đã unique -> không cần index thường
create index if not exists idx_ban_sao_trang_thai on ban_sao_sach(trang_thai);

-- Bạn đọc
create index if not exists idx_ban_doc_ho_ten on ban_doc(ho_ten);
create index if not exists idx_ban_doc_email on ban_doc(email);
create index if not exists idx_ban_doc_han_the on ban_doc(han_the);

-- Phiếu mượn
create index if not exists idx_phieu_muon_ban_doc on phieu_muon(ban_doc_id);
create index if not exists idx_phieu_muon_trang_thai on phieu_muon(trang_thai);
create index if not exists idx_phieu_muon_ngay_hen_tra on phieu_muon(ngay_hen_tra);
create index if not exists idx_phieu_muon_tao_boi on phieu_muon(tao_boi);

-- Chi tiết mượn
create index if not exists idx_ctm_phieu on chi_tiet_muon(phieu_muon_id);
create index if not exists idx_ctm_ban_sao on chi_tiet_muon(ban_sao_id);
create index if not exists idx_ctm_thoi_gian_tra on chi_tiet_muon(thoi_gian_tra);
-- Tối ưu check "trả hết chưa" khi đóng phiếu
create index if not exists idx_ctm_phieu_open
  on chi_tiet_muon(phieu_muon_id)
  where thoi_gian_tra is null;

-- Tiền phạt
create index if not exists idx_tien_phat_phieu on tien_phat(phieu_muon_id);
create index if not exists idx_tien_phat_ban_sao on tien_phat(ban_sao_id);
create index if not exists idx_tien_phat_da_thanh_toan on tien_phat(da_thanh_toan);

-- Một bản sao chỉ có 1 lượt “đang mượn” tại 1 thời điểm
create unique index if not exists uq_ctm_ban_sao_dang_muon
on chi_tiet_muon(ban_sao_id)
where thoi_gian_tra is null;