"""
Run this ONCE locally to get your SESSION_STRING.
Copy the output and set it as an environment variable on Render.

Usage:
    python3 scripts/export_session.py
"""
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from app.config import get_settings


async def main():
    settings = get_settings()
    client = TelegramClient(StringSession(), settings.api_id, settings.api_hash)

    await client.start(phone=settings.phone_number)
    session_string = client.session.save()
    await client.disconnect()

    print("\n" + "="*60)
    print("SESSION_STRING (copy this to Render env vars):")
    print("="*60)
    print(session_string)
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
