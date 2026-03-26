import re
from datetime import datetime
from decimal import Decimal
from typing import Optional

import psycopg2

try:
    from psycopg2 import errors as pg_errors
except Exception:
    pg_errors = None


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\d{10}$")


def valid_date(text: str) -> bool:
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def to_none(text: Optional[str]):
    text = (text or "").strip()
    return text if text else None


def valid_email(text: Optional[str]) -> bool:
    value = to_none(text)
    return value is None or bool(EMAIL_RE.fullmatch(value))


def valid_phone(text: Optional[str]) -> bool:
    value = to_none(text)
    return value is None or bool(PHONE_RE.fullmatch(value))


def digits_only(value: str) -> bool:
    return value.isdigit() or value == ""


def format_money(value) -> str:
    if value is None:
        return "0"
    if isinstance(value, Decimal):
        value = float(value)
    return f"{value:,.0f}"


def display_copy_option(code, title) -> str:
    return f"{code} | {title}"


def extract_copy_code(display_text: str) -> str:
    return (display_text or "").split(" | ", 1)[0].strip()


def is_pg_instance(exc: Exception, class_name: str) -> bool:
    if pg_errors is None:
        return False
    error_cls = getattr(pg_errors, class_name, None)
    return error_cls is not None and isinstance(exc, error_cls)


def clean_db_message(exc: Exception) -> str:
    if isinstance(exc, psycopg2.Error):
        diag = getattr(exc, "diag", None)
        primary = getattr(diag, "message_primary", None)
        if primary:
            return str(primary).strip()
    return str(exc).strip()


def friendly_error_message(exc: Exception) -> str:
    msg = clean_db_message(exc)
    lowered = msg.lower()

    if is_pg_instance(exc, "UniqueViolation"):
        if "ten_dang_nhap" in lowered:
            return "Tên đăng nhập đã tồn tại."
        if "email" in lowered:
            return "Email đã tồn tại."
        if "isbn" in lowered:
            return "ISBN đã tồn tại."
        if "ma_ban_sao" in lowered:
            return "Mã bản sao đã tồn tại."
        return "Dữ liệu bị trùng, vui lòng kiểm tra lại."

    if is_pg_instance(exc, "ForeignKeyViolation"):
        return "Không thể xóa hoặc cập nhật vì dữ liệu này đang được sử dụng ở nơi khác."

    if is_pg_instance(exc, "CheckViolation"):
        if "email" in lowered:
            return "Email không đúng định dạng."
        if "sdt" in lowered or "so_dien_thoai" in lowered:
            return "Số điện thoại phải gồm đúng 10 chữ số."
        return msg or "Dữ liệu không hợp lệ."

    if is_pg_instance(exc, "NotNullViolation"):
        return "Vui lòng nhập đầy đủ các trường bắt buộc."

    if "duplicate key value violates unique constraint" in lowered:
        return "Dữ liệu bị trùng, vui lòng kiểm tra lại."
    if "violates foreign key constraint" in lowered:
        return "Không thể xóa hoặc cập nhật vì dữ liệu này đang được sử dụng ở nơi khác."
    if "violates not-null constraint" in lowered:
        return "Vui lòng nhập đầy đủ các trường bắt buộc."
    if "email" in lowered and ("invalid" in lowered or "không" in lowered):
        return "Email không đúng định dạng."
    if "sdt" in lowered or "so dien thoai" in lowered or "số điện thoại" in lowered:
        return "Số điện thoại phải gồm đúng 10 chữ số."

    return msg or "Đã xảy ra lỗi không xác định."