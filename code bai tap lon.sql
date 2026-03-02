/* =========================================================
   QUẢN LÝ THƯ VIỆN - FULL SQL - PostgreSQL
   (CÓ ĐĂNG NHẬP + ĐĂNG KÝ + MƯỢN/TRẢ/GIA HẠN + VIEW/INDEX/TRIGGER)

   Quy định nghiệp vụ:
     - Mỗi phiếu mượn tối đa 5 cuốn
     - Gia hạn tối đa 2 lần
     - Phạt trễ hạn = 2000/ngày
     - Cho phép mượn lại cùng 1 bản sao sau khi trả
       (unique partial index với điều kiện thoi_gian_tra IS NULL)
     - Chống mượn trùng do race-condition: SELECT ... FOR UPDATE
     - Tránh lỗi “mượn hụt nhưng bản sao bị kẹt DANG_MUON”:
       sp_muon_sach KHÔNG xoá thủ công, để transaction rollback tự nhiên
     - Không tạo tiền phạt 0 đồng
     - ten_dang_nhap không phân biệt hoa/thường (citext)
     - Thống nhất log thời gian bằng timestamptz
     - Bảo vệ trạng thái ban_sao_sach khỏi update tay gây sai logic
   ========================================================= */

-- ===================== 0) RESET + TẠO SCHEMA =====================
drop schema if exists thu_vien cascade;
create schema thu_vien;
set search_path to thu_vien;

create extension if not exists pgcrypto;
create extension if not exists citext;

-- ===================== 1) TẠO BẢNG =====================

-- 1.1 Tài khoản người dùng (đăng nhập)
create table tai_khoan_nguoi_dung (
  user_id serial primary key,
  ten_dang_nhap citext not null unique,
  mat_khau_hash text not null,
  vai_tro varchar(20) not null default 'NHAN_VIEN'
    check (vai_tro in ('QUAN_TRI','NHAN_VIEN')),
  dang_hoat_dong boolean not null default true,
  tao_luc timestamptz not null default now()
);

-- 1.2 Danh mục
create table danh_muc (
  danh_muc_id serial primary key,
  ten varchar(100) not null unique
);

-- 1.3 Sách (isbn có thể null)
create table sach (
  sach_id serial primary key,
  tieu_de varchar(200) not null,
  tac_gia varchar(150) not null,
  nha_xuat_ban varchar(150),
  isbn varchar(20) unique,
  danh_muc_id int references danh_muc(danh_muc_id),
  tao_luc timestamptz not null default now()
);

-- 1.4 Bản sao sách
create table ban_sao_sach (
  ban_sao_id serial primary key,
  sach_id int not null references sach(sach_id) on delete cascade,
  ma_ban_sao varchar(50) not null unique,
  trang_thai varchar(20) not null default 'SAN_SANG'
    check (trang_thai in ('SAN_SANG','DANG_MUON','MAT','HU_HONG')),
  ghi_chu varchar(200)
);

-- 1.5 Bạn đọc
create table ban_doc (
  ban_doc_id serial primary key,
  ho_ten varchar(150) not null,
  loai_ban_doc varchar(20) not null default 'HOC_SINH'
    check (loai_ban_doc in ('HOC_SINH','GIAO_VIEN','KHACH')),
  email varchar(120) unique,
  sdt varchar(20),
  han_the date not null,
  dang_hoat_dong boolean not null default true
);

-- 1.6 Phiếu mượn
create table phieu_muon (
  phieu_muon_id serial primary key,
  ban_doc_id int not null references ban_doc(ban_doc_id),
  ngay_muon date not null default current_date,
  ngay_hen_tra date not null,
  trang_thai varchar(10) not null default 'DANG_MUON'
    check (trang_thai in ('DANG_MUON','DA_DONG')),
  so_lan_gia_han int not null default 0 check (so_lan_gia_han >= 0),
  ghi_chu varchar(250),
  tao_boi int references tai_khoan_nguoi_dung(user_id),
  check (ngay_hen_tra >= ngay_muon)
);

