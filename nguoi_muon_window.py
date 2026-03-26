import tkinter as tk
from tkinter import ttk, messagebox

from utils import friendly_error_message, valid_date, to_none, valid_email, valid_phone, digits_only


class NguoiMuonMixin:
    def build_readers_tab(self):
        top = tk.Frame(self.tab_readers)
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Tìm bạn đọc").pack(side="left")
        self.reader_search_entry = tk.Entry(top, width=30)
        self.reader_search_entry.pack(side="left", padx=5)
        tk.Button(top, text="Tìm", command=self.search_readers).pack(side="left", padx=5)
        tk.Button(top, text="Làm mới", command=self.load_readers).pack(side="left", padx=5)

        form = tk.LabelFrame(self.tab_readers, text="Thông tin bạn đọc", padx=10, pady=10)
        form.pack(fill="x", padx=10, pady=8)

        phone_vcmd = (self.root.register(digits_only), "%P")

        tk.Label(form, text="Họ tên").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.reader_name_entry = tk.Entry(form, width=35)
        self.reader_name_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form, text="Loại").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.reader_type_combo = ttk.Combobox(form, width=28, state="readonly", values=self.reader_types)
        self.reader_type_combo.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form, text="Email").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.reader_email_entry = tk.Entry(form, width=35)
        self.reader_email_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form, text="SĐT").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.reader_phone_entry = tk.Entry(
            form,
            width=28,
            validate="key",
            validatecommand=phone_vcmd,
        )
        self.reader_phone_entry.grid(row=1, column=3, padx=5, pady=5)

        tk.Label(form, text="Hạn thẻ (YYYY-MM-DD)").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.reader_expiry_entry = tk.Entry(form, width=35)
        self.reader_expiry_entry.grid(row=2, column=1, padx=5, pady=5)

        self.reader_active_var = tk.BooleanVar(value=True)
        tk.Checkbutton(form, text="Đang hoạt động", variable=self.reader_active_var).grid(row=2, column=2, padx=5, pady=5, sticky="w")

        btns = tk.Frame(self.tab_readers)
        btns.pack(fill="x", padx=10, pady=5)
        tk.Button(btns, text="Thêm", width=15, bg="#4CAF50", fg="white", command=self.add_reader).pack(side="left", padx=5)
        tk.Button(btns, text="Sửa", width=15, bg="#2196F3", fg="white", command=self.update_reader).pack(side="left", padx=5)
        tk.Button(btns, text="Xóa", width=15, bg="#f44336", fg="white", command=self.delete_reader).pack(side="left", padx=5)
        tk.Button(btns, text="Xóa form", width=15, command=self.clear_reader_form).pack(side="left", padx=5)

        table_frame = tk.Frame(self.tab_readers)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id", "ho_ten", "loai", "email", "sdt", "han_the", "active")
        self.reader_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, t, w in [
            ("id", "ID", 60),
            ("ho_ten", "Họ tên", 220),
            ("loai", "Loại", 120),
            ("email", "Email", 220),
            ("sdt", "SĐT", 120),
            ("han_the", "Hạn thẻ", 110),
            ("active", "Hoạt động", 100),
        ]:
            self.reader_tree.heading(c, text=t)
            self.reader_tree.column(c, width=w)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.reader_tree.yview)
        self.reader_tree.configure(yscrollcommand=y_scroll.set)
        self.reader_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        self.reader_tree.bind("<<TreeviewSelect>>", self.on_reader_select)

    def _validate_reader_form(self, name, email, phone, expiry):
        if not name:
            messagebox.showwarning("Cảnh báo", "Họ tên không được để trống.")
            return False
        if not valid_date(expiry):
            messagebox.showwarning("Cảnh báo", "Hạn thẻ không hợp lệ. Định dạng YYYY-MM-DD.")
            return False
        if not valid_email(email):
            messagebox.showwarning("Cảnh báo", "Email không đúng định dạng.")
            return False
        if not valid_phone(phone):
            messagebox.showwarning("Cảnh báo", "Số điện thoại phải gồm đúng 10 chữ số.")
            return False
        return True

    def load_readers(self):
        try:
            self.clear_tree(self.reader_tree)
            rows = self.execute(
                """
                SELECT ban_doc_id, ho_ten, loai_ban_doc, email, sdt, han_the, dang_hoat_dong
                FROM ban_doc
                ORDER BY ban_doc_id;
                """,
                fetch=True,
            )
            for row in rows:
                self.reader_tree.insert("", "end", values=row)
            self.clear_reader_form()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được bạn đọc.\n{friendly_error_message(e)}")

    def search_readers(self):
        kw = self.reader_search_entry.get().strip()
        try:
            self.clear_tree(self.reader_tree)
            rows = self.execute(
                """
                SELECT ban_doc_id, ho_ten, loai_ban_doc, email, sdt, han_the, dang_hoat_dong
                FROM ban_doc
                WHERE ho_ten ILIKE %s
                   OR COALESCE(email, '') ILIKE %s
                   OR COALESCE(sdt, '') ILIKE %s
                ORDER BY ban_doc_id;
                """,
                (f"%{kw}%", f"%{kw}%", f"%{kw}%"),
                fetch=True,
            )
            for row in rows:
                self.reader_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Tìm bạn đọc thất bại.\n{friendly_error_message(e)}")

    def add_reader(self):
        name = self.reader_name_entry.get().strip()
        rtype = self.reader_type_combo.get().strip() or "HOC_SINH"
        email = to_none(self.reader_email_entry.get())
        phone = to_none(self.reader_phone_entry.get())
        expiry = self.reader_expiry_entry.get().strip()
        active = self.reader_active_var.get()

        if not self._validate_reader_form(name, email, phone, expiry):
            return

        try:
            self.execute(
                """
                INSERT INTO ban_doc(ho_ten, loai_ban_doc, email, sdt, han_the, dang_hoat_dong)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (name, rtype, email, phone, expiry, active),
            )
            messagebox.showinfo("Thành công", "Thêm bạn đọc thành công.")
            self.load_readers()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Thêm bạn đọc thất bại.\n{friendly_error_message(e)}")

    def update_reader(self):
        if not self.selected_reader_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn bạn đọc.")
            return

        name = self.reader_name_entry.get().strip()
        rtype = self.reader_type_combo.get().strip() or "HOC_SINH"
        email = to_none(self.reader_email_entry.get())
        phone = to_none(self.reader_phone_entry.get())
        expiry = self.reader_expiry_entry.get().strip()
        active = self.reader_active_var.get()

        if not self._validate_reader_form(name, email, phone, expiry):
            return

        try:
            self.execute(
                """
                UPDATE ban_doc
                SET ho_ten = %s,
                    loai_ban_doc = %s,
                    email = %s,
                    sdt = %s,
                    han_the = %s,
                    dang_hoat_dong = %s
                WHERE ban_doc_id = %s;
                """,
                (name, rtype, email, phone, expiry, active, self.selected_reader_id),
            )
            messagebox.showinfo("Thành công", "Cập nhật bạn đọc thành công.")
            self.load_readers()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Cập nhật bạn đọc thất bại.\n{friendly_error_message(e)}")

    def delete_reader(self):
        if self.role != "QUAN_TRI":
            messagebox.showwarning("Không có quyền", "Chỉ QUAN_TRI mới được xóa bạn đọc.")
            return
        if not self.selected_reader_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn bạn đọc.")
            return
        if not messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa bạn đọc này không?"):
            return

        try:
            self.execute("DELETE FROM ban_doc WHERE ban_doc_id = %s;", (self.selected_reader_id,))
            messagebox.showinfo("Thành công", "Xóa bạn đọc thành công.")
            self.load_readers()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Xóa bạn đọc thất bại.\n{friendly_error_message(e)}")

    def on_reader_select(self, event):
        sel = self.reader_tree.focus()
        if not sel:
            return
        values = self.reader_tree.item(sel, "values")
        self.selected_reader_id = values[0]
        self.reader_name_entry.delete(0, tk.END)
        self.reader_name_entry.insert(0, values[1] or "")
        self.reader_type_combo.set(values[2] or "HOC_SINH")
        self.reader_email_entry.delete(0, tk.END)
        self.reader_email_entry.insert(0, values[3] or "")
        self.reader_phone_entry.delete(0, tk.END)
        self.reader_phone_entry.insert(0, values[4] or "")
        self.reader_expiry_entry.delete(0, tk.END)
        self.reader_expiry_entry.insert(0, str(values[5]) if values[5] else "")
        self.reader_active_var.set(str(values[6]).lower() == "true")

    def clear_reader_form(self):
        self.selected_reader_id = None
        self.reader_name_entry.delete(0, tk.END)
        self.reader_type_combo.set("HOC_SINH")
        self.reader_email_entry.delete(0, tk.END)
        self.reader_phone_entry.delete(0, tk.END)
        self.reader_expiry_entry.delete(0, tk.END)
        self.reader_active_var.set(True)
