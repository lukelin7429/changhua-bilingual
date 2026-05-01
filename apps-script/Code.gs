/**
 * 彰化雙語網站 — 共用測驗收件 Web App
 * ----------------------------------------------
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
 */

const SHEET_ID   = '17abM_sbDrsEdqbGfX8jGBXW76DRoOb668Nt-9W7VIDY';
const SHEET_NAME = 'responses';

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

function doPost(e) {
  try {
    const data  = JSON.parse(e.postData.contents);
    const sheet = getOrCreateSheet_();

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

function getOrCreateSheet_() {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
  }
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold');
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
