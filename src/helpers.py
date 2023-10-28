from typing import Any
from datetime import datetime

from tinkoff.invest import Quotation
from src.date_utils import dtf

from src.converter import Converter


def to_json_serializable(obj: Any) -> dict[str, Any]:
    d = {}
    for attr_name in dir(obj):
        if not attr_name.startswith('_'):
            v = getattr(obj, attr_name)
            if isinstance(v, Quotation):
                v = Converter.quotation_to_decimal(v)
            elif isinstance(v, datetime):
                v = dtf.datetime_strf(v)
            elif isinstance(v,)

            d[attr_name] = v
    return d
