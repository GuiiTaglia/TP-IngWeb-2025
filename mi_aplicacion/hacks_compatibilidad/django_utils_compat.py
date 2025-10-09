
class datetime_safe:
    @classmethod
    def new_datetime(cls, *args, **kwargs):
        from datetime import datetime
        return datetime(*args, **kwargs)

    @classmethod
    def new_date(cls, *args, **kwargs):
        from datetime import date
        return date(*args, **kwargs)