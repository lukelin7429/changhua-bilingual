/**
 * 彰化雙語網站 — 共用測驗收件 Web App
 * ----------------------------------------------
 * 這份程式碼寫進哪一張試算表的 Apps Script 編輯器都可以（openById 會直接
 * 指定目標試算表，不受程式碼「掛在哪」影響）——通常就貼在 SHEET_ID 那張裡。
 *
 * 部署方式：
 * 1. 在 Google Sheets 開一張新試算表，命名為「彰化雙語網站_作答紀錄」
 * 2. 複製試算表的 ID（網址中 /d/ 後面那段），貼到下方 SHEET_ID
 * 3. 在試算表 → 擴充功能 → Apps Script，把這份程式碼貼入 Code.gs
 * 4. 部署 → 新增部署作業 → 類型選「網路應用程式」
 *    - 執行身份：自己（你的 Google 帳號）
 *    - 存取權：任何人
 * 5. 複製產生的 Web App URL，貼到 index.html 中 CONFIG.WEBHOOK_URL
 *
 * 注意：每次修改 .gs 後要「管理部署 → 編輯 → 版本選新版本 → 部署」才會生效
 *
 * FET 測驗（中文挑戰／學校文化）走 FET_SHEET_ID 那張獨立的試算表，
 * 跟其他節慶測驗共用的 SHEET_ID 分開——兩張都必須是這個 Google 帳號
 * 自己擁有或至少有編輯權限的試算表，openById 才寫得進去。
 */

const SHEET_ID   = '17abM_sbDrsEdqbGfX8jGBXW76DRoOb668Nt-9W7VIDY';
const SHEET_NAME = 'responses';

// FET 教師管理試算表（Luke 指定，獨立於上面共用的節慶測驗試算表）：
// https://docs.google.com/spreadsheets/d/1lBWhxRISyXasaFFPSgvn4ft7zgdNz8RpgPvfxGhBGEs/
const FET_SHEET_ID = '1lBWhxRISyXasaFFPSgvn4ft7zgdNz8RpgPvfxGhBGEs';

const HEADERS = [
  'timestamp',      // 提交時間
  'school_id',      // 學校代碼（協會內部編號）
  'festival_id',    // 節慶代碼（如 mothers-day-2026）
  'school',         // 學生填的學校名
  'class',          // 班級
  'student_name',   // 姓名
  'score',          // 得分
  'total',          // 總題數
  'percentage',     // 百分比
  'answers_json',   // 詳細作答紀錄（JSON）
  'user_agent',     // 瀏覽器資訊（除錯用）
];

// FET 教師測驗（中文挑戰 / 學校文化）——同一份試算表、各自獨立分頁。
// data.quiz 對到下面的 key 就會寫進對應分頁；不是這兩個 key 的請求，
// 一律沿用舊的 'responses' 分頁與 HEADERS，既有節慶測驗行為不受影響。
const FET_QUIZZES = {
  'fet-mandarin-challenge': {
    sheetName: 'fet_mandarin_challenge',
    headers: ['timestamp', 'teacher_id', 'teacher_name', 'round', 'score', 'total', 'percentage', 'answers_json', 'user_agent'],
  },
  'fet-school-culture': {
    sheetName: 'fet_school_culture',
    headers: ['timestamp', 'teacher_id', 'teacher_name', 'round', 'score', 'total', 'percentage', 'answers_json', 'user_agent'],
  },
};

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const fetQuiz = FET_QUIZZES[data.quiz];

    if (fetQuiz) {
      const sheet = getOrCreateSheet_(FET_SHEET_ID, fetQuiz.sheetName, fetQuiz.headers);
      sheet.appendRow([
        new Date(),
        String(data.teacher_id   || ''),
        String(data.teacher_name || ''),
        String(data.round        || ''),
        Number(data.score        || 0),
        Number(data.total        || 0),
        data.total ? Math.round((data.score / data.total) * 100) : 0,
        JSON.stringify(data.answers || []),
        String(data.user_agent   || ''),
      ]);
      return jsonOut_({ ok: true });
    }

    const sheet = getOrCreateSheet_(SHEET_ID, SHEET_NAME, HEADERS);
    sheet.appendRow([
      new Date(),
      String(data.school_id    || ''),
      String(data.festival_id  || ''),
      String(data.school       || ''),
      String(data.class        || ''),
      String(data.student_name || ''),
      Number(data.score        || 0),
      Number(data.total        || 0),
      data.total ? Math.round((data.score / data.total) * 100) : 0,
      JSON.stringify(data.answers || []),
      String(data.user_agent   || ''),
    ]);

    return jsonOut_({ ok: true });
  } catch (err) {
    return jsonOut_({ ok: false, error: err.toString() });
  }
}

function doGet() {
  return ContentService.createTextOutput(
    'Changhua Bilingual Quiz endpoint OK. Use POST to submit.'
  );
}

function getOrCreateSheet_(spreadsheetId, sheetName, headers) {
  const ss = SpreadsheetApp.openById(spreadsheetId);
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  }
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function jsonOut_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * 一次性測試函式：在 Apps Script 編輯器點「執行」可手動驗證寫入是否正常
 */
function _smokeTest() {
  doPost({
    postData: {
      contents: JSON.stringify({
        school_id:    'demo-school',
        festival_id:  'mothers-day-2026',
        school:       '彰化國小',
        class:        '六年三班',
        student_name: '測試學生',
        score: 5, total: 5,
        answers: [{q:0,picked:0,correct:true}],
        user_agent: 'smoke-test',
      }),
    },
  });
}

/**
 * FET 測驗（中文挑戰 / 學校文化）的手動驗證 — 執行後檢查
 * fet_mandarin_challenge 分頁是否多了一列測試資料
 */
function _smokeTestFetQuiz() {
  doPost({
    postData: {
      contents: JSON.stringify({
        quiz: 'fet-mandarin-challenge',
        teacher_id: 'FET-000',
        teacher_name: '測試外師',
        round: '2026-08',
        score: 18, total: 20,
        answers: [{ q: 0, picked: 0, correct: true }],
        user_agent: 'smoke-test',
      }),
    },
  });
}
