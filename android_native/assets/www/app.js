/* ==============================================================
   MPESB Patwari CBT Examination Simulator - Mobile Application JS
   ============================================================== */

// State
let allShifts = [];
let currentQuestions = [];
let currentQIdx = 0;
let userAnswers = {}; // qno -> "A"|"B"|"C"|"D"
let questionStates = {}; // qno -> "NOT_VISITED" | "NOT_ANSWERED" | "ANSWERED" | "MARKED" | "MARKED_ANSWERED"
let examMode = "EXAM"; // "EXAM" or "PRACTICE"
let currentShiftInfo = null;
let timerInterval = null;
let timerSeconds = 180 * 60; // 3 hours
let currentLangMode = "both"; // "both", "en", "hi"
let currentSubjectCount = 25;
let currentAttemptData = null;
let reviewFilter = "all";
let modalTargetQuestion = null;

// Initialize when DOM loaded
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  loadDashboardData();
  setupAndroidBridgeFallback();
});

// Mock/Fallback bridge for testing in desktop browser
function setupAndroidBridgeFallback() {
  if (typeof window.Android === "undefined") {
    console.warn("Android interface not detected. Using mock fallback for browser testing.");
    window.Android = {
      getShifts: () => JSON.stringify(Array.from({length: 70}, (_, i) => ({
        shift_index: i + 1,
        name: `Test #${String(i+1).padStart(2,'0')} - ${['01 Apr', '02 Apr', '03 Apr', '04 Apr'][i % 4]} 2023`,
        date: `${['01-04-2023', '02-04-2023', '03-04-2023'][i % 3]}`,
        slot: i % 2 === 0 ? "9:00 AM - 12:00 PM" : "2:30 PM - 5:30 PM",
        question_count: 200
      }))),
      getShiftQuestions: (id) => JSON.stringify(Array.from({length: 200}, (_, i) => ({
        shift_id: id,
        qno: i + 1,
        subject: ["General Knowledge", "General English", "General Hindi", "General Mathematics", "General Reasoning", "General Science", "General Management", "Computer Proficiency"][Math.floor(i / 25)],
        question_en: `Sample Question #${i + 1} in English for Test ${id}`,
        question_hi: `परीक्षण ${id} के लिए नमूना प्रश्न #${i + 1} हिन्दी में`,
        opt_a_en: "Option A text", opt_b_en: "Option B text", opt_c_en: "Option C text", opt_d_en: "Option D text",
        opt_a_hi: "विकल्प A", opt_b_hi: "विकल्प B", opt_c_hi: "विकल्प C", opt_d_hi: "विकल्प D",
        correct_ans: ["A", "B", "C", "D"][i % 4],
        solution_en: "Step 1: Understand the core formula.\nStep 2: Substitute given values.\nStep 3: Verification proves Option is correct.",
        solution_hi: "चरण 1: मुख्य सूत्र को समझें।\nचरण 2: दिए गए मानों को रखें।\nचरण 3: सत्यापन सही विकल्प सिद्ध करता है।"
      }))),
      getQuestionsBySubject: (sub, limit) => window.Android.getShiftQuestions(1),
      getShiftSubjectQuestions: (shiftId, subject) => {
        const all = JSON.parse(window.Android.getShiftQuestions(shiftId));
        return JSON.stringify(all.filter(q => q.subject && q.subject.toLowerCase().includes(subject.toLowerCase().replace(/%/g, ''))).slice(0, 25));
      },
      getSubjectSets: (subject) => {
        return JSON.stringify(Array.from({length: 70}, (_, i) => ({
          shift_id: i + 1,
          name: `Mock Paper #${String(i+1).padStart(2, '0')}`,
          date: `${['15-03-2023', '16-03-2023', '17-03-2023', '18-03-2023'][i % 4]}`,
          slot: i % 2 === 0 ? "9:00 AM - 12:00 PM" : "2:30 PM - 5:30 PM",
          question_count: 25
        })));
      },
      searchQuestions: () => "[]",
      toggleBookmark: () => true,
      isBookmarked: () => false,
      getBookmarks: () => "[]",
      saveUserNote: () => true,
      saveTestAttempt: () => 1,
      getTestAttempts: () => "[]",
      getTestAttempt: (id) => JSON.stringify({
        id: id,
        title: "Test #01",
        shift_id: 1,
        mode: "EXAM",
        score: 150.0,
        max_score: 200.0,
        total_questions: 200,
        correct_count: 150,
        incorrect_count: 30,
        unattempted_count: 20,
        marked_count: 5,
        time_spent_secs: 7200,
        answers_json: "{}",
        section_scores_json: "{}"
      }),
      getSummaryStats: () => JSON.stringify({total_attempts: 0, avg_score: 0.0, best_score: 0.0, bookmarks_count: 0}),
      saveSetting: () => {},
      getSetting: (k, d) => d,
      showToast: (msg) => console.log("Toast: " + msg)
    };
  }
}

// -------------------------------------------------------------
// Theme & Navigation
// -------------------------------------------------------------
function initTheme() {
  const saved = (window.Android && window.Android.getSetting) ? window.Android.getSetting("theme", "light") : "light";
  setTheme(saved);
}

function toggleTheme() {
  const isDark = document.body.classList.contains("theme-dark");
  const next = isDark ? "light" : "dark";
  setTheme(next);
  if (window.Android && window.Android.saveSetting) {
    window.Android.saveSetting("theme", next);
  }
}

function setTheme(theme) {
  if (theme === "dark") {
    document.body.classList.remove("theme-light");
    document.body.classList.add("theme-dark");
    document.getElementById("theme-icon").textContent = "☀️";
  } else {
    document.body.classList.remove("theme-dark");
    document.body.classList.add("theme-light");
    document.getElementById("theme-icon").textContent = "🌙";
  }
}

function showView(viewId) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  const target = document.getElementById(viewId);
  if (target) target.classList.add("active");

  const btnBack = document.getElementById("btn-back");
  const btnLang = document.getElementById("btn-lang-toggle");
  const btnPal = document.getElementById("btn-palette");

  if (viewId === "view-dashboard") {
    btnBack.classList.add("hidden");
    btnLang.classList.add("hidden");
    btnPal.classList.add("hidden");
    document.getElementById("app-title").textContent = "MPESB CBT Simulator";
    document.getElementById("app-subtitle").textContent = "14,000 Questions • 70 Shifts";
    loadDashboardData();
  } else if (viewId === "view-exam") {
    btnBack.classList.remove("hidden");
    btnLang.classList.remove("hidden");
    btnPal.classList.remove("hidden");
    document.getElementById("app-title").textContent = currentShiftInfo ? currentShiftInfo.name : "Exam";
    document.getElementById("app-subtitle").textContent = examMode === "EXAM" ? "Live CBT Mode" : "Practice Mode";
  } else if (viewId === "view-result") {
    btnBack.classList.remove("hidden");
    btnLang.classList.add("hidden");
    btnPal.classList.add("hidden");
    document.getElementById("app-title").textContent = "Performance Scorecard";
    document.getElementById("app-subtitle").textContent = "Detailed Result Analysis";
  }
}

