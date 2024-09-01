from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from database.models import *
from datetime import datetime, timedelta


engine = create_async_engine(url='sqlite+aiosqlite:///tg_bot_db.sqlite3', echo=True)
async_session = async_sessionmaker(engine)


class AsyncCore:
    @staticmethod
    async def create_tables():
        """Создает все таблицы в базе данных."""
        async with engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all) удаляет все таблицы
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def add_user(tg_id: BigInteger, username: str):
        """Добавляет нового пользователя в базу данных."""
        async with async_session() as session:
            await session.execute(insert(UserORM).values(tg_id=tg_id, username=username).prefix_with("OR IGNORE"))
            await session.commit()


    @staticmethod
    async def get_user_sts(tg_id: BigInteger):
        async with async_session() as session:
            return await session.scalar(select(UserORM).where(UserORM.tg_id == tg_id))

    @staticmethod
    async def upsert_tournaments(dates: list) -> list:
        """Проверяет существование турниров на указанные даты и создает новые, если необходимо."""
        async with async_session() as session:
            # Получаем существующие турниры на указанные даты
            stmt = select(TournamentORM).where(TournamentORM.date.in_(dates))
            result = await session.execute(stmt)
            existing_tournaments = result.scalars().all()
            existing_dates = {t.date for t in existing_tournaments}

            # Определяем даты, для которых нужно создать новые турниры
            new_dates = [date for date in dates if date not in existing_dates]

            new_tournaments = []
            if new_dates:
                # Создаем новые турниры для недостающих дат
                insert_stmt = insert(TournamentORM).values(
                    [
                        {
                            'name': f"Турнир {date.strftime('%Y-%m-%d %H:%M')}",
                            'date': date,
                            'status': TournamentStatus.PLANNED
                        }
                        for date in new_dates
                    ]
                ).returning(TournamentORM.id, TournamentORM.name)

                result = await session.execute(insert_stmt)
                await session.commit()
                new_tournaments = result.fetchall()

            # Объединяем существующие и новые турниры
            all_tournaments = existing_tournaments + [t._asdict() for t in new_tournaments]

            return all_tournaments


    @staticmethod
    async def tournament_details(tournament_id: int) -> dict:
        async with async_session() as session:
            # Запрашиваем данные по турниру
            stmt = (
                select(
                    TournamentORM.name,
                    TournamentORM.date,
                    TournamentORM.status,
                    UserORM.username,
                    MtgORM.username.label("mtg_username"),
                    SetVoteORM.set_name,
                    SetVoteORM.votes
                )
                .join(RegistrationORM, RegistrationORM.tournament_id == TournamentORM.id)
                .join(UserORM, UserORM.id == RegistrationORM.user_id)
                .outerjoin(MtgORM, MtgORM.user_id == UserORM.id)
                .outerjoin(SetVoteORM, SetVoteORM.tournament_id == TournamentORM.id)
                .filter(TournamentORM.id == tournament_id)
                .order_by(SetVoteORM.votes.desc())
            )

            result = await session.execute(stmt)
            rows = result.fetchall()

            if not rows:
                return f"error: Tournament not found, {tournament_id}"

            # Извлечение данных
            tournament_name = rows[0].name
            tournament_date = rows[0].date
            tournament_status = rows[0].status

            # Зарегистрированные игроки
            registered_players = {}
            for row in rows:
                if row.username not in registered_players:
                    registered_players[row.username] = row.mtg_username

            # Топ-3 сетов
            top_sets = []
            for row in rows[:3]:  # берем первые три строки, т.к. они отсортированы по голосам
                top_sets.append({"set_name": row.set_name, "votes": row.votes})

            # Формируем результат
            details = {
                "tournament_name": tournament_name,
                "tournament_date": tournament_date,
                "tournament_status": tournament_status,
                "registered_players": registered_players,
                "top_sets": top_sets,
            }
            return details

    @staticmethod
    async def get_set():
        async with async_session() as session:
            result = await session.execute(select(SetORM))
            return result.scalars().all()

    @staticmethod
    async def register_user_for_tournament(tg_id: int, tournament_id: int, set_id: int):
        async with async_session() as session:
            try:
                # Создаем подзапрос для получения user_id по tg_id
                subquery_user_id = select(UserORM.id).filter(UserORM.tg_id == tg_id).scalar_subquery()

                # Проверяем, существует ли пользователь с данным tg_id
                user_id = await session.scalar(subquery_user_id)
                if not user_id:
                    return {"error": "User not found"}

                # Проверяем, если пользователь уже зарегистрирован на этот турнир
                existing_registration = await session.scalar(
                    select(RegistrationORM)
                    .where(RegistrationORM.user_id == user_id)
                    .where(RegistrationORM.tournament_id == tournament_id)
                )

                if existing_registration:
                    return {"message": "User already registered"}

                # Создаем новую запись о регистрации
                registration = RegistrationORM(
                    user_id=user_id,
                    tournament_id=tournament_id,
                    status=RegStatus.CONFIRMED  # Статус регистрации по умолчанию
                )

                # Добавляем регистрацию в сессию
                session.add(registration)

                # Обновляем данные в таблице голосования за сет
                set_vote = await session.scalar(
                    select(SetVoteORM)
                    .where(SetVoteORM.user_id == user_id)
                    .where(SetVoteORM.tournament_id == tournament_id)
                    .where(SetVoteORM.set_id == set_id)
                )

                if set_vote:
                    set_vote.votes += 1  # Обновляем голос
                else:
                    set_name = await session.scalar(
                        select(SetORM.set_name).where(SetORM.id == set_id)
                    )
                    set_vote = SetVoteORM(
                        tournament_id=tournament_id,
                        set_id=set_id,
                        set_name=set_name,
                        votes=1,
                        user_id=user_id
                    )
                    session.add(set_vote)

                # Фиксируем изменения в базе данных
                await session.commit()
                return {"success": True, "message": "User successfully registered for the tournament"}

            except Exception as e:
                await session.rollback()  # Откат изменений в случае ошибки
                return {"error": str(e)}


    @staticmethod
    async def get_tournaments_for_current_week():
        async with async_session as session:
            # Определяем начало и конец текущей недели
            today = datetime.today()
            start_of_week = today - timedelta(days=today.weekday())  # Понедельник текущей недели
            end_of_week = start_of_week + timedelta(days=6)  # Воскресенье текущей недели

            # Запрашиваем турниры, проходящие на текущей неделе
            query = (
                select(TournamentORM)
                .where(TournamentORM.date >= start_of_week)
                .where(TournamentORM.date <= end_of_week)
            )
            # Выполняем запрос и возвращаем результат
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_tournament(tnmt_id: int):
        async with async_session() as session:
            return await session.scalar(select(TournamentORM).where(TournamentORM.id == tnmt_id))

    @staticmethod   # Выгружват все турниры для конкретного пользователя по tg_id.
    async def get_user_tournaments(tg_id: BigInteger):
        async with async_session() as session:
            # Сначала находим пользователя по tg_id
            user = await session.scalar(
                select(UserORM).where(UserORM.tg_id == tg_id)
            )

            if user is None:
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
    async def get_tournament_by_date(date: datetime):
        async with async_session() as session:
            return await session.scalar(select(TournamentORM).where(TournamentORM.date == date))

    @staticmethod
    async def get_user_by_tg_id(tg_id: int):
        """Получает пользователя по Telegram ID."""
        async with async_session() as session:
            return await session.scalar(select(UserORM).where(UserORM.tg_id == tg_id))

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