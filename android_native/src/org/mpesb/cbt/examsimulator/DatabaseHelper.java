package org.mpesb.cbt.examsimulator;

import android.content.ContentValues;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.zip.GZIPInputStream;

public class DatabaseHelper {
    private static final String TAG = "DatabaseHelper";
    private static final String DB_NAME = "exam_data.db";
    private static final String DB_ASSET_GZ = "exam_data.db.gz";
    private static final int CURRENT_DB_VERSION = 2; // Version 2: Complete 14,000 solutions pre-cached

    private final Context context;
    private SQLiteDatabase db;

    public DatabaseHelper(Context context) {
        this.context = context;
        ensureDatabase();
    }

    private synchronized void ensureDatabase() {
        File dbFile = context.getDatabasePath(DB_NAME);
        SharedPreferences prefs = context.getSharedPreferences("app_prefs", Context.MODE_PRIVATE);
        int savedVer = prefs.getInt("db_version", 0);

        boolean needExtract = !dbFile.exists() || dbFile.length() < 1000000 || savedVer < CURRENT_DB_VERSION;

        if (needExtract) {
            // Backup user data if upgrading from previous database
            List<ContentValues> backupBookmarks = new ArrayList<>();
            List<ContentValues> backupAttempts = new ArrayList<>();
            List<ContentValues> backupNotes = new ArrayList<>();

            if (dbFile.exists() && dbFile.length() > 500000) {
                try (SQLiteDatabase oldDb = SQLiteDatabase.openDatabase(dbFile.getAbsolutePath(), null, SQLiteDatabase.OPEN_READONLY)) {
                    // Backup bookmarks
                    try (Cursor c = oldDb.rawQuery("SELECT shift_id, qno, subject, note, created_at FROM bookmarks", null)) {
                        while (c.moveToNext()) {
                            ContentValues cv = new ContentValues();
                            cv.put("shift_id", c.getInt(0));
                            cv.put("qno", c.getInt(1));
                            cv.put("subject", c.getString(2));
                            cv.put("note", c.getString(3));
                            cv.put("created_at", c.getString(4));
                            backupBookmarks.add(cv);
                        }
                    } catch (Exception ignored) {}

                    // Backup test attempts
                    try (Cursor c = oldDb.rawQuery("SELECT shift_id, title, mode, started_at, completed_at, score, max_score, total_questions, correct_count, incorrect_count, unattempted_count, marked_count, time_spent_secs, answers_json, section_scores_json FROM test_attempts", null)) {
                        while (c.moveToNext()) {
                            ContentValues cv = new ContentValues();
                            cv.put("shift_id", c.getInt(0));
                            cv.put("title", c.getString(1));
                            cv.put("mode", c.getString(2));
                            cv.put("started_at", c.getString(3));
                            cv.put("completed_at", c.getString(4));
                            cv.put("score", c.getDouble(5));
                            cv.put("max_score", c.getDouble(6));
                            cv.put("total_questions", c.getInt(7));
                            cv.put("correct_count", c.getInt(8));
                            cv.put("incorrect_count", c.getInt(9));
                            cv.put("unattempted_count", c.getInt(10));
                            cv.put("marked_count", c.getInt(11));
                            cv.put("time_spent_secs", c.getInt(12));
                            cv.put("answers_json", c.getString(13));
                            cv.put("section_scores_json", c.getString(14));
                            backupAttempts.add(cv);
                        }
                    } catch (Exception ignored) {}

                    // Backup user notes
                    try (Cursor c = oldDb.rawQuery("SELECT shift_id, qno, user_notes FROM questions WHERE user_notes IS NOT NULL AND user_notes != ''", null)) {
                        while (c.moveToNext()) {
                            ContentValues cv = new ContentValues();
                            cv.put("shift_id", c.getInt(0));
                            cv.put("qno", c.getInt(1));
                            cv.put("user_notes", c.getString(2));
                            backupNotes.add(cv);
                        }
                    } catch (Exception ignored) {}
                } catch (Exception e) {
                    Log.w(TAG, "Could not read old database for backup: " + e.getMessage());
                }
            }

            dbFile.getParentFile().mkdirs();
            Log.i(TAG, "Extracting full database v" + CURRENT_DB_VERSION + " from asset " + DB_ASSET_GZ + "...");
            try (InputStream is = context.getAssets().open(DB_ASSET_GZ);
                 GZIPInputStream gzis = new GZIPInputStream(is);
                 FileOutputStream fos = new FileOutputStream(dbFile)) {
                byte[] buffer = new byte[8192];
                int len;
                while ((len = gzis.read(buffer)) > 0) {
                    fos.write(buffer, 0, len);
                }
                fos.flush();
                Log.i(TAG, "Database extraction complete: " + dbFile.length() + " bytes.");
                prefs.edit().putInt("db_version", CURRENT_DB_VERSION).apply();
            } catch (Exception e) {
                Log.e(TAG, "Error extracting database: " + e.getMessage(), e);
            }

            // Restore user data into newly extracted database
            if (!backupBookmarks.isEmpty() || !backupAttempts.isEmpty() || !backupNotes.isEmpty()) {
                try (SQLiteDatabase newDb = SQLiteDatabase.openDatabase(dbFile.getAbsolutePath(), null, SQLiteDatabase.OPEN_READWRITE)) {
                    for (ContentValues cv : backupBookmarks) {
                        newDb.insertWithOnConflict("bookmarks", null, cv, SQLiteDatabase.CONFLICT_REPLACE);
                    }
                    for (ContentValues cv : backupAttempts) {
                        newDb.insert("test_attempts", null, cv);
                    }
                    for (ContentValues cv : backupNotes) {
                        int sId = cv.getAsInteger("shift_id");
                        int qNo = cv.getAsInteger("qno");
                        String note = cv.getAsString("user_notes");
                        ContentValues ncv = new ContentValues();
                        ncv.put("user_notes", note);
                        newDb.update("questions", ncv, "shift_id = ? AND qno = ?", new String[]{String.valueOf(sId), String.valueOf(qNo)});
                    }
                } catch (Exception e) {
                    Log.w(TAG, "Error restoring user data: " + e.getMessage());
                }
            }
        }

        try {
            db = SQLiteDatabase.openDatabase(dbFile.getAbsolutePath(), null, SQLiteDatabase.OPEN_READWRITE);
            db.execSQL("CREATE TABLE IF NOT EXISTS bookmarks (id INTEGER PRIMARY KEY AUTOINCREMENT, shift_id INTEGER, qno INTEGER, subject TEXT, note TEXT, created_at TEXT, UNIQUE(shift_id, qno))");
            db.execSQL("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)");
            db.execSQL("CREATE TABLE IF NOT EXISTS test_attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, shift_id INTEGER, title TEXT, mode TEXT, started_at TEXT, completed_at TEXT, score REAL, max_score REAL, total_questions INTEGER, correct_count INTEGER, incorrect_count INTEGER, unattempted_count INTEGER, marked_count INTEGER, time_spent_secs INTEGER, answers_json TEXT, section_scores_json TEXT)");
        } catch (Exception e) {
            Log.e(TAG, "Error opening database: " + e.getMessage(), e);
        }
    }

