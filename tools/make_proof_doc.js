// Build the proofreading document for the Mandarin question banks.
// One row per question, with every field that contains Chinese, and an empty
// column for Luke to type corrections into. Question ids are printed so the
// marked-up file can be read back and applied to the JSON precisely.

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, HeadingLevel, AlignmentType, PageOrientation, ShadingType,
  BorderStyle, PageBreak,
} = require('docx');

const REPO = process.argv[2];
const OUT = process.argv[3];

const ZH = 'PingFang TC';
const LEVELS = [
  { file: 'beginner', name: 'Beginner 入門', prefix: 'B' },
  { file: 'intermediate', name: 'Intermediate 進階', prefix: 'I' },
  { file: 'advanced', name: 'Advanced 高階', prefix: 'A' },
];
const MEETINGS = ['2026 年 9 月', '2026 年 10 月', '2026 年 11 月', '2026 年 12 月',
                  '2027 年 1 月', '2027 年 3 月', '2027 年 4 月', '2027 年 5 月',
                  '2027 年 6 月'];
const TYPE_ZH = {
  word: '字詞', listen: '聽力', expression: '用語', dialogue: '應答',
  situation: '情境', measure: '量詞', idiom: '成語',
};

// Landscape A4 usable width with 1440 DXA margins on each side.
const COLS = [900, 2100, 1900, 6100, 2958];
const TABLE_W = COLS.reduce((a, b) => a + b, 0);

const p = (text, opts = {}) => new Paragraph({
  spacing: { after: opts.after === undefined ? 40 : opts.after },
  alignment: opts.align,
  children: [new TextRun({
    text, bold: opts.bold, italics: opts.italics, size: opts.size || 19,
    color: opts.color, font: opts.font || ZH,
  })],
});

const cell = (children, opts = {}) => new TableCell({
  width: { size: opts.w, type: WidthType.DXA },
  shading: opts.shade ? { type: ShadingType.CLEAR, fill: opts.shade } : undefined,
  margins: { top: 80, bottom: 80, left: 110, right: 110 },
  children,
});

function headerRow() {
  const h = (t, w) => cell([p(t, { bold: true, size: 18, color: 'FFFFFF' })],
                           { w, shade: '1F6E6E' });
  return new TableRow({
    tableHeader: true,
    children: [h('題號', COLS[0]), h('中文', COLS[1]), h('拼音', COLS[2]),
               h('英文語境與說明', COLS[3]), h('✎ 修正（請寫在這一欄）', COLS[4])],
  });
}

function questionRow(q, shade) {
  const letters = ['A', 'B', 'C', 'D'];
  const body = [
    p(q.q, { size: 18 }),
    ...q.opts.map((o, i) => p(
      `${letters[i]}. ${o}${i === q.ok ? '   ✓ 正解' : ''}`,
      { size: 17, bold: i === q.ok, color: i === q.ok ? '2F7D5C' : '444444' },
    )),
    p(q.why, { size: 17, color: '555555', after: 0 }),
  ];
  return new TableRow({
    children: [
      cell([p(q.id, { bold: true, size: 18 }),
            p(TYPE_ZH[q.type] || q.type, { size: 15, color: '888888', after: 0 })],
           { w: COLS[0], shade }),
      cell([p(q.zh, { bold: true, size: 26, after: 0 })], { w: COLS[1], shade }),
      cell([p(q.py, { italics: true, size: 20, color: '444444', after: 0 })],
           { w: COLS[2], shade }),
      cell(body, { w: COLS[3], shade }),
      cell([p('', { after: 0 })], { w: COLS[4], shade }),
    ],
  });
}

const banks = LEVELS.map(l => ({
  ...l,
  data: JSON.parse(fs.readFileSync(
    path.join(REPO, 'fets/mandarin-challenge/data', l.file + '.json'), 'utf8')),
}));
const total = banks.reduce((n, b) => n + b.data.questions.length, 0);

