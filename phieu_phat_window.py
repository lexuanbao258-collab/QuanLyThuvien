import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from pdf_utils import draw_wrapped_text
from utils import friendly_error_message, format_money


class PhieuPhatMixin:
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
            y = height - 22 * mm

            c.setFont(self.pdf_font_name, 16)
            c.drawString(20 * mm, y, "PHIẾU PHẠT QUÁ HẠN")

            y -= 12 * mm
            c.setFont(self.pdf_font_name, 11)
            c.drawString(20 * mm, y, f"Mã phiếu mượn: {phieu_muon_id}")
            y -= 7 * mm
            c.drawString(20 * mm, y, f"Họ tên bạn đọc: {fine_rows[0][10] or ''}")

            y -= 10 * mm
            c.setFont(self.pdf_font_name, 12)
            c.drawString(20 * mm, y, "Danh sách mức phạt")

            y -= 8 * mm
            c.setFont(self.pdf_font_name, 10)

            total_money = 0
            paid_text = "Đã thanh toán" if fine_rows[0][8] else "Chưa thanh toán"

            for idx, row in enumerate(fine_rows, start=1):
                _, _, _, ma_ban_sao, tieu_de, so_ngay_tre, so_tien, tao_luc, _, thanh_toan_luc, _ = row
                total_money += float(so_tien)

                y = draw_wrapped_text(c, f"{idx}. [{ma_ban_sao}] {tieu_de}", 24 * mm, y, max_width_chars=85, line_height=5 * mm)
                y = draw_wrapped_text(c, f"Số ngày trễ: {so_ngay_tre} | Số tiền: {format_money(so_tien)} VND", 30 * mm, y, max_width_chars=85, line_height=5 * mm)
                y = draw_wrapped_text(c, f"Tạo lúc: {tao_luc} | Thanh toán: {thanh_toan_luc if thanh_toan_luc else 'Chưa thanh toán'}", 30 * mm, y, max_width_chars=85, line_height=5 * mm)
                y -= 2 * mm

                if y < 30 * mm:
                    c.showPage()
                    y = height - 22 * mm
                    c.setFont(self.pdf_font_name, 10)

            y -= 8 * mm
            c.setFont(self.pdf_font_name, 12)
            c.drawString(20 * mm, y, f"Tổng tiền phạt: {format_money(total_money)} VND")

            y -= 8 * mm
            c.setFont(self.pdf_font_name, 11)
            c.drawString(20 * mm, y, f"Trạng thái thanh toán: {paid_text}")

            y -= 15 * mm
            c.drawString(20 * mm, y, "Người lập phiếu")
            c.drawString(130 * mm, y, "Người nộp phạt")
            y -= 18 * mm
            c.drawString(20 * mm, y, "(Ký, ghi rõ họ tên)")
            c.drawString(130 * mm, y, "(Ký, ghi rõ họ tên)")

            c.save()
            messagebox.showinfo("Thành công", f"Đã xuất PDF phiếu phạt:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Xuất PDF phiếu phạt thất bại.\n{friendly_error_message(e)}")

    # ===================== USERS =====================
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
            messagebox.showerror("Lỗi", f"Không tải được tiền phạt.\n{friendly_error_message(e)}")
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
            messagebox.showerror("Lỗi", f"Tìm tiền phạt thất bại.\n{friendly_error_message(e)}")

    # ===================== INVENTORY =====================