    public synchronized String getShifts() {
        JSONArray arr = new JSONArray();
        if (db == null) return arr.toString();
        try (Cursor c = db.rawQuery("SELECT shift_index, name, date, slot, start_page, end_page, page_count, question_count FROM shifts ORDER BY shift_index ASC", null)) {
            while (c.moveToNext()) {
                JSONObject obj = new JSONObject();
                obj.put("shift_index", c.getInt(0));
                obj.put("name", c.getString(1));
                obj.put("date", c.getString(2));
                obj.put("slot", c.getString(3));
                obj.put("start_page", c.getInt(4));
                obj.put("end_page", c.getInt(5));
                obj.put("page_count", c.getInt(6));
                obj.put("question_count", c.getInt(7));
                arr.put(obj);
            }
        } catch (Exception e) {
            Log.e(TAG, "getShifts error: " + e.getMessage());
        }
        return arr.toString();
    }

    public synchronized String getShiftQuestions(int shiftId) {
        JSONArray arr = new JSONArray();
        if (db == null) return arr.toString();
        try (Cursor c = db.rawQuery("SELECT shift_id, qno, qid, subject, question_en, question_hi, question_full, opt_a_en, opt_a_hi, opt_a_full, opt_b_en, opt_b_hi, opt_b_full, opt_c_en, opt_c_hi, opt_c_full, opt_d_en, opt_d_hi, opt_d_full, correct_ans, page_num, solution_en, solution_hi, user_notes FROM questions WHERE shift_id = ? ORDER BY qno ASC", new String[]{String.valueOf(shiftId)})) {
            while (c.moveToNext()) {
                JSONObject q = cursorToQuestion(c);
                arr.put(q);
            }
        } catch (Exception e) {
            Log.e(TAG, "getShiftQuestions error: " + e.getMessage());
        }
        return arr.toString();
    }

