from telethon import TelegramClient, events, Button
import requests
import os
import time
from flask import Flask

# Fetch required credentials from environment variables
API_ID = int(os.getenv("API_ID", 25618359))  # Replace with your actual API ID or set it in Render
API_HASH = os.getenv("API_HASH", "65e8b35c588ff38624c4d4d3aabe481a")  # Replace with your actual API Hash
BOT_TOKEN = os.getenv("BOT_TOKEN", "7645375723:AAEuSF_4oQ1igBxzK5Ojr0r-x3BXdO86eWM")  # Replace with your actual Bot Token
PORT = int(os.getenv("PORT", 8080))  # Render automatically provides PORT

# Initialize the Telegram client
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Progress bar function with ETA, file size, and speed
def progress_bar(progress, total, start_time, speed, length=10):
    if total == 0:
        return "[⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜] 0% - Size: 0B - ETA: ∞"

    completed = int(progress / total * length)
    bar = '✅' * completed + '⬜' * (length - completed)
    percentage = int(progress / total * 100)

    eta = (total - progress) / speed if speed > 0 else float('inf')

    # Format file size and speed
    total_size_str = f"{total / (1024 * 1024):.2f} MB"
    speed_str = f"{speed / 1024:.2f} KB/s"
    eta_str = f"{int(eta // 60)}m {int(eta % 60)}s" if eta < float('inf') else "∞"

    return f"[{bar}] {percentage}% - 📦 Size: {total_size_str} - ⏳ ETA: {eta_str} - 🚀 Speed: {speed_str}"

# Handle /start command with a reply keyboard
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    buttons = [
        [Button.text("🚀 Upload File", resize=True, single_use=True)]
    ]
    usage_message = (
        "Hello! 👋\n\n"
        "I am a URL Upload Bot 🤖. Click '🚀 Upload File' to start!\n\n"
        "Note: I support files up to 2GB using MTProto. 📂"
    )
    await event.reply(usage_message, buttons=buttons)

# Handle the button press and ask for a file URL
@client.on(events.NewMessage(pattern='🚀 Upload File'))
async def handle_upload_request(event):
    await event.reply("🔗 Please send me the URL of the file you want to upload.")

# Handle URL and upload process
@client.on(events.NewMessage)
async def upload_handler(event):
    if not event.message.text.startswith('http'):
        return

    url = event.message.text
    filename = url.split("/")[-1]

    try:
        # Send an initial message for progress tracking
        progress_message = await event.reply("🔍 Preparing to download...")

        # Start downloading the file
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        progress_tracker = {'last_progress': -1}  # Use a dict to track progress
        start_time = time.time()

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded_size += len(chunk)

                # Calculate the current progress and speed
                elapsed_time = time.time() - start_time
                current_progress = int(downloaded_size / total_size * 100)
                speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0

                # Update the progress bar only if progress has changed
                if current_progress != progress_tracker['last_progress']:
                    progress = progress_bar(downloaded_size, total_size, start_time, speed)
                    await progress_message.edit(f"⬇️ Downloading...\n{progress}")
                    progress_tracker['last_progress'] = current_progress

        await progress_message.edit("✅ Download complete. Preparing upload...")

        # Upload the file to Telegram
        async def upload_progress(current, total):
            current_upload_progress = int(current / total * 100)
            elapsed_time = time.time() - start_time
            speed = current / elapsed_time if elapsed_time > 0 else 0

            if current_upload_progress != progress_tracker['last_progress']:
                upload_progress_bar = progress_bar(current, total, start_time, speed)
                await progress_message.edit(f"⬆️ Uploading...\n{upload_progress_bar}")
                progress_tracker['last_progress'] = current_upload_progress

        await client.send_file(event.chat_id, filename,
                               caption=f"📤 Uploaded: {filename}",
                               progress_callback=upload_progress)

        # Cleanup
        os.remove(filename)
        await progress_message.edit("🎉 Upload complete. ✅")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# Auto-ping system using Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running and alive! 🌟", 200

# Run Flask alongside the bot
if __name__ == "__main__":
    from threading import Thread

    def run_flask():
        app.run(host="0.0.0.0", port=PORT)

    def run_telethon():
        print(f"Bot is running on port {PORT}... 🚀")
        client.run_until_disconnected()

    # Run Flask in a separate thread to handle pings
    Thread(target=run_flask).start()
    run_telethon()
