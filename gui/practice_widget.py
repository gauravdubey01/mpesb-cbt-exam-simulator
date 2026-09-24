import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QComboBox, QMessageBox, QDialog,
    QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from gui.styles import get_theme_colors
from core.solution_engine import SolutionEngine

class PracticeWidget(QWidget):
    exit_to_dashboard = pyqtSignal()

    def __init__(self, db, extractor, parent=None):
        super().__init__(parent)
        self.db = db
        self.extractor = extractor
        self.solution_engine = SolutionEngine(self.db)
        self.questions = []
        self.filtered_questions = []
        self.current_q_idx = 0
        self.shift_info = {}
        self.lang_mode = "both"
        self.font_scale = 0
        self.is_dark = False

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(10)

        # Top Bar
        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)

        # Content Splitter or Layout
        h_layout = QHBoxLayout()
        h_layout.setSpacing(12)

        # Left: Question & Instant Answer Panel
        q_panel = self._create_question_panel()
        h_layout.addWidget(q_panel, 7)

        # Right: Practice Navigator & Stats
        nav_panel = self._create_nav_panel()
        h_layout.addWidget(nav_panel, 3)

        main_layout.addLayout(h_layout, 1)

    def _create_top_bar(self):
        self.top_bar_frame = QFrame()
        self.top_bar_frame.setStyleSheet("background: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 6px;")
        layout = QHBoxLayout(self.top_bar_frame)
        layout.setContentsMargins(10, 4, 10, 4)

        self.btn_back = QPushButton("⬅ Back to Dashboard")
        self.btn_back.setStyleSheet("""
            QPushButton {
                background: #f8f9fa; border: 1px solid #ced4da;
                border-radius: 6px; padding: 6px 14px; font-weight: 600;
            }
            QPushButton:hover { background: #e9ecef; }
        """)
        self.btn_back.clicked.connect(self.exit_to_dashboard.emit)
        layout.addWidget(self.btn_back)

        self.lbl_title = QLabel("📖 Practice & Revision Mode")
        self.lbl_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: #198754;")
        layout.addWidget(self.lbl_title)

        layout.addStretch()

        # Language Buttons
        lbl_l = QLabel("View:")
        lbl_l.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(lbl_l)

        self.btn_l_both = QPushButton("Bilingual")
        self.btn_l_both.setCheckable(True)
        self.btn_l_both.setChecked(True)
        self.btn_l_both.clicked.connect(lambda: self._set_lang("both"))
        layout.addWidget(self.btn_l_both)

        self.btn_l_en = QPushButton("English")
        self.btn_l_en.setCheckable(True)
        self.btn_l_en.clicked.connect(lambda: self._set_lang("en"))
        layout.addWidget(self.btn_l_en)

        self.btn_l_hi = QPushButton("हिन्दी")
        self.btn_l_hi.setCheckable(True)
        self.btn_l_hi.clicked.connect(lambda: self._set_lang("hi"))
        layout.addWidget(self.btn_l_hi)

        return self.top_bar_frame

    def _create_question_panel(self):
        self.q_panel_frame = QFrame()
        self.q_panel_frame.setStyleSheet("background: #ffffff; border: 1px solid #dee2e6; border-radius: 8px;")
        layout = QVBoxLayout(self.q_panel_frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Meta row
        meta_h = QHBoxLayout()
        self.lbl_q_header = QLabel("Question 1 of 200")
        self.lbl_q_header.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        meta_h.addWidget(self.lbl_q_header)

        self.lbl_subject = QLabel("Subject: General")
        self.lbl_subject.setStyleSheet("background: #e7f1ff; color: #0d6efd; border-radius: 4px; padding: 3px 8px; font-weight: bold;")
        meta_h.addWidget(self.lbl_subject)

        meta_h.addStretch()

        self.btn_bm = QPushButton("☆ Bookmark")
        self.btn_bm.setStyleSheet("border: 1px solid #ffc107; color: #b07d00; border-radius: 4px; padding: 4px 8px; font-weight: bold;")
        self.btn_bm.clicked.connect(self._toggle_bm)
        meta_h.addWidget(self.btn_bm)
        layout.addLayout(meta_h)

        # Scroll for Question & Options
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        c_widget = QWidget()
        c_layout = QVBoxLayout(c_widget)
        c_layout.setContentsMargins(4, 4, 10, 4)
        c_layout.setSpacing(12)

        self.lbl_q_text = QLabel()
        self.lbl_q_text.setWordWrap(True)
        self.lbl_q_text.setFont(QFont("Segoe UI", 12))
        self.lbl_q_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        c_layout.addWidget(self.lbl_q_text)

        self.lbl_img = QLabel()
        self.lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_img.setVisible(False)
        c_layout.addWidget(self.lbl_img)

        # Option Clickable Cards
        self.opt_cards = {}
        self.opt_labels = {}
        self.opt_badges = {}
        for k in ("A", "B", "C", "D"):
            c_frame = QFrame()
            c_frame.setStyleSheet("border: 1.5px solid #ced4da; border-radius: 8px; background: #ffffff; padding: 8px;")
            c_h = QHBoxLayout(c_frame)
            c_h.setContentsMargins(10, 8, 10, 8)
            
            b = QLabel(f" {k} ")
            b.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            b.setStyleSheet("background: #f1f3f5; color: #495057; border-radius: 4px; padding: 3px 7px;")
            c_h.addWidget(b)
            self.opt_badges[k] = b

            lbl = QLabel()
            lbl.setWordWrap(True)
            lbl.setFont(QFont("Segoe UI", 11))
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            c_h.addWidget(lbl, 1)

            c_frame.mousePressEvent = lambda ev, key=k: self._on_practice_option_click(key)
            self.opt_cards[k] = c_frame
            self.opt_labels[k] = lbl
            c_layout.addWidget(c_frame)

        # Feedback / Explanation Card
        self.feedback_card = QFrame()
        self.feedback_card.setStyleSheet("background: #f8f9fa; border: 1.5px solid #e9ecef; border-radius: 8px; padding: 12px;")
        self.feedback_layout = QVBoxLayout(self.feedback_card)
        self.feedback_layout.setSpacing(8)

        # Status & Answer Header
        self.lbl_feedback_status = QLabel()
        self.lbl_feedback_status.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.feedback_layout.addWidget(self.lbl_feedback_status)

        self.lbl_correct_reveal = QLabel()
        self.lbl_correct_reveal.setFont(QFont("Segoe UI", 11))
        self.lbl_correct_reveal.setWordWrap(True)
        self.feedback_layout.addWidget(self.lbl_correct_reveal)

        # Personal Note Banner (if present)
        self.lbl_user_note_banner = QLabel()
        self.lbl_user_note_banner.setFont(QFont("Segoe UI", 10))
        self.lbl_user_note_banner.setWordWrap(True)
        self.lbl_user_note_banner.setStyleSheet("background: #fff3cd; color: #664d03; border: 1px solid #ffecb5; border-radius: 6px; padding: 6px 10px;")
        self.lbl_user_note_banner.setVisible(False)
        self.feedback_layout.addWidget(self.lbl_user_note_banner)

        # Separator line
        self.sep_sol = QFrame()
        self.sep_sol.setFrameShape(QFrame.Shape.HLine)
        self.sep_sol.setStyleSheet("color: #ced4da; margin: 4px 0;")
        self.feedback_layout.addWidget(self.sep_sol)

        # Detailed Solution Box Header
        h_sol = QHBoxLayout()
        self.lbl_sol_title = QLabel("💡 Detailed Step-by-Step Solution & Concepts:")
        self.lbl_sol_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_sol_title.setStyleSheet("color: #0d6efd;")
        h_sol.addWidget(self.lbl_sol_title)
        h_sol.addStretch()

        self.btn_edit_note = QPushButton("✏️ Add / Edit My Note")
        self.btn_edit_note.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.btn_edit_note.setStyleSheet("background: #2563eb; color: #fff; border-radius: 4px; padding: 4px 10px;")
        self.btn_edit_note.clicked.connect(self._on_edit_note)
        h_sol.addWidget(self.btn_edit_note)
        self.feedback_layout.addLayout(h_sol)

        # Detailed Solution Text (rich HTML)
        self.lbl_solution_text = QLabel()
        self.lbl_solution_text.setFont(QFont("Segoe UI", 10))
        self.lbl_solution_text.setWordWrap(True)
        self.lbl_solution_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.feedback_layout.addWidget(self.lbl_solution_text)

        self.feedback_card.setVisible(False)
        c_layout.addWidget(self.feedback_card)
        c_layout.addStretch()

        scroll.setWidget(c_widget)
        layout.addWidget(scroll, 1)

        # Bottom Bar
        b_bar = QHBoxLayout()
        self.btn_show_ans = QPushButton("💡 Show Answer Key")
        self.btn_show_ans.setStyleSheet("background: #ffc107; color: #000; font-weight: bold; border-radius: 6px; padding: 8px 16px;")
        self.btn_show_ans.clicked.connect(self._reveal_answer)
        b_bar.addWidget(self.btn_show_ans)

        self.btn_view_pdf = QPushButton("📄 Original PDF Clip")
        self.btn_view_pdf.setStyleSheet("border: 1px solid #0d6efd; color: #0d6efd; border-radius: 6px; padding: 8px 14px; font-weight: bold;")
        self.btn_view_pdf.clicked.connect(self._view_clip)
        b_bar.addWidget(self.btn_view_pdf)

        b_bar.addStretch()

        btn_p = QPushButton("⬅ Previous")
        btn_p.setStyleSheet("background: #6c757d; color: #fff; font-weight: bold; border-radius: 6px; padding: 8px 16px;")
        btn_p.clicked.connect(self._prev)
        b_bar.addWidget(btn_p)

        btn_n = QPushButton("Next ➡")
        btn_n.setStyleSheet("background: #198754; color: #fff; font-weight: bold; border-radius: 6px; padding: 8px 18px;")
        btn_n.clicked.connect(self._next)
        b_bar.addWidget(btn_n)

        layout.addLayout(b_bar)
        return self.q_panel_frame

    def _create_nav_panel(self):
        self.nav_panel_frame = QFrame()
        self.nav_panel_frame.setStyleSheet("background: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px;")
        layout = QVBoxLayout(self.nav_panel_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        lbl = QLabel("Filter by Subject:")
        lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(lbl)

        self.combo_subject = QComboBox()
        self.combo_subject.currentIndexChanged.connect(self._filter_by_subject)
        layout.addWidget(self.combo_subject)

        lbl_grid = QLabel("Quick Jump:")
        lbl_grid.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(lbl_grid)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid_w = QWidget()
        self.grid_l = QGridLayout(self.grid_w)
        self.grid_l.setSpacing(5)
        self.nav_buttons = {}
        scroll.setWidget(self.grid_w)
        layout.addWidget(scroll, 1)

        return self.nav_panel_frame

    def load_practice(self, shift_info, questions):
        self.shift_info = shift_info
        self.questions = questions
        self.all_questions = questions
        self.filtered_questions = list(questions)
        self.current_q_idx = 0
        self.selected_answers = {}

        # Populate subject filter
        subjects = sorted(list(set(q.get("subject", "General") for q in questions)))
        self.combo_subject.blockSignals(True)
        self.combo_subject.clear()
        self.combo_subject.addItem("All Subjects")
        for s in subjects:
            self.combo_subject.addItem(s)
        self.combo_subject.blockSignals(False)

        self.lbl_title.setText(f"📖 Practice: {shift_info.get('name', 'Questions')}")
        self._build_grid()
        self._display(0)

    def _filter_by_subject(self, idx):
        sub = self.combo_subject.currentText()
        if sub == "All Subjects":
            self.filtered_questions = list(self.all_questions)
        else:
            self.filtered_questions = [q for q in self.all_questions if q.get("subject") == sub]
        self._build_grid()
        self._display(0)

    def _build_grid(self):
        while self.grid_l.count():
            item = self.grid_l.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.nav_buttons.clear()

        c = get_theme_colors(self.is_dark)
        cols = 5
        for idx, q in enumerate(self.filtered_questions):
            btn = QPushButton(str(idx + 1))
            btn.setFixedSize(36, 32)
            btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            btn.setStyleSheet(f"background: {c['palette_unvisited_bg']}; color: {c['palette_unvisited_text']}; border: 1px solid {c['palette_unvisited_border']}; border-radius: 4px;")
            btn.clicked.connect(lambda ch, i=idx: self._display(i))
            row = idx // cols
            col = idx % cols
            self.grid_l.addWidget(btn, row, col)
            self.nav_buttons[idx] = btn

    def _display(self, idx):
        if idx < 0 or idx >= len(self.filtered_questions):
            return
        self.current_q_idx = idx
        q = self.filtered_questions[idx]
        c = get_theme_colors(self.is_dark)

        self.lbl_q_header.setText(f"Question {idx + 1} of {len(self.filtered_questions)} (Paper Q.{q['qno']})")
        self.lbl_subject.setText(f"Subject: {q.get('subject', 'General')}")
        self.lbl_subject.setStyleSheet(f"background: {c['sub_badge_bg']}; color: {c['sub_badge_text']}; border: 1px solid {c['sub_badge_border']}; border-radius: 4px; padding: 3px 8px; font-weight: bold;")

        is_bm = self.db.is_bookmarked(self.shift_info.get("shift_index", 1), q["qno"])
        self.btn_bm.setText("★ Bookmarked" if is_bm else "☆ Bookmark")
        self.btn_bm.setStyleSheet(f"background: {c['bm_bg']}; color: {c['bm_text']}; border: 1px solid {c['bm_border']}; border-radius: 4px; padding: 4px 8px; font-weight: bold;")

        # Text
        q_txt = self._format_text(q.get("question_en", ""), q.get("question_hi", ""), q.get("question_full", ""))
        self.lbl_q_text.setText(q_txt)

        # Image
        imgs = q.get("images", [])
        if imgs and os.path.exists(imgs[0]):
            pix = QPixmap(imgs[0])
            self.lbl_img.setPixmap(pix.scaledToWidth(min(600, pix.width()), Qt.TransformationMode.SmoothTransformation))
            self.lbl_img.setVisible(True)
        else:
            self.lbl_img.setVisible(False)

        # Options
        for k in ("A", "B", "C", "D"):
            en = q.get(f"opt_{k.lower()}_en", "")
            hi = q.get(f"opt_{k.lower()}_hi", "")
            full = q.get(f"opt_{k.lower()}_full", "")
            self.opt_labels[k].setText(self._format_text(en, hi, full))

        # Check if already answered in practice
        sel = self.selected_answers.get(q["qno"])
        if sel:
            self._render_feedback(sel)
        else:
            self.feedback_card.setVisible(False)
            self._reset_card_styles()

        # Update Grid button highlight
        for i, btn in self.nav_buttons.items():
            if i == idx:
                btn.setStyleSheet(f"background: {c['pill_active_bg']}; color: {c['pill_active_text']}; font-weight: bold; border-radius: 4px;")
            elif self.filtered_questions[i]["qno"] in self.selected_answers:
                btn.setStyleSheet("background: #16a34a; color: #ffffff; font-weight: bold; border-radius: 4px;")
            else:
                btn.setStyleSheet(f"background: {c['palette_unvisited_bg']}; color: {c['palette_unvisited_text']}; border: 1px solid {c['palette_unvisited_border']}; border-radius: 4px;")

    def _reset_card_styles(self):
        c = get_theme_colors(self.is_dark)
        for k, card in self.opt_cards.items():
            card.setStyleSheet(f"border: 1.5px solid {c['card_border']}; border-radius: 8px; background: {c['card_bg']}; padding: 8px;")
        for k, badge in getattr(self, "opt_badges", {}).items():
            badge.setStyleSheet(f"background: {c['opt_badge_bg']}; color: {c['opt_badge_text']}; border: 1px solid {c['opt_badge_border']}; border-radius: 4px; padding: 3px 7px;")

    def _on_practice_option_click(self, opt_key):
        q = self.filtered_questions[self.current_q_idx]
        self.selected_answers[q["qno"]] = opt_key
        self._render_feedback(opt_key)

    def _reveal_answer(self):
        q = self.filtered_questions[self.current_q_idx]
        corr = q.get("correct_ans", "A").strip()
        self.selected_answers[q["qno"]] = corr
        self._render_feedback(corr)

    def _render_feedback(self, chosen):
        q = self.filtered_questions[self.current_q_idx]
        corr = q.get("correct_ans", "A").strip()
        c = get_theme_colors(self.is_dark)

        for k, card in self.opt_cards.items():
            if k == corr:
                card.setStyleSheet(f"border: 2px solid {c['correct_border']}; border-radius: 8px; background: {c['correct_bg']}; padding: 8px;")
            elif k == chosen and chosen != corr:
                card.setStyleSheet(f"border: 2px solid {c['wrong_border']}; border-radius: 8px; background: {c['wrong_bg']}; padding: 8px;")
            else:
                card.setStyleSheet(f"border: 1.5px solid {c['card_border']}; border-radius: 8px; background: {c['card_bg']}; padding: 8px;")

        self.feedback_card.setStyleSheet(f"background: {c['card_bg']}; border: 1.5px solid {c['card_border']}; border-radius: 8px; padding: 12px;")
        self.feedback_card.setVisible(True)
        if chosen == corr:
            self.lbl_feedback_status.setText("✅ Correct Answer! (+1.00 Marks)")
            self.lbl_feedback_status.setStyleSheet("color: #16a34a;")
        else:
            self.lbl_feedback_status.setText(f"❌ Incorrect Response (You selected Option {chosen})")
            self.lbl_feedback_status.setStyleSheet("color: #dc2626;")

        self.lbl_correct_reveal.setText(f"Official Answer Key: Option ({corr})  |  Subject: {q.get('subject', 'General')}")
        self.lbl_correct_reveal.setStyleSheet(f"color: {c['text_muted']}; font-weight: 600;")

        # User Note Banner
        note = q.get("user_notes", "")
        if note and note.strip():
            self.lbl_user_note_banner.setText(f"📝 <b>My Study Note:</b> {note.strip()}")
            self.lbl_user_note_banner.setStyleSheet("background: #332b00; color: #fde047; border: 1px solid #854d0e; border-radius: 6px; padding: 6px 10px;" if self.is_dark else "background: #fff3cd; color: #664d03; border: 1px solid #ffecb5; border-radius: 6px; padding: 6px 10px;")
            self.lbl_user_note_banner.setVisible(True)
        else:
            self.lbl_user_note_banner.setVisible(False)

        # Detailed Solution Rendering
        sol = self.solution_engine.get_solution(q)
        en = sol.get("solution_en", "")
        hi = sol.get("solution_hi", "")
        if self.lang_mode == "en":
            sol_html = en or hi
        elif self.lang_mode == "hi":
            sol_html = hi or en
        else:
            sol_html = f"{en}<hr style='border: 0.5px solid {c['card_border']}; margin: 8px 0;'>{hi}" if en and hi and en != hi else (en or hi)
        self.lbl_solution_text.setText(sol_html)

    def _on_edit_note(self):
        q = self.filtered_questions[self.current_q_idx]
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
        btn_save.setStyleSheet("background: #16a34a; color: #fff; font-weight: bold; border-radius: 6px; padding: 6px 16px;")

        def save():
            new_note = txt.toPlainText().strip()
            sh_id = q.get("shift_id", self.shift_info.get("shift_index", 1))
            self.db.save_user_note(sh_id, q["qno"], new_note)
            q["user_notes"] = new_note
            if new_note:
                self.lbl_user_note_banner.setText(f"📝 <b>My Study Note:</b> {new_note}")
                self.lbl_user_note_banner.setStyleSheet("background: #332b00; color: #fde047; border: 1px solid #854d0e; border-radius: 6px; padding: 6px 10px;" if self.is_dark else "background: #fff3cd; color: #664d03; border: 1px solid #ffecb5; border-radius: 6px; padding: 6px 10px;")
                self.lbl_user_note_banner.setVisible(True)
            else:
                self.lbl_user_note_banner.setVisible(False)
            dialog.accept()

        btn_save.clicked.connect(save)
        btn_h.addWidget(btn_cancel)
        btn_h.addWidget(btn_save)
        d_layout.addLayout(btn_h)
        dialog.exec()

    def set_dark_mode(self, is_dark):
        self.is_dark = is_dark
        c = get_theme_colors(is_dark)
        if hasattr(self, "top_bar_frame"):
            self.top_bar_frame.setStyleSheet(f"background: {c['topbar_bg']}; border: 1px solid {c['topbar_border']}; border-radius: 8px; padding: 6px;")
        if hasattr(self, "btn_back"):
            self.btn_back.setStyleSheet(f"background: {c['btn_back_bg']}; color: {c['btn_back_text']}; border: 1px solid {c['btn_back_border']}; border-radius: 6px; padding: 6px 14px; font-weight: 600;")
        if hasattr(self, "q_panel_frame"):
            self.q_panel_frame.setStyleSheet(f"background: {c['card_bg']}; border: 1px solid {c['card_border']}; border-radius: 8px;")
        if hasattr(self, "nav_panel_frame"):
            self.nav_panel_frame.setStyleSheet(f"background: {c['card_bg']}; border: 1px solid {c['card_border']}; border-radius: 8px; padding: 10px;")
        if hasattr(self, "btn_view_pdf"):
            col = "#60a5fa" if is_dark else "#0d6efd"
            self.btn_view_pdf.setStyleSheet(f"border: 1px solid {col}; color: {col}; border-radius: 6px; padding: 8px 14px; font-weight: bold;")
        if hasattr(self, "btn_prev"):
            self.btn_prev.setStyleSheet(f"background: {'#334155' if is_dark else '#6c757d'}; color: #fff; font-weight: bold; border-radius: 6px; padding: 8px 16px;")
        if hasattr(self, "lbl_subject"):
            self.lbl_subject.setStyleSheet(f"background: {c['sub_badge_bg']}; color: {c['sub_badge_text']}; border: 1px solid {c['sub_badge_border']}; border-radius: 4px; padding: 3px 8px; font-weight: bold;")
        if hasattr(self, "btn_bm"):
            self.btn_bm.setStyleSheet(f"background: {c['bm_bg']}; color: {c['bm_text']}; border: 1px solid {c['bm_border']}; border-radius: 4px; padding: 4px 8px; font-weight: bold;")
        self._reset_card_styles()
        if getattr(self, "filtered_questions", None):
            self._display(self.current_q_idx)

    def _format_text(self, en, hi, fallback):
        if self.lang_mode == "en":
            return en if en.strip() else fallback
        elif self.lang_mode == "hi":
            return hi if hi.strip() else fallback
        else:
            if en.strip() and hi.strip() and en.strip() != hi.strip():
                return f"{en.strip()}\n\n{hi.strip()}"
            return en.strip() or hi.strip() or fallback.strip()

    def _set_lang(self, mode):
        self.lang_mode = mode
        self.btn_l_both.setChecked(mode == "both")
        self.btn_l_en.setChecked(mode == "en")
        self.btn_l_hi.setChecked(mode == "hi")
        self._display(self.current_q_idx)

    def _prev(self):
        if self.current_q_idx > 0:
            self._display(self.current_q_idx - 1)

    def _next(self):
        if self.current_q_idx < len(self.filtered_questions) - 1:
            self._display(self.current_q_idx + 1)

    def _toggle_bm(self):
        q = self.filtered_questions[self.current_q_idx]
        sh_id = self.shift_info.get("shift_index", 1)
        res = self.db.toggle_bookmark(sh_id, q["qno"], q.get("subject", ""))
        self.btn_bm.setText("★ Bookmarked" if res else "☆ Bookmark")

    def _view_clip(self):
        q = self.filtered_questions[self.current_q_idx]
        sh_id = self.shift_info.get("shift_index", 1)
        clip = self.extractor.render_question_clip(sh_id, q["qno"], q.get("page_num", 0))
        if clip and os.path.exists(clip):
            d = QDialog(self)
            d.setWindowTitle(f"Question {q['qno']} PDF Clip")
            d.resize(700, 480)
            l = QVBoxLayout(d)
            s = QScrollArea()
            s.setWidgetResizable(True)
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setPixmap(QPixmap(clip))
            s.setWidget(lbl)
            l.addWidget(s)
            b = QPushButton("Close")
            b.clicked.connect(d.accept)
            l.addWidget(b, 0, Qt.AlignmentFlag.AlignRight)
            d.exec()
