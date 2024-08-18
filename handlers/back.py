from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import chat_action
from keyboards.main_kb import start_kb, nearest_weekend
from state import FindGame,MyGames, Stats
from database.core import AsyncCore

back_router = Router()

#
# @back_router.callback_query(F.data == 'back_to_start')
# async def find_game(callback: CallbackQuery, state: FSMContext):
#     await state.clear()
#     sts = await AsyncCore.get_user_sts(callback.from_user.id)
#     print(f"\033[92m {sts} - ok \033[0m")
#     print(f"\033[92m AsyncCore.get_user_sts (F.data == back_to_start) - ok \033[0m")
#     total_games = sts.wins + sts.losses
#     if total_games > 0:
#         winrate = (sts.wins / total_games) * 100
#         winrate_text = f"{winrate:.2f}%"
#     else:
#         winrate_text = "N/A"
#     await callback.message.edit_text(text=f'Привет, {sts.username},\n'
#                               f'Добро пожаловать в таверну "Гнутая мишень"!\n'
#                               f'Здесь ты можешь записаться на драфт в МТГА\n\n'
#                               f'Твоя статистика:\n'
#                               f'Количество побед: {sts.wins}\n'
#                               f'Винрейт: {winrate_text}',
#                          reply_markup=start_kb)

    #
    # @back_router.callback_query(F.data == 'back_to_find_menu')
    # async def find_game(callback: CallbackQuery, state: FSMContext):
    #     await state.clear()
    #     sts = await AsyncCore.get_user_sts(callback.from_user.id)
    #     total_games = sts.wins + sts.losses
    #     if total_games > 0:
    #         winrate = (sts.wins / total_games) * 100
    #         winrate_text = f"{winrate:.2f}%"
    #     else:
    #         winrate_text = "N/A"
    #     await callback.message.edit_text(text=f'Привет, {sts.username},\n'
    #                               f'Добро пожаловать в таверну "Гнутая мишень"!\n'
    #                               f'Здесь ты можешь записаться на драфт в МТГА\n\n'
    #                               f'Твоя статистика:\n'
    #                               f'Количество побед: {sts.wins}\n'
    #                               f'Винрейт: {winrate_text}',
    #                          reply_markup=start_kb)
