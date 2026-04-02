import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from app.config import get_settings

def build_client() -> TelegramClient:
    settings = get_settings()
    session_string = os.getenv("SESSION_STRING", "").strip()

    # On Render: use SESSION_STRING env var (no file needed)
    # Locally: fall back to file-based session
    session = StringSession(session_string) if session_string else settings.session_name

    client = TelegramClient(session, settings.api_id, settings.api_hash)
    client.phone = settings.phone_number
    return client