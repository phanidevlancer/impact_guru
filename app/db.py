import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, func
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///campaign.db")

# Render provides postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Campaign(Base):
    __tablename__ = "campaigns"

    id           = Column(Integer, primary_key=True)
    name         = Column(String, unique=True, nullable=False)
    start_number = Column(String, nullable=False)
    current_number = Column(String, nullable=False)
    link         = Column(String, nullable=False)
    status           = Column(String, default="paused")   # paused | active | done
    total_sent       = Column(Integer, default=0)
    batch_size       = Column(Integer, default=10)
    force_next_batch = Column(Boolean, default=False)
    created_at       = Column(DateTime, default=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id             = Column(Integer, primary_key=True)
    campaign_id    = Column(Integer, nullable=False)
    phone_number   = Column(String, nullable=False)
    template_id    = Column(Integer, nullable=False)
    message_text   = Column(Text, nullable=False)
    telegram_msg_id = Column(Integer, nullable=True)
    status         = Column(String, nullable=False)   # sent | failed | no_account
    batch_number   = Column(Integer, nullable=False)
    sent_at        = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)


# ── Campaign helpers ──────────────────────────────────────────────────────────

def get_or_create_campaign(name: str, start_number: str, link: str) -> Campaign:
    with Session() as s:
        campaign = s.query(Campaign).filter_by(name=name).first()
        if not campaign:
            campaign = Campaign(
                name=name,
                start_number=start_number,
                current_number=start_number,
                link=link,
            )
            s.add(campaign)
            s.commit()
            s.refresh(campaign)
        return Campaign(
            id=campaign.id,
            name=campaign.name,
            start_number=campaign.start_number,
            current_number=campaign.current_number,
            link=campaign.link,
            status=campaign.status,
            total_sent=campaign.total_sent,
            batch_size=campaign.batch_size,
            force_next_batch=campaign.force_next_batch,
        )


def reload_campaign(campaign_id: int) -> Campaign:
    with Session() as s:
        c = s.query(Campaign).filter_by(id=campaign_id).first()
        return Campaign(
            id=c.id, name=c.name, start_number=c.start_number,
            current_number=c.current_number, link=c.link,
            status=c.status, total_sent=c.total_sent,
            batch_size=c.batch_size, force_next_batch=c.force_next_batch,
        )


def set_campaign_status(campaign_id: int, status: str):
    with Session() as s:
        s.query(Campaign).filter_by(id=campaign_id).update({"status": status})
        s.commit()


def set_force_next_batch(campaign_id: int, value: bool):
    with Session() as s:
        s.query(Campaign).filter_by(id=campaign_id).update({"force_next_batch": value})
        s.commit()


def update_campaign_progress(campaign_id: int, next_number: str, sent_count: int):
    with Session() as s:
        c = s.query(Campaign).filter_by(id=campaign_id).first()
        c.current_number = next_number
        c.total_sent += sent_count
        s.commit()


def save_message(
    campaign_id: int,
    phone_number: str,
    template_id: int,
    message_text: str,
    telegram_msg_id: int | None,
    status: str,
    batch_number: int,
):
    with Session() as s:
        msg = Message(
            campaign_id=campaign_id,
            phone_number=phone_number,
            template_id=template_id,
            message_text=message_text,
            telegram_msg_id=telegram_msg_id,
            status=status,
            batch_number=batch_number,
        )
        s.add(msg)
        s.commit()


def get_stats(campaign_id: int) -> dict:
    with Session() as s:
        rows = (
            s.query(Message.status, func.count(Message.id))
            .filter_by(campaign_id=campaign_id)
            .group_by(Message.status)
            .all()
        )
        return {status: count for status, count in rows}


def get_next_batch_number(campaign_id: int) -> int:
    with Session() as s:
        result = s.query(func.max(Message.batch_number)).filter_by(campaign_id=campaign_id).scalar()
        return (result or 0) + 1
