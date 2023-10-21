class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            og = super(Singleton, cls)
            cls._instance = og.__init__(cls, *args, **kwargs)
        return cls._instance
