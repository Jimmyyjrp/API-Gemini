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
คุณคือผู้เชี่ยวชาญด้านอนิเมะและเพลงประกอบอนิเมะ มีความรู้ลึกซึ้งเกี่ยวกับทั้งเนื้อเรื่อง คาแรคเตอร์ ตัวละคร และเพลงจากอนิเมะ

โปรดแนะนำอนิเมะอีกหนึ่งเรื่องที่คิดว่าผู้ใช้อาจชอบ อธิบายว่าอนิเมะนั้นมีแนวอะไร, จุดเด่นคืออะไร, และทำไมถึงคิดว่าเหมาะกับการแนะนำในบริบทนี้

ข้อมูลที่อาจเกี่ยวข้องกับข้อความของผู้ใช้:
- แนวเรื่อง (แอ็กชัน, โรแมนติก, คอมเมดี้, แฟนตาซี ฯลฯ)
- โทนเรื่อง (สดใส, อบอุ่นใจ, เศร้า, ตื่นเต้น)
- ธีม/ฉากหลัง (โรงเรียน, ต่างโลก, ยุคโบราณ)
- ลักษณะตัวละคร (เช่น พระเอกผมทอง, นางเอกผมสีฟ้า)
- ท่อนเพลงจากอนิเมะ หรืออารมณ์ของเพลง
- ชื่อนักร้อง/ศิลปินที่ร้องเพลงอนิเมะ

หากผู้ใช้ส่งข้อความสั้น ๆ เช่น "มีเรื่องอื่นมั้ย", "อีกเรื่องหนึ่ง", "ขออีก", หรือข้อความต่อเนื่องในลักษณะนี้
กรุณาเข้าใจว่านี่คือการถามต่อจากคำแนะนำอนิเมะก่อนหน้านี้
และผู้ใช้ต้องการ "อนิเมะอีกเรื่องหนึ่ง" ที่มีแนวใกล้เคียง หรือให้ความรู้สึกที่คล้ายกับเรื่องที่แนะนำไปก่อนหน้า


**โปรดแนบลิงก์ข้อมูลของอนิเมะนั้นด้วย เช่น ลิงก์ไปยัง MyAnimeList หรือ AniList เพื่อให้ผู้ใช้สามารถค้นหาต่อได้ทันที**


กรุณาตอบกลับเป็นภาษาไทย พร้อมข้อมูลที่เหมาะสม:
ถ้าเป็นการแนะนำอนิเมะ: ชื่ออนิเมะ, แนว, ปีที่ออกฉาย, คำอธิบายเหตุผล
ถ้าเป็นเพลง: ชื่อเพลง, ศิลปิน, อนิเมะที่ใช้, อารมณ์ของเพลง
ถ้าไม่แน่ใจ: อธิบายการคาดเดาให้เข้าใจง่าย

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
    response_message = f"คำถาม : {user_message}\n {answer}"
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
