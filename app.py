from google import genai
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage
from flask import Flask, request, abort
from linebot.models import FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent, TextComponent, URIAction
import re


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
คุณคือผู้เชี่ยวชาญ เพื่อนสนิทที่รักการดูอนิเมะและฟังเพลงอนิเมะมาก ๆ  
คุณพูดจาเป็นกันเอง น่ารัก และให้คำแนะนำเหมือนคุยกับเพื่อน ไม่เป็นทางการจนเกินไป  
เวลาผู้ใช้ถามหาอนิเมะหรือเพลง ช่วยแนะนำด้วยภาษาที่อบอุ่น ขี้เล่น เหมือนแชร์สิ่งที่ชอบให้เพื่อนฟัง  
ใส่อีโมจิหรือคำอุทานบ้างก็ได้ตามธรรมชาติ (แต่ไม่เยอะจนรกนะ) 

คุณคือผู้ช่วยแนะนำอนิเมะตามความต้องการของผู้ใช้ เช่น แนวเรื่อง อารมณ์ ตัวละคร หรือคำอธิบายสั้น ๆ  
งานของคุณคือแนะนำอนิเมะที่ตรงกับคำขอ โดยใช้สำนวนสนุก อารมณ์ดี และเป็นกันเอง

หลีกเลี่ยงการแนะนำอนิเมะเรื่องเดิมซ้ำที่เคยแนะำไปแล้ว (ถ้ามีการแนะนำไปแล้วในบทสนทนานี้)
พยายามเลือกอนิเมะที่หลากหลาย: ต่างปี ต่างสตูดิโอ หรือมีโทน/เนื้อหาที่หลากหลาย
ถ้าผู้ใช้ไม่ได้ระบุแนวเรื่อง ให้คุณช่วยแนะนำหลายแนว (2-3 แนวที่น่าจะโดนใจ)
ถ้าผู้ใช้พิมพ์ว่า "ขออีกเรื่อง", "อีกเรื่องหนึ่ง", หรือ "มีอีกไหม" → ให้คุณแนะนำเรื่องใหม่ในแนวเดียวกันแต่ไม่ซ้ำ

สิ่งที่ต้องทำ
แนะนำเรื่องใหม่ ห้ามซ้ำกับรายการด้านบน
 

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
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt]
    )
    return response.text


# ฟังก์ชันจัดการข้อความที่ได้รับจากผู้ใช้
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id

    print(f"Received message: {user_message} from {user_id}")

    # คำแนวจีบ
    flirting_keywords = [
        "มีแฟนยัง", "คุณมีแฟนยัง", "จีบได้ไหม", "จีบได้มั้ย", "โสดไหม", "แฟนยัง", 
        "ตกหลุมรัก", "คุณน่ารัก", "ชอบคุณ", "ชอบบอท", "บอทน่ารัก", "จีบบอท"
    ]

    if any(keyword in user_message.lower() for keyword in flirting_keywords):
        cute_reply = "มีแล้วน่ะ ชื่อเรโอะ จีบไม่ได้ แต่ถ้าเป็นเรื่องที่เกี่ยวกับการ์ตูนหรืออนิเมะ สามารถถามได้ตลอดเลยครับผม"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=cute_reply))
        return

    # ส่งข้อความไปหา Gemini API
    answer = generate_answer(user_message)

    # ลบ Markdown ที่ไม่จำเป็น
    clean_answer = re.sub(r"\*+", "", answer)
    clean_answer = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1\n\2", clean_answer)

    # แทนหัวข้อด้วยอีโมจิน่ารัก ๆ (ทั้งอนิเมะและเพลง)
    clean_answer = re.sub(r"[^\S\r\n]*ชื่อ[ ]?เรื่อง[ ]*:[^\S\r\n]*", "🎬 ชื่อเรื่อง: ", clean_answer, flags=re.IGNORECASE)
    clean_answer = re.sub(r"[^\S\r\n]*แนว[ ]*:[^\S\r\n]*", "🧭 แนว: ", clean_answer, flags=re.IGNORECASE)
    clean_answer = re.sub(r"[^\S\r\n]*ปี[ ]*:[^\S\r\n]*", "📅 ปี: ", clean_answer, flags=re.IGNORECASE)
    clean_answer = re.sub(r"[^\S\r\n]*เหตุผล[ ]*:[^\S\r\n]*", "❤️ เหตุผล: ", clean_answer, flags=re.IGNORECASE)
    clean_answer = re.sub(r"[^\S\r\n]*ลิงก์[ ]*:[^\S\r\n]*", "🔗 ลิงก์: ", clean_answer, flags=re.IGNORECASE)
    clean_answer = re.sub(r"[^\S\r\n]*ชื่อ[ ]?เพลง[ ]*:[^\S\r\n]*", "🎶 ชื่อเพลง: ", clean_answer, flags=re.IGNORECASE)
    clean_answer = re.sub(r"[^\S\r\n]*ศิลปิน[ ]*:[^\S\r\n]*", "🎤 ศิลปิน: ", clean_answer, flags=re.IGNORECASE)
    clean_answer = re.sub(r"[^\S\r\n]*จากเรื่อง[ ]*:[^\S\r\n]*", "🎬 จากเรื่อง: ", clean_answer, flags=re.IGNORECASE)
    clean_answer = re.sub(r"[^\S\r\n]*อารมณ์[ ]?เพลง[ ]*:[^\S\r\n]*", "🎧 อารมณ์เพลง: ", clean_answer, flags=re.IGNORECASE)

    # ส่งกลับไปยัง LINE
    response_message = f"{clean_answer}"
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
