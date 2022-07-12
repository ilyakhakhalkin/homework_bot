import telegram
import requests
from http import HTTPStatus
import logging
import time
import sys
import os
from dotenv import load_dotenv


load_dotenv()

PRACTICUM_TOKEN = os.getenv('TOKEN_YANDEX')
TELEGRAM_TOKEN = os.getenv('TOKEN_TELEGRAM')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 60
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
        super().__init__()
        self.token = token
        self.chat_id = chat_id
        self.bot = telegram.Bot(token=self.token)

        self.messages_seen = []

    def emit(self, record):
        """Отправка логов"""

        message = record.getMessage()
        is_new_message = message not in self.messages_seen

        if is_new_message:
            self.messages_seen.append(message)
            msg = self.format(record)
            self.bot.send_message(self.chat_id, msg, parse_mode="HTML")

    def clear_messages_history(self):
        self.messages_seen = []
        print('cleaned')


def init_logger(name):
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


init_logger(__name__)
logger = logging.getLogger(__name__)


def send_message(bot, message):
    """Отправляет сообщение в Telegram"""

    response = bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message,
    )

    if response['text'] == message:
        logger.info('Сообщение в Telegram успешно отправлено')
        logger.handlers[1].clear_messages_history()
    else:
        logger.error('Сбой при отправке сообщения в Telegram')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API практикума"""

    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    logger.debug(f'params: {params}')

    response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
    logger.debug(f'response: {response}')

    if response.status_code == HTTPStatus.OK:
        logger.info('Ответ от практикума получен')
        return response.json()
    else:
        logger.error(f'Ошибка {response.status_code} при запросе к endpoint')


def check_response(response):
    """Проверяет ответ API практикума"""

    if 'homeworks' not in response:
        logger.error('Отсутствуют ключи в ответе от практикума')
        return []

    homeworks = response.get('homeworks')
    logger.debug(f'123123123 homeworks: {homeworks}')

    if homeworks == []:
        logger.debug('В ответе нет новых статусов')
    elif homeworks:
        logger.info('Ответ от практикума проверен - ОК')

    return homeworks


def parse_status(homework):
    """Извлекает информацию о конкретной домашней работе"""

    homework_name = homework['lesson_name']
    logger.debug(f'homework_name: {homework_name}')

    homework_status = homework['status']
    logger.debug(f'homework_status: {homework_status}')

    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        logger.info(f'Статус работы "{homework_name}" получен')
    else:
        logger.error('Обнаружен недокументированный статус домашней работы')
        verdict = 'Ошибка: неизвестный статус'

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


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
    logger.debug(f'bot: {bot}')

    current_timestamp = int(time.time())
    logger.debug(f'current_timestamp: {current_timestamp}')

    while True:
        try:
            response = get_api_answer(current_timestamp)
            logger.debug(f'response: {response}')

            homeworks = check_response(response)
            logger.debug(f'homeworks: {homeworks}')

            if homeworks == []:
                logger.info('Нет новых статусов. Ждём следующего цикла')
                time.sleep(RETRY_TIME)
                continue

            for work in homeworks:
                message = parse_status(work)
                logger.debug(f'message: {message}')
                send_message(bot, message)

            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)

        except Exception as error:
            logger.exception(error)
            time.sleep(RETRY_TIME)
        else:
            logger.error('Непредвиденная ошибка')


if __name__ == '__main__':
    main()
