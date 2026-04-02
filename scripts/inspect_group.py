import asyncio
import sys
from app.client import build_client
from app.utils import short_text


async def main(target: str) -> None:
    client = build_client()

    async with client:
        entity = await client.get_entity(target)
        print("✅ Resolved target")
        print(f"ID   : {getattr(entity, 'id', None)}")
        print(f"Type : {entity.__class__.__name__}")
        print()

        print("Recent messages:\n")
        async for msg in client.iter_messages(entity, limit=10):
            sender_id = getattr(msg, "sender_id", None)
            print(
                f"[{msg.id}] sender={sender_id} "
                f"text={short_text(msg.text, 120)!r}"
            )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/inspect_group.py <group_username_or_link>")
    asyncio.run(main(sys.argv[1]))