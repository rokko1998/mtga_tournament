from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


from utils import nearest_weekend

# start = ReplyKeyboardMarkup(keyboard=[
#     [KeyboardButton(text='Найти игру'),
#      KeyboardButton(text='Мои игры')],
#     [KeyboardButton(text='Статистика')]
# ], input_field_placeholder='Выберите пункт меню ↓', resize_keyboard=True, one_time_keyboard=True)

# Создание основной Inline-клавиатуры
# def get_main_menu_keyboard():
#     keyboard = InlineKeyboardMarkup(row_width=2)
#     keyboard.add(
#         InlineKeyboardButton(text='Найти игру', callback_data='find_game'),
#         InlineKeyboardButton(text='Мои игры', callback_data='my_games')
#     )
#     keyboard.add(InlineKeyboardButton(text='Статистика', callback_data='statistics'))
#     return keyboard

start_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Найти игру', callback_data='find_game'),
     InlineKeyboardButton(text='Мои игры', callback_data='my_games')],
    [InlineKeyboardButton(text='Статистика', callback_data='statistics')]
])



#
# async def nearest_game():
#     dates = await nearest_weekend()
#     first_date = dates[0]
#     existing_tournament = await session.execute(select(TournamentORM).where(TournamentORM.date == first_date))
#     tournaments = []
#
#     for date in dates:
#         existing_tournament = await session.execute(select(TournamentORM).where(TournamentORM.date == date))
#         tournament = existing_tournament.scalar_one_or_none()
#
#         if tournament is None:
#             tournament = TournamentORM(
#                 name=f"Турнир на {date.strftime('%d.%m %H:%M')}",
#                 date=date,
#                 status=TournamentStatus.UPCOMING,
#                 set="",
#                 created_at=datetime.datetime.utcnow(),
#                 updated_at=datetime.datetime.utcnow(),
#             )
#             session.add(tournament)
#
#         await session.commit()
#
#         tournaments.append(tournament)
#
#     keyboard = InlineKeyboardBuilder()
#     for tournament in tournaments:
#         keyboard.button(text=f"{tournament.name}", callback_data=f'tournament_{tournament.id}')
#     return keyboard.adjust(2).as_markup()
#
'''клава для хендлера tournament_info, доделать
async def tournament_info_kb(tnmt):
    keyboard = InlineKeyboardBuilder()
    # Пользователь в нем не зарегистрирован
    # Турнир в статусе planned:
    # Кнопки: зарегистрироваться, назад 
    # Турнир в статусе ongoing:
    # Кнопки: Обновить, назад
    # Пользователь в нем зарегистрирован.         #user.registrstion.(tnmt.status) == regitrstion.status
    # Кнопки: обновить, назад

    for element in range (1,6):
        keyboard.button(text=str(element), callback_data=f'tournament_{element}')
    return keyboard.adjust(3).as_markup()
'''











