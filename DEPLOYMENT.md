# Deployment Guide — AWS EC2

This guide walks you through deploying the ImpactGuru Telegram campaign on an AWS EC2 instance from scratch.

---

## Prerequisites

- An AWS account
- A Telegram account
- Your ImpactGuru fundraising link

---

## Step 1 — Get Telegram API Credentials

You need these to connect to Telegram programmatically.

1. Go to [https://my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Click **API development tools**
4. Fill in the form:
   - App title: anything (e.g. `MyApp`)
   - Short name: anything (e.g. `myapp`)
5. Click **Create application**
6. You will see:
   - `App api_id` → this is your **API_ID**
   - `App api_hash` → this is your **API_HASH**

Keep these private — never share them publicly.

---

## Step 2 — Launch an EC2 Instance

1. Go to [https://console.aws.amazon.com/ec2](https://console.aws.amazon.com/ec2)
2. Click **Launch Instance**
3. Configure:
   - **Name**: `telegram-campaign`
   - **OS**: Ubuntu 24.04 LTS
   - **Instance type**: `t2.micro` (free tier) or `t3.small`
   - **Key pair**: Create new → download the `.pem` file → save it safely
4. Under **Network settings** → Edit → Add inbound rules:
   - SSH: Port `22`, Source `0.0.0.0/0`
   - Custom TCP: Port `8501`, Source `0.0.0.0/0` (for Streamlit dashboard)
5. Click **Launch Instance**
6. Wait ~1 minute for it to start
7. Copy the **Public IPv4 address** from the instance details

---

## Step 3 — Connect to EC2

On your local machine:

```bash
# Make the key file private (Mac/Linux only)
chmod 400 /path/to/your-key.pem

# SSH into EC2
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

Replace `YOUR_EC2_PUBLIC_IP` with the IP you copied in Step 2.

---

## Step 4 — Setup the Server

Run these commands on EC2 one by one:

```bash
# Update system packages
sudo apt update

# Install required system packages
sudo apt install -y python3.12-venv git sqlite3 tmux

# Clone the project
git clone https://github.com/phanidevlancer/impact_guru.git
cd impact_guru

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install -e .
```

---

## Step 5 — Get Your Session String

This step must be done **on your local machine** (not EC2), because it requires Telegram OTP verification.

```bash
# On your local machine (not EC2)
cd /path/to/impact_guru
source venv/bin/activate   # or venv\Scripts\activate on Windows
python scripts/export_session.py
```

- It will ask for your phone number → enter it with country code (e.g. `+919866802205`)
- Telegram will send you an OTP → enter it
- It prints a long string like `1BVtsOHoBu52VB...`
- **Copy that string** — this is your `SESSION_STRING`

> Keep this string private. It gives full access to your Telegram account.
> To revoke it: Telegram → Settings → Devices → Terminate all other sessions.

---

## Step 6 — Create the .env File on EC2

Back on EC2:

```bash
nano .env
```

Fill in the values:

```
API_ID=your_api_id_from_step1
API_HASH=your_api_hash_from_step1
PHONE_NUMBER=+919XXXXXXXXX
SESSION_NAME=telegram_session
SESSION_STRING=your_session_string_from_step5
```

| Variable | Where to get it |
|---|---|
| `API_ID` | my.telegram.org → API development tools |
| `API_HASH` | my.telegram.org → API development tools |
| `PHONE_NUMBER` | Your Telegram phone number with country code |
| `SESSION_NAME` | Leave as `telegram_session` (used for local file session) |
| `SESSION_STRING` | Output of `python scripts/export_session.py` on local machine |

Save and exit: **Ctrl+O → Enter → Ctrl+X**

---

## Step 7 — Start the Worker

The worker sends messages in batches. It starts in a waiting state until you start it from the dashboard.

```bash
# Create a tmux session for the worker
tmux new -s worker

# Activate venv
source venv/bin/activate

# Start the worker (replace values as needed)
python scripts/run_campaign.py \
  --name impactguru_v1 \
  --start +919000000000 \
  --link 'https://www.impactguru.com/fundraiser/help-bijjarapu-shiva' \
  --schedule \
  --batch-delay 3600
```

You should see:
```
Worker ready. Waiting for campaign to be started from the dashboard...
```

**Detach from tmux** (keeps running after you close terminal):
Press `Ctrl+B` then `D`

---

## Step 8 — Start the Dashboard

```bash
# Create a new tmux session for the dashboard
tmux new -s dashboard

# Activate venv
source venv/bin/activate

# Start Streamlit dashboard
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
```

**Detach from tmux**:
Press `Ctrl+B` then `D`

---

## Step 9 — Open the Dashboard

Open your browser and go to:

```
http://YOUR_EC2_PUBLIC_IP:8501
```

Click **▶ Start / Resume** to begin sending messages.

---

## tmux Cheat Sheet

| Command | What it does |
|---|---|
| `tmux new -s name` | Create a new session |
| `Ctrl+B then D` | Detach (leave session running) |
| `tmux attach -t worker` | Reattach to worker session |
| `tmux attach -t dashboard` | Reattach to dashboard session |
| `tmux ls` | List all running sessions |
| `Ctrl+C` | Stop the running process |

---

## Updating the Code

When you push new code from your local machine, pull it on EC2 and restart only what changed:

```bash
git pull
```

| What changed | What to restart |
|---|---|
| `dashboard.py` | Only dashboard |
| `app/campaign.py` | Only worker |
| `app/db.py` | Both |
| `app/templates.py` | Only worker |

**Restart dashboard:**
```bash
tmux attach -t dashboard
# Ctrl+C to stop
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
# Ctrl+B then D to detach
```

**Restart worker:**
```bash
tmux attach -t worker
# Ctrl+C to stop
python scripts/run_campaign.py --name impactguru_v1 --start +919000000000 --link 'https://www.impactguru.com/fundraiser/help-bijjarapu-shiva' --schedule --batch-delay 3600
# Ctrl+B then D to detach
```

---

## Keep Dashboard Always Awake (Optional)

Streamlit has no inactivity timeout, but if you want external uptime monitoring:

1. Go to [https://cron-job.org](https://cron-job.org) → create free account
2. Add a new cron job:
   - URL: `http://YOUR_EC2_PUBLIC_IP:8501`
   - Schedule: every 10 minutes
3. Save

This pings your dashboard every 10 minutes.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'app'`**
```bash
pip install -e .
```

**`no such column: messages.last_seen`**
```bash
sqlite3 campaign.db "ALTER TABLE messages ADD COLUMN last_seen TEXT;"
```

**`externally-managed-environment` error**
```bash
sudo apt install -y python3.12-venv
python3 -m venv venv
source venv/bin/activate
```

**Dashboard not loading in browser**
- Check port 8501 is open in EC2 Security Group inbound rules
- Make sure dashboard tmux session is running: `tmux ls`

**Worker not starting**
- Check `.env` file has all 5 values filled in
- Make sure venv is activated: `source venv/bin/activate`
