"""
Styles and theme definitions for the CBT Exam Testing Software.
Supports both Light and Dark modern themes.
"""

from PyQt6.QtGui import QPalette, QColor

LIGHT_STYLE = """
QMainWindow, QDialog {
    background-color: #f4f7f6;
    font-family: 'Segoe UI', 'Nirmala UI', 'Mangal', sans-serif;
}

QWidget {
    font-family: 'Segoe UI', 'Nirmala UI', 'Mangal', sans-serif;
    color: #212529;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #e9ecef;
    width: 10px;
    border-radius: 5px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #adb5bd;
    min-height: 25px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #6c757d;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Group Boxes & Frames */
QFrame.card {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: 10px;
    padding: 12px;
}

QGroupBox {
    font-weight: bold;
    font-size: 14px;
    border: 1px solid #ced4da;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 15px;
    background: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 5px 0 5px;
    color: #0d6efd;
}

/* Primary Action Buttons */
QPushButton.btn-primary {
    background-color: #0d6efd;
    color: #ffffff;
    font-weight: 600;
    font-size: 14px;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
}
QPushButton.btn-primary:hover {
    background-color: #0b5ed7;
}

QPushButton.btn-success {
    background-color: #198754;
    color: #ffffff;
    font-weight: 600;
    font-size: 14px;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
}
QPushButton.btn-success:hover {
    background-color: #157347;
}

QPushButton.btn-warning {
    background-color: #ffc107;
    color: #000000;
    font-weight: 600;
    font-size: 14px;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
}

QPushButton.btn-secondary {
    background-color: #6c757d;
    color: #ffffff;
    font-weight: 600;
    font-size: 14px;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
}

QPushButton.btn-danger {
    background-color: #dc3545;
    color: #ffffff;
    font-weight: 600;
    font-size: 14px;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
}

QPushButton.btn-purple {
    background-color: #6f42c1;
    color: #ffffff;
    font-weight: 600;
    font-size: 14px;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
}

QPushButton.btn-outline {
    background-color: #ffffff;
    color: #0d6efd;
    border: 1.5px solid #0d6efd;
    font-weight: 600;
    font-size: 13px;
    border-radius: 6px;
    padding: 8px 16px;
}
QPushButton.btn-outline:hover {
    background-color: #e7f1ff;
}

/* TabWidget */
QTabWidget::pane {
    border: 1px solid #dee2e6;
    background: #ffffff;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background: #e9ecef;
    color: #495057;
    padding: 8px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: bold;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #0d6efd;
    border-bottom: 2px solid #0d6efd;
}

/* Tables */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    gridline-color: #f1f3f5;
    font-size: 13px;
    color: #212529;
}
QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #f1f3f5;
    color: #212529;
}
QTableWidget::item:alternate {
    background-color: #f8f9fa;
    color: #212529;
}
QTableWidget::item:selected {
    background-color: #e7f1ff;
    color: #0d6efd;
}
QTableWidget QWidget {
    background: transparent;
}
QHeaderView::section {
    background-color: #f8f9fa;
    color: #495057;
    padding: 10px;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid #dee2e6;
    font-size: 13px;
}

/* ComboBox and Inputs */
QComboBox, QLineEdit, QSpinBox {
    background-color: #ffffff;
    color: #212529;
    border: 1.5px solid #ced4da;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
}
QComboBox:focus, QLineEdit:focus, QSpinBox:focus {
    border-color: #86b7fe;
}
QComboBox::drop-down {
    border: none;
    width: 25px;
}
"""

DARK_STYLE = """
QMainWindow, QDialog {
    background-color: #161622;
    font-family: 'Segoe UI', 'Nirmala UI', 'Mangal', sans-serif;
}

QWidget {
    font-family: 'Segoe UI', 'Nirmala UI', 'Mangal', sans-serif;
    color: #e2e8f0;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #1e1e30;
    width: 10px;
    border-radius: 5px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #475569;
    min-height: 25px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #64748b;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Group Boxes & Frames */
QFrame.card {
    background-color: #1e1e30;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 12px;
}

QGroupBox {
    font-weight: bold;
    font-size: 14px;
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 15px;
    background: #1e1e30;
    color: #e2e8f0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 5px 0 5px;
    color: #60a5fa;
}

/* Primary Action Buttons */
QPushButton.btn-primary {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 600;
    font-size: 14px;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
}
QPushButton.btn-primary:hover {
    background-color: #1d4ed8;
}

QPushButton.btn-success {
    background-color: #16a34a;
    color: #ffffff;
    font-weight: 600;
    font-size: 14px;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
}
QPushButton.btn-success:hover {
    background-color: #15803d;
}

QPushButton.btn-warning {
    background-color: #d97706;
    color: #ffffff;
    font-weight: 600;
    font-size: 14px;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
}

QPushButton.btn-secondary {
    background-color: #475569;
    color: #ffffff;
    font-weight: 600;
    font-size: 14px;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
}

QPushButton.btn-danger {
    background-color: #dc2626;
    color: #ffffff;
    font-weight: 600;
    font-size: 14px;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
}

QPushButton.btn-purple {
    background-color: #7c3aed;
    color: #ffffff;
    font-weight: 600;
    font-size: 14px;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
}

QPushButton.btn-outline {
    background-color: #1e1e30;
    color: #60a5fa;
    border: 1.5px solid #60a5fa;
    font-weight: 600;
    font-size: 13px;
    border-radius: 6px;
    padding: 8px 16px;
}
QPushButton.btn-outline:hover {
    background-color: #2b354d;
}

/* TabWidget */
QTabWidget::pane {
    border: 1px solid #334155;
    background: #1e1e30;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background: #161622;
    color: #94a3b8;
    padding: 8px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: bold;
    margin-right: 2px;
    border: 1px solid #334155;
}
QTabBar::tab:selected {
    background: #1e1e30;
    color: #60a5fa;
    border-bottom: 2px solid #60a5fa;
}

/* Tables */
QTableWidget {
    background-color: #1a1a28;
    alternate-background-color: #222234;
    border: 1px solid #334155;
    border-radius: 8px;
    gridline-color: #2d3748;
    font-size: 13px;
    color: #f1f5f9;
}
QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #2d3748;
    color: #f1f5f9;
}
QTableWidget::item:alternate {
    background-color: #222234;
    color: #f1f5f9;
}
QTableWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}
QTableWidget QWidget {
    background: transparent;
}
QHeaderView::section {
    background-color: #12121d;
    color: #94a3b8;
    padding: 10px;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid #334155;
    font-size: 13px;
}

/* ComboBox and Inputs */
QComboBox, QLineEdit, QSpinBox {
    background-color: #1e1e30;
    color: #f8fafc;
    border: 1.5px solid #475569;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
}
QComboBox:focus, QLineEdit:focus, QSpinBox:focus {
    border-color: #60a5fa;
}
QComboBox::drop-down {
    border: none;
    width: 25px;
}
QComboBox QAbstractItemView {
    background-color: #1e1e30;
    color: #f8fafc;
    selection-background-color: #2b3955;
}
"""

