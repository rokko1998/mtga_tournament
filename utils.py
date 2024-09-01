from datetime import datetime, timedelta

async def nearest_weekend():
    today = datetime.today().date()  # Получаем текущую дату
    weekday = today.weekday()

    if weekday == 5:  # Сегодня суббота
        next_saturday = today
        next_sunday = today + timedelta(days=1)
    elif weekday == 6:  # Сегодня воскресенье
        next_saturday = today + timedelta(days=6)
        next_sunday = today
    else:  # Любой другой день
        days_until_saturday = 5 - weekday
        days_until_sunday = 6 - weekday
        next_saturday = today + timedelta(days=days_until_saturday)
        next_sunday = today + timedelta(days=days_until_sunday)

    dates = [
        datetime(next_saturday.year, next_saturday.month, next_saturday.day, 12, 0),
        datetime(next_saturday.year, next_saturday.month, next_saturday.day, 18, 0),
        datetime(next_sunday.year, next_sunday.month, next_sunday.day, 12, 0),
        datetime(next_sunday.year, next_sunday.month, next_sunday.day, 18, 0),
    ]

    return dates

async def get_info(tournament):
    # Проверка на наличие ошибки
    if "error" in tournament:
        return f"Ошибка: {tournament['error']}"

    # Формирование заголовка
    message = f"<b>🏆 Турнир: </b> {tournament['tournament_name']}\n"
    message += f"<b>📅 Дата: </b> {tournament['tournament_date'].strftime('%Y-%m-%d %H:%M')}\n"
    message += f"<b>🔖 Статус: </b> {tournament['tournament_status'].value.capitalize()}\n\n"

    # Список зарегистрированных игроков
    message += "<b>👥 Зарегистрированные игроки:</b>\n"
    for username, mtg_username in tournament["registered_players"].items():
        message += f"- {username} (MTG: {mtg_username})\n"

    if not tournament["registered_players"]:
        message += "Нет зарегистрированных игроков.\n"

    message += "\n"

    # Топ-3 сета в голосовании
    message += "<b>🏅 Топ-3 сета в голосовании:</b>\n"
    for i, set_info in enumerate(tournament["top_sets"], start=1):
        message += f"{i}. {set_info['set_name']} - {set_info['votes']} голосов\n"

    if not tournament["top_sets"]:
        message += "Нет голосов за сеты.\n"
    return message