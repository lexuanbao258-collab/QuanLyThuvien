import os
import textwrap

from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PDF_FONT_NAME = None

def ensure_pdf_font():
    global PDF_FONT_NAME
    if PDF_FONT_NAME:
        return PDF_FONT_NAME

    candidates = [
        ("DejaVuSans", [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/local/share/fonts/DejaVuSans.ttf",
        ]),
        ("Arial", [
            "C:/Windows/Fonts/arial.ttf",
            "/Library/Fonts/Arial.ttf",
        ]),
    ]

    for font_name, paths in candidates:
        for path in paths:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, path))
                    PDF_FONT_NAME = font_name
                    return PDF_FONT_NAME
                except Exception:
                    pass

    PDF_FONT_NAME = "Helvetica"
    return PDF_FONT_NAME

def draw_wrapped_text(pdf_canvas, text, x, y, max_width_chars=90, line_height=6 * mm):
    if text is None:
        text = ""
    wrapped = textwrap.wrap(str(text), width=max_width_chars) or [""]
    for line in wrapped:
        pdf_canvas.drawString(x, y, line)
        y -= line_height
    return y
