from dotenv import load_dotenv
import os
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
import json
from pathlib import Path

# === Load .env secrets ===
load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
phone_number = os.getenv("PHONE_NUMBER")
channel_username = os.getenv("CHANNEL_USERNAME")
fetch_limit = int(os.getenv("FETCH_LIMIT", 20))  # default = 20




# === Keyword filter ===
BANNED_KEYWORDS = [w.strip() for w in os.getenv("BANNED_KEYWORDS", "").split(",") if w.strip()]
TAGS_TO_REMOVE = [w.strip() for w in os.getenv("TAGS_TO_REMOVE", "").split(",") if w.strip()]




# === Load existing messages (if any) ===
json_path = Path("telegram_posts.json")
existing_data = []
seen_ids = set()

if json_path.exists():
    with open(json_path, "r", encoding="utf-8") as f:
        existing_data = json.load(f)
        seen_ids = {msg.get("id") for msg in existing_data}

# === Init client ===
client = TelegramClient('session_name', api_id, api_hash)

from telethon.tl.types import Message

async def main():
    await client.start(phone=phone_number)
    print("Logged in!")

    entity = await client.get_entity(channel_username)

    new_messages = []
    async for message in client.iter_messages(entity, limit=fetch_limit):
        if not isinstance(message, Message) or not message.message:
            continue

        if message.id in seen_ids:
            continue  # Already saved

        if any(word in message.message for word in BANNED_KEYWORDS):
            continue

        # Clean text
        cleaned_text = message.message
        for tag in TAGS_TO_REMOVE:
            cleaned_text = cleaned_text.replace(tag, '')
        cleaned_text = cleaned_text.strip()

        post_link = f"https://t.me/{channel_username.strip('@')}/{message.id}"

        new_messages.append({
            'id': message.id,
            'date': str(message.date),
            'text': cleaned_text,
            'link': post_link
        })

    if new_messages:
        updated_data = existing_data + new_messages
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Saved {len(new_messages)} new messages.")
    else:
        print("No new messages found.")

with client:
    client.loop.run_until_complete(main())
