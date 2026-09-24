# MPESB Patwari CBT Examination Simulator (Windows Software)

A modern, high-performance offline Windows desktop Computer-Based Test (CBT) software built with Python and PyQt6, powered by the official **MPESB Patwari Recruitment Exam Question Bank (`G2SG4_Patwari_2022_QB.pdf`)**.

---

## Key Features

- **70 Full Official Exam Shifts (14,000 Questions)**:
  - Covers all dates and slots (Shift 1 & Shift 2) from March to April 2023.
  - Complete 200 questions per shift with official answer keys.
- **Full Bilingual Support (English & हिन्दी)**:
  - Switch anytime between **Bilingual (Both)**, **English Only**, and **हिन्दी Only** with a single click.
  - Crisp Devanagari Hindi font rendering (`Nirmala UI` / `Mangal`).
- **Authentic CBT Exam Interface (TCS iON / MPESB style)**:
  - **Live Countdown Timer**: 3-hour timer with alert styling under 15 minutes and auto-submission.
  - **200-Question Color Palette**:
    - 🟢 **Green**: Answered
    - 🔴 **Red**: Not Answered
    - ⚪ **Silver**: Not Visited
    - 🟣 **Purple**: Marked for Review
    - 🟣+🟢 **Purple + Green border**: Answered & Marked for Review
  - **Section / Subject Navigation**: Jump directly to General Knowledge, English, Hindi, Mathematics, Reasoning, Science, Management, or Computer Knowledge.
  - **Action Toolbar**: *Save & Next*, *Mark for Review & Next*, *Clear Response*, *Previous*.
  - **Keyboard Shortcuts**: Keys `1`/`2`/`3`/`4` or `A`/`B`/`C`/`D` to pick options, `Left`/`Right` arrow keys to navigate questions.
- **Diagrams & Visual Support**:
  - Automatically extracts and displays question diagrams, geometry figures, and reasoning series.
  - **"View Original PDF Clip"** button lets you inspect the exact official PDF snippet for any question.
- **Practice & Study Mode**:
  - Untimed, stress-free mode with instant answer reveal and explanation upon selecting an option.
  - Filter questions within any test by subject.
- **Subject-Wise Practice**:
  - Pick any subject (e.g. 25, 50, or 100 questions of GK, Maths, Reasoning, Computer Knowledge) drawn across papers.
- **In-Depth Performance Analytics & Scorecard**:
  - Overall score, max marks, percentage, accuracy %, and time spent.
  - Section-by-section breakdown (Total, Attempted, Correct, Incorrect, Score, Accuracy %).
  - Full Question-by-Question review with filters for **Incorrect (Mistakes)**, **Correct**, and **Unattempted**.
- **Dark Mode & Eye Comfort Themes**:
  - Full toggleable **Dark Mode** (`🌙 Dark Mode` / `☀️ Light Mode`) with persistent setting saved to SQLite.
  - Custom color coding for low-glare nighttime study sessions.
- **Bookmarks & Revision**:
  - Star difficult questions during exams or practice to review them anytime from the dashboard.

---

## How to Run

### Method 1: Double-Click the Windows Application Shortcut
Double-click:
```
ExamSimulator.lnk
```
or run directly from:
```
dist\ExamSimulator\ExamSimulator.exe
```

### Method 2: Double-Click the EXE Launcher
Double-click:
```cmd
Launch_ExamSimulator_EXE.bat
```

### Method 3: Run via Python
Double-click:
```cmd
Start_Exam_Software.bat
```
or open PowerShell in this directory:
```powershell
python main.py
```

---

## System Requirements
- Windows 10 / 11
- Python 3.10+ (tested with Python 3.12)
- Dependencies: `PyQt6`, `pymupdf` (both already installed in the environment)
