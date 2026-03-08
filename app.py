import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import psycopg2

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "BaitaplonCSDL",
    "user": "postgres",
    "password": "25082006",
}


def get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SET search_path TO thu_vien;")
    cur.close()
    return conn


def valid_date(text: str) -> bool:
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def to_none(text: str):
    text = text.strip()
    return text if text else None


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
            cur.execute("""
                INSERT INTO tai_khoan_nguoi_dung(ten_dang_nhap, mat_khau_hash, vai_tro, dang_hoat_dong)
                VALUES (LOWER(TRIM(%s)), crypt(%s, gen_salt('bf')), 'NHAN_VIEN', true);
            """, (username, password))
            conn.commit()
            messagebox.showinfo("Thành công", "Đăng ký tài khoản thành công.", parent=self.top)
            self.top.destroy()
        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Lỗi", f"Đăng ký thất bại.\n{e}", parent=self.top)
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

            query = """
                SELECT user_id, ten_dang_nhap, vai_tro
                FROM tai_khoan_nguoi_dung
                WHERE ten_dang_nhap = %s
                  AND dang_hoat_dong = true
                  AND mat_khau_hash = crypt(%s, mat_khau_hash)
            """

            cur.execute(query, (username, password))
            row = cur.fetchone()

            if row:
                user_id, ten_dang_nhap, vai_tro = row
                messagebox.showinfo("Thành công", "Đăng nhập thành công")

                self.root.destroy()

                root = tk.Tk()
                app = LibraryApp(root, user_id, ten_dang_nhap, vai_tro)
                root.mainloop()
            else:
                messagebox.showerror("Lỗi", "Sai tên đăng nhập hoặc mật khẩu.")

        except Exception as e:
            messagebox.showerror("Lỗi", str(e))
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()


