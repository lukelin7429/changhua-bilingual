# 彰化雙語網站專案

人師教育協會（My Culture Connect）為彰化縣國小設計的雙語節慶教材。
透過 GitHub Pages 集中代管，於各校 Google Sites 以 iframe 方式嵌入。

## 結構

```
festivals/        各節慶單元，每個資料夾一個獨立的 index.html
  mothers-day/
apps-script/      共用的 Apps Script 後端，收集學生作答到 Google Sheet
```

## 設計原則

- **定高 App**：iframe 高度固定 720px，內部以階段切換不出現捲軸
- **單一 Apps Script Endpoint**：所有節慶、所有學校共用同一個收件 URL，以 `school_id` 與 `festival_id` 欄位區分
- **單一 Google Sheet**：用 Filter Views 為各校分視角

## 部署

GitHub Pages 自動發佈於 `main` 分支，網址：
`https://changhua-bilingual.org/festivals/<festival>/`

## 各校客製

每所合作學校的 `index.html` 只需修改 `CONFIG.SCHOOL_ID` 一處。
