/**
 * 溪州國中 聽力挑戰 Listening Challenge — Google Apps Script 收件程式
 * ====================================================================
 * 接收 /schools/sijhou-jhs/lessons/listening/<期數>/ 網頁送出的成績，
 * 每位學生寫一列到「這張」試算表的 Responses 分頁（container-bound，
 * 不需要 SHEET_ID）。
 *
 * 設定（一次）：
 *   1. 在 luke@mycultureconnect.org 開一張新的 Google 試算表，
 *      命名「溪州國中 聽力挑戰 成績」。
 *   2. 擴充功能 → Apps Script，刪掉範例程式，貼上這整份。
 *   3. 部署 → 新增部署作業 → 類型「網路應用程式」
 *        執行身分：我    存取權：任何人
 *   4. 複製 Web App 網址，貼到每一期 index.html 的 ENDPOINT。
 *   5. 在編輯器選 _smokeTest → 執行，確認 Responses 多一列測試資料。
 *   6. （選用）選 setupRaffle → 執行，建立「滿分名單」分頁。
 *
 * 修改這份程式後要重新部署：管理部署作業 → 編輯 → 版本：新版本 → 部署。
 */

var TAB = 'Responses';
var QUESTIONS = 5;
var HEADERS = ['時間 Time', '期數 Issue', '班級 Class', '姓名 Name', '分數 Score',
               'Q1', 'Q2', 'Q3', 'Q4', 'Q5', '瀏覽器 Browser'];

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(20000);                     // 全校同時交卷時，一次寫一列
    var data = JSON.parse(e.postData.contents);
    var answers = data.answers || [];
    var row = [
      new Date(),
      "'" + String(data.issue || ''),         // 保留 01 的前導 0
      String(data.cls || '').slice(0, 10),
      String(data.name || '').slice(0, 30),
      Number(data.score || 0)
    ];
    for (var i = 0; i < QUESTIONS; i++) row.push(String(answers[i] != null ? answers[i] : ''));
    row.push(String(data.user_agent || '').slice(0, 200));
    getSheet_().appendRow(row);
    return jsonOut_({ ok: true });
  } catch (err) {
    return jsonOut_({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

function doGet() {
  return ContentService.createTextOutput('Sijhou Listening Challenge endpoint OK.');
}

function getSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(TAB);
  if (!sheet) {
    sheet = ss.insertSheet(TAB, 0);
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight('bold');
    sheet.setFrozenRows(1);
    sheet.getRange('A:A').setNumberFormat('yyyy/MM/dd HH:mm:ss');
  }
  return sheet;
}

function jsonOut_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
                       .setMimeType(ContentService.MimeType.JSON);
}

/* 在編輯器執行一次，確認 Responses 分頁多一列測試資料（確認後可刪除該列）。 */
function _smokeTest() {
  var out = doPost({ postData: { contents: JSON.stringify({
    quiz: 'sijhou-listening', issue: 'TEST', cls: '701', name: '測試學生',
    score: 100, total: 100, answers: ['C ✓', 'B ✓', 'A ✓', 'D ✓', 'C ✓'],
    user_agent: 'smoke-test'
  }) } });
  Logger.log(out.getContent());
}

/**
 * 滿分名單 — 在編輯器執行一次。建立「滿分名單 Perfect」分頁，
 * 用公式即時列出每一期 100 分的同學（同一期同班同名只列一次），
 * 之後新交卷的資料會自動出現，不用重新部署。
 */
function setupRaffle() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  getSheet_();
  var st = ss.getSheetByName('滿分名單 Perfect') || ss.insertSheet('滿分名單 Perfect');
  st.clear();
  st.getRange('A1:C1').setValues([['期數 Issue', '班級 Class', '姓名 Name']]).setFontWeight('bold');
  st.getRange('A2').setFormula(
    '=IFERROR(SORT(UNIQUE(FILTER({' + TAB + '!B2:B,' + TAB + '!C2:C,' + TAB + '!D2:D},' +
    TAB + '!E2:E=100,' + TAB + '!B2:B<>"TEST")),1,TRUE,2,TRUE),"（目前還沒有滿分）")');
  st.setFrozenRows(1);
  st.setColumnWidth(1, 110); st.setColumnWidth(2, 110); st.setColumnWidth(3, 160);
}