function navigateBack() {
  const activeView = document.querySelector(".view.active").id;
  if (activeView === "view-exam") {
    if (examMode === "EXAM") {
      if (confirm("Are you sure you want to pause or exit this exam? Unsubmitted progress will be lost.")) {
        clearInterval(timerInterval);
        showView("view-dashboard");
      }
    } else {
      showView("view-dashboard");
    }
  } else if (activeView === "view-result") {
    showView("view-dashboard");
  }
}

window.handleAndroidBack = function() {
  const activeDrawer = document.getElementById("palette-drawer").classList.contains("open");
  if (activeDrawer) {
    togglePalette();
    return true;
  }
  const modalNote = !document.getElementById("modal-note").classList.contains("hidden");
  if (modalNote) {
    closeModal("modal-note");
    return true;
  }
  const modalSol = !document.getElementById("modal-solution").classList.contains("hidden");
  if (modalSol) {
    closeModal("modal-solution");
    return true;
  }
  const activeView = document.querySelector(".view.active").id;
  if (activeView !== "view-dashboard") {
    navigateBack();
    return true;
  }
  return false; // Exit app
};

// -------------------------------------------------------------
// Dashboard & Tabs
// -------------------------------------------------------------
function switchDashTab(tabId, btn) {
  document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".dash-tab-content").forEach(c => c.classList.remove("active"));
  document.querySelectorAll(".hero-action-btn").forEach(b => b.classList.remove("active"));

  const targetTab = document.getElementById(`tab-${tabId}`);
  if (targetTab) targetTab.classList.add("active");

  const tabBtn = btn || document.getElementById(`tab-btn-${tabId}`);
  if (tabBtn) tabBtn.classList.add("active");

  const heroBtn = document.getElementById(`hero-btn-${tabId}`);
  if (heroBtn) heroBtn.classList.add("active");

  if (tabId === "subjects") renderSubjectsTab();
  if (tabId === "history") loadHistoryTab();
  if (tabId === "bookmarks") loadBookmarksTab();
}

function loadDashboardData() {
  try {
    const statsStr = window.Android.getSummaryStats();
    const stats = JSON.parse(statsStr || "{}");
    document.getElementById("stat-attempts").textContent = stats.total_attempts || 0;
    document.getElementById("stat-avg").textContent = (stats.avg_score || 0).toFixed(1);
    document.getElementById("stat-best").textContent = (stats.best_score || 0).toFixed(1);
    document.getElementById("stat-bookmarks").textContent = stats.bookmarks_count || 0;

    const shiftsStr = window.Android.getShifts();
    allShifts = JSON.parse(shiftsStr || "[]");
    renderShiftsList(allShifts);

    renderSubjectsTab();
  } catch (e) {
    console.error("loadDashboardData error", e);
  }
}

function renderShiftsList(shifts) {
  const container = document.getElementById("shifts-list");
  if (!shifts || shifts.length === 0) {
    container.innerHTML = `<div class="hint-text text-center py-20">No matching shifts found.</div>`;
    return;
  }

  container.innerHTML = shifts.map(s => `
    <div class="item-card">
      <div class="item-card-header">
        <span class="item-title">${escapeHtml(s.name)}</span>
        <span class="badge-subject">200 Qs</span>
      </div>
      <div class="item-meta">
        📅 ${escapeHtml(s.date || '')} &bull; ⏰ ${escapeHtml(s.slot || '')}
      </div>
      <div class="item-actions">
        <button class="btn btn-success btn-block" onclick="startExam(${s.shift_index}, 'EXAM')">▶ Full CBT Exam</button>
        <button class="btn btn-outline btn-block" onclick="startExam(${s.shift_index}, 'PRACTICE')">📖 Practice</button>
        <button class="btn btn-outline btn-xs" onclick="toggleShiftSubjectChips(${s.shift_index})">🎯 Subject Sets ▾</button>
      </div>
      <div id="shift-sub-chips-${s.shift_index}" class="card-sub-expand hidden">
        ${SUBJECT_CONFIG.map(sub => `
          <div class="sub-set-chip" onclick="startSubjectSetPractice('${sub.key}', ${s.shift_index}, 'PRACTICE')">
            <span class="chip-name">${sub.name}</span>
            <span class="chip-cnt">${sub.qPerSet} Qs ➔</span>
          </div>
        `).join("")}
      </div>
    </div>
  `).join("");
}

function toggleShiftSubjectChips(shiftId) {
  const el = document.getElementById(`shift-sub-chips-${shiftId}`);
  if (el) el.classList.toggle("hidden");
}

function filterShifts() {
  const query = document.getElementById("shift-search").value.trim().toLowerCase();
  const slot = document.getElementById("shift-slot-filter").value;

  const filtered = allShifts.filter(s => {
    const matchQuery = !query || (s.name && s.name.toLowerCase().includes(query)) || (s.date && s.date.includes(query));
    const matchSlot = slot === "ALL" || (s.slot && s.slot.includes(slot));
    return matchQuery && matchSlot;
  });

  renderShiftsList(filtered);
}

// -------------------------------------------------------------
// Subject Practice Sets Engine
// -------------------------------------------------------------
const SUBJECT_CONFIG = [
  { key: "Maths", filter: "Maths", name: "📐 General Mathematics", count: "1,750 Qs", totalSets: 70, qPerSet: 25, color: "#dc3545" },
  { key: "Hindi", filter: "Hindi", name: "📖 General Hindi", count: "1,750 Qs", totalSets: 70, qPerSet: 25, color: "#b07d00" },
  { key: "Science", filter: "Science", name: "🔬 General Science", count: "1,750 Qs", totalSets: 70, qPerSet: 25, color: "#0dcaf0" },
  { key: "English", filter: "English", name: "🔤 General English", count: "1,750 Qs", totalSets: 70, qPerSet: 25, color: "#198754" },
  { key: "Reasoning", filter: "Reasoning", name: "🧩 General Reasoning", count: "1,400 Qs", totalSets: 70, qPerSet: 20, color: "#6f42c1" },
  { key: "Aptitude", filter: "Aptitude", name: "⚡ General Aptitude", count: "1,400 Qs", totalSets: 70, qPerSet: 20, color: "#fd7e14" },
  { key: "Computer", filter: "Computer", name: "💻 Computer Proficiency", count: "1,400 Qs", totalSets: 70, qPerSet: 20, color: "#d63384" },
  { key: "Management", filter: "Management", name: "💼 General Management", count: "1,400 Qs", totalSets: 70, qPerSet: 20, color: "#6610f2" },
  { key: "Knowledge", filter: "Gen. Knowledge", name: "🏛️ General Knowledge", count: "1,400 Qs", totalSets: 70, qPerSet: 20, color: "#0d6efd" }
];

