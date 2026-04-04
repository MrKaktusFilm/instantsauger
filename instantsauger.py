import cmd
import os
import sys
from pathlib import Path
import logging
from urllib.parse import urlparse, parse_qs

from telegram.ext import ApplicationBuilder, MessageHandler, filters
import subprocess
import re
import asyncio

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

YOUTUBE_REGEX = r'(https?://(?:www\.)?(?:youtube\.com/[^"]+|youtu\.be/[^"]+))'

async def handle_message(update, context):
    text = update.message.text
    logger.info(f"Nachricht empfangen: {text}")

    try:
        match = re.search(YOUTUBE_REGEX, text)
        if match:
            url = match.group(1)
            logger.info(f"YouTube-URL erkannt: {url}")

            parsed_url = urlparse(url)
            query = parse_qs(parsed_url.query)
            is_playlist = bool(query.get("list")) or parsed_url.path.startswith("/playlist")
            is_channel = bool(re.search(r"youtube\.com/(?:channel/|c/|user/|@)", url))

            if is_playlist:
                logger.info(f"Playlist-URL erkannt, starte Download")
                await update.message.reply_text(f"📥 Lade die Playlist herunter: {url}")
            elif is_channel:
                logger.info(f"Kanal-URL erkannt, starte Download aller Videos")
                await update.message.reply_text(f"📥 Lade alle Videos des Kanals herunter: {url}")
            else:
                logger.info(f"Einzelvideo-URL erkannt, starte Download")
                await update.message.reply_text(f"📥 Starte Download...")

            # yt-dlp Befehl: speichere in Unterordner mit Kanalnamen via %(uploader)s
            output_template = "/home/marko/videos/instantsauger/%(uploader)s/%(title)s.%(ext)s"

            cmd = [
                "yt-dlp",
                "-v",
                "-o", output_template
            ]

            if is_playlist or is_channel:
                archive_file = "/home/marko/videos/instantsauger/.archive"
                cmd += ["--download-archive", archive_file]

            cmd.append(url)
            logger.info(f"Starte yt-dlp: {' '.join(cmd)}")
            # Starte Prozess und warte auf Completion
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            
            # Gib Output direkt aus
            for line in process.stdout:
                logger.info(f"[yt-dlp] {line.rstrip()}")
            
            process.wait()
            stdout = process.stdout.read() if process.stdout else ""

            if process.returncode == 0:
                logger.info(f"Download erfolgreich abgeschlossen (Return-Code: 0)")
                logger.info(f"yt-dlp Output:\n{stdout}")

                if is_channel:
                    await update.message.reply_text(f"✅ Kanal erfolgreich heruntergeladen! \n{url}")
                else:
                    await update.message.reply_text(f"✅ Video erfolgreich heruntergeladen! \n{url}")
            else:
                logger.error(f"Download fehlgeschlagen (Return-Code: {process.returncode})")
                error_msg = stdout
                await update.message.reply_text(f"❌ Fehler beim Download:\n{error_msg[:500]}")

        else:
            logger.warning(f"Keine gültige YouTube-URL gefunden")
            await update.message.reply_text("Bitte sende mir einen gültigen YouTube-Link.")

    except Exception as e:
        logger.exception(f"Exception aufgetreten: {str(e)}")
        await update.message.reply_text(f"❌ Ein Fehler ist aufgetreten:\n{str(e)[:500]}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

app.run_polling()