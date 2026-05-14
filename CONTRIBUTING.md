# 協作指南 Contributing Guide

歡迎加入彰化雙語網站專案。這份文件是給協作者（collaborator）的入門指引，請在開始做第一個學校之前完整讀過一次。

主理人：林吉祥 Luke（lukelin7429）
所屬組織：人師教育協會 My Culture Connect
網域：https://changhua-bilingual.org

---

## 一、你的角色與權限

- 你被加為這個 repo 的 **collaborator (Write 權限)**
- 你**可以**：開分支、推 commit、開 Pull Request、修改自己負責的學校資料夾
- 你**不需要也不要**：動 CNAME、動 GitHub Pages 設定、動 apps-script/、動 .github/、改其他學校資料夾、merge 自己的 PR
- 所有 PR 由 Luke review 後 merge，merge 後約 1–2 分鐘自動上線

---

## 二、網址規則（重要）

學校頁面網址格式固定為：

```
https://changhua-bilingual.org/schools/<學校slug>/
https://changhua-bilingual.org/schools/<學校slug>/festivals/
https://changhua-bilingual.org/schools/<學校slug>/bilingual-campus/
```

- slug 一律小寫英文，用學校官方羅馬拼音（例：和美 = `homei`、文昌 = `wenchang`）
- 開新學校之前**先跟 Luke 確認 slug**，slug 一旦上線就不能改
- 你的 GitHub 帳號名稱不會出現在任何網址中

---

## 三、工作流程

### 1. 一次性設定

```bash
git clone https://github.com/lukelin7429/changhua-bilingual.git
cd changhua-bilingual
```

### 2. 每次做新學校或修改

```bash
# 從最新的 main 開分支
git checkout main
git pull
git checkout -b school/<學校slug>

# 做你的修改 ...

git add schools/<學校slug>
git commit -m "Add <學校名> bilingual campus page"
git push -u origin school/<學校slug>
```

然後到 GitHub 上開 Pull Request，target 是 `main`。Luke 會 review。

### 3. 不要做的事

- ❌ 不要直接 push 到 `main`
- ❌ 不要 force push (`git push -f`)
- ❌ 不要 `git add .` 或 `git add -A`，請只 add 你自己學校的資料夾
- ❌ 不要 commit `.env`、Google API key、家長/老師個資、薪資資料、簽名圖片
- ❌ 不要動別人學校的檔案，即使你覺得可以順手改

---

## 四、學校資料夾結構

每所學校在 `schools/<slug>/` 底下，標準結構：

```
schools/<slug>/
  index.html              # 學校首頁（如果學校已有 banner，從第一章節開始即可）
  bilingual-campus/
    index.html            # 雙語校園
  festivals/              # 不要建子頁！見第六節
  assets/                 # 學校自己的圖片
```

建新學校最快的方式：複製一所已上線、結構接近的學校，整個資料夾複製、改 slug、改內容。

---

## 五、設計規範（必須遵守）

### 5.1 字體

**繁體中文必須用系統字體**：

```css
font-family: 'PingFang TC', 'Apple LiGothic Medium', 'Microsoft JhengHei', sans-serif;
```

絕對不要用 Google Fonts 的中文顯示字體（ZCOOL、Ma Shan Zheng、Zhi Mang Xing 等）——這些字體對繁體字支援差。英文部分可以用 Google Fonts（Montserrat、Lato、Playfair Display 等）。

### 5.2 背景

**全頁純白底 `#fff`**。不用 cream、米色、漸層。小型 UI 元素（卡片、按鈕）可以例外。

### 5.3 不要放會變動的數字

**任何頁面的 banner / hero 都不可以**放這些數字：

- 班級數、學生數、教師數
- 校齡（「創校 70 年」不行，「Est. 1955」可以）
- 影片數、單元數、場景數
- 「連續 X 年」獎項計數
- 卡片右上角的 meta count

改用穩定事實標籤：`Est. 1955`、`Rural Campus`、`MOE Honored`、`Coastal Campus`。

### 5.4 不列處室主任

學校網站只列**校長**。主任輪調太頻繁，不上網站。如果學校沒提供，也不要追問。

### 5.5 不要 Click-out（彈新分頁）

