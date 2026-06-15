# CLAUDE.md — 彰化雙語資源網 / 各校雙語子站

> 這份檔案每次在本 repo 工作都會被自動載入。動任何學校頁面前先讀這三條鐵律。
> 違反過太多次，Luke 已多次震怒——**這是硬規則，不是建議**。

---

## 🔴 交付前三大鐵律（每次動工都要逐項檢查，不可略過）

### 1. Banner / Hero 照片 — 禁全幅遮罩
- 照片畫質清晰時，**不要**蓋全幅色彩/暗化 overlay（橘黃紅 radial gradient、整片暗化）——會把照片弄得「髒髒的」。
- 文字可讀性只用**底部單一漸層 scrim**：
  `linear-gradient(180deg, transparent 0%, transparent ~40%, rgba(10,20,42,.62) 100%)`
  （上半完全透明保住照片，只有文字所在底部柔和加深）
- 小字壓在亮天空 → 給**字**加 `text-shadow:0 1px 10px rgba(0,0,0,.5)`，不要為它加遮罩。
- 細節：memory `feedback_banner_no_muddy_overlay`

### 2. 字體 / 整套設計 — 一律以 `schools/yangming-jhs/` 為母版
- **第一個動作**：`head -200 schools/yangming-jhs/index.html` 抓 `:root` 色票 + 字型 stack + 字級規格，**直接複製**，不要憑直覺重發明。
- **絕對 px，禁 rem**：不准用 `1rem` / `clamp(1rem,…)` 當 body 或重要段落（換算後桌機 14–18px = Luke 眼中「小到可怕」）。
- 下限：body ≥ **20px** mobile / **23px** desktop；**任何要被讀的文字**（caption、中文補述、list item、卡片小標、對話框）≥ **17px / 19px**；只有純裝飾 eyebrow/badge 可 12–14px。
- 斷點 **720px**。font stack：`'Inter','PingFang TC','Apple LiGothic Medium','Microsoft JhengHei',sans-serif`，serif accent 用 `'Playfair Display'`。
- 細節 + 完整字級表：memory `feedback_school_site_typography`

### 3. Word of the Day / 單元分類 — 以 `schools/dajuang/lessons/` 為母版
- WOTD / Lessons 落地頁複製大莊的「主題色卡片網格」：`.units` grid（1→2→3 欄）+ `.unit` 卡（巨型 emoji hero 180px、每分類自己的漸層主題色、hover 上浮）。
- 標籤格式：`Unit 0X · <Stream> | <Title EN> / <Title ZH>`。
- 個別單元頁用 `.vc`（vocab card）元件，每單元 9 字。
- 細節：memory `reference_dajuang_wotd_category_design`

---

## ☑ 交付前自檢（mobile viewport 從頭滑到尾）

1. ☐ Banner 沒有全幅遮罩，照片乾淨？
2. ☐ body ≥20/23px、次要文字 ≥17/19px、**完全沒有 rem**？
3. ☐ `:root` 與字型是從 yangming-jhs 複製來的？
4. ☐ WOTD/Lessons 頁用了大莊的主題色卡片網格？
5. ☐ 滿版白底、不鎖中央窄欄？（見 memory `feedback_school_site_no_center_column`、`feedback_white_background`）

**只要有一段中文小到要瞇眼、或 banner 看起來霧濁，就是不及格，重做後才交付。**

---

## 🔴 Footer 標準署名（全縣統一，每校每頁都要）

每校**每一頁最底部**（`</body>` 前、`</footer>` 之外）放一條自帶樣式的標準署名條 `class="cb-credit"`，深色底 `#241f1b`、金色連結 `#e6c179`，內容**三行、各自連結**：

```
Site by  <My Culture Connect→www.mycultureconnect.org>  <人師教育協會→www.twrses.org>
Guided by  <CIEETRC 彰化縣國際教育暨英語教育資源中心→www.cieetrc.chc.edu.tw>
<Changhua Bilingual Hub 彰化雙語資源網→changhua-bilingual.org>
```

- **不要**在各校自己的 footer 裡再寫「Bilingual website by… / Guided by CIEETRC… / Part of the Changhua Bilingual Hub」舊署名——只留 ©、地址、校名、校網連結、計數器；署名統一由這條 cb-credit 負責。
- 母版＝竹塘（jhutang 的 `.ft__bottom` 原生含這三行；其他校用附加的 cb-credit 條）。
- 連結務必用 **www.twrses.org**、**www.mycultureconnect.org**（無 www 連不上）。
- 2026-06 全量 rollout 腳本：`/tmp/add_credit_strip.py`（加條）、`/tmp/clean_old_credits.py`（清舊署名）；細節 memory `project_zhutang_site`。

## 其他常踩規則（速查，細節在 memory）
- 每頁都要 banner，禁純文字白底標題；子頁 banner 不重用首頁那張
- banner 用校門/校舍/校徽/地景，不用人物照
- 🔴 **絕對不放會逐年變動的數字**（班級數、學生數、影片數、校齡/第 N 年）——首頁數字 band 與本文敘述都算。改用**永久穩定的事實**：創校年、定名年、設施落成年、百年慶、地點/市中心、特色設施（中央廚房/游泳館/烘焙教室）。Luke 已糾正多次。
- 雙語頁全 inline single-page，痛恨 click-out
- 卡片左上角不放單一中文字徽章；只列校長不列主任
- 不建議 Google Forms（嵌站測驗自製 HTML + Apps Script pipeline）
- 每校客製，不複用模板
- 🔴 **每頁都要有動感**（Luke 明確要求）。Hub 頁面分兩套動效引擎，新頁務必其一：
  - 套 hub chrome 的頁（首頁、`resources/*`）已吃 `assets/js/hub.js`（reveal selector 在 `initReveal()`，新類名要加進去）。
  - bespoke 頁（festivals / disaster-english / 1-on-1 / soccer / partners / 含 quiz）吃全站動效層 `assets/css/motion.css` + `assets/js/motion.js`（drop-in，不碰字型/色/版面）。
  - **新增這類頁後跑 `python3 scripts/inject_motion_layer.py`**（idempotent，自動略過已有 motion 的頁與 schools/）即補上動效。schools/ 各校自帶 motion 層，不歸這裡。

> 完整脈絡見 vault `組織事務/人師教育協會/彰化雙語網站專案/彰化雙語資源網/`（編號討論 + 現狀盤點 16）。