let activeSubjectKey = "Maths";
let activeSubjectSets = [];

function selectActiveSubject(key) {
  activeSubjectKey = key;
  renderSubjectsTab();
}

function renderSubjectsTab() {
  const navContainer = document.getElementById("subject-nav-scroll");
  if (!navContainer) return;

  navContainer.innerHTML = SUBJECT_CONFIG.map(sub => `
    <button class="subject-nav-pill ${sub.key === activeSubjectKey ? 'active' : ''}" onclick="selectActiveSubject('${sub.key}')">
      ${sub.name}
    </button>
  `).join("");

  loadActiveSubjectSets();
}

function loadActiveSubjectSets() {
  const subObj = SUBJECT_CONFIG.find(s => s.key === activeSubjectKey) || SUBJECT_CONFIG[0];
  document.getElementById("sub-active-title").textContent = `${subObj.name} Practice Sets`;
  document.getElementById("sub-active-desc").textContent = `${subObj.totalSets} Official Practice Sets • ${subObj.count} Questions • Official Exam Papers`;
  document.getElementById("sub-active-badge").textContent = `${subObj.qPerSet} Qs / Set`;

  try {
    let setsStr = "[]";
    if (window.Android && window.Android.getSubjectSets) {
      setsStr = window.Android.getSubjectSets(subObj.filter);
    }
    activeSubjectSets = JSON.parse(setsStr || "[]");
    renderSubjectSetsList(activeSubjectSets);
  } catch (e) {
    console.error("loadActiveSubjectSets error", e);
    renderSubjectSetsList([]);
  }
}

function renderSubjectSetsList(sets) {
  const container = document.getElementById("subject-sets-list");
  if (!container) return;
  const subObj = SUBJECT_CONFIG.find(s => s.key === activeSubjectKey) || SUBJECT_CONFIG[0];

  if (!sets || sets.length === 0) {
    container.innerHTML = `<div class="hint-text text-center py-20">No practice sets found for this subject.</div>`;
    return;
  }

  container.innerHTML = sets.map((s, idx) => `
    <div class="item-card">
      <div class="item-card-header">
        <span class="item-title">📝 ${subObj.name.split(" ")[1]} Set #${String(idx + 1).padStart(2, '0')}</span>
        <span class="badge-subject">${s.question_count || subObj.qPerSet} Questions</span>
      </div>
      <div class="item-meta">
        📄 Paper: <b>${escapeHtml(s.name)}</b> &bull; 📅 ${escapeHtml(s.date || '')} &bull; ⏰ ${escapeHtml(s.slot || '')}
      </div>
      <div class="item-actions">
        <button class="btn btn-outline btn-block" onclick="startSubjectSetPractice('${subObj.key}', ${s.shift_id}, 'PRACTICE')">📖 Practice Set</button>
        <button class="btn btn-success btn-block" onclick="startSubjectSetPractice('${subObj.key}', ${s.shift_id}, 'EXAM')">⏱️ CBT Test</button>
      </div>
    </div>
  `).join("");
}

function filterSubjectSets() {
  const q = (document.getElementById("subject-set-search").value || "").trim().toLowerCase();
  if (!q) {
    renderSubjectSetsList(activeSubjectSets);
    return;
  }
  const filtered = activeSubjectSets.filter((s, idx) => {
    const setName = `set ${idx + 1}`.toLowerCase();
    const paperName = (s.name || "").toLowerCase();
    const date = (s.date || "").toLowerCase();
    const slot = (s.slot || "").toLowerCase();
    return setName.includes(q) || paperName.includes(q) || date.includes(q) || slot.includes(q);
  });
  renderSubjectSetsList(filtered);
}

