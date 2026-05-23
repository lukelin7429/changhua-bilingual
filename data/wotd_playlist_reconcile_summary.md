# WOTD Playlist 對齊 wotd.csv — 摘要報告

產出日期：自動生成 / 來源 playlist：3,029 支 / 既有 wotd.csv：2166 唯一影片

## 解析統計

| 狀態 | 數量 | 說明 |
|---|---:|---|
| `ok` | 2911 | 學校名對齊 schools.yml 成功 |
| `mcc_self` | 66 | 人師教育協會自製（非學校 contributor）|
| `ccc_ny` | 8 | CCC 紐約首府華社中文學校（跨組織）|
| `out_of_county` | 39 | 非彰化縣學校（台中／南投等跨縣合作）|
| `school_not_in_yml` | 0 | 彰化學校但 schools.yml 沒收錄 → **需補進 schools.yml** |
| `missing` | 5 | 描述沒夠線索抓到學校 → **手動查補** |

句子抽取：sentence_1 命中 3027 / 3029

## 新增影片

- Playlist 上但 wotd.csv 沒收錄：**863 支**
- 已收錄：2166 支
- → 詳見 `wotd_new_videos.csv`

## 去重決策

- 重複群組（同 keyword + 同 sentence_1）：**356 組**
- 規則：(1) 校影片數少的優先（讓更多學校露臉）(2) 鄉鎮代表性少的為 tiebreaker (3) video_id 穩定
- 結果：865 支建議移除、356 支保留
- → 詳見 `wotd_dedup_decisions.csv`

## 需要補進 schools.yml 的學校

這些是 description 裡有「彰化XX國小/國中」但 schools.yml 找不到的：

| 學校 | 影片數 |
|---|---:|

## 描述沒線索的影片（11 支需手動查）

見 `wotd_missing_school.csv` 中 status=missing 的列。