    public synchronized String getQuestionsBySubject(String subject, int limit) {
        JSONArray arr = new JSONArray();
        if (db == null) return arr.toString();
        String sql = "SELECT shift_id, qno, qid, subject, question_en, question_hi, question_full, opt_a_en, opt_a_hi, opt_a_full, opt_b_en, opt_b_hi, opt_b_full, opt_c_en, opt_c_hi, opt_c_full, opt_d_en, opt_d_hi, opt_d_full, correct_ans, page_num, solution_en, solution_hi, user_notes FROM questions WHERE subject LIKE ? ORDER BY RANDOM() LIMIT ?";
        try (Cursor c = db.rawQuery(sql, new String[]{"%" + subject + "%", String.valueOf(limit)})) {
            while (c.moveToNext()) {
                arr.put(cursorToQuestion(c));
            }
        } catch (Exception e) {
            Log.e(TAG, "getQuestionsBySubject error: " + e.getMessage());
        }
        return arr.toString();
    }

    public synchronized String searchQuestions(String query, String subject, int limit) {
        JSONArray arr = new JSONArray();
        if (db == null) return arr.toString();
        String sql;
        String[] args;
        String qLike = "%" + query + "%";
        if (subject != null && !subject.isEmpty() && !subject.equalsIgnoreCase("All Subjects")) {
            sql = "SELECT shift_id, qno, qid, subject, question_en, question_hi, question_full, opt_a_en, opt_a_hi, opt_a_full, opt_b_en, opt_b_hi, opt_b_full, opt_c_en, opt_c_hi, opt_c_full, opt_d_en, opt_d_hi, opt_d_full, correct_ans, page_num, solution_en, solution_hi, user_notes FROM questions WHERE (question_en LIKE ? OR question_hi LIKE ? OR question_full LIKE ?) AND subject LIKE ? ORDER BY shift_id ASC, qno ASC LIMIT ?";
            args = new String[]{qLike, qLike, qLike, "%" + subject + "%", String.valueOf(limit)};
        } else {
            sql = "SELECT shift_id, qno, qid, subject, question_en, question_hi, question_full, opt_a_en, opt_a_hi, opt_a_full, opt_b_en, opt_b_hi, opt_b_full, opt_c_en, opt_c_hi, opt_c_full, opt_d_en, opt_d_hi, opt_d_full, correct_ans, page_num, solution_en, solution_hi, user_notes FROM questions WHERE question_en LIKE ? OR question_hi LIKE ? OR question_full LIKE ? ORDER BY shift_id ASC, qno ASC LIMIT ?";
            args = new String[]{qLike, qLike, qLike, String.valueOf(limit)};
        }
        try (Cursor c = db.rawQuery(sql, args)) {
            while (c.moveToNext()) {
                arr.put(cursorToQuestion(c));
            }
        } catch (Exception e) {
            Log.e(TAG, "searchQuestions error: " + e.getMessage());
        }
        return arr.toString();
    }

    private JSONObject cursorToQuestion(Cursor c) throws Exception {
        JSONObject q = new JSONObject();
        q.put("shift_id", c.getInt(0));
        q.put("qno", c.getInt(1));
        q.put("qid", c.getString(2));
        q.put("subject", c.getString(3));
        q.put("question_en", c.getString(4));
        q.put("question_hi", c.getString(5));
        q.put("question_full", c.getString(6));
        q.put("opt_a_en", c.getString(7));
        q.put("opt_a_hi", c.getString(8));
        q.put("opt_a_full", c.getString(9));
        q.put("opt_b_en", c.getString(10));
        q.put("opt_b_hi", c.getString(11));
        q.put("opt_b_full", c.getString(12));
        q.put("opt_c_en", c.getString(13));
        q.put("opt_c_hi", c.getString(14));
        q.put("opt_c_full", c.getString(15));
        q.put("opt_d_en", c.getString(16));
        q.put("opt_d_hi", c.getString(17));
        q.put("opt_d_full", c.getString(18));
        q.put("correct_ans", c.getString(19));
        q.put("page_num", c.getInt(20));
        q.put("solution_en", c.getString(21));
        q.put("solution_hi", c.getString(22));
        q.put("user_notes", c.getString(23));
        return q;
    }

