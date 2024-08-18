from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import chat_action
from keyboards.main_kb import start_kb, nearest_weekend
from state import FindGame,MyGames, Stats
from database.core import AsyncCore
from database.models import TournamentStatus

router = Router()


# Сколько турниров сыграно, сколько всего побед +%wins
# Топ 3 Имена пользователей игроков с большим количеством побед в турнирах
# Ближайший турнир на который зарегистрирован пользователь (дата и время),
# если такой есть.

# Message хендлер команды старт, главное меню
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await AsyncCore.add_user(message.from_user.id, message.from_user.username)
    await state.clear()
    sts = await AsyncCore.get_user_sts(message.from_user.id)
    total_games = sts.wins + sts.losses
    if total_games > 0:
        winrate = (sts.wins / total_games) * 100
        winrate_text = f"{winrate:.2f}%"
    else:
        winrate_text = "N/A"
    await message.answer(text=f'Привет, {sts.username},\n'
                              f'Добро пожаловать в таверну "Гнутая мишень"!\n'
                              f'Здесь ты можешь записаться на драфт в МТГА\n\n'
                              f'Твоя статистика:\n'
                              f'Количество побед: {sts.wins}\n'
                              f'Винрейт: {winrate_text}',
                         reply_markup=start_kb)

# Хендлер кнопки "Найти игру" главного меню, выводит список турниров этой недели
@router.callback_query(F.data == 'find_game')
async def find_game(callback: CallbackQuery, state: FSMContext):
    dates = await nearest_weekend()
    # print(f"\033[92m{dates}\033[0m")
    tournaments = await AsyncCore.upsert_tournaments(dates)
    keyboard = InlineKeyboardBuilder()

    for tournament in tournaments:
        tournament_id = tournament.id
        tournament_name = tournament.name
        keyboard.button(
            text=f'{tournament_name}',
            callback_data=f'tournament_{tournament_id}'
        )
    keyboard.button(text='Назад', callback_data='back_to_start')

    await callback.answer('Выберите турнир')
    await state.set_state(FindGame.find_menu)
    await callback.message.edit_text('Выберите турнир:', reply_markup=keyboard.adjust(2).as_markup())

# Хендлер кнопки "Турнир #id" в меню "Найти игру", выводит инфу по турниру и разные кнопки
@router.callback_query(FindGame.find_menu)
async def tournament_info(callback: CallbackQuery, state: FSMContext):
    tournament_id = callback.data.split("_")[1]
    user_id = callback.from_user.id
    await state.update_data(tournament_id=tournament_id)
    tournament = await AsyncCore.tournament_details(tournament_id)
    # Извлечение данных
    registered_players = tournament.registrations
    set_votes = tournament.set_votes
    winning_set_name = (tournament.winning_set.description if tournament.winning_set else "Сет еще не определен")

    # условие для выбора клавиатуры/текста
    user_registered = any(reg.user_id == user_id for reg in tournament.registrations)
    keyboard = InlineKeyboardBuilder()
    if tournament.status == TournamentStatus.PLANNED:
        # Подготовка данных для отправки
        players_info = "\n".join(
            [f"{reg.user.username} ({', '.join(acc.username for acc in reg.user.accounts)})" for reg in
             registered_players]
        )

        top_sets = sorted(set_votes, key=lambda sv: sv.votes, reverse=True)[:3]
        top_sets_info = "\n".join([f"{sv.set_name}: {sv.votes} голосов" for sv in top_sets])
        message = (
            f"Турнир: {tournament.name}\n"
            f"Дата: {tournament.date}\n"
            f"Статус: Запланирован\n\n"
            f"Зарегистрированные игроки ({len(registered_players)}):\n{players_info}\n\n"
            f"Топ-3 сета в голосовании:\n{top_sets_info}"
        )
        if user_registered:
            await state.set_state(MyGames.my_games_menu)
            keyboard.button(text='Отменить регистрацию', callback_data=f'cancel_registration_{tournament_id}')
            keyboard.button(text='Изменить выбор сета', callback_data=f'change_set_{tournament_id}')
            keyboard.button(text='Назад', callback_data='find_game')
            await callback.message.edit_text(text=message, reply_markup=keyboard.adjust(2).as_markup())
        else:
            await state.set_state(FindGame.tournament_info)
            keyboard.row(
                InlineKeyboardButton(text='Зарегистрироваться', callback_data=f'reg_{tournament_id}')
            )
            keyboard.row(
                InlineKeyboardButton(text='Обновить', callback_data=f'refresh_{tournament_id}'),
                InlineKeyboardButton(text='Назад', callback_data='find_game')
            )
            await callback.message.edit_text(text=message, reply_markup=keyboard.as_markup())

    elif tournament.status == TournamentStatus.UPCOMING:
        if user_registered:
            await callback.message.edit_text('Выберите турнир:', reply_markup=keyboard.adjust(2).as_markup())
        else:
            await callback.message.edit_text('Выберите турнир:', reply_markup=keyboard.adjust(2).as_markup())

    elif tournament.status == TournamentStatus.ONGOING:
        if user_registered:
            await callback.message.edit_text('Выберите турнир:', reply_markup=keyboard.adjust(2).as_markup())
        else:
            await callback.message.edit_text('Выберите турнир:', reply_markup=keyboard.adjust(2).as_markup())



    #пытаюсь собрать этот большой и сложный хендлер

