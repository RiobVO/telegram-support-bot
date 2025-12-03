import re
from datetime import datetime
from typing import Dict, Any, List

from .config import ADMIN_IDS, ID_PREFIX
import app.bot_core as core  # чтобы менять core.ID_COUNTER, а не копию


# --- Права и валидация ввода ---


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def validate_name(s: str) -> bool:
    s = s.strip()
    return 2 <= len(s) <= 120

PHONE_RE = re.compile(r'^[\+\d][\d\s\-\(\)]{6,19}$')

def validate_phone(s: str) -> bool:
    s = s.strip()
    if not PHONE_RE.fullmatch(s):
        return False
    digits = re.sub(r'\D', '', s)
    return 7 <= len(digits) <= 20  # грубая, но жизненная проверка

def truncate(s: str, n: int = 140) -> str:
    s = s.strip()
    return s if len(s) <= n else s[:n - 1] + "…"

def generate_external_id() -> str:
    core.ID_COUNTER += 1
    return f"{ID_PREFIX}-{datetime.utcnow().year}-{core.ID_COUNTER:06d}"


def card_text(lang: str, external_id: str, name: str, phone: str,
              category: str, text: str, status: str) -> str:
    return (
        f"🆔 <b>{external_id}</b>\n"
        f"🌐 {lang}\n"
        f"👤 {name}\n"
        f"📞 {phone}\n"
        f"📂 {category}\n"
        f"🔧 Статус: {status}\n\n"
        f"{text}"
    )

def replace_status_line(txt: str, new_status: str) -> str:
    return re.sub(r"(🔧 Статус:\s*)(.*)", rf"\1{new_status}", txt)

def build_bitrix_description(lang: str, name: str, phone: str,
                             category: str, text: str,
                             attachments: List[Dict[str, str]],
                             external_id: str) -> str:
    lines = [
        f"Внешний ID: {external_id}",
        f"Язык: {lang}",
        f"Имя: {name}",
        f"Телефон: {phone}",
        f"Категория: {category}",
        "",
        "Текст обращения:",
        text,
        "",
    ]
    if attachments:
        lines.append("Вложения (отправлены в служебный канал):")
        for i, a in enumerate(attachments, 1):
            lines.append(f"{i}. {a['type']}: file_id={a['file_id']}")
    else:
        lines.append("Вложения: нет")
    return "\n".join(lines)
