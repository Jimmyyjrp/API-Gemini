from google import genai
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage
from flask import Flask, request, abort
from linebot.models import FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent, TextComponent, URIAction


# LINE API Access Token และ Channel Secret
CHANNEL_ACCESS_TOKEN = 'rLoSpWjE4tJlrvLQXZN1ki7c9oWmvjJ+jNrtEnp7h80oh4D3GauvvdIOug9fEDeLbx7opxXfRBVmsxS57K2eh2tITggJuBJ5XxhNFLMumNK/pkaxfxZ7mh7o20pWMixtdK2IcqvHAioxIMrpRrHj7wdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'fff648004304c3a6bcde6c056eecd810'

# สร้าง client สำหรับเชื่อมต่อกับ Gemini API
client = genai.Client(api_key="AIzaSyCMra2j44ztGyuTP8MzkJirs1TFtzuHpmo")

# สร้าง LineBotApi และ WebhookHandler
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# สร้าง Flask app
app = Flask(__name__)

# ฟังก์ชันหลักในการใช้ Gemini API
def generate_answer(user_message):
    prompt = f"""
คุณคือ Seishiro Nagi ผู้เป็นคำแนะนำด้านการหาการ์ตูน อนิเมะ และเพลงประกอบอนิเมะ
คุณเป็นผู้เชี่ยวชาญที่มีความรู้ลึกซึ้งเกี่ยวกับเนื้อเรื่อง คาแรคเตอร์ เพลง และธีมต่าง ๆ ของอนิเมะ

หน้าที่ของคุณคือ:
1. วิเคราะห์ข้อความจากผู้ใช้ ว่าเกี่ยวข้องกับแนวเรื่อง โทน ฉากหลัง คาแรคเตอร์ เพลง หรือศิลปิน
2. แนะนำอนิเมะหรือเพลงที่ตรงกับข้อความนั้นให้แม่นยำที่สุด
3. ถ้าไม่แน่ใจ ให้คาดเดาอย่างมีเหตุผล และอธิบายให้เข้าใจง่าย

ตัวอย่างข้อมูลที่อาจเกี่ยวข้อง:
- แนวเรื่อง: แอ็กชัน, โรแมนติก, คอมเมดี้, แฟนตาซี ฯลฯ
- โทนเรื่อง: สดใส, อบอุ่นใจ, เศร้า, ดาร์ก, ตื่นเต้น
- ธีมหรือฉากหลัง: โรงเรียน, ต่างโลก, ยุคโบราณ, อนาคต
- ตัวละคร: เช่น พระเอกผมทอง, นางเอกผมสีฟ้า, คนใส่แว่น ฯลฯ
- เพลง: ท่อนเพลง, อารมณ์เพลง
- ศิลปิน: เช่น LiSA, Aimer, YOASOBI ฯลฯ

**รูปแบบคำตอบที่ต้องการ (สำหรับใช้ใน LINE Bot):**
1. [TH] คำอธิบายภาษาไทย
2. [EN] คำแปลภาษาอังกฤษ
3. Anime Title: ชื่ออนิเมะ
4. Image URL: ลิงก์ภาพโปสเตอร์
5. Watch URL: ลิงก์ดูอนิเมะออนไลน์ (ถ้ามี)

ข้อความจากผู้ใช้: “{user_message}”

กรุณาตอบตามรูปแบบนี้เท่านั้น
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt]
    )
    return response.text


# ฟังก์ชันจัดการข้อความที่ได้รับจากผู้ใช้
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id  # ได้ User ID ของผู้ใช้

    print(f"Received message: {user_message} from {user_id}")

    # ส่งข้อความที่ผู้ใช้ถามไปยัง Gemini API เพื่อขอคำตอบ
    answer = generate_answer(user_message)
    
    # ส่งคำตอบกลับไปยังผู้ใช้ใน LINE
    response_message = f"คำถาม: {user_message}\nคำตอบ: {answer}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message))

# Webhook URL สำหรับรับข้อความจาก LINE
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Error:", e)
        abort(400)

    return 'OK'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
