from typing import List, Dict, Any, Optional
import asyncio

from aiogram import F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.enums import ContentType

from .bot_core import bot, router, HISTORY, TASK_INDEX
from .config import (
    SUPPORT_CHAT_ID,
    BITRIX_MODE,
    BITRIX_SMART_ENTITY_ID,
    BITRIX_SMART_CATEGORY_ID,
    BITRIX_SMART_STAGE_ID,
    BITRIX_RESPONSIBLE_ID,
)
from .localization import t, TEXTS, CATEGORIES_BY_LANG
from .states import Form
from .keyboards import (
    kb_languages,
    kb_consent,
    kb_categories,
    kb_attachments,
    kb_review,
    kb_edit_menu,
    kb_admin_card,
    kb_after_submit,
)
from .helpers import (
    validate_name,
    validate_phone,
    truncate,
    generate_external_id,
    card_text,
    build_bitrix_description,
)
from .bitrix_api import (
    bitrix_task_add,
    bitrix_task_update_status,
    bitrix_task_complete,
    bitrix_task_comment,
    bitrix_crm_item_add,
    bitrix_crm_item_update,
    bitrix_crm_timeline_comment,
)


# -------------------- Старт и выбор языка --------------------


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.Lang)
    await message.answer(
        t("lang_prompt", "RU"),
        reply_markup=kb_languages(),
    )


@router.message(Form.Lang)
async def set_lang(message: Message, state: FSMContext):
    text = (message.text or "").strip()

    if text not in {"RU", "UZ", "EN"}:
        await message.answer(TEXTS["RU"]["lang_prompt"], reply_markup=kb_languages())
        return

    await state.update_data(lang=text, attachments=[], category=None)
    await message.answer(
        t("consent_text", text),
        reply_markup=kb_consent(text),
    )
    await state.set_state(Form.Consent)


# -------------------- Согласие и ФИО --------------------


@router.message(Form.Consent)
async def consent_step(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "RU")

    if (message.text or "").strip() != t("consent_agree", lang):
        await message.answer(
            t("consent_text", lang),
            reply_markup=kb_consent(lang),
        )
        return

    await state.set_state(Form.Name)
    await message.answer(
        t("ask_name", lang),
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Form.Name)
async def name_step(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "RU")
    text = (message.text or "").strip()

    if not validate_name(text):
        await message.answer(t("invalid_name", lang))
        return

    await state.update_data(name=text)
    await state.set_state(Form.Phone)
    await message.answer(t("ask_phone", lang))


@router.message(Form.Phone)
async def phone_step(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "RU")
    text = (message.text or "").strip()

    if not validate_phone(text):
        await message.answer(t("invalid_phone", lang))
        return

    await state.update_data(phone=text)
    await state.set_state(Form.Category)
    await message.answer(
        t("choose_category", lang),
        reply_markup=kb_categories(lang),
    )


# -------------------- Категория и текст --------------------


@router.message(Form.Category)
async def category_step(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "RU")
    text = (message.text or "").strip()

    if text not in CATEGORIES_BY_LANG.get(lang, []):
        await message.answer(
            t("choose_category", lang),
            reply_markup=kb_categories(lang),
        )
        return

    await state.update_data(category=text)
    await state.set_state(Form.Text)
    await message.answer(
        t("ask_text", lang),
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Form.Text)
async def text_step(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "RU")
    text = (message.text or "").strip()

    if len(text) < 15:
        await message.answer(t("text_too_short", lang))
        return

    await state.update_data(text=text)
    await state.set_state(Form.Attachments)
    await message.answer(
        t("attachments_hint", lang),
        reply_markup=kb_attachments(lang),
    )


# -------------------- Вложения --------------------


@router.message(
    Form.Attachments,
    F.text.in_(
        {
            TEXTS["RU"]["btn_done"],
            TEXTS["RU"]["btn_skip"],
            TEXTS["UZ"]["btn_done"],
            TEXTS["UZ"]["btn_skip"],
            TEXTS["EN"]["btn_done"],
            TEXTS["EN"]["btn_skip"],
        }
    ),
)
async def attachments_done(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "RU")
    attachments = data.get("attachments", [])

    await state.set_state(Form.Review)

    text_sample = truncate(data.get("text", ""))
    review = (
        f"{t('review_title', lang)}\n\n"
        + t("review_fields", lang).format(
            lang=lang,
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            cat=data.get("category", ""),
            text_sample=text_sample,
            n=len(attachments),
        )
    )

    await message.answer(review, reply_markup=kb_review(lang))


