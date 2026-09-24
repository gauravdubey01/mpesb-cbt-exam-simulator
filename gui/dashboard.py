import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QLineEdit, QComboBox, QSpinBox,
    QMessageBox, QGridLayout, QFileDialog, QDialog, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from core.solution_engine import SolutionEngine
from core.pdf_exporter import PDFExporter
from gui.styles import get_theme_colors

class DashboardWidget(QWidget):
    start_exam_mode = pyqtSignal(dict)      # emits shift_info
    start_practice_mode = pyqtSignal(dict)  # emits shift_info
    start_subject_practice = pyqtSignal(str, int) # emits subject_name, question_count
    view_past_attempt = pyqtSignal(int)     # emits attempt_id

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.shifts = []
        self.solution_engine = SolutionEngine(self.db)
        self.pdf_exporter = PDFExporter(self.db, self.solution_engine)
        self.search_results = []
        self.is_dark = False

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(14)

        # 1. Hero Header Banner
        hero = self._create_hero_banner()
        main_layout.addWidget(hero)

        # 2. Stats KPI Row
        stats_frame = self._create_stats_row()
        main_layout.addWidget(stats_frame)

        # 3. Main Navigation Tabs
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        # Tab 1: All 70 Mock Tests
        tab_mocks = self._create_mock_tests_tab()
        self.tabs.addTab(tab_mocks, "📋 Full Mock Tests (70 Shifts)")

        # Tab 2: Subject-Wise Practice
        tab_subjects = self._create_subject_practice_tab()
        self.tabs.addTab(tab_subjects, "🎯 Subject-Wise Practice")

        # Tab 3: Past Test Attempts
        tab_history = self._create_history_tab()
        self.tabs.addTab(tab_history, "📊 Test History & Progress")

        # Tab 4: Bookmarks
        tab_bookmarks = self._create_bookmarks_tab()
        self.tabs.addTab(tab_bookmarks, "★ Saved Bookmarks")

        # Tab 5: Question Bank & Solutions Hub
        tab_solutions = self._create_solutions_tab()
        self.tabs.addTab(tab_solutions, "📚 Solutions & Question Bank")

        main_layout.addWidget(self.tabs, 1)

    def _create_hero_banner(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0d6efd, stop:1 #0a58ca);
                border-radius: 10px;
                padding: 16px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(6)

        lbl_title = QLabel("MPESB Patwari CBT Examination Simulator")
        lbl_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #ffffff;")
        layout.addWidget(lbl_title)

        lbl_sub = QLabel("Official Question Bank: 70 Shifts • 14,000 Questions • English & हिन्दी Bilingual • Full CBT Simulation")
        lbl_sub.setFont(QFont("Segoe UI", 11))
        lbl_sub.setStyleSheet("color: #e7f1ff;")
        layout.addWidget(lbl_sub)

        return frame

    def _create_stats_row(self):
        self.stats_frame = QFrame()
        self.stats_frame.setStyleSheet("background: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px;")
        layout = QHBoxLayout(self.stats_frame)
        layout.setSpacing(16)

        self.kpi_cards = []
        self.kpi_tests = self._make_kpi("TESTS TAKEN", "0", "#0d6efd")
        self.kpi_avg = self._make_kpi("AVG SCORE", "0.0 / 200", "#198754")
        self.kpi_best = self._make_kpi("BEST SCORE", "0.0", "#6f42c1")
        self.kpi_bm = self._make_kpi("BOOKMARKS", "0", "#b07d00")

        layout.addWidget(self.kpi_tests)
        layout.addWidget(self.kpi_avg)
        layout.addWidget(self.kpi_best)
        layout.addWidget(self.kpi_bm)

        return self.stats_frame

    def _make_kpi(self, title, val, color):
        f = QFrame()
        f.setStyleSheet("background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 6px;")
        l = QVBoxLayout(f)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.setSpacing(2)

        lbl_t = QLabel(title)
        lbl_t.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_t.setStyleSheet("color: #6c757d;")
        lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_v = QLabel(val)
        lbl_v.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_v.setStyleSheet(f"color: {color};")
        lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)

        l.addWidget(lbl_t)
        l.addWidget(lbl_v)
        f.val_label = lbl_v
        f.title_label = lbl_t
        self.kpi_cards.append(f)
        return f

    # -------------------------------------------------------------
    # Tab 1: Mock Tests Table
    # -------------------------------------------------------------
    def _create_mock_tests_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Filter bar
        f_bar = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Search by Date (e.g. 01 Apr, 15 Mar) or Slot...")
        self.txt_search.textChanged.connect(self._filter_shifts_table)
        f_bar.addWidget(self.txt_search, 1)

        self.combo_slot = QComboBox()
        self.combo_slot.addItems(["All Slots", "Shift 1", "Shift 2"])
        self.combo_slot.currentIndexChanged.connect(self._filter_shifts_table)
        f_bar.addWidget(self.combo_slot)

        layout.addLayout(f_bar)

        # Table
        self.table_shifts = QTableWidget()
        self.table_shifts.setColumnCount(6)
        self.table_shifts.setHorizontalHeaderLabels([
            "Test #", "Exam Date", "Slot", "Questions", "CBT Exam Mode", "Practice Mode"
        ])
        self.table_shifts.verticalHeader().setDefaultSectionSize(50)
        self.table_shifts.verticalHeader().setVisible(False)
        self.table_shifts.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_shifts.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_shifts.setColumnWidth(0, 80)
        self.table_shifts.setColumnWidth(2, 110)
        self.table_shifts.setColumnWidth(3, 110)
        self.table_shifts.setColumnWidth(4, 180)
        self.table_shifts.setColumnWidth(5, 160)
        self.table_shifts.setAlternatingRowColors(True)
        layout.addWidget(self.table_shifts, 1)

        return w

    # -------------------------------------------------------------
    # Tab 2: Subject-Wise Practice
    # -------------------------------------------------------------
    def _create_subject_practice_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        lbl = QLabel("Select a Subject to Practice Targeted Questions Across All 70 Papers:")
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(lbl)

        # Controls row
        c_row = QHBoxLayout()
        lbl_count = QLabel("Number of Questions to Practice:")
        lbl_count.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        c_row.addWidget(lbl_count)

        self.spin_count = QSpinBox()
        self.spin_count.setRange(5, 200)
        self.spin_count.setValue(50)
        self.spin_count.setSingleStep(10)
        c_row.addWidget(self.spin_count)

        lbl_hint = QLabel("(Choose any count up to 200 from the full 14,000 question bank)")
        lbl_hint.setStyleSheet("color: #6c757d; font-style: italic; font-size: 11px;")
        c_row.addWidget(lbl_hint)

        c_row.addStretch()
        layout.addLayout(c_row)

        # Grid of Subjects
        grid = QGridLayout()
        grid.setSpacing(12)

        subjects = [
            ("🏛️ General Knowledge", "1,400 Questions", "Gen. Knowledge", "#0d6efd"),
            ("🔤 General English", "1,750 Questions", "Gen. English", "#198754"),
            ("📖 General Hindi", "1,750 Questions", "Gen. Hindi", "#b07d00"),
            ("📐 General Mathematics", "1,750 Questions", "Gen. Maths", "#dc3545"),
            ("🧩 General Reasoning", "1,400 Questions", "Gen. Reasoning", "#6f42c1"),
            ("🔬 General Science", "1,750 Questions", "Gen. Science", "#0dcaf0"),
            ("💼 General Management", "1,400 Questions", "Gen. Management", "#6610f2"),
            ("💻 Computer Proficiency", "1,400 Questions", "Gen. Computer", "#d63384"),
        ]

        self.subject_card_frames = []
        for i, (display_name, count_str, key_name, col) in enumerate(subjects):
            card = self._make_subject_card(display_name, count_str, key_name, col)
            r = i // 4
            c = i % 4
            grid.addWidget(card, r, c)

        layout.addLayout(grid)
        layout.addStretch()
        return w

    def _make_subject_card(self, title, count_str, key, color):
        f = QFrame()
        f.setStyleSheet(f"""
            QFrame {{
                background: #ffffff;
                border: 1.5px solid #dee2e6;
                border-radius: 8px;
                padding: 14px;
            }}
            QFrame:hover {{
                border-color: {color};
                background: #f8fbff;
            }}
        """)
        l = QVBoxLayout(f)
        l.setSpacing(6)

        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl.setWordWrap(True)
        l.addWidget(lbl)

        lbl_cnt = QLabel(f"Bank: {count_str}")
        lbl_cnt.setFont(QFont("Segoe UI", 9))
        lbl_cnt.setStyleSheet("color: #6c757d; font-weight: 600;")
        l.addWidget(lbl_cnt)

        btn = QPushButton("Practice Questions ➔")
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color}; color: #ffffff; font-weight: bold;
                border-radius: 6px; padding: 8px; font-size: 11px;
            }}
        """)
        btn.clicked.connect(lambda: self.start_subject_practice.emit(key, self.spin_count.value()))
        l.addWidget(btn)

        f.base_color = color
        f.count_lbl = lbl_cnt
        self.subject_card_frames.append(f)
        return f

    # -------------------------------------------------------------
    # Tab 3: Test History
    # -------------------------------------------------------------
    def _create_history_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self.table_history = QTableWidget()
        self.table_history.setColumnCount(7)
        self.table_history.setHorizontalHeaderLabels([
            "ID", "Test Paper", "Date / Time", "Score", "Accuracy", "Time Spent", "Review Solutions"
        ])
        self.table_history.verticalHeader().setDefaultSectionSize(48)
        self.table_history.verticalHeader().setVisible(False)
        self.table_history.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_history.setColumnWidth(0, 60)
        self.table_history.setColumnWidth(2, 140)
        self.table_history.setColumnWidth(3, 110)
        self.table_history.setColumnWidth(4, 100)
        self.table_history.setColumnWidth(5, 110)
        self.table_history.setColumnWidth(6, 140)
        self.table_history.setAlternatingRowColors(True)
        layout.addWidget(self.table_history, 1)

        return w

    # -------------------------------------------------------------
    # Tab 4: Bookmarks
    # -------------------------------------------------------------
    def _create_bookmarks_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self.table_bookmarks = QTableWidget()
        self.table_bookmarks.setColumnCount(5)
        self.table_bookmarks.setHorizontalHeaderLabels([
            "Shift #", "Q#", "Subject", "Question Preview", "Correct Ans"
        ])
        self.table_bookmarks.verticalHeader().setDefaultSectionSize(44)
        self.table_bookmarks.verticalHeader().setVisible(False)
        self.table_bookmarks.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_bookmarks.setColumnWidth(0, 80)
        self.table_bookmarks.setColumnWidth(1, 60)
        self.table_bookmarks.setColumnWidth(2, 160)
        self.table_bookmarks.setColumnWidth(4, 110)
        self.table_bookmarks.setAlternatingRowColors(True)
        layout.addWidget(self.table_bookmarks, 1)

        return w

    # -------------------------------------------------------------
    # Tab 5: Question Bank & Solutions Hub
    # -------------------------------------------------------------
    def _create_solutions_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Search Bar and Filters
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search across 14,000 questions (e.g. 'Simple Interest', 'अनुच्छेद', 'RAM', 'Profit')...")
        self.search_input.setFixedHeight(36)
        self.search_input.returnPressed.connect(self._on_search_questions)
        filter_bar.addWidget(self.search_input, 2)

        self.search_subject_combo = QComboBox()
        self.search_subject_combo.setFixedHeight(36)
        self.search_subject_combo.addItems([
            "All Subjects",
            "General Knowledge",
            "General English",
            "General Hindi",
            "General Mathematics",
            "General Reasoning",
            "General Science",
            "General Management",
            "Computer Proficiency",
        ])
        self.search_subject_combo.currentIndexChanged.connect(self._on_search_questions)
        filter_bar.addWidget(self.search_subject_combo, 1)

        btn_search = QPushButton("🔍 Search")
        btn_search.setFixedHeight(36)
        btn_search.setStyleSheet("background: #0d6efd; color: #fff; font-weight: bold; border-radius: 6px; padding: 0 16px;")
        btn_search.clicked.connect(self._on_search_questions)
        filter_bar.addWidget(btn_search)

        self.btn_export_pdf = QPushButton("📄 Export PDF with Solutions")
        self.btn_export_pdf.setFixedHeight(36)
        self.btn_export_pdf.setStyleSheet("background: #198754; color: #fff; font-weight: bold; border-radius: 6px; padding: 0 16px;")
        self.btn_export_pdf.clicked.connect(self._on_export_pdf_solutions)
        filter_bar.addWidget(self.btn_export_pdf)

        layout.addLayout(filter_bar)

        # Status text
        self.lbl_search_status = QLabel("Enter keywords to search official questions and view step-by-step solutions.")
        self.lbl_search_status.setStyleSheet("color: #6c757d; font-size: 11px;")
        layout.addWidget(self.lbl_search_status)

        # Results Table
        self.table_search = QTableWidget()
        self.table_search.setColumnCount(7)
        self.table_search.setHorizontalHeaderLabels([
            "Shift", "Q#", "Subject", "Question Preview", "Ans Key", "Notes", "Action"
        ])
        self.table_search.verticalHeader().setDefaultSectionSize(44)
        self.table_search.verticalHeader().setVisible(False)
        self.table_search.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_search.setColumnWidth(0, 70)
        self.table_search.setColumnWidth(1, 55)
        self.table_search.setColumnWidth(2, 150)
        self.table_search.setColumnWidth(4, 75)
        self.table_search.setColumnWidth(5, 75)
        self.table_search.setColumnWidth(6, 140)
        self.table_search.setAlternatingRowColors(True)
        layout.addWidget(self.table_search, 1)

        return w

    def _on_search_questions(self):
        query = self.search_input.text().strip()
        sub = self.search_subject_combo.currentText()
        if sub == "All Subjects":
            sub_filter = None
        elif sub == "General Knowledge":
            sub_filter = "Knowledge"
        elif sub == "General English":
            sub_filter = "English"
        elif sub == "General Hindi":
            sub_filter = "Hindi"
        elif sub == "General Mathematics":
            sub_filter = "Maths"
        elif sub == "General Reasoning":
            sub_filter = "Reasoning"
        elif sub == "General Science":
            sub_filter = "Science"
        elif sub == "General Management":
            sub_filter = "Management"
        elif sub == "Computer Proficiency":
            sub_filter = "Computer"
        else:
            sub_filter = None

        results = self.db.search_questions(query, subject=sub_filter, limit=100)
        self.search_results = results
        self.lbl_search_status.setText(f"Found {len(results)} matching questions in Question Bank.")

        self.table_search.setRowCount(len(results))
        for row, q in enumerate(results):
            self.table_search.setItem(row, 0, QTableWidgetItem(f"Shift {q.get('shift_id', 1)}"))
            self.table_search.setItem(row, 1, QTableWidgetItem(f"Q.{q.get('qno', 1)}"))
            self.table_search.setItem(row, 2, QTableWidgetItem(q.get("subject", "General")))

            prev = q.get("question_en") or q.get("question_hi") or q.get("question_full", "")
            prev = " ".join(prev.split())
            if len(prev) > 85:
                prev = prev[:85] + "..."
            self.table_search.setItem(row, 3, QTableWidgetItem(prev))

            corr_item = QTableWidgetItem(f"Option {q.get('correct_ans', '')}")
            corr_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_search.setItem(row, 4, corr_item)

            has_note = "📝 Note" if q.get("user_notes") else "-"
            note_item = QTableWidgetItem(has_note)
            note_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_search.setItem(row, 5, note_item)

            btn_sol = QPushButton("💡 View Solution")
            btn_sol.setFixedHeight(30)
            btn_sol.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_sol.setStyleSheet("""
                QPushButton {
                    background-color: #0d6efd;
                    color: #ffffff;
                    font-weight: bold;
                    border-radius: 5px;
                    border: none;
                    padding: 4px 10px;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #0b5ed7; }
            """)
            btn_sol.clicked.connect(lambda ch, item=q: self._on_inspect_question_solution(item))
            self.table_search.setCellWidget(row, 6, self._create_cell_button_widget(btn_sol))

    def _on_inspect_question_solution(self, q):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Detailed Solution — Shift {q.get('shift_id')} Q.{q.get('qno')} [{q.get('subject')}]")
        dialog.resize(720, 620)

        c = get_theme_colors(self.is_dark)

        d_layout = QVBoxLayout(dialog)
        d_layout.setContentsMargins(14, 12, 14, 12)
        d_layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        w = QWidget()
        c_layout = QVBoxLayout(w)
        c_layout.setSpacing(10)

        # Title
        lbl_head = QLabel(f"Shift #{q.get('shift_id')} • Question #{q.get('qno')} — {q.get('subject', 'General')}")
        lbl_head.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_head.setStyleSheet("color: #0d6efd;")
        c_layout.addWidget(lbl_head)

        # Question Frame
        q_frame = QFrame()
        q_frame.setStyleSheet(f"background: {c['card_bg']}; border: 1px solid {c['card_border']}; border-radius: 8px; padding: 12px;")
        q_box = QVBoxLayout(q_frame)
        q_box.setSpacing(8)

        en = q.get("question_en", "")
        hi = q.get("question_hi", "")
        full = q.get("question_full", "")
        q_text = f"{en}\n\n{hi}" if en and hi and en != hi else (en or hi or full)

        lbl_q = QLabel(q_text)
        lbl_q.setFont(QFont("Segoe UI", 11))
        lbl_q.setWordWrap(True)
        lbl_q.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        q_box.addWidget(lbl_q)

        # Image if available
        imgs = q.get("images", [])
        if imgs and os.path.exists(imgs[0]):
            lbl_img = QLabel()
            lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pix = QPixmap(imgs[0])
            lbl_img.setPixmap(pix.scaledToWidth(min(520, pix.width()), Qt.TransformationMode.SmoothTransformation))
            q_box.addWidget(lbl_img)

        c_layout.addWidget(q_frame)

        # Options
        corr = q.get("correct_ans", "").strip()
        for k in ("A", "B", "C", "D"):
            opt_en = q.get(f"opt_{k.lower()}_en", "")
            opt_hi = q.get(f"opt_{k.lower()}_hi", "")
            opt_full = q.get(f"opt_{k.lower()}_full", "")
            opt_text = f"{opt_en} / {opt_hi}" if opt_en and opt_hi and opt_en != opt_hi else (opt_en or opt_hi or opt_full)

            opt_f = QFrame()
            is_corr = (k == corr)
            border_c = c['correct_border'] if is_corr else c['card_border']
            bg_c = c['correct_bg'] if is_corr else c['card_bg']
            opt_f.setStyleSheet(f"background: {bg_c}; border: {'2px solid' if is_corr else '1px solid'} {border_c}; border-radius: 6px; padding: 6px;")

            opt_h = QHBoxLayout(opt_f)
            badge = QLabel(f" {k} ")
            badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            badge.setStyleSheet("background: #e9ecef; border-radius: 4px; padding: 2px 6px;" if not is_corr else "background: #198754; color: #fff; border-radius: 4px; padding: 2px 6px;")
            opt_h.addWidget(badge)

            lbl_opt = QLabel(opt_text)
            lbl_opt.setFont(QFont("Segoe UI", 10))
            lbl_opt.setWordWrap(True)
            lbl_opt.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            opt_h.addWidget(lbl_opt, 1)

            if is_corr:
                lbl_tag = QLabel("✔ Correct Ans")
                lbl_tag.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                lbl_tag.setStyleSheet("color: #198754;")
                opt_h.addWidget(lbl_tag)

            c_layout.addWidget(opt_f)

        # Detailed Solution Section
        sol_frame = QFrame()
        sol_frame.setStyleSheet(f"background: {c['card_bg']}; border: 1.5px solid {c['card_border']}; border-radius: 8px; padding: 12px;")
        sol_box = QVBoxLayout(sol_frame)
        sol_box.setSpacing(8)

        lbl_sol_t = QLabel("💡 Detailed Step-by-Step Solution & Concept Explanation:")
        lbl_sol_t.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_sol_t.setStyleSheet("color: #0d6efd;")
        sol_box.addWidget(lbl_sol_t)

        sol = self.solution_engine.get_solution(q)
        sol_en = sol.get("solution_en", "")
        sol_hi = sol.get("solution_hi", "")
        if sol_en and sol_hi and sol_en != sol_hi:
            sol_html = f"{sol_en}<hr style='border: 0.5px solid {c['card_border']}; margin: 8px 0;'>{sol_hi}"
        else:
            sol_html = sol_en or sol_hi

        lbl_sol_body = QLabel(sol_html)
        lbl_sol_body.setFont(QFont("Segoe UI", 10))
        lbl_sol_body.setWordWrap(True)
        lbl_sol_body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        sol_box.addWidget(lbl_sol_body)

        c_layout.addWidget(sol_frame)

        # Personal Study Note Section
        note_frame = QFrame()
        note_frame.setStyleSheet(f"background: {c['sub_badge_bg']}; border: 1px solid {c['card_border']}; border-radius: 8px; padding: 10px;")
        note_box = QVBoxLayout(note_frame)
        note_box.setSpacing(6)

        lbl_n_t = QLabel("📝 Personal Study Note / Mnemonic Trick:")
        lbl_n_t.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        note_box.addWidget(lbl_n_t)

        txt_note = QTextEdit()
        txt_note.setFont(QFont("Segoe UI", 10))
        txt_note.setFixedHeight(65)
        txt_note.setPlaceholderText("Write your revision notes, tricks, or formulas here...")
        txt_note.setPlainText(q.get("user_notes", "") or "")
        note_box.addWidget(txt_note)

        btn_save_n = QPushButton("💾 Save Note")
        btn_save_n.setFixedWidth(120)
        btn_save_n.setStyleSheet("background: #198754; color: #fff; font-weight: bold; border-radius: 4px; padding: 4px;")
        
        def save_note_action():
            new_note = txt_note.toPlainText().strip()
            self.db.save_user_note(q["shift_id"], q["qno"], new_note)
            q["user_notes"] = new_note
            QMessageBox.information(dialog, "Note Saved", "Your personal study note has been saved!")
            self._on_search_questions()

        btn_save_n.clicked.connect(save_note_action)
        note_box.addWidget(btn_save_n)

        c_layout.addWidget(note_frame)
        c_layout.addStretch()

        scroll.setWidget(w)
        d_layout.addWidget(scroll, 1)

        # Bottom close button
        b_box = QHBoxLayout()
        b_box.addStretch()
        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("background: #6c757d; color: #fff; font-weight: bold; border-radius: 6px; padding: 6px 18px;")
        btn_close.clicked.connect(dialog.accept)
        b_box.addWidget(btn_close)
        d_layout.addLayout(b_box)

        dialog.exec()

    def _on_export_pdf_solutions(self):
        # Choose export source
        has_search = bool(self.search_results)
        msg = QMessageBox(self)
        msg.setWindowTitle("Export PDF with Solutions")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText("Choose which test content you want to export as a printable PDF with detailed step-by-step solutions:")
        
        btn_search_export = None
        if has_search:
            btn_search_export = msg.addButton(f"Current Search ({len(self.search_results)} Questions)", QMessageBox.ButtonRole.ActionRole)
        
        btn_shift_export = msg.addButton("Full Mock Test Shift (200 Questions)", QMessageBox.ButtonRole.ActionRole)
        btn_cancel = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

        msg.exec()
        clicked = msg.clickedButton()

        if clicked == btn_cancel or clicked is None:
            return

        export_questions = []
        doc_title = ""

        if clicked == btn_search_export:
            export_questions = self.search_results
            doc_title = f"Question Bank Search ({len(export_questions)} Questions)"
        else:
            # Let user choose shift number (1 to 70)
            from PyQt6.QtWidgets import QInputDialog
            shifts = self.db.get_shifts()
            shift_names = [f"Shift {s['shift_index']} — {s.get('name', '')} ({s.get('date', '')})" for s in shifts]
            chosen_name, ok = QInputDialog.getItem(self, "Select Shift", "Choose a Shift paper to export with complete solutions:", shift_names, 0, False)
            if not ok or not chosen_name:
                return
            shift_idx = int(chosen_name.split()[1])
            doc_title = f"Shift #{shift_idx} Full Mock Test"
            export_questions = self.db.get_shift_questions(shift_idx)

        if not export_questions:
            QMessageBox.warning(self, "No Questions", "No questions found to export.")
            return

        # Choose save path
        default_filename = f"{doc_title.replace(' ', '_').replace('#', '').replace('/', '_')}_Solutions.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Solutions PDF", os.path.join(os.path.expanduser("~"), default_filename), "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            self.pdf_exporter.export_test_with_solutions(doc_title, export_questions, file_path)
            res = QMessageBox.information(
                self, "Export Successful",
                f"Printable Question Paper with Detailed Solutions generated successfully!\n\nSaved at:\n{file_path}\n\nWould you like to open it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if res == QMessageBox.StandardButton.Yes:
                os.startfile(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to generate PDF:\n{str(e)}")


    # -------------------------------------------------------------
    # Data Refresh
    # -------------------------------------------------------------
    def refresh_data(self):
        self.shifts = self.db.get_shifts()
        self._filter_shifts_table()
        self._refresh_stats()
        self._refresh_history()
        self._refresh_bookmarks()

    def _refresh_stats(self):
        stats = self.db.get_summary_stats()
        self.kpi_tests.val_label.setText(str(stats["total_attempts"]))
        self.kpi_avg.val_label.setText(f"{stats['avg_score']:.1f} / 200")
        self.kpi_best.val_label.setText(f"{stats['best_score']:.1f}")
        self.kpi_bm.val_label.setText(str(stats["bookmarks_count"]))

    def set_dark_mode(self, is_dark):
        self.is_dark = is_dark
        if is_dark:
            self.stats_frame.setStyleSheet("background: #1e1e30; border: 1px solid #334155; border-radius: 8px; padding: 10px;")
            for card in getattr(self, "kpi_cards", []):
                card.setStyleSheet("background: #282842; border: 1px solid #334155; border-radius: 6px; padding: 6px;")
                card.title_label.setStyleSheet("color: #94a3b8;")
            for sc in getattr(self, "subject_card_frames", []):
                sc.setStyleSheet(f"""
                    QFrame {{
                        background: #1e1e30;
                        border: 1.5px solid #334155;
                        border-radius: 8px;
                        padding: 14px;
                    }}
                    QFrame:hover {{
                        border-color: {sc.base_color};
                        background: #282842;
                    }}
                """)
                sc.count_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        else:
            self.stats_frame.setStyleSheet("background: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px;")
            for card in getattr(self, "kpi_cards", []):
                card.setStyleSheet("background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 6px;")
                card.title_label.setStyleSheet("color: #6c757d;")
            for sc in getattr(self, "subject_card_frames", []):
                sc.setStyleSheet(f"""
                    QFrame {{
                        background: #ffffff;
                        border: 1.5px solid #dee2e6;
                        border-radius: 8px;
                        padding: 14px;
                    }}
                    QFrame:hover {{
                        border-color: {sc.base_color};
                        background: #f8fbff;
                    }}
                """)
                sc.count_lbl.setStyleSheet("color: #6c757d; font-weight: 600;")

        tbl_qss = f"""
            QTableWidget {{
                background-color: {'#1a1a28' if is_dark else '#ffffff'};
                alternate-background-color: {'#222234' if is_dark else '#f8f9fa'};
                border: 1px solid {'#334155' if is_dark else '#dee2e6'};
                border-radius: 8px;
                gridline-color: {'#2d3748' if is_dark else '#f1f3f5'};
                font-size: 13px;
                color: {'#f1f5f9' if is_dark else '#212529'};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {'#2d3748' if is_dark else '#f1f3f5'};
                color: {'#f1f5f9' if is_dark else '#212529'};
            }}
            QTableWidget::item:alternate {{
                background-color: {'#222234' if is_dark else '#f8f9fa'};
                color: {'#f1f5f9' if is_dark else '#212529'};
            }}
            QTableWidget::item:selected {{
                background-color: {'#2563eb' if is_dark else '#e7f1ff'};
                color: {'#ffffff' if is_dark else '#0d6efd'};
            }}
            QTableWidget QWidget {{
                background: transparent;
            }}
            QHeaderView::section {{
                background-color: {'#12121d' if is_dark else '#f8f9fa'};
                color: {'#94a3b8' if is_dark else '#495057'};
                padding: 10px;
                font-weight: bold;
                border: none;
                border-bottom: 2px solid {'#334155' if is_dark else '#dee2e6'};
                font-size: 13px;
            }}
        """
        for tbl in (getattr(self, "table_shifts", None), getattr(self, "table_history", None), getattr(self, "table_bookmarks", None), getattr(self, "table_search", None)):
            if tbl:
                tbl.setStyleSheet(tbl_qss)

    def _create_cell_button_widget(self, btn):
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn)
        return container

    def _filter_shifts_table(self):
        query = self.txt_search.text().strip().lower()
        slot_filter = self.combo_slot.currentText()

        filtered = []
        for s in self.shifts:
            if slot_filter != "All Slots" and slot_filter != s.get("slot"):
                continue
            if query:
                s_str = f"{s.get('date', '')} {s.get('slot', '')} {s.get('name', '')}".lower()
                if query not in s_str:
                    continue
            filtered.append(s)

        self.table_shifts.setRowCount(len(filtered))
        for row, s in enumerate(filtered):
            idx_item = QTableWidgetItem(f"#{s['shift_index']:02d}")
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_shifts.setItem(row, 0, idx_item)

            self.table_shifts.setItem(row, 1, QTableWidgetItem(s.get("date", "")))
            self.table_shifts.setItem(row, 2, QTableWidgetItem(s.get("slot", "")))
            
            q_cnt_item = QTableWidgetItem("200 Qs")
            q_cnt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_shifts.setItem(row, 3, q_cnt_item)

            # Start CBT Exam Button
            btn_exam = QPushButton("▶ Start CBT Exam")
            btn_exam.setFixedHeight(34)
            btn_exam.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_exam.setStyleSheet("""
                QPushButton {
                    background-color: #198754;
                    color: #ffffff;
                    font-weight: bold;
                    font-size: 12px;
                    border-radius: 6px;
                    border: none;
                    padding: 4px 12px;
                }
                QPushButton:hover { background-color: #157347; }
                QPushButton:pressed { background-color: #0e5b37; }
            """)
            btn_exam.clicked.connect(lambda ch, shift=s: self.start_exam_mode.emit(shift))
            self.table_shifts.setCellWidget(row, 4, self._create_cell_button_widget(btn_exam))

            # Practice Button
            btn_prac = QPushButton("📖 Practice Mode")
            btn_prac.setFixedHeight(34)
            btn_prac.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_prac.setStyleSheet("""
                QPushButton {
                    background-color: #0d6efd;
                    color: #ffffff;
                    font-weight: bold;
                    font-size: 12px;
                    border-radius: 6px;
                    border: none;
                    padding: 4px 12px;
                }
                QPushButton:hover { background-color: #0b5ed7; }
                QPushButton:pressed { background-color: #0a58ca; }
            """)
            btn_prac.clicked.connect(lambda ch, shift=s: self.start_practice_mode.emit(shift))
            self.table_shifts.setCellWidget(row, 5, self._create_cell_button_widget(btn_prac))

    def _refresh_history(self):
        attempts = self.db.get_test_attempts()
        self.table_history.setRowCount(len(attempts))

        for row, a in enumerate(attempts):
            self.table_history.setItem(row, 0, QTableWidgetItem(str(a["id"])))
            self.table_history.setItem(row, 1, QTableWidgetItem(a.get("title", "")))
            
            dt = a.get("completed_at", "").replace("T", " ")[:16]
            self.table_history.setItem(row, 2, QTableWidgetItem(dt))

            sc = f"{a.get('score', 0):.1f} / {a.get('max_score', 200):.0f}"
            self.table_history.setItem(row, 3, QTableWidgetItem(sc))

            corr = a.get("correct_count", 0)
            tot = a.get("correct_count", 0) + a.get("incorrect_count", 0)
            acc = f"{(corr / tot * 100):.1f}%" if tot > 0 else "0.0%"
            self.table_history.setItem(row, 4, QTableWidgetItem(acc))

            time_s = a.get("time_spent_secs", 0)
            hrs = time_s // 3600
            mins = (time_s % 3600) // 60
            self.table_history.setItem(row, 5, QTableWidgetItem(f"{hrs:02d}h {mins:02d}m"))

            btn_rev = QPushButton("🔍 Review Solutions")
            btn_rev.setFixedHeight(32)
            btn_rev.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_rev.setStyleSheet("""
                QPushButton {
                    background-color: #6f42c1;
                    color: #ffffff;
                    font-weight: bold;
                    border-radius: 5px;
                    border: none;
                    padding: 4px 12px;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #59359a; }
            """)
            btn_rev.clicked.connect(lambda ch, att_id=a["id"]: self.view_past_attempt.emit(att_id))
            self.table_history.setCellWidget(row, 6, self._create_cell_button_widget(btn_rev))

    def _refresh_bookmarks(self):
        bms = self.db.get_bookmarks()
        self.table_bookmarks.setRowCount(len(bms))
        for row, b in enumerate(bms):
            self.table_bookmarks.setItem(row, 0, QTableWidgetItem(f"Shift {b.get('shift_id')}"))
            self.table_bookmarks.setItem(row, 1, QTableWidgetItem(f"Q.{b.get('qno')}"))
            self.table_bookmarks.setItem(row, 2, QTableWidgetItem(b.get("subject", "")))
            
            preview = b.get("question_en") or b.get("question_hi") or ""
            preview = preview.replace("\n", " ")[:80]
            self.table_bookmarks.setItem(row, 3, QTableWidgetItem(preview))

            self.table_bookmarks.setItem(row, 4, QTableWidgetItem(f"Option {b.get('correct_ans', '')}"))