// ---------------------------------------------------------------- cover page
const cover = [
  p('中文題庫 校對稿', { bold: true, size: 44, after: 120 }),
  p('彰化雙語資源網 · 外師中文學習內容', { size: 22, color: '666666', after: 320 }),

  p('這份文件是什麼', { bold: true, size: 24, after: 120 }),
  p(`網站上「中文挑戰」頁面與「每日練習」App 共用同一份題庫，總共 ${total} 題。` +
    '兩邊的內容完全來自這份題庫，所以校對這一份，兩邊就都會修正到。', { after: 240 }),

  p('怎麼標記', { bold: true, size: 24, after: 120 }),
  p('每一題最右邊有一欄「✎ 修正」。看到要改的地方，就在那一欄寫下正確的內容，' +
    '並註明是哪一個欄位。例如：', { after: 120 }),
  p('　　拼音 → lǎo shī', { font: ZH, color: '2F7D5C', after: 40 }),
  p('　　中文 → 老師好嗎', { font: ZH, color: '2F7D5C', after: 40 }),
  p('　　說明 → 「辛苦了」不能用在學生身上', { font: ZH, color: '2F7D5C', after: 40 }),
  p('　　正解 → 應該是 C', { font: ZH, color: '2F7D5C', after: 240 }),
  p('沒有問題的題目就留空。題號（B001、I045…）請不要更動——我要靠它把你的修改' +
    '對回原始檔案。用 Word 的追蹤修訂也可以，但寫在「修正」欄最不容易漏看。',
    { after: 320 }),

  p('請特別留意這幾件事', { bold: true, size: 24, after: 120 }),
  p('一、拼音的聲調。這是整份題庫最可能出錯的地方，我是逐題手寫的，' +
    '沒有用自動轉換（多音字會錯），但仍可能有疏漏。', { after: 100 }),
  p('二、台灣用法。有沒有哪個詞其實是大陸說法、或彰化校園實際上不這樣講。', { after: 100 }),
  p('三、正解是否真的正確，以及四個選項有沒有第二個也講得通。', { after: 100 }),
  p('四、說明寫得對不對、會不會誤導外師。', { after: 320 }),

  p('一個技術上的提醒', { bold: true, size: 24, after: 120 }),
  p('每一題的發音音檔是用「中文」欄的內容產生的。所以：', { after: 100 }),
  p('　· 只改拼音、英文或說明 → 音檔不受影響，改完即可上線。', { after: 60 }),
  p('　· 改到「中文」欄 → 那一題的音檔要重新產生並重新上傳。' +
    '這我會處理，你只要照常標記就好。', { after: 320 }),

  p(`內容規模：${banks.map(b => `${b.name} ${b.data.questions.length} 題`).join('　·　')}　·　合計 ${total} 題`,
    { size: 18, color: '888888' }),
];

// ------------------------------------------------------------------ sections
const children = [...cover];

banks.forEach((bank, bi) => {
  children.push(new Paragraph({ children: [new PageBreak()] }));
  children.push(new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { after: 160 },
    children: [new TextRun({ text: bank.name, font: ZH, size: 32, bold: true, color: '1F6E6E' })],
  }));
  children.push(p(bank.data.blurbZh || '', { color: '666666', size: 18, after: 240 }));

  const qs = bank.data.questions;
  for (let r = 0; r < Math.ceil(qs.length / 20); r++) {
    const slice = qs.slice(r * 20, (r + 1) * 20);
    if (!slice.length) continue;
    children.push(new Paragraph({
      heading: HeadingLevel.HEADING_2,
      spacing: { before: 240, after: 120 },
      children: [new TextRun({
        text: `M${r + 1}　${MEETINGS[r] || '備用'}　（${slice[0].id}–${slice[slice.length - 1].id}）`,
        font: ZH, size: 24, bold: true,
      })],
    }));
    children.push(new Table({
      columnWidths: COLS,
      width: { size: TABLE_W, type: WidthType.DXA },
      borders: {
        top: { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
        bottom: { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
        left: { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
        right: { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
        insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: 'DDDDDD' },
        insideVertical: { style: BorderStyle.SINGLE, size: 4, color: 'DDDDDD' },
      },
      rows: [headerRow(), ...slice.map((q, i) => questionRow(q, i % 2 ? 'F7F5F1' : undefined))],
    }));
  }
});

const doc = new Document({
  creator: 'Changhua Bilingual Hub',
  title: '中文題庫校對稿',
  styles: { default: { document: { run: { font: ZH, size: 19 } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE },
        margin: { top: 1080, bottom: 1080, left: 1440, right: 1440 },
      },
    },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUT, buf);
  console.log(`${OUT}  ${(buf.length / 1024).toFixed(0)} KB  ${total} questions`);
});
