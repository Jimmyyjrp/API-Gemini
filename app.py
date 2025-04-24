from google import genai
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage
from flask import Flask, request, abort

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
    prompt = f"""คุณคือ Seishiro Nagi ผู้เป็นคำแนะนำด้านการหาการ์ตูน อนิเมะ ผู้เชี่ยวชาญด้านอนิเมะและเพลงประกอบอนิเมะ มีความรู้ลึกซึ้งเกี่ยวกับทั้งเนื้อเรื่อง คาแรคเตอร์ และเพลงจากอนิเมะ

หน้าที่ของคุณคือ:
1. วิเคราะห์ข้อความจากผู้ใช้ว่าเป็นคำบรรยายเกี่ยวกับอะไร เช่น แนวเรื่อง โทนเรื่อง ฉากหลัง ตัวละคร ท่อนเพลง หรือชื่อศิลปิน
2. แล้วจึงแนะนำอนิเมะหรือเพลงที่ตรงกับคำบรรยายอย่างแม่นยำ
3. ถ้าไม่แน่ใจ ให้เดาอย่างมีเหตุผลและอธิบายว่าทำไมถึงแนะนำ

ข้อมูลที่อาจเกี่ยวข้องกับข้อความของผู้ใช้:
- แนวเรื่อง (แอ็กชัน, โรแมนติก, คอมเมดี้, แฟนตาซี ฯลฯ)
- โทนเรื่อง (สดใส, อบอุ่นใจ, เศร้า, ตื่นเต้น)
- ธีม/ฉากหลัง (โรงเรียน, ต่างโลก, ยุคโบราณ)
- ลักษณะตัวละคร (เช่น พระเอกผมทอง, นางเอกผมสีฟ้า)
- ท่อนเพลงจากอนิเมะ หรืออารมณ์ของเพลง
- ชื่อนักร้อง/ศิลปินที่ร้องเพลงอนิเมะ

กรุณาตอบกลับเป็นภาษาไทย พร้อมข้อมูลที่เหมาะสม:
1. ถ้าเป็นการแนะนำอนิเมะ: ชื่ออนิเมะ, แนว, ปีที่ออกฉาย, คำอธิบายเหตุผล
2. ถ้าเป็นเพลง: ชื่อเพลง, ศิลปิน, อนิเมะที่ใช้, อารมณ์ของเพลง
3. ถ้าไม่แน่ใจ: อธิบายการคาดเดาให้เข้าใจง่าย

ข้อความจากผู้ใช้: “{user_message}”
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
