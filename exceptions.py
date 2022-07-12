class ResponseCodeError(Exception):
    """Код ответа сервера != 200"""
    pass


class UndefinedHomeworkStatusError(Exception):
    """В словаре нет искомого статуса"""
    pass


class NothingNewException(Exception):
    """Нет новых статусов домашек"""
    pass


class EmptyDictError(Exception):
    """В словаре не оказалось ключей"""
    pass


class HomeworksIsNotAListError(Exception):
    """Домашки пришли не в виде списка"""
    pass
