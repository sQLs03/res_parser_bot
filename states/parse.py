from aiogram.dispatcher.filters.state import State, StatesGroup


class ParseFile(StatesGroup):
    waiting_for_file = State()

class HistoInfo(StatesGroup):
    waiting_timeframe = State()
    waiting_delta = State()
    waiting_unx = State()
    waiting_market = State()

