import tkinter as tk
from tkinter import ttk, messagebox

from utils import friendly_error_message, to_none, display_copy_option, extract_copy_code


class SachMixin:
    def build_books_tab(self):
        top = tk.Frame(self.tab_books)
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Tìm sách").pack(side="left")
        self.book_search_entry = tk.Entry(top, width=30)
        self.book_search_entry.pack(side="left", padx=5)
        tk.Button(top, text="Tìm", command=self.search_books).pack(side="left", padx=5)
        tk.Button(top, text="Làm mới", command=self.load_books).pack(side="left", padx=5)

        form = tk.LabelFrame(self.tab_books, text="Thông tin sách", padx=10, pady=10)
        form.pack(fill="x", padx=10, pady=8)

        tk.Label(form, text="Tiêu đề").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.book_title_entry = tk.Entry(form, width=35)
        self.book_title_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form, text="Tác giả").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.book_author_entry = tk.Entry(form, width=30)
        self.book_author_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form, text="Nhà xuất bản").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.book_publisher_entry = tk.Entry(form, width=35)
        self.book_publisher_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form, text="ISBN").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.book_isbn_entry = tk.Entry(form, width=30)
        self.book_isbn_entry.grid(row=1, column=3, padx=5, pady=5)

        tk.Label(form, text="Danh mục").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.book_category_combo = ttk.Combobox(form, width=32, state="readonly")
        self.book_category_combo.grid(row=2, column=1, padx=5, pady=5)

        btns = tk.Frame(self.tab_books)
        btns.pack(fill="x", padx=10, pady=5)
        tk.Button(btns, text="Thêm", bg="#4CAF50", fg="white", width=15, command=self.add_book).pack(side="left", padx=5)
        tk.Button(btns, text="Sửa", bg="#2196F3", fg="white", width=15, command=self.update_book).pack(side="left", padx=5)
        tk.Button(btns, text="Xóa", bg="#f44336", fg="white", width=15, command=self.delete_book).pack(side="left", padx=5)
        tk.Button(btns, text="Xóa form", width=15, command=self.clear_book_form).pack(side="left", padx=5)

        table_frame = tk.Frame(self.tab_books)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id", "tieu_de", "tac_gia", "nxb", "isbn", "danh_muc", "tao_luc")
        self.book_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, t, w in [
            ("id", "ID", 60),
            ("tieu_de", "Tiêu đề", 260),
            ("tac_gia", "Tác giả", 180),
            ("nxb", "Nhà xuất bản", 180),
            ("isbn", "ISBN", 140),
            ("danh_muc", "Danh mục", 140),
            ("tao_luc", "Tạo lúc", 170),
        ]:
            self.book_tree.heading(c, text=t)
            self.book_tree.column(c, width=w)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.book_tree.yview)
        self.book_tree.configure(yscrollcommand=y_scroll.set)
        self.book_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        self.book_tree.bind("<<TreeviewSelect>>", self.on_book_select)

    def load_books(self):
        try:
            self.clear_tree(self.book_tree)
            rows = self.execute(
                """
                SELECT s.sach_id, s.tieu_de, s.tac_gia, s.nha_xuat_ban, s.isbn, d.ten, s.tao_luc
                FROM sach s
                LEFT JOIN danh_muc d ON s.danh_muc_id = d.danh_muc_id
                ORDER BY s.sach_id;
                """,
                fetch=True,
            )
            for row in rows:
                self.book_tree.insert("", "end", values=row)

            if hasattr(self, "copy_book_combo"):
                self.copy_book_combo["values"] = [f"{r[0]} - {r[1]}" for r in rows]
            self.clear_book_form()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được sách.\n{friendly_error_message(e)}")

    def search_books(self):
        kw = self.book_search_entry.get().strip()
        try:
            self.clear_tree(self.book_tree)
            rows = self.execute(
                """
                SELECT s.sach_id, s.tieu_de, s.tac_gia, s.nha_xuat_ban, s.isbn, d.ten, s.tao_luc
                FROM sach s
                LEFT JOIN danh_muc d ON s.danh_muc_id = d.danh_muc_id
                WHERE s.tieu_de ILIKE %s
                   OR s.tac_gia ILIKE %s
                   OR COALESCE(s.isbn, '') ILIKE %s
                ORDER BY s.sach_id;
                """,
                (f"%{kw}%", f"%{kw}%", f"%{kw}%"),
                fetch=True,
            )
            for row in rows:
                self.book_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Tìm sách thất bại.\n{friendly_error_message(e)}")

    def add_book(self):
        title = self.book_title_entry.get().strip()
        author = self.book_author_entry.get().strip()
        publisher = to_none(self.book_publisher_entry.get())
        isbn = to_none(self.book_isbn_entry.get())
        category_id = self.categories.get(self.book_category_combo.get().strip())

        if not title or not author:
            messagebox.showwarning("Cảnh báo", "Tiêu đề và tác giả không được để trống.")
            return

        try:
            self.execute(
                """
                INSERT INTO sach(tieu_de, tac_gia, nha_xuat_ban, isbn, danh_muc_id)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (title, author, publisher, isbn, category_id),
            )
            messagebox.showinfo("Thành công", "Thêm sách thành công.")
            self.load_books()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Thêm sách thất bại.\n{friendly_error_message(e)}")

    def update_book(self):
        if not self.selected_book_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn sách cần sửa.")
            return

        title = self.book_title_entry.get().strip()
        author = self.book_author_entry.get().strip()
        publisher = to_none(self.book_publisher_entry.get())
        isbn = to_none(self.book_isbn_entry.get())
        category_id = self.categories.get(self.book_category_combo.get().strip())

        if not title or not author:
            messagebox.showwarning("Cảnh báo", "Tiêu đề và tác giả không được để trống.")
            return

        try:
            self.execute(
                """
                UPDATE sach
                SET tieu_de = %s,
                    tac_gia = %s,
                    nha_xuat_ban = %s,
                    isbn = %s,
                    danh_muc_id = %s
                WHERE sach_id = %s;
                """,
                (title, author, publisher, isbn, category_id, self.selected_book_id),
            )
            messagebox.showinfo("Thành công", "Cập nhật sách thành công.")
            self.load_books()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Cập nhật sách thất bại.\n{friendly_error_message(e)}")

    def delete_book(self):
        if self.role != "QUAN_TRI":
            messagebox.showwarning("Không có quyền", "Chỉ QUAN_TRI mới được xóa sách.")
            return
        if not self.selected_book_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn sách cần xóa.")
            return
        if not messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa sách này không?"):
            return

        try:
            self.execute("DELETE FROM sach WHERE sach_id = %s;", (self.selected_book_id,))
            messagebox.showinfo("Thành công", "Xóa sách thành công.")
            self.load_books()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Xóa sách thất bại.\n{friendly_error_message(e)}")

    def on_book_select(self, event):
        sel = self.book_tree.focus()
        if not sel:
            return
        values = self.book_tree.item(sel, "values")
        self.selected_book_id = values[0]
        self.book_title_entry.delete(0, tk.END)
        self.book_title_entry.insert(0, values[1] or "")
        self.book_author_entry.delete(0, tk.END)
        self.book_author_entry.insert(0, values[2] or "")
        self.book_publisher_entry.delete(0, tk.END)
        self.book_publisher_entry.insert(0, values[3] or "")
        self.book_isbn_entry.delete(0, tk.END)
        self.book_isbn_entry.insert(0, values[4] or "")
        self.book_category_combo.set(values[5] or "")

    def clear_book_form(self):
        self.selected_book_id = None
        self.book_title_entry.delete(0, tk.END)
        self.book_author_entry.delete(0, tk.END)
        self.book_publisher_entry.delete(0, tk.END)
        self.book_isbn_entry.delete(0, tk.END)
        self.book_category_combo.set("")

    def _set_copy_combo_by_code(self, code):
        if not hasattr(self, "copy_code_combo"):
            return
        target = str(code or "").strip()
        for value in self.copy_code_combo.cget("values"):
            if extract_copy_code(value) == target:
                self.copy_code_combo.set(value)
                return
        self.copy_code_combo.set(target)

    def _refresh_copy_code_options(self):
        if not hasattr(self, "copy_code_combo"):
            return
        rows = self.execute(
            """
            SELECT bss.ma_ban_sao, s.tieu_de
            FROM ban_sao_sach bss
            JOIN sach s ON s.sach_id = bss.sach_id
            ORDER BY bss.ma_ban_sao;
            """,
            fetch=True,
        )
        self.copy_code_combo["values"] = [display_copy_option(row[0], row[1]) for row in rows]

    # ===================== COPIES =====================
    def build_copies_tab(self):
        top = tk.Frame(self.tab_copies)
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Tìm bản sao").pack(side="left")
        self.copy_search_entry = tk.Entry(top, width=30)
        self.copy_search_entry.pack(side="left", padx=5)
        tk.Button(top, text="Tìm", command=self.search_copies).pack(side="left", padx=5)
        tk.Button(top, text="Làm mới", command=self.load_copies).pack(side="left", padx=5)

        quick_add = tk.LabelFrame(self.tab_copies, text="Thêm nhanh bản sao", padx=10, pady=10)
        quick_add.pack(fill="x", padx=10, pady=8)

        tk.Label(quick_add, text="Sách").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.copy_book_combo = ttk.Combobox(quick_add, width=45, state="readonly")
        self.copy_book_combo.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(quick_add, text="Tiền tố").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.copy_prefix_entry = tk.Entry(quick_add, width=18)
        self.copy_prefix_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(quick_add, text="Số lượng").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.copy_quantity_entry = tk.Entry(quick_add, width=10)
        self.copy_quantity_entry.grid(row=0, column=5, padx=5, pady=5)

        tk.Button(quick_add, text="Thêm bản sao", width=15, bg="#4CAF50", fg="white", command=self.add_copies_quick).grid(row=0, column=6, padx=10, pady=5)

        edit = tk.LabelFrame(self.tab_copies, text="Cập nhật trạng thái / ghi chú", padx=10, pady=10)
        edit.pack(fill="x", padx=10, pady=8)

        tk.Label(edit, text="Mã bản sao").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.copy_code_combo = ttk.Combobox(edit, width=32, state="readonly")
        self.copy_code_combo.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(edit, text="Trạng thái").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.copy_status_combo = ttk.Combobox(edit, width=20, state="readonly", values=self.copy_statuses)
        self.copy_status_combo.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(edit, text="Ghi chú").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.copy_note_entry = tk.Entry(edit, width=50)
        self.copy_note_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="w")

        tk.Button(edit, text="Cập nhật trạng thái", width=16, bg="#2196F3", fg="white", command=self.update_copy_status).grid(row=0, column=4, padx=8, pady=5)
        tk.Button(edit, text="Lưu ghi chú", width=16, bg="#607D8B", fg="white", command=self.update_copy_note).grid(row=1, column=4, padx=8, pady=5)

        table_frame = tk.Frame(self.tab_copies)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id", "sach_id", "ma_ban_sao", "tieu_de", "trang_thai", "ghi_chu")
        self.copy_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, t, w in [
            ("id", "ID", 60),
            ("sach_id", "Sách ID", 80),
            ("ma_ban_sao", "Mã bản sao", 120),
            ("tieu_de", "Tiêu đề", 300),
            ("trang_thai", "Trạng thái", 120),
            ("ghi_chu", "Ghi chú", 220),
        ]:
            self.copy_tree.heading(c, text=t)
            self.copy_tree.column(c, width=w)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.copy_tree.yview)
        self.copy_tree.configure(yscrollcommand=y_scroll.set)
        self.copy_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        self.copy_tree.bind("<<TreeviewSelect>>", self.on_copy_select)

    def load_copies(self):
        try:
            self.clear_tree(self.copy_tree)
            rows = self.execute(
                """
                SELECT bss.ban_sao_id, bss.sach_id, bss.ma_ban_sao, s.tieu_de, bss.trang_thai, bss.ghi_chu
                FROM ban_sao_sach bss
                JOIN sach s ON s.sach_id = bss.sach_id
                ORDER BY bss.ban_sao_id;
                """,
                fetch=True,
            )
            for row in rows:
                self.copy_tree.insert("", "end", values=row)
            self._refresh_copy_code_options()
            if hasattr(self, "refresh_borrow_op_options"):
                self.refresh_borrow_op_options()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được bản sao.\n{friendly_error_message(e)}")

    def search_copies(self):
        kw = self.copy_search_entry.get().strip()
        try:
            self.clear_tree(self.copy_tree)
            rows = self.execute(
                """
                SELECT bss.ban_sao_id, bss.sach_id, bss.ma_ban_sao, s.tieu_de, bss.trang_thai, bss.ghi_chu
                FROM ban_sao_sach bss
                JOIN sach s ON s.sach_id = bss.sach_id
                WHERE bss.ma_ban_sao ILIKE %s
                   OR s.tieu_de ILIKE %s
                   OR bss.trang_thai ILIKE %s
                ORDER BY bss.ban_sao_id;
                """,
                (f"%{kw}%", f"%{kw}%", f"%{kw}%"),
                fetch=True,
            )
            for row in rows:
                self.copy_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Tìm bản sao thất bại.\n{friendly_error_message(e)}")

    def add_copies_quick(self):
        book_text = self.copy_book_combo.get().strip()
        prefix = self.copy_prefix_entry.get().strip()
        quantity = self.copy_quantity_entry.get().strip()

        if not book_text:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn sách.")
            return
        if not prefix:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tiền tố.")
            return
        if not quantity.isdigit() or int(quantity) <= 0:
            messagebox.showwarning("Cảnh báo", "Số lượng phải là số nguyên dương.")
            return

        try:
            book_id = int(book_text.split(" - ")[0])
            self.execute("CALL sp_them_ban_sao(%s, %s, %s);", (book_id, prefix, int(quantity)))
            messagebox.showinfo("Thành công", "Thêm bản sao thành công.")
            self.copy_prefix_entry.delete(0, tk.END)
            self.copy_quantity_entry.delete(0, tk.END)
            self.load_copies()
            self.load_inventory()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Thêm bản sao thất bại.\n{friendly_error_message(e)}")

    def update_copy_status(self):
        code = extract_copy_code(self.copy_code_combo.get())
        status = self.copy_status_combo.get().strip()
        if not code or not status:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn mã bản sao và trạng thái.")
            return
        try:
            self.execute("CALL sp_cap_nhat_trang_thai_ban_sao(%s, %s, %s);", (self.user_id, code, status))
            messagebox.showinfo("Thành công", "Cập nhật trạng thái thành công.")
            self.load_copies()
            self.load_inventory()
            self.load_borrowings_open()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Cập nhật trạng thái thất bại.\n{friendly_error_message(e)}")

    def update_copy_note(self):
        code = extract_copy_code(self.copy_code_combo.get())
        note = to_none(self.copy_note_entry.get())
        if not code:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn mã bản sao.")
            return
        try:
            self.execute("UPDATE ban_sao_sach SET ghi_chu = %s WHERE ma_ban_sao = %s;", (note, code))
            messagebox.showinfo("Thành công", "Lưu ghi chú thành công.")
            self.load_copies()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lưu ghi chú thất bại.\n{friendly_error_message(e)}")

    def on_copy_select(self, event):
        sel = self.copy_tree.focus()
        if not sel:
            return
        values = self.copy_tree.item(sel, "values")
        self._set_copy_combo_by_code(values[2] or "")
        self.copy_status_combo.set(values[4] or "")
        self.copy_note_entry.delete(0, tk.END)
        self.copy_note_entry.insert(0, values[5] or "")
