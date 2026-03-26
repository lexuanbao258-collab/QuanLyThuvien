import csv
from textwrap import fill
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from utils import friendly_error_message, format_money


class ThongKeMixin:
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
            rows = self.execute(
                """
                SELECT sach_id, tieu_de, tac_gia, tong_ban_sao, san_sang, dang_muon, mat_hoac_hu_hong
                FROM v_ton_kho_sach
                ORDER BY sach_id;
                """,
                fetch=True,
            )
            for row in rows:
                self.inventory_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được tồn kho.\n{friendly_error_message(e)}")

    def export_inventory_csv(self):
        try:
            rows = self.execute(
                """
                SELECT sach_id, tieu_de, tac_gia, tong_ban_sao, san_sang, dang_muon, mat_hoac_hu_hong
                FROM v_ton_kho_sach
                ORDER BY sach_id;
                """,
                fetch=True,
            )
            if not rows:
                messagebox.showinfo("Thông báo", "Không có dữ liệu tồn kho để xuất.")
                return

            path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV file", "*.csv")],
                title="Lưu tồn kho",
            )
            if not path:
                return

            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["SachID", "TieuDe", "TacGia", "TongBanSao", "SanSang", "DangMuon", "MatHuHong"])
                writer.writerows(rows)

            messagebox.showinfo("Thành công", f"Đã xuất file:\n{path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Xuất CSV thất bại.\n{friendly_error_message(e)}")

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

        self.total_reader_debt_label = tk.Label(summary, text="Bạn đọc còn nợ: 0", font=("Arial", 11, "bold"))
        self.total_reader_debt_label.pack(side="left", padx=10)

        content = tk.PanedWindow(self.tab_reports, sashrelief=tk.RAISED)
        content.pack(fill="both", expand=True, padx=10, pady=8)

        left_panel = tk.Frame(content)
        right_panel = tk.Frame(content)
        content.add(left_panel, stretch="always")
        content.add(right_panel, stretch="always")

        overdue_box = tk.LabelFrame(left_panel, text="Phiếu mượn quá hạn", padx=10, pady=10)
        overdue_box.pack(fill="both", expand=True, padx=5, pady=5)

        overdue_table = tk.Frame(overdue_box)
        overdue_table.pack(fill="both", expand=True)

        cols = ("phieu", "ho_ten", "ngay_muon", "ngay_hen_tra", "so_ngay_qua_han")
        self.overdue_tree = ttk.Treeview(overdue_table, columns=cols, show="headings")
        for c, t, w in [
            ("phieu", "Phiếu", 90),
            ("ho_ten", "Bạn đọc", 180),
            ("ngay_muon", "Ngày mượn", 100),
            ("ngay_hen_tra", "Ngày hẹn trả", 100),
            ("so_ngay_qua_han", "Quá hạn", 90),
        ]:
            self.overdue_tree.heading(c, text=t)
            self.overdue_tree.column(c, width=w)

        self.overdue_tree.tag_configure("overdue", background="#ffe0e0")

        y_scroll = ttk.Scrollbar(overdue_table, orient="vertical", command=self.overdue_tree.yview)
        self.overdue_tree.configure(yscrollcommand=y_scroll.set)
        self.overdue_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

        chart_box = tk.LabelFrame(left_panel, text="Biểu đồ cột", padx=10, pady=10)
        chart_box.pack(fill="both", expand=True, padx=5, pady=5)

        self.top_books_figure = Figure(figsize=(7.5, 4.6), dpi=100)
        self.top_books_canvas = FigureCanvasTkAgg(self.top_books_figure, master=chart_box)
        self.top_books_canvas.get_tk_widget().pack(fill="both", expand=True)

        top_books_box = tk.LabelFrame(right_panel, text="Top sách được mượn nhiều", padx=10, pady=10)
        top_books_box.pack(fill="both", expand=True, padx=5, pady=5)

        top_books_table = tk.Frame(top_books_box)
        top_books_table.pack(fill="both", expand=True)

        top_cols = ("sach_id", "tieu_de", "tac_gia", "so_luot_muon")
        self.top_books_tree = ttk.Treeview(top_books_table, columns=top_cols, show="headings")
        for c, t, w in [
            ("sach_id", "ID", 60),
            ("tieu_de", "Tiêu đề", 220),
            ("tac_gia", "Tác giả", 150),
            ("so_luot_muon", "Lượt mượn", 90),
        ]:
            self.top_books_tree.heading(c, text=t)
            self.top_books_tree.column(c, width=w)

        y_scroll_top = ttk.Scrollbar(top_books_table, orient="vertical", command=self.top_books_tree.yview)
        self.top_books_tree.configure(yscrollcommand=y_scroll_top.set)
        self.top_books_tree.pack(side="left", fill="both", expand=True)
        y_scroll_top.pack(side="right", fill="y")

        debt_box = tk.LabelFrame(right_panel, text="Bạn đọc còn nợ phạt", padx=10, pady=10)
        debt_box.pack(fill="both", expand=True, padx=5, pady=5)

        debt_table = tk.Frame(debt_box)
        debt_table.pack(fill="both", expand=True)

        debt_cols = ("ban_doc_id", "ho_ten", "email", "so_muc_phat", "tong_no")
        self.reader_debt_tree = ttk.Treeview(debt_table, columns=debt_cols, show="headings")
        for c, t, w in [
            ("ban_doc_id", "ID", 60),
            ("ho_ten", "Họ tên", 160),
            ("email", "Email", 180),
            ("so_muc_phat", "Mục phạt", 80),
            ("tong_no", "Tổng nợ", 100),
        ]:
            self.reader_debt_tree.heading(c, text=t)
            self.reader_debt_tree.column(c, width=w)

        y_scroll_debt = ttk.Scrollbar(debt_table, orient="vertical", command=self.reader_debt_tree.yview)
        self.reader_debt_tree.configure(yscrollcommand=y_scroll_debt.set)
        self.reader_debt_tree.pack(side="left", fill="both", expand=True)
        y_scroll_debt.pack(side="right", fill="y")

    def load_reports(self):
        try:
            self.clear_tree(self.overdue_tree)
            self.clear_tree(self.top_books_tree)
            self.clear_tree(self.reader_debt_tree)

            borrow_count = self.execute("SELECT COUNT(*) FROM v_dang_muon;", fetchone=True)[0]

            overdue_rows = self.execute(
                """
                SELECT phieu_muon_id, ho_ten, ngay_muon, ngay_hen_tra, so_ngay_qua_han
                FROM v_phieu_muon_qua_han_chi_tiet
                ORDER BY so_ngay_qua_han DESC, ngay_hen_tra;
                """,
                fetch=True,
            )

            fine_total = self.execute(
                """
                SELECT COALESCE(SUM(so_tien), 0)
                FROM tien_phat
                WHERE da_thanh_toan = false;
                """,
                fetchone=True,
            )[0]

            top_books = self.execute(
                """
                SELECT sach_id, tieu_de, tac_gia, so_luot_muon
                FROM v_top_sach_muon
                WHERE so_luot_muon > 0
                ORDER BY so_luot_muon DESC, tieu_de
                LIMIT 10;
                """,
                fetch=True,
            )

            debt_rows = self.execute(
                """
                SELECT ban_doc_id, ho_ten, email, so_muc_phat_chua_tt, tong_no
                FROM v_ban_doc_no_phat
                ORDER BY tong_no DESC, ho_ten
                LIMIT 10;
                """,
                fetch=True,
            )

            for row in overdue_rows:
                self.overdue_tree.insert("", "end", values=row, tags=("overdue",))

            for row in top_books:
                self.top_books_tree.insert("", "end", values=row)

            for row in debt_rows:
                row_list = list(row)
                row_list[-1] = format_money(row_list[-1])
                self.reader_debt_tree.insert("", "end", values=row_list)

            self.total_borrowing_label.config(text=f"Đang mượn: {borrow_count}")
            self.total_overdue_label.config(text=f"Phiếu quá hạn: {len(overdue_rows)}")
            self.total_fine_label.config(text=f"Phạt chưa thanh toán: {format_money(fine_total)} VND")
            self.total_reader_debt_label.config(text=f"Bạn đọc còn nợ: {len(debt_rows)}")

            self.draw_top_books_chart(top_books)

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được báo cáo.\n{friendly_error_message(e)}")

    def draw_top_books_chart(self, top_books):
        self.top_books_figure.clear()
        ax = self.top_books_figure.add_subplot(111)

        data = [row for row in top_books if int(row[3] or 0) > 0]

        if not data:
            ax.text(
                0.5,
                0.5,
                "Chưa có dữ liệu mượn sách để vẽ biểu đồ",
                ha="center",
                va="center",
                fontsize=11,
            )
            ax.set_axis_off()
            self.top_books_canvas.draw()
            return

        labels = []
        values = []

        for row in data[:6]:
            tieu_de = str(row[1] or "").strip()
            so_luot_muon = int(row[3] or 0)

            wrapped_label = fill(tieu_de, width=14)

            labels.append(wrapped_label)
            values.append(so_luot_muon)

        x_pos = list(range(len(labels)))
        bars = ax.bar(x_pos, values)

        ax.set_title("Top sách mượn nhiều", fontsize=18, fontweight="bold", pad=12)
        ax.set_xlabel("Sách", fontsize=11)
        ax.set_ylabel("Lượt mượn", fontsize=11)

        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=0, ha="center", fontsize=10)

        ax.yaxis.set_major_locator(MaxNLocator(integer=True))

        max_value = max(values)
        ax.set_ylim(0, max_value + max(1, int(max_value * 0.2)))
        ax.grid(axis="y", linestyle="--", alpha=0.35)

        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.05,
                str(value),
                ha="center",
                va="bottom",
                fontsize=10,
            )

        self.top_books_figure.subplots_adjust(
            left=0.10,
            right=0.97,
            top=0.88,
            bottom=0.30,
        )

        self.top_books_canvas.draw()

    def export_overdue_csv(self):
        try:
            rows = self.execute(
                """
                SELECT phieu_muon_id, ban_doc_id, ho_ten, email, sdt, ngay_muon, ngay_hen_tra, so_ngay_qua_han, trang_thai
                FROM v_phieu_muon_qua_han_chi_tiet
                ORDER BY so_ngay_qua_han DESC, ngay_hen_tra;
                """,
                fetch=True,
            )

            if not rows:
                messagebox.showinfo("Thông báo", "Hiện không có phiếu quá hạn để xuất.")
                return

            path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV file", "*.csv")],
                title="Lưu báo cáo quá hạn",
            )
            if not path:
                return

            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "PhieuMuonID",
                    "BanDocID",
                    "HoTen",
                    "Email",
                    "SDT",
                    "NgayMuon",
                    "NgayHenTra",
                    "SoNgayQuaHan",
                    "TrangThai",
                ])
                writer.writerows(rows)

            messagebox.showinfo("Thành công", f"Đã xuất file:\n{path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Xuất CSV thất bại.\n{friendly_error_message(e)}")