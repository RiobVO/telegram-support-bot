from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from .localization import TEXTS, CATEGORIES_BY_LANG, t



def kb_languages() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=TEXTS["RU"]["lang_ru"])
    b.button(text=TEXTS["UZ"]["lang_uz"])
    b.button(text=TEXTS["EN"]["lang_en"])
    b.adjust(3)
    return b.as_markup(resize_keyboard=True, one_time_keyboard=True)

def kb_consent(lang: str) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=t("consent_agree", lang))
    return b.as_markup(resize_keyboard=True)

def kb_categories(lang: str) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    for cat in CATEGORIES_BY_LANG[lang]:
        b.button(text=cat)
    b.adjust(2)
    return b.as_markup(resize_keyboard=True)

def kb_attachments(lang: str) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=t("btn_done", lang))
    b.button(text=t("btn_skip", lang))
    b.adjust(2)
    return b.as_markup(resize_keyboard=True)

def kb_review(lang: str) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=t("btn_edit", lang))
    b.button(text=t("btn_send", lang))
    b.adjust(2)
    return b.as_markup(resize_keyboard=True)

def kb_edit_menu(lang: str) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=t("edit_name", lang))
    b.button(text=t("edit_phone", lang))
    b.button(text=t("edit_category", lang))
    b.button(text=t("edit_text", lang))
    b.button(text=t("edit_attachments", lang))
    b.adjust(2, 2, 1)
    return b.as_markup(resize_keyboard=True)


def kb_admin_card(external_id: str, lang: str) -> InlineKeyboardMarkup:
    ib = InlineKeyboardBuilder()
    ib.button(text="🛠 В работу", callback_data=f"adm:work:{external_id}")
    ib.button(text="✅ Закрыть", callback_data=f"adm:close:{external_id}")
    return ib.as_markup()

# Post-submit keyboard
def kb_after_submit(lang: str) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=t("btn_new_request", lang))
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)