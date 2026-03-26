Project Python quản lý thư viện đã được tách thành nhiều file để dễ đọc và dễ bảo trì.

Cách chạy:
1. pip install -r requirements.txt
2. python main.py

Các file chính:
- main.py: điểm khởi động
- login_window.py: đăng nhập / đăng ký
- main_window.py: cửa sổ chính
- nguoi_dung_window.py: quản lý tài khoản
- the_loai_window.py: quản lý thể loại
- sach_window.py: quản lý sách và bản sao
- nguoi_muon_window.py: quản lý bạn đọc
- phieu_muon_window.py: mượn / trả / phiếu mượn
- phieu_phat_window.py: tiền phạt
- thong_ke_window.py: tồn kho / báo cáo
- config.py, db.py, utils.py, pdf_utils.py: file dùng chung
