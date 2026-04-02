from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    api_id : int
    api_hash: str
    phone_number : str
    session_name : str
    

def get_settings() -> Settings:
    api_id_raw = os.getenv("API_ID", "").strip()
    api_hash = os.getenv("API_HASH", "").strip()
    phone_number = os.getenv("PHONE_NUMBER", "").strip()
    session_name = os.getenv("SESSION_NAME", "telegram_session").strip()

    if not api_id_raw:
        raise ValueError("Missing API_ID in .env")
    if not api_hash:
        raise ValueError("Missing API_HASH in .env")
    if not phone_number:
        raise ValueError("Missing PHONE_NUMBER in .env")

    try:
        api_id = int(api_id_raw)
    except ValueError as exc:
        raise ValueError("API_ID must be an integer") from exc

    return Settings(
        api_id=api_id,
        api_hash=api_hash,
        phone_number=phone_number,
        session_name=session_name,
    )