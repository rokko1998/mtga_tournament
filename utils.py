import datetime

async def nearest_weekend():
    today = datetime.date.today()
    days_until_saturday = (5 - today.weekday() + 7) % 7
    days_until_sunday = (6 - today.weekday() + 7) % 7

    if days_until_saturday == 0:
        days_until_saturday = 7
    if days_until_sunday == 0:
        days_until_sunday = 7

    next_saturday = today + datetime.timedelta(days=days_until_saturday)
    next_sunday = today + datetime.timedelta(days=days_until_sunday)

    dates = [
        datetime.datetime(next_saturday.year, next_saturday.month, next_saturday.day, 12, 0),
        datetime.datetime(next_saturday.year, next_saturday.month, next_saturday.day, 18, 0),
        datetime.datetime(next_sunday.year, next_sunday.month, next_sunday.day, 12, 0),
        datetime.datetime(next_sunday.year, next_sunday.month, next_sunday.day, 18, 0),
    ]

    return dates