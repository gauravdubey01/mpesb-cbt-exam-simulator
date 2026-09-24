import sys
from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressDialog, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont

from gui.styles import get_theme_stylesheet, get_theme_colors, get_dark_palette
from gui.dashboard import DashboardWidget
from gui.cbt_exam_widget import CBTExamWidget
from gui.practice_widget import PracticeWidget
from gui.result_widget import ResultWidget

class MainWindow(QMainWindow):
    def __init__(self, db, extractor):
        super().__init__()
        self.db = db
        self.extractor = extractor
        self.is_dark = (self.db.get_setting("theme", "light") == "dark")

        self.setWindowTitle("MPESB Patwari CBT Examination Simulator (70 Shifts • 14,000 Questions)")
        self.resize(1280, 800)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(12, 6, 12, 6)
        central_layout.setSpacing(6)

        # Global Utility Bar
        top_utility = QHBoxLayout()
        self.lbl_global_brand = QLabel("MPESB Patwari CBT Simulator — 70 Papers • 14,000 Questions (Bilingual)")
        self.lbl_global_brand.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        top_utility.addWidget(self.lbl_global_brand)

        top_utility.addStretch()

        self.btn_theme = QPushButton("☀️ Light Mode" if self.is_dark else "🌙 Dark Mode")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.clicked.connect(self._toggle_theme)
        top_utility.addWidget(self.btn_theme)

        central_layout.addLayout(top_utility)

        # Main Stack
        self.stack = QStackedWidget(self)
        central_layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        # Initialize Views
        self.dashboard = DashboardWidget(self.db, self)
        self.cbt_exam = CBTExamWidget(self.db, self.extractor, self)
        self.practice = PracticeWidget(self.db, self.extractor, self)
        self.result = ResultWidget(self.db, self.extractor, self)

        self.stack.addWidget(self.dashboard)   # index 0
        self.stack.addWidget(self.cbt_exam)    # index 1
        self.stack.addWidget(self.practice)    # index 2
        self.stack.addWidget(self.result)      # index 3

        # Connect Signals
        self.dashboard.start_exam_mode.connect(self._launch_cbt_exam)
        self.dashboard.start_practice_mode.connect(self._launch_practice)
        self.dashboard.start_subject_practice.connect(self._launch_subject_practice)
        self.dashboard.view_past_attempt.connect(self._view_past_attempt)

        self.cbt_exam.test_submitted.connect(self._on_exam_submitted)
        self.cbt_exam.exit_to_dashboard.connect(self._go_to_dashboard)

        self.practice.exit_to_dashboard.connect(self._go_to_dashboard)

        self.result.back_to_dashboard.connect(self._go_to_dashboard)
        self.result.retake_test.connect(self._launch_cbt_exam)

        # Apply initial theme
        self._apply_theme()

        # Initial data load
        self.dashboard.refresh_data()

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        self.db.set_setting("theme", "dark" if self.is_dark else "light")
        self._apply_theme()

    def _apply_theme(self):
        app = QApplication.instance()
        if app:
            if self.is_dark:
                app.setPalette(get_dark_palette())
            else:
                app.setPalette(app.style().standardPalette())

        self.setStyleSheet(get_theme_stylesheet(self.is_dark))
        self.btn_theme.setText("☀️ Light Mode" if self.is_dark else "🌙 Dark Mode")
        btn_bg = "#2b354d" if self.is_dark else "#e9ecef"
        btn_text = "#f8fafc" if self.is_dark else "#212529"
        btn_border = "#475569" if self.is_dark else "#ced4da"
        self.btn_theme.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_text};
                border: 1.5px solid {btn_border};
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {'#3b4866' if self.is_dark else '#dee2e6'};
            }}
        """)
        self.lbl_global_brand.setStyleSheet(f"color: {'#60a5fa' if self.is_dark else '#0d6efd'}; font-weight: bold;")

        self.dashboard.set_dark_mode(self.is_dark)
        self.cbt_exam.set_dark_mode(self.is_dark)
        self.practice.set_dark_mode(self.is_dark)
        self.result.set_dark_mode(self.is_dark)

    def _get_shift_questions(self, shift_info):
        shift_idx = shift_info["shift_index"]
        if self.db.is_shift_cached(shift_idx):
            return self.db.get_shift_questions(shift_idx)

        # Show quick progress dialog while parsing from PDF
        progress = QProgressDialog(f"Loading and extracting questions for {shift_info.get('name', 'Test')}...", None, 0, 0, self)
        progress.setWindowTitle("Extracting Test Paper")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        try:
            questions = self.extractor.parse_shift_questions(shift_info)
            self.db.save_shift_questions(shift_idx, questions)
            progress.close()
            return questions
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Extraction Error", f"Failed to parse test questions: {str(e)}")
            return []

    def _launch_cbt_exam(self, shift_info):
        questions = self._get_shift_questions(shift_info)
        if not questions:
            return
        self.cbt_exam.load_test(shift_info, questions, duration_minutes=180)
        self.stack.setCurrentWidget(self.cbt_exam)

    def _launch_practice(self, shift_info):
        questions = self._get_shift_questions(shift_info)
        if not questions:
            return
        self.practice.load_practice(shift_info, questions)
        self.stack.setCurrentWidget(self.practice)

    def _launch_subject_practice(self, subject_key, count):
        # Fetch from DB
        questions = self.db.get_questions_by_subject(subject_key, limit=count)
        if not questions:
            # If not enough cached questions, extract from shift 1 & 2
            shifts = self.db.get_shifts()
            if shifts:
                self._get_shift_questions(shifts[0])
                if len(shifts) > 1:
                    self._get_shift_questions(shifts[1])
                questions = self.db.get_questions_by_subject(subject_key, limit=count)

        if not questions:
            QMessageBox.warning(self, "No Questions", f"No questions found for {subject_key}. Please load a test first.")
            return

        mock_shift_info = {
            "shift_index": 0,
            "name": f"Subject Practice: {subject_key} ({len(questions)} Qs)"
        }
        self.practice.load_practice(mock_shift_info, questions)
        self.stack.setCurrentWidget(self.practice)

    def _on_exam_submitted(self, attempt_data):
        self.result.load_attempt(attempt_data)
        self.stack.setCurrentWidget(self.result)

    def _view_past_attempt(self, attempt_id):
        attempt = self.db.get_test_attempt_by_id(attempt_id)
        if not attempt:
            QMessageBox.warning(self, "Not Found", "Attempt data not found.")
            return
        # Load questions for this shift
        sh_id = attempt.get("shift_id", 1)
        questions = self.db.get_shift_questions(sh_id)
        attempt["questions"] = questions
        self.result.load_attempt(attempt)
        self.stack.setCurrentWidget(self.result)

    def _go_to_dashboard(self):
        self.dashboard.refresh_data()
        self.stack.setCurrentWidget(self.dashboard)
