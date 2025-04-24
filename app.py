from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage
from google.generativeai import GenerativeModel
import google.generativeai as genai
import re

# LINE API Access Token และ Channel Secret
CHANNEL_ACCESS_TOKEN = 'rLoSpWjE4tJlrvLQXZN1ki7c9oWmvjJ+jNrtEnp7h80oh4D3GauvvdIOug9fEDeLbx7opxXfRBVmsxS57K2eh2tITggJuBJ5XxhNFLMumNK/pkaxfxZ7mh7o20pWMixtdK2IcqvHAioxIMrpRrHj7wdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'fff648004304c3a6bcde6c056eecd810'

# สร้าง client สำหรับเชื่อมต่อ Gemini
genai.configure(api_key="AIzaSyCMra2j44ztGyuTP8MzkJirs1TFtzuHpmo")
model = genai.GenerativeModel("gemini-2.0-flash")

# LINE Bot API
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Flask app
app = Flask(__name__)

# ฟังก์ชันเรียก Gemini
def generate_answer(user_message):
    prompt = f"""
คุณคือผู้เชี่ยวชาญ เพื่อนสนิทที่รักการดูอนิเมะและฟังเพลงอนิเมะมาก ๆ  
คุณพูดจาเป็นกันเอง น่ารัก และให้คำแนะนำเหมือนคุยกับเพื่อน ไม่เป็นทางการจนเกินไป  
เวลาผู้ใช้ถามหาอนิเมะหรือเพลง ช่วยแนะนำด้วยภาษาที่อบอุ่น ขี้เล่น เหมือนแชร์สิ่งที่ชอบให้เพื่อนฟัง  
ใส่อีโมจิหรือคำอุทานบ้างก็ได้ตามธรรมชาติ (แต่ไม่เยอะจนรกนะ)

ถ้าผู้ใช้ถามว่า "มีเรื่องอื่นมั้ย", "อีกเรื่องหนึ่ง", "ขออีก", ฯลฯ  
ให้เข้าใจว่าเขาต้องการอนิเมะแนะนำเพิ่มจากเรื่องก่อนหน้า  
ช่วยแนะนำเรื่องใหม่ที่น่าจะถูกใจในโทนเดียวกัน พร้อมเล่าแบบกันเองว่าเพราะอะไรถึงน่าดู 

และใช้คำแนะนำคำอธิบายที่สั้นกระชับ และเข้าใจง่าย
ตัวอย่างคำตอบที่ดี:
- “โอ้ยย ถ้าชอบเรื่องนี้ เดี๋ยวต้องโดนเรื่องนี้แน่เลย 💥”
- “เอาจริง เพลงเปิดอย่างปังอ่ะ ฟังแล้วขนลุก!”
- “เรื่องนี้คืออบอุ่นหัวใจมาก ๆ ดูแล้วน้ำตาคลออะเพื่อน 🥹”

กรุณาตอบเป็นภาษาไทย พร้อมข้อมูลต่อไปนี้:
ถ้าเป็นอนิเมะ: ชื่อเรื่อง, แนว, ปี, เหตุผล, และลิงก์ (เช่น MyAnimeList ถ้าเดาได้)
ถ้าเป็นเพลง: ชื่อเพลง, ศิลปิน, จากเรื่องอะไร, อารมณ์เพลง, เหตุผลที่แนะนำ
ถ้าไม่แน่ใจ: อธิบายเหตุผลให้เข้าใจง่าย และขอโทษแบบน่ารัก ๆ

ข้อความจากผู้ใช้: “{user_message}”
"""
    response = model.generate_content(prompt)
    return response.text.strip()

# ฟังก์ชันจัดการข้อความ
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id

    # คำแนวจีบ
    flirting_keywords = [
        "มีแฟนยัง", "คุณมีแฟนยัง", "จีบได้ไหม", "จีบได้มั้ย", "โสดไหม", "แฟนยัง", 
        "ตกหลุมรัก", "คุณน่ารัก", "ชอบคุณ", "ชอบบอท", "บอทน่ารัก", "จีบบอท"
    ]
    if any(keyword in user_message.lower() for keyword in flirting_keywords):
        reply = "มีแล้วน่ะ ชื่อเรโอะ จีบไม่ได้ แต่ถ้าเป็นเรื่องที่เกี่ยวกับการ์ตูนหรืออนิเมะ ถามมาได้ตลอดเลยนะ~"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # เรียก Gemini
    answer = generate_answer(user_message)

    # ทำความสะอาดข้อความ
    clean_answer = re.sub(r"\*+", "", answer)
    clean_answer = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1\n\2", clean_answer)
    clean_answer = clean_answer.replace("ชื่อเรื่อง:", "🎬 ชื่อเรื่อง:")
    clean_answer = clean_answer.replace("แนว:", "🧭 แนว:")
    clean_answer = clean_answer.replace("ปี:", "📅 ปี:")
    clean_answer = clean_answer.replace("เหตุผล:", "❤️ เหตุผล:")
    clean_answer = clean_answer.replace("ลิงก์:", "🔗 ลิงก์:")

    # ส่งข้อความกลับ
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=clean_answer))

# Webhook
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Error: {e}")
        abort(400)
    return 'OK'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
