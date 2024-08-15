from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import asyncio
import logging
import ast
from dotenv import load_dotenv
import os
from handlers.globe import router
from handlers.back import back_router
from database.core import AsyncCore
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.models import *
from sqlalchemy.orm import joinedload

engine = create_async_engine(url='sqlite+aiosqlite:///tg_bot_db.sqlite3', echo=True)
async_session = async_sessionmaker(engine)


async def main():
    #anrkad = await AsyncCore.add_user()
    async with async_session() as session:
        stmt = (
            select(TournamentORM)
            .options(
                joinedload(TournamentORM.registrations).joinedload(RegistrationORM.user).joinedload(
                    UserORM.accounts),
                joinedload(TournamentORM.set_votes),
                joinedload(TournamentORM.winning_set)
            )
            .where(TournamentORM.id == tournament_id)
        )
        result = await session.execute(stmt)
        anrkad = result.scalar_one_or_none()

    print(anrkad)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Тест завершен')
