import tkinter as tk
from tkinter import ttk, messagebox

from utils import friendly_error_message


class NguoiDungMixin:
    def build_users_tab(self):
        top = tk.Frame(self.tab_users)
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Tìm tài khoản").pack(side="left")
        self.user_search_entry = tk.Entry(top, width=30)
        self.user_search_entry.pack(side="left", padx=5)
        tk.Button(top, text="Tìm", command=self.search_users).pack(side="left", padx=5)
        tk.Button(top, text="Làm mới", command=self.load_users).pack(side="left", padx=5)

        form = tk.LabelFrame(self.tab_users, text="Thông tin tài khoản", padx=10, pady=10)
        form.pack(fill="x", padx=10, pady=8)

        tk.Label(form, text="Tên đăng nhập").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.manage_user_username = tk.Entry(form, width=30)
        self.manage_user_username.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form, text="Mật khẩu mới").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.manage_user_password = tk.Entry(form, width=25, show="*")
        self.manage_user_password.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form, text="Vai trò").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.manage_user_role = ttk.Combobox(form, width=28, state="readonly", values=self.roles)
        self.manage_user_role.grid(row=1, column=1, padx=5, pady=5)

        self.manage_user_active = tk.BooleanVar(value=True)
        tk.Checkbutton(form, text="Đang hoạt động", variable=self.manage_user_active).grid(row=1, column=2, padx=5, pady=5, sticky="w")

        btns = tk.Frame(self.tab_users)
        btns.pack(fill="x", padx=10, pady=5)

        tk.Button(btns, text="Thêm", width=15, bg="#4CAF50", fg="white", command=self.add_user).pack(side="left", padx=5)
        tk.Button(btns, text="Sửa", width=15, bg="#2196F3", fg="white", command=self.update_user).pack(side="left", padx=5)
        tk.Button(btns, text="Khóa/Mở", width=15, bg="#FF9800", fg="white", command=self.toggle_user_active).pack(side="left", padx=5)
        tk.Button(btns, text="Xóa form", width=15, command=self.clear_user_form).pack(side="left", padx=5)

        table_frame = tk.Frame(self.tab_users)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id", "username", "role", "active", "created")
        self.user_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.user_tree.heading("id", text="ID")
        self.user_tree.heading("username", text="Tên đăng nhập")
        self.user_tree.heading("role", text="Vai trò")
        self.user_tree.heading("active", text="Hoạt động")
        self.user_tree.heading("created", text="Tạo lúc")

        self.user_tree.column("id", width=60, anchor="center")
        self.user_tree.column("username", width=220)
        self.user_tree.column("role", width=120)
        self.user_tree.column("active", width=100)
        self.user_tree.column("created", width=180)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=y_scroll.set)
        self.user_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        self.user_tree.bind("<<TreeviewSelect>>", self.on_user_select)
    def load_users(self):
        try:
            self.clear_tree(self.user_tree)
            rows = self.execute("""
                SELECT user_id, ten_dang_nhap, vai_tro, dang_hoat_dong, tao_luc
                FROM tai_khoan_nguoi_dung
                ORDER BY user_id;
            """, fetch=True)
            for row in rows:
                self.user_tree.insert("", "end", values=row)
            self.clear_user_form()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được tài khoản.\n{friendly_error_message(e)}")
    def search_users(self):
        kw = self.user_search_entry.get().strip()
        try:
            self.clear_tree(self.user_tree)
            rows = self.execute("""
                SELECT user_id, ten_dang_nhap, vai_tro, dang_hoat_dong, tao_luc
                FROM tai_khoan_nguoi_dung
                WHERE ten_dang_nhap ILIKE %s OR vai_tro ILIKE %s
                ORDER BY user_id;
            """, (f"%{kw}%", f"%{kw}%"), fetch=True)
            for row in rows:
                self.user_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Tìm tài khoản thất bại.\n{friendly_error_message(e)}")
    def add_user(self):
        if self.role != "QUAN_TRI":
            messagebox.showwarning("Không có quyền", "Chỉ QUAN_TRI mới được thêm tài khoản.")
            return

        username = self.manage_user_username.get().strip().lower()
        password = self.manage_user_password.get().strip()
        role = self.manage_user_role.get().strip() or "NHAN_VIEN"
        active = self.manage_user_active.get()

        if not username or len(username) < 3:
            messagebox.showwarning("Cảnh báo", "Tên đăng nhập phải có ít nhất 3 ký tự.")
            return
        if not password or len(password) < 6:
            messagebox.showwarning("Cảnh báo", "Mật khẩu phải có ít nhất 6 ký tự.")
            return

        try:
            self.execute("""
                INSERT INTO tai_khoan_nguoi_dung(ten_dang_nhap, mat_khau_hash, vai_tro, dang_hoat_dong)
                VALUES (LOWER(TRIM(%s)), crypt(%s, gen_salt('bf')), %s, %s);
            """, (username, password, role, active))
            messagebox.showinfo("Thành công", "Thêm tài khoản thành công.")
            self.load_users()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Thêm tài khoản thất bại.\n{friendly_error_message(e)}")
    def update_user(self):
        if self.role != "QUAN_TRI":
            messagebox.showwarning("Không có quyền", "Chỉ QUAN_TRI mới được sửa tài khoản.")
            return
        if not self.selected_user_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn tài khoản cần sửa.")
            return

        username = self.manage_user_username.get().strip().lower()
        password = self.manage_user_password.get().strip()
        role = self.manage_user_role.get().strip() or "NHAN_VIEN"
        active = self.manage_user_active.get()

        if not username:
            messagebox.showwarning("Cảnh báo", "Tên đăng nhập không được để trống.")
            return

        try:
            if password:
                self.execute("""
                    UPDATE tai_khoan_nguoi_dung
                    SET ten_dang_nhap = LOWER(TRIM(%s)),
                        mat_khau_hash = crypt(%s, gen_salt('bf')),
                        vai_tro = %s,
                        dang_hoat_dong = %s
                    WHERE user_id = %s;
                """, (username, password, role, active, self.selected_user_id))
            else:
                self.execute("""
                    UPDATE tai_khoan_nguoi_dung
                    SET ten_dang_nhap = LOWER(TRIM(%s)),
                        vai_tro = %s,
                        dang_hoat_dong = %s
                    WHERE user_id = %s;
                """, (username, role, active, self.selected_user_id))
            messagebox.showinfo("Thành công", "Cập nhật tài khoản thành công.")
            self.load_users()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Cập nhật tài khoản thất bại.\n{friendly_error_message(e)}")
    def toggle_user_active(self):
        if self.role != "QUAN_TRI":
            messagebox.showwarning("Không có quyền", "Chỉ QUAN_TRI mới được khóa/mở tài khoản.")
            return
        if not self.selected_user_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn tài khoản.")
            return
        try:
            self.execute("""
                UPDATE tai_khoan_nguoi_dung
                SET dang_hoat_dong = NOT dang_hoat_dong
                WHERE user_id = %s;
            """, (self.selected_user_id,))
            messagebox.showinfo("Thành công", "Đã cập nhật trạng thái tài khoản.")
            self.load_users()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Cập nhật trạng thái thất bại.\n{friendly_error_message(e)}")
    def on_user_select(self, event):
        sel = self.user_tree.focus()
        if not sel:
            return
        values = self.user_tree.item(sel, "values")
        self.selected_user_id = values[0]
        self.manage_user_username.delete(0, tk.END)
        self.manage_user_username.insert(0, values[1] or "")
        self.manage_user_password.delete(0, tk.END)
        self.manage_user_role.set(values[2] or "NHAN_VIEN")
        self.manage_user_active.set(str(values[3]).lower() == "true")
    def clear_user_form(self):
        self.selected_user_id = None
        self.manage_user_username.delete(0, tk.END)
        self.manage_user_password.delete(0, tk.END)
        self.manage_user_role.set("NHAN_VIEN")
        self.manage_user_active.set(True)

    # ===================== CATEGORIES =====================
