from google import genai
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage, FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent, TextComponent, URIAction
from flask import Flask, request, abort
import re
import json


# LINE API Access Token และ Channel Secret
CHANNEL_ACCESS_TOKEN = 'rLoSpWjE4tJlrvLQXZN1ki7c9oWmvjJ+jNrtEnp7h80oh4D3GauvvdIOug9fEDeLbx7opxXfRBVmsxS57K2eh2tITggJuBJ5XxhNFLMumNK/pkaxfxZ7mh7o20pWMixtdK2IcqvHAioxIMrpRrHj7wdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'fff648004304c3a6bcde6c056eecd810'

# สร้าง client สำหรับเชื่อมต่อกับ Gemini API
client = genai.Client(api_key="YOUR_GEMINI_API_KEY")

# สร้าง LineBotApi และ WebhookHandler
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# สร้าง Flask app
app = Flask(__name__)

# ฟังก์ชันหลักในการใช้ Gemini API

def generate_song_json(user_message):
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
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt]
    )
    try:
        return json.loads(response.text.strip().replace("\"""", ''))
    except:
        return None

# สร้าง Flex Message แบบโปสเตอร์เพลง

def create_song_flex(song_data):
    bubble = BubbleContainer(
        hero=ImageComponent(
            url=song_data["image_url"],
            size="full",
            aspect_ratio="20:13",
            aspect_mode="cover",
            action=URIAction(uri=song_data["youtube_url"], label="เปิดเพลง")
        ),
        body=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(text=song_data["title"], weight="bold", size="lg"),
                TextComponent(text=f"ศิลปิน: {song_data['artist']}", size="sm"),
                TextComponent(text=f"จาก: {song_data['anime']}", size="sm"),
                TextComponent(text=f"🎧 อารมณ์: {song_data['mood']}", size="sm"),
                TextComponent(text=f"❤️ {song_data['reason']}", wrap=True, size="sm"),
            ]
        ),
        footer=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(
                    text="▶ ไปฟังเพลง", color="#1DB446", size="sm",
                    action=URIAction(uri=song_data["youtube_url"], label="ฟังเพลง")
                )
            ]
        )
    )
    return FlexSendMessage(alt_text=song_data["title"], contents=bubble)

# คำแนวจีบ
flirting_keywords = [
    "มีแฟนยัง", "คุณมีแฟนยัง", "จีบได้ไหม", "จีบได้มั้ย", "โสดไหม", "แฟนยัง",
    "ตกหลุมรัก", "คุณน่ารัก", "ชอบคุณ", "ชอบบอท", "บอทน่ารัก", "จีบบอท"
]

# ฟังก์ชันจัดการข้อความที่ได้รับจากผู้ใช้
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id
    print(f"Received message: {user_message} from {user_id}")

    if any(keyword in user_message.lower() for keyword in flirting_keywords):
        cute_reply = "มีแล้วน่ะ ชื่อเรโอะ จีบไม่ได้ แต่ถ้าเป็นเรื่องที่เกี่ยวกับการ์ตูนหรืออนิเมะ สามารถถามได้ตลอดเลยครับผม"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=cute_reply))
        return

    song_data = generate_song_json(user_message)

    if song_data:
        flex_msg = create_song_flex(song_data)
        line_bot_api.reply_message(event.reply_token, flex_msg)
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="แงง ขอโทษนะ เราหาข้อมูลเพลงไม่ได้เลย 😢 ลองถามใหม่น้า~"))

# Webhook URL
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