function setSubjectCount(count, btn) {
  currentSubjectCount = count;
  document.querySelectorAll(".subject-count-selector .pill-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
}

function startSubjectSetPractice(subjectKey, shiftId, mode) {
  const subObj = SUBJECT_CONFIG.find(s => s.key === subjectKey) || SUBJECT_CONFIG[0];
  try {
    let qStr = "";
    if (window.Android && window.Android.getShiftSubjectQuestions) {
      qStr = window.Android.getShiftSubjectQuestions(shiftId, subObj.filter);
    } else {
      qStr = window.Android.getQuestionsBySubject(subObj.filter, subObj.qPerSet);
    }
    currentQuestions = JSON.parse(qStr || "[]");
    if (!currentQuestions || currentQuestions.length === 0) {
      alert(`No questions found for ${subObj.name} in Shift #${shiftId}`);
      return;
    }
    const shift = allShifts.find(s => s.shift_index === shiftId);
    const paperDate = shift ? shift.date : "";
    currentShiftInfo = {
      shift_index: shiftId,
      name: `${subObj.name} Set #${shiftId} (${currentQuestions.length} Qs)${paperDate ? ' - ' + paperDate : ''}`
    };
    examMode = mode;
    initExamSession();
  } catch (e) {
    console.error("startSubjectSetPractice error", e);
    alert("Error starting subject practice: " + e.message);
  }
}

function startActiveSubjectShuffle() {
  const subObj = SUBJECT_CONFIG.find(s => s.key === activeSubjectKey) || SUBJECT_CONFIG[0];
  try {
    const qStr = window.Android.getQuestionsBySubject(subObj.filter, currentSubjectCount);
    currentQuestions = JSON.parse(qStr || "[]");
    if (!currentQuestions || currentQuestions.length === 0) {
      alert("No questions found for " + subObj.name);
      return;
    }
    currentShiftInfo = {
      shift_index: 0,
      name: `${subObj.name} Quick Shuffle (${currentQuestions.length} Qs)`
    };
    examMode = "PRACTICE";
    initExamSession();
  } catch (e) {
    console.error("startActiveSubjectShuffle error", e);
  }
}

// -------------------------------------------------------------
// CBT Exam & Practice Engine
// -------------------------------------------------------------
function startExam(shiftId, mode) {
  try {
    const qStr = window.Android.getShiftQuestions(shiftId);
    currentQuestions = JSON.parse(qStr || "[]");
    if (!currentQuestions || currentQuestions.length === 0) {
      alert("Unable to load shift questions.");
      return;
    }
    const shift = allShifts.find(s => s.shift_index === shiftId);
    currentShiftInfo = shift || { shift_index: shiftId, name: `Shift #${shiftId}` };
    examMode = mode;
    initExamSession();
  } catch (e) {
    console.error("startExam error", e);
  }
}

function initExamSession() {
  currentQIdx = 0;
  userAnswers = {};
  questionStates = {};
  currentQuestions.forEach(q => {
    questionStates[q.qno] = "NOT_VISITED";
  });
  if (currentQuestions.length > 0) {
    questionStates[currentQuestions[0].qno] = "NOT_ANSWERED";
  }

  // Timer & Mode actions
  clearInterval(timerInterval);
  if (examMode === "EXAM") {
    // If set is 25 Qs, give 25 mins. If full 200 Qs, give 180 mins (3 hours)
    timerSeconds = Math.min(180 * 60, Math.max(10 * 60, currentQuestions.length * 60));
    document.getElementById("exam-timer-container").classList.remove("hidden");
    document.getElementById("btn-submit-exam").classList.remove("hidden");
    document.getElementById("btn-reveal-solution").classList.add("hidden");
    startTimer();
  } else {
    document.getElementById("exam-timer-container").classList.add("hidden");
    document.getElementById("btn-submit-exam").classList.add("hidden");
    document.getElementById("btn-reveal-solution").classList.remove("hidden");
  }

  // Populate in-exam subject filter
  const subFilterEl = document.getElementById("exam-subject-filter");
  if (subFilterEl) {
    const subs = Array.from(new Set(currentQuestions.map(q => q.subject || "General")));
    if (subs.length > 1) {
      subFilterEl.innerHTML = `<option value="ALL">All Subjects (${currentQuestions.length} Qs)</option>` +
        subs.map(s => {
          const cnt = currentQuestions.filter(q => q.subject === s).length;
          return `<option value="${escapeHtml(s)}">${escapeHtml(s.replace(" Graduate", ""))} (${cnt})</option>`;
        }).join("");
      subFilterEl.value = "ALL";
      subFilterEl.classList.remove("hidden");
    } else {
      subFilterEl.classList.add("hidden");
    }
  }

  renderQuestion();
  renderPalette();
  showView("view-exam");
}

function filterExamBySubject(sub) {
  if (sub === "ALL") {
    currentQIdx = 0;
  } else {
    const idx = currentQuestions.findIndex(q => q.subject === sub);
    if (idx !== -1) currentQIdx = idx;
  }
  renderQuestion();
  renderPalette();
}

function revealPracticeSolution() {
  if (!currentQuestions || currentQuestions.length === 0) return;
  const q = currentQuestions[currentQIdx];
  const corr = (q.correct_ans || "A").trim();

  const fbCard = document.getElementById("practice-feedback-card");
  fbCard.classList.remove("hidden");

  const chosen = userAnswers[q.qno];
  const fbStatus = document.getElementById("feedback-status");
  if (chosen) {
    if (chosen === corr) {
      fbStatus.textContent = "✅ Correct Answer! (+1.00 Marks)";
      fbStatus.className = "feedback-status text-green";
    } else {
      fbStatus.textContent = `❌ Incorrect (You selected Option ${chosen})`;
      fbStatus.className = "feedback-status text-danger";
    }
  } else {
    fbStatus.textContent = `💡 Official Answer Key: Option (${corr})`;
    fbStatus.className = "feedback-status text-blue";
  }

  document.getElementById("feedback-correct-answer").textContent =
    `Official Answer Key: Option (${corr})  |  Subject: ${q.subject || 'General'}`;

  // Study note banner
  const noteBanner = document.getElementById("feedback-user-note");
  if (q.user_notes && q.user_notes.trim()) {
    noteBanner.innerHTML = `📝 <b>My Study Note:</b> ${escapeHtml(q.user_notes)}`;
    noteBanner.classList.remove("hidden");
  } else {
    noteBanner.classList.add("hidden");
  }

  // Solution
  const sol = getOrGenerateSolution(q);
  const solEn = sol.solution_en || "";
  const solHi = sol.solution_hi || "";
  let solText = "";
  if (currentLangMode === "en") solText = solEn || solHi;
  else if (currentLangMode === "hi") solText = solHi || solEn;
  else solText = (solEn && solHi && solEn !== solHi) ? `${solEn}\n\n───────────────\n${solHi}` : (solEn || solHi);

  document.getElementById("feedback-solution-text").textContent = solText;

  // Highlight correct option
  document.querySelectorAll(".option-item").forEach(item => {
    const badge = item.querySelector(".opt-badge");
    if (badge && badge.textContent.trim() === corr) {
      item.classList.add("correct");
    }
  });

  fbCard.scrollIntoView({ behavior: 'smooth' });
}

function startTimer() {
  updateTimerDisplay();
  timerInterval = setInterval(() => {
    timerSeconds--;
    if (timerSeconds <= 0) {
      clearInterval(timerInterval);
      alert("Time is up! Submitting exam automatically.");
      submitExam();
    } else {
      updateTimerDisplay();
    }
  }, 1000);
}

function updateTimerDisplay() {
  const hrs = Math.floor(timerSeconds / 3600);
  const mins = Math.floor((timerSeconds % 3600) / 60);
  const secs = timerSeconds % 60;
  document.getElementById("exam-timer-text").textContent =
    `${String(hrs).padStart(2,'0')}:${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}`;
}

function toggleLanguageMode() {
  if (currentLangMode === "both") currentLangMode = "en";
  else if (currentLangMode === "en") currentLangMode = "hi";
  else currentLangMode = "both";

  const btn = document.getElementById("btn-lang-toggle");
  btn.textContent = currentLangMode === "both" ? "EN/हिन्दी" : (currentLangMode === "en" ? "EN" : "हिन्दी");
  renderQuestion();
}

function renderQuestion() {
  if (!currentQuestions || currentQuestions.length === 0) return;
  const q = currentQuestions[currentQIdx];

  document.getElementById("exam-subject-badge").textContent = q.subject || "General";
  document.getElementById("exam-qno-badge").textContent = `Q. ${currentQIdx + 1} / ${currentQuestions.length}`;
  document.getElementById("q-paper-title").textContent = `Shift #${q.shift_id || currentShiftInfo.shift_index} - Q.${q.qno}`;

  // Bookmark star state
  const isBm = window.Android.isBookmarked(q.shift_id || currentShiftInfo.shift_index, q.qno);
  const btnBm = document.getElementById("btn-bookmark-cur");
  btnBm.className = isBm ? "bookmark-btn active" : "bookmark-btn";
  btnBm.textContent = isBm ? "★" : "☆";

  // Question Text (Bilingual format)
  const qEn = q.question_en || q.question_full || "";
  const qHi = q.question_hi || q.question_full || "";
  let displayText = "";
  if (currentLangMode === "en") displayText = qEn || qHi;
  else if (currentLangMode === "hi") displayText = qHi || qEn;
  else displayText = (qEn && qHi && qEn !== qHi) ? `${qEn}\n\n${qHi}` : (qEn || qHi);

  document.getElementById("q-text").textContent = displayText;

  // Options
  const chosen = userAnswers[q.qno];
  const corr = (q.correct_ans || "").trim();
  const optsContainer = document.getElementById("options-container");
  optsContainer.innerHTML = ["A", "B", "C", "D"].map(k => {
    const kLower = k.toLowerCase();
    const optEn = q[`opt_${kLower}_en`] || q[`opt_${kLower}_full`] || "";
    const optHi = q[`opt_${kLower}_hi`] || q[`opt_${kLower}_full`] || "";
    let optText = "";
    if (currentLangMode === "en") optText = optEn || optHi;
    else if (currentLangMode === "hi") optText = optHi || optEn;
    else optText = (optEn && optHi && optEn !== optHi) ? `${optEn} / ${optHi}` : (optEn || optHi);

    let extraClass = "";
    if (chosen === k) extraClass += " selected";
    if (examMode === "PRACTICE" && chosen) {
      if (k === corr) extraClass += " correct";
      else if (chosen === k && chosen !== corr) extraClass += " wrong";
    }

    return `
      <div class="option-item ${extraClass}" onclick="selectOption('${k}')">
        <span class="opt-badge">${k}</span>
        <span class="opt-text">${escapeHtml(optText)}</span>
      </div>
    `;
  }).join("");

  // Practice Mode Feedback & Solution
  const fbCard = document.getElementById("practice-feedback-card");
  if (examMode === "PRACTICE" && chosen) {
    fbCard.classList.remove("hidden");
    const fbStatus = document.getElementById("feedback-status");
    if (chosen === corr) {
      fbStatus.textContent = "✅ Correct Answer! (+1.00 Marks)";
      fbStatus.className = "feedback-status text-green";
    } else {
      fbStatus.textContent = `❌ Incorrect (You selected Option ${chosen})`;
      fbStatus.className = "feedback-status text-danger";
    }
    document.getElementById("feedback-correct-answer").textContent =
      `Official Answer Key: Option (${corr})  |  Subject: ${q.subject || 'General'}`;

    // Study note banner
    const noteBanner = document.getElementById("feedback-user-note");
    if (q.user_notes && q.user_notes.trim()) {
      noteBanner.innerHTML = `📝 <b>My Study Note:</b> ${escapeHtml(q.user_notes)}`;
      noteBanner.classList.remove("hidden");
    } else {
      noteBanner.classList.add("hidden");
    }

    // Solution
    const sol = getOrGenerateSolution(q);
    const solEn = sol.solution_en || "";
    const solHi = sol.solution_hi || "";
    let solText = "";
    if (currentLangMode === "en") solText = solEn || solHi;
    else if (currentLangMode === "hi") solText = solHi || solEn;
    else solText = (solEn && solHi && solEn !== solHi) ? `${solEn}\n\n───────────────\n${solHi}` : (solEn || solHi);

    document.getElementById("feedback-solution-text").textContent = solText;
  } else {
    fbCard.classList.add("hidden");
  }

  // Prev / Next button states
  document.getElementById("btn-prev").disabled = (currentQIdx === 0);
  document.getElementById("btn-save-next").textContent = (currentQIdx === currentQuestions.length - 1) ? "Save & Finish" : "Save & Next ➔";

  updatePaletteNode(currentQIdx);
}

function selectOption(key) {
  const q = currentQuestions[currentQIdx];
  userAnswers[q.qno] = key;
  if (questionStates[q.qno] === "MARKED") {
    questionStates[q.qno] = "MARKED_ANSWERED";
  } else {
    questionStates[q.qno] = "ANSWERED";
  }
  renderQuestion();
  renderPalette();
}

function clearCurrentResponse() {
  const q = currentQuestions[currentQIdx];
  delete userAnswers[q.qno];
  questionStates[q.qno] = "NOT_ANSWERED";
  renderQuestion();
  renderPalette();
}

function markReviewAndNext() {
  const q = currentQuestions[currentQIdx];
  if (userAnswers[q.qno]) {
    questionStates[q.qno] = "MARKED_ANSWERED";
  } else {
    questionStates[q.qno] = "MARKED";
  }
  advanceNext();
}

function saveAndNext() {
  const q = currentQuestions[currentQIdx];
  if (!userAnswers[q.qno]) {
    questionStates[q.qno] = "NOT_ANSWERED";
  } else if (questionStates[q.qno] !== "MARKED_ANSWERED") {
    questionStates[q.qno] = "ANSWERED";
  }
  advanceNext();
}

function advanceNext() {
  if (currentQIdx < currentQuestions.length - 1) {
    currentQIdx++;
    const nextQ = currentQuestions[currentQIdx];
    if (questionStates[nextQ.qno] === "NOT_VISITED") {
      questionStates[nextQ.qno] = "NOT_ANSWERED";
    }
    renderQuestion();
    renderPalette();
  } else {
    if (examMode === "EXAM") {
      confirmSubmitExam();
    } else {
      alert("You have reached the end of this practice set!");
    }
  }
}

function navPrev() {
  if (currentQIdx > 0) {
    currentQIdx--;
    renderQuestion();
    renderPalette();
  }
}

// Question Palette
function togglePalette() {
  const drawer = document.getElementById("palette-drawer");
  const backdrop = document.getElementById("backdrop");
  drawer.classList.toggle("open");
  backdrop.classList.toggle("hidden");
}

function closeAllDrawers() {
  document.getElementById("palette-drawer").classList.remove("open");
  document.getElementById("backdrop").classList.add("hidden");
}

function renderPalette() {
  const grid = document.getElementById("palette-grid");
  grid.innerHTML = currentQuestions.map((q, idx) => {
    const st = questionStates[q.qno] || "NOT_VISITED";
    let stateClass = "not-visited";
    if (st === "ANSWERED") stateClass = "answered";
    else if (st === "NOT_ANSWERED") stateClass = "not-answered";
    else if (st === "MARKED") stateClass = "marked";
    else if (st === "MARKED_ANSWERED") stateClass = "marked-answered";

    const isCurrent = (idx === currentQIdx) ? "current" : "";

    return `
      <div class="palette-node ${stateClass} ${isCurrent}" onclick="jumpToQuestion(${idx})">
        ${idx + 1}
      </div>
    `;
  }).join("");
}

function updatePaletteNode(idx) {
  document.querySelectorAll(".palette-node").forEach((node, i) => {
    if (i === idx) node.classList.add("current");
    else node.classList.remove("current");
  });
}

function jumpToQuestion(idx) {
  currentQIdx = idx;
  const q = currentQuestions[currentQIdx];
  if (questionStates[q.qno] === "NOT_VISITED") {
    questionStates[q.qno] = "NOT_ANSWERED";
  }
  renderQuestion();
  togglePalette();
}

function toggleCurrentBookmark() {
  const q = currentQuestions[currentQIdx];
  const shId = q.shift_id || currentShiftInfo.shift_index;
  const isNowBm = window.Android.toggleBookmark(shId, q.qno, q.subject || "General");
  const btn = document.getElementById("btn-bookmark-cur");
  btn.className = isNowBm ? "bookmark-btn active" : "bookmark-btn";
  btn.textContent = isNowBm ? "★" : "☆";
  window.Android.showToast(isNowBm ? "Question saved to Bookmarks!" : "Bookmark removed.");
}

// -------------------------------------------------------------
// Exam Submission & Results
// -------------------------------------------------------------
function confirmSubmitExam() {
  let answered = 0;
  let marked = 0;
  let notAnswered = 0;
  currentQuestions.forEach(q => {
    if (userAnswers[q.qno]) answered++;
    const st = questionStates[q.qno];
    if (st === "MARKED" || st === "MARKED_ANSWERED") marked++;
    if (st === "NOT_ANSWERED") notAnswered++;
  });

  const msg = `Submit Examination?\n\n• Answered: ${answered}\n• Not Answered: ${notAnswered}\n• Marked for Review: ${marked}\n• Total: ${currentQuestions.length}\n\nDo you want to submit your test?`;
  if (confirm(msg)) {
    submitExam();
  }
}

function submitExam() {
  clearInterval(timerInterval);

  let corrCount = 0;
  let incorrCount = 0;
  let unattCount = 0;
  const sectionScores = {};

  currentQuestions.forEach(q => {
    const sub = q.subject || "General";
    if (!sectionScores[sub]) {
      sectionScores[sub] = { total: 0, attempted: 0, correct: 0, wrong: 0, score: 0.0 };
    }
    sectionScores[sub].total++;

    const chosen = userAnswers[q.qno];
    const corr = (q.correct_ans || "").trim();

    if (!chosen) {
      unattCount++;
    } else if (chosen === corr) {
      corrCount++;
      sectionScores[sub].attempted++;
      sectionScores[sub].correct++;
      sectionScores[sub].score += 1.0;
    } else {
      incorrCount++;
      sectionScores[sub].attempted++;
      sectionScores[sub].wrong++;
    }
  });

  const timeSpent = (180 * 60) - timerSeconds;
  const totalScore = corrCount * 1.0;
  const maxScore = currentQuestions.length * 1.0;

  const attempt = {
    title: currentShiftInfo ? currentShiftInfo.name : "Exam Attempt",
    shift_id: currentShiftInfo ? currentShiftInfo.shift_index : 1,
    mode: examMode,
    score: totalScore,
    max_score: maxScore,
    total_questions: currentQuestions.length,
    correct_count: corrCount,
    incorrect_count: incorrCount,
    unattempted_count: unattCount,
    marked_count: 0,
    time_spent_secs: timeSpent,
    answers_json: JSON.stringify(userAnswers),
    section_scores_json: JSON.stringify(sectionScores)
  };

  // Save to SQLite
  window.Android.saveTestAttempt(
    attempt.title, attempt.shift_id, attempt.mode, attempt.score, attempt.maxScore || attempt.max_score,
    attempt.total_questions, attempt.correct_count, attempt.incorrect_count, attempt.unattempted_count,
    attempt.marked_count, attempt.time_spent_secs, attempt.answers_json, attempt.section_scores_json
  );

  currentAttemptData = attempt;
  renderResultView(attempt, sectionScores);
  showView("view-result");
}

function renderResultView(attempt, sectionScores) {
  document.getElementById("res-title").textContent = `📊 Scorecard: ${attempt.title}`;
  document.getElementById("res-score").textContent = `${attempt.score.toFixed(1)} / ${attempt.max_score.toFixed(0)}`;

  const attempted = attempt.correct_count + attempt.incorrect_count;
  const acc = attempted > 0 ? ((attempt.correct_count / attempted) * 100).toFixed(1) + "%" : "0.0%";
  document.getElementById("res-accuracy").textContent = acc;
  document.getElementById("res-attempted").textContent = `${attempted} / ${attempt.total_questions}`;

  const hrs = Math.floor(attempt.time_spent_secs / 3600);
  const mins = Math.floor((attempt.time_spent_secs % 3600) / 60);
  const secs = attempt.time_spent_secs % 60;
  document.getElementById("res-time").textContent = `${String(hrs).padStart(2,'0')}:${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}`;

  // Section Table
  let tableHtml = `
    <table>
      <thead>
        <tr>
          <th>Subject</th>
          <th>Total</th>
          <th>Correct</th>
          <th>Score</th>
          <th>Accuracy</th>
        </tr>
      </thead>
      <tbody>
  `;
  for (const [sub, st] of Object.entries(sectionScores)) {
    const sAcc = st.attempted > 0 ? ((st.correct / st.attempted) * 100).toFixed(1) + "%" : "0.0%";
    tableHtml += `
      <tr>
        <td><b>${escapeHtml(sub)}</b></td>
        <td>${st.total}</td>
        <td class="text-green font-bold">${st.correct}</td>
        <td><b>${st.score.toFixed(1)}</b></td>
        <td>${sAcc}</td>
      </tr>
    `;
  }
  tableHtml += `</tbody></table>`;
  document.getElementById("res-sections-table").innerHTML = tableHtml;

  filterReviewQuestions("all");
}

function filterReviewQuestions(filter, btn) {
  reviewFilter = filter;
  if (btn) {
    document.querySelectorAll(".filter-pill-row .pill-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
  }

  const container = document.getElementById("res-questions-list");
  const filtered = currentQuestions.filter(q => {
    const u = userAnswers[q.qno];
    const c = (q.correct_ans || "").trim();
    if (filter === "all") return true;
    if (filter === "correct") return u && u === c;
    if (filter === "wrong") return u && u !== c;
    if (filter === "unattempted") return !u;
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `<div class="hint-text text-center py-20">No questions in this filter.</div>`;
    return;
  }

  container.innerHTML = filtered.map(q => {
    const u = userAnswers[q.qno];
    const c = (q.correct_ans || "").trim();
    let badgeText = "⚪ Skipped";
    let badgeClass = "text-muted";
    if (u) {
      if (u === c) { badgeText = "✅ Correct (+1.00)"; badgeClass = "text-green"; }
      else { badgeText = `❌ Wrong (You: ${u})`; badgeClass = "text-danger"; }
    }

    const preview = (q.question_en || q.question_hi || "").substring(0, 90).replace(/\s+/g, " ");

    return `
      <div class="item-card">
        <div class="item-card-header">
          <span class="item-title">Q.${q.qno} &bull; ${escapeHtml(q.subject || 'General')}</span>
          <span class="${badgeClass} font-bold text-xs">${badgeText}</span>
        </div>
        <div class="item-meta">${escapeHtml(preview)}...</div>
        <div class="item-actions">
          <button class="btn btn-outline btn-xs" onclick='openSolutionModal(${JSON.stringify(q).replace(/'/g, "&apos;")})'>💡 View Detailed Solution</button>
        </div>
      </div>
    `;
  }).join("");
}

// -------------------------------------------------------------
// Solutions Hub & Search
// -------------------------------------------------------------
function searchSolutions() {
  const query = document.getElementById("sol-search-input").value.trim();
  const sub = document.getElementById("sol-subject-filter").value;

  try {
    const resStr = window.Android.searchQuestions(query, sub, 80);
    const results = JSON.parse(resStr || "[]");
    document.getElementById("sol-results-status").textContent = `Found ${results.length} questions in Question Bank.`;

    const container = document.getElementById("sol-results-list");
    if (results.length === 0) {
      container.innerHTML = `<div class="hint-text text-center py-20">No matching questions found. Try another search term.</div>`;
      return;
    }

    container.innerHTML = results.map(q => {
      const prev = (q.question_en || q.question_hi || q.question_full || "").substring(0, 95).replace(/\s+/g, " ");
      return `
        <div class="item-card">
          <div class="item-card-header">
            <span class="item-title">Shift #${q.shift_id} Q.${q.qno} &bull; ${escapeHtml(q.subject || 'General')}</span>
            <span class="badge-marks">Option (${q.correct_ans || 'A'})</span>
          </div>
          <div class="item-meta">${escapeHtml(prev)}...</div>
          <div class="item-actions">
            <button class="btn btn-primary btn-xs" onclick='openSolutionModal(${JSON.stringify(q).replace(/'/g, "&apos;")})'>💡 View Solution & Notes</button>
          </div>
        </div>
      `;
    }).join("");
  } catch (e) {
    console.error("searchSolutions error", e);
  }
}

function openSolutionModal(q) {
  modalTargetQuestion = q;
  document.getElementById("modal-sol-title").textContent = `Shift #${q.shift_id} Q.${q.qno} — ${q.subject || 'General'}`;

  const qEn = q.question_en || q.question_full || "";
  const qHi = q.question_hi || q.question_full || "";
  document.getElementById("modal-sol-qtext").textContent = (qEn && qHi && qEn !== qHi) ? `${qEn}\n\n${qHi}` : (qEn || qHi);

  // Options
  const corr = (q.correct_ans || "A").trim();
  document.getElementById("modal-sol-options").innerHTML = ["A", "B", "C", "D"].map(k => {
    const kLower = k.toLowerCase();
    const optEn = q[`opt_${kLower}_en`] || q[`opt_${kLower}_full`] || "";
    const optHi = q[`opt_${kLower}_hi`] || q[`opt_${kLower}_full`] || "";
    const isCorr = (k === corr);
    return `
      <div class="option-item ${isCorr ? 'correct' : ''}">
        <span class="opt-badge">${k}</span>
        <span class="opt-text">${escapeHtml(optEn)} / ${escapeHtml(optHi)}</span>
        ${isCorr ? '<span class="text-green font-bold text-xs">✔ Answer</span>' : ''}
      </div>
    `;
  }).join("");

  const sol = getOrGenerateSolution(q);
  const solText = `${sol.solution_en}\n\n────────────────\n${sol.solution_hi}`;
  document.getElementById("modal-sol-body").textContent = solText;

  const noteEl = document.getElementById("modal-sol-note");
  noteEl.textContent = (q.user_notes && q.user_notes.trim()) ? q.user_notes : "No personal study note saved yet.";

  openModal("modal-solution");
}

// -------------------------------------------------------------
// Solution Generator Engine (Client Fallback)
// -------------------------------------------------------------
function getOrGenerateSolution(q) {
  if (q.solution_en && q.solution_en.trim()) {
    return { solution_en: q.solution_en, solution_hi: q.solution_hi || q.solution_en };
  }

  const sub = (q.subject || "").toLowerCase();
  const corr = q.correct_ans || "A";
  const corrText = q[`opt_${corr.toLowerCase()}_en`] || q[`opt_${corr.toLowerCase()}_full`] || "";

  if (sub.includes("math") || sub.includes("aptitude")) {
    return {
      solution_en: `Step 1: Identify given parameters from problem statement.\nStep 2: Apply the governing mathematical formula.\nStep 3: Substitute known values and simplify step-by-step.\nStep 4: The calculation yields ${corrText || 'the target value'}. Hence, Option (${corr}) is correct.`,
      solution_hi: `चरण 1: प्रश्न में दिए गए मानों और मापदंडों की पहचान करें।\nचरण 2: उपयुक्त गणितीय सूत्र लागू करें।\nचरण 3: मानों को सूत्र में रखकर गणना को सरल करें।\nचरण 4: गणना से अभीष्ट मान प्राप्त होता है। अतः विकल्प (${corr}) सही उत्तर है।`
    };
  } else if (sub.includes("reasoning")) {
    return {
      solution_en: `Step 1: Analyze the underlying logical pattern or series sequence.\nStep 2: Check step differences and rule consistency across elements.\nStep 3: Deduce the relationship leading directly to Option (${corr}) as the correct answer.`,
      solution_hi: `चरण 1: श्रृंखला या तर्क के अंतर्निहित पैटर्न का विश्लेषण करें।\nचरण 2: तत्वों के बीच संबंधों और नियमों की पुष्टि करें।\nचरण 3: तार्किक विश्लेषण से स्पष्ट है कि विकल्प (${corr}) सही उत्तर है।`
    };
  } else if (sub.includes("english")) {
    return {
      solution_en: `Grammar & Concept Note:\n• Rule: Identify sentence structure, voice/tense agreement, or grammatical context.\n• Explanation: Option (${corr}) correctly adheres to standard English grammar rules.`,
      solution_hi: `व्याकरण एवं संकल्पना नोट:\n• अंग्रेजी व्याकरण के नियमानुसार वाक्य संरचना, काल (Tense) और पद सामंजस्य के आधार पर विकल्प (${corr}) शुद्ध रूप है।`
    };
  } else if (sub.includes("hindi")) {
    return {
      solution_en: `Hindi Vyakaran Concept:\n• Option (${corr}) satisfies the grammatical rule (Sandhi/Samas/Shuddh Vartani).\n• Thus, Option (${corr}) is the official correct choice.`,
      solution_hi: `हिन्दी व्याकरण स्पष्टीकरण:\n• प्रश्न में पूछे गए व्याकरणिक नियम (संधि/समास/पर्यायवाची/शुद्ध वर्तनी) के अनुसार विकल्प (${corr}) पूर्णतः मानक और शुद्ध है।`
    };
  } else {
    return {
      solution_en: `Key Concept Explanation:\n• Background: Official MPESB examination curriculum verifies Option (${corr}) as factually correct.\n• Important takeaway: Remember this concept for quick recall in CBT exams.`,
      solution_hi: `महत्वपूर्ण संकल्पना एवं स्पष्टीकरण:\n• आधिकारिक पाठ्यक्रम और संदर्भ के अनुसार विकल्प (${corr}) प्रामाणिक और सही उत्तर है।\n• आगामी परीक्षाओं के लिए इस तथ्य को स्मरण रखें।`
    };
  }
}

// -------------------------------------------------------------
// Study Notes
// -------------------------------------------------------------
function openNoteEditor() {
  const q = currentQuestions[currentQIdx];
  modalTargetQuestion = q;
  document.getElementById("modal-note-title").textContent = `Personal Note — Q.${q.qno}`;
  document.getElementById("note-textarea").value = q.user_notes || "";
  openModal("modal-note");
}

function openNoteEditorFromModal() {
  if (!modalTargetQuestion) return;
  document.getElementById("modal-note-title").textContent = `Personal Note — Shift #${modalTargetQuestion.shift_id} Q.${modalTargetQuestion.qno}`;
  document.getElementById("note-textarea").value = modalTargetQuestion.user_notes || "";
  closeModal("modal-solution");
  openModal("modal-note");
}

function saveCurrentNote() {
  if (!modalTargetQuestion) return;
  const newNote = document.getElementById("note-textarea").value.trim();
  const shId = modalTargetQuestion.shift_id || currentShiftInfo.shift_index;
  window.Android.saveUserNote(shId, modalTargetQuestion.qno, newNote);
  modalTargetQuestion.user_notes = newNote;
  window.Android.showToast("Personal study note saved!");
  closeModal("modal-note");
  renderQuestion();
}

// -------------------------------------------------------------
// History & Bookmarks Tabs
// -------------------------------------------------------------
function loadHistoryTab() {
  try {
    const listStr = window.Android.getTestAttempts();
    const attempts = JSON.parse(listStr || "[]");
    const container = document.getElementById("history-list");
    if (attempts.length === 0) {
      container.innerHTML = `<div class="hint-text text-center py-20">No past test attempts yet. Complete a mock test to track your performance!</div>`;
      return;
    }

    container.innerHTML = attempts.map(a => {
      const attempted = a.correct_count + a.incorrect_count;
      const acc = attempted > 0 ? ((a.correct_count / attempted) * 100).toFixed(1) + "%" : "0%";
      const mins = Math.floor(a.time_spent_secs / 60);

      return `
        <div class="item-card">
          <div class="item-card-header">
            <span class="item-title">${escapeHtml(a.title)}</span>
            <span class="badge-marks font-bold">${a.score.toFixed(1)} / ${a.max_score.toFixed(0)}</span>
          </div>
          <div class="item-meta">
            📅 ${escapeHtml(a.completed_at || '')} &bull; Accuracy: <b>${acc}</b> &bull; Time: <b>${mins}m</b>
          </div>
          <div class="item-actions">
            <button class="btn btn-outline btn-block" onclick="reviewPastAttempt(${a.id})">🔍 Review Solutions & Mistakes</button>
            <button class="btn btn-success btn-xs" onclick="startExam(${a.shift_id}, 'EXAM')">🔄 Retake</button>
          </div>
        </div>
      `;
    }).join("");
  } catch (e) {
    console.error("loadHistoryTab error", e);
  }
}

function reviewPastAttempt(attemptId) {
  try {
    let attempt = null;
    if (window.Android && window.Android.getTestAttempt) {
      const attStr = window.Android.getTestAttempt(attemptId);
      if (attStr) attempt = JSON.parse(attStr);
    }
    if (!attempt) {
      alert("Attempt details could not be retrieved.");
      return;
    }

    const qStr = window.Android.getShiftQuestions(attempt.shift_id);
    currentQuestions = JSON.parse(qStr || "[]");
    if (!currentQuestions || currentQuestions.length === 0) {
      alert("Unable to load questions for this test shift.");
      return;
    }

    try {
      userAnswers = JSON.parse(attempt.answers_json || "{}");
    } catch (e) {
      userAnswers = {};
    }

    let sectionScores = {};
    try {
      sectionScores = JSON.parse(attempt.section_scores_json || "{}");
    } catch (e) {
      sectionScores = {};
    }

    const shift = allShifts.find(s => s.shift_index === attempt.shift_id);
    currentShiftInfo = shift || { shift_index: attempt.shift_id, name: attempt.title };
    currentAttemptData = attempt;
    examMode = attempt.mode || "EXAM";

    renderResultView(attempt, sectionScores);
    showView("view-result");
  } catch (e) {
    console.error("reviewPastAttempt error", e);
    alert("Error loading past test review: " + e.message);
  }
}

function retakeCurrentTest() {
  if (currentShiftInfo && currentShiftInfo.shift_index) {
    startExam(currentShiftInfo.shift_index, "EXAM");
  } else if (currentAttemptData && currentAttemptData.shift_id) {
    startExam(currentAttemptData.shift_id, "EXAM");
  } else {
    showView("view-dashboard");
  }
}

function loadBookmarksTab() {
  try {
    const bmsStr = window.Android.getBookmarks();
    const bms = JSON.parse(bmsStr || "[]");
    const container = document.getElementById("bookmarks-list");
    if (bms.length === 0) {
      container.innerHTML = `<div class="hint-text text-center py-20">No saved bookmarks. Tap the star icon (★) while practicing to bookmark important questions.</div>`;
      return;
    }

    container.innerHTML = bms.map(b => {
      const prev = (b.question_en || b.question_hi || "").substring(0, 95).replace(/\s+/g, " ");
      return `
        <div class="item-card">
          <div class="item-card-header">
            <span class="item-title">Shift #${b.shift_id} Q.${b.qno} &bull; ${escapeHtml(b.subject || '')}</span>
            <span class="badge-subject">Option ${b.correct_ans || ''}</span>
          </div>
          <div class="item-meta">${escapeHtml(prev)}...</div>
          <div class="item-actions">
            <button class="btn btn-outline btn-xs" onclick='openSolutionModal(${JSON.stringify(b).replace(/'/g, "&apos;")})'>💡 Inspect Solution</button>
          </div>
        </div>
      `;
    }).join("");
  } catch (e) {
    console.error("loadBookmarksTab error", e);
  }
}

// -------------------------------------------------------------
// Modal Utilities
// -------------------------------------------------------------
function openModal(id) {
  document.getElementById(id).classList.remove("hidden");
}

function closeModal(id) {
  document.getElementById(id).classList.add("hidden");
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[m]);
}
