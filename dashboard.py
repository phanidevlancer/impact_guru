import streamlit as st
import pandas as pd
from datetime import datetime
from app.db import (
    Session, Campaign, Message, init_db,
    set_campaign_status, set_force_next_batch,
    reload_campaign,
)

st.set_page_config(page_title="Campaign Dashboard", layout="wide")
st.title("ImpactGuru Campaign Dashboard")

init_db()

with Session() as s:
    campaigns = s.query(Campaign).all()

if not campaigns:
    st.info("No campaigns found. Run a campaign first.")
    st.stop()

# Campaign selector
campaign_names = [c.name for c in campaigns]
selected_name = st.selectbox("Select Campaign", campaign_names)
campaign = reload_campaign(next(c.id for c in campaigns if c.name == selected_name))

# ── Overview ──────────────────────────────────────────────────────────────────
st.subheader("Overview")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Status", campaign.status.upper())
col2.metric("Total Sent", campaign.total_sent)
col3.metric("Started From", campaign.start_number)
col4.metric("Next Number", campaign.current_number)

# Next batch range
next_end = "+" + str(int(campaign.current_number.lstrip("+")) + campaign.batch_size - 1)
col5.metric("Next Batch Range", f"{campaign.current_number} → {next_end}")

st.markdown(f"**Link:** {campaign.link}")

# ── Controls ──────────────────────────────────────────────────────────────────
st.subheader("Controls")

ctrl1, ctrl2, ctrl3, ctrl4 = st.columns(4)

with ctrl1:
    if campaign.status == "paused":
        if st.button("▶ Start / Resume", use_container_width=True):
            set_campaign_status(campaign.id, "active")
            st.success("Campaign started.")
            st.rerun()
    elif campaign.status == "active":
        if st.button("⏸ Pause Campaign", use_container_width=True):
            set_campaign_status(campaign.id, "paused")
            st.success("Campaign paused.")
            st.rerun()

with ctrl2:
    if st.button("⚡ Force Next Batch Now", use_container_width=True):
        set_force_next_batch(campaign.id, True)
        st.success("Next batch will start within 30 seconds.")

with ctrl3:
    if st.button("✅ Mark as Done", use_container_width=True):
        set_campaign_status(campaign.id, "done")
        st.success("Campaign marked as done.")
        st.rerun()

with ctrl4:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# ── Stats ─────────────────────────────────────────────────────────────────────
with Session() as s:
    messages = s.query(Message).filter_by(campaign_id=campaign.id).all()

if not messages:
    st.info("No messages sent yet.")
    st.stop()

df = pd.DataFrame([{
    "phone_number":    m.phone_number,
    "status":          m.status,
    "batch":           m.batch_number,
    "telegram_msg_id": m.telegram_msg_id,
    "sent_at":         m.sent_at,
    "message":         m.message_text,
} for m in messages])

st.subheader("Message Stats")
counts = df["status"].value_counts()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Sent",          counts.get("sent", 0))
c2.metric("No Account",    counts.get("no_account", 0))
c3.metric("Failed",        counts.get("failed", 0))
c4.metric("Total Attempts", len(df))

st.bar_chart(counts)

# ── Success rate ──────────────────────────────────────────────────────────────
total = len(df)
sent  = counts.get("sent", 0)
rate  = round((sent / total) * 100, 1) if total else 0
st.progress(rate / 100, text=f"Success Rate: {rate}%")

# ── Batch breakdown ───────────────────────────────────────────────────────────
st.subheader("Batch Breakdown")
batch_df = (
    df.groupby(["batch", "status"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)
st.dataframe(batch_df, use_container_width=True)

# ── Sent over time ────────────────────────────────────────────────────────────
st.subheader("Sent Over Time")
sent_df = df[df["status"] == "sent"].copy()
if not sent_df.empty:
    sent_df["sent_at"] = pd.to_datetime(sent_df["sent_at"])
    sent_df = sent_df.set_index("sent_at").resample("1h").size().reset_index(name="count")
    st.line_chart(sent_df.set_index("sent_at"))

# ── Template usage ────────────────────────────────────────────────────────────
st.subheader("Template Usage")
template_counts = df.groupby("message").size().reset_index(name="count").sort_values("count", ascending=False)
st.dataframe(template_counts, use_container_width=True)

# ── Recent messages ───────────────────────────────────────────────────────────
st.subheader("Recent Messages (last 50)")
st.dataframe(
    df.sort_values("sent_at", ascending=False).head(50),
    use_container_width=True,
)

# ── Search ────────────────────────────────────────────────────────────────────
st.subheader("Search by Phone Number")
search = st.text_input("Enter phone number")
if search:
    result = df[df["phone_number"].str.contains(search)]
    st.dataframe(result, use_container_width=True)
