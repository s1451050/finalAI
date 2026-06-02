import time
from flask import Flask, request, jsonify
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)

# ==========================================
# ⚙️ LINE Message API 群發設定區 (請填入金鑰與多個 ID)
# ==========================================
LINE_CHANNEL_ACCESS_TOKEN = "aOFBFW9fEErWeF2rK55QwntCJZuFKLHaPYAvR8uCSqzGoAUDZcuNQrwka3VbLjxBPh/xvDJE459guzQqIw35mQWPYK/FwiIY0f7q2gj2aybNzmZHcVn1V9TvZhtXolO1G9dpMXT1qm2PMGua4MwaJwdB04t89/1O/w1cDnyilFU="

# 🎯 在這裡填入所有要接收通知的家人 User ID（最多可以放 500 個喔！）
LINE_USER_IDS = [
    "Uf2a00cc3b73a9c4bd34d8dcd8115511a",  # Uf2a00cc3b73a9c4bd34d8dcd8115511a
]

try:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    print(f"ℹ️ [LINE 設定] 群發模組載入成功！目前設定接收人數：{len(LINE_USER_IDS)} 人")
except Exception as e:
    print(f"⚠️ [LINE 警告] LINE 模組初始化失敗: {e}")


def send_line_message(text_msg):
    """【群發專用】同時發送訊息給清單中的所有人"""
    try:
        # 將原本的 push_message 改為 multicast
        line_bot_api.multicast(LINE_USER_IDS, TextSendMessage(text=text_msg))
        print(f"📩 [LINE 群發成功] 已同時推播給 {len(LINE_USER_IDS)} 位家人！")
    except Exception as e:
        print(f"❌ [LINE 群發失敗] 錯誤原因: {e}")


# ==========================================
# 後面的 @app.route("/predict", methods=["POST"]) 以下程式碼完全不用變動
# ==========================================
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        total_energy = data.get("total_energy", 0.0)
        max_g = data.get("max_g", 0.0)

        print("\n" + "=" * 50)
        print(f"📊 [收到硬體端數據] 最大衝擊力 Max G: {max_g:.2f} G")
        print(f"📊 特徵工程指標 - 累積晃動總能量積分: {total_energy:.2f}")

        if total_energy < 20.0:
            decision = "FALL_CONFIRMED"
            alert_title = "🚨【緊急求救：真摔倒致昏迷】"
            log_msg = "🚨 AI 最終決策結果：【 確定跌倒！長輩可能失去意識！ 】"
            line_msg = f"{alert_title}\n雲端 AI 確診為真實摔倒！長輩撞擊後失去意識，晃動特徵極低({total_energy:.1f})，請立刻前往確認！"
        else:
            decision = "NO_FALL"
            alert_title = "🔵【日常動態提醒：安全攔截】"
            log_msg = "🔵 AI 最終決策結果：【 日常行為噪訊，已自動攔截 】"
            line_msg = f"{alert_title}\n檢測到撞擊({max_g:.1f}G)，但 AI 分析長輩隨後仍有持續活動特徵({total_energy:.1f})，判定為安全日常行為，已解除警報。"

        print(log_msg)
        print("=" * 50)

        # 呼叫群發功能
        send_line_message(line_msg)

        return jsonify({"status": "success", "decision": decision, "total_energy": total_energy})

    except Exception as e:
        print(f"❌ 伺服器處理錯誤: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    print("\n🚀 [系統啟動] 智慧長者防誤報跌倒偵測——端雲協同 AI 伺服器已上線！")
    print("📍 正在監聽區域網路所有連線，通訊埠: 5000")
    app.run(host="0.0.0.0", port=5000, debug=False)