@router.message(
    Form.Attachments,
    F.content_type.in_(
        {
            ContentType.PHOTO,
            ContentType.DOCUMENT,
            ContentType.VIDEO,
            ContentType.VOICE,
        }
    ),
)
async def attachments_collect(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "RU")
    attachments: List[Dict[str, str]] = data.get("attachments", [])

    if len(attachments) >= 10:
        await message.answer(t("too_many_attachments", lang))
        return

    if message.content_type == ContentType.PHOTO:
        file_id = message.photo[-1].file_id
        attachments.append({"type": "photo", "file_id": file_id})
    elif message.content_type == ContentType.DOCUMENT:
        attachments.append({"type": "document", "file_id": message.document.file_id})
    elif message.content_type == ContentType.VIDEO:
        attachments.append({"type": "video", "file_id": message.video.file_id})
    elif message.content_type == ContentType.VOICE:
        attachments.append({"type": "voice", "file_id": message.voice.file_id})

    await state.update_data(attachments=attachments)


# -------------------- Обзор и правки --------------------


@router.message(
    Form.Review,
    F.text.in_(
        {
            TEXTS["RU"]["btn_edit"],
            TEXTS["UZ"]["btn_edit"],
            TEXTS["EN"]["btn_edit"],
        }
    ),
)
async def review_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "RU")

    await state.set_state(Form.EditChoice)
    await message.answer(
        t("edit_what", lang),
        reply_markup=kb_edit_menu(lang),
    )


@router.message(Form.EditChoice)
async def edit_choice(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "RU")
    txt = (message.text or "").strip()

    mapping = {
        t("edit_name", lang): ("Name", t("ask_name", lang)),
        t("edit_phone", lang): ("Phone", t("ask_phone", lang)),
        t("edit_category", lang): ("Category", t("choose_category", lang)),
        t("edit_text", lang): ("Text", t("ask_text", lang)),
        t("edit_attachments", lang): ("Attachments", t("attachments_hint", lang)),
    }

    if txt not in mapping:
        await message.answer(
            t("edit_what", lang),
            reply_markup=kb_edit_menu(lang),
        )
        return

    target_state, prompt = mapping[txt]

    await message.answer(
        t("review_back", lang).format(what=txt),
        reply_markup=ReplyKeyboardRemove(),
    )

    if target_state == "Name":
        await state.set_state(Form.Name)
        await message.answer(prompt)
    elif target_state == "Phone":
        await state.set_state(Form.Phone)
        await message.answer(prompt)
    elif target_state == "Category":
        await state.set_state(Form.Category)
        await message.answer(
            prompt,
            reply_markup=kb_categories(lang),
        )
    elif target_state == "Text":
        await state.set_state(Form.Text)
        await message.answer(prompt)
    elif target_state == "Attachments":
        await state.update_data(attachments=[])
        await state.set_state(Form.Attachments)
        await message.answer(
            prompt,
            reply_markup=kb_attachments(lang),
        )


# -------------------- Отправка заявки --------------------