-- 1.7 Chi tiết mượn theo bản sao
-- Không đặt unique(ban_sao_id) trực tiếp để vẫn mượn lại sau khi trả
create table chi_tiet_muon (
  chi_tiet_muon_id serial primary key,
  phieu_muon_id int not null references phieu_muon(phieu_muon_id) on delete cascade,
  ban_sao_id int not null references ban_sao_sach(ban_sao_id),
  thoi_gian_muon timestamptz not null default now(),
  thoi_gian_tra timestamptz,
  tra_boi int references tai_khoan_nguoi_dung(user_id)
);

-- 1.8 Tiền phạt
create table tien_phat (
  tien_phat_id serial primary key,
  phieu_muon_id int not null references phieu_muon(phieu_muon_id) on delete cascade,
  ban_sao_id int not null references ban_sao_sach(ban_sao_id),
  so_ngay_tre int not null check (so_ngay_tre >= 0),
  so_tien numeric(12,2) not null check (so_tien >= 0),
  tao_luc timestamptz not null default now(),
  da_thanh_toan boolean not null default false,
  thanh_toan_luc timestamptz,
  unique(phieu_muon_id, ban_sao_id)
);

-- ===================== 2) INDEX =====================

-- Index tìm kiếm sách
create index if not exists idx_sach_tieu_de on sach(tieu_de);
create index if not exists idx_sach_tac_gia on sach(tac_gia);
create index if not exists idx_sach_isbn on sach(isbn);
create index if not exists idx_sach_danh_muc on sach(danh_muc_id);

-- Index bản sao
create index if not exists idx_ban_sao_sach_id on ban_sao_sach(sach_id);
create index if not exists idx_ban_sao_ma on ban_sao_sach(ma_ban_sao);
create index if not exists idx_ban_sao_trang_thai on ban_sao_sach(trang_thai);

-- Index bạn đọc
create index if not exists idx_ban_doc_ho_ten on ban_doc(ho_ten);
create index if not exists idx_ban_doc_email on ban_doc(email);
create index if not exists idx_ban_doc_han_the on ban_doc(han_the);

-- (Tuỳ chọn) Unique sdt nếu bạn muốn chặt chẽ hơn:
-- create unique index if not exists uq_ban_doc_sdt on ban_doc(sdt) where sdt is not null;

-- Index phiếu mượn
create index if not exists idx_phieu_muon_ban_doc on phieu_muon(ban_doc_id);
create index if not exists idx_phieu_muon_trang_thai on phieu_muon(trang_thai);
create index if not exists idx_phieu_muon_ngay_hen_tra on phieu_muon(ngay_hen_tra);
create index if not exists idx_phieu_muon_tao_boi on phieu_muon(tao_boi);

-- Index chi tiết mượn
create index if not exists idx_ctm_phieu on chi_tiet_muon(phieu_muon_id);
create index if not exists idx_ctm_ban_sao on chi_tiet_muon(ban_sao_id);
create index if not exists idx_ctm_thoi_gian_tra on chi_tiet_muon(thoi_gian_tra);

-- Index tiền phạt
create index if not exists idx_tien_phat_phieu on tien_phat(phieu_muon_id);
create index if not exists idx_tien_phat_ban_sao on tien_phat(ban_sao_id);
create index if not exists idx_tien_phat_da_thanh_toan on tien_phat(da_thanh_toan);

-- Mỗi bản sao chỉ có 1 lần “đang mượn” (chưa trả), nhưng vẫn được mượn lại sau khi trả
create unique index if not exists uq_ctm_ban_sao_dang_muon
on chi_tiet_muon(ban_sao_id)
where thoi_gian_tra is null;

-- ===================== 3) VIEW =====================

-- Thống kê tồn kho theo sách
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

-- ===================== 4) HÀM / THỦ TỤC =====================

-- 4.1 Đăng nhập: trả về user_id + vai_tro nếu mật khẩu đúng
create or replace function fn_dang_nhap(p_ten_dang_nhap text, p_mat_khau text)
returns table(user_id int, vai_tro text)
language sql stable as $$
  select u.user_id, u.vai_tro
  from tai_khoan_nguoi_dung u
  where u.ten_dang_nhap = p_ten_dang_nhap
    and u.dang_hoat_dong = true
    and u.mat_khau_hash = crypt(p_mat_khau, u.mat_khau_hash);
$$;

-- 4.2 Đăng ký tài khoản: người dùng tự tạo (mặc định NHAN_VIEN)
create or replace function fn_dang_ky_tai_khoan(p_ten_dang_nhap text, p_mat_khau text)
returns int
language plpgsql as $$
declare
  v_user_id int;
  v_username text;
