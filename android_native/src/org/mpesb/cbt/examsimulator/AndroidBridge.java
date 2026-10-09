package org.mpesb.cbt.examsimulator;

import android.content.Context;
import android.webkit.JavascriptInterface;
import android.widget.Toast;

public class AndroidBridge {
    private final Context context;
    private final DatabaseHelper dbHelper;

    public AndroidBridge(Context context, DatabaseHelper dbHelper) {
        this.context = context;
        this.dbHelper = dbHelper;
    }

    @JavascriptInterface
    public String getShifts() {
        return dbHelper.getShifts();
    }

    @JavascriptInterface
    public String getShiftQuestions(int shiftId) {
        return dbHelper.getShiftQuestions(shiftId);
    }

    @JavascriptInterface
    public String getQuestionsBySubject(String subject, int limit) {
        return dbHelper.getQuestionsBySubject(subject, limit);
    }

    @JavascriptInterface
    public String getShiftSubjectQuestions(int shiftId, String subject) {
        return dbHelper.getShiftSubjectQuestions(shiftId, subject);
    }

    @JavascriptInterface
    public String getSubjectSets(String subject) {
        return dbHelper.getSubjectSets(subject);
    }

    @JavascriptInterface
    public String searchQuestions(String query, String subject, int limit) {
        return dbHelper.searchQuestions(query, subject, limit);
    }

    @JavascriptInterface
    public boolean toggleBookmark(int shiftId, int qno, String subject) {
        return dbHelper.toggleBookmark(shiftId, qno, subject);
    }

    @JavascriptInterface
    public boolean isBookmarked(int shiftId, int qno) {
        return dbHelper.isBookmarked(shiftId, qno);
    }

    @JavascriptInterface
    public String getBookmarks() {
        return dbHelper.getBookmarks();
    }

    @JavascriptInterface
    public boolean saveUserNote(int shiftId, int qno, String note) {
        return dbHelper.saveUserNote(shiftId, qno, note);
    }

    @JavascriptInterface
    public long saveTestAttempt(String title, int shiftId, String mode, double score, double maxScore,
                                int totalQ, int corr, int incorr, int unatt, int marked, int timeSpent,
                                String answersJson, String sectionScoresJson) {
        return dbHelper.saveTestAttempt(title, shiftId, mode, score, maxScore, totalQ, corr, incorr, unatt, marked, timeSpent, answersJson, sectionScoresJson);
    }

    @JavascriptInterface
    public String getTestAttempts() {
        return dbHelper.getTestAttempts();
    }

    @JavascriptInterface
    public String getTestAttempt(int attemptId) {
        return dbHelper.getTestAttempt(attemptId);
    }

    @JavascriptInterface
    public String getSummaryStats() {
        return dbHelper.getSummaryStats();
    }

    @JavascriptInterface
    public void saveSetting(String key, String value) {
        dbHelper.saveSetting(key, value);
    }

    @JavascriptInterface
    public String getSetting(String key, String defVal) {
        return dbHelper.getSetting(key, defVal);
    }

    @JavascriptInterface
    public void showToast(final String message) {
        if (context instanceof MainActivity) {
            ((MainActivity) context).runOnUiThread(() -> Toast.makeText(context, message, Toast.LENGTH_SHORT).show());
        }
    }
}