MAIN_STYLE = LIGHT_STYLE

def get_theme_stylesheet(is_dark=False):
    return DARK_STYLE if is_dark else LIGHT_STYLE

def get_dark_palette():
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor("#161622"))
    p.setColor(QPalette.ColorRole.WindowText, QColor("#f1f5f9"))
    p.setColor(QPalette.ColorRole.Base, QColor("#1a1a28"))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor("#222234"))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1a1a28"))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor("#f1f5f9"))
    p.setColor(QPalette.ColorRole.Text, QColor("#f1f5f9"))
    p.setColor(QPalette.ColorRole.Button, QColor("#1e1e30"))
    p.setColor(QPalette.ColorRole.ButtonText, QColor("#f1f5f9"))
    p.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.Highlight, QColor("#2563eb"))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    return p

def get_theme_colors(is_dark=False):
    if is_dark:
        return {
            "bg": "#161622",
            "card_bg": "#1e1e30",
            "card_border": "#334155",
            "card_hover": "#282842",
            "card_selected_bg": "#1e3a5f",
            "card_selected_border": "#3b82f6",
            "text": "#f8fafc",
            "text_muted": "#94a3b8",
            "topbar_bg": "#1e1e30",
            "topbar_border": "#334155",
            "sub_badge_bg": "#1e293b",
            "sub_badge_text": "#60a5fa",
            "sub_badge_border": "#3b82f6",
            "opt_badge_bg": "#242d42",
            "opt_badge_text": "#93c5fd",
            "opt_badge_border": "#3b82f6",
            "correct_bg": "#123d24",
            "correct_border": "#16a34a",
            "wrong_bg": "#451820",
            "wrong_border": "#dc2626",
            "pill_bg": "#252538",
            "pill_border": "#334155",
            "pill_text": "#cbd5e1",
            "pill_active_bg": "#2563eb",
            "pill_active_text": "#ffffff",
            "palette_unvisited_bg": "#252538",
            "palette_unvisited_text": "#cbd5e1",
            "palette_unvisited_border": "#334155",
            "btn_back_bg": "#252538",
            "btn_back_text": "#f8fafc",
            "btn_back_border": "#475569",
            "bm_bg": "#2b2510",
            "bm_border": "#d97706",
            "bm_text": "#fbbf24",
            "table_row_bg": "#1a1a28",
            "table_alt_row_bg": "#222234",
            "table_text": "#f1f5f9",
        }
    else:
        return {
            "bg": "#f4f7f6",
            "card_bg": "#ffffff",
            "card_border": "#ced4da",
            "card_hover": "#f8fbff",
            "card_selected_bg": "#e8f0fe",
            "card_selected_border": "#1a73e8",
            "text": "#212529",
            "text_muted": "#6c757d",
            "topbar_bg": "#ffffff",
            "topbar_border": "#dee2e6",
            "sub_badge_bg": "#e7f1ff",
            "sub_badge_text": "#0d6efd",
            "sub_badge_border": "#badbcc",
            "opt_badge_bg": "#f1f3f5",
            "opt_badge_text": "#495057",
            "opt_badge_border": "#ced4da",
            "correct_bg": "#d1e7dd",
            "correct_border": "#198754",
            "wrong_bg": "#f8d7da",
            "wrong_border": "#dc3545",
            "pill_bg": "#e9ecef",
            "pill_border": "#ced4da",
            "pill_text": "#495057",
            "pill_active_bg": "#0d6efd",
            "pill_active_text": "#ffffff",
            "palette_unvisited_bg": "#f1f3f5",
            "palette_unvisited_text": "#495057",
            "palette_unvisited_border": "#ced4da",
            "btn_back_bg": "#f8f9fa",
            "btn_back_text": "#212529",
            "btn_back_border": "#ced4da",
            "bm_bg": "#ffffff",
            "bm_border": "#ffc107",
            "bm_text": "#b07d00",
            "table_row_bg": "#ffffff",
            "table_alt_row_bg": "#f8f9fa",
            "table_text": "#212529",
        }
