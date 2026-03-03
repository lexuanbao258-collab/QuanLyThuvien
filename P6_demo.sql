set search_path to thu_vien;

-- SAMPLE DATA
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

-- ====== DEMO (tuỳ chọn): Mở comment từng khối để test ======

-- 6.1 Đăng ký tài khoản
-- do $$
-- declare v_user int;
-- begin
--   call sp_dang_ky_tai_khoan('user01','matkhau123', v_user);
--   raise notice 'Đăng ký OK. user_id=%', v_user;
-- end $$;

-- 6.2 Đăng nhập
-- do $$
-- declare v_user int; v_role text;
-- begin
--   call sp_dang_nhap('staff','123456', v_user, v_role);
--   raise notice 'Đăng nhập OK. user_id=%, role=%', v_user, v_role;
-- end $$;

-- 6.3 Mượn sách
-- do $$
-- declare v_user int; v_role text; v_bd int; v_phieu int;
-- begin
--   call sp_dang_nhap('staff','123456', v_user, v_role);
--   select ban_doc_id into v_bd from ban_doc where email='a@gmail.com';
--   call sp_muon_sach(v_user, v_bd, current_date + 7, array['CC-001','DM-001'], 'Demo muon', v_phieu);
--   raise notice 'Mượn OK. phieu_muon_id=%', v_phieu;
-- end $$;

-- 6.4 Trả sách
-- do $$
-- declare v_user int; v_role text;
-- begin
--   call sp_dang_nhap('staff','123456', v_user, v_role);
--   call sp_tra_sach(v_user, 'CC-001');
--   raise notice 'Đã trả CC-001';
-- end $$;

-- 6.5 Thanh toán tiền phạt
-- do $$
-- declare v_user int; v_role text; v_tong numeric(12,2);
-- begin
--   call sp_dang_nhap('admin','123456', v_user, v_role);
--   -- thay 1 bằng phieu_muon_id thực tế
--   call sp_thanh_toan_tien_phat(v_user, 1, v_tong);
--   raise notice 'Đã thu phạt. Tổng tiền=%.', v_tong;
-- end $$;
