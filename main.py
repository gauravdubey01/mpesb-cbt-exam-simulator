import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from core.extractor import PDFExtractor
from core.db import ExamDB
from gui.main_window import MainWindow

def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def find_pdf_path():
    base_dir = get_base_dir()
    candidates = [
        os.path.join(base_dir, "G2SG4_Patwari_2022_QB.pdf"),
        os.path.join(os.getcwd(), "G2SG4_Patwari_2022_QB.pdf"),
        os.path.join(os.path.dirname(base_dir), "G2SG4_Patwari_2022_QB.pdf"),
        os.path.join(os.path.dirname(os.path.dirname(base_dir)), "G2SG4_Patwari_2022_QB.pdf"),
        os.path.abspath("G2SG4_Patwari_2022_QB.pdf")
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

def main():
    # Configure High DPI scaling for modern Windows displays
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("MPESB Patwari CBT Simulator")

    base_dir = get_base_dir()
    pdf_path = find_pdf_path()
    
    # Locate DB: prefer root db if already exists
    root_dir = os.path.dirname(pdf_path) if pdf_path else base_dir
    db_path = os.path.join(root_dir, "exam_data.db")
    cache_dir = os.path.join(root_dir, "cache")

    db = ExamDB(db_path=db_path)
    extractor = PDFExtractor(pdf_path=pdf_path, cache_dir=cache_dir)

    # Initial scan of shifts if not already present
    shifts = db.get_shifts()
    if not shifts and os.path.exists(pdf_path):
        shifts = extractor.scan_shifts()
        db.populate_shifts(shifts)

    window = MainWindow(db, extractor)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
