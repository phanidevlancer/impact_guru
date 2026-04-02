import asyncio
from app.client import build_client


async def main() -> None:
    client = build_client()

    await client.start(phone=client.phone)
    async with client:
        me = await client.get_me()
        print("✅ Login successful")
        print(f"Name     : {getattr(me, 'first_name', '')} {getattr(me, 'last_name', '')}".strip())
        print(f"Username : @{me.username}" if me.username else "Username : (none)")
        print(f"Phone    : {me.phone}")


if __name__ == "__main__":
    asyncio.run(main())