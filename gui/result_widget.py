import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QSplitter, QMessageBox, QDialog, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from gui.styles import get_theme_colors
from core.solution_engine import SolutionEngine

class ResultWidget(QWidget):
    back_to_dashboard = pyqtSignal()
    retake_test = pyqtSignal(dict)  # emits shift_info

    def __init__(self, db, extractor, parent=None):
        super().__init__(parent)
        self.db = db
        self.extractor = extractor
        self.solution_engine = SolutionEngine(self.db)
        self.attempt_data = {}
        self.questions = []
        self.user_answers = {}
        self.filtered_review_indices = []
        self.kpi_cards = []
        self.is_dark = False

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)

        # Header Action Bar
        top_bar = QHBoxLayout()
        btn_dash = QPushButton("⬅ Back to Dashboard")
        btn_dash.setStyleSheet("""
            QPushButton {
                background: #f8f9fa; border: 1.5px solid #ced4da;
                border-radius: 6px; padding: 8px 16px; font-weight: 600;
            }
            QPushButton:hover { background: #e9ecef; }
        """)
        btn_dash.clicked.connect(self.back_to_dashboard.emit)
        top_bar.addWidget(btn_dash)

        self.lbl_title = QLabel("📊 Test Performance Analysis & Scorecard")
        self.lbl_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: #0d6efd;")
        top_bar.addWidget(self.lbl_title)

        top_bar.addStretch()

        self.btn_retake = QPushButton("🔄 Retake This Test")
        self.btn_retake.setStyleSheet("""
            QPushButton {
                background: #198754; color: #fff; font-weight: bold;
                border-radius: 6px; padding: 8px 18px;
            }
            QPushButton:hover { background: #157347; }
        """)
        self.btn_retake.clicked.connect(self._on_retake)
        top_bar.addWidget(self.btn_retake)

        main_layout.addLayout(top_bar)

        # Main Tabs: 1. Scorecard & Section Analysis, 2. Question-by-Question Solution Review
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        # Tab 1: Scorecard
        tab_scorecard = self._create_scorecard_tab()
        self.tabs.addTab(tab_scorecard, "🏆 Scorecard & Section Breakdown")

        # Tab 2: Detailed Review
        tab_review = self._create_review_tab()
        self.tabs.addTab(tab_review, "🔍 Question-by-Question Review")

        main_layout.addWidget(self.tabs, 1)

    def _create_scorecard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(14)

        # Overview KPI Cards
        self.kpi_frame = QFrame()
        self.kpi_frame.setStyleSheet("background: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px;")
        kpi_layout = QHBoxLayout(self.kpi_frame)
        kpi_layout.setSpacing(15)

        self.kpi_cards = []
        self.card_score = self._make_kpi_card("TOTAL SCORE", "0.0 / 200", "#0d6efd")
        self.card_accuracy = self._make_kpi_card("ACCURACY", "0.0%", "#198754")
        self.card_attempted = self._make_kpi_card("ATTEMPTED", "0 / 200", "#6f42c1")
        self.card_correct = self._make_kpi_card("CORRECT", "0", "#198754")
        self.card_incorrect = self._make_kpi_card("INCORRECT", "0", "#dc3545")
        self.card_time = self._make_kpi_card("TIME SPENT", "00:00:00", "#495057")

        kpi_layout.addWidget(self.card_score)
        kpi_layout.addWidget(self.card_accuracy)
        kpi_layout.addWidget(self.card_attempted)
        kpi_layout.addWidget(self.card_correct)
        kpi_layout.addWidget(self.card_incorrect)
        kpi_layout.addWidget(self.card_time)

        layout.addWidget(self.kpi_frame)

        # Section-Wise Table
        lbl_sec = QLabel("Section-wise Breakdown:")
        lbl_sec.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_sec)

        self.table_sections = QTableWidget()
        self.table_sections.setColumnCount(7)
        self.table_sections.setHorizontalHeaderLabels([
            "Subject / Section", "Total Qs", "Attempted", "Correct", "Wrong", "Score", "Accuracy %"
        ])
        self.table_sections.verticalHeader().setDefaultSectionSize(40)
        self.table_sections.verticalHeader().setVisible(False)
        self.table_sections.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 7):
            self.table_sections.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.table_sections.setAlternatingRowColors(True)
        layout.addWidget(self.table_sections, 1)

        return widget

    def _make_kpi_card(self, title, default_val, color):
        f = QFrame()
        f.setStyleSheet("background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 6px;")
        l = QVBoxLayout(f)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.setSpacing(4)

        lbl_t = QLabel(title)
        lbl_t.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_t.setStyleSheet("color: #6c757d;")
        lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_v = QLabel(default_val)
        lbl_v.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_v.setStyleSheet(f"color: {color};")
        lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)

        l.addWidget(lbl_t)
        l.addWidget(lbl_v)
        f.val_label = lbl_v
        f.title_label = lbl_t
        self.kpi_cards.append(f)
        return f

    def _create_review_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Filter bar
        f_bar = QHBoxLayout()
        lbl_f = QLabel("Filter Questions:")
        lbl_f.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        f_bar.addWidget(lbl_f)

        self.btn_f_all = QPushButton("All Questions")
        self.btn_f_all.clicked.connect(lambda: self._filter_review("all"))
        f_bar.addWidget(self.btn_f_all)

        self.btn_f_wrong = QPushButton("❌ Incorrect (Mistakes)")
        self.btn_f_wrong.setStyleSheet("color: #dc3545; font-weight: bold;")
        self.btn_f_wrong.clicked.connect(lambda: self._filter_review("wrong"))
        f_bar.addWidget(self.btn_f_wrong)

        self.btn_f_correct = QPushButton("✅ Correct")
        self.btn_f_correct.setStyleSheet("color: #198754; font-weight: bold;")
        self.btn_f_correct.clicked.connect(lambda: self._filter_review("correct"))
        f_bar.addWidget(self.btn_f_correct)

        self.btn_f_unattempted = QPushButton("⚪ Unattempted")
        self.btn_f_unattempted.clicked.connect(lambda: self._filter_review("unattempted"))
        f_bar.addWidget(self.btn_f_unattempted)

        f_bar.addStretch()
        layout.addLayout(f_bar)

        # Splitter: List of questions on left, Details on right
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Table of Questions
        self.table_review = QTableWidget()
        self.table_review.setColumnCount(5)
        self.table_review.setHorizontalHeaderLabels(["Q#", "Subject", "Your Ans", "Correct", "Status"])
        self.table_review.verticalHeader().setDefaultSectionSize(38)
        self.table_review.verticalHeader().setVisible(False)
        self.table_review.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_review.setColumnWidth(0, 50)
        self.table_review.setColumnWidth(2, 75)
        self.table_review.setColumnWidth(3, 75)
        self.table_review.setColumnWidth(4, 95)
        self.table_review.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_review.itemSelectionChanged.connect(self._on_review_question_selected)
        splitter.addWidget(self.table_review)

        # Right Question Detail Display
        r_detail = self._create_review_detail_panel()
        splitter.addWidget(r_detail)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)

        layout.addWidget(splitter, 1)
        return widget

    def _create_review_detail_panel(self):
        self.detail_frame = QFrame()
        self.detail_frame.setStyleSheet("background: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px;")
        layout = QVBoxLayout(self.detail_frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Meta Header
        self.lbl_rev_q_title = QLabel("Select a question to inspect solution")
        self.lbl_rev_q_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(self.lbl_rev_q_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        w = QWidget()
        self.rev_content_layout = QVBoxLayout(w)
        self.rev_content_layout.setSpacing(10)

        self.lbl_rev_text = QLabel()
        self.lbl_rev_text.setWordWrap(True)
        self.lbl_rev_text.setFont(QFont("Segoe UI", 11))
        self.lbl_rev_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.rev_content_layout.addWidget(self.lbl_rev_text)

        self.lbl_rev_img = QLabel()
        self.lbl_rev_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_rev_img.setVisible(False)
        self.rev_content_layout.addWidget(self.lbl_rev_img)

        self.rev_opt_frames = {}
        self.rev_opt_labels = {}
        for k in ("A", "B", "C", "D"):
            c = QFrame()
            c.setStyleSheet("border: 1px solid #ced4da; border-radius: 6px; padding: 6px; background: #f8f9fa;")
            h = QHBoxLayout(c)
            b = QLabel(f" {k} ")
            b.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            b.setStyleSheet("background: #e9ecef; border-radius: 4px; padding: 2px 6px;")
            h.addWidget(b)

            l = QLabel()
            l.setWordWrap(True)
            l.setFont(QFont("Segoe UI", 10))
            l.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            h.addWidget(l, 1)

            self.rev_opt_frames[k] = c
            self.rev_opt_labels[k] = l
            self.rev_content_layout.addWidget(c)

        self.lbl_rev_summary = QLabel()
        self.lbl_rev_summary.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_rev_summary.setStyleSheet("padding: 8px; border-radius: 6px;")
        self.rev_content_layout.addWidget(self.lbl_rev_summary)

        # Personal Note Banner (if present)
        self.lbl_rev_user_note = QLabel()
        self.lbl_rev_user_note.setFont(QFont("Segoe UI", 10))
        self.lbl_rev_user_note.setWordWrap(True)
        self.lbl_rev_user_note.setStyleSheet("background: #fff3cd; color: #664d03; border: 1px solid #ffecb5; border-radius: 6px; padding: 6px 10px;")
        self.lbl_rev_user_note.setVisible(False)
        self.rev_content_layout.addWidget(self.lbl_rev_user_note)

        # Separator line
        self.sep_rev_sol = QFrame()
        self.sep_rev_sol.setFrameShape(QFrame.Shape.HLine)
        self.sep_rev_sol.setStyleSheet("color: #ced4da; margin: 4px 0;")
        self.rev_content_layout.addWidget(self.sep_rev_sol)

        # Detailed Solution Box Header
        h_sol = QHBoxLayout()
        self.lbl_rev_sol_title = QLabel("💡 Detailed Step-by-Step Solution & Concepts:")
        self.lbl_rev_sol_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_rev_sol_title.setStyleSheet("color: #0d6efd;")
        h_sol.addWidget(self.lbl_rev_sol_title)
        h_sol.addStretch()

        self.btn_rev_edit_note = QPushButton("✏️ Add / Edit My Note")
        self.btn_rev_edit_note.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.btn_rev_edit_note.setStyleSheet("background: #2563eb; color: #fff; border-radius: 4px; padding: 4px 10px;")
        self.btn_rev_edit_note.clicked.connect(self._on_edit_review_note)
        h_sol.addWidget(self.btn_rev_edit_note)
        self.rev_content_layout.addLayout(h_sol)

        # Detailed Solution Text (rich HTML)
        self.lbl_rev_solution = QLabel()
        self.lbl_rev_solution.setFont(QFont("Segoe UI", 10))
        self.lbl_rev_solution.setWordWrap(True)
        self.lbl_rev_solution.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.rev_content_layout.addWidget(self.lbl_rev_solution)

        self.rev_content_layout.addStretch()
        scroll.setWidget(w)
        layout.addWidget(scroll, 1)
        return self.detail_frame

    # -------------------------------------------------------------
    # Load and Populate Attempt Results
    # -------------------------------------------------------------
    def load_attempt(self, attempt_data):
        self.attempt_data = attempt_data
        self.questions = attempt_data.get("questions", [])
        self.user_answers = attempt_data.get("answers", {})

        title = attempt_data.get("title", "Exam Attempt")
        self.lbl_title.setText(f"📊 Result Analysis: {title}")

        score = attempt_data.get("score", 0.0)
        max_score = attempt_data.get("max_score", 200.0)
        total_q = attempt_data.get("total_questions", len(self.questions))
        corr = attempt_data.get("correct_count", 0)
        incorr = attempt_data.get("incorrect_count", 0)
        unatt = attempt_data.get("unattempted_count", total_q - corr - incorr)
        attempted = corr + incorr
        accuracy = (corr / attempted * 100.0) if attempted > 0 else 0.0
        time_spent = attempt_data.get("time_spent_secs", 0)

        # Update KPI cards
        self.card_score.val_label.setText(f"{score:.1f} / {max_score:.0f}")
        self.card_accuracy.val_label.setText(f"{accuracy:.1f}%")
        self.card_attempted.val_label.setText(f"{attempted} / {total_q}")
        self.card_correct.val_label.setText(str(corr))
        self.card_incorrect.val_label.setText(str(incorr))

        hrs = time_spent // 3600
        mins = (time_spent % 3600) // 60
        secs = time_spent % 60
        self.card_time.val_label.setText(f"{hrs:02d}:{mins:02d}:{secs:02d}")

        # Update Section Breakdown Table
        section_scores = attempt_data.get("section_scores", {})
        self.table_sections.setRowCount(len(section_scores))
        for row, (sub, stats) in enumerate(section_scores.items()):
            tot = stats["total"]
            att = stats["attempted"]
            cor = stats["correct"]
            wrg = stats["wrong"]
            sc = stats["score"]
            acc = (cor / att * 100.0) if att > 0 else 0.0

            self.table_sections.setItem(row, 0, QTableWidgetItem(sub))
            self.table_sections.setItem(row, 1, QTableWidgetItem(str(tot)))
            self.table_sections.setItem(row, 2, QTableWidgetItem(str(att)))
            self.table_sections.setItem(row, 3, QTableWidgetItem(str(cor)))
            self.table_sections.setItem(row, 4, QTableWidgetItem(str(wrg)))
            self.table_sections.setItem(row, 5, QTableWidgetItem(f"{sc:.1f}"))
            self.table_sections.setItem(row, 6, QTableWidgetItem(f"{acc:.1f}%"))

        # Default filter: All questions
        self._filter_review("all")
        self.tabs.setCurrentIndex(0)

    def _filter_review(self, mode):
        self.filtered_review_indices = []
        for idx, q in enumerate(self.questions):
            qno = q["qno"]
            u_ans = self.user_answers.get(qno)
            c_ans = q.get("correct_ans", "").strip()

            if mode == "all":
                self.filtered_review_indices.append(idx)
            elif mode == "wrong" and u_ans and u_ans != c_ans:
                self.filtered_review_indices.append(idx)
            elif mode == "correct" and u_ans and u_ans == c_ans:
                self.filtered_review_indices.append(idx)
            elif mode == "unattempted" and not u_ans:
                self.filtered_review_indices.append(idx)

        # Populate review table
        self.table_review.setRowCount(len(self.filtered_review_indices))
        for row, idx in enumerate(self.filtered_review_indices):
            q = self.questions[idx]
            qno = q["qno"]
            sub = q.get("subject", "General")
            c_ans = q.get("correct_ans", "").strip()
            u_ans = self.user_answers.get(qno, "-")

            status = "⚪ Skipped"
            if u_ans != "-":
                status = "✅ Correct" if u_ans == c_ans else "❌ Incorrect"

            self.table_review.setItem(row, 0, QTableWidgetItem(str(qno)))
            self.table_review.setItem(row, 1, QTableWidgetItem(sub))
            self.table_review.setItem(row, 2, QTableWidgetItem(u_ans))
            self.table_review.setItem(row, 3, QTableWidgetItem(c_ans))
            self.table_review.setItem(row, 4, QTableWidgetItem(status))

        if self.filtered_review_indices:
            self.table_review.selectRow(0)

    def _on_review_question_selected(self):
        selected_rows = self.table_review.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if row < 0 or row >= len(self.filtered_review_indices):
            return

        q_idx = self.filtered_review_indices[row]
        q = self.questions[q_idx]
        qno = q["qno"]
        c_ans = q.get("correct_ans", "").strip()
        u_ans = self.user_answers.get(qno)

        self.lbl_rev_q_title.setText(f"Question #{qno} — {q.get('subject', 'General')}")

        # Format question text
        en = q.get("question_en", "")
        hi = q.get("question_hi", "")
        full = q.get("question_full", "")
        if en and hi and en != hi:
            q_text = f"{en}\n\n{hi}"
        else:
            q_text = en or hi or full
        self.lbl_rev_text.setText(q_text)

        # Image
        imgs = q.get("images", [])
        if imgs and os.path.exists(imgs[0]):
            pix = QPixmap(imgs[0])
            self.lbl_rev_img.setPixmap(pix.scaledToWidth(min(550, pix.width()), Qt.TransformationMode.SmoothTransformation))
            self.lbl_rev_img.setVisible(True)
        else:
            self.lbl_rev_img.setVisible(False)

        # Options
        for k in ("A", "B", "C", "D"):
            opt_en = q.get(f"opt_{k.lower()}_en", "")
            opt_hi = q.get(f"opt_{k.lower()}_hi", "")
            opt_full = q.get(f"opt_{k.lower()}_full", "")
            if opt_en and opt_hi and opt_en != opt_hi:
                opt_str = f"{opt_en} / {opt_hi}"
            else:
                opt_str = opt_en or opt_hi or opt_full
            self.rev_opt_labels[k].setText(opt_str)

            c = get_theme_colors(self.is_dark)
            c_frame = self.rev_opt_frames[k]
            if k == c_ans:
                c_frame.setStyleSheet(f"border: 2px solid {c['correct_border']}; background: {c['correct_bg']}; border-radius: 6px; padding: 6px;")
            elif k == u_ans and u_ans != c_ans:
                c_frame.setStyleSheet(f"border: 2px solid {c['wrong_border']}; background: {c['wrong_bg']}; border-radius: 6px; padding: 6px;")
            else:
                c_frame.setStyleSheet(f"border: 1.5px solid {c['card_border']}; background: {c['card_bg']}; border-radius: 6px; padding: 6px;")

        # Status Summary Badge
        if not u_ans:
            self.lbl_rev_summary.setText(f"⚪ You skipped this question. Correct Option: ({c_ans})")
            self.lbl_rev_summary.setStyleSheet("background: #f8f9fa; color: #6c757d; border: 1px solid #dee2e6;" if not self.is_dark else "background: #252538; color: #94a3b8; border: 1px solid #334155;")
        elif u_ans == c_ans:
            self.lbl_rev_summary.setText(f"✅ Your Answer: ({u_ans}) is Correct! (+1.00 Marks)")
            self.lbl_rev_summary.setStyleSheet("background: #d1e7dd; color: #0f5132; border: 1px solid #badbcc;" if not self.is_dark else "background: #123d24; color: #4ade80; border: 1px solid #16a34a;")
        else:
            self.lbl_rev_summary.setText(f"❌ Your Answer: ({u_ans}) was Incorrect. Correct Answer: ({c_ans})")
            self.lbl_rev_summary.setStyleSheet("background: #f8d7da; color: #842029; border: 1px solid #f5c2c7;" if not self.is_dark else "background: #451820; color: #f87171; border: 1px solid #dc2626;")

        # Personal Note Banner
        note = q.get("user_notes", "")
        if note and note.strip():
            self.lbl_rev_user_note.setText(f"📝 <b>My Study Note:</b> {note.strip()}")
            self.lbl_rev_user_note.setStyleSheet("background: #332b00; color: #fde047; border: 1px solid #854d0e; border-radius: 6px; padding: 6px 10px;" if self.is_dark else "background: #fff3cd; color: #664d03; border: 1px solid #ffecb5; border-radius: 6px; padding: 6px 10px;")
            self.lbl_rev_user_note.setVisible(True)
        else:
            self.lbl_rev_user_note.setVisible(False)

        # Detailed Solution Rendering
        sol = self.solution_engine.get_solution(q)
        en = sol.get("solution_en", "")
        hi = sol.get("solution_hi", "")
        c_th = get_theme_colors(self.is_dark)
        if en and hi and en != hi:
            sol_html = f"{en}<hr style='border: 0.5px solid {c_th['card_border']}; margin: 8px 0;'>{hi}"
        else:
            sol_html = en or hi
        self.lbl_rev_solution.setText(sol_html)

    def _on_edit_review_note(self):
        selected_rows = self.table_review.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if row < 0 or row >= len(self.filtered_review_indices):
            return

        q_idx = self.filtered_review_indices[row]
        q = self.questions[q_idx]
        cur_note = q.get("user_notes", "") or ""

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Personal Study Note — Question #{q['qno']}")
        dialog.resize(480, 260)
        d_layout = QVBoxLayout(dialog)
        d_layout.setContentsMargins(14, 12, 14, 12)
        d_layout.setSpacing(10)

        lbl = QLabel("Add your personal shortcut, mnemonic trick, or revision note:")
        lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        d_layout.addWidget(lbl)

        txt = QTextEdit()
        txt.setFont(QFont("Segoe UI", 10))
        txt.setPlainText(cur_note)
        txt.setPlaceholderText("e.g. Remember: SI formula SI = PRT/100, or trick for 10th 5-year plan...")
        d_layout.addWidget(txt)

        btn_h = QHBoxLayout()
        btn_h.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_save = QPushButton("💾 Save Note")
        btn_save.setStyleSheet("background: #198754; color: #fff; font-weight: bold; border-radius: 6px; padding: 6px 14px;")

        def do_save():
            new_text = txt.toPlainText().strip()
            shift_id = q.get("shift_id", self.attempt_data.get("shift_id", 1))
            self.db.save_user_note(shift_id, q["qno"], new_text)
            q["user_notes"] = new_text
            if new_text:
                self.lbl_rev_user_note.setText(f"📝 <b>My Study Note:</b> {new_text}")
                self.lbl_rev_user_note.setStyleSheet("background: #332b00; color: #fde047; border: 1px solid #854d0e; border-radius: 6px; padding: 6px 10px;" if self.is_dark else "background: #fff3cd; color: #664d03; border: 1px solid #ffecb5; border-radius: 6px; padding: 6px 10px;")
                self.lbl_rev_user_note.setVisible(True)
            else:
                self.lbl_rev_user_note.setVisible(False)
            dialog.accept()

        btn_save.clicked.connect(do_save)
        btn_h.addWidget(btn_cancel)
        btn_h.addWidget(btn_save)
        d_layout.addLayout(btn_h)
        dialog.exec()


    def set_dark_mode(self, is_dark):
        self.is_dark = is_dark
        c = get_theme_colors(is_dark)
        if hasattr(self, "kpi_frame"):
            self.kpi_frame.setStyleSheet(f"background: {c['card_bg']}; border: 1px solid {c['card_border']}; border-radius: 8px; padding: 10px;")
        for card in getattr(self, "kpi_cards", []):
            card.setStyleSheet(f"background: {c['sub_badge_bg']}; border: 1px solid {c['card_border']}; border-radius: 6px; padding: 6px;")
            if hasattr(card, "title_label"):
                card.title_label.setStyleSheet("color: #94a3b8;" if is_dark else "color: #6c757d;")
        if hasattr(self, "detail_frame"):
            self.detail_frame.setStyleSheet(f"background: {c['card_bg']}; border: 1px solid {c['card_border']}; border-radius: 8px; padding: 10px;")

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
        for tbl in (getattr(self, "table_sections", None), getattr(self, "table_review", None)):
            if tbl:
                tbl.setStyleSheet(tbl_qss)

        self._on_review_question_selected()

    def _on_retake(self):
        sh_id = self.attempt_data.get("shift_id", 1)
        shift_info = {"shift_index": sh_id, "name": self.attempt_data.get("title", f"Test #{sh_id}")}
        self.retake_test.emit(shift_info)