begin
  v_username := lower(trim(p_ten_dang_nhap));

  if v_username is null or length(v_username) < 3 then
    raise exception 'Tên đăng nhập phải có ít nhất 3 ký tự';
  end if;

  if v_username !~ '^[a-z0-9._-]+$' then
    raise exception 'Tên đăng nhập chỉ được chứa: a-z, 0-9, dấu chấm (.), gạch dưới (_), gạch ngang (-)';
  end if;

  if p_mat_khau is null or length(p_mat_khau) < 6 then
    raise exception 'Mật khẩu phải có ít nhất 6 ký tự';
  end if;

  insert into tai_khoan_nguoi_dung(ten_dang_nhap, mat_khau_hash, vai_tro, dang_hoat_dong)
  values (v_username, crypt(p_mat_khau, gen_salt('bf')), 'NHAN_VIEN', true)
  returning user_id into v_user_id;

  return v_user_id;

exception
  when unique_violation then
    raise exception 'Tên đăng nhập đã tồn tại';
end $$;

-- 4.3 Thêm nhanh N bản sao (không hardcode sequence)
create or replace procedure sp_them_ban_sao(
  p_sach_id int,
  p_tien_to text,
  p_so_luong int
)
language plpgsql as $$
declare
  i int;
  v_seq text;
  v_next_id bigint;
  v_ma text;
begin
  if p_so_luong <= 0 then
    raise exception 'Số lượng phải lớn hơn 0';
  end if;

  if not exists (select 1 from sach where sach_id = p_sach_id) then
    raise exception 'Không tìm thấy sách';
  end if;

  v_seq := pg_get_serial_sequence('thu_vien.ban_sao_sach', 'ban_sao_id');
  if v_seq is null then
    raise exception 'Không tìm thấy sequence cho thu_vien.ban_sao_sach.ban_sao_id';
  end if;

  for i in 1..p_so_luong loop
    execute format('select nextval(%L)', v_seq) into v_next_id;
    v_ma := p_tien_to || '-' || lpad(v_next_id::text, 4, '0');

    insert into ban_sao_sach(ban_sao_id, sach_id, ma_ban_sao, trang_thai)
    values (v_next_id, p_sach_id, v_ma, 'SAN_SANG');
  end loop;
end $$;

-- 4.4 Mượn sách (yêu cầu user_id đã đăng nhập)
-- FIX quan trọng: KHÔNG xoá thủ công khi lỗi, để transaction rollback tự nhiên
create or replace function sp_muon_sach(
  p_user_id int,
  p_ban_doc_id int,
  p_ngay_hen_tra date,
  p_ds_ma_ban_sao text[],
  p_ghi_chu text default null
) returns int
language plpgsql as $$
declare
  v_phieu_muon_id int;
  v_count int;
  c text;
  v_ban_sao_id int;
  v_trang_thai text;
begin
  if not exists (select 1 from tai_khoan_nguoi_dung where user_id=p_user_id and dang_hoat_dong=true) then
    raise exception 'Không có quyền (cần đăng nhập)';
  end if;

  if p_ngay_hen_tra < current_date then
    raise exception 'Ngày hẹn trả phải lớn hơn hoặc bằng hôm nay';
  end if;

  if not exists (
    select 1 from ban_doc
    where ban_doc_id=p_ban_doc_id and dang_hoat_dong=true and han_the >= current_date
  ) then
    raise exception 'Bạn đọc không hợp lệ / hết hạn / không hoạt động';
  end if;

  v_count := array_length(p_ds_ma_ban_sao, 1);
  if v_count is null or v_count = 0 then
    raise exception 'Chưa chọn bản sao nào để mượn';
  end if;
  if v_count > 5 then
    raise exception 'Mỗi phiếu mượn tối đa 5 cuốn';
  end if;

  -- Chống trùng mã bản sao trong mảng
  if exists (
    select 1
    from unnest(p_ds_ma_ban_sao) x
    group by x
    having count(*) > 1
  ) then
    raise exception 'Danh sách mã bản sao bị trùng';
  end if;

  insert into phieu_muon(ban_doc_id, ngay_hen_tra, ghi_chu, tao_boi)
  values (p_ban_doc_id, p_ngay_hen_tra, p_ghi_chu, p_user_id)
  returning phieu_muon_id into v_phieu_muon_id;

  foreach c in array p_ds_ma_ban_sao loop
    select ban_sao_id, trang_thai
      into v_ban_sao_id, v_trang_thai
    from ban_sao_sach
    where ma_ban_sao = c
    for update;

    if v_ban_sao_id is null then
      raise exception 'Không tìm thấy mã bản sao: %', c;
    end if;

    if v_trang_thai <> 'SAN_SANG' then
      raise exception 'Bản sao % không sẵn sàng (trạng thái=%)', c, v_trang_thai;
    end if;

    insert into chi_tiet_muon(phieu_muon_id, ban_sao_id)
    values (v_phieu_muon_id, v_ban_sao_id);
  end loop;

  return v_phieu_muon_id;
