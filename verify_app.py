import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
import sys
from PyQt6.QtWidgets import QApplication
from core.extractor import PDFExtractor
from core.db import ExamDB
from gui.main_window import MainWindow

def run_tests():
    app = QApplication(sys.argv)
    db = ExamDB()
    extractor = PDFExtractor()
    shifts = db.get_shifts()
    print(f"1. Database has {len(shifts)} shifts populated.")
    assert len(shifts) == 70, f"Expected 70 shifts, got {len(shifts)}"

    window = MainWindow(db, extractor)
    print("2. MainWindow instantiated successfully.")

    # Test loading shift 1
    s1 = shifts[0]
    window._launch_cbt_exam(s1)
    print(f"3. CBT Exam launched for: {s1.get('name')}")
    assert len(window.cbt_exam.questions) == 200, f"Expected 200 questions, got {len(window.cbt_exam.questions)}"

    q1_text = window.cbt_exam.lbl_question_text.text()
    print("4. Q1 Text preview:", repr(q1_text[:60]))
    assert len(q1_text) > 10, "Question 1 text should not be empty"

    # Test language toggle
    window.cbt_exam.set_language_mode("en")
    print("5. English language mode switched successfully.")
    window.cbt_exam.set_language_mode("hi")
    print("6. Hindi language mode switched successfully.")
    window.cbt_exam.set_language_mode("both")
    print("7. Bilingual mode restored.")

    # Test option selection (B is correct for Q1)
    window.cbt_exam._select_option_by_key("B")
    assert window.cbt_exam.user_answers.get(1) == "B", "User answer for Q1 should be B"
    print("8. Option selection verified (selected B).")

    # Test Save & Next
    window.cbt_exam._save_and_next()
    assert window.cbt_exam.current_q_idx == 1, "Should advance to question index 1"
    print("9. Save & Next navigation verified.")

    # Test Practice mode
    window._launch_practice(s1)
    assert len(window.practice.filtered_questions) == 200
    print("10. Practice mode launched successfully with 200 questions.")

    # Test practice option click and SolutionEngine integration
    window.practice._on_practice_option_click("B")
    assert not window.practice.feedback_card.isHidden(), "Feedback card should be visible"
    sol_html = window.practice.lbl_solution_text.text()
    assert len(sol_html) > 20, "Detailed solution text should be populated"
    print("11. Practice instant answer feedback & Detailed Solution verified.")

    # Test personal study note saving & loading
    test_note = "Trick: Remember formula X = Y + Z"
    db.save_user_note(1, 1, test_note)
    q1_db = db.get_question(1, 1)
    assert q1_db.get("user_notes") == test_note, "Personal study note should be saved and loaded"
    print("12. Question personal study note save/retrieve verified.")

    # Test CBT Exam submission
    window.cbt_exam._submit_test()
    assert window.result.card_score.val_label.text().startswith("1.0"), "Score should be 1.0"
    print("13. Exam submission & Scorecard generation verified: Score =", window.result.card_score.val_label.text())

    # Test Result Review Mode solution inspection
    assert len(window.result.lbl_rev_solution.text()) > 20, "Result review solution should be populated"
    print("14. Result Review solution inspection verified.")

    # Test Subject Practice with > 25 questions (e.g. 50 questions)
    window._launch_subject_practice("Gen. English Graduate", 50)
    assert len(window.practice.questions) == 50, f"Expected 50 questions, got {len(window.practice.questions)}"
    print("15. Subject Practice mode successfully loaded 50 questions (> 25 Qs verified!).")

    # Test Question Bank keyword search
    search_res = db.search_questions("ratio", limit=10)
    assert len(search_res) > 0, "Keyword search should return matching questions"
    print(f"16. Question Bank search verified (Found {len(search_res)} questions for 'ratio').")

    # Test PDF Exporter
    from core.pdf_exporter import PDFExporter
    pdf_exp = PDFExporter(db)
    test_pdf_path = os.path.join(os.path.dirname(__file__), "test_solutions_output.pdf")
    pdf_exp.export_test_with_solutions("Test Mock Verification", search_res[:5], test_pdf_path)
    assert os.path.exists(test_pdf_path) and os.path.getsize(test_pdf_path) > 1000, "PDF should be generated and non-empty"
    print(f"17. Printable PDF export with detailed solutions verified ({os.path.getsize(test_pdf_path)} bytes).")
    try:
        os.remove(test_pdf_path)
    except Exception:
        pass

    # Test Dark Mode toggle
    initial_theme = window.is_dark
    window._toggle_theme()
    assert window.is_dark != initial_theme
    assert db.get_setting("theme") == ("dark" if window.is_dark else "light")
    print("18. Toggled theme and verified database persistence.")

    window._toggle_theme()
    assert window.is_dark == initial_theme
    assert db.get_setting("theme") == ("dark" if initial_theme else "light")
    print("19. Toggled theme back and verified state restored.")

    # Test returning to dashboard
    window._go_to_dashboard()
    print("20. Returned to dashboard successfully.")

    print("\n[PASS] ALL 20 TEST CASES PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
