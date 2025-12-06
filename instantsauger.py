import os
import sys
from pathlib import Path

from telegram.ext import ApplicationBuilder, MessageHandler, filters
import subprocess
import re
import asyncio

# Lade .env aus dem selben Verzeichnis, falls python-dotenv installiert ist
BASE_DIR = Path(__file__).parent
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except Exception:
    # dotenv nicht verfügbar -> verlasse dich auf echte Umgebungsvariablen
    pass

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("Error: BOT_TOKEN ist nicht gesetzt. Bitte in .env oder in der Umgebung definieren.")
    sys.exit(1)

YOUTUBE_REGEX = r"(https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=[\w-]+|channel/[\w-]+|c/[\w-]+|user/[\w-]+|@[\w-]+)|youtu\.be/[\w-]+))"

async def handle_message(update, context):
    text = update.message.text

    try:
        match = re.search(YOUTUBE_REGEX, text)
        if match:
            url = match.group(1)

            # Erkenne Kanal-URLs (channel/, c/, user/ oder @handle)
            is_channel = bool(re.search(r"youtube\.com/(?:channel/|c/|user/|@)", url))

            if is_channel:
                await update.message.reply_text(f"📥 Lade alle Videos des Kanals herunter: {url}")
            else:
                await update.message.reply_text(f"📥 Lade herunter: {url}")

            # yt-dlp Befehl: speichere in Unterordner mit Kanalnamen via %(uploader)s
            output_template = "/home/marko/videos/instantsauger/%(uploader)s/%(title)s.%(ext)s"
            cmd = ["yt-dlp"]
            # sicherstellen, dass bei Kanal-URLs die Playlist geladen wird, bei Einzelvideos nicht
            if is_channel:
                cmd += ["--yes-playlist"]
            else:
                cmd += ["--no-playlist"]
            cmd += [url, "-o", output_template]

            # Starte Prozess und warte auf Completion
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                if is_channel:
                    await update.message.reply_text(f"✅ Kanal erfolgreich heruntergeladen!")
                else:
                    await update.message.reply_text(f"✅ Video erfolgreich heruntergeladen!")
            else:
                error_msg = stderr if stderr else stdout
                await update.message.reply_text(f"❌ Fehler beim Download:\n{error_msg[:500]}")

        else:
            await update.message.reply_text("Bitte sende mir einen gültigen YouTube-Link.")

    except Exception as e:
        await update.message.reply_text(f"❌ Ein Fehler ist aufgetreten:\n{str(e)[:500]}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

app.run_polling()