end $$;

-- 4.5 Trả sách (yêu cầu user_id đã đăng nhập)
create or replace procedure sp_tra_sach(p_user_id int, p_ma_ban_sao text)
language plpgsql as $$
declare
  v_ban_sao_id int;
  v_phieu_muon_id int;
begin
  if not exists (select 1 from tai_khoan_nguoi_dung where user_id=p_user_id and dang_hoat_dong=true) then
    raise exception 'Không có quyền (cần đăng nhập)';
  end if;

  select ban_sao_id into v_ban_sao_id
  from ban_sao_sach
  where ma_ban_sao = p_ma_ban_sao;

  if v_ban_sao_id is null then
    raise exception 'Không tìm thấy mã bản sao';
  end if;

  update chi_tiet_muon
  set thoi_gian_tra = now(),
      tra_boi = p_user_id
  where ban_sao_id = v_ban_sao_id
    and thoi_gian_tra is null
  returning phieu_muon_id into v_phieu_muon_id;

  if v_phieu_muon_id is null then
    raise exception 'Bản sao này hiện không ở trạng thái đang mượn';
  end if;

  -- Trạng thái bản sao + tiền phạt + đóng phiếu do trigger xử lý
end $$;

-- 4.6 Gia hạn (tối đa 2 lần)
create or replace procedure sp_gia_han(p_user_id int, p_phieu_muon_id int, p_ngay_hen_tra_moi date)
language plpgsql as $$
declare
  v_ngay_hen_tra date;
  v_so_lan int;
  v_trang_thai text;
begin
  if not exists (select 1 from tai_khoan_nguoi_dung where user_id=p_user_id and dang_hoat_dong=true) then
    raise exception 'Không có quyền (cần đăng nhập)';
  end if;

  select ngay_hen_tra, so_lan_gia_han, trang_thai
  into v_ngay_hen_tra, v_so_lan, v_trang_thai
  from phieu_muon
  where phieu_muon_id = p_phieu_muon_id;

  if not found then
    raise exception 'Không tìm thấy phiếu mượn';
  end if;

  if v_trang_thai <> 'DANG_MUON' then
    raise exception 'Phiếu mượn không ở trạng thái đang mượn';
  end if;

  if v_ngay_hen_tra < current_date then
    raise exception 'Phiếu mượn đã quá hạn, không thể gia hạn';
  end if;

  if v_so_lan >= 2 then
    raise exception 'Gia hạn tối đa 2 lần';
  end if;

  if p_ngay_hen_tra_moi <= v_ngay_hen_tra then
    raise exception 'Ngày hẹn trả mới phải sau ngày hẹn trả cũ';
  end if;

  if not exists (
    select 1 from chi_tiet_muon
    where phieu_muon_id=p_phieu_muon_id and thoi_gian_tra is null
  ) then
    raise exception 'Không còn bản sao nào đang mượn để gia hạn';
  end if;

  update phieu_muon
  set ngay_hen_tra = p_ngay_hen_tra_moi,
      so_lan_gia_han = so_lan_gia_han + 1
  where phieu_muon_id = p_phieu_muon_id;
end $$;

-- ===================== 5) TRIGGER =====================

