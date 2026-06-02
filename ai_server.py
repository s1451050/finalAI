import os
from flask import Flask, request, jsonify
from linebot import LineBotApi
from linebot.models import TextSendMessage, URIAction, ButtonsTemplate, TemplateSendMessage
import numpy as np
from sklearn.svm import SVC

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

def train_and_predict(max_g, total_energy):
    """現場用記憶庫訓練一個 SVM AI 模型並進行預測"""
    X = np.array([data[:2] for data in memory_database]) # 特徵值
    y = np.array([data[2] for data in memory_database])  # 標籤答案
    
    # 初始化一個支援向量機 (SVM)
    model = SVC(kernel='linear', C=1.0)
    model.fit(X, y) # 讓 AI 現場學習現有的記憶
    
    # 進行預測
    prediction = model.predict([[max_g, total_energy]])
    return int(prediction[0])

def send_adaptive_line(text_msg, max_g, total_energy):
    """發送帶有『互動式學習按鈕』的 LINE 訊息"""
    # 取得當前 Render 的公网基本網址 (自動抓取或手動填寫)
    base_url = "https://finalai-4r3h.onrender.com"
    
    # 建立互動按鈕，讓人類教導 AI
    buttons_template = ButtonsTemplate(
        title="🧠 AI 跌倒自學習系統反馈",
        text=f"數據: {max_g:.1f}G / 能量:{total_energy:.1f}\n請問 AI 剛才判斷正確嗎？",
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
            # 發送文字警報
            line_bot_api.push_message(user_id, TextSendMessage(text=text_msg))
            # 發送機器學習反饋按鈕
            line_bot_api.push_message(user_id, template_message)
        except Exception as e:
            print(f"❌ LINE 發送失敗: {e}")

# ==========================================
# 🌐 路由 1：接收 ESP32 的特徵數據
# ==========================================
@app.route("/predict", methods=["POST"])
def predict():
    global last_raw_data
    try:
        data = request.get_json()
        max_g = float(data.get("max_g", 0.0))
        total_energy = float(data.get("total_energy", 0.0))
        
        last_raw_data = {"max_g": max_g, "total_energy": total_energy}
        
        # 🧠 丟給 SVM 機器學習模型進行即時訓練與分類
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
        send_adaptive_line(line_msg, max_g, total_energy)
        
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
        # 取得剛才點擊按鈕時傳過來的數據與正確答案
        g = float(request.args.get("g"))
        e = float(request.args.get("e"))
        correct_label = int(ans) # 0 代表安全，1 代表跌倒
        
        # 🎯 進化：把這筆新經驗塞進記憶庫！
        memory_database.append([g, e, correct_label])
        
        print(f"\n📈 [AI 完成自主學習！] 新增經驗 -> G:{g}, 能量:{e}, 標籤:{correct_label}")
        print(f"📊 當前總記憶樣本數增長至: {len(memory_database)} 筆")
        
        return f"<h3>🧠 AI 已成功將此案例學進大腦！(當前記憶庫共有 {len(memory_database)} 筆經驗)</h3><p>下次遇到類似動態，AI 將做出更精準的判斷！</p>"
    except Exception as e:
        return f"<h3>❌ 學習失敗: {e}</h3>", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)