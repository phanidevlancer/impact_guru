import asyncio
import argparse
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.types import InputPhoneContact
from app.client import build_client


async def main(target: str, message: str) -> None:
    client = build_client()

    await client.start(phone=client.phone)
    async with client:
        if target.startswith("+"):
            # Import temporarily so Telethon can resolve the phone number
            result = await client(ImportContactsRequest([
                InputPhoneContact(client_id=0, phone=target, first_name="Temp", last_name="")
            ]))
            entity = result.users[0] if result.users else None
            if not entity:
                print(f"No Telegram account found for {target}")
                return
            sent = await client.send_message(entity, message)
            await client(DeleteContactsRequest(id=[entity]))
        else:
            sent = await client.send_message(target, message)
        print(f"✅ Message sent to {target}")
        print(f"   Message ID : {sent.id}")
        print(f"   Sent at    : {sent.date}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a Telegram message")
    parser.add_argument("target", help="Recipient phone number or username (e.g. +919985788376)")
    parser.add_argument("--message", "-m", default="Hello from Telethon starter kit ✅", help="Message to send")
    args = parser.parse_args()

    asyncio.run(main(args.target, args.message))