所有內容 **inline single page**，內部跳轉用 anchor (`#section`)。不要把學員推去外連 CTA 或新分頁。模仿 `schools/wansing/` 的 Shannon 八週講義結構。

### 5.6 學費

**絕對不要**寫「學費」「收費」「課程費用」之類的字眼。人師教育協會 24 年純公益，所有實習老師授課都免費。

### 5.7 學校已有 banner 的情況

如果 twrses（學校子網域）已經有設計師做的 banner，**不要重做 hero 蓋過去**。你的頁面從第一個章節開始即可。

---

## 六、Sub-nav 七連結（標準）

每所學校的 sub-nav 順序**固定**這七個 link，順序不可以變：

1. Home
2. Lessons
3. Bilingual Campus
4. Teachers
5. About
6. Contact
7. Festivals ← **永遠在最後**

### Festivals 特殊規則

- **不要**在學校資料夾下建 `festivals/index.html`
- Sub-nav 的 Festivals link **用絕對 URL**：
  ```html
  <a href="https://changhua-bilingual.org/festivals/?from=<學校slug>">Festivals</a>
  ```
- 新學校上線後，要記得在 `festivals/index.html` 的 JS slug 名單裡加上你的學校 slug（這步 Luke 會處理，但你可以提醒）

---

## 七、Bilingual Campus 必嵌兩條 Playlist

每所學校的 `bilingual-campus/index.html` 必須嵌入兩條共用 playlist：

1. **課室英語 Classroom English**（Sarah Thomas）
2. **廣播英語 Morning Broadcast English**（Sarah + Susan）

詳細 playlist URL 在 Luke 的 Obsidian vault `共用素材/影音 Playlists.md`，新學校開始前向 Luke 索取最新版。**不要自己上 YouTube 找替代**。

---

## 八、測驗（Quiz）規則

如果頁面有測驗：

- **不用 Google Forms**，一律自製 HTML quiz + Apps Script Webhook → Google Sheet
- 所有測驗共用同一個 Apps Script endpoint（在 `apps-script/`），用 `school_id` 和 `festival_id` 區分
- **Options（選項）一律純英文**。中文只能出現在 `zh` 提示與作答後的 explanation。選項並列中文等同送答案。
- 不要新增新的 Apps Script endpoint，找 Luke 給你現有的 URL

---

## 九、品牌 URL 區分

文宣或頁面提到組織名稱時，連結要分清楚：

- **「人師教育協會 / My Culture Connect」** → 連 `https://www.mycultureconnect.org`（協會官網）
- **「Changhua Bilingual Network」** → 連 `https://changhua-bilingual.org`（本站，子網域是 `changhua.`）

兩個是不同層級的品牌，不要混用。

---

## 十、Festival 系列頁面的調色板

跨校共用的 Festival 頁面 banner 統一用**暖灰** `#2a2725`（不是 navy），這樣嵌入任何學校都不衝突。學校自己頁面可以有自己的主色，但 Festival 頁面不要動這個共用色。

---

## 十一、PII 與隱私

絕對不要 commit 這些內容：

- 學生姓名、家長聯絡資料、班級名冊
- 外籍老師的薪資、簽證資料、簽名圖片
- 任何 API key、Google service account JSON、`.env`
- 老師護照、合約、健康資料

如果你的本機資料夾裡有這些檔案，加到 `.gitignore`，**不要**靠 `git add` 時手動跳過。

---

## 十二、不清楚就問

這份文件無法涵蓋所有情境。遇到下列狀況請先問 Luke：

- 學校提出「特殊設計需求」（漸層 banner、彈窗、cookie 同意等）
- 學校要在頁面加表單收家長資料
- 學校要嵌入 Google Map、Google Calendar、外部報名系統
- 學校給你的素材中有未公開的學生照片
- 任何需要動到 `apps-script/`、`CNAME`、根目錄檔案的需求

寧可多問一次，不要事後拆掉重做。

---

## 十三、Commit Message 慣例

使用簡潔的英文 commit message，動詞開頭：

```
Add Tianzhong Elementary bilingual campus page
Fix Hualong festival link to use absolute URL
Update Wenchang principal info
```

PR 標題用一句話描述這個 PR 完成了什麼，例如：

```
Add Yongjing Elementary site (schools/yongjing/)
```

---

歡迎加入。有任何問題隨時跟 Luke 聯絡。
