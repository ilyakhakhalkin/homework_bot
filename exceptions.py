class ResponseCodeError(Exception):
    """Вызывается, если код ответа сервера != 200"""
    pass


class UndefinedHomeworkStatusError(Exception):
    """Вызывается, если в словаре нет искомого статуса"""
    pass


class EmptyDictError(Exception):
    """Вызывается, если в словаре не оказалось ключей"""
    pass


class HomeworksIsNotAListError(Exception):
    """Вызывается, если домашки пришли не в виде списка"""
    pass
