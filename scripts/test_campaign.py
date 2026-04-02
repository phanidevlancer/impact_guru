"""
Quick test — sends to a fixed list of numbers using the campaign templates & DB.
"""
import asyncio
import random
from app.db import init_db, get_or_create_campaign, save_message, get_stats, get_next_batch_number
from app.templates import TEMPLATES
from app.client import build_client
from app.campaign import _resolve_and_send

TEST_NUMBERS = [
    "+919985788376",
    "+919866802205",
]

LINK = "https://www.impactguru.com/fundraiser/help-bijjarapu-shiva"  # replace with real link
CAMPAIGN_NAME = "test_run"


async def main():
    init_db()
    campaign = get_or_create_campaign(CAMPAIGN_NAME, TEST_NUMBERS[0], LINK)
    batch_number = get_next_batch_number(campaign.id)

    client = build_client()
    await client.start(phone=client.phone)

    async with client:
        for phone in TEST_NUMBERS:
            template = random.choice(TEMPLATES)
            message = template.format(link=LINK)
            template_id = TEMPLATES.index(template)

            print(f"Sending to {phone} ...", end=" ", flush=True)
            telegram_msg_id, status, last_seen, fail_reason = await _resolve_and_send(client, phone, message)

            save_message(
                campaign_id=campaign.id,
                phone_number=phone,
                template_id=template_id,
                message_text=message,
                telegram_msg_id=telegram_msg_id,
                status=status,
                batch_number=batch_number,
                last_seen=last_seen,
                fail_reason=fail_reason,
            )
            print(f"{status.upper()} (msg_id={telegram_msg_id})")
            print(f"  Message: {message}\n")

    stats = get_stats(campaign.id)
    print("── Stats ──────────────────────")
    print(f"  Sent       : {stats.get('sent', 0)}")
    print(f"  No account : {stats.get('no_account', 0)}")
    print(f"  Failed     : {stats.get('failed', 0)}")


if __name__ == "__main__":
    asyncio.run(main())
