import datetime
import enum

from sqlalchemy import BigInteger, ForeignKey, func, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Relationship, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from typing import Annotated, List
from sqlalchemy.ext.hybrid import hybrid_property


str_256 = Annotated[str, mapped_column(String(256))]
stat = Annotated[int, mapped_column(default=0)]
int_pk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[datetime.datetime, mapped_column(server_default=func.now(), onupdate=func.now())]


class TournamentStatus(enum.Enum):
    PLANNED = "planned" # идет регистрация участников
    UPCOMING = "upcoming" # Турнир начат, идет процесс драфта, игры еще не начались
    ONGOING = "ongoing" # драфт закончен, проходят игры
    COMPLETED = "completed" # турнир завершен
    CANCELLED = "cancelled" # турнир отменен


class RegStatus(enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Base(AsyncAttrs, DeclarativeBase):
    pass


class UserORM(Base):
    __tablename__ = 'users'

    id: Mapped[int_pk]
    tg_id = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str_256]
    wins: Mapped[stat] #int dflt-0 количество побед
    losses: Mapped[stat]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    # Relationships
    set_votes: Mapped[List['SetVoteORM']] = Relationship(back_populates='user')
    registrations: Mapped[List['RegistrationORM']] = Relationship(back_populates='user')
    matches_as_player1: Mapped[List['MatchORM']] = Relationship(back_populates='player1',
                                                                foreign_keys='MatchORM.player1_id')
    matches_as_player2: Mapped[List['MatchORM']] = Relationship(back_populates='player2',
                                                                foreign_keys='MatchORM.player2_id')
    set_stats: Mapped[List['SetStatsORM']] = Relationship(back_populates='user')
    tournament_stats: Mapped[List['TournamentStatsORM']] = Relationship(back_populates='user')
    accounts: Mapped[List['MtgORM']] = Relationship('MtgORM', back_populates='user', cascade="all, delete-orphan")


    # чето ленивая загрузка возникает, буду менять во внешнем коде, когда закончу с match логику вернусь посмотрю
    # @hybrid_property
    # def wins(self):
    #     return len([match for match in self.matches_as_player1 if match.result == 'player1_win']) + \
    #         len([match for match in self.matches_as_player2 if match.result == 'player2_win'])
    #
    # @wins.expression
    # def wins(cls):
    #     return (
    #         select([func.count(MatchORM.id)])
    #         .where(
    #             ((MatchORM.player1_id == cls.id) & (MatchORM.result == 'player1_win')) |
    #             ((MatchORM.player2_id == cls.id) & (MatchORM.result == 'player2_win'))
    #         )
    #         .correlate(cls)
    #         .label("wins")
    #     )
    #
    # @hybrid_property
    # def losses(self):
    #     return len([match for match in self.matches_as_player1 if match.result == 'player2_win']) + \
    #            len([match for match in self.matches_as_player2 if match.result == 'player1_win'])
    #
    # @losses.expression
    # def losses(cls):
    #     return (
    #         select([func.count(MatchORM.id)])
    #         .where(
    #             ((MatchORM.player1_id == cls.id) & (MatchORM.result == 'player2_win')) |
    #             ((MatchORM.player2_id == cls.id) & (MatchORM.result == 'player1_win'))
    #         )
    #         .correlate(cls)
    #         .label("losses")
    #     )

class MtgORM(Base):
    __tablename__ = 'mtg_accounts'

    id: Mapped[int_pk]
    username: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    user: Mapped['UserORM'] = Relationship('UserORM', back_populates='accounts')


class TournamentORM(Base):
    __tablename__ = 'tournaments'

    id: Mapped[int_pk]
    name: Mapped[str_256]
    date: Mapped[datetime.datetime]
    status: Mapped[TournamentStatus] = mapped_column(default=TournamentStatus.PLANNED)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    # Relationships
    sets: Mapped[List['TournamentSetORM']] = Relationship('TournamentSetORM', back_populates='tournament')
    registrations: Mapped[List['RegistrationORM']] = Relationship(back_populates='tournament')
    matches: Mapped[List['MatchORM']] = Relationship(back_populates='tournament')
    tournament_stats: Mapped[List['TournamentStatsORM']] = Relationship(back_populates='tournament')
    set_votes: Mapped[List['SetVoteORM']] = Relationship(back_populates='tournament')
    winning_set_id: Mapped[int | None] = mapped_column(ForeignKey('sets.id'), nullable=True)
    winning_set: Mapped['SetORM'] = Relationship('SetORM', back_populates='tournaments_as_winner')


