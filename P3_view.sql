set search_path to thu_vien;

-- Tồn kho theo sách
create or replace view v_ton_kho_sach as
select
  s.sach_id, s.tieu_de, s.tac_gia,
  count(bss.ban_sao_id) as tong_ban_sao,
  count(*) filter (where bss.trang_thai='SAN_SANG') as san_sang,
  count(*) filter (where bss.trang_thai='DANG_MUON') as dang_muon,
  count(*) filter (where bss.trang_thai in ('MAT','HU_HONG')) as mat_hoac_hu_hong
from sach s
left join ban_sao_sach bss on bss.sach_id = s.sach_id
group by s.sach_id, s.tieu_de, s.tac_gia;

-- Phiếu mượn quá hạn
create or replace view v_phieu_muon_qua_han as
select *
from phieu_muon
where trang_thai='DANG_MUON' and ngay_hen_tra < current_date;

-- Danh sách đang mượn (chưa trả)
create or replace view v_dang_muon as
select
  pm.phieu_muon_id, pm.ngay_muon, pm.ngay_hen_tra, pm.trang_thai,
  bd.ban_doc_id, bd.ho_ten,
  s.sach_id, s.tieu_de,
  bss.ban_sao_id, bss.ma_ban_sao,
  ctm.thoi_gian_muon, ctm.thoi_gian_tra,
  tk.ten_dang_nhap as tao_boi_user
from chi_tiet_muon ctm
join phieu_muon pm on pm.phieu_muon_id = ctm.phieu_muon_id
join ban_doc bd on bd.ban_doc_id = pm.ban_doc_id
join ban_sao_sach bss on bss.ban_sao_id = ctm.ban_sao_id
join sach s on s.sach_id = bss.sach_id
left join tai_khoan_nguoi_dung tk on tk.user_id = pm.tao_boi
where ctm.thoi_gian_tra is null;