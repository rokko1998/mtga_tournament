from aiogram.fsm.state import StatesGroup, State


class FindGame(StatesGroup):
    find_menu = State()
    tournament_info = State()
    vote_for_set = State()
    enter_game_account = State()

class MyGames(StatesGroup):
    my_games_menu = State()
    registered_tournament_info = State()
    update_set_preference = State()
    update_game_account = State()
    ongoing_tournament = State()
    enter_match_result = State()

class Stats(StatesGroup):
    stats_menu = State()
    manage_accounts = State()
    account_stats = State()


