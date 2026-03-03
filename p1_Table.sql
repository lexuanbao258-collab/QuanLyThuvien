
-- 0) RESET + SCHEMA
drop schema if exists thu_vien cascade;
create schema thu_vien;
set search_path to thu_vien;

-- Extensions
create extension if not exists pgcrypto;
create extension if not exists citext;

set search_path to thu_vien;

-- 1.1 Tài khoản người dùng
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

-- 1.3 Sách
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
  email citext unique,
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

-- 1.7 Chi tiết mượn
create table chi_tiet_muon (
  chi_tiet_muon_id serial primary key,
  phieu_muon_id int not null references phieu_muon(phieu_muon_id) on delete cascade,
  ban_sao_id int not null references ban_sao_sach(ban_sao_id),
  thoi_gian_muon timestamptz not null default now(),
  thoi_gian_tra timestamptz,
  tra_boi int references tai_khoan_nguoi_dung(user_id),
  -- Chống trùng bản sao trong cùng phiếu
  unique (phieu_muon_id, ban_sao_id),
  -- Trả phải >= mượn (nếu có trả)
  check (thoi_gian_tra is null or thoi_gian_tra >= thoi_gian_muon)
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
  unique (phieu_muon_id, ban_sao_id)
);
