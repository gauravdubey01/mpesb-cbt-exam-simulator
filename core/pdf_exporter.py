"""
PDF Exporter for MPESB Patwari CBT Exam Simulator.
Generates printable question papers and solution sheets using PyMuPDF.
"""

import os
import pymupdf

class PDFExporter:
    def __init__(self, db, solution_engine=None):
        self.db = db
        self.solution_engine = solution_engine

    def export_test_with_solutions(self, title, questions, output_path):
        """
        Creates a PDF with questions and their detailed step-by-step solutions.
        """
        doc = pymupdf.open()
        
        # Color palette
        c_blue = (0.05, 0.43, 0.99)
        c_dark = (0.1, 0.1, 0.1)
        c_gray = (0.4, 0.4, 0.4)
        c_green = (0.09, 0.53, 0.33)

        # Page setup
        margin = 36
        page_w, page_h = pymupdf.paper_size("a4")

        page = doc.new_page(width=page_w, height=page_h)
        y = margin

        # Header
        page.insert_text((margin, y), "MPESB Patwari CBT Examination Simulator", fontsize=16, color=c_blue)
        y += 20
        page.insert_text((margin, y), f"Paper: {title}  |  Total Questions: {len(questions)}", fontsize=11, color=c_dark)
        y += 15
        page.draw_line(pymupdf.Point(margin, y), pymupdf.Point(page_w - margin, y), color=c_gray, width=0.8)
        y += 18

        for idx, q in enumerate(questions):
            qno = q.get("qno", idx + 1)
            sub = q.get("subject", "General")
            q_en = q.get("question_en", "") or q.get("question_full", "")
            corr = q.get("correct_ans", "A")

            # Check page overflow
            if y > page_h - 100:
                page = doc.new_page(width=page_w, height=page_h)
                y = margin

            # Question Title & Subject
            q_header = f"Q.{idx + 1} (Paper Q.{qno})  [{sub}]"
            page.insert_text((margin, y), q_header, fontsize=10, color=c_blue)
            y += 14

            # Question Text
            clean_q = " ".join(q_en.split())
            if len(clean_q) > 160:
                clean_q = clean_q[:160] + "..."
            page.insert_text((margin + 10, y), clean_q, fontsize=9.5, color=c_dark)
            y += 14

            # Options
            opt_str = (
                f"A: {q.get('opt_a_en') or q.get('opt_a_hi') or ''}    "
                f"B: {q.get('opt_b_en') or q.get('opt_b_hi') or ''}    "
                f"C: {q.get('opt_c_en') or q.get('opt_c_hi') or ''}    "
                f"D: {q.get('opt_d_en') or q.get('opt_d_hi') or ''}"
            )
            clean_opt = " ".join(opt_str.split())[:180]
            page.insert_text((margin + 10, y), clean_opt, fontsize=8.5, color=c_gray)
            y += 13

            # Correct Answer & Brief Solution
            page.insert_text((margin + 10, y), f"Correct Answer: Option ({corr})", fontsize=9, color=c_green)
            y += 13

            # If solution engine is available, get explanation snippet
            if self.solution_engine:
                sol = self.solution_engine.get_solution(q)
                sol_raw = sol.get("solution_en", "").replace("<br>", " ").replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
                sol_snippet = " ".join(sol_raw.split())[:170]
                if sol_snippet:
                    page.insert_text((margin + 10, y), f"Solution: {sol_snippet}", fontsize=8.5, color=c_dark)
                    y += 14

            y += 10

        # Create output directory if not present
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc.save(output_path)
        doc.close()
        return output_path
