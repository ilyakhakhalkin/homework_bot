import telegram
import requests
from http import HTTPStatus
import logging
import time
import sys
import os
import exceptions
from dotenv import load_dotenv


load_dotenv()

PRACTICUM_TOKEN = os.getenv('TOKEN_YANDEX')
TELEGRAM_TOKEN = os.getenv('TOKEN_TELEGRAM')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class telegramHandler(logging.StreamHandler):
    """Хендлер для отправки логов в телеграм."""

    def __init__(self, token, chat_id):
        """Инициализация хендлера.
        self.token = токен бота Telegram
        self.chat_id = идентификатор чата пользователя
        """
        super().__init__()
        self.token = token
        self.chat_id = chat_id
        self.bot = telegram.Bot(token=self.token)
        self.messages_seen = []

    def emit(self, record):
        """Отправка логов."""
        message = record.getMessage()
        is_new_message = message not in self.messages_seen

        if is_new_message:
            self.messages_seen.append(message)
            msg = self.format(record)
            self.bot.send_message(self.chat_id, msg, parse_mode="HTML")

    def clear_messages_history(self):
        """Удаление сохраненных логов."""
        self.messages_seen = []


def init_logger(name):
    """Инициализация логгера и хендлеров."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(stream_handler)

    tg_handler = telegramHandler(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    tg_handler.setLevel(logging.ERROR)
    tg_handler.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(tg_handler)

    logger.debug('Логгер инициализирован')


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    response = bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message,
    )

    if response['text'] == message:
        logger.info('Сообщение в Telegram успешно отправлено')
        # logger.handlers[1].clear_messages_history()
    else:
        logger.error('Сбой при отправке сообщения в Telegram')


def get_api_answer(current_timestamp):
    """Запрос к API практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)

    if response.status_code != HTTPStatus.OK:
        logger.error(f'Ошибка {response.status_code} при запросе к endpoint')
        raise RuntimeError

    try:
        response_json = response.json()
    except ValueError:
        logger.error('Не удалось преобразовать данные')

    logger.info('Ответ от практикума получен')
    return response_json


def check_response(response):
    """Проверяет ответ API практикума."""
    if type(response) is not dict:
        logger.error('Неверный тип ответа')
        raise TypeError

    if 'homeworks' not in response.keys():
        logger.error('Отсутствие ожидаемых ключей')
        raise KeyError

    if type(response['homeworks']) is not list:
        logger.error('Неверный тип данных')
        raise TypeError

    homeworks = response.get('homeworks')

    logger.debug(f'homeworks: {homeworks}')
    logger.info('Ответ от практикума проверен - ОК')

    return homeworks


def parse_status(homework):
    """Извлекает информацию о конкретной домашней работе."""
    homework_name = homework['homework_name']
    logger.debug(f'homework_name: {homework_name}')

    homework_status = homework['status']
    logger.debug(f'homework_status: {homework_status}')

    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        logger.info(f'Статус работы "{homework_name}" получен')

        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logger.error('Обнаружен недокументированный статус домашней работы')
        raise exceptions.UndefinedHomeworkStatusError


def check_tokens():
    """Проверка наличия токенов."""
    if not PRACTICUM_TOKEN:
        logger.critical('Отсутствует токен практикума')
        return False
    if not TELEGRAM_TOKEN:
        logger.critical('Отсутствует токен Telegram')
        return False
    if not TELEGRAM_CHAT_ID:
        logger.critical('Отсутствует id чата Telegram')
        return False

    logger.info('Токены проверены - OK')

    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Ошибка авторизации')
        return

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)

            for work in homeworks:
                message = parse_status(work)
                send_message(bot, message)

            current_timestamp = response.get('current_date')

        except Exception as error:
            logger.exception(error)

        time.sleep(RETRY_TIME)


init_logger(__name__)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    """main."""
    main()
