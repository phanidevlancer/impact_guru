from typing import Optional

def short_text(value : Optional[str], limit : int = 80) -> str : 
    if not value:
        return ""
    value = value.replace("\n", " ").strip()
    return value if len(value) <= limit else value[:limit - 3] +"..."