from telethon import TelegramClient, events
import requests
import os

# Directly add your API credentials here
API_ID = 25618359  # Replace with your actual API ID
API_HASH = "65e8b35c588ff38624c4d4d3aabe481a"  # Replace with your actual API Hash
BOT_TOKEN = "7645375723:AAEuSF_4oQ1igBxzK5Ojr0r-x3BXdO86eWM"  # Replace with your actual Bot Token

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

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded_size += len(chunk)

                # Update the progress bar
                progress = progress_bar(downloaded_size, total_size)
                await progress_message.edit(f"Downloading...\n{progress}")

        await progress_message.edit("Download complete. Preparing upload...")

        # Upload the file to Telegram
        async def upload_progress(current, total):
            progress = progress_bar(current, total)
            await progress_message.edit(f"Uploading...\n{progress}")

        await client.send_file(event.chat_id, filename, caption=f"Uploaded: {filename}", progress_callback=upload_progress)

        # Cleanup
        os.remove(filename)
        await progress_message.edit("Upload complete. ✅")
    except Exception as e:
        await event.reply(f"Error: {str(e)}")

# Start the bot
print("Bot is running...")
client.run_until_disconnected()
