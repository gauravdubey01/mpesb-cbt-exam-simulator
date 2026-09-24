import sqlite3
import json
import os
from datetime import datetime

class ExamDB:
    def __init__(self, db_path="exam_data.db"):
        self.db_path = os.path.abspath(db_path)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shift_index INTEGER UNIQUE,
                name TEXT,
                date TEXT,
                slot TEXT,
                start_page INTEGER,
                end_page INTEGER,
                page_count INTEGER,
                question_count INTEGER DEFAULT 200
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shift_id INTEGER,
                qno INTEGER,
                qid TEXT,
                subject TEXT,
                question_en TEXT,
                question_hi TEXT,
                question_full TEXT,
                opt_a_en TEXT,
                opt_a_hi TEXT,
                opt_a_full TEXT,
                opt_b_en TEXT,
                opt_b_hi TEXT,
                opt_b_full TEXT,
                opt_c_en TEXT,
                opt_c_hi TEXT,
                opt_c_full TEXT,
                opt_d_en TEXT,
                opt_d_hi TEXT,
                opt_d_full TEXT,
                correct_ans TEXT,
                images_json TEXT,
                page_num INTEGER,
                UNIQUE(shift_id, qno)
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS test_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shift_id INTEGER,
                title TEXT,
                mode TEXT,
                started_at TEXT,
                completed_at TEXT,
                score REAL,
                max_score REAL,
                total_questions INTEGER,
                correct_count INTEGER,
                incorrect_count INTEGER,
                unattempted_count INTEGER,
                marked_count INTEGER,
                time_spent_secs INTEGER,
                answers_json TEXT,
                section_scores_json TEXT
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shift_id INTEGER,
                qno INTEGER,
                subject TEXT,
                note TEXT,
                created_at TEXT,
                UNIQUE(shift_id, qno)
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """)

            # Version 2 Schema Migration: Add solution & user note columns if missing
            cur.execute("PRAGMA table_info(questions)")
            cols = [r["name"] for r in cur.fetchall()]
            if "solution_en" not in cols:
                cur.execute("ALTER TABLE questions ADD COLUMN solution_en TEXT")
            if "solution_hi" not in cols:
                cur.execute("ALTER TABLE questions ADD COLUMN solution_hi TEXT")
            if "solution_steps" not in cols:
                cur.execute("ALTER TABLE questions ADD COLUMN solution_steps TEXT")
            if "solution_source" not in cols:
                cur.execute("ALTER TABLE questions ADD COLUMN solution_source TEXT")
            if "user_notes" not in cols:
                cur.execute("ALTER TABLE questions ADD COLUMN user_notes TEXT")

            conn.commit()

    def populate_shifts(self, shifts):
        with self.get_connection() as conn:
            cur = conn.cursor()
            for s in shifts:
                cur.execute("""
                INSERT INTO shifts (shift_index, name, date, slot, start_page, end_page, page_count, question_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(shift_index) DO UPDATE SET
                    name=excluded.name,
                    date=excluded.date,
                    slot=excluded.slot,
                    start_page=excluded.start_page,
                    end_page=excluded.end_page,
                    page_count=excluded.page_count
                """, (
                    s["shift_index"], s.get("name", f"Shift {s['shift_index']}"),
                    s["date"], s["slot"], s["start_page"], s["end_page"],
                    s.get("page_count", 0), s.get("question_count", 200)
                ))
            conn.commit()

    def get_shifts(self):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM shifts ORDER BY shift_index ASC")
            return [dict(r) for r in cur.fetchall()]

    def is_shift_cached(self, shift_index):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM questions WHERE shift_id = ?", (shift_index,))
            count = cur.fetchone()[0]
            return count >= 190  # Complete shift has 200 questions

    def save_shift_questions(self, shift_index, questions):
        with self.get_connection() as conn:
            cur = conn.cursor()
            for q in questions:
                images_json = json.dumps(q.get("images", []))
                cur.execute("""
                INSERT INTO questions (
                    shift_id, qno, qid, subject, question_en, question_hi, question_full,
                    opt_a_en, opt_a_hi, opt_a_full, opt_b_en, opt_b_hi, opt_b_full,
                    opt_c_en, opt_c_hi, opt_c_full, opt_d_en, opt_d_hi, opt_d_full,
                    correct_ans, images_json, page_num
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(shift_id, qno) DO UPDATE SET
                    qid=excluded.qid,
                    subject=excluded.subject,
                    question_en=excluded.question_en,
                    question_hi=excluded.question_hi,
                    question_full=excluded.question_full,
                    opt_a_en=excluded.opt_a_en,
                    opt_a_hi=excluded.opt_a_hi,
                    opt_a_full=excluded.opt_a_full,
                    opt_b_en=excluded.opt_b_en,
                    opt_b_hi=excluded.opt_b_hi,
                    opt_b_full=excluded.opt_b_full,
                    opt_c_en=excluded.opt_c_en,
                    opt_c_hi=excluded.opt_c_hi,
                    opt_c_full=excluded.opt_c_full,
                    opt_d_en=excluded.opt_d_en,
                    opt_d_hi=excluded.opt_d_hi,
                    opt_d_full=excluded.opt_d_full,
                    correct_ans=excluded.correct_ans,
                    images_json=excluded.images_json,
                    page_num=excluded.page_num
                """, (
                    shift_index, q["qno"], q.get("qid", ""), q.get("subject", "General"),
                    q.get("question_en", ""), q.get("question_hi", ""), q.get("question_full", ""),
                    q.get("opt_a_en", ""), q.get("opt_a_hi", ""), q.get("opt_a_full", ""),
                    q.get("opt_b_en", ""), q.get("opt_b_hi", ""), q.get("opt_b_full", ""),
                    q.get("opt_c_en", ""), q.get("opt_c_hi", ""), q.get("opt_c_full", ""),
                    q.get("opt_d_en", ""), q.get("opt_d_hi", ""), q.get("opt_d_full", ""),
                    q.get("correct_ans", "A"), images_json, q.get("page_num", 0)
                ))
            conn.commit()

    def get_shift_questions(self, shift_index):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM questions WHERE shift_id = ? ORDER BY qno ASC", (shift_index,))
            rows = cur.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["images"] = json.loads(d["images_json"]) if d.get("images_json") else []
                results.append(d)
            return results

    get_questions_by_shift = get_shift_questions

    def get_questions_by_subject(self, subject, limit=50):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT * FROM questions 
            WHERE subject LIKE ? 
            ORDER BY RANDOM() LIMIT ?
            """, (f"%{subject}%", limit))
            rows = cur.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["images"] = json.loads(d["images_json"]) if d.get("images_json") else []
                results.append(d)
            return results

    def get_all_subjects(self):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT subject FROM questions WHERE subject != '' ORDER BY subject ASC")
            return [r[0] for r in cur.fetchall()]

    def save_test_attempt(self, attempt_data):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO test_attempts (
                shift_id, title, mode, started_at, completed_at, score, max_score,
                total_questions, correct_count, incorrect_count, unattempted_count,
                marked_count, time_spent_secs, answers_json, section_scores_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                attempt_data.get("shift_id", 0),
                attempt_data.get("title", "Exam Attempt"),
                attempt_data.get("mode", "Exam"),
                attempt_data.get("started_at", datetime.now().isoformat()),
                attempt_data.get("completed_at", datetime.now().isoformat()),
                attempt_data.get("score", 0.0),
                attempt_data.get("max_score", 200.0),
                attempt_data.get("total_questions", 200),
                attempt_data.get("correct_count", 0),
                attempt_data.get("incorrect_count", 0),
                attempt_data.get("unattempted_count", 0),
                attempt_data.get("marked_count", 0),
                attempt_data.get("time_spent_secs", 0),
                json.dumps(attempt_data.get("answers", {})),
                json.dumps(attempt_data.get("section_scores", {}))
            ))
            conn.commit()
            return cur.lastrowid

    def get_test_attempts(self, limit=50):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM test_attempts ORDER BY id DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["answers"] = json.loads(d["answers_json"]) if d.get("answers_json") else {}
                d["section_scores"] = json.loads(d["section_scores_json"]) if d.get("section_scores_json") else {}
                results.append(d)
            return results

    def get_test_attempt_by_id(self, attempt_id):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM test_attempts WHERE id = ?", (attempt_id,))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["answers"] = json.loads(d["answers_json"]) if d.get("answers_json") else {}
            d["section_scores"] = json.loads(d["section_scores_json"]) if d.get("section_scores_json") else {}
            return d

    def toggle_bookmark(self, shift_id, qno, subject=""):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM bookmarks WHERE shift_id = ? AND qno = ?", (shift_id, qno))
            row = cur.fetchone()
            if row:
                cur.execute("DELETE FROM bookmarks WHERE id = ?", (row[0],))
                conn.commit()
                return False  # unbookmarked
            else:
                cur.execute("""
                INSERT INTO bookmarks (shift_id, qno, subject, created_at)
                VALUES (?, ?, ?, ?)
                """, (shift_id, qno, subject, datetime.now().isoformat()))
                conn.commit()
                return True  # bookmarked

    def is_bookmarked(self, shift_id, qno):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM bookmarks WHERE shift_id = ? AND qno = ?", (shift_id, qno))
            return cur.fetchone() is not None

    def get_bookmarks(self):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT b.*, q.question_en, q.question_hi, q.subject as q_subject, q.correct_ans
            FROM bookmarks b
            LEFT JOIN questions q ON b.shift_id = q.shift_id AND b.qno = q.qno
            ORDER BY b.id DESC
            """)
            return [dict(r) for r in cur.fetchall()]

    def get_summary_stats(self):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*), AVG(score), MAX(score), SUM(total_questions) FROM test_attempts")
            row = cur.fetchone()
            cur.execute("SELECT COUNT(*) FROM bookmarks")
            b_count = cur.fetchone()[0]
            return {
                "total_attempts": row[0] or 0,
                "avg_score": round(row[1], 1) if row[1] is not None else 0.0,
                "best_score": round(row[2], 1) if row[2] is not None else 0.0,
                "total_questions_attempted": row[3] or 0,
                "bookmarks_count": b_count
            }

    def get_setting(self, key, default=None):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cur.fetchone()
            return row[0] if row else default

    def set_setting(self, key, value):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, str(value)))
            conn.commit()

    def update_question_solution(self, shift_id, qno, solution_en, solution_hi="", solution_steps=None, solution_source="auto"):
        steps_json = json.dumps(solution_steps) if solution_steps else ""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            UPDATE questions
            SET solution_en = ?, solution_hi = ?, solution_steps = ?, solution_source = ?
            WHERE shift_id = ? AND qno = ?
            """, (solution_en, solution_hi, steps_json, solution_source, shift_id, qno))
            conn.commit()

    def save_user_note(self, shift_id, qno, note):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            UPDATE questions
            SET user_notes = ?
            WHERE shift_id = ? AND qno = ?
            """, (note, shift_id, qno))
            conn.commit()

    def get_question(self, shift_id, qno):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM questions WHERE shift_id = ? AND qno = ?", (shift_id, qno))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["images"] = json.loads(d["images_json"]) if d.get("images_json") else []
            d["solution_steps"] = json.loads(d["solution_steps"]) if d.get("solution_steps") else []
            return d

    def search_questions(self, query, subject=None, limit=50):
        with self.get_connection() as conn:
            cur = conn.cursor()
            q_like = f"%{query}%"
            if subject and subject != "All Subjects":
                cur.execute("""
                SELECT * FROM questions
                WHERE (question_en LIKE ? OR question_hi LIKE ? OR question_full LIKE ?)
                  AND subject LIKE ?
                ORDER BY shift_id ASC, qno ASC LIMIT ?
                """, (q_like, q_like, q_like, f"%{subject}%", limit))
            else:
                cur.execute("""
                SELECT * FROM questions
                WHERE question_en LIKE ? OR question_hi LIKE ? OR question_full LIKE ?
                ORDER BY shift_id ASC, qno ASC LIMIT ?
                """, (q_like, q_like, q_like, limit))
            rows = cur.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["images"] = json.loads(d["images_json"]) if d.get("images_json") else []
                d["solution_steps"] = json.loads(d["solution_steps"]) if d.get("solution_steps") else []
                results.append(d)
            return results