-- 5.0 Bảo vệ trạng thái ban_sao_sach khỏi update tay gây sai logic
create or replace function trg_bao_ve_trang_thai_ban_sao()
returns trigger
language plpgsql as $$
begin
  if new.trang_thai = 'SAN_SANG' and exists (
    select 1 from chi_tiet_muon
    where ban_sao_id = new.ban_sao_id and thoi_gian_tra is null
  ) then
    raise exception 'Không thể đặt SAN_SANG vì bản sao đang được mượn';
  end if;

  if new.trang_thai = 'DANG_MUON' and not exists (
    select 1 from chi_tiet_muon
    where ban_sao_id = new.ban_sao_id and thoi_gian_tra is null
  ) then
    raise exception 'Không thể đặt DANG_MUON vì không có bản ghi mượn đang mở';
  end if;

  return new;
end $$;

drop trigger if exists bao_ve_trang_thai on ban_sao_sach;
create trigger bao_ve_trang_thai
before update of trang_thai on ban_sao_sach
for each row execute function trg_bao_ve_trang_thai_ban_sao();

-- 5.1 Trước khi mượn: kiểm tra phiếu đang mượn, tối đa 5, bản sao phải sẵn sàng
create or replace function trg_kiem_tra_truoc_khi_muon()
returns trigger
language plpgsql as $$
declare
  v_trang_thai_phieu text;
  v_count int;
  v_trang_thai_ban_sao text;
begin
  select trang_thai into v_trang_thai_phieu
  from phieu_muon
  where phieu_muon_id = new.phieu_muon_id;

  if v_trang_thai_phieu <> 'DANG_MUON' then
    raise exception 'Phiếu mượn % không ở trạng thái đang mượn', new.phieu_muon_id;
  end if;

  -- Giới hạn: mỗi phiếu mượn tối đa 5 cuốn (tổng chi tiết trong phiếu)
  select count(*) into v_count
  from chi_tiet_muon
  where phieu_muon_id = new.phieu_muon_id;

  if v_count + 1 > 5 then
    raise exception 'Mỗi phiếu mượn tối đa 5 cuốn';
  end if;

  select trang_thai into v_trang_thai_ban_sao
  from ban_sao_sach
  where ban_sao_id = new.ban_sao_id;

  if v_trang_thai_ban_sao <> 'SAN_SANG' then
    raise exception 'Bản sao không sẵn sàng (trạng thái=%)', v_trang_thai_ban_sao;
  end if;

  return new;
end $$;

drop trigger if exists truoc_khi_muon on chi_tiet_muon;
create trigger truoc_khi_muon
before insert on chi_tiet_muon
for each row execute function trg_kiem_tra_truoc_khi_muon();

-- 5.2 Sau khi mượn: chuyển bản sao sang DANG_MUON
create or replace function trg_sau_khi_muon()
returns trigger
language plpgsql as $$
begin
  update ban_sao_sach
  set trang_thai='DANG_MUON'
  where ban_sao_id = new.ban_sao_id;

  return new;
end $$;

drop trigger if exists sau_khi_muon on chi_tiet_muon;
create trigger sau_khi_muon
after insert on chi_tiet_muon
for each row execute function trg_sau_khi_muon();

-- 5.3 Sau khi trả: chuyển bản sao về SAN_SANG + tính phạt (nếu trễ) + đóng phiếu nếu trả hết
create or replace function trg_sau_khi_tra()
returns trigger
language plpgsql as $$
declare
  v_ngay_hen_tra date;
  v_so_ngay_tre int;
  v_so_tien numeric(12,2);
begin
  if old.thoi_gian_tra is null and new.thoi_gian_tra is not null then

    -- trả -> set SAN_SANG
    update ban_sao_sach
    set trang_thai='SAN_SANG'
    where ban_sao_id = new.ban_sao_id;

    -- tính phạt
    select ngay_hen_tra into v_ngay_hen_tra
    from phieu_muon
    where phieu_muon_id = new.phieu_muon_id;

    v_so_ngay_tre := greatest(0, (new.thoi_gian_tra::date - v_ngay_hen_tra));
    v_so_tien := v_so_ngay_tre * 2000;

    -- chỉ tạo/cập nhật tiền phạt nếu có trễ
    if v_so_ngay_tre > 0 then
      insert into tien_phat(phieu_muon_id, ban_sao_id, so_ngay_tre, so_tien)
      values (new.phieu_muon_id, new.ban_sao_id, v_so_ngay_tre, v_so_tien)
      on conflict (phieu_muon_id, ban_sao_id) do update
      set so_ngay_tre = excluded.so_ngay_tre,
          so_tien = excluded.so_tien,
          tao_luc = now()
      where tien_phat.da_thanh_toan = false;
    end if;

    -- đóng phiếu nếu đã trả hết
    if not exists (
      select 1 from chi_tiet_muon
      where phieu_muon_id = new.phieu_muon_id and thoi_gian_tra is null
    ) then
      update phieu_muon
      set trang_thai='DA_DONG'
      where phieu_muon_id = new.phieu_muon_id;
    end if;

  end if;

  return new;
