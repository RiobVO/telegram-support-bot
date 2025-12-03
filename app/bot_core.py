from collections import deque
from typing import Deque, Dict, Any

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import BOT_TOKEN, EXPORT_LOOKBACK



# --- Bot & Dispatcher ---

bot = Bot(
    BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()
router = Router()
dp.include_router(router)


# --- In-memory storage (без БД) ---

# Счётчик внешних ID (используется в helpers.generate_external_id)
ID_COUNTER = 0

# История карточек для /stats и /export
# Каждый элемент: dict(id, date, language, name, phone, category, status, text_len, attachments_count)
HISTORY: Deque[Dict[str, Any]] = deque(maxlen=EXPORT_LOOKBACK)

# Индекс по внешнему ID для админ-кнопок:
# external_id -> {"task_id": Optional[int], "crm_item_id": Optional[int],
#                 "channel_message_id": int, "status": str}
TASK_INDEX: Dict[str, Dict[str, Any]] = {}