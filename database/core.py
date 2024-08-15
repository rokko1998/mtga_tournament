from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from database.models import *

engine = create_async_engine(url='sqlite+aiosqlite:///tg_bot_db.sqlite3', echo=True)
async_session = async_sessionmaker(engine)


class AsyncCore:
    @staticmethod
    async def create_tables():
        """Создает все таблицы в базе данных."""
        async with engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def tournament_details(tournament_id: int):
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
            return result.scalars().unique().one_or_none()


    # @staticmethod
    # async def get_set():
    #     async with async_session() as session:
    #         return await session.scalar(select(SetORM)).all()

    @staticmethod
    async def get_set():
        async with async_session() as session:
            return (await session.scalars(select(SetORM))).all()
    @staticmethod
    async def get_user_sts(tg_id: BigInteger):
        async with async_session() as session:
            return await session.scalar(select(UserORM).where(UserORM.tg_id == tg_id))

    @staticmethod
    async def get_tournament(tnmt_id: int):
        async with async_session() as session:
            return await session.scalar(select(TournamentORM).where(TournamentORM.id == tnmt_id))

    @staticmethod   # Выгружват все турниры для конкретного пользователя по tg_id.
    async def get_user_tournaments(tg_id: int):
        async with async_session() as session:
            # Сначала находим пользователя по tg_id
            user = await session.scalar(
                select(UserORM).where(UserORM.tg_id == tg_id)
            )

            if user is None:
                print("Залупа")
                return []  # Возвращаем пустой список, если пользователь не найден

            # Запрашиваем турниры, в которых зарегистрирован этот пользователь
            result = await session.execute(
                select(TournamentORM)
                .join(RegistrationORM)
                .where(RegistrationORM.user_id == user.id)
                .options(selectinload(TournamentORM.registrations))
            )
            return result.scalars().all()  # Возвращаем список турниров

    @staticmethod
    async def get_tournament_by_date(date: datetime.datetime):
        async with async_session() as session:
            return await session.scalar(select(TournamentORM).where(TournamentORM.date == date))


    @staticmethod
    async def create_tournament(date: datetime.datetime):
        """Создает турнир на указанную дату и возвращает его ID."""
        async with async_session() as session:
            result = await session.execute(
                 insert(TournamentORM)
                .values(
                    name=f"Турнир {date.strftime('%Y-%m-%d %H:%M')}",
                    date=date,
                    status=TournamentStatus.PLANNED,
                )
                .returning(TournamentORM.id, TournamentORM.name)
            )
            await session.commit()
            return result.fetchone()

    @staticmethod
    async def add_user(tg_id: BigInteger, username: str):
        """Добавляет нового пользователя в базу данных."""
        async with async_session() as session:
            await session.execute(insert(UserORM).values(tg_id=tg_id, username=username).prefix_with("OR IGNORE"))
            await session.commit()

    @staticmethod
    async def get_user_by_tg_id(tg_id: int):
        """Получает пользователя по Telegram ID."""
        async with async_session() as session:
            return await session.scalar(select(UserORM).where(UserORM.tg_id == tg_id))

    @staticmethod
    async def register_user_for_tournament(user_id: int, tournament_id: int):
        """Регистрирует пользователя на турнир."""
        async with async_session() as session:
            async with session.begin():
                registration = RegistrationORM(user_id=user_id, tournament_id=tournament_id, status='registered')
                session.add(registration)
    #
    # @staticmethod
    # async def create_tournament(name: str, date: datetime.datetime, status: str, set_name: str):
    #     """Создает новый турнир."""
    #     async with async_session() as session:
    #         async with session.begin():
    #             tournament = TournamentORM(
    #                 name=f"Турнир на {date.strftime('%d.%m %H:%M')}",
    #                 date=date,
    #                 status=TournamentStatus.UPCOMING,
    #                 set="",
    #                 created_at=datetime.datetime.utcnow(),
    #                 updated_at=datetime.datetime.utcnow(),
    #             )
    #             session.add(tournament)

    @staticmethod
    async  def set_tournament_set():
        pass
    #
    # @staticmethod
    # async def get_tournament_by_id(tournament_id: int):
    #     """Получает турнир по его ID."""
    #     async with async_session() as session:
    #         result = await session.scalar(TournamentORM.select().where(TournamentORM.id == tournament_id))
    #         return result

    @staticmethod
    async def add_match(tournament_id: int, player1_id: int, player2_id: int):
        """Добавляет матч в турнир."""
        async with async_session() as session:
            async with session.begin():
                match = MatchORM(tournament_id=tournament_id, player1_id=player1_id, player2_id=player2_id, result='')
                session.add(match)

    @staticmethod
    async def update_match_result(match_id: int, result: str):
        """Обновляет результат матча."""
        async with async_session() as session:
            async with session.begin():
                match = await session.get(MatchORM, match_id)
                if match:
                    match.result = result

    @staticmethod
    async def update_tournament_stats(user_id: int, tournament_id: int, wins: int, losses: int, draws: int):
        """Обновляет статистику пользователя в рамках турнира."""
        async with async_session() as session:
            async with session.begin():
                stat = TournamentStatsORM(user_id=user_id, tournament_id=tournament_id, wins=wins, losses=losses,
                                          draws=draws)
                session.add(stat)

    @staticmethod
    async def get_user_stats(user_id: int):
        """Получает общую статистику пользователя."""
        async with async_session() as session:
            user = await session.get(UserORM, user_id)
            if user:
                return {
                    'username': user.username,
                    'total_wins': user.total_wins,
                    'total_losses': user.total_losses,
                    'set_stats': await AsyncCore.get_user_set_stats(user_id)
                }

    @staticmethod
    async def get_user_set_stats(user_id: int):
        """Получает статистику пользователя по сетам."""
        async with async_session() as session:
            result = await session.execute(SetStatsORM.select().where(SetStatsORM.user_id == user_id))
            return result.scalars().all()

    @staticmethod
    async def get_top_players(limit: int = 10):
        """Возвращает топ-10 игроков по количеству побед."""
        async with async_session() as session:
            result = await session.execute(
                UserORM.select().order_by(UserORM.total_wins.desc()).limit(limit)
            )
            return result.scalars().all()

    @staticmethod
    async def get_user_rank(user_id: int):
        """Возвращает место пользователя в общем рейтинге."""
        async with async_session() as session:
            user = await session.get(UserORM, user_id)
            if not user:
                return None

            result = await session.execute(
                UserORM.select().where(UserORM.total_wins > user.total_wins)
            )
            count = result.scalar() or 0
            return count + 1

    @staticmethod
    async def close_tournament(tournament_id: int):
        """Закрывает турнир и фиксирует результаты."""
        async with async_session() as session:
            async with session.begin():
                tournament = await session.get(TournamentORM, tournament_id)
                if tournament:
                    tournament.status = 'closed'
                    # Обновляем глобальную статистику пользователей по итогам турнира
                    stats = await session.execute(
                        TournamentStatsORM.select().where(TournamentStatsORM.tournament_id == tournament_id)
                    )
                    for stat in stats.scalars().all():
                        user = await session.get(UserORM, stat.user_id)
                        if user:
                            user.total_wins += stat.wins
                            user.total_losses += stat.losses
                            session.add(user)

    @staticmethod
    async def get_tournament_stats(tournament_id: int):
        """Получает статистику по турниру."""
        async with async_session() as session:
            result = await session.execute(
                TournamentStatsORM.select().where(TournamentStatsORM.tournament_id == tournament_id)
            )
            return result.scalars().all()