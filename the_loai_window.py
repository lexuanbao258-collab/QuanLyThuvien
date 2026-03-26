import tkinter as tk
from tkinter import ttk, messagebox

from utils import friendly_error_message


class TheLoaiMixin:
    def build_categories_tab(self):
        top = tk.Frame(self.tab_categories)
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Tìm danh mục").pack(side="left")
        self.category_search_entry = tk.Entry(top, width=30)
        self.category_search_entry.pack(side="left", padx=5)
        tk.Button(top, text="Tìm", command=self.search_categories).pack(side="left", padx=5)
        tk.Button(top, text="Làm mới", command=self.load_categories).pack(side="left", padx=5)

        form = tk.LabelFrame(self.tab_categories, text="Thông tin danh mục", padx=10, pady=10)
        form.pack(fill="x", padx=10, pady=8)

        tk.Label(form, text="Tên danh mục").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.category_name_entry = tk.Entry(form, width=40)
        self.category_name_entry.grid(row=0, column=1, padx=5, pady=5)

        btns = tk.Frame(self.tab_categories)
        btns.pack(fill="x", padx=10, pady=5)
        tk.Button(btns, text="Thêm", width=15, bg="#4CAF50", fg="white", command=self.add_category).pack(side="left", padx=5)
        tk.Button(btns, text="Sửa", width=15, bg="#2196F3", fg="white", command=self.update_category).pack(side="left", padx=5)
        tk.Button(btns, text="Xóa", width=15, bg="#f44336", fg="white", command=self.delete_category).pack(side="left", padx=5)
        tk.Button(btns, text="Xóa form", width=15, command=self.clear_category_form).pack(side="left", padx=5)

        table_frame = tk.Frame(self.tab_categories)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id", "ten")
        self.category_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.category_tree.heading("id", text="ID")
        self.category_tree.heading("ten", text="Tên danh mục")
        self.category_tree.column("id", width=80, anchor="center")
        self.category_tree.column("ten", width=350)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.category_tree.yview)
        self.category_tree.configure(yscrollcommand=y_scroll.set)
        self.category_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        self.category_tree.bind("<<TreeviewSelect>>", self.on_category_select)
    def load_categories(self):
        try:
            self.clear_tree(self.category_tree)
            rows = self.execute("SELECT danh_muc_id, ten FROM danh_muc ORDER BY ten;", fetch=True)
            self.categories = {name: cid for cid, name in rows}
            for row in rows:
                self.category_tree.insert("", "end", values=row)

            names = list(self.categories.keys())
            if hasattr(self, "book_category_combo"):
                self.book_category_combo["values"] = names
            self.clear_category_form()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được danh mục.\n{friendly_error_message(e)}")
    def search_categories(self):
        kw = self.category_search_entry.get().strip()
        try:
            self.clear_tree(self.category_tree)
            rows = self.execute("""
                SELECT danh_muc_id, ten
                FROM danh_muc
                WHERE ten ILIKE %s
                ORDER BY ten;
            """, (f"%{kw}%",), fetch=True)
            for row in rows:
                self.category_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Tìm danh mục thất bại.\n{friendly_error_message(e)}")
    def add_category(self):
        name = self.category_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Cảnh báo", "Tên danh mục không được để trống.")
            return
        try:
            self.execute("INSERT INTO danh_muc(ten) VALUES (%s);", (name,))
            messagebox.showinfo("Thành công", "Thêm danh mục thành công.")
            self.load_categories()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Thêm danh mục thất bại.\n{friendly_error_message(e)}")
    def update_category(self):
        if not self.selected_category_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn danh mục.")
            return
        name = self.category_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Cảnh báo", "Tên danh mục không được để trống.")
            return
        try:
            self.execute("UPDATE danh_muc SET ten = %s WHERE danh_muc_id = %s;", (name, self.selected_category_id))
            messagebox.showinfo("Thành công", "Cập nhật danh mục thành công.")
            self.load_categories()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Cập nhật danh mục thất bại.\n{friendly_error_message(e)}")
    def delete_category(self):
        if not self.selected_category_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn danh mục.")
            return
        if not messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa danh mục này không?"):
            return
        try:
            self.execute("DELETE FROM danh_muc WHERE danh_muc_id = %s;", (self.selected_category_id,))
            messagebox.showinfo("Thành công", "Xóa danh mục thành công.")
            self.load_categories()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Xóa danh mục thất bại.\n{friendly_error_message(e)}")
    def on_category_select(self, event):
        sel = self.category_tree.focus()
        if not sel:
            return
        values = self.category_tree.item(sel, "values")
        self.selected_category_id = values[0]
        self.category_name_entry.delete(0, tk.END)
        self.category_name_entry.insert(0, values[1] or "")
    def clear_category_form(self):
        self.selected_category_id = None
        self.category_name_entry.delete(0, tk.END)

    # ===================== BOOKS =====================
