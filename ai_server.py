import os
from flask import Flask, request, jsonify
from linebot import LineBotApi
from linebot.models import TextSendMessage, URIAction, ButtonsTemplate, TemplateSendMessage
import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler  # ✨ 解決困難 4 引入的核心庫

app = Flask(__name__)

# ==========================================
# ⚙️ LINE 設定區 (請填入你的金鑰)
# ==========================================
LINE_CHANNEL_ACCESS_TOKEN = "aOFBFW9fEErWeF2rK55QwntCJZuFKLHaPYAvR8uCSqzGoAUDZcuNQrwka3VbLjxBPh/xvDJE459guzQqIw35mQWPYK/FwiIY0f7q2gj2aybNzmZHcVn1V9TvZhtXolO1G9dpMXT1qm2PMGua4MwaJwdB04t89/1O/w1cDnyilFU=YOUR_CHANNEL_ACCESS_TOKEN"
LINE_USER_IDS = [
    "Uf2a00cc3b73a9c4bd34d8dcd8115511a",  # 填入你的 User ID
]

try:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    print("ℹ️ [LINE] 模組載入成功！")
except Exception as e:
    print(f"⚠️ [LINE] 初始化失敗: {e}")

# ==========================================
# 🧠 機器學習記憶庫 (自學習核心)
# 欄位：[最大衝擊力 G, 晃動能量積分, 答案標籤(1=跌倒, 0=日常活動)]
# ==========================================
memory_database = [
    [4.5, 2.1, 1],   # 初始經驗 1：大撞擊＋不動 -> 跌倒
    [1.5, 45.0, 0],  # 初始經驗 2：小撞擊＋大動 -> 安全
    [3.2, 55.0, 0],  # 初始經驗 3：大撞擊＋隨後繼續大動 -> 日常拍打或坐下
    [5.0, 1.2, 1]    # 初始經驗 4：超大撞擊＋完全不動 -> 嚴重跌倒
]

# 暫存最後一次傳進來的數據，等待人類給予反饋學習
last_raw_data = {"max_g": 0.0, "total_energy": 0.0}

# ==========================================
# 🏡 解決瀏覽器打開顯示 Not Found 的根目錄網頁
# ==========================================
@app.route("/")
def home():
    return """
    <div style="text-align: center; margin-top: 50px; font-family: Arial, sans-serif;">
        <h1 style="color: #2b5797;">🚨 智慧長照隨身防跌系統 ── 雲端大腦</h1>
        <p style="color: #555; font-size: 18px;">系統狀態：<span style="color: #107c41; font-weight: bold;">🟢 雲端常駐待命中 (Production Ready)</span></p>
        <p style="color: #888;">邊緣端 (ESP32) 特徵資料管線、SVM 機器學習模型與 LINE Bot API 已就緒。</p>
    </div>
    """

def train_and_predict(max_g, total_energy):
    """現場用記憶庫訓練一個 SVM AI 模型並進行預測"""
    X = np.array([data[:2] for data in memory_database]) # 特徵值矩阵
    y = np.array([data[2] for data in memory_database])  # 標籤答案
    
    # ───【✨ 解決困難 4：導入特徵標準化 (Feature Scaling)】───
    # 因為 Max_G (1~5) 與 Total_Energy (10~100) 尺度差了百倍，導致距離計算失準
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X) # 將特徵矩陣縮放至同一個常態分佈尺度
    new_data_scaled = scaler.transform([[max_g, total_energy]]) # 同步縮放新傳入的數據
    
    # ───【✨ 解決困難 5：修正類別不平衡 (Imbalanced Data)】───
    # 調整 C=1.0，並加入 class_weight='balanced'
    # 當日常安全樣本(0)遠多於跌倒(1)時，AI 會自動加大猜錯跌倒的懲罰權重，防止致命漏報！
    model = SVC(kernel='linear', C=1.0, class_weight='balanced')
    model.fit(X_scaled, y) # 讓 AI 現場學習標準化後的歷史記憶
    
    # 進行預測
    prediction = model.predict(new_data_scaled)
    return int(prediction[0])

