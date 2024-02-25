from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import holidays

ISO_FORMAT = '%Y-%m-%d %H:%M:%S%z'
TZ_MOSCOW = ZoneInfo('Europe/Moscow')
TZ_UTC = ZoneInfo('UTC')

ru_holidays = holidays.country_holidays('RU', years=([x for x in range(1970, datetime.now().year+5)]))
ru_holidays = [
    dt for dt in ru_holidays
    if not (dt.month == 1 and dt.day in [3, 4, 5, 6, 7, 8])
]


class DateTimeFactory:
    BUG_1DAY_CANDLE_DATE = datetime(year=1970, month=1, day=1, tzinfo=TZ_UTC)

    @classmethod
    def now(cls) -> datetime:
        return datetime.now(tz=TZ_UTC)

    @classmethod
    def replace_time(cls, dt: datetime) -> datetime:
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)


class BaseDateTimeFormatter(ABC):
    @property
    @abstractmethod
    def _TZ(self) -> ZoneInfo:
        ...

    @property
    @abstractmethod
    def _date_format(self) -> str:
        ...

    @property
    @abstractmethod
    def _time_format(self) -> str:
        return ''

    @property
    def _datetime_format(self) -> str:
        return ' '.join([self._date_format, self._time_format])

    def date_strf(self, v: datetime) -> str:
        return v.strftime(self._date_format)

    def time_strf(self, v: datetime) -> str:
        return v.strftime(self._time_format)

    def datetime_strf(self, v: datetime) -> str:
        return v.strftime(self._datetime_format)

    def date_strp(self, v: str) -> datetime:
        return datetime.strptime(v, self._date_format)

    def time_strp(self, v: str) -> datetime:
        return datetime.strptime(v, self._time_format).replace(tzinfo=self._TZ)

    def datetime_strp(self, v: str) -> datetime:
        return datetime.strptime(v, self._datetime_format).replace(tzinfo=self._TZ)


class SystemDateTimeFormatter(BaseDateTimeFormatter):
    _TZ = TZ_UTC
    _date_format = '%d.%m.%Y'
    _time_format = '%H:%M:%S'


class ISODateTimeFormatter(BaseDateTimeFormatter):
    _TZ = TZ_UTC
    _date_format, _time_format = ISO_FORMAT.split()


dt_form_sys = SystemDateTimeFormatter()
dt_form_iso = ISODateTimeFormatter()
dt_form_msc = SystemDateTimeFormatter()
dt_form_msc._TZ = TZ_MOSCOW


def is_minute_passed(old_dt: datetime) -> bool:
    dt_now = DateTimeFactory.now()
    return dt_now - old_dt > timedelta(minutes=1) or dt_now.minute != old_dt.minute


