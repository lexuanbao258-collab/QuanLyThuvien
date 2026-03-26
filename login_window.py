import tkinter as tk
from tkinter import messagebox

from db import get_connection
from main_window import MainWindow
from utils import friendly_error_message

class RegisterWindow:

    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Đăng ký tài khoản")
        self.top.geometry("420x270")
        self.top.resizable(False, False)
        self.top.grab_set()

        frame = tk.Frame(self.top, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="ĐĂNG KÝ TÀI KHOẢN", font=("Arial", 15, "bold"), fg="blue").pack(pady=10)

        form = tk.Frame(frame)
        form.pack(pady=10)

        tk.Label(form, text="Tên đăng nhập").grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = tk.Entry(form, width=28)
        self.username_entry.grid(row=0, column=1, pady=5)

        tk.Label(form, text="Mật khẩu").grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = tk.Entry(form, width=28, show="*")
        self.password_entry.grid(row=1, column=1, pady=5)

        tk.Label(form, text="Nhập lại mật khẩu").grid(row=2, column=0, sticky="w", pady=5)
        self.confirm_entry = tk.Entry(form, width=28, show="*")
        self.confirm_entry.grid(row=2, column=1, pady=5)

        btns = tk.Frame(frame)
        btns.pack(pady=10)

        tk.Button(btns, text="Đăng ký", width=14, bg="#4CAF50", fg="white", command=self.register).pack(side="left", padx=5)
        tk.Button(btns, text="Đóng", width=14, command=self.top.destroy).pack(side="left", padx=5)

        self.username_entry.focus()

    def register(self):
        username = self.username_entry.get().strip().lower()
        password = self.password_entry.get().strip()
        confirm = self.confirm_entry.get().strip()

        if not username or not password or not confirm:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin.", parent=self.top)
            return

        if password != confirm:
            messagebox.showwarning("Cảnh báo", "Mật khẩu nhập lại không khớp.", parent=self.top)
            return

        conn = None
        cur = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "CALL sp_dang_ky_tai_khoan(%s, %s, NULL);",
                (username, password)
            )
            result = cur.fetchone()
            conn.commit()

            user_id = result[0] if result else None
            messagebox.showinfo("Thành công", f"Đăng ký tài khoản thành công. Mã tài khoản: {user_id}", parent=self.top)
            self.top.destroy()

        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Lỗi", friendly_error_message(e), parent=self.top)
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()


class LoginWindow:

    def __init__(self, root):
        self.root = root
        self.root.title("Đăng nhập hệ thống thư viện")
        self.root.geometry("440x290")
        self.root.resizable(False, False)

        frame = tk.Frame(root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="QUẢN LÝ THƯ VIỆN", font=("Arial", 17, "bold"), fg="blue").pack(pady=12)

        form = tk.Frame(frame)
        form.pack(pady=10)

        tk.Label(form, text="Tên đăng nhập").grid(row=0, column=0, sticky="w", pady=6)
        self.username_entry = tk.Entry(form, width=28)
        self.username_entry.grid(row=0, column=1, pady=6)

        tk.Label(form, text="Mật khẩu").grid(row=1, column=0, sticky="w", pady=6)
        self.password_entry = tk.Entry(form, width=28, show="*")
        self.password_entry.grid(row=1, column=1, pady=6)

        btns = tk.Frame(frame)
        btns.pack(pady=15)

        tk.Button(btns, text="Đăng nhập", width=14, bg="#2196F3", fg="white", command=self.login).pack(side="left", padx=5)
        tk.Button(btns, text="Đăng ký", width=14, bg="#4CAF50", fg="white", command=self.open_register).pack(side="left", padx=5)
        tk.Button(btns, text="Thoát", width=14, command=self.root.destroy).pack(side="left", padx=5)

        self.username_entry.focus()
        self.root.bind("<Return>", lambda event: self.login())

    def open_register(self):
        RegisterWindow(self.root)

    def login(self):
        username = self.username_entry.get().strip().lower()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin.")
            return

        conn = None
        cur = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "CALL sp_dang_nhap(%s, %s, NULL, NULL);",
                (username, password)
            )
            row = cur.fetchone()
            conn.commit()

            if row:
                user_id, vai_tro = row
                messagebox.showinfo("Thành công", "Đăng nhập thành công.")
                self.root.destroy()

                root = tk.Tk()
                app = MainWindow(root, user_id, username, vai_tro)
                root.mainloop()
            else:
                messagebox.showerror("Lỗi", "Sai tên đăng nhập hoặc mật khẩu.")

        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Lỗi", friendly_error_message(e))
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

