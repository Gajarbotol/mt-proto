from telethon import TelegramClient, events
import requests
import os
from flask import Flask

# Fetch required credentials from environment variables
API_ID = int(os.getenv("API_ID", 25618359))  # Replace with your actual API ID or set it in Render
API_HASH = os.getenv("API_HASH", "65e8b35c588ff38624c4d4d3aabe481a")  # Replace with your actual API Hash
BOT_TOKEN = os.getenv("BOT_TOKEN", "7645375723:AAEuSF_4oQ1igBxzK5Ojr0r-x3BXdO86eWM")  # Replace with your actual Bot Token
PORT = int(os.getenv("PORT", 8080))  # Render automatically provides PORT

# Initialize the Telegram client
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Progress bar function
def progress_bar(progress, total, length=10):
    if total == 0:
        return "[⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜] 0%"
    completed = int(progress / total * length)
    bar = '✅' * completed + '⬜' * (length - completed)
    return f"[{bar}] {int(progress / total * 100)}%"

# Handle /start command
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    usage_message = (
        "Hello! 👋\n\n"
        "I am a URL Upload Bot. Here's how to use me:\n\n"
        "1️⃣ Send `/upload <file_url>` - Replace `<file_url>` with the direct URL of the file you want to download and upload.\n"
        "2️⃣ I will download the file and show you progress.\n"
        "3️⃣ Once complete, I will upload the file and share it with you.\n\n"
        "Note: I support files up to 2GB using MTProto. 🚀"
    )
    await event.reply(usage_message)

# Handle /upload command
@client.on(events.NewMessage(pattern='/upload'))
async def upload_handler(event):
    args = event.message.text.split(maxsplit=1)
    if len(args) != 2:
        await event.reply("Usage: /upload <file_url>")
        return

    url = args[1]
    filename = url.split("/")[-1]

    try:
        # Send an initial message for progress tracking
        progress_message = await event.reply("Preparing to download...")

        # Start downloading the file
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        last_progress = None

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded_size += len(chunk)

                # Update the progress bar only if progress has changed
                progress = progress_bar(downloaded_size, total_size)
                if progress != last_progress:
                    await progress_message.edit(f"Downloading...\n{progress}")
                    last_progress = progress

        await progress_message.edit("Download complete. Preparing upload...")

        # Upload the file to Telegram
        async def upload_progress(current, total):
            upload_progress_bar = progress_bar(current, total)
            if upload_progress_bar != last_progress:
                await progress_message.edit(f"Uploading...\n{upload_progress_bar}")

        await client.send_file(event.chat_id, filename, caption=f"Uploaded: {filename}", progress_callback=upload_progress)

        # Cleanup
        os.remove(filename)
        await progress_message.edit("Upload complete. ✅")
    except Exception as e:
        await event.reply(f"Error: {str(e)}")

# Auto-ping system using Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running and alive!", 200

# Run Flask alongside the bot
if __name__ == "__main__":
    from threading import Thread

    def run_flask():
        app.run(host="0.0.0.0", port=PORT)

    def run_telethon():
        print(f"Bot is running on port {PORT}...")
        client.run_until_disconnected()

    # Run Flask in a separate thread to handle pings
    Thread(target=run_flask).start()
    run_telethon()