class SetVoteORM(Base):
    __tablename__ = 'set_votes'

    id: Mapped[int_pk]
    tournament_id: Mapped[int] = mapped_column(ForeignKey('tournaments.id'), nullable=False)
    set_id: Mapped[int] = mapped_column(ForeignKey('sets.id'), nullable=False)
    set_name: Mapped[str] = mapped_column(nullable=False)
    votes: Mapped[int] = mapped_column(default=0)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    # Relationships
    tournament: Mapped['TournamentORM'] = Relationship(back_populates='set_votes')
    set: Mapped['SetORM'] = Relationship(back_populates='set_votes')
    user: Mapped['UserORM'] = Relationship(back_populates='set_votes')


class SetORM(Base):
    __tablename__ = 'sets'

    id: Mapped[int_pk]  # Первичный ключ
    set_name: Mapped[str_256]
    description: Mapped[str_256]  # Описание сета

    # Relationships
    tournaments: Mapped[List['TournamentSetORM']] = Relationship('TournamentSetORM', back_populates='set')
    set_votes: Mapped[List['SetVoteORM']] = Relationship(back_populates='set')
    tournaments_as_winner: Mapped[List['TournamentORM']] = Relationship('TournamentORM', back_populates='winning_set')


class TournamentSetORM(Base):
    __tablename__ = 'tournament_sets'

    tournament_id: Mapped[int] = mapped_column(ForeignKey('tournaments.id'), primary_key=True)
    set_id: Mapped[int] = mapped_column(ForeignKey('sets.id'), primary_key=True)

    # Relationships
    tournament: Mapped['TournamentORM'] = Relationship('TournamentORM', back_populates='sets')
    set: Mapped['SetORM'] = Relationship('SetORM', back_populates='tournaments')


class RegistrationORM(Base):
    __tablename__ = 'registrations'

    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    tournament_id: Mapped[int] = mapped_column(ForeignKey('tournaments.id'))
    status: Mapped[RegStatus]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    # Relationships
    user: Mapped['UserORM'] = Relationship(back_populates='registrations')
    tournament: Mapped['TournamentORM'] = Relationship(back_populates='registrations')


class MatchORM(Base):
    __tablename__ = 'matches'

    id: Mapped[int_pk]
    tournament_id: Mapped[int] = mapped_column(ForeignKey('tournaments.id'))
    player1_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    player2_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    result: Mapped[str_256]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    # Relationships
    tournament: Mapped['TournamentORM'] = Relationship(back_populates='matches')
    player1: Mapped['UserORM'] = Relationship(back_populates='matches_as_player1', foreign_keys=[player1_id])
    player2: Mapped['UserORM'] = Relationship(back_populates='matches_as_player2', foreign_keys=[player2_id])


class SetStatsORM(Base):
    __tablename__ = 'set_stats'

    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    set_name: Mapped[str_256]
    wins: Mapped[int] = mapped_column(default=0)
    losses: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    # Relationships
    user: Mapped['UserORM'] = Relationship(back_populates='set_stats')


class TournamentStatsORM(Base):
    __tablename__ = 'tournament_stats'

    id: Mapped[int_pk]
    tournament_id: Mapped[int] = mapped_column(ForeignKey('tournaments.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    wins: Mapped[int] = mapped_column(default=0)
    losses: Mapped[int] = mapped_column(default=0)
    draws: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    # Relationships
    user: Mapped['UserORM'] = Relationship(back_populates='tournament_stats')
    tournament: Mapped['TournamentORM'] = Relationship(back_populates='tournament_stats')