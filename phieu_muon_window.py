from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from pdf_utils import draw_wrapped_text
from utils import (
    friendly_error_message,
    valid_date,
    format_money,
    to_none,
    display_copy_option,
    extract_copy_code,
)


class PhieuMuonMixin:
    def export_loan_pdf(self):
        selected = self.loan_tree.focus()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một phiếu mượn để xuất PDF.")
            return

        values = self.loan_tree.item(selected, "values")
        phieu_muon_id = values[0]

        try:
            loan_info = self.execute(
                """
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
                """,
                (phieu_muon_id,),
                fetchone=True,
            )

            detail_rows = self.execute(
                """
                SELECT bss.ma_ban_sao, s.tieu_de, s.tac_gia, ctm.thoi_gian_muon, ctm.thoi_gian_tra
                FROM chi_tiet_muon ctm
                JOIN ban_sao_sach bss ON bss.ban_sao_id = ctm.ban_sao_id
                JOIN sach s ON s.sach_id = bss.sach_id
                WHERE ctm.phieu_muon_id = %s
                ORDER BY ctm.chi_tiet_muon_id;
                """,
                (phieu_muon_id,),
                fetch=True,
            )

            if not loan_info:
                messagebox.showerror("Lỗi", "Không tìm thấy dữ liệu phiếu mượn.")
                return

            filepath = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF file", "*.pdf")],
                title="Lưu phiếu mượn PDF",
                initialfile=f"phieu_muon_{phieu_muon_id}.pdf",
            )

            if not filepath:
                return

            c = canvas.Canvas(filepath, pagesize=A4)
            _, height = A4
            y = height - 22 * mm

            c.setFont(self.pdf_font_name, 16)
            c.drawString(20 * mm, y, "PHIẾU MƯỢN SÁCH")

            y -= 12 * mm
            c.setFont(self.pdf_font_name, 11)
            info_lines = [
                f"Mã phiếu mượn: {loan_info[0]}",
                f"Họ tên bạn đọc: {loan_info[1] or ''}",
                f"Email: {loan_info[2] or ''}",
                f"Số điện thoại: {loan_info[3] or ''}",
                f"Ngày mượn: {loan_info[4]}",
                f"Ngày hẹn trả: {loan_info[5]}",
                f"Trạng thái: {loan_info[6]}",
                f"Số lần gia hạn: {loan_info[7]}",
                f"Tạo bởi: {loan_info[9] or ''}",
                f"Ghi chú: {loan_info[8] or ''}",
            ]

            for line in info_lines:
                y = draw_wrapped_text(c, line, 20 * mm, y, max_width_chars=90, line_height=6 * mm)

            y -= 4 * mm
            c.setFont(self.pdf_font_name, 12)
            c.drawString(20 * mm, y, "Danh sách sách mượn")

            y -= 8 * mm
            c.setFont(self.pdf_font_name, 10)

            for idx, row in enumerate(detail_rows, start=1):
                ma_ban_sao, tieu_de, tac_gia, tg_muon, tg_tra = row
                y = draw_wrapped_text(
                    c,
                    f"{idx}. [{ma_ban_sao}] {tieu_de} - {tac_gia}",
                    24 * mm,
                    y,
                    max_width_chars=85,
                    line_height=5 * mm,
                )
                y = draw_wrapped_text(
                    c,
                    f"Thời gian mượn: {tg_muon} | Thời gian trả: {tg_tra if tg_tra else 'Chưa trả'}",
                    30 * mm,
                    y,
                    max_width_chars=85,
                    line_height=5 * mm,
                )
                y -= 2 * mm

                if y < 30 * mm:
                    c.showPage()
                    y = height - 22 * mm
                    c.setFont(self.pdf_font_name, 10)

            y -= 8 * mm
            c.setFont(self.pdf_font_name, 11)
            c.drawString(20 * mm, y, "Người lập phiếu")
            c.drawString(130 * mm, y, "Bạn đọc")
            y -= 18 * mm
            c.drawString(20 * mm, y, "(Ký, ghi rõ họ tên)")
            c.drawString(130 * mm, y, "(Ký, ghi rõ họ tên)")

            c.save()
            messagebox.showinfo("Thành công", f"Đã xuất PDF phiếu mượn:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Xuất PDF phiếu mượn thất bại.\n{friendly_error_message(e)}")

    def build_borrow_ops_tab(self):
        main_container = tk.Frame(self.tab_borrow_ops)
        main_container.pack(fill="both", expand=True, padx=10, pady=8)
        main_container.columnconfigure(0, weight=1)

        borrow_frame = tk.LabelFrame(main_container, text="Mượn sách", padx=12, pady=12)
        borrow_frame.grid(row=0, column=0, sticky="ew")
        borrow_frame.columnconfigure(0, weight=0)
        borrow_frame.columnconfigure(1, weight=1)
        borrow_frame.columnconfigure(2, weight=0)
        borrow_frame.columnconfigure(3, weight=1)

        left_form = tk.Frame(borrow_frame)
        left_form.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=(0, 14))
        left_form.columnconfigure(1, weight=1)

        tk.Label(left_form, text="Người mượn").grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")
        self.borrow_reader_combo = ttk.Combobox(left_form, width=38, state="readonly")
        self.borrow_reader_combo.grid(row=0, column=1, padx=0, pady=6, sticky="ew")

        tk.Label(left_form, text="Ngày hẹn trả").grid(row=1, column=0, padx=(0, 8), pady=6, sticky="w")
        self.borrow_due_entry = tk.Entry(left_form, width=18)
        self.borrow_due_entry.grid(row=1, column=1, padx=0, pady=6, sticky="w")
        self.borrow_due_entry.insert(0, str(date.today()))

        tk.Label(left_form, text="Ghi chú").grid(row=2, column=0, padx=(0, 8), pady=6, sticky="nw")
        self.borrow_note_entry = tk.Entry(left_form, width=42)
        self.borrow_note_entry.grid(row=2, column=1, padx=0, pady=6, sticky="ew")

        tk.Button(
            left_form,
            text="Mượn sách",
            width=18,
            bg="#4CAF50",
            fg="white",
            command=self.borrow_books,
        ).grid(row=3, column=1, padx=0, pady=(10, 0), sticky="w")

        copies_frame = tk.Frame(borrow_frame)
        copies_frame.grid(row=0, column=2, columnspan=2, sticky="nsew")
        copies_frame.columnconfigure(0, weight=1)

        tk.Label(
            copies_frame,
            text="Chọn bản sao sách (giữ Ctrl để chọn nhiều)",
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        borrow_list_frame = tk.Frame(copies_frame)
        borrow_list_frame.grid(row=1, column=0, sticky="nsew")
        borrow_list_frame.columnconfigure(0, weight=1)
        borrow_list_frame.rowconfigure(0, weight=1)

        self.borrow_copies_listbox = tk.Listbox(
            borrow_list_frame,
            width=52,
            height=7,
            selectmode=tk.MULTIPLE,
            exportselection=False,
        )
        self.borrow_copies_listbox.grid(row=0, column=0, sticky="nsew")
        borrow_scroll = ttk.Scrollbar(borrow_list_frame, orient="vertical", command=self.borrow_copies_listbox.yview)
        borrow_scroll.grid(row=0, column=1, sticky="ns")
        self.borrow_copies_listbox.configure(yscrollcommand=borrow_scroll.set)

        ops_frame = tk.Frame(main_container)
        ops_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        for col in range(3):
            ops_frame.columnconfigure(col, weight=1)

        return_frame = tk.LabelFrame(ops_frame, text="Trả sách", padx=12, pady=12)
        return_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        return_frame.columnconfigure(1, weight=1)

        tk.Label(return_frame, text="Mã bản sao").grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")
        self.return_copy_combo = ttk.Combobox(return_frame, width=28, state="readonly")
        self.return_copy_combo.grid(row=0, column=1, padx=0, pady=6, sticky="ew")
        tk.Button(
            return_frame,
            text="Trả sách",
            width=16,
            bg="#FF9800",
            fg="white",
            command=self.return_book,
        ).grid(row=1, column=1, padx=0, pady=(8, 0), sticky="w")

        renew_frame = tk.LabelFrame(ops_frame, text="Gia hạn", padx=12, pady=12)
        renew_frame.grid(row=0, column=1, sticky="nsew", padx=4)
        renew_frame.columnconfigure(1, weight=1)

        tk.Label(renew_frame, text="Mã phiếu mượn").grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")
        self.renew_borrow_id_entry = tk.Entry(renew_frame, width=18)
        self.renew_borrow_id_entry.grid(row=0, column=1, padx=0, pady=6, sticky="ew")

        tk.Label(renew_frame, text="Ngày hẹn trả mới").grid(row=1, column=0, padx=(0, 8), pady=6, sticky="w")
        self.renew_due_entry = tk.Entry(renew_frame, width=18)
        self.renew_due_entry.grid(row=1, column=1, padx=0, pady=6, sticky="ew")

        tk.Button(
            renew_frame,
            text="Gia hạn",
            width=16,
            bg="#2196F3",
            fg="white",
            command=self.renew_borrow,
        ).grid(row=2, column=1, padx=0, pady=(8, 0), sticky="w")

        pay_frame = tk.LabelFrame(ops_frame, text="Thanh toán phạt", padx=12, pady=12)
        pay_frame.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        pay_frame.columnconfigure(1, weight=1)

        tk.Label(pay_frame, text="Mã phiếu mượn").grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")
        self.pay_borrow_id_entry = tk.Entry(pay_frame, width=18)
        self.pay_borrow_id_entry.grid(row=0, column=1, padx=0, pady=6, sticky="ew")

        tk.Button(
            pay_frame,
            text="Thanh toán",
            width=16,
            bg="#9C27B0",
            fg="white",
            command=self.pay_fine,
        ).grid(row=1, column=1, padx=0, pady=(8, 0), sticky="w")

        open_frame = tk.LabelFrame(main_container, text="Đang mượn", padx=10, pady=10)
        open_frame.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        main_container.rowconfigure(2, weight=1)

        toolbar = tk.Frame(open_frame)
        toolbar.pack(fill="x", pady=(0, 6))
        tk.Button(toolbar, text="Làm mới", width=12, command=self.load_borrowings_open).pack(side="left")

        table_frame = tk.Frame(open_frame)
        table_frame.pack(fill="both", expand=True)

        cols = ("phieu", "ban_doc", "ho_ten", "tieu_de", "ma_ban_sao", "ngay_muon", "ngay_hen_tra")
        self.open_borrow_tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)
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
            self.open_borrow_tree.column(c, width=w, anchor="center" if c in {"phieu", "ban_doc", "ma_ban_sao", "ngay_muon", "ngay_hen_tra"} else "w")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.open_borrow_tree.yview)
        self.open_borrow_tree.configure(yscrollcommand=y_scroll.set)
        self.open_borrow_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

    def _format_reader_option(self, reader_id, name, phone=None, reader_type=None):
        parts = [str(reader_id), name or ""]
        if phone:
            parts.append(str(phone))
        elif reader_type:
            parts.append(str(reader_type))
        return " | ".join(parts)

    def _extract_reader_id(self, display_text):
        value = (display_text or "").split(" | ", 1)[0].strip()
        return int(value) if value.isdigit() else None

    def refresh_borrow_op_options(self):
        if hasattr(self, "borrow_reader_combo"):
            reader_rows = self.execute(
                """
                SELECT ban_doc_id, ho_ten, sdt, loai_ban_doc
                FROM ban_doc
                WHERE dang_hoat_dong = true
                  AND han_the >= current_date
                ORDER BY ho_ten, ban_doc_id;
                """,
                fetch=True,
            )
            self.borrow_reader_combo["values"] = [
                self._format_reader_option(row[0], row[1], row[2], row[3]) for row in reader_rows
            ]

        if hasattr(self, "borrow_copies_listbox"):
            self.borrow_copies_listbox.delete(0, tk.END)
            available_rows = self.execute(
                """
                SELECT bss.ma_ban_sao, s.tieu_de
                FROM ban_sao_sach bss
                JOIN sach s ON s.sach_id = bss.sach_id
                WHERE bss.trang_thai = 'SAN_SANG'
                ORDER BY bss.ma_ban_sao;
                """,
                fetch=True,
            )
            for row in available_rows:
                self.borrow_copies_listbox.insert(tk.END, display_copy_option(row[0], row[1]))

        if hasattr(self, "return_copy_combo"):
            borrowed_rows = self.execute(
                """
                SELECT DISTINCT ma_ban_sao, tieu_de
                FROM v_dang_muon
                ORDER BY ma_ban_sao;
                """,
                fetch=True,
            )
            self.return_copy_combo["values"] = [display_copy_option(row[0], row[1]) for row in borrowed_rows]

    def borrow_books(self):
        reader_display = self.borrow_reader_combo.get().strip()
        reader_id = self._extract_reader_id(reader_display)
        due_date = self.borrow_due_entry.get().strip()
        note = to_none(self.borrow_note_entry.get())
        selected_indices = self.borrow_copies_listbox.curselection()

        if not reader_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn người mượn từ danh sách bạn đọc.")
            return
        if not valid_date(due_date):
            messagebox.showwarning("Cảnh báo", "Ngày hẹn trả không hợp lệ.")
            return
        if not selected_indices:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất 1 bản sao sách.")
            return

        copy_list = []
        for idx in selected_indices:
            item = self.borrow_copies_listbox.get(idx)
            code = extract_copy_code(item)
            if code:
                copy_list.append(code)

        if not copy_list:
            messagebox.showwarning("Cảnh báo", "Danh sách bản sao không hợp lệ.")
            return

        try:
            result = self.execute(
                "CALL sp_muon_sach(%s, %s, %s, %s, %s, NULL);",
                (self.user_id, reader_id, due_date, copy_list, note),
                fetchone=True,
            )
            phieu_id = result[0] if result else ""
            messagebox.showinfo("Thành công", f"Mượn sách thành công. Mã phiếu: {phieu_id}")
            self.borrow_reader_combo.set("")
            self.borrow_copies_listbox.selection_clear(0, tk.END)
            self.borrow_note_entry.delete(0, tk.END)
            self.load_loans()
            self.load_loan_details()
            self.load_borrowings_open()
            self.load_copies()
            self.load_fines()
            self.load_inventory()
            self.load_reports()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Mượn sách thất bại.\n{friendly_error_message(e)}")

    def return_book(self):
        code = extract_copy_code(self.return_copy_combo.get())
        if not code:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn mã bản sao.")
            return
        try:
            self.execute("CALL sp_tra_sach(%s, %s);", (self.user_id, code))
            messagebox.showinfo("Thành công", "Trả sách thành công.")
            self.return_copy_combo.set("")
            self.load_loans()
            self.load_loan_details()
            self.load_borrowings_open()
            self.load_copies()
            self.load_fines()
            self.load_inventory()
            self.load_reports()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Trả sách thất bại.\n{friendly_error_message(e)}")

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
            messagebox.showerror("Lỗi", f"Gia hạn thất bại.\n{friendly_error_message(e)}")

    def pay_fine(self):
        borrow_id = self.pay_borrow_id_entry.get().strip()
        if not borrow_id.isdigit():
            messagebox.showwarning("Cảnh báo", "Mã phiếu phải là số.")
            return

        try:
            result = self.execute(
                "CALL sp_thanh_toan_tien_phat(%s, %s, NULL);",
                (self.user_id, int(borrow_id)),
                fetchone=True,
            )
            total = result[0] if result else 0
            messagebox.showinfo(
                "Thành công",
                f"Thanh toán tiền phạt thành công.\nTổng tiền: {format_money(total)} VND",
            )
            self.pay_borrow_id_entry.delete(0, tk.END)
            self.load_fines()
            self.load_reports()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Thanh toán thất bại.\n{friendly_error_message(e)}")

    def load_borrowings_open(self):
        try:
            self.clear_tree(self.open_borrow_tree)
            rows = self.execute(
                """
                SELECT phieu_muon_id, ban_doc_id, ho_ten, tieu_de, ma_ban_sao, ngay_muon, ngay_hen_tra
                FROM v_dang_muon
                ORDER BY phieu_muon_id DESC, thoi_gian_muon DESC;
                """,
                fetch=True,
            )
            for row in rows:
                self.open_borrow_tree.insert("", "end", values=row)
            self.refresh_borrow_op_options()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được danh sách đang mượn.\n{friendly_error_message(e)}")

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
            rows = self.execute(
                """
                SELECT pm.phieu_muon_id, pm.ban_doc_id, bd.ho_ten, pm.ngay_muon, pm.ngay_hen_tra,
                       pm.trang_thai, pm.so_lan_gia_han, pm.ghi_chu, pm.tao_boi
                FROM phieu_muon pm
                JOIN ban_doc bd ON bd.ban_doc_id = pm.ban_doc_id
                ORDER BY pm.phieu_muon_id DESC;
                """,
                fetch=True,
            )
            for row in rows:
                self.loan_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được phiếu mượn.\n{friendly_error_message(e)}")

    def search_loans(self):
        status = self.loan_status_combo.get().strip()
        try:
            self.clear_tree(self.loan_tree)
            if status:
                rows = self.execute(
                    """
                    SELECT pm.phieu_muon_id, pm.ban_doc_id, bd.ho_ten, pm.ngay_muon, pm.ngay_hen_tra,
                           pm.trang_thai, pm.so_lan_gia_han, pm.ghi_chu, pm.tao_boi
                    FROM phieu_muon pm
                    JOIN ban_doc bd ON bd.ban_doc_id = pm.ban_doc_id
                    WHERE pm.trang_thai = %s
                    ORDER BY pm.phieu_muon_id DESC;
                    """,
                    (status,),
                    fetch=True,
                )
            else:
                rows = self.execute(
                    """
                    SELECT pm.phieu_muon_id, pm.ban_doc_id, bd.ho_ten, pm.ngay_muon, pm.ngay_hen_tra,
                           pm.trang_thai, pm.so_lan_gia_han, pm.ghi_chu, pm.tao_boi
                    FROM phieu_muon pm
                    JOIN ban_doc bd ON bd.ban_doc_id = pm.ban_doc_id
                    ORDER BY pm.phieu_muon_id DESC;
                    """,
                    fetch=True,
                )
            for row in rows:
                self.loan_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lọc phiếu mượn thất bại.\n{friendly_error_message(e)}")

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
            rows = self.execute(
                """
                SELECT ctm.chi_tiet_muon_id, ctm.phieu_muon_id, ctm.ban_sao_id, bss.ma_ban_sao, s.tieu_de,
                       ctm.thoi_gian_muon, ctm.thoi_gian_tra, ctm.tra_boi
                FROM chi_tiet_muon ctm
                JOIN ban_sao_sach bss ON bss.ban_sao_id = ctm.ban_sao_id
                JOIN sach s ON s.sach_id = bss.sach_id
                ORDER BY ctm.chi_tiet_muon_id DESC;
                """,
                fetch=True,
            )
            for row in rows:
                self.loan_detail_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được chi tiết mượn.\n{friendly_error_message(e)}")

    def search_loan_details(self):
        loan_id = self.loan_detail_search_entry.get().strip()
        if loan_id and not loan_id.isdigit():
            messagebox.showwarning("Cảnh báo", "Mã phiếu phải là số.")
            return
        try:
            self.clear_tree(self.loan_detail_tree)
            if loan_id:
                rows = self.execute(
                    """
                    SELECT ctm.chi_tiet_muon_id, ctm.phieu_muon_id, ctm.ban_sao_id, bss.ma_ban_sao, s.tieu_de,
                           ctm.thoi_gian_muon, ctm.thoi_gian_tra, ctm.tra_boi
                    FROM chi_tiet_muon ctm
                    JOIN ban_sao_sach bss ON bss.ban_sao_id = ctm.ban_sao_id
                    JOIN sach s ON s.sach_id = bss.sach_id
                    WHERE ctm.phieu_muon_id = %s
                    ORDER BY ctm.chi_tiet_muon_id DESC;
                    """,
                    (int(loan_id),),
                    fetch=True,
                )
            else:
                rows = self.execute(
                    """
                    SELECT ctm.chi_tiet_muon_id, ctm.phieu_muon_id, ctm.ban_sao_id, bss.ma_ban_sao, s.tieu_de,
                           ctm.thoi_gian_muon, ctm.thoi_gian_tra, ctm.tra_boi
                    FROM chi_tiet_muon ctm
                    JOIN ban_sao_sach bss ON bss.ban_sao_id = ctm.ban_sao_id
                    JOIN sach s ON s.sach_id = bss.sach_id
                    ORDER BY ctm.chi_tiet_muon_id DESC;
                    """,
                    fetch=True,
                )
            for row in rows:
                self.loan_detail_tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Tìm chi tiết mượn thất bại.\n{friendly_error_message(e)}")
