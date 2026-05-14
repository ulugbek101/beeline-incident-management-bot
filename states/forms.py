from aiogram.fsm.state import State, StatesGroup


class UserRegistrationForm(StatesGroup):
    fullname = State()
    phone_number = State()


class IncidentRegistrationForm(StatesGroup):
    fullname = State()
    description = State()
    phone_number = State()
