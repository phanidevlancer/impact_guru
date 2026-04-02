# Telethon Starter Kit

## Setup

1. Create a virtual environment
2. Install dependencies
3. Add your credentials to `.env`
4. Run the login check

## Commands

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

python scripts/login_check.py
python scripts/send_test_message.py
python scripts/list_dialogs.py
python scripts/inspect_group.py me