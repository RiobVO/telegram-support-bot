from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    Lang = State()
    Consent = State()
    Name = State()
    Phone = State()
    Category = State()
    Text = State()
    Attachments = State()
    Review = State()
    EditChoice = State()
