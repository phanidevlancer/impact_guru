import asyncio
from app.client import build_client
from app.utils import short_text


async def main() -> None:
    client = build_client()

    async with client:
        print("Fetching dialogs...\n")
        async for dialog in client.iter_dialogs():
            print(
                f"{dialog.id} | "
                f"name={dialog.name!r} | "
                f"is_user={dialog.is_user} | "
                f"is_group={dialog.is_group} | "
                f"is_channel={dialog.is_channel} | "
                f"unread={dialog.unread_count} | "
                f"last={short_text(dialog.message.text if dialog.message else '')}"
            )


if __name__ == "__main__":
    asyncio.run(main())