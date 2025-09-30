import requests
import random
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import textwrap
from apscheduler.schedulers.blocking import BlockingScheduler
import pytz
from dotenv import load_dotenv
import json

# ----------------------------
# Load Environment Variables
# ----------------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# ----------------------------
# Path for logging
# ----------------------------
LOG_FILE = r"C:\Me\Learning\Python\happyclub\quotes_log.txt"
POST_COUNT_FILE = r"C:\Me\Learning\Python\happyclub\post_count.txt"

# ----------------------------
# Get and update post count
# ----------------------------
def get_post_count():
    if not os.path.exists(POST_COUNT_FILE):
        return 0
    with open(POST_COUNT_FILE, "r") as f:
        return int(f.read().strip())

def update_post_count(count):
    with open(POST_COUNT_FILE, "w") as f:
        f.write(str(count))

# ----------------------------
# APIs for Quotes (min 7 words)
# ----------------------------
def get_random_quote(min_words=7):
    apis = ["zen", "favqs", "quotable"]
    for _ in range(5):
        choice = random.choice(apis)
        try:
            if choice == "zen":
                data = requests.get("https://zenquotes.io/api/random", timeout=10).json()[0]
                quote = f'"{data["q"]}" — {data["a"]}'
            elif choice == "favqs":
                data = requests.get("https://favqs.com/api/qotd", timeout=10).json()
                quote = f'"{data["quote"]["body"]}" — {data["quote"]["author"]}'
            elif choice == "quotable":
                data = requests.get("https://api.quotable.io/random", timeout=10).json()
                quote = f'"{data["content"]}" — {data["author"]}'
            else:
                continue

            if len(quote.split()) >= min_words:
                return quote
        except:
            continue
    return "Stay motivated! 💪"

# ----------------------------
# Logging
# ----------------------------
def log_quote(quote):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(quote + "\n")

def is_duplicate(quote):
    if not os.path.exists(LOG_FILE):
        return False
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return quote in f.read()

# ----------------------------
# Generate Quote Image + Watermark
# ----------------------------
def create_quote_image(text):
    bg_colors = [(25,25,25), (40, 90, 150), (120, 20, 60), (50,150,100), (180,120,40)]
    bg_color = random.choice(bg_colors)
    img = Image.new("RGB", (800, 600), color=bg_color)
    draw = ImageDraw.Draw(img)

    fonts = ["arial.ttf", "times.ttf", "calibri.ttf"]
    font_size = 60
    try:
        font = ImageFont.truetype(random.choice(fonts), font_size)
    except:
        font = ImageFont.load_default()
        font_size = 20

    wrapped_text = textwrap.fill(text, width=30)

    MIN_FONT_SIZE = 30
    while True:
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
        text_height = bbox[3] - bbox[1]
        if text_height < img.height * 0.8 or font_size <= MIN_FONT_SIZE:
            break
        font_size -= 2
        try:
            font = ImageFont.truetype(random.choice(fonts), font_size)
        except:
            font = ImageFont.load_default()

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (img.width - text_width) / 2
    y = (img.height - text_height) / 2

    draw.multiline_text((x, y), wrapped_text, font=font, fill="white", align="center")

    # Add watermark @rajat0323
    watermark_text = "@rajat0323"
    try:
        watermark_font = ImageFont.truetype("arial.ttf", 25)
    except:
        watermark_font = ImageFont.load_default()
    bbox_w = draw.textbbox((0,0), watermark_text, font=watermark_font)
    w_width = bbox_w[2] - bbox_w[0]
    w_height = bbox_w[3] - bbox_w[1]
    draw.text((img.width - w_width - 20, img.height - w_height - 20),
              watermark_text, font=watermark_font, fill=(200,200,200))

    filename = f"quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(filename)
    return filename

# ----------------------------
# Send Photo to Telegram
# ----------------------------
def send_photo(filename, caption="✨ Daily Motivation ✨"):
    hashtags = "#Motivation #Inspiration #DailyQuotes #Success #Mindset"
    caption = f"{caption}\n\n{hashtags}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(filename, "rb") as photo:
        payload = {"chat_id": CHANNEL_ID, "caption": caption}
        files = {"photo": photo}
        response = requests.post(url, data=payload, files=files)
        print("Telegram response:", response.json())

# ----------------------------
# Send Poll (anonymous for channel)
# ----------------------------
def send_poll(question, options):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"
    payload = {
        "chat_id": CHANNEL_ID,
        "question": question,
        "options": json.dumps(options),
        "is_anonymous": True  # must be True for channel
    }
    response = requests.post(url, data=payload)
    print("Poll response:", response.json())

# ----------------------------
# Main Function
# ----------------------------
def post_quote():
    count = get_post_count() + 1
    update_post_count(count)

    # Every 5th post -> send poll
    if count % 5 == 0:
        question = "Which type of quotes do you like the most?"
        options = ["Motivational", "Success", "Life Lessons", "Funny"]
        send_poll(question, options)
        print(f"Post {count}: Sent poll!")
        return

    # Regular quote post
    quote = get_random_quote()
    if is_duplicate(quote):
        print("⚠️ Duplicate quote, skipping...")
        return

    print(f"Post {count} Quote:", quote)
    filename = create_quote_image(quote)
    caption = f"{quote}\n✨ Share this with your friends! ✨"
    send_photo(filename, caption)
    log_quote(quote)
    os.remove(filename)

# ----------------------------
# Scheduler
# ----------------------------
if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone=pytz.timezone("Asia/Kolkata"))
    scheduler.add_job(post_quote, "interval", hours=3)  # every 3 hours
    print("Quote bot started...")
    scheduler.start()
