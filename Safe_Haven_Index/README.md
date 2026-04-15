# 🌍 Safe Haven Index

> 你認為「避風港」應該長什麼樣？拉動權重，答案就變了。

互動式儀表板，用六項全球指標排名「哪些國家最適合當避風港」。權重是**你**決定的——政治穩定度重要還是能源自給重要、英語普及率重要還是離衝突多遠重要，滑桿拉一拉就看到排名怎麼翻轉。

## Key Findings（預設等權重）

- **Top 5**：Australia、Canada、New Zealand、Norway、Ireland — 共同特徵是政治穩定度高 + 英語國家 + 地理遠離衝突熱點
- **任何 preset 下 Australia 都穩拿第 1**：六項指標全部 ≥65 分，沒有明顯弱點（結構性安全，不是靠單一強項拉分）
- **Singapore / UAE 的排名高度依賴權重**：兩國因英語普及（SG）或移民友善（UAE）局部強勢，但在 security-focused preset 下就掉出前 10
- **底部集中在南亞 + 活躍衝突區**：Ukraine (24.9)、Pakistan (36.5)、Egypt (44.3)、Bangladesh (45.3)、Nigeria (47.2)
- **Norway 在 security-focused preset 躍升至 #2**（原本 #4）——能源 100% 自給 + 政治穩定度前段，只是移民友善度普通被等權重稀釋

*(數字為 61 個主要國家，World Bank 2022–2023 年資料 + EF English Proficiency Index)*

## 螢幕截圖

> 執行 `streamlit run app.py` 後在瀏覽器打開 http://localhost:8501

- **Rankings tab**：排名表 + Red-Yellow-Green 熱度底色
- **Map tab**：Plotly choropleth 世界地圖
- **Indicator profile tab**：任選一國看六維雷達圖
- **Sidebar**：六個權重滑桿 + 4 個 preset（Equal / Security / Lifestyle / Economic）

## 快速開始

```bash
pip install -r requirements.txt
python build_index.py          # 用內建 snapshot 算一次排名
streamlit run app.py           # 啟動互動儀表板
```

想用最新 World Bank 資料：

```bash
python build_index.py --live   # 打 WB API，更新到 data/raw/
```

（離線也能跑，`build_index.py` 不給 `--live` 就用 `data/snapshot/countries.csv`，這份是 repo 內建的。）

## 六項指標與資料來源

| 指標 | 中文 | 資料來源 | 原始單位 | 標準化 |
|---|---|---|---|---|
| `political_stability` | 政治穩定度 | World Bank `PV.EST`（WGI）| -2.5 .. +2.5 | clip 到理論區間後線性縮放到 0–100 |
| `energy_self_sufficiency` | 能源自給率 | 由 WB `EG.IMP.CONS.ZS` 推導 | % 進口 | `100 - imports%`，負值（淨出口）保留 |
| `healthcare_quality` | 醫療品質 | WB `SP.DYN.LE00.IN` + `SH.XPD.CHEX.PC.CD` | 歲 × USD | 70% 壽命 + 30% log(人均支出) |
| `immigration_friendliness` | 移民友善度 | 淨移民率（/千人）| rate | 線性縮放（-10..+15 合理區間）|
| `english_prevalence` | 英語普及率 | EF EPI + 英語原生/官方旗標 | 30–100 | 直接縮放 |
| `conflict_distance` | 距離衝突熱點 | 首都到 14 個熱點的 haversine 最小距離 | km | log(1+km) 避免遠距差異過度壓縮排名 |

衝突熱點清單（`data/reference/conflict_zones.csv`，可自行編輯）：
烏克蘭、加薩、敘利亞、葉門、蘇丹、緬甸、海地、索馬利亞、阿富汗、台海、南海、朝鮮半島、喀什米爾、衣索比亞提格雷。

## 合成分數怎麼算

```
normalised_weight_i = max(0, w_i) / Σ max(0, w_j)
safe_haven_score = Σ normalised_weight_i × indicator_score_i
```

缺值用**全域中位數**插補，但 `data_completeness` 欄會顯示該國六項中有幾項是真的觀察到的，不是插出來的。

## 資料夾結構

```
Safe_Haven_Index/
├── README.md
├── requirements.txt
├── build_index.py              # CLI：計算所有指標 + 預設排名
├── app.py                      # Streamlit 儀表板
├── data/
│   ├── snapshot/
│   │   └── countries.csv       # 內建 61 國 snapshot（離線 fallback）
│   ├── reference/
│   │   ├── conflict_zones.csv  # 14 個衝突熱點座標
│   │   └── english_proficiency.csv  # EF EPI + 英語國家旗標
│   ├── raw/                    # `--live` 模式會快取 WB API 回傳
│   └── safe_haven_index.csv    # build_index.py 輸出
└── src/
    ├── fetch.py                # WB API client + 離線 fallback
    ├── indicators.py           # 六個指標的計算 + 0-100 標準化
    └── scoring.py              # 加權合成 + 排名
```

## 設計取捨（留個紀錄）

- **為什麼挑這六項？** 題目指定的，但也的確覆蓋了「避風港」討論常見的幾個面向：制度（政治穩定）、自主（能源）、生存（醫療）、融入（英語、移民）、地緣（衝突距離）。
- **為什麼用 World Bank 為主？** 免費、無金鑰、歷史悠久、多數指標涵蓋 180+ 國。但英語普及和衝突距離 WB 沒有，所以這兩項用第三方資料補。
- **為什麼內建 snapshot？** 讓人 clone 下來直接 `streamlit run` 就看得到結果，不用先設 API key、不用先等抓資料。想用最新資料再跑 `--live`。
- **什麼時候這個分數會誤導人？** 當你把權重拉成極端單一項時——比如權重全部壓在英語普及，那菲律賓會跳得很高；但這不代表菲律賓真的是避風港。複合分數的意義就在分散風險，單一維度看排名會失真。
- **這不是地緣政治預測**。是一個幫助對話的工具，不是決策依據。

## 可能的延伸

- 加時間維度（滑 2010 → 2024）看各國分數怎麼變化
- 加「關切議題」篩選（氣候脆弱度、網路自由度、言論自由指數）
- 用 `--live` 跑完 WB API 後，補上完整 200+ 國 coverage
- 把幾個 preset 做成分享連結（query string 帶權重）
