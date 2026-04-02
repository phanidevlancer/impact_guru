import asyncio
import random
import logging
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.types import (
    InputPhoneContact,
    UserStatusOnline, UserStatusOffline,
    UserStatusRecently, UserStatusLastWeek,
    UserStatusLastMonth,
)

from app.db import (
    get_or_create_campaign,
    reload_campaign,
    set_campaign_status,
    set_force_next_batch,
    update_campaign_progress,
    save_message,
    get_stats,
    get_next_batch_number,
    init_db,
)
from app.templates import TEMPLATES
from app.client import build_client

logger = logging.getLogger(__name__)


def _increment_phone(phone: str) -> str:
    """Increment a phone number like +919000000000 by 1."""
    prefix = "+"
    digits = phone.lstrip("+")
    incremented = str(int(digits) + 1)
    return prefix + incremented


def _parse_last_seen(status) -> str:
    if isinstance(status, UserStatusOnline):
        return "online"
    if isinstance(status, UserStatusOffline):
        return status.was_online.strftime("%Y-%m-%d %H:%M") if status.was_online else "offline"
    if isinstance(status, UserStatusRecently):
        return "recently"
    if isinstance(status, UserStatusLastWeek):
        return "last_week"
    if isinstance(status, UserStatusLastMonth):
        return "last_month"
    return "unknown"


async def _resolve_and_send(client, phone: str, message: str) -> tuple[int | None, str, str | None]:
    """
    Import contact temporarily, send message, delete contact.
    Returns (telegram_msg_id, status, last_seen).
    """
    try:
        result = await client(ImportContactsRequest([
            InputPhoneContact(client_id=0, phone=phone, first_name="T", last_name="")
        ]))
        if not result.users:
            return None, "no_account", None

        entity = result.users[0]
        last_seen = _parse_last_seen(entity.status)
        sent = await client.send_message(entity, message)
        await client(DeleteContactsRequest(id=[entity]))
        return sent.id, "sent", last_seen

    except Exception as e:
        logger.error(f"Failed to send to {phone}: {e}")
        return None, "failed", None


async def run_batch(
    campaign_name: str,
    start_number: str,
    link: str,
    batch_size: int = 10,
    min_delay: int = 30,
    max_delay: int = 120,
):
    """Send one batch of messages and save progress to DB."""
    init_db()

    campaign = get_or_create_campaign(
        name=campaign_name,
        start_number=start_number,
        link=link,
    )

    if campaign.status != "active":
        print(f"Campaign '{campaign_name}' is {campaign.status}. Exiting.")
        return

    current_number = campaign.current_number
    batch_number = get_next_batch_number(campaign.id)

    print(f"\n{'='*50}")
    print(f"Campaign : {campaign_name}")
    print(f"Batch    : #{batch_number}")
    print(f"Starting : {current_number}")
    print(f"Sending  : {batch_size} messages")
    print(f"{'='*50}\n")

    client = build_client()
    await client.start(phone=client.phone)

    async with client:
        for i in range(batch_size):
            # Check if paused before each message
            live = reload_campaign(campaign.id)
            if live.status == "paused":
                print("Campaign paused. Waiting...")
                while True:
                    await asyncio.sleep(30)
                    live = reload_campaign(campaign.id)
                    if live.status == "active":
                        print("Campaign resumed.")
                        break

            template = random.choice(TEMPLATES)
            message = template.format(link=link)
            template_id = TEMPLATES.index(template)

            print(f"[{i+1}/{batch_size}] Sending to {current_number} ...", end=" ", flush=True)

            telegram_msg_id, status, last_seen = await _resolve_and_send(client, current_number, message)

            save_message(
                campaign_id=campaign.id,
                phone_number=current_number,
                template_id=template_id,
                message_text=message,
                telegram_msg_id=telegram_msg_id,
                status=status,
                batch_number=batch_number,
                last_seen=last_seen,
            )

            print(f"{status.upper()} (msg_id={telegram_msg_id})")

            next_number = _increment_phone(current_number)
            update_campaign_progress(campaign.id, next_number, 1 if status == "sent" else 0)
            current_number = next_number


            # Random delay between messages (skip after last)
            if i < batch_size - 1:
                delay = random.randint(min_delay, max_delay)
                print(f"    ⏳ Waiting {delay}s before next message...")
                await asyncio.sleep(delay)

    stats = get_stats(campaign.id)
    print(f"\n{'='*50}")
    print(f"Batch #{batch_number} complete.")
    print(f"  Sent       : {stats.get('sent', 0)}")
    print(f"  No account : {stats.get('no_account', 0)}")
    print(f"  Failed     : {stats.get('failed', 0)}")
    print(f"  Next number: {current_number}")
    print(f"{'='*50}\n")


async def run_scheduled(
    campaign_name: str,
    start_number: str,
    link: str,
    batch_size: int = 10,
    batch_delay: int = 3600,
    min_delay: int = 30,
    max_delay: int = 120,
    max_batches: int | None = None,
):
    """Run batches continuously with a delay between each batch."""
    init_db()
    campaign = get_or_create_campaign(campaign_name, start_number, link)
    batch_count = 0

    # Wait for admin to start the campaign from the dashboard
    print("Worker ready. Waiting for campaign to be started from the dashboard...")
    while True:
        live = reload_campaign(campaign.id)
        if live.status == "active":
            break
        if live.status == "done":
            print("Campaign is marked done. Exiting.")
            return
        await asyncio.sleep(30)

    print("Campaign started!")

    while True:
        await run_batch(
            campaign_name=campaign_name,
            start_number=start_number,
            link=link,
            batch_size=batch_size,
            min_delay=min_delay,
            max_delay=max_delay,
        )
        batch_count += 1

        if max_batches and batch_count >= max_batches:
            print(f"Reached max_batches={max_batches}. Stopping.")
            break

        print(f"Next batch in {batch_delay}s ({batch_delay // 60} min). Press Ctrl+C to stop.\n")
        # Wait in 30s intervals so we can respond to force_next_batch or pause
        elapsed = 0
        while elapsed < batch_delay:
            await asyncio.sleep(30)
            elapsed += 30
            live = reload_campaign(campaign.id)
            if live.force_next_batch:
                print("Force next batch triggered from dashboard.")
                set_force_next_batch(live.id, False)
                break
            if live.status == "paused":
                print("Campaign paused between batches. Waiting...")
                while True:
                    await asyncio.sleep(30)
                    live = reload_campaign(live.id)
                    if live.status == "active":
                        print("Campaign resumed.")
                        break