@router.message(
    Form.Review,
    F.text.in_(
        {
            TEXTS["RU"]["btn_send"],
            TEXTS["UZ"]["btn_send"],
            TEXTS["EN"]["btn_send"],
        }
    ),
)
async def review_send(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "RU")

    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    category = (data.get("category") or "").strip()
    text = (data.get("text") or "").strip()
    attachments: List[Dict[str, str]] = data.get("attachments", [])

    external_id = generate_external_id()
    status_new = t("card_status_new", lang)

    # 1) Карточка в служебный канал
    msg = await bot.send_message(
        chat_id=SUPPORT_CHAT_ID,
        text=card_text(lang, external_id, name, phone, category, text, status_new),
        reply_markup=kb_admin_card(external_id, lang),
    )

    # 2) Вложения отдельными сообщениями
    send_tasks = []
    for a in attachments:
        if a["type"] == "photo":
            send_tasks.append(
                bot.send_photo(
                    SUPPORT_CHAT_ID,
                    a["file_id"],
                    reply_to_message_id=msg.message_id,
                )
            )
        elif a["type"] == "document":
            send_tasks.append(
                bot.send_document(
                    SUPPORT_CHAT_ID,
                    a["file_id"],
                    reply_to_message_id=msg.message_id,
                )
            )
        elif a["type"] == "video":
            send_tasks.append(
                bot.send_video(
                    SUPPORT_CHAT_ID,
                    a["file_id"],
                    reply_to_message_id=msg.message_id,
                )
            )
        elif a["type"] == "voice":
            send_tasks.append(
                bot.send_voice(
                    SUPPORT_CHAT_ID,
                    a["file_id"],
                    reply_to_message_id=msg.message_id,
                )
            )

    if send_tasks:
        await asyncio.gather(*send_tasks)

    # 3) Создаём сущность в Bitrix24
    description = build_bitrix_description(
        lang,
        name,
        phone,
        category,
        text,
        attachments,
        external_id,
    )
    title = f"Жалоба {name} ({phone}) — {external_id}"

    task_id: Optional[int] = None
    crm_item_id: Optional[int] = None

    if BITRIX_MODE == "CRM" and BITRIX_SMART_ENTITY_ID:
        crm_fields: Dict[str, Any] = {
            "title": title,
            "assignedById": int(BITRIX_RESPONSIBLE_ID),
        }

        if BITRIX_SMART_CATEGORY_ID:
            try:
                crm_fields["categoryId"] = int(BITRIX_SMART_CATEGORY_ID)
            except Exception:
                crm_fields["categoryId"] = BITRIX_SMART_CATEGORY_ID

        if BITRIX_SMART_STAGE_ID:
            crm_fields["stageId"] = BITRIX_SMART_STAGE_ID

        crm_item_id = await asyncio.to_thread(
            bitrix_crm_item_add,
            int(BITRIX_SMART_ENTITY_ID),
            crm_fields,
        )

        if crm_item_id:
            await asyncio.to_thread(
                bitrix_crm_timeline_comment,
                int(BITRIX_SMART_ENTITY_ID),
                int(crm_item_id),
                description,
            )
        else:
            await bot.send_message(SUPPORT_CHAT_ID, t("bitrix_error", lang))
    else:
        task_id = await asyncio.to_thread(
            bitrix_task_add,
            title,
            description,
            BITRIX_RESPONSIBLE_ID,
        )
        if task_id is None:
            await bot.send_message(SUPPORT_CHAT_ID, t("bitrix_error", lang))

    # 3.1) Добавляем в карточку ID сущности
    extra_line = ""
    if crm_item_id:
        extra_line = f"\n🧩 CRM item: {crm_item_id}"
    elif task_id:
        extra_line = f"\n🧩 Task ID: {task_id}"

    if extra_line:
        try:
            await bot.edit_message_text(
                chat_id=SUPPORT_CHAT_ID,
                message_id=msg.message_id,
                text=msg.text + extra_line,
                reply_markup=msg.reply_markup,
            )
        except Exception:
            pass

    # 4) Обновляем индексы
    TASK_INDEX[external_id] = {
        "task_id": task_id,
        "crm_item_id": crm_item_id,
        "channel_message_id": msg.message_id,
        "status": status_new,
    }

    HISTORY.append(
        {
            "id": external_id,
            "date": msg.date,
            "language": lang,
            "name": name,
            "phone": phone,
            "category": category,
            "status": status_new,
            "text_len": len(text),
            "attachments_count": len(attachments),
        }
    )

    # 5) Ответ пользователю и предложение создать ещё одну заявку
    await message.answer(
        t("submitted", lang).format(eid=external_id),
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer(
        t("after_submit_prompt", lang),
        reply_markup=kb_after_submit(lang),
    )
    await state.clear()


# -------------------- Шорткат "новая заявка" --------------------


@router.message(
    F.text.in_(
        {
            TEXTS["RU"]["btn_new_request"],
            TEXTS["UZ"]["btn_new_request"],
            TEXTS["EN"]["btn_new_request"],
        }
    )
)
async def new_request_shortcut(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.Lang)
    await message.answer(
        t("lang_prompt", "RU"),
        reply_markup=kb_languages(),
    )
