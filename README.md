# 智慧隨身型跌倒自適應預警與雲端通報裝置 (Smart Fall-Detection IoT System)

本專案建構了一套結合邊緣運算（Edge Computing）與雲端智慧（Cloud AI）的自適應長者跌倒偵測與主動通報系統。硬體端採用 ESP32 微控制器進行即時特徵擷取，雲端則佈署 Python 支援向量機（SVM）機器學習演算法，取代傳統死板的固定門檻值，並透過 LINE Bot 建立具備人類反饋進化的學習閉環（Learning Loop）。

---

## 🛠️ 專案三大核心特色
1. **端雲協同兩階段防誤報**：邊緣端進行 $2.8\text{ G}$ 突波捕捉與 10 秒動態能量積分；雲端端利用 SVM 現場重新訓練（Online Retraining）計算最佳決策超平面。
2. **工業級強韌通訊技術**：利用 `client->setInsecure()` 繞過憑證信任鏈，確保設備終身免燒錄維護；使用 `serializeJson()` 進行高容錯資料壓縮傳輸。
3. **主動式使用者反饋閉環**：家屬可透過 LINE Flex Message 按鈕即時修正 AI 誤報，引導模型進行線上監督式學習（Online Supervised Learning），越用越精準。

---

## 📂 目錄結構說明 (Repository Structure)

本專案開源原始碼依據「端雲架構」完整劃分如下：

```text
├── Arduino_ESP32/
│   ├── ESP32_Edge_Computing.ino  # ESP32 主程式（含 I2C 採樣、能量積分、HTTPS 傳輸）
│   └── README.md                 # 邊緣端硬體開發與接線說明
│
├── Cloud_Python/
│   ├── app.py                    # Flask 核心伺服器（含 SVM 模型即時重訓、LINE API 控制）
│   ├── requirements.txt          # Python 依賴套件清單 (scikit-learn, Flask, line-bot-sdk)
│   └── README.md                 # 雲端環境佈署與環境變數設定指南
│
└── Schema/
    └── system_architecture.png   # 系統整體架構數據流向圖