end $$;

drop trigger if exists sau_khi_tra on chi_tiet_muon;
create trigger sau_khi_tra
after update of thoi_gian_tra on chi_tiet_muon
for each row execute function trg_sau_khi_tra();

-- ===================== 6) DỮ LIỆU MẪU =====================

insert into tai_khoan_nguoi_dung(ten_dang_nhap, mat_khau_hash, vai_tro)
values
('admin', crypt('123456', gen_salt('bf')), 'QUAN_TRI'),
('staff', crypt('123456', gen_salt('bf')), 'NHAN_VIEN')
on conflict (ten_dang_nhap) do nothing;

insert into danh_muc(ten) values ('Cong nghe'), ('Tieu thuyet')
on conflict do nothing;

insert into sach(tieu_de, tac_gia, nha_xuat_ban, isbn, danh_muc_id) values
('Clean Code','Robert C. Martin','Prentice Hall','9780132350884',
 (select danh_muc_id from danh_muc where ten='Cong nghe')),
('De Men Phieu Luu Ky','To Hoai','Kim Dong',null,
 (select danh_muc_id from danh_muc where ten='Tieu thuyet'))
on conflict do nothing;

insert into ban_sao_sach(sach_id, ma_ban_sao) values
((select sach_id from sach where tieu_de='Clean Code'), 'CC-001'),
((select sach_id from sach where tieu_de='Clean Code'), 'CC-002'),
((select sach_id from sach where tieu_de='De Men Phieu Luu Ky'), 'DM-001')
on conflict (ma_ban_sao) do nothing;

insert into ban_doc(ho_ten, loai_ban_doc, email, sdt, han_the, dang_hoat_dong) values
('Nguyen Van A','HOC_SINH','a@gmail.com','0900000001', current_date + 365, true)
on conflict (email) do nothing;

-- ===================== 7) DEMO (TUỲ CHỌN) =====================

-- 7.0 Demo đăng ký + đăng nhập
-- select thu_vien.fn_dang_ky_tai_khoan('user01', 'matkhau123') as user_id_moi;
-- select * from thu_vien.fn_dang_nhap('user01', 'matkhau123');

-- 7.1 Demo mượn sách
do $$
declare
  v_user_id int;
  v_ban_doc_id int;
  v_phieu int;
begin
  select user_id into v_user_id from fn_dang_nhap('staff','123456') limit 1;
  select ban_doc_id into v_ban_doc_id from ban_doc where email='a@gmail.com';

  v_phieu := sp_muon_sach(
    v_user_id,
    v_ban_doc_id,
    current_date + 7,
    array['CC-001','DM-001'],
    'Demo muon sach co dang nhap'
  );

  raise notice 'Mượn thành công. phieu_muon_id=%', v_phieu;
end $$;

-- 7.2 Demo tạo quá hạn để test tiền phạt (không vi phạm check ngay_hen_tra >= ngay_muon)
do $$
declare
  v_phieu int;
begin
  select max(phieu_muon_id) into v_phieu from phieu_muon;

  update phieu_muon
  set ngay_muon = current_date - 10,
      ngay_hen_tra = current_date - 3
  where phieu_muon_id = v_phieu;

  raise notice 'Đã tạo quá hạn. phieu_muon_id=%', v_phieu;
end $$;

-- 7.3 Demo trả 1 bản sao
do $$
declare
  v_user_id int;
begin
  select user_id into v_user_id from fn_dang_nhap('staff','123456') limit 1;

  call sp_tra_sach(v_user_id, 'CC-001');

  raise notice 'Đã trả CC-001';
end $$;

-- 7.4 Xem tiền phạt / tồn kho / đang mượn
-- select * from tien_phat order by tien_phat_id desc;
-- select * from v_ton_kho_sach order by sach_id;
-- select * from v_dang_muon order by phieu_muon_id, ma_ban_sao;