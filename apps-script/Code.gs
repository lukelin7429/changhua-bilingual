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
 * FET 測驗（中文挑戰／校園文化）走 FET_SHEET_ID 那張獨立的試算表，
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

// FET 教師測驗 —— 兩個分頁：中文挑戰一個、校園文化一個。
// 級別不再拆分頁，改成 level 欄位，這樣一個分頁就能看出這個月誰交了、誰沒交，
// 用篩選器切 round / level 即可。
const FET_HEADERS = [
  'timestamp',      // 提交時間
  'teacher_id',     // 教師編號 F01–F74
  'teacher_name',   // 姓名
  'level',          // 中文：beginner / intermediate / advanced
                    // 文化：first-year / experienced
  'round',          // M1–M9（對應九次外師會議）
  'score',          // 得分
  'total',          // 總題數
  'percentage',     // 百分比
  'answers_json',   // 詳細作答紀錄（JSON）
  'user_agent',     // 瀏覽器資訊（除錯用）
];

// key = 網頁送來的 data.quiz。level 是這個 key 的預設級別，
// 網頁若另外送 data.level 就以網頁送的為準。
const FET_QUIZZES = {
  // 中文挑戰
  'fet-mandarin-beginner':     { sheetName: 'mandarin', level: 'beginner' },
  'fet-mandarin-intermediate': { sheetName: 'mandarin', level: 'intermediate' },
  'fet-mandarin-advanced':     { sheetName: 'mandarin', level: 'advanced' },
  'fet-mandarin-challenge':    { sheetName: 'mandarin', level: '' },  // 2026-07 以前的舊版單一題組

  // 校園文化
  'fet-culture-first-year':    { sheetName: 'culture',  level: 'first-year' },
  'fet-culture-experienced':   { sheetName: 'culture',  level: 'experienced' },
  'fet-school-culture':        { sheetName: 'culture',  level: '' },  // 舊版，沒有分級
};

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const fetQuiz = FET_QUIZZES[data.quiz];

    if (fetQuiz) {
      const sheet = getOrCreateSheet_(FET_SHEET_ID, fetQuiz.sheetName, FET_HEADERS);
      sheet.appendRow([
        new Date(),
        String(data.teacher_id   || ''),
        String(data.teacher_name || ''),
        String(data.level        || fetQuiz.level || ''),
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
 * FET 兩個分頁的手動驗證 —— 在編輯器選這個函式按「執行」，跑完後應該看到：
 *   mandarin 分頁：三筆 FET-000（beginner / intermediate / advanced）
 *   culture  分頁：兩筆 FET-000（first-year / experienced）
 * 確認完把這五列刪掉即可。
 */
function _smokeTestFetSheets() {
  const cases = [
    { quiz: 'fet-mandarin-beginner',     level: 'beginner' },
    { quiz: 'fet-mandarin-intermediate', level: 'intermediate' },
    { quiz: 'fet-mandarin-advanced',     level: 'advanced' },
    { quiz: 'fet-culture-first-year',    level: 'first-year' },
    { quiz: 'fet-culture-experienced',   level: 'experienced' },
  ];
  cases.forEach(function (c) {
    doPost({
      postData: {
        contents: JSON.stringify({
          quiz: c.quiz,
          level: c.level,
          teacher_id: 'FET-000',
          teacher_name: '測試外師',
          round: 'M1',
          score: 17, total: 20,
          answers: [{ id: 'B001', type: 'word', picked: 1, correct: true }],
          user_agent: 'smoke-test',
        }),
      },
    });
  });
}