def send_adaptive_line(text_msg, max_g, total_energy, is_sos=False):
    """發送帶有『互動式學習按鈕』的 LINE 訊息"""
    base_url = "https://finalai-4r3h.onrender.com"
    
    # 建立互動按鈕模板
    if is_sos:
        # 如果是主動求救，按鈕選項略有不同（不需要問 AI 判斷對不對，純確認或誤觸攔截）
        buttons_template = ButtonsTemplate(
            title="🚨 SOS 主動求助確認",
            text=f"長輩已按下隨身緊急按鈕求援！",
            actions=[
                URIAction(label="⭕ 已聯絡長輩/平安確認", uri=f"{base_url}/feedback?ans=correct"),
                URIAction(label="❌ 家屬註記：此為誤觸", uri=f"{base_url}/feedback?ans=0&g={max_g}&e={total_energy}")
            ]
        )
    else:
        # 正常 AI 跌倒偵測的反饋按鈕
        buttons_template = ButtonsTemplate(
            title="🧠 AI 跌倒自學習系統反饋",
            text=f"數據: {max_g:.1f}G / 能量: {total_energy:.1f}\n請問 AI 剛才判斷正確嗎？",
            actions=[
                URIAction(label="⭕ 判斷正確 (保持現狀)", uri=f"{base_url}/feedback?ans=correct"),
                URIAction(label="❌ 判斷錯誤！這是日常活動", uri=f"{base_url}/feedback?ans=0&g={max_g}&e={total_energy}"),
                URIAction(label="❌ 判斷錯誤！這是真跌倒", uri=f"{base_url}/feedback?ans=1&g={max_g}&e={total_energy}")
            ]
        )
    
    template_message = TemplateSendMessage(alt_text="AI 跌倒警報", template=buttons_template)

    for user_id in LINE_USER_IDS:
        if "YOUR_USER_ID" in user_id or user_id.strip() == "": continue
        try:
            line_bot_api.push_message(user_id, TextSendMessage(text=text_msg))
            line_bot_api.push_message(user_id, template_message)
        except Exception as e:
            print(f"❌ LINE 發送失敗: {e}")

# ==========================================
# 🌐 路由 1：接收 ESP32 的特徵數據 (AI預警 + SOS展望雙模態)
# ==========================================
@app.route("/predict", methods=["POST"])
def predict():
    global last_raw_data
    try:
        data = request.get_json()
        max_g = float(data.get("max_g", 0.0))
        total_energy = float(data.get("total_energy", 0.0))
        
        # ───【✨ 實現展望 4：雙模態主動求助(SOS)功能】───
        # 檢查封包內是否帶有 ESP32 長按按鈕強行送出的 "SOS_MANUAL" 狀態
        status = data.get("status", "AUTO")
        
        if status == "SOS_MANUAL":
            print("\n🚨 [🚨 收到硬體端長按指令] 長輩啟動主動求助模態 (SOS Panic Button)！")
            line_msg = f"🚨【⚠️ 最高緊急求助】\n長輩手動【長按隨身按鈕 3 秒】發出求救訊號！請立刻確認安全！"
            send_adaptive_line(line_msg, max_g, total_energy, is_sos=True)
            return jsonify({"status": "success", "decision": "SOS_MANUAL_TRIGGERED"})
        
        # ───【正常 AI 被動偵測模態】───
        last_raw_data = {"max_g": max_g, "total_energy": total_energy}
        
        # 🧠 丟給優化後的 SVM 機器學習模型進行即時訓練與幾何分類
        ai_result = train_and_predict(max_g, total_energy)
        
        print(f"\n🤖 [AI 進行線上學習分類] 當前記憶庫樣本數: {len(memory_database)}")
        
        if ai_result == 1:
            decision = "FALL_CONFIRMED"
            line_msg = f"🚨【緊急求救】\n機器學習 AI 判定長輩發生【真實跌倒】！(撞擊力:{max_g:.2f}G, 晃動能量:{total_energy:.2f})"
        else:
            decision = "NO_FALL"
            line_msg = f"🔵【平安提醒】\n機器學習 AI 自動攔截本次撞擊，判定為【日常行為】。(撞擊力:{max_g:.2f}G, 晃動能量:{total_energy:.2f})"

        print(f"🎯 AI 決策結果: {decision}")
        
        # 發送 LINE 及自學習按鈕
        send_adaptive_line(line_msg, max_g, total_energy, is_sos=False)
        
        return jsonify({"status": "success", "decision": decision})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# 🌐 路由 2：接收來自 LINE 按鈕的人類學習反饋 (Learning Loop)
# ==========================================
@app.route("/feedback", methods=["GET"])
def feedback():
    ans = request.args.get("ans")
    
    if ans == "correct":
        return "<h3>🎉 謝謝反饋！AI 模型表現良好，將繼續保持！</h3>"
    
    try:
        g = float(request.args.get("g"))
        e = float(request.args.get("e"))
        correct_label = int(ans) # 0 代表安全，1 代表跌倒
        
        # 🎯 進化：把這筆由人類專家(家屬)標註的新經驗，永久塞進記憶庫！
        memory_database.append([g, e, correct_label])
        
        print(f"\n📈 [AI 完成自主學習！] 新增經驗 -> G:{g}, 能量:{e}, 標籤:{correct_label}")
        print(f"📊 當前總記憶樣本數增長至: {len(memory_database)} 筆")
        
        return f"<h3>🧠 AI 已成功將此案例學進大腦！(當前記憶庫共有 {len(memory_database)} 筆經驗)</h3><p>下次遇到類似動態，決策超平面（Hyperplane）將自動修正！</p>"
    except Exception as e:
        return f"<h3>❌ 學習失敗: {e}</h3>", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)