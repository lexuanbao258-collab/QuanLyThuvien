set search_path to thu_vien;

-- 5.0 Bảo vệ trạng thái ban_sao_sach khỏi update tay gây sai logic
create or replace function trg_bao_ve_trang_thai_ban_sao()
returns trigger
language plpgsql as $$
begin
  -- Không thể đặt SAN_SANG nếu còn mượn mở
  if new.trang_thai = 'SAN_SANG' and exists (
    select 1 from chi_tiet_muon
    where ban_sao_id = new.ban_sao_id and thoi_gian_tra is null
  ) then
    raise exception 'Không thể đặt SAN_SANG vì bản sao đang được mượn';
  end if;

  -- Không thể đặt DANG_MUON nếu không có bản ghi mượn đang mở
  if new.trang_thai = 'DANG_MUON' and not exists (
    select 1 from chi_tiet_muon
    where ban_sao_id = new.ban_sao_id and thoi_gian_tra is null
  ) then
    raise exception 'Không thể đặt DANG_MUON vì không có bản ghi mượn đang mở';
  end if;

  -- Không thể đặt MAT/HU_HONG khi còn mượn mở
  if new.trang_thai in ('MAT','HU_HONG') and exists (
    select 1 from chi_tiet_muon
    where ban_sao_id = new.ban_sao_id and thoi_gian_tra is null
  ) then
    raise exception 'Không thể đặt % vì bản sao đang được mượn', new.trang_thai;
  end if;

  return new;
end $$;

drop trigger if exists bao_ve_trang_thai on ban_sao_sach;
create trigger bao_ve_trang_thai
before update of trang_thai on ban_sao_sach
for each row execute function trg_bao_ve_trang_thai_ban_sao();

-- 5.1 Trước khi mượn: phiếu phải DANG_MUON, tối đa 5 cuốn, bản sao SAN_SANG
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

  -- mỗi phiếu tối đa 5 cuốn (tổng dòng chi tiết trong phiếu)
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

-- 5.2 Sau khi mượn: set bản sao -> DANG_MUON
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

-- 5.3 Sau khi trả: set bản sao -> SAN_SANG, tính phạt nếu trễ, đóng phiếu nếu trả hết
create or replace function trg_sau_khi_tra()
returns trigger
language plpgsql as $$
declare
  v_ngay_hen_tra date;
  v_so_ngay_tre int;
  v_so_tien numeric(12,2);
begin
  if old.thoi_gian_tra is null and new.thoi_gian_tra is not null then

    update ban_sao_sach
    set trang_thai='SAN_SANG'
    where ban_sao_id = new.ban_sao_id;

    select ngay_hen_tra into v_ngay_hen_tra
    from phieu_muon
    where phieu_muon_id = new.phieu_muon_id;

    v_so_ngay_tre := greatest(0, (new.thoi_gian_tra::date - v_ngay_hen_tra));
    v_so_tien := v_so_ngay_tre * 2000;

    if v_so_ngay_tre > 0 then
      insert into tien_phat(phieu_muon_id, ban_sao_id, so_ngay_tre, so_tien)
      values (new.phieu_muon_id, new.ban_sao_id, v_so_ngay_tre, v_so_tien)
      on conflict (phieu_muon_id, ban_sao_id) do update
      set so_ngay_tre = excluded.so_ngay_tre,
          so_tien = excluded.so_tien,
          tao_luc = now()
      where tien_phat.da_thanh_toan = false;
    end if;

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