@router.callback_query(F.data == 'my_games')
async def tournament_info(callback: CallbackQuery, state: FSMContext):
    tnmts = await AsyncCore.get_user_tournaments(callback.from_user.id)

    if not tnmts:
        dates = await nearest_weekend()
        keyboard = InlineKeyboardBuilder()

        for date in dates:
            tournament = await AsyncCore.get_tournament_by_date(date)
            if tournament:
                # Если турнир с такой датой уже существует
                tournament_id = tournament.id
                tournament_name = tournament.name
            else:
                # Если турнира с такой датой нет, создаём новый
                tournament_id, tournament_name = await AsyncCore.create_tournament(date)

            keyboard.button(
                text=f'{tournament_name}',
                callback_data=f'tournament_{tournament_id}'
            )
        keyboard.adjust(2)  # Сначала настраиваем кнопки
        keyboard.button(text='Назад', callback_data='back_to_start')
        keyboard.adjust(2)  # Устанавливаем, что кнопка "Назад" будет одна на своей строке

        await callback.answer(f'У вас нет активных турниров\n'
                              f'Вы перенаправлены в меню Поиска игры')
        await state.set_state(FindGame.find_menu)
        await callback.message.edit_text('Выберите турнир:', reply_markup=keyboard.as_markup())
    elif len(tnmts) == 1:
        tournament = tnmts[0]
        await state.set_state(MyGames.registered_tournament_info)
        await state.update_data(tournament=tournament.id)
        await callback.answer(f'У вас только один турнир\n'
                              f'    Инфо по турниру')
        tournament = await AsyncCore.tournament_details(tournament.id)
        # Извлечение данных
        registered_players = tournament.registrations
        set_votes = tournament.set_votes

        # Подготовка данных для отправки
        players_info = "\n".join(
            [f"{reg.user.username} ({', '.join(acc.username for acc in reg.user.accounts)})" for reg in
             registered_players]
        )

        if tournament.status == TournamentStatus.PLANNED:
            # Топ-3 сета по голосам
            top_sets = sorted(set_votes, key=lambda sv: sv.votes, reverse=True)[:3]
            top_sets_info = "\n".join([f"{sv.set_name}: {sv.votes} голосов" for sv in top_sets])
            message = (
                f"Турнир: {tournament.name}\n"
                f"Дата: {tournament.date}\n"
                f"Статус: Запланирован\n\n"
                f"Зарегистрированные игроки ({len(registered_players)}):\n{players_info}\n\n"
                f"Топ-3 сета в голосовании:\n{top_sets_info}"
            )
            set_kb = InlineKeyboardBuilder()
            sets = await AsyncCore.get_set()
            for set in sets:
                set_kb.button(text=set.name, callback_data=set.id)
            set_kb.button(text='Back', callback_data='back_to_find_menu')
        else:
            winning_set_name = (
                tournament.winning_set.description if tournament.winning_set else "Сет еще не определен"
            )
            message = (
                f"Турнир: {tournament.name}\n"
                f"Дата: {tournament.date}\n"
                f"Статус: {tournament.status.value}\n\n"
                f"Зарегистрированные игроки ({len(registered_players)}):\n{players_info}\n\n"
                f"Победивший сет: {winning_set_name}"
            )
            set_kb = InlineKeyboardBuilder()
            # Клава-заглушка, надо будет переделать
            sets = await AsyncCore.get_set()
            for set in sets:
                set_kb.button(text=set.name, callback_data=set.id)
        await callback.message.edit_text(text=message, reply_markup=set_kb)
    else:
        await state.set_state(MyGames.my_games_menu)
        keyboard = InlineKeyboardBuilder()
        for tnmt in tnmts:
            keyboard.button(text=tnmt.name, callback_data=f'tournament_{tnmt.id}')
        await callback.message.edit_text('Ваши туриниры:', reply_markup=keyboard.adjust(2).as_markup())




@router.callback_query(F.data == 'find_game')
async def find_game(callback: CallbackQuery):
    dates = await nearest_weekend()
    #tournament_ids = []
    keyboard = InlineKeyboardBuilder()
    for date in dates:
        element = await AsyncCore.create_tournament(date)
        #tournament_ids.append(tournament_id)
        keyboard.button(text=str(element), callback_data=f'tournament_{element}')
    await callback.answer('Турнир выбран!')
    #await state.update_data(chdate=callback.data)
    #await state.set_state(cg_state.ch_set)
    await callback.message.edit_text('chose tournament:', reply_markup= keyboard.adjust(3).as_markup())