class LibraryApp:
    def __init__(self, root, user_id, username, role):
        self.root = root
        self.user_id = user_id
        self.username = username
        self.role = role

        self.root.title("Ứng dụng quản lý thư viện")
        self.root.geometry("1500x840")

        self.categories = {}
        self.reader_types = ["HOC_SINH", "GIAO_VIEN", "KHACH"]
        self.copy_statuses = ["SAN_SANG", "DANG_MUON", "MAT", "HU_HONG"]
        self.roles = ["QUAN_TRI", "NHAN_VIEN"]

        self.selected_category_id = None
        self.selected_user_id = None
        self.selected_book_id = None
        self.selected_reader_id = None

        self.create_header()
        self.create_tabs()
        self.refresh_all()

    def create_header(self):
        header = tk.Frame(self.root, bg="#1976D2", height=60)
        header.pack(fill="x")

        tk.Label(
            header,
            text="HỆ THỐNG QUẢN LÝ THƯ VIỆN",
            bg="#1976D2",
            fg="white",
            font=("Arial", 18, "bold")
        ).pack(side="left", padx=20, pady=12)

        tk.Label(
            header,
            text=f"Đăng nhập: {self.username} | Vai trò: {self.role}",
            bg="#1976D2",
            fg="white",
            font=("Arial", 11, "bold")
        ).pack(side="right", padx=20)

    def create_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_users = ttk.Frame(self.notebook)
        self.tab_categories = ttk.Frame(self.notebook)
        self.tab_books = ttk.Frame(self.notebook)
        self.tab_copies = ttk.Frame(self.notebook)
        self.tab_readers = ttk.Frame(self.notebook)
        self.tab_borrow_ops = ttk.Frame(self.notebook)
        self.tab_loans = ttk.Frame(self.notebook)
        self.tab_loan_details = ttk.Frame(self.notebook)
        self.tab_fines = ttk.Frame(self.notebook)
        self.tab_inventory = ttk.Frame(self.notebook)
        self.tab_reports = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_users, text="Tài khoản")
        self.notebook.add(self.tab_categories, text="Danh mục")
        self.notebook.add(self.tab_books, text="Sách")
        self.notebook.add(self.tab_copies, text="Bản sao")
        self.notebook.add(self.tab_readers, text="Bạn đọc")
        self.notebook.add(self.tab_borrow_ops, text="Mượn / Trả / Gia hạn")
        self.notebook.add(self.tab_loans, text="Phiếu mượn")
        self.notebook.add(self.tab_loan_details, text="Chi tiết mượn")
        self.notebook.add(self.tab_fines, text="Tiền phạt")
        self.notebook.add(self.tab_inventory, text="Tồn kho")
        self.notebook.add(self.tab_reports, text="Báo cáo")

        self.build_users_tab()
        self.build_categories_tab()
        self.build_books_tab()
        self.build_copies_tab()
        self.build_readers_tab()
        self.build_borrow_ops_tab()
        self.build_loans_tab()
        self.build_loan_details_tab()
        self.build_fines_tab()
        self.build_inventory_tab()
        self.build_reports_tab()

    def execute(self, query, params=None, fetch=False, fetchone=False):
        conn = None
        cur = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(query, params)
            result = None
            if fetchone:
                result = cur.fetchone()
            elif fetch:
                result = cur.fetchall()
            conn.commit()
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    def refresh_all(self):
        self.load_categories()
        self.load_users()
        self.load_books()
        self.load_copies()
        self.load_readers()
        self.load_loans()
        self.load_loan_details()
        self.load_fines()
        self.load_inventory()
        self.load_borrowings_open()
        self.load_reports()

    def export_loan_pdf(self):
        selected = self.loan_tree.focus()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một phiếu mượn để xuất PDF.")
            return

        values = self.loan_tree.item(selected, "values")
        phieu_muon_id = values[0]

        try:
            loan_info = self.execute("""
                SELECT pm.phieu_muon_id,
                       bd.ho_ten,
                       bd.email,
                       bd.sdt,
                       pm.ngay_muon,
                       pm.ngay_hen_tra,
                       pm.trang_thai,
                       pm.so_lan_gia_han,
                       pm.ghi_chu,
                       tk.ten_dang_nhap
                FROM phieu_muon pm
                JOIN ban_doc bd ON bd.ban_doc_id = pm.ban_doc_id
                LEFT JOIN tai_khoan_nguoi_dung tk ON tk.user_id = pm.tao_boi
                WHERE pm.phieu_muon_id = %s;
            """, (phieu_muon_id,), fetchone=True)

            detail_rows = self.execute("""
                SELECT bss.ma_ban_sao, s.tieu_de, s.tac_gia, ctm.thoi_gian_muon, ctm.thoi_gian_tra
                FROM chi_tiet_muon ctm
                JOIN ban_sao_sach bss ON bss.ban_sao_id = ctm.ban_sao_id
                JOIN sach s ON s.sach_id = bss.sach_id
                WHERE ctm.phieu_muon_id = %s
                ORDER BY ctm.chi_tiet_muon_id;
            """, (phieu_muon_id,), fetch=True)

            if not loan_info:
                messagebox.showerror("Lỗi", "Không tìm thấy dữ liệu phiếu mượn.")
                return

            filepath = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF file", "*.pdf")],
                title="Lưu phiếu mượn PDF",
                initialfile=f"phieu_muon_{phieu_muon_id}.pdf"
            )

            if not filepath:
                return

            c = canvas.Canvas(filepath, pagesize=A4)
            _, height = A4
            y = height - 25 * mm

            c.setFont("Helvetica-Bold", 16)
            c.drawString(25 * mm, y, "PHIEU MUON SACH")

            y -= 12 * mm
            c.setFont("Helvetica", 11)
            c.drawString(25 * mm, y, f"Ma phieu muon: {loan_info[0]}")
            y -= 7 * mm
            c.drawString(25 * mm, y, f"Ho ten ban doc: {loan_info[1] or ''}")
            y -= 7 * mm
            c.drawString(25 * mm, y, f"Email: {loan_info[2] or ''}")
            y -= 7 * mm
            c.drawString(25 * mm, y, f"So dien thoai: {loan_info[3] or ''}")
            y -= 7 * mm
            c.drawString(25 * mm, y, f"Ngay muon: {loan_info[4]}")
            y -= 7 * mm
            c.drawString(25 * mm, y, f"Ngay hen tra: {loan_info[5]}")
            y -= 7 * mm
            c.drawString(25 * mm, y, f"Trang thai: {loan_info[6]}")
            y -= 7 * mm
            c.drawString(25 * mm, y, f"So lan gia han: {loan_info[7]}")
            y -= 7 * mm
            c.drawString(25 * mm, y, f"Tao boi: {loan_info[9] or ''}")
            y -= 7 * mm
            c.drawString(25 * mm, y, f"Ghi chu: {loan_info[8] or ''}")

            y -= 12 * mm
            c.setFont("Helvetica-Bold", 12)
            c.drawString(25 * mm, y, "Danh sach sach muon:")

            y -= 8 * mm
            c.setFont("Helvetica", 10)

            for idx, row in enumerate(detail_rows, start=1):
                ma_ban_sao, tieu_de, tac_gia, tg_muon, tg_tra = row
                line = f"{idx}. [{ma_ban_sao}] {tieu_de} - {tac_gia}"
                c.drawString(28 * mm, y, line[:110])

                y -= 6 * mm
                c.drawString(35 * mm, y, f"Thoi gian muon: {tg_muon} | Thoi gian tra: {tg_tra if tg_tra else 'Chua tra'}")
                y -= 8 * mm

                if y < 30 * mm:
                    c.showPage()
                    y = height - 25 * mm
                    c.setFont("Helvetica", 10)

            y -= 10 * mm
            c.setFont("Helvetica", 11)
            c.drawString(25 * mm, y, "Nguoi lap phieu")
            c.drawString(130 * mm, y, "Ban doc")
            y -= 20 * mm
            c.drawString(25 * mm, y, "(Ky, ghi ro ho ten)")
            c.drawString(130 * mm, y, "(Ky, ghi ro ho ten)")

            c.save()
            messagebox.showinfo("Thành công", f"Đã xuất PDF phiếu mượn:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Xuất PDF phiếu mượn thất bại.\n{e}")

    def export_fine_pdf(self):
        selected = self.fine_tree.focus()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một phiếu phạt để xuất PDF.")
            return

        values = self.fine_tree.item(selected, "values")
        phieu_muon_id = values[1]

        try:
            fine_rows = self.execute("""
                SELECT tp.tien_phat_id,
                       tp.phieu_muon_id,
                       tp.ban_sao_id,
                       bss.ma_ban_sao,
                       s.tieu_de,
                       tp.so_ngay_tre,
                       tp.so_tien,
                       tp.tao_luc,
                       tp.da_thanh_toan,
                       tp.thanh_toan_luc,
                       bd.ho_ten
                FROM tien_phat tp
                JOIN ban_sao_sach bss ON bss.ban_sao_id = tp.ban_sao_id
                JOIN sach s ON s.sach_id = bss.sach_id
                JOIN phieu_muon pm ON pm.phieu_muon_id = tp.phieu_muon_id
                JOIN ban_doc bd ON bd.ban_doc_id = pm.ban_doc_id
                WHERE tp.phieu_muon_id = %s
                ORDER BY tp.tien_phat_id;
            """, (phieu_muon_id,), fetch=True)

            if not fine_rows:
                messagebox.showerror("Lỗi", "Không tìm thấy dữ liệu tiền phạt.")
                return

            filepath = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF file", "*.pdf")],
                title="Lưu phiếu phạt PDF",
                initialfile=f"phieu_phat_{phieu_muon_id}.pdf"
            )

            if not filepath:
                return

            c = canvas.Canvas(filepath, pagesize=A4)
            _, height = A4
            y = height - 25 * mm

            c.setFont("Helvetica-Bold", 16)
            c.drawString(25 * mm, y, "PHIEU PHAT QUA HAN")

            y -= 12 * mm
            c.setFont("Helvetica", 11)
            c.drawString(25 * mm, y, f"Ma phieu muon: {phieu_muon_id}")
            y -= 7 * mm
            c.drawString(25 * mm, y, f"Ho ten ban doc: {fine_rows[0][10] or ''}")

            y -= 12 * mm
            c.setFont("Helvetica-Bold", 12)
            c.drawString(25 * mm, y, "Danh sach muc phat:")

            y -= 8 * mm
            c.setFont("Helvetica", 10)

            total_money = 0
            paid_text = "Da thanh toan" if fine_rows[0][8] else "Chua thanh toan"

            for idx, row in enumerate(fine_rows, start=1):
                _, _, _, ma_ban_sao, tieu_de, so_ngay_tre, so_tien, tao_luc, _, thanh_toan_luc, _ = row
                total_money += float(so_tien)

                line1 = f"{idx}. [{ma_ban_sao}] {tieu_de}"
                line2 = f"So ngay tre: {so_ngay_tre} | So tien: {so_tien} VND"
                line3 = f"Tao luc: {tao_luc} | Thanh toan: {thanh_toan_luc if thanh_toan_luc else 'Chua thanh toan'}"

                c.drawString(28 * mm, y, line1[:110])
                y -= 6 * mm
                c.drawString(35 * mm, y, line2)
                y -= 6 * mm
                c.drawString(35 * mm, y, line3[:120])
                y -= 8 * mm

                if y < 30 * mm:
                    c.showPage()
                    y = height - 25 * mm
                    c.setFont("Helvetica", 10)

            y -= 8 * mm
            c.setFont("Helvetica-Bold", 12)
            c.drawString(25 * mm, y, f"Tong tien phat: {total_money:,.0f} VND")

            y -= 8 * mm
            c.setFont("Helvetica", 11)
            c.drawString(25 * mm, y, f"Trang thai thanh toan: {paid_text}")

            y -= 15 * mm
            c.drawString(25 * mm, y, "Nguoi lap phieu")
            c.drawString(130 * mm, y, "Nguoi nop phat")
            y -= 20 * mm
            c.drawString(25 * mm, y, "(Ky, ghi ro ho ten)")
            c.drawString(130 * mm, y, "(Ky, ghi ro ho ten)")

            c.save()
            messagebox.showinfo("Thành công", f"Đã xuất PDF phiếu phạt:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Xuất PDF phiếu phạt thất bại.\n{e}")

    # ===================== USERS =====================

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
            messagebox.showerror("Lỗi", f"Không tải được tài khoản.\n{e}")

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
            messagebox.showerror("Lỗi", f"Tìm tài khoản thất bại.\n{e}")

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
            messagebox.showerror("Lỗi", f"Thêm tài khoản thất bại.\n{e}")

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
            messagebox.showerror("Lỗi", f"Cập nhật tài khoản thất bại.\n{e}")

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
            messagebox.showerror("Lỗi", f"Cập nhật trạng thái thất bại.\n{e}")

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
            messagebox.showerror("Lỗi", f"Không tải được danh mục.\n{e}")

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
            messagebox.showerror("Lỗi", f"Tìm danh mục thất bại.\n{e}")

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
            messagebox.showerror("Lỗi", f"Thêm danh mục thất bại.\n{e}")

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
            messagebox.showerror("Lỗi", f"Cập nhật danh mục thất bại.\n{e}")

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
            messagebox.showerror("Lỗi", f"Xóa danh mục thất bại.\n{e}")

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
            rows = self.execute("""
                SELECT s.sach_id, s.tieu_de, s.tac_gia, s.nha_xuat_ban, s.isbn, d.ten, s.tao_luc
                FROM sach s
                LEFT JOIN danh_muc d ON s.danh_muc_id = d.danh_muc_id
                ORDER BY s.sach_id;
            """, fetch=True)
            for row in rows:
                self.book_tree.insert("", "end", values=row)

            if hasattr(self, "copy_book_combo"):
                self.copy_book_combo["values"] = [f"{r[0]} - {r[1]}" for r in rows]
            self.clear_book_form()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được sách.\n{e}")

    def search_books(self):
        kw = self.book_search_entry.get().strip()
        try:
            self.clear_tree(self.book_tree)
            rows = self.execute("""
                SELECT s.sach_id, s.tieu_de, s.tac_gia, s.nha_xuat_ban, s.isbn, d.ten, s.tao_luc
                FROM sach s
                LEFT JOIN danh_muc d ON s.danh_muc_id = d.danh_muc_id
                WHERE s.tieu_de ILIKE %s
                   OR s.tac_gia ILIKE %s
                   OR COALESCE(s.isbn, '') ILIKE %s
                ORDER BY s.sach_id;
            """, (f"%{kw}%", f"%{kw}%", f"%{kw}%"), fetch=True)
            for row in rows:
                self.book_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Tìm sách thất bại.\n{e}")

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
            self.execute("""
                INSERT INTO sach(tieu_de, tac_gia, nha_xuat_ban, isbn, danh_muc_id)
                VALUES (%s, %s, %s, %s, %s);
            """, (title, author, publisher, isbn, category_id))
            messagebox.showinfo("Thành công", "Thêm sách thành công.")
            self.load_books()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Thêm sách thất bại.\n{e}")

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
            self.execute("""
                UPDATE sach
                SET tieu_de = %s,
                    tac_gia = %s,
                    nha_xuat_ban = %s,
                    isbn = %s,
                    danh_muc_id = %s
                WHERE sach_id = %s;
            """, (title, author, publisher, isbn, category_id, self.selected_book_id))
            messagebox.showinfo("Thành công", "Cập nhật sách thành công.")
            self.load_books()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Cập nhật sách thất bại.\n{e}")

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
            messagebox.showerror("Lỗi", f"Xóa sách thất bại.\n{e}")

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
        self.copy_code_entry = tk.Entry(edit, width=24)
        self.copy_code_entry.grid(row=0, column=1, padx=5, pady=5)

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
            rows = self.execute("""
                SELECT bss.ban_sao_id, bss.sach_id, bss.ma_ban_sao, s.tieu_de, bss.trang_thai, bss.ghi_chu
                FROM ban_sao_sach bss
                JOIN sach s ON s.sach_id = bss.sach_id
                ORDER BY bss.ban_sao_id;
            """, fetch=True)
            for row in rows:
                self.copy_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được bản sao.\n{e}")

    def search_copies(self):
        kw = self.copy_search_entry.get().strip()
        try:
            self.clear_tree(self.copy_tree)
            rows = self.execute("""
                SELECT bss.ban_sao_id, bss.sach_id, bss.ma_ban_sao, s.tieu_de, bss.trang_thai, bss.ghi_chu
                FROM ban_sao_sach bss
                JOIN sach s ON s.sach_id = bss.sach_id
                WHERE bss.ma_ban_sao ILIKE %s
                   OR s.tieu_de ILIKE %s
                   OR bss.trang_thai ILIKE %s
                ORDER BY bss.ban_sao_id;
            """, (f"%{kw}%", f"%{kw}%", f"%{kw}%"), fetch=True)
            for row in rows:
                self.copy_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Tìm bản sao thất bại.\n{e}")

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
            messagebox.showerror("Lỗi", f"Thêm bản sao thất bại.\n{e}")

    def update_copy_status(self):
        code = self.copy_code_entry.get().strip()
        status = self.copy_status_combo.get().strip()
        if not code or not status:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập mã bản sao và trạng thái.")
            return
        try:
            self.execute("CALL sp_cap_nhat_trang_thai_ban_sao(%s, %s, %s);", (self.user_id, code, status))
            messagebox.showinfo("Thành công", "Cập nhật trạng thái thành công.")
            self.load_copies()
            self.load_inventory()
            self.load_borrowings_open()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Cập nhật trạng thái thất bại.\n{e}")

    def update_copy_note(self):
        code = self.copy_code_entry.get().strip()
        note = to_none(self.copy_note_entry.get())
        if not code:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập mã bản sao.")
            return
        try:
            self.execute("UPDATE ban_sao_sach SET ghi_chu = %s WHERE ma_ban_sao = %s;", (note, code))
            messagebox.showinfo("Thành công", "Lưu ghi chú thành công.")
            self.load_copies()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lưu ghi chú thất bại.\n{e}")

    def on_copy_select(self, event):
        sel = self.copy_tree.focus()
        if not sel:
            return
        values = self.copy_tree.item(sel, "values")
        self.copy_code_entry.delete(0, tk.END)
        self.copy_code_entry.insert(0, values[2] or "")
        self.copy_status_combo.set(values[4] or "")
        self.copy_note_entry.delete(0, tk.END)
        self.copy_note_entry.insert(0, values[5] or "")

    # ===================== READERS =====================

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
        self.reader_phone_entry = tk.Entry(form, width=28)
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

    def load_readers(self):
        try:
            self.clear_tree(self.reader_tree)
            rows = self.execute("""
                SELECT ban_doc_id, ho_ten, loai_ban_doc, email, sdt, han_the, dang_hoat_dong
                FROM ban_doc
                ORDER BY ban_doc_id;
            """, fetch=True)
            for row in rows:
                self.reader_tree.insert("", "end", values=row)
            self.clear_reader_form()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được bạn đọc.\n{e}")

    def search_readers(self):
        kw = self.reader_search_entry.get().strip()
        try:
            self.clear_tree(self.reader_tree)
            rows = self.execute("""
                SELECT ban_doc_id, ho_ten, loai_ban_doc, email, sdt, han_the, dang_hoat_dong
                FROM ban_doc
                WHERE ho_ten ILIKE %s
                   OR COALESCE(email, '') ILIKE %s
                   OR COALESCE(sdt, '') ILIKE %s
                ORDER BY ban_doc_id;
            """, (f"%{kw}%", f"%{kw}%", f"%{kw}%"), fetch=True)
            for row in rows:
                self.reader_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Tìm bạn đọc thất bại.\n{e}")

    def add_reader(self):
        name = self.reader_name_entry.get().strip()
        rtype = self.reader_type_combo.get().strip() or "HOC_SINH"
        email = to_none(self.reader_email_entry.get())
        phone = to_none(self.reader_phone_entry.get())
        expiry = self.reader_expiry_entry.get().strip()
        active = self.reader_active_var.get()

        if not name:
            messagebox.showwarning("Cảnh báo", "Họ tên không được để trống.")
            return
        if not valid_date(expiry):
            messagebox.showwarning("Cảnh báo", "Hạn thẻ không hợp lệ. Định dạng YYYY-MM-DD.")
            return

        try:
            self.execute("""
                INSERT INTO ban_doc(ho_ten, loai_ban_doc, email, sdt, han_the, dang_hoat_dong)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (name, rtype, email, phone, expiry, active))
            messagebox.showinfo("Thành công", "Thêm bạn đọc thành công.")
            self.load_readers()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Thêm bạn đọc thất bại.\n{e}")

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

        if not name:
            messagebox.showwarning("Cảnh báo", "Họ tên không được để trống.")
            return
        if not valid_date(expiry):
            messagebox.showwarning("Cảnh báo", "Hạn thẻ không hợp lệ. Định dạng YYYY-MM-DD.")
            return

        try:
            self.execute("""
                UPDATE ban_doc
                SET ho_ten = %s,
                    loai_ban_doc = %s,
                    email = %s,
                    sdt = %s,
                    han_the = %s,
                    dang_hoat_dong = %s
                WHERE ban_doc_id = %s;
            """, (name, rtype, email, phone, expiry, active, self.selected_reader_id))
            messagebox.showinfo("Thành công", "Cập nhật bạn đọc thành công.")
            self.load_readers()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Cập nhật bạn đọc thất bại.\n{e}")

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
            messagebox.showerror("Lỗi", f"Xóa bạn đọc thất bại.\n{e}")

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

    # ===================== BORROW OPS =====================

    def build_borrow_ops_tab(self):
        borrow_frame = tk.LabelFrame(self.tab_borrow_ops, text="Mượn sách", padx=10, pady=10)
        borrow_frame.pack(fill="x", padx=10, pady=8)

        tk.Label(borrow_frame, text="Mã bạn đọc").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.borrow_reader_id_entry = tk.Entry(borrow_frame, width=18)
        self.borrow_reader_id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(borrow_frame, text="Ngày hẹn trả").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.borrow_due_entry = tk.Entry(borrow_frame, width=18)
        self.borrow_due_entry.grid(row=0, column=3, padx=5, pady=5)
        self.borrow_due_entry.insert(0, str(date.today()))

        tk.Label(borrow_frame, text="Mã bản sao (cách nhau dấu phẩy)").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.borrow_copies_entry = tk.Entry(borrow_frame, width=72)
        self.borrow_copies_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="w")

        tk.Label(borrow_frame, text="Ghi chú").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.borrow_note_entry = tk.Entry(borrow_frame, width=72)
        self.borrow_note_entry.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="w")

        tk.Button(borrow_frame, text="Mượn sách", width=18, bg="#4CAF50", fg="white", command=self.borrow_books).grid(row=3, column=0, padx=5, pady=8)

        return_frame = tk.LabelFrame(self.tab_borrow_ops, text="Trả sách", padx=10, pady=10)
        return_frame.pack(fill="x", padx=10, pady=8)

        tk.Label(return_frame, text="Mã bản sao").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.return_copy_entry = tk.Entry(return_frame, width=30)
        self.return_copy_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(return_frame, text="Trả sách", width=18, bg="#FF9800", fg="white", command=self.return_book).grid(row=0, column=2, padx=5, pady=5)

        renew_frame = tk.LabelFrame(self.tab_borrow_ops, text="Gia hạn", padx=10, pady=10)
        renew_frame.pack(fill="x", padx=10, pady=8)

        tk.Label(renew_frame, text="Mã phiếu mượn").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.renew_borrow_id_entry = tk.Entry(renew_frame, width=20)
        self.renew_borrow_id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(renew_frame, text="Ngày hẹn trả mới").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.renew_due_entry = tk.Entry(renew_frame, width=20)
        self.renew_due_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Button(renew_frame, text="Gia hạn", width=18, bg="#2196F3", fg="white", command=self.renew_borrow).grid(row=1, column=0, padx=5, pady=5)

        pay_frame = tk.LabelFrame(self.tab_borrow_ops, text="Thanh toán phạt", padx=10, pady=10)
        pay_frame.pack(fill="x", padx=10, pady=8)

        tk.Label(pay_frame, text="Mã phiếu mượn").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.pay_borrow_id_entry = tk.Entry(pay_frame, width=20)
        self.pay_borrow_id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(pay_frame, text="Thanh toán", width=18, bg="#9C27B0", fg="white", command=self.pay_fine).grid(row=0, column=2, padx=5, pady=5)

        open_frame = tk.LabelFrame(self.tab_borrow_ops, text="Đang mượn", padx=10, pady=10)
        open_frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Button(open_frame, text="Làm mới", command=self.load_borrowings_open).pack(anchor="w", pady=5)

        table_frame = tk.Frame(open_frame)
        table_frame.pack(fill="both", expand=True)

        cols = ("phieu", "ban_doc", "ho_ten", "tieu_de", "ma_ban_sao", "ngay_muon", "ngay_hen_tra")
        self.open_borrow_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, t, w in [
            ("phieu", "Phiếu", 70),
            ("ban_doc", "Bạn đọc", 80),
            ("ho_ten", "Họ tên", 180),
            ("tieu_de", "Tiêu đề", 300),
            ("ma_ban_sao", "Mã bản sao", 110),
            ("ngay_muon", "Ngày mượn", 100),
            ("ngay_hen_tra", "Ngày hẹn trả", 100),
        ]:
            self.open_borrow_tree.heading(c, text=t)
            self.open_borrow_tree.column(c, width=w)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.open_borrow_tree.yview)
        self.open_borrow_tree.configure(yscrollcommand=y_scroll.set)
        self.open_borrow_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

    def borrow_books(self):
        reader_id = self.borrow_reader_id_entry.get().strip()
        due_date = self.borrow_due_entry.get().strip()
        note = to_none(self.borrow_note_entry.get())
        copies_text = self.borrow_copies_entry.get().strip()

        if not reader_id.isdigit():
            messagebox.showwarning("Cảnh báo", "Mã bạn đọc phải là số.")
            return
        if not valid_date(due_date):
            messagebox.showwarning("Cảnh báo", "Ngày hẹn trả không hợp lệ.")
            return
        if not copies_text:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập mã bản sao.")
            return

        copy_list = [x.strip() for x in copies_text.split(",") if x.strip()]
        if not copy_list:
            messagebox.showwarning("Cảnh báo", "Danh sách mã bản sao không hợp lệ.")
            return

        try:
            self.execute("CALL sp_muon_sach(%s, %s, %s, %s, %s, NULL);", (self.user_id, int(reader_id), due_date, copy_list, note))
            messagebox.showinfo("Thành công", "Mượn sách thành công.")
            self.borrow_reader_id_entry.delete(0, tk.END)
            self.borrow_copies_entry.delete(0, tk.END)
            self.borrow_note_entry.delete(0, tk.END)
            self.load_loans()
            self.load_loan_details()
            self.load_borrowings_open()
            self.load_copies()
            self.load_fines()
            self.load_inventory()
            self.load_reports()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Mượn sách thất bại.\n{e}")

    def return_book(self):
        code = self.return_copy_entry.get().strip()
        if not code:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập mã bản sao.")
            return
        try:
            self.execute("CALL sp_tra_sach(%s, %s);", (self.user_id, code))
            messagebox.showinfo("Thành công", "Trả sách thành công.")
            self.return_copy_entry.delete(0, tk.END)
            self.load_loans()
            self.load_loan_details()
            self.load_borrowings_open()
            self.load_copies()
            self.load_fines()
            self.load_inventory()
            self.load_reports()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Trả sách thất bại.\n{e}")

    def renew_borrow(self):
        borrow_id = self.renew_borrow_id_entry.get().strip()
        new_due = self.renew_due_entry.get().strip()

        if not borrow_id.isdigit():
            messagebox.showwarning("Cảnh báo", "Mã phiếu phải là số.")
            return
        if not valid_date(new_due):
            messagebox.showwarning("Cảnh báo", "Ngày hẹn trả mới không hợp lệ.")
            return

        try:
            self.execute("CALL sp_gia_han(%s, %s, %s);", (self.user_id, int(borrow_id), new_due))
            messagebox.showinfo("Thành công", "Gia hạn thành công.")
            self.renew_borrow_id_entry.delete(0, tk.END)
            self.renew_due_entry.delete(0, tk.END)
            self.load_loans()
            self.load_borrowings_open()
            self.load_reports()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Gia hạn thất bại.\n{e}")

    def pay_fine(self):
        borrow_id = self.pay_borrow_id_entry.get().strip()
        if not borrow_id.isdigit():
            messagebox.showwarning("Cảnh báo", "Mã phiếu phải là số.")
            return
        try:
            self.execute("CALL sp_thanh_toan_tien_phat(%s, %s, NULL);", (self.user_id, int(borrow_id)))
            messagebox.showinfo("Thành công", "Thanh toán tiền phạt thành công.")
            self.pay_borrow_id_entry.delete(0, tk.END)
            self.load_fines()
            self.load_reports()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Thanh toán thất bại.\n{e}")

    def load_borrowings_open(self):
        try:
            self.clear_tree(self.open_borrow_tree)
            rows = self.execute("""
                SELECT phieu_muon_id, ban_doc_id, ho_ten, tieu_de, ma_ban_sao, ngay_muon, ngay_hen_tra
                FROM v_dang_muon
                ORDER BY phieu_muon_id DESC, thoi_gian_muon DESC;
            """, fetch=True)
            for row in rows:
                self.open_borrow_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được danh sách đang mượn.\n{e}")

    # ===================== LOANS =====================

    def build_loans_tab(self):
        top = tk.Frame(self.tab_loans)
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Lọc trạng thái").pack(side="left")
        self.loan_status_combo = ttk.Combobox(top, width=20, state="readonly", values=["", "DANG_MUON", "DA_DONG"])
        self.loan_status_combo.pack(side="left", padx=5)
        tk.Button(top, text="Lọc", command=self.search_loans).pack(side="left", padx=5)
        tk.Button(top, text="Làm mới", command=self.load_loans).pack(side="left", padx=5)
        tk.Button(top, text="Xuất PDF phiếu mượn", command=self.export_loan_pdf).pack(side="left", padx=5)

        table_frame = tk.Frame(self.tab_loans)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id", "ban_doc_id", "ho_ten", "ngay_muon", "ngay_hen_tra", "trang_thai", "so_lan_gia_han", "ghi_chu", "tao_boi")
        self.loan_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, t, w in [
            ("id", "Phiếu", 70),
            ("ban_doc_id", "Bạn đọc", 80),
            ("ho_ten", "Họ tên", 180),
            ("ngay_muon", "Ngày mượn", 100),
            ("ngay_hen_tra", "Ngày hẹn trả", 100),
            ("trang_thai", "Trạng thái", 100),
            ("so_lan_gia_han", "Gia hạn", 80),
            ("ghi_chu", "Ghi chú", 220),
            ("tao_boi", "Tạo bởi", 80),
        ]:
            self.loan_tree.heading(c, text=t)
            self.loan_tree.column(c, width=w)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.loan_tree.yview)
        self.loan_tree.configure(yscrollcommand=y_scroll.set)
        self.loan_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

    def load_loans(self):
        try:
            self.clear_tree(self.loan_tree)
            rows = self.execute("""
                SELECT pm.phieu_muon_id, pm.ban_doc_id, bd.ho_ten, pm.ngay_muon, pm.ngay_hen_tra,
                       pm.trang_thai, pm.so_lan_gia_han, pm.ghi_chu, pm.tao_boi
                FROM phieu_muon pm
                JOIN ban_doc bd ON bd.ban_doc_id = pm.ban_doc_id
                ORDER BY pm.phieu_muon_id DESC;
            """, fetch=True)
            for row in rows:
                self.loan_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được phiếu mượn.\n{e}")

    def search_loans(self):
        status = self.loan_status_combo.get().strip()
        try:
            self.clear_tree(self.loan_tree)
            if status:
                rows = self.execute("""
                    SELECT pm.phieu_muon_id, pm.ban_doc_id, bd.ho_ten, pm.ngay_muon, pm.ngay_hen_tra,
                           pm.trang_thai, pm.so_lan_gia_han, pm.ghi_chu, pm.tao_boi
                    FROM phieu_muon pm
                    JOIN ban_doc bd ON bd.ban_doc_id = pm.ban_doc_id
                    WHERE pm.trang_thai = %s
                    ORDER BY pm.phieu_muon_id DESC;
                """, (status,), fetch=True)
            else:
                rows = self.execute("""
                    SELECT pm.phieu_muon_id, pm.ban_doc_id, bd.ho_ten, pm.ngay_muon, pm.ngay_hen_tra,
                           pm.trang_thai, pm.so_lan_gia_han, pm.ghi_chu, pm.tao_boi
                    FROM phieu_muon pm
                    JOIN ban_doc bd ON bd.ban_doc_id = pm.ban_doc_id
                    ORDER BY pm.phieu_muon_id DESC;
                """, fetch=True)
            for row in rows:
                self.loan_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lọc phiếu mượn thất bại.\n{e}")

    # ===================== LOAN DETAILS =====================

    def build_loan_details_tab(self):
        top = tk.Frame(self.tab_loan_details)
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Mã phiếu").pack(side="left")
        self.loan_detail_search_entry = tk.Entry(top, width=20)
        self.loan_detail_search_entry.pack(side="left", padx=5)
        tk.Button(top, text="Tìm", command=self.search_loan_details).pack(side="left", padx=5)
        tk.Button(top, text="Làm mới", command=self.load_loan_details).pack(side="left", padx=5)

        table_frame = tk.Frame(self.tab_loan_details)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("ct_id", "phieu", "ban_sao_id", "ma_ban_sao", "tieu_de", "tg_muon", "tg_tra", "tra_boi")
        self.loan_detail_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, t, w in [
            ("ct_id", "CT", 60),
            ("phieu", "Phiếu", 70),
            ("ban_sao_id", "Bản sao ID", 90),
            ("ma_ban_sao", "Mã bản sao", 120),
            ("tieu_de", "Tiêu đề", 280),
            ("tg_muon", "Thời gian mượn", 170),
            ("tg_tra", "Thời gian trả", 170),
            ("tra_boi", "Trả bởi", 80),
        ]:
            self.loan_detail_tree.heading(c, text=t)
            self.loan_detail_tree.column(c, width=w)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.loan_detail_tree.yview)
        self.loan_detail_tree.configure(yscrollcommand=y_scroll.set)
        self.loan_detail_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

    def load_loan_details(self):
        try:
            self.clear_tree(self.loan_detail_tree)
            rows = self.execute("""
                SELECT ctm.chi_tiet_muon_id, ctm.phieu_muon_id, ctm.ban_sao_id, bss.ma_ban_sao, s.tieu_de,
                       ctm.thoi_gian_muon, ctm.thoi_gian_tra, ctm.tra_boi
                FROM chi_tiet_muon ctm
                JOIN ban_sao_sach bss ON bss.ban_sao_id = ctm.ban_sao_id
                JOIN sach s ON s.sach_id = bss.sach_id
                ORDER BY ctm.chi_tiet_muon_id DESC;
            """, fetch=True)
            for row in rows:
                self.loan_detail_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được chi tiết mượn.\n{e}")

    def search_loan_details(self):
        loan_id = self.loan_detail_search_entry.get().strip()
        if loan_id and not loan_id.isdigit():
            messagebox.showwarning("Cảnh báo", "Mã phiếu phải là số.")
            return
        try:
            self.clear_tree(self.loan_detail_tree)
            if loan_id:
                rows = self.execute("""
                    SELECT ctm.chi_tiet_muon_id, ctm.phieu_muon_id, ctm.ban_sao_id, bss.ma_ban_sao, s.tieu_de,
                           ctm.thoi_gian_muon, ctm.thoi_gian_tra, ctm.tra_boi
                    FROM chi_tiet_muon ctm
                    JOIN ban_sao_sach bss ON bss.ban_sao_id = ctm.ban_sao_id
                    JOIN sach s ON s.sach_id = bss.sach_id
                    WHERE ctm.phieu_muon_id = %s
                    ORDER BY ctm.chi_tiet_muon_id DESC;
                """, (int(loan_id),), fetch=True)
            else:
                rows = self.execute("""
                    SELECT ctm.chi_tiet_muon_id, ctm.phieu_muon_id, ctm.ban_sao_id, bss.ma_ban_sao, s.tieu_de,
                           ctm.thoi_gian_muon, ctm.thoi_gian_tra, ctm.tra_boi
                    FROM chi_tiet_muon ctm
                    JOIN ban_sao_sach bss ON bss.ban_sao_id = ctm.ban_sao_id
                    JOIN sach s ON s.sach_id = bss.sach_id
                    ORDER BY ctm.chi_tiet_muon_id DESC;
                """, fetch=True)
            for row in rows:
                self.loan_detail_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Tìm chi tiết mượn thất bại.\n{e}")

    # ===================== FINES =====================

    def build_fines_tab(self):
        top = tk.Frame(self.tab_fines)
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Mã phiếu").pack(side="left")
        self.fine_search_entry = tk.Entry(top, width=20)
        self.fine_search_entry.pack(side="left", padx=5)
        tk.Button(top, text="Tìm", command=self.search_fines).pack(side="left", padx=5)
        tk.Button(top, text="Làm mới", command=self.load_fines).pack(side="left", padx=5)
        tk.Button(top, text="Xuất PDF phiếu phạt", command=self.export_fine_pdf).pack(side="left", padx=5)

        table_frame = tk.Frame(self.tab_fines)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id", "phieu", "ban_sao_id", "so_ngay_tre", "so_tien", "tao_luc", "da_thanh_toan", "thanh_toan_luc")
        self.fine_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, t, w in [
            ("id", "ID", 60),
            ("phieu", "Phiếu", 80),
            ("ban_sao_id", "Bản sao", 80),
            ("so_ngay_tre", "Ngày trễ", 80),
            ("so_tien", "Số tiền", 100),
            ("tao_luc", "Tạo lúc", 170),
            ("da_thanh_toan", "Đã thanh toán", 110),
            ("thanh_toan_luc", "Thanh toán lúc", 170),
        ]:
            self.fine_tree.heading(c, text=t)
            self.fine_tree.column(c, width=w)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.fine_tree.yview)
        self.fine_tree.configure(yscrollcommand=y_scroll.set)
        self.fine_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

    def load_fines(self):
        try:
            self.clear_tree(self.fine_tree)
            rows = self.execute("""
                SELECT tien_phat_id, phieu_muon_id, ban_sao_id, so_ngay_tre, so_tien, tao_luc, da_thanh_toan, thanh_toan_luc
                FROM tien_phat
                ORDER BY tien_phat_id DESC;
            """, fetch=True)
            for row in rows:
                self.fine_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được tiền phạt.\n{e}")

    def search_fines(self):
        value = self.fine_search_entry.get().strip()
        if value and not value.isdigit():
            messagebox.showwarning("Cảnh báo", "Mã phiếu phải là số.")
            return
        try:
            self.clear_tree(self.fine_tree)
            if value:
                rows = self.execute("""
                    SELECT tien_phat_id, phieu_muon_id, ban_sao_id, so_ngay_tre, so_tien, tao_luc, da_thanh_toan, thanh_toan_luc
                    FROM tien_phat
                    WHERE phieu_muon_id = %s
                    ORDER BY tien_phat_id DESC;
                """, (int(value),), fetch=True)
            else:
                rows = self.execute("""
                    SELECT tien_phat_id, phieu_muon_id, ban_sao_id, so_ngay_tre, so_tien, tao_luc, da_thanh_toan, thanh_toan_luc
                    FROM tien_phat
                    ORDER BY tien_phat_id DESC;
                """, fetch=True)
            for row in rows:
                self.fine_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Tìm tiền phạt thất bại.\n{e}")

    # ===================== INVENTORY =====================

    def build_inventory_tab(self):
        top = tk.Frame(self.tab_inventory)
        top.pack(fill="x", padx=10, pady=8)
        tk.Button(top, text="Làm mới", command=self.load_inventory).pack(side="left", padx=5)
        tk.Button(top, text="Xuất CSV", command=self.export_inventory_csv).pack(side="left", padx=5)

        table_frame = tk.Frame(self.tab_inventory)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("sach_id", "tieu_de", "tac_gia", "tong", "san_sang", "dang_muon", "mat_hu")
        self.inventory_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, t, w in [
            ("sach_id", "Sách ID", 70),
            ("tieu_de", "Tiêu đề", 320),
            ("tac_gia", "Tác giả", 180),
            ("tong", "Tổng bản sao", 100),
            ("san_sang", "Sẵn sàng", 100),
            ("dang_muon", "Đang mượn", 100),
            ("mat_hu", "Mất/Hư", 100),
        ]:
            self.inventory_tree.heading(c, text=t)
            self.inventory_tree.column(c, width=w)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=y_scroll.set)
        self.inventory_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

    def load_inventory(self):
        try:
            self.clear_tree(self.inventory_tree)
            rows = self.execute("""
                SELECT sach_id, tieu_de, tac_gia, tong_ban_sao, san_sang, dang_muon, mat_hoac_hu_hong
                FROM v_ton_kho_sach
                ORDER BY sach_id;
            """, fetch=True)
            for row in rows:
                self.inventory_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được tồn kho.\n{e}")

    def export_inventory_csv(self):
        try:
            rows = self.execute("""
                SELECT sach_id, tieu_de, tac_gia, tong_ban_sao, san_sang, dang_muon, mat_hoac_hu_hong
                FROM v_ton_kho_sach
                ORDER BY sach_id;
            """, fetch=True)
            if not rows:
                messagebox.showinfo("Thông báo", "Không có dữ liệu tồn kho để xuất.")
                return

            path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV file", "*.csv")],
                title="Lưu tồn kho"
            )
            if not path:
                return

            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["SachID", "TieuDe", "TacGia", "TongBanSao", "SanSang", "DangMuon", "MatHuHong"])
                writer.writerows(rows)

            messagebox.showinfo("Thành công", f"Đã xuất file:\n{path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Xuất CSV thất bại.\n{e}")

    # ===================== REPORTS =====================

    def build_reports_tab(self):
        top = tk.Frame(self.tab_reports)
        top.pack(fill="x", padx=10, pady=10)
        tk.Button(top, text="Làm mới báo cáo", command=self.load_reports).pack(side="left", padx=5)
        tk.Button(top, text="Xuất quá hạn CSV", command=self.export_overdue_csv).pack(side="left", padx=5)

        summary = tk.Frame(self.tab_reports)
        summary.pack(fill="x", padx=10, pady=5)

        self.total_borrowing_label = tk.Label(summary, text="Đang mượn: 0", font=("Arial", 11, "bold"))
        self.total_borrowing_label.pack(side="left", padx=10)

        self.total_overdue_label = tk.Label(summary, text="Phiếu quá hạn: 0", font=("Arial", 11, "bold"))
        self.total_overdue_label.pack(side="left", padx=10)

        self.total_fine_label = tk.Label(summary, text="Phạt chưa thanh toán: 0", font=("Arial", 11, "bold"))
        self.total_fine_label.pack(side="left", padx=10)

        overdue_box = tk.LabelFrame(self.tab_reports, text="Phiếu mượn quá hạn", padx=10, pady=10)
        overdue_box.pack(fill="both", expand=True, padx=10, pady=8)

        table_frame = tk.Frame(overdue_box)
        table_frame.pack(fill="both", expand=True)

        cols = ("phieu", "ban_doc", "ngay_muon", "ngay_hen_tra", "trang_thai")
        self.overdue_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, t, w in [
            ("phieu", "Phiếu", 90),
            ("ban_doc", "Bạn đọc", 90),
            ("ngay_muon", "Ngày mượn", 120),
            ("ngay_hen_tra", "Ngày hẹn trả", 120),
            ("trang_thai", "Trạng thái", 120),
        ]:
            self.overdue_tree.heading(c, text=t)
            self.overdue_tree.column(c, width=w)

        self.overdue_tree.tag_configure("overdue", background="#ffe0e0")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.overdue_tree.yview)
        self.overdue_tree.configure(yscrollcommand=y_scroll.set)
        self.overdue_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

    def load_reports(self):
        try:
            self.clear_tree(self.overdue_tree)

            borrow_count = self.execute("SELECT COUNT(*) FROM v_dang_muon;", fetchone=True)[0]
            overdue_rows = self.execute("""
                SELECT phieu_muon_id, ban_doc_id, ngay_muon, ngay_hen_tra, trang_thai
                FROM v_phieu_muon_qua_han
                ORDER BY ngay_hen_tra;
            """, fetch=True)
            fine_total = self.execute("""
                SELECT COALESCE(SUM(so_tien), 0)
                FROM tien_phat
                WHERE da_thanh_toan = false;
            """, fetchone=True)[0]

            for row in overdue_rows:
                self.overdue_tree.insert("", "end", values=row, tags=("overdue",))

            self.total_borrowing_label.config(text=f"Đang mượn: {borrow_count}")
            self.total_overdue_label.config(text=f"Phiếu quá hạn: {len(overdue_rows)}")
            self.total_fine_label.config(text=f"Phạt chưa thanh toán: {fine_total}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được báo cáo.\n{e}")

    def export_overdue_csv(self):
        try:
            rows = self.execute("""
                SELECT phieu_muon_id, ban_doc_id, ngay_muon, ngay_hen_tra, trang_thai
                FROM v_phieu_muon_qua_han
                ORDER BY ngay_hen_tra;
            """, fetch=True)

            if not rows:
                messagebox.showinfo("Thông báo", "Hiện không có phiếu quá hạn để xuất.")
                return

            path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV file", "*.csv")],
                title="Lưu báo cáo quá hạn"
            )
            if not path:
                return

            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["PhieuMuonID", "BanDocID", "NgayMuon", "NgayHenTra", "TrangThai"])
                writer.writerows(rows)

            messagebox.showinfo("Thành công", f"Đã xuất file:\n{path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Xuất CSV thất bại.\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()