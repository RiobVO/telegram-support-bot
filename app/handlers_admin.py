import asyncio
import csv
import os
import tempfile
from collections import Counter
from typing import Dict, Any

from aiogram import F
from aiogram.types import CallbackQuery, Message, FSInputFile

from .bot_core import bot, router, HISTORY, TASK_INDEX
from .config import (
    SUPPORT_CHAT_ID,
    BITRIX_MODE,
    BITRIX_SMART_ENTITY_ID,
)
from .localization import t, TEXTS
from .helpers import is_admin, replace_status_line
from .bitrix_api import (
    bitrix_task_comment,
    bitrix_task_complete,
    bitrix_crm_timeline_comment,
)


async def _ensure_admin(obj) -> bool:
    """Проверка прав админа для команд и callback-ов."""
    user_id = obj.from_user.id
    if not is_admin(user_id):
        msg = t("admin_no_access", "RU")
        if isinstance(obj, Message):
            await obj.answer(msg)
        else:
            await obj.answer(msg, show_alert=True)
        return False
    return True


# -------------------- Кнопки на карточке (В работу / Закрыть) --------------------


@router.callback_query(F.data.startswith("adm:"))
async def admin_card_action(callback: CallbackQuery):
    if not await _ensure_admin(callback):
        return

    data = callback.data.split(":")
    if len(data) != 3:
        await callback.answer("Некорректные данные", show_alert=True)
        return

    _, action, external_id = data
    info: Dict[str, Any] | None = TASK_INDEX.get(external_id)

    if not info or not callback.message or not callback.message.text:
        await callback.answer("Карточка не найдена", show_alert=True)
        return

    msg = callback.message
    text = msg.text

    # Пытаемся вытащить язык из второй строки "🌐 RU"
    lang = "RU"
    lines = text.splitlines()
    if len(lines) >= 2 and "🌐" in lines[1]:
        lang = lines[1].split("🌐", 1)[1].strip()

    if action == "work":
        new_status = t("card_status_work", lang)
        bitrix_comment = "Заявка взята в работу из Telegram"
    elif action == "close":
        new_status = t("card_status_closed", lang)
        bitrix_comment = "Заявка закрыта из Telegram"
    else:
        await callback.answer("Неизвестное действие", show_alert=True)
        return

    # Обновляем текст карточки
    new_text = replace_status_line(text, new_status)
    try:
        await msg.edit_text(new_text, reply_markup=msg.reply_markup)
    except Exception:
        # если уже кто-то успел отредактировать — молча игнорируем
        pass

    # Обновляем наши структуры
    info["status"] = new_status
    task_id = info.get("task_id")
    crm_item_id = info.get("crm_item_id")

    for rec in reversed(HISTORY):
        if rec["id"] == external_id:
            rec["status"] = new_status
            break

    # Пишем комментарий в Bitrix
    if action == "close":
        if BITRIX_MODE == "CRM" and crm_item_id:
            await asyncio.to_thread(
                bitrix_crm_timeline_comment,
                int(BITRIX_SMART_ENTITY_ID),
                int(crm_item_id),
                bitrix_comment,
            )
        elif task_id:
            await asyncio.to_thread(bitrix_task_comment, int(task_id), bitrix_comment)
            await asyncio.to_thread(bitrix_task_complete, int(task_id))
    else:  # work
        if BITRIX_MODE == "CRM" and crm_item_id:
            await asyncio.to_thread(
                bitrix_crm_timeline_comment,
                int(BITRIX_SMART_ENTITY_ID),
                int(crm_item_id),
                bitrix_comment,
            )
        elif task_id:
            await asyncio.to_thread(bitrix_task_comment, int(task_id), bitrix_comment)

    await callback.answer("Статус обновлён")

# -------------------- /whereami --------------------


@router.message(F.text == "/whereami")
async def cmd_whereami(message: Message):
    if not await _ensure_admin(message):
        return

    lang = "RU"
    await message.answer(
        t("whereami", lang).format(cid=message.chat.id)
    )

# -------------------- /stats --------------------


@router.message(F.text == "/stats")
async def cmd_stats(message: Message):
    if not await _ensure_admin(message):
        return

    lang = "RU"
    n = len(HISTORY)

    status_new = t("card_status_new", lang)
    status_work = t("card_status_work", lang)
    status_closed = t("card_status_closed", lang)

    new_count = sum(1 for r in HISTORY if r["status"] == status_new)
    work_count = sum(1 for r in HISTORY if r["status"] == status_work)
    closed_count = sum(1 for r in HISTORY if r["status"] == status_closed)

    cats = Counter(r["category"] for r in HISTORY if r.get("category"))
    cats_str = ", ".join(f"{k}={v}" for k, v in cats.most_common()) or "нет данных"

    header = t("stats_header", lang).format(n=n)
    body = t("stats_line", lang).format(
        new=new_count,
        work=work_count,
        closed=closed_count,
        cats=cats_str,
    )

    await message.answer(f"{header}\n{body}")

# -------------------- /export --------------------


@router.message(F.text == "/export")
async def cmd_export(message: Message):
    if not await _ensure_admin(message):
        return

    if not HISTORY:
        await message.answer(t("export_empty", "RU"))
        return

    fd, path = tempfile.mkstemp(prefix="export_", suffix=".csv")
    os.close(fd)

    try:
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(
                [
                    "id",
                    "date",
                    "language",
                    "name",
                    "phone",
                    "category",
                    "status",
                    "text_len",
                    "attachments_count",
                ]
            )
            for rec in HISTORY:
                writer.writerow(
                    [
                        rec["id"],
                        rec["date"],
                        rec["language"],
                        rec["name"],
                        rec["phone"],
                        rec["category"],
                        rec["status"],
                        rec["text_len"],
                        rec["attachments_count"],
                    ]
                )

        await message.answer_document(
            FSInputFile(path),
            caption=t("export_ready", "RU"),
        )
    finally:
        if os.path.exists(path):
            os.remove(path)
