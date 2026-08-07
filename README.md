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

### ⚠️ 剛 clone 完的人請先讀這段

`build.py` 產生圖片網址時，`?v=` 快取碼取的是**檔案的 mtime**。git 不保存 mtime，所以**重新 clone 之後所有檔案的 mtime 都是 clone 當下的時間**——這時候直接跑 `build.py`，130 多張圖的 `?v=` 會全部被改掉，`git diff` 出現一大坨與你的修改無關的雜訊，很容易誤 commit。

跑 `build.py` 前先把 mtime 還原成 committed HTML 裡記錄的值：

```bash
python3 - <<'PY'
import re, os
n = 0
for f in ['schools/index.html', 'index.html']:
    s = open(f, encoding='utf-8').read()
    for m in re.finditer(r'"(/assets/[^"?]+)\?v=(\d+)"', s):
        p, ts = m.group(1).lstrip('/'), int(m.group(2))
        if os.path.exists(p):
            os.utime(p, (ts, ts)); n += 1
print('restored mtimes:', n)
PY
```

跑完再 `python3 build.py`，diff 就只會剩下你真正改的東西。（只有真的換了圖檔時，才該讓那一張的 `?v=` 更新。）

**另外**：`schools/index.html` 是產生出來的，**不要手改**。手改的內容下次有人跑 `build.py` 就會被蓋掉，而且會讓 HTML 與 `schools.yml` 不同步（2026-07 就出現過大城鄉卡片排序錯誤、校數顯示 3 但實際 4 的情形）。要改內容一律改 `data/schools.yml`。

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
