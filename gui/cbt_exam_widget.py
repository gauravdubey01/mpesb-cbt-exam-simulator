import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QButtonGroup, QRadioButton,
    QDialog, QMessageBox, QSpacerItem, QSizePolicy, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon, QKeySequence, QShortcut

from gui.styles import get_theme_colors

class CBTExamWidget(QWidget):
    # Signals
    test_submitted = pyqtSignal(dict)  # emits attempt result dictionary
    exit_to_dashboard = pyqtSignal()

    def __init__(self, db, extractor, parent=None):
        super().__init__(parent)
        self.db = db
        self.extractor = extractor
        self.current_shift_info = None
        self.questions = []
        self.current_q_idx = 0
        self.is_dark = False
        
        # Test state
        self.user_answers = {}        # qno -> 'A' | 'B' | 'C' | 'D'
        self.question_states = {}     # qno -> 'not_visited'|'not_answered'|'answered'|'marked'|'marked_answered'
        self.marked_for_review = set() # set of qnos
        self.time_total_secs = 180 * 60 # 3 hours default
        self.time_left_secs = self.time_total_secs
        
        # Settings
        self.lang_mode = "both"  # "both", "en", "hi"
        self.font_scale = 0      # delta in pt
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer_tick)
        
        self._init_ui()
        self._setup_shortcuts()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # 1. Top Header Bar
        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)

        # 2. Section Tabs Bar
        self.sections_bar = self._create_sections_bar()
        main_layout.addWidget(self.sections_bar)

        # 3. Middle Work Area (Splitter: Question Area on Left, Palette on Right)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        left_container = self._create_question_area()
        right_container = self._create_palette_area()

        splitter.addWidget(left_container)
        splitter.addWidget(right_container)
        splitter.setStretchFactor(0, 7)  # Question area gets 70% width
        splitter.setStretchFactor(1, 3)  # Palette gets 30% width

        main_layout.addWidget(splitter, 1)

    def _create_top_bar(self):
        self.top_bar_frame = QFrame()
        self.top_bar_frame.setObjectName("topBar")
        self.top_bar_frame.setStyleSheet("""
            QFrame#topBar {
                background: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        layout = QHBoxLayout(self.top_bar_frame)
        layout.setContentsMargins(12, 6, 12, 6)

        # Title
        self.lbl_exam_title = QLabel("MPESB Patwari CBT Simulator")
        self.lbl_exam_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lbl_exam_title.setStyleSheet("color: #0d6efd;")
        layout.addWidget(self.lbl_exam_title)

        layout.addStretch()

        # Language Selector
        lbl_lang = QLabel("Language:")
        lbl_lang.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(lbl_lang)

        self.btn_lang_both = QPushButton("Bilingual (दोनों)")
        self.btn_lang_both.setCheckable(True)
        self.btn_lang_both.setChecked(True)
        self.btn_lang_both.clicked.connect(lambda: self.set_language_mode("both"))
        layout.addWidget(self.btn_lang_both)

        self.btn_lang_en = QPushButton("English")
        self.btn_lang_en.setCheckable(True)
        self.btn_lang_en.clicked.connect(lambda: self.set_language_mode("en"))
        layout.addWidget(self.btn_lang_en)

        self.btn_lang_hi = QPushButton("हिन्दी")
        self.btn_lang_hi.setCheckable(True)
        self.btn_lang_hi.clicked.connect(lambda: self.set_language_mode("hi"))
        layout.addWidget(self.btn_lang_hi)

        layout.addSpacing(15)

        # Font Zoom Controls
        lbl_font = QLabel("Font:")
        layout.addWidget(lbl_font)
        btn_font_dec = QPushButton("A-")
        btn_font_dec.setFixedWidth(32)
        btn_font_dec.clicked.connect(lambda: self.adjust_font_scale(-1))
        layout.addWidget(btn_font_dec)

        btn_font_inc = QPushButton("A+")
        btn_font_inc.setFixedWidth(32)
        btn_font_inc.clicked.connect(lambda: self.adjust_font_scale(1))
        layout.addWidget(btn_font_inc)

        layout.addSpacing(20)

        # Timer Badge
        self.lbl_timer = QLabel("Time Left: 03:00:00")
        self.lbl_timer.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lbl_timer.setStyleSheet("""
            background-color: #e7f1ff;
            color: #0d6efd;
            border: 1.5px solid #0d6efd;
            border-radius: 6px;
            padding: 4px 12px;
        """)
        layout.addWidget(self.lbl_timer)

        return self.top_bar_frame

    def _create_sections_bar(self):
        self.scroll_sections = QScrollArea()
        self.scroll_sections.setFixedHeight(46)
        self.scroll_sections.setWidgetResizable(True)
        self.scroll_sections.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_sections.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_sections.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.sections_widget = QWidget()
        self.sections_layout = QHBoxLayout(self.sections_widget)
        self.sections_layout.setContentsMargins(0, 0, 0, 0)
        self.sections_layout.setSpacing(6)
        self.scroll_sections.setWidget(self.sections_widget)

        return self.scroll_sections

    def _create_question_area(self):
        self.question_container = QFrame()
        self.question_container.setObjectName("questionArea")
        self.question_container.setStyleSheet("""
            QFrame#questionArea {
                background: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(self.question_container)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Question Sub-header (Q Number, Subject Badge, Marks, Bookmark)
        q_meta_layout = QHBoxLayout()
        self.lbl_q_num = QLabel("Question No. 1")
        self.lbl_q_num.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        q_meta_layout.addWidget(self.lbl_q_num)

        self.lbl_q_subject = QLabel("Subject: General Knowledge")
        self.lbl_q_subject.setStyleSheet("""
            background: #f1f3f5;
            color: #495057;
            border-radius: 4px;
            padding: 3px 8px;
            font-weight: 600;
        """)
        q_meta_layout.addWidget(self.lbl_q_subject)

        q_meta_layout.addStretch()

        lbl_marks = QLabel("Marks: +1.00  |  -0.00")
        lbl_marks.setStyleSheet("color: #6c757d; font-size: 11px;")
        q_meta_layout.addWidget(lbl_marks)

        self.btn_bookmark = QPushButton("☆ Bookmark")
        self.btn_bookmark.setFixedWidth(100)
        self.btn_bookmark.setCheckable(True)
        self.btn_bookmark.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                border: 1px solid #ffc107;
                color: #b07d00;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:checked {
                background: #ffc107;
                color: #000000;
            }
        """)
        self.btn_bookmark.clicked.connect(self._toggle_current_bookmark)
        q_meta_layout.addWidget(self.btn_bookmark)

        layout.addLayout(q_meta_layout)

        # Separator Line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #e9ecef;")
        layout.addWidget(line)

        # Question Content Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        q_content_widget = QWidget()
        self.q_content_layout = QVBoxLayout(q_content_widget)
        self.q_content_layout.setContentsMargins(4, 4, 12, 4)
        self.q_content_layout.setSpacing(14)

        # Question Text Label
        self.lbl_question_text = QLabel()
        self.lbl_question_text.setWordWrap(True)
        self.lbl_question_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lbl_question_text.setFont(QFont("Segoe UI", 12))
        self.q_content_layout.addWidget(self.lbl_question_text)

        # Image Container (for questions with diagrams)
        self.lbl_question_img = QLabel()
        self.lbl_question_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_question_img.setVisible(False)
        self.q_content_layout.addWidget(self.lbl_question_img)

        # Option Cards Layout
        self.options_container = QVBoxLayout()
        self.options_container.setSpacing(10)
        self.option_cards = {}
        self.option_radios = {}
        self.option_text_labels = {}
        self.option_badges = {}

        self.btn_group = QButtonGroup(self)
        for opt_key in ("A", "B", "C", "D"):
            card, radio, lbl_text, badge = self._create_option_card(opt_key)
            self.option_cards[opt_key] = card
            self.option_radios[opt_key] = radio
            self.option_text_labels[opt_key] = lbl_text
            self.option_badges[opt_key] = badge
            self.btn_group.addButton(radio)
            self.options_container.addWidget(card)

        self.btn_group.buttonClicked.connect(self._on_option_selected)
        self.q_content_layout.addLayout(self.options_container)
        self.q_content_layout.addStretch()

        scroll.setWidget(q_content_widget)
        layout.addWidget(scroll, 1)

        # Bottom Action Bar
        bottom_bar = self._create_bottom_action_bar()
        layout.addWidget(bottom_bar)

        return self.question_container

    def _create_option_card(self, opt_key):
        card = QFrame()
        card.setObjectName(f"optCard_{opt_key}")
        card.setProperty("class", "option-card")
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1.5px solid #ced4da;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame:hover {
                background-color: #f8fbff;
                border-color: #86b7fe;
            }
        """)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        radio = QRadioButton()
        radio.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(radio)

        badge = QLabel(f" {opt_key} ")
        badge.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        badge.setStyleSheet("""
            background: #e9ecef;
            color: #212529;
            border-radius: 4px;
            padding: 3px 7px;
        """)
        layout.addWidget(badge)

        lbl_text = QLabel()
        lbl_text.setWordWrap(True)
        lbl_text.setFont(QFont("Segoe UI", 11))
        lbl_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(lbl_text, 1)

        # Allow clicking entire card to select radio
        card.mousePressEvent = lambda ev, r=radio: r.setChecked(True) or self._on_option_selected(r)

        return card, radio, lbl_text, badge

    def _create_bottom_action_bar(self):
        bar = QFrame()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(10)

        self.btn_mark_review = QPushButton("🟣 Mark for Review & Next")
        self.btn_mark_review.setObjectName("btnMarkReview")
        self.btn_mark_review.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: #ffffff;
                font-weight: 600;
                font-size: 13px;
                border-radius: 6px;
                padding: 10px 16px;
            }
            QPushButton:hover { background-color: #59359a; }
        """)
        self.btn_mark_review.clicked.connect(self._mark_for_review_and_next)
        layout.addWidget(self.btn_mark_review)

        self.btn_clear = QPushButton("🧹 Clear Response")
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #6c757d;
                border: 1.5px solid #ced4da;
                font-weight: 600;
                font-size: 13px;
                border-radius: 6px;
                padding: 10px 14px;
            }
            QPushButton:hover { background-color: #f8f9fa; border-color: #adb5bd; }
        """)
        self.btn_clear.clicked.connect(self._clear_response)
        layout.addWidget(self.btn_clear)

        self.btn_view_clip = QPushButton("📄 View Original PDF Clip")
        self.btn_view_clip.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #0d6efd;
                border: 1.5px solid #0d6efd;
                font-weight: 600;
                font-size: 13px;
                border-radius: 6px;
                padding: 10px 14px;
            }
            QPushButton:hover { background-color: #e7f1ff; }
        """)
        self.btn_view_clip.clicked.connect(self._view_original_clip)
        layout.addWidget(self.btn_view_clip)

        layout.addStretch()

        self.btn_prev = QPushButton("⬅️ Previous")
        self.btn_prev.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: #ffffff;
                font-weight: 600;
                font-size: 13px;
                border-radius: 6px;
                padding: 10px 18px;
            }
            QPushButton:hover { background-color: #5c636a; }
        """)
        self.btn_prev.clicked.connect(self._prev_question)
        layout.addWidget(self.btn_prev)

        self.btn_save_next = QPushButton("💾 Save & Next ➡️")
        self.btn_save_next.setStyleSheet("""
            QPushButton {
                background-color: #198754;
                color: #ffffff;
                font-weight: 600;
                font-size: 13px;
                border-radius: 6px;
                padding: 10px 22px;
            }
            QPushButton:hover { background-color: #157347; }
        """)
        self.btn_save_next.clicked.connect(self._save_and_next)
        layout.addWidget(self.btn_save_next)

        return bar

    def _create_palette_area(self):
        self.palette_container = QFrame()
        self.palette_container.setObjectName("paletteArea")
        self.palette_container.setStyleSheet("""
            QFrame#paletteArea {
                background: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(self.palette_container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Candidate Profile Box
        self.profile_frame = QFrame()
        self.profile_frame.setStyleSheet("background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 6px;")
        p_layout = QHBoxLayout(self.profile_frame)
        p_layout.setContentsMargins(8, 6, 8, 6)

        lbl_avatar = QLabel("👤")
        lbl_avatar.setFont(QFont("Segoe UI", 18))
        p_layout.addWidget(lbl_avatar)

        p_info = QVBoxLayout()
        lbl_name = QLabel("Candidate: Aspirant")
        lbl_name.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_sub = QLabel("Roll No: 2024-PATWARI")
        lbl_sub.setFont(QFont("Segoe UI", 9))
        lbl_sub.setStyleSheet("color: #6c757d;")
        p_info.addWidget(lbl_name)
        p_info.addWidget(lbl_sub)
        p_layout.addLayout(p_info)
        p_layout.addStretch()

        layout.addWidget(self.profile_frame)

        # Legend Box
        self.legend_frame = self._create_legend_box()
        layout.addWidget(self.legend_frame)

        # Question Grid Label
        lbl_grid_title = QLabel("Question Palette (Click to Jump):")
        lbl_grid_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(lbl_grid_title)

        # Scrollable Question Grid
        scroll_grid = QScrollArea()
        scroll_grid.setWidgetResizable(True)
        scroll_grid.setStyleSheet("QScrollArea { border: 1px solid #e9ecef; border-radius: 6px; }")

        self.grid_widget = QWidget()
        self.palette_grid = QGridLayout(self.grid_widget)
        self.palette_grid.setContentsMargins(8, 8, 8, 8)
        self.palette_grid.setSpacing(6)
        self.palette_buttons = {}

        scroll_grid.setWidget(self.grid_widget)
        layout.addWidget(scroll_grid, 1)

        # Big Submit Button
        self.btn_submit = QPushButton("SUBMIT TEST")
        self.btn_submit.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: #ffffff;
                font-weight: bold;
                font-size: 15px;
                border-radius: 8px;
                padding: 12px;
            }
            QPushButton:hover { background-color: #0b5ed7; }
        """)
        self.btn_submit.clicked.connect(self._confirm_and_submit_test)
        layout.addWidget(self.btn_submit)

        return self.palette_container

    def _create_legend_box(self):
        frame = QFrame()
        frame.setStyleSheet("background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 6px;")
        layout = QGridLayout(frame)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.lbl_cnt_answered = QLabel("0")
        self.lbl_cnt_not_answered = QLabel("0")
        self.lbl_cnt_marked = QLabel("0")
        self.lbl_cnt_not_visited = QLabel("0")

        # Row 0: Answered & Not Answered
        layout.addWidget(self._make_legend_item("#198754", "Answered", self.lbl_cnt_answered), 0, 0)
        layout.addWidget(self._make_legend_item("#dc3545", "Not Answered", self.lbl_cnt_not_answered), 0, 1)

        # Row 1: Marked & Not Visited
        layout.addWidget(self._make_legend_item("#6f42c1", "Marked", self.lbl_cnt_marked), 1, 0)
        layout.addWidget(self._make_legend_item("#adb5bd", "Not Visited", self.lbl_cnt_not_visited), 1, 1)

        return frame

    def _make_legend_item(self, color, label_text, count_label):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(2, 2, 2, 2)
        h.setSpacing(6)

        dot = QLabel()
        dot.setFixedSize(14, 14)
        dot.setStyleSheet(f"background-color: {color}; border-radius: 7px;")
        h.addWidget(dot)

        txt = QLabel(label_text)
        txt.setFont(QFont("Segoe UI", 9))
        h.addWidget(txt)

        count_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        h.addWidget(count_label)
        h.addStretch()

        return w

    def _setup_shortcuts(self):
        # Keyboard Shortcuts
        QShortcut(QKeySequence("1"), self, lambda: self._select_option_by_key("A"))
        QShortcut(QKeySequence("A"), self, lambda: self._select_option_by_key("A"))
        QShortcut(QKeySequence("2"), self, lambda: self._select_option_by_key("B"))
        QShortcut(QKeySequence("B"), self, lambda: self._select_option_by_key("B"))
        QShortcut(QKeySequence("3"), self, lambda: self._select_option_by_key("C"))
        QShortcut(QKeySequence("C"), self, lambda: self._select_option_by_key("C"))
        QShortcut(QKeySequence("4"), self, lambda: self._select_option_by_key("D"))
        QShortcut(QKeySequence("D"), self, lambda: self._select_option_by_key("D"))

        QShortcut(QKeySequence("Right"), self, self._save_and_next)
        QShortcut(QKeySequence("Left"), self, self._prev_question)

    def _select_option_by_key(self, opt_key):
        if opt_key in self.option_radios:
            self.option_radios[opt_key].setChecked(True)
            self._on_option_selected(self.option_radios[opt_key])

    # -------------------------------------------------------------
    # Test Loading and State Management
    # -------------------------------------------------------------
    def load_test(self, shift_info, questions, duration_minutes=180):
        self.current_shift_info = shift_info
        self.questions = questions
        self.current_q_idx = 0
        self.user_answers.clear()
        self.marked_for_review.clear()
        self.question_states.clear()

        for q in questions:
            self.question_states[q["qno"]] = "not_visited"

        self.time_total_secs = duration_minutes * 60
        self.time_left_secs = self.time_total_secs

        self.lbl_exam_title.setText(shift_info.get("name", "CBT Exam Paper"))
        self._build_section_tabs()
        self._build_palette_buttons()
        self._display_question(0)

        self.timer.start(1000)
        self._update_timer_display()

    def _build_section_tabs(self):
        # Clear existing tabs
        while self.sections_layout.count():
            item = self.sections_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Group questions by subject
        subject_first_q = {}
        subject_counts = {}
        for idx, q in enumerate(self.questions):
            sub = q.get("subject", "General")
            if sub not in subject_first_q:
                subject_first_q[sub] = idx
                subject_counts[sub] = 0
            subject_counts[sub] += 1

        self.section_buttons = {}
        for sub, first_idx in subject_first_q.items():
            btn = QPushButton(f"{sub} ({subject_counts[sub]})")
            btn.setProperty("class", "section-pill")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e9ecef;
                    color: #495057;
                    border-radius: 14px;
                    padding: 4px 12px;
                    font-size: 12px;
                    font-weight: 600;
                    border: 1px solid #ced4da;
                }
                QPushButton:hover { background-color: #dee2e6; }
            """)
            btn.clicked.connect(lambda ch, idx=first_idx: self._jump_to_question(idx))
            self.sections_layout.addWidget(btn)
            self.section_buttons[sub] = btn

        self.sections_layout.addStretch()

    def _build_palette_buttons(self):
        # Clear existing buttons
        while self.palette_grid.count():
            item = self.palette_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.palette_buttons.clear()

        cols = 5
        for idx, q in enumerate(self.questions):
            qno = q["qno"]
            btn = QPushButton(str(qno))
            btn.setFixedSize(36, 32)
            btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda ch, i=idx: self._jump_to_question(i))
            
            row = idx // cols
            col = idx % cols
            self.palette_grid.addWidget(btn, row, col)
            self.palette_buttons[qno] = btn

        self._refresh_palette_styles()

    def _display_question(self, idx):
        if idx < 0 or idx >= len(self.questions):
            return

        self.current_q_idx = idx
        q = self.questions[idx]
        qno = q["qno"]

        # Mark question state as not_answered if it was not_visited
        if self.question_states.get(qno) == "not_visited":
            self.question_states[qno] = "not_answered"

        # Update metadata header
        self.lbl_q_num.setText(f"Question No. {qno} of {len(self.questions)}")
        sub = q.get("subject", "General")
        self.lbl_q_subject.setText(f"Subject: {sub}")
        c = get_theme_colors(self.is_dark)
        self.lbl_q_subject.setStyleSheet(f"background: {c['sub_badge_bg']}; color: {c['sub_badge_text']}; border: 1px solid {c['sub_badge_border']}; border-radius: 4px; padding: 3px 8px; font-weight: 600;")

        # Update bookmark button
        is_bm = self.db.is_bookmarked(self.current_shift_info.get("shift_index", 1), qno)
        self.btn_bookmark.setChecked(is_bm)
        self.btn_bookmark.setText("★ Bookmarked" if is_bm else "☆ Bookmark")
        self.btn_bookmark.setStyleSheet(f"background: {c['bm_bg']}; color: {c['bm_text']}; border: 1px solid {c['bm_border']}; border-radius: 4px; padding: 4px 8px; font-weight: bold;")

        # Format Question Text based on language mode
        q_text = self._format_bilingual_text(q.get("question_en", ""), q.get("question_hi", ""), q.get("question_full", ""))
        self.lbl_question_text.setText(q_text)
        base_font = QFont("Segoe UI", 12 + self.font_scale)
        self.lbl_question_text.setFont(base_font)

        # Show Question Image if present
        images = q.get("images", [])
        if images and os.path.exists(images[0]):
            pix = QPixmap(images[0])
            if not pix.isNull():
                scaled_pix = pix.scaledToWidth(min(650, pix.width()), Qt.TransformationMode.SmoothTransformation)
                self.lbl_question_img.setPixmap(scaled_pix)
                self.lbl_question_img.setVisible(True)
            else:
                self.lbl_question_img.setVisible(False)
        else:
            self.lbl_question_img.setVisible(False)

        # Populate Options
        self.btn_group.setExclusive(False)
        current_ans = self.user_answers.get(qno)

        for opt_key in ("A", "B", "C", "D"):
            en = q.get(f"opt_{opt_key.lower()}_en", "")
            hi = q.get(f"opt_{opt_key.lower()}_hi", "")
            full = q.get(f"opt_{opt_key.lower()}_full", "")
            opt_text = self._format_bilingual_text(en, hi, full)
            self.option_text_labels[opt_key].setText(opt_text)
            self.option_text_labels[opt_key].setFont(QFont("Segoe UI", 11 + self.font_scale))

            if opt_key in self.option_badges:
                self.option_badges[opt_key].setStyleSheet(f"background: {c['opt_badge_bg']}; color: {c['opt_badge_text']}; border: 1px solid {c['opt_badge_border']}; border-radius: 4px; padding: 3px 7px;")

            radio = self.option_radios[opt_key]
            card = self.option_cards[opt_key]
            is_selected = (current_ans == opt_key)
            radio.setChecked(is_selected)
            if is_selected:
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: {c['card_selected_bg']};
                        border: 2px solid {c['card_selected_border']};
                        border-radius: 8px;
                        padding: 10px;
                    }}
                """)
            else:
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: {c['card_bg']};
                        border: 1.5px solid {c['card_border']};
                        border-radius: 8px;
                        padding: 10px;
                    }}
                    QFrame:hover {{
                        background-color: {c['card_hover']};
                        border-color: {c['card_selected_border']};
                    }}
                """)

        self.btn_group.setExclusive(True)

        # Update active section pill highlight
        for s_name, btn in self.section_buttons.items():
            if s_name == sub:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {c['pill_active_bg']};
                        color: {c['pill_active_text']};
                        border-radius: 14px;
                        padding: 4px 12px;
                        font-size: 12px;
                        font-weight: 600;
                        border: 1px solid {c['pill_active_bg']};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {c['pill_bg']};
                        color: {c['pill_text']};
                        border-radius: 14px;
                        padding: 4px 12px;
                        font-size: 12px;
                        font-weight: 600;
                        border: 1px solid {c['pill_border']};
                    }}
                    QPushButton:hover {{ background-color: {c['card_hover']}; }}
                """)

        self._refresh_palette_styles()

    def _format_bilingual_text(self, en, hi, fallback_full=""):
        if self.lang_mode == "en":
            return en if en.strip() else fallback_full
        elif self.lang_mode == "hi":
            return hi if hi.strip() else fallback_full
        else: # both
            if en.strip() and hi.strip() and en.strip() != hi.strip():
                return f"{en.strip()}\n\n{hi.strip()}"
            elif en.strip():
                return en.strip()
            elif hi.strip():
                return hi.strip()
            else:
                return fallback_full.strip()

    def set_language_mode(self, mode):
        self.lang_mode = mode
        self.btn_lang_both.setChecked(mode == "both")
        self.btn_lang_en.setChecked(mode == "en")
        self.btn_lang_hi.setChecked(mode == "hi")
        self._display_question(self.current_q_idx)

    def adjust_font_scale(self, delta):
        self.font_scale = max(-3, min(6, self.font_scale + delta))
        self._display_question(self.current_q_idx)

    def set_dark_mode(self, is_dark):
        self.is_dark = is_dark
        c = get_theme_colors(is_dark)
        if hasattr(self, "top_bar_frame"):
            self.top_bar_frame.setStyleSheet(f"""
                QFrame#topBar {{
                    background: {c['topbar_bg']};
                    border: 1px solid {c['topbar_border']};
                    border-radius: 8px;
                    padding: 6px;
                }}
            """)
        if hasattr(self, "question_container"):
            self.question_container.setStyleSheet(f"""
                QFrame#questionArea {{
                    background: {c['card_bg']};
                    border: 1px solid {c['card_border']};
                    border-radius: 8px;
                }}
            """)
        if hasattr(self, "palette_container"):
            self.palette_container.setStyleSheet(f"""
                QFrame#paletteArea {{
                    background: {c['card_bg']};
                    border: 1px solid {c['card_border']};
                    border-radius: 8px;
                }}
            """)
        if hasattr(self, "profile_frame"):
            self.profile_frame.setStyleSheet(f"background: {c['sub_badge_bg']}; border: 1px solid {c['card_border']}; border-radius: 6px; padding: 6px;")
        if hasattr(self, "legend_frame"):
            self.legend_frame.setStyleSheet(f"background: {c['sub_badge_bg']}; border: 1px solid {c['card_border']}; border-radius: 6px; padding: 6px;")
        if hasattr(self, "btn_clear"):
            self.btn_clear.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['card_bg']};
                    color: {c['text_muted']};
                    border: 1.5px solid {c['card_border']};
                    font-weight: 600;
                    font-size: 13px;
                    border-radius: 6px;
                    padding: 10px 14px;
                }}
                QPushButton:hover {{ background-color: {c['card_hover']}; }}
            """)
        if hasattr(self, "btn_view_clip"):
            col = "#60a5fa" if is_dark else "#0d6efd"
            self.btn_view_clip.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['card_bg']};
                    color: {col};
                    border: 1.5px solid {col};
                    font-weight: 600;
                    font-size: 13px;
                    border-radius: 6px;
                    padding: 10px 14px;
                }}
                QPushButton:hover {{ background-color: {c['card_hover']}; }}
            """)
        if hasattr(self, "btn_prev"):
            self.btn_prev.setStyleSheet(f"""
                QPushButton {{
                    background-color: {'#334155' if is_dark else '#6c757d'};
                    color: #ffffff;
                    font-weight: 600;
                    font-size: 13px;
                    border-radius: 6px;
                    padding: 10px 18px;
                }}
                QPushButton:hover {{ background-color: {'#475569' if is_dark else '#5c636a'}; }}
            """)
        if self.questions:
            self._display_question(self.current_q_idx)

    # -------------------------------------------------------------
    # Navigation & Actions
    # -------------------------------------------------------------
    def _on_option_selected(self, button):
        selected_key = None
        c = get_theme_colors(self.is_dark)
        for key, r in self.option_radios.items():
            if r == button or r.isChecked():
                selected_key = key
                self.option_cards[key].setStyleSheet(f"""
                    QFrame {{
                        background-color: {c['card_selected_bg']};
                        border: 2px solid {c['card_selected_border']};
                        border-radius: 8px;
                        padding: 10px;
                    }}
                """)
            else:
                self.option_cards[key].setStyleSheet(f"""
                    QFrame {{
                        background-color: {c['card_bg']};
                        border: 1.5px solid {c['card_border']};
                        border-radius: 8px;
                        padding: 10px;
                    }}
                    QFrame:hover {{
                        background-color: {c['card_hover']};
                        border-color: {c['card_selected_border']};
                    }}
                """)

        if selected_key:
            qno = self.questions[self.current_q_idx]["qno"]
            self.user_answers[qno] = selected_key
            if qno in self.marked_for_review:
                self.question_states[qno] = "marked_answered"
            else:
                self.question_states[qno] = "answered"
            self._refresh_palette_styles()

    def _save_and_next(self):
        qno = self.questions[self.current_q_idx]["qno"]
        if qno in self.user_answers:
            if qno in self.marked_for_review:
                self.question_states[qno] = "marked_answered"
            else:
                self.question_states[qno] = "answered"
        else:
            if qno not in self.marked_for_review:
                self.question_states[qno] = "not_answered"

        if self.current_q_idx < len(self.questions) - 1:
            self._display_question(self.current_q_idx + 1)
        else:
            self._refresh_palette_styles()

    def _mark_for_review_and_next(self):
        qno = self.questions[self.current_q_idx]["qno"]
        self.marked_for_review.add(qno)
        if qno in self.user_answers:
            self.question_states[qno] = "marked_answered"
        else:
            self.question_states[qno] = "marked"

        if self.current_q_idx < len(self.questions) - 1:
            self._display_question(self.current_q_idx + 1)
        else:
            self._refresh_palette_styles()

    def _clear_response(self):
        qno = self.questions[self.current_q_idx]["qno"]
        if qno in self.user_answers:
            del self.user_answers[qno]
        if qno in self.marked_for_review:
            self.question_states[qno] = "marked"
        else:
            self.question_states[qno] = "not_answered"

        c = get_theme_colors(self.is_dark)
        self.btn_group.setExclusive(False)
        for key, r in self.option_radios.items():
            r.setChecked(False)
            self.option_cards[key].setStyleSheet(f"""
                QFrame {{
                    background-color: {c['card_bg']};
                    border: 1.5px solid {c['card_border']};
                    border-radius: 8px;
                    padding: 10px;
                }}
                QFrame:hover {{
                    background-color: {c['card_hover']};
                    border-color: {c['card_selected_border']};
                }}
            """)
        self.btn_group.setExclusive(True)
        self._refresh_palette_styles()

    def _prev_question(self):
        if self.current_q_idx > 0:
            self._display_question(self.current_q_idx - 1)

    def _jump_to_question(self, idx):
        if 0 <= idx < len(self.questions):
            self._display_question(idx)

    def _toggle_current_bookmark(self):
        qno = self.questions[self.current_q_idx]["qno"]
        sub = self.questions[self.current_q_idx].get("subject", "")
        sh_id = self.current_shift_info.get("shift_index", 1)
        new_state = self.db.toggle_bookmark(sh_id, qno, sub)
        self.btn_bookmark.setChecked(new_state)
        self.btn_bookmark.setText("★ Bookmarked" if new_state else "☆ Bookmark")

    def _view_original_clip(self):
        q = self.questions[self.current_q_idx]
        sh_id = self.current_shift_info.get("shift_index", 1)
        qno = q["qno"]
        page_num = q.get("page_num", 0)

        clip_path = self.extractor.render_question_clip(sh_id, qno, page_num)
        if clip_path and os.path.exists(clip_path):
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Original PDF Clip - Question {qno}")
            dialog.resize(750, 500)
            d_layout = QVBoxLayout(dialog)
            
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setPixmap(QPixmap(clip_path))
            scroll.setWidget(lbl)
            
            d_layout.addWidget(scroll)
            btn_close = QPushButton("Close")
            btn_close.clicked.connect(dialog.accept)
            d_layout.addWidget(btn_close, 0, Qt.AlignmentFlag.AlignRight)
            dialog.exec()
        else:
            QMessageBox.information(self, "Clip Notice", "Original PDF page clip is not available for this question.")

    # -------------------------------------------------------------
    # Palette Updates & Legend Counts
    # -------------------------------------------------------------
    def _refresh_palette_styles(self):
        answered = 0
        not_answered = 0
        marked = 0
        not_visited = 0

        current_qno = self.questions[self.current_q_idx]["qno"] if self.questions else -1

        for q in self.questions:
            qno = q["qno"]
            state = self.question_states.get(qno, "not_visited")
            btn = self.palette_buttons.get(qno)
            if not btn:
                continue

            # Base style according to state
            if state == "answered":
                answered += 1
                bg_color = "#198754"
                text_color = "#ffffff"
                border_radius = "5px"
                border = "none"
            elif state == "not_answered":
                not_answered += 1
                bg_color = "#dc3545"
                text_color = "#ffffff"
                border_radius = "5px"
                border = "none"
            elif state == "marked":
                marked += 1
                bg_color = "#6f42c1"
                text_color = "#ffffff"
                border_radius = "16px"
                border = "none"
            elif state == "marked_answered":
                answered += 1
                marked += 1
                bg_color = "#6f42c1"
                text_color = "#ffffff"
                border_radius = "16px"
                border = "2px solid #198754"
            else: # not_visited
                not_visited += 1
                c = get_theme_colors(self.is_dark)
                bg_color = c['palette_unvisited_bg']
                text_color = c['palette_unvisited_text']
                border_radius = "5px"
                border = f"1px solid {c['palette_unvisited_border']}"

            # Highlight current question
            if qno == current_qno:
                border = "3px solid #0d6efd"

            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: {text_color};
                    border-radius: {border_radius};
                    border: {border};
                    font-weight: bold;
                }}
            """)

        self.lbl_cnt_answered.setText(str(answered))
        self.lbl_cnt_not_answered.setText(str(not_answered))
        self.lbl_cnt_marked.setText(str(marked))
        self.lbl_cnt_not_visited.setText(str(not_visited))

    # -------------------------------------------------------------
    # Timer
    # -------------------------------------------------------------
    def _on_timer_tick(self):
        if self.time_left_secs > 0:
            self.time_left_secs -= 1
            self._update_timer_display()
        else:
            self.timer.stop()
            QMessageBox.warning(self, "Time Expired", "Time limit reached! Submitting your test automatically.")
            self._submit_test()

    def _update_timer_display(self):
        hrs = self.time_left_secs // 3600
        mins = (self.time_left_secs % 3600) // 60
        secs = self.time_left_secs % 60
        self.lbl_timer.setText(f"Time Left: {hrs:02d}:{mins:02d}:{secs:02d}")

        if self.time_left_secs <= 15 * 60: # 15 minutes left
            self.lbl_timer.setStyleSheet("""
                background-color: #f8d7da;
                color: #dc3545;
                border: 1.5px solid #dc3545;
                border-radius: 6px;
                padding: 4px 12px;
            """)
        else:
            self.lbl_timer.setStyleSheet("""
                background-color: #e7f1ff;
                color: #0d6efd;
                border: 1.5px solid #0d6efd;
                border-radius: 6px;
                padding: 4px 12px;
            """)

    # -------------------------------------------------------------
    # Submission
    # -------------------------------------------------------------
    def _confirm_and_submit_test(self):
        answered = len(self.user_answers)
        total = len(self.questions)
        unanswered = total - answered
        marked = len(self.marked_for_review)

        msg = (
            f"Are you sure you want to submit the test?\n\n"
            f"• Total Questions: {total}\n"
            f"• Questions Answered: {answered}\n"
            f"• Questions Not Answered: {unanswered}\n"
            f"• Marked for Review: {marked}\n\n"
            f"Time Remaining: {self.lbl_timer.text().replace('Time Left: ', '')}"
        )
        reply = QMessageBox.question(
            self, "Submit Confirmation", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.timer.stop()
            self._submit_test()

    def _submit_test(self):
        self.timer.stop()
        time_spent = self.time_total_secs - self.time_left_secs

        # Calculate scores
        correct_count = 0
        incorrect_count = 0
        unattempted_count = 0
        section_stats = {}

        for q in self.questions:
            qno = q["qno"]
            sub = q.get("subject", "General")
            c_ans = q.get("correct_ans", "").strip()
            u_ans = self.user_answers.get(qno)

            if sub not in section_stats:
                section_stats[sub] = {"total": 0, "attempted": 0, "correct": 0, "wrong": 0, "score": 0.0}
            section_stats[sub]["total"] += 1

            if u_ans:
                section_stats[sub]["attempted"] += 1
                if u_ans == c_ans:
                    correct_count += 1
                    section_stats[sub]["correct"] += 1
                    section_stats[sub]["score"] += 1.0
                else:
                    incorrect_count += 1
                    section_stats[sub]["wrong"] += 1
            else:
                unattempted_count += 1

        total_score = float(correct_count)
        max_score = float(len(self.questions))

        attempt_data = {
            "shift_id": self.current_shift_info.get("shift_index", 1),
            "title": self.current_shift_info.get("name", "Mock Test"),
            "mode": "Exam",
            "score": total_score,
            "max_score": max_score,
            "total_questions": len(self.questions),
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "unattempted_count": unattempted_count,
            "marked_count": len(self.marked_for_review),
            "time_spent_secs": time_spent,
            "answers": self.user_answers,
            "section_scores": section_stats,
            "questions": self.questions
        }

        # Save to SQLite
        attempt_id = self.db.save_test_attempt(attempt_data)
        attempt_data["attempt_id"] = attempt_id

        # Emit signal to switch to results view
        self.test_submitted.emit(attempt_data)
