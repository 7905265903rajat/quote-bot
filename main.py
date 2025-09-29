import requests
import random
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import textwrap
from apscheduler.schedulers.blocking import BlockingScheduler
import pytz
from dotenv import load_dotenv

# ----------------------------
# Load Environment Variables
# ----------------------------
load_dotenv()  # reads .env file
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# ----------------------------
# Path for logging
# ----------------------------
LOG_FILE = r"C:\Me\Learning\Python\happyclub\quotes_log.txt"

# ----------------------------
# APIs for Quotes
# ----------------------------
def get_random_quote():
    apis = ["zen", "favqs", "quotable"]
    choice = random.choice(apis)

    try:
        if choice == "zen":
            data = requests.get("https://zenquotes.io/api/random", timeout=10).json()[0]
            return f'"{data["q"]}" — {data["a"]}'

        elif choice == "favqs":
            data = requests.get("https://favqs.com/api/qotd", timeout=10).json()
            return f'"{data["quote"]["body"]}" — {data["quote"]["author"]}'

        elif choice == "quotable":
            data = requests.get("https://api.quotable.io/random", timeout=10).json()
            return f'"{data["content"]}" — {data["author"]}'
    except:
        return "Stay motivated! 💪"

# ----------------------------
# Logging to avoid repeats
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
# Generate Image with Quote (Larger Text)
# ----------------------------
def create_quote_image(text):
    # Random background color
    bg_colors = [(25,25,25), (40, 90, 150), (120, 20, 60), (50,150,100), (180,120,40)]
    bg_color = random.choice(bg_colors)
    img = Image.new("RGB", (800, 600), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Random font
    fonts = ["arial.ttf", "times.ttf", "calibri.ttf"]
    font_size = 60  # starting large
    try:
        font = ImageFont.truetype(random.choice(fonts), font_size)
    except:
        font = ImageFont.load_default()
        font_size = 20

    wrapped_text = textwrap.fill(text, width=30)

    # Dynamically reduce font size if text too tall
    while True:
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
        text_height = bbox[3] - bbox[1]
        if text_height < img.height * 0.8 or font_size <= 20:
            break
        font_size -= 2
        try:
            font = ImageFont.truetype(random.choice(fonts), font_size)
        except:
            font = ImageFont.load_default()

    # Center text
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (img.width - text_width) / 2
    y = (img.height - text_height) / 2

    draw.multiline_text((x, y), wrapped_text, font=font, fill="white", align="center")

    # Save image
    filename = f"quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(filename)
    return filename

# ----------------------------
# Send Photo to Telegram
# ----------------------------
def send_photo(filename, caption="✨ Daily Motivation ✨"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(filename, "rb") as photo:
        payload = {"chat_id": CHANNEL_ID, "caption": caption}
        files = {"photo": photo}
        response = requests.post(url, data=payload, files=files)
        print("Telegram response:", response.json())

# ----------------------------
# Main Function
# ----------------------------
def post_quote():
    quote = get_random_quote()
    if is_duplicate(quote):
        print("⚠️ Duplicate quote, skipping...")
        return

    print("Quote:", quote)
    filename = create_quote_image(quote)
    send_photo(filename)
    log_quote(quote)
    os.remove(filename)

# ----------------------------
# Scheduler
# ----------------------------
if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone=pytz.timezone("Asia/Kolkata"))
    scheduler.add_job(post_quote, "interval", seconds=30)  # for testing
    # For daily posting at 7 AM, use:
    # scheduler.add_job(post_quote, "cron", hour=7, minute=0)
    print("Quote bot started...")
    scheduler.start()
