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