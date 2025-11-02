from datetime import datetime, date
from zoneinfo import ZoneInfo
from django.conf import settings

def current_class_year_choices(rollover_month=7, rollover_day=1, tz_name=None):
    tz = ZoneInfo(tz_name or getattr(settings, "TIME_ZONE", "America/Chicago"))
    today = datetime.now(tz).date()
    start = today.year + 1 if (today.month, today.day) >= (rollover_month, rollover_day) else today.year
    years = [str(y) for y in range(start, start + 4)]
    return years