# 彰化雙語網站專案

人師教育協會（My Culture Connect）為彰化縣國小設計的雙語節慶教材。
透過 GitHub Pages 集中代管，於各校 Google Sites 以 iframe 方式嵌入。

## 結構

```
index.html         Hub 首頁（含彰化鄉鎮互動地圖）
schools/           Hub 學校總覽 + 各校子站
  index.html       /schools/ 89 校總覽（依鄉鎮分組，從 data/schools.yml 產生）
  <slug>/          各校獨立子站
fets/              Hub 外師名錄頁
resources/         Hub 雙語資源頁（WotD / EduResources / Charming）
festivals/         共用節慶教材（8 個節慶）
data/              網站資料 single source of truth
  townships.yml    26 鄉鎮（中英、郵遞區號、town_id）
  schools.yml      89+ 校（鄉鎮、URL、學制、平台）
  fets.yml         外師名錄
assets/
  css/hub.css      Hub 共用樣式
  js/hub.js        Hub 共用 JS（互動地圖、學校搜尋）
  map/             彰化鄉鎮 GeoJSON
build.py           讀 YAML 重建 Hub HTML（編輯 YAML 後執行）
apps-script/       共用的 Apps Script 後端，收集學生作答到 Google Sheet
```

## Hub 維護流程

1. 編輯 `data/` 下的 YAML（schools.yml / fets.yml / townships.yml）。
2. 執行 `python3 build.py` 重新生成 `index.html` / `schools/index.html` / `fets/index.html` / `resources/index.html`。
3. `git add . && git commit && git push`。GitHub Pages 自動部署。

## 設計原則

- **定高 App**：iframe 高度固定 720px，內部以階段切換不出現捲軸
- **單一 Apps Script Endpoint**：所有節慶、所有學校共用同一個收件 URL，以 `school_id` 與 `festival_id` 欄位區分
- **單一 Google Sheet**：用 Filter Views 為各校分視角

## 部署

GitHub Pages 自動發佈於 `main` 分支，網址：
`https://changhua-bilingual.org/festivals/<festival>/`

## 各校客製

每所合作學校的 `index.html` 只需修改 `CONFIG.SCHOOL_ID` 一處。

## 協作者

加入此專案的協作者請先閱讀 [CONTRIBUTING.md](./CONTRIBUTING.md)。