    public synchronized boolean saveUserNote(int shiftId, int qno, String note) {
        if (db == null) return false;
        try {
            ContentValues cv = new ContentValues();
            cv.put("user_notes", note);
            db.update("questions", cv, "shift_id = ? AND qno = ?", new String[]{String.valueOf(shiftId), String.valueOf(qno)});
            return true;
        } catch (Exception e) {
            Log.e(TAG, "saveUserNote error: " + e.getMessage());
            return false;
        }
    }

    public synchronized boolean toggleBookmark(int shiftId, int qno, String subject) {
        if (db == null) return false;
        try (Cursor c = db.rawQuery("SELECT id FROM bookmarks WHERE shift_id = ? AND qno = ?", new String[]{String.valueOf(shiftId), String.valueOf(qno)})) {
            if (c.moveToFirst()) {
                db.delete("bookmarks", "shift_id = ? AND qno = ?", new String[]{String.valueOf(shiftId), String.valueOf(qno)});
                return false; // unbookmarked
            } else {
                ContentValues cv = new ContentValues();
                cv.put("shift_id", shiftId);
                cv.put("qno", qno);
                cv.put("subject", subject);
                cv.put("created_at", new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault()).format(new Date()));
                db.insert("bookmarks", null, cv);
                return true; // bookmarked
            }
        } catch (Exception e) {
            Log.e(TAG, "toggleBookmark error: " + e.getMessage());
            return false;
        }
    }

    public synchronized boolean isBookmarked(int shiftId, int qno) {
        if (db == null) return false;
        try (Cursor c = db.rawQuery("SELECT id FROM bookmarks WHERE shift_id = ? AND qno = ?", new String[]{String.valueOf(shiftId), String.valueOf(qno)})) {
            return c.moveToFirst();
        } catch (Exception e) {
            return false;
        }
    }

    public synchronized String getBookmarks() {
        JSONArray arr = new JSONArray();
        if (db == null) return arr.toString();
        String sql = "SELECT b.shift_id, b.qno, b.subject, b.created_at, q.question_en, q.question_hi, q.correct_ans, q.solution_en, q.solution_hi, q.user_notes " +
                     "FROM bookmarks b JOIN questions q ON b.shift_id = q.shift_id AND b.qno = q.qno " +
                     "ORDER BY b.id DESC";
        try (Cursor c = db.rawQuery(sql, null)) {
            while (c.moveToNext()) {
                JSONObject b = new JSONObject();
                b.put("shift_id", c.getInt(0));
                b.put("qno", c.getInt(1));
                b.put("subject", c.getString(2));
                b.put("created_at", c.getString(3));
                b.put("question_en", c.getString(4));
                b.put("question_hi", c.getString(5));
                b.put("correct_ans", c.getString(6));
                b.put("solution_en", c.getString(7));
                b.put("solution_hi", c.getString(8));
                b.put("user_notes", c.getString(9));
                arr.put(b);
            }
        } catch (Exception e) {
            Log.e(TAG, "getBookmarks error: " + e.getMessage());
        }
        return arr.toString();
    }

    public synchronized long saveTestAttempt(String title, int shiftId, String mode, double score, double maxScore,
                                             int totalQ, int corr, int incorr, int unatt, int marked, int timeSpent,
                                             String answersJson, String sectionScoresJson) {
        if (db == null) return -1;
        try {
            ContentValues cv = new ContentValues();
            cv.put("title", title);
            cv.put("shift_id", shiftId);
            cv.put("mode", mode);
            cv.put("score", score);
            cv.put("max_score", maxScore);
            cv.put("total_questions", totalQ);
            cv.put("correct_count", corr);
            cv.put("incorrect_count", incorr);
            cv.put("unattempted_count", unatt);
            cv.put("marked_count", marked);
            cv.put("time_spent_secs", timeSpent);
            cv.put("started_at", new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault()).format(new Date()));
            cv.put("completed_at", new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault()).format(new Date()));
            cv.put("answers_json", answersJson);
            cv.put("section_scores_json", sectionScoresJson);
            return db.insert("test_attempts", null, cv);
        } catch (Exception e) {
            Log.e(TAG, "saveTestAttempt error: " + e.getMessage());
            return -1;
        }
    }

    public synchronized String getTestAttempts() {
        JSONArray arr = new JSONArray();
        if (db == null) return arr.toString();
        try (Cursor c = db.rawQuery("SELECT id, shift_id, title, mode, completed_at, score, max_score, total_questions, correct_count, incorrect_count, unattempted_count, time_spent_secs, answers_json, section_scores_json FROM test_attempts ORDER BY id DESC", null)) {
            while (c.moveToNext()) {
                JSONObject a = new JSONObject();
                a.put("id", c.getInt(0));
                a.put("shift_id", c.getInt(1));
                a.put("title", c.getString(2));
                a.put("mode", c.getString(3));
                a.put("completed_at", c.getString(4));
                a.put("score", c.getDouble(5));
                a.put("max_score", c.getDouble(6));
                a.put("total_questions", c.getInt(7));
                a.put("correct_count", c.getInt(8));
                a.put("incorrect_count", c.getInt(9));
                a.put("unattempted_count", c.getInt(10));
                a.put("time_spent_secs", c.getInt(11));
                a.put("answers_json", c.getString(12));
                a.put("section_scores_json", c.getString(13));
                arr.put(a);
            }
        } catch (Exception e) {
            Log.e(TAG, "getTestAttempts error: " + e.getMessage());
        }
        return arr.toString();
    }

    public synchronized String getTestAttempt(int attemptId) {
        JSONObject a = new JSONObject();
        if (db == null) return a.toString();
        try (Cursor c = db.rawQuery("SELECT id, shift_id, title, mode, completed_at, score, max_score, total_questions, correct_count, incorrect_count, unattempted_count, time_spent_secs, answers_json, section_scores_json FROM test_attempts WHERE id = ?", new String[]{String.valueOf(attemptId)})) {
            if (c.moveToFirst()) {
                a.put("id", c.getInt(0));
                a.put("shift_id", c.getInt(1));
                a.put("title", c.getString(2));
                a.put("mode", c.getString(3));
                a.put("completed_at", c.getString(4));
                a.put("score", c.getDouble(5));
                a.put("max_score", c.getDouble(6));
                a.put("total_questions", c.getInt(7));
                a.put("correct_count", c.getInt(8));
                a.put("incorrect_count", c.getInt(9));
                a.put("unattempted_count", c.getInt(10));
                a.put("time_spent_secs", c.getInt(11));
                a.put("answers_json", c.getString(12));
                a.put("section_scores_json", c.getString(13));
            }
        } catch (Exception e) {
            Log.e(TAG, "getTestAttempt error: " + e.getMessage());
        }
        return a.toString();
    }

    public synchronized String getSummaryStats() {
        JSONObject obj = new JSONObject();
        if (db == null) return obj.toString();
        try {
            int attempts = 0;
            double avgScore = 0.0;
            double bestScore = 0.0;
            try (Cursor c = db.rawQuery("SELECT COUNT(*), AVG(score), MAX(score) FROM test_attempts", null)) {
                if (c.moveToFirst()) {
                    attempts = c.getInt(0);
                    avgScore = c.getDouble(1);
                    bestScore = c.getDouble(2);
                }
            }
            int bookmarks = 0;
            try (Cursor c = db.rawQuery("SELECT COUNT(*) FROM bookmarks", null)) {
                if (c.moveToFirst()) bookmarks = c.getInt(0);
            }
            obj.put("total_attempts", attempts);
            obj.put("avg_score", avgScore);
            obj.put("best_score", bestScore);
            obj.put("bookmarks_count", bookmarks);
        } catch (Exception e) {
            Log.e(TAG, "getSummaryStats error: " + e.getMessage());
        }
        return obj.toString();
    }

    public synchronized void saveSetting(String key, String value) {
        if (db == null) return;
        try {
            ContentValues cv = new ContentValues();
            cv.put("key", key);
            cv.put("value", value);
            db.insertWithOnConflict("settings", null, cv, SQLiteDatabase.CONFLICT_REPLACE);
        } catch (Exception e) {
            Log.e(TAG, "saveSetting error: " + e.getMessage());
        }
    }

    public synchronized String getSetting(String key, String defaultValue) {
        if (db == null) return defaultValue;
        try (Cursor c = db.rawQuery("SELECT value FROM settings WHERE key = ?", new String[]{key})) {
            if (c.moveToFirst()) return c.getString(0);
        } catch (Exception ignored) {}
        return defaultValue;
    }
}
