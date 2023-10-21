from typing import Any


class TinkoffAPIError(Exception):
    pass


class ResourceExhausted(TinkoffAPIError):
    """ Token hit limit  """

    def __init__(self, data: Any = None):
        self.data = data
        super().__init__()
