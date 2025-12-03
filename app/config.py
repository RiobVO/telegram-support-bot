import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# сначала грузим .env.dev
load_dotenv(BASE_DIR / ".env.dev")

# --- Base bot config ---

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN is empty. Set it in .env.dev", file=sys.stderr)
    sys.exit(1)

SUPPORT_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID", "-1000000000000"))
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

ID_PREFIX = os.getenv("ID_PREFIX", "HR").strip()
EXPORT_LOOKBACK = int(os.getenv("EXPORT_LOOKBACK", "200"))

# --- Bitrix base ---

BITRIX_BASE = os.getenv("BITRIX_WEBHOOK_BASE", "").rstrip("/") + "/"
BITRIX_RESPONSIBLE_ID = int(os.getenv("BITRIX_RESPONSIBLE_ID", "1"))

# --- Smart process / CRM mode ---

BITRIX_MODE = os.getenv("BITRIX_MODE", "TASKS").upper()  # TASKS or CRM

BITRIX_SMART_ENTITY_ID = os.getenv("BITRIX_SMART_ENTITY_ID", "").strip()
BITRIX_SMART_CATEGORY_ID = os.getenv("BITRIX_SMART_CATEGORY_ID", "0").strip()

BITRIX_SMART_STAGE_ID = os.getenv("BITRIX_SMART_STAGE_ID", "").strip()
BITRIX_SMART_STAGE_WORK = os.getenv("BITRIX_SMART_STAGE_WORK", "").strip()
BITRIX_SMART_STAGE_CLOSED = os.getenv("BITRIX_SMART_STAGE_CLOSED", "").strip()
