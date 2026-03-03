set search_path to thu_vien;

-- 4.1 Đăng ký tài khoản (OUT: user_id)
create or replace procedure sp_dang_ky_tai_khoan(
  in  p_ten_dang_nhap text,
  in  p_mat_khau text,
  out o_user_id int
)
language plpgsql as $$
declare
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
  returning user_id into o_user_id;

exception
  when unique_violation then
    raise exception 'Tên đăng nhập đã tồn tại';
end $$;

-- 4.2 Đăng nhập (OUT: user_id, vai_tro)
create or replace procedure sp_dang_nhap(
  in  p_ten_dang_nhap text,
  in  p_mat_khau text,
  out o_user_id int,
  out o_vai_tro text
)
language plpgsql as $$
begin
  select u.user_id, u.vai_tro
  into o_user_id, o_vai_tro
  from tai_khoan_nguoi_dung u
  where u.ten_dang_nhap = p_ten_dang_nhap
    and u.dang_hoat_dong = true
    and u.mat_khau_hash = crypt(p_mat_khau, u.mat_khau_hash);

  if o_user_id is null then
    raise exception 'Sai tên đăng nhập hoặc mật khẩu';
  end if;
end $$;

-- 4.3 Thêm nhanh N bản sao
create or replace procedure sp_them_ban_sao(
  in p_sach_id int,
  in p_tien_to text,
  in p_so_luong int
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
    raise exception 'Không tìm thấy sequence cho ban_sao_sach.ban_sao_id';
  end if;

  for i in 1..p_so_luong loop
    execute format('select nextval(%L)', v_seq) into v_next_id;
    v_ma := p_tien_to || '-' || lpad(v_next_id::text, 4, '0');

    insert into ban_sao_sach(ban_sao_id, sach_id, ma_ban_sao, trang_thai)
    values (v_next_id, p_sach_id, v_ma, 'SAN_SANG');
  end loop;
end $$;

-- 4.4 Mượn sách (OUT: phieu_muon_id)
create or replace procedure sp_muon_sach(
  in  p_user_id int,
  in  p_ban_doc_id int,
  in  p_ngay_hen_tra date,
  in  p_ds_ma_ban_sao text[],
  in  p_ghi_chu text ,
  out o_phieu_muon_id int
)
language plpgsql as $$
declare
  v_count int;
  c text;
  v_ban_sao_id int;
  v_trang_thai text;
  v_ds_sorted text[];
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

  if exists (
    select 1 from unnest(p_ds_ma_ban_sao) x
    group by x having count(*) > 1
  ) then
    raise exception 'Danh sách mã bản sao bị trùng';
  end if;

  -- Sắp xếp để giảm khả năng deadlock khi đồng thời mượn nhiều bản sao
  select array_agg(x order by x) into v_ds_sorted
  from unnest(p_ds_ma_ban_sao) x;

  insert into phieu_muon(ban_doc_id, ngay_hen_tra, ghi_chu, tao_boi)
  values (p_ban_doc_id, p_ngay_hen_tra, p_ghi_chu, p_user_id)
  returning phieu_muon_id into o_phieu_muon_id;

  foreach c in array v_ds_sorted loop
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
    values (o_phieu_muon_id, v_ban_sao_id);
  end loop;
end $$;

-- 4.5 Trả sách
create or replace procedure sp_tra_sach(
  in p_user_id int,
  in p_ma_ban_sao text
)
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

  -- trạng thái bản sao + tiền phạt + đóng phiếu do trigger xử lý
end $$;

-- 4.6 Gia hạn (tối đa 2 lần) + kiểm tra thẻ bạn đọc còn hạn
create or replace procedure sp_gia_han(
  in p_user_id int,
  in p_phieu_muon_id int,
  in p_ngay_hen_tra_moi date
)
language plpgsql as $$
declare
  v_ngay_hen_tra date;
  v_so_lan int;
  v_trang_thai text;
  v_bd int;
  v_han_the date;
  v_bd_active boolean;
begin
  if not exists (select 1 from tai_khoan_nguoi_dung where user_id=p_user_id and dang_hoat_dong=true) then
    raise exception 'Không có quyền (cần đăng nhập)';
  end if;

  select pm.ngay_hen_tra, pm.so_lan_gia_han, pm.trang_thai, pm.ban_doc_id
  into v_ngay_hen_tra, v_so_lan, v_trang_thai, v_bd
  from phieu_muon pm
  where pm.phieu_muon_id = p_phieu_muon_id;

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

  -- (Policy) Thẻ bạn đọc còn hạn và đang hoạt động
  select han_the, dang_hoat_dong into v_han_the, v_bd_active
  from ban_doc where ban_doc_id = v_bd;

  if v_bd_active is not true or v_han_the < current_date then
    raise exception 'Thẻ bạn đọc đã hết hạn hoặc không hoạt động';
  end if;

  update phieu_muon
  set ngay_hen_tra = p_ngay_hen_tra_moi,
      so_lan_gia_han = so_lan_gia_han + 1
  where phieu_muon_id = p_phieu_muon_id;
end $$;

-- 4.7 Thanh toán tiền phạt
create or replace procedure sp_thanh_toan_tien_phat(
  in p_user_id int,
  in p_phieu_muon_id int,
  out o_tong_tien numeric(12,2)
)
language plpgsql as $$
begin
  if not exists (select 1 from tai_khoan_nguoi_dung where user_id=p_user_id and dang_hoat_dong=true) then
    raise exception 'Không có quyền (cần đăng nhập)';
  end if;

  select coalesce(sum(so_tien),0)
    into o_tong_tien
  from tien_phat
  where phieu_muon_id = p_phieu_muon_id
    and da_thanh_toan = false;

  update tien_phat
    set da_thanh_toan = true,
        thanh_toan_luc = now()
  where phieu_muon_id = p_phieu_muon_id
    and da_thanh_toan = false;
end $$;

-- 4.8 Cập nhật trạng thái bản sao an toàn (chống chuyển khi còn mượn mở)
create or replace procedure sp_cap_nhat_trang_thai_ban_sao(
  in p_user_id int,
  in p_ma_ban_sao text,
  in p_trang_thai text
)
language plpgsql as $$
declare
  v_ban_sao_id int;
begin
  if p_trang_thai not in ('SAN_SANG','DANG_MUON','MAT','HU_HONG') then
    raise exception 'Trạng thái không hợp lệ';
  end if;

  if not exists (select 1 from tai_khoan_nguoi_dung where user_id=p_user_id and dang_hoat_dong=true) then
    raise exception 'Không có quyền (cần đăng nhập)';
  end if;

  select ban_sao_id into v_ban_sao_id
  from ban_sao_sach where ma_ban_sao = p_ma_ban_sao
  for update;

  if v_ban_sao_id is null then
    raise exception 'Không tìm thấy mã bản sao';
  end if;

  if p_trang_thai in ('MAT','HU_HONG') and exists (
      select 1 from chi_tiet_muon where ban_sao_id = v_ban_sao_id and thoi_gian_tra is null
  ) then
    raise exception 'Bản sao đang được mượn, không thể đặt %', p_trang_thai;
  end if;

  update ban_sao_sach
  set trang_thai = p_trang_thai
  where ban_sao_id = v_ban_sao_id;
end $$;