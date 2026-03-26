import tkinter as tk
from tkinter import ttk

from db import get_connection
from pdf_utils import ensure_pdf_font
from nguoi_dung_window import NguoiDungMixin
from the_loai_window import TheLoaiMixin
from sach_window import SachMixin
from nguoi_muon_window import NguoiMuonMixin
from phieu_muon_window import PhieuMuonMixin
from phieu_phat_window import PhieuPhatMixin
from thong_ke_window import ThongKeMixin

class MainWindow(
    NguoiDungMixin,
    TheLoaiMixin,
    SachMixin,
    NguoiMuonMixin,
    PhieuMuonMixin,
    PhieuPhatMixin,
    ThongKeMixin,
):
    def __init__(self, root, user_id, username, role):
        self.root = root
        self.user_id = user_id
        self.username = username
        self.role = role
        self.pdf_font_name = ensure_pdf_font()

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

    # ===================== PDF EXPORT =====================

