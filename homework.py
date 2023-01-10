import json
import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from telegram.ext import MessageHandler, Updater

load_dotenv()

PRACTICUM_TOKEN = os.getenv('TOKEN_YANDEX')
TELEGRAM_TOKEN = os.getenv('TOKEN_TELEGRAM')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 60 * 10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def init_logger(name):
    """Инициализация логгера и хендлеров."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    format = '%(asctime)s - %(levelname)s - %(name)s:%(lineno)s - %(message)s'

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter(format))
    logger.addHandler(stream_handler)

    logger.debug('Логгер инициализирован')


init_logger(__name__)
logger = logging.getLogger(__name__)


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )

        logger.info('Сообщение в Telegram успешно отправлено')

    except telegram.TelegramError as err:
        raise telegram.TelegramError(err)


def get_api_answer(current_timestamp):
    """Запрос к API практикума."""
    timestamp = current_timestamp or int(time.time() - RETRY_TIME)
    params = {'from_date': timestamp}

    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise requests.RequestException(
                f'Ошибка {response.status_code} при запросе к {ENDPOINT}'
            )

        response_json = response.json()

    except ConnectionError:
        raise ConnectionError(f'Не удалось выполнить запрос к {ENDPOINT}')

    except json.decoder.JSONDecodeError:
        raise ValueError('Не удалось преобразовать данные JSON')

    logger.info('Ответ от практикума получен')
    return response_json


def check_response(response):
    """Проверяет ответ API практикума."""
    if type(response) is not dict:
        raise TypeError('Неверный тип ответа')

    if 'homeworks' not in response.keys():
        raise KeyError('Отсутствие ожидаемых ключей')

    if type(response['homeworks']) is not list:
        raise TypeError('Неверный тип данных')

    homeworks = response.get('homeworks')
    logger.debug(f'homeworks: {homeworks}')

    if type(homeworks) is list:
        logger.info('Ответ от практикума проверен - ОК')
        return homeworks
    raise TypeError('Неверный тип данных')


def parse_status(homework):
    """Извлекает информацию о конкретной домашней работе."""
    if type(homework) is not dict:
        raise TypeError('Неверный тип данных')

    if 'homework_name' not in homework.keys():
        raise KeyError('Отсутствие ожидаемых ключей')

    homework_name = homework.get('homework_name')
    logger.debug(f'homework_name: {homework_name}')

    homework_status = homework.get('status')
    logger.debug(f'homework_status: {homework_status}')

    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        logger.info(f'Статус работы "{homework_name}" получен')

        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    raise KeyError('Обнаружен недокументированный статус домашней работы')


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
        sys.exit('Ошибка авторизации')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    updater.dispatcher.add_handler(
        MessageHandler(
            None,
            lambda *args: send_message(bot, args[0].message.text)
        )
    )
    updater.start_polling()

    current_timestamp = int(time.time() - RETRY_TIME)
    log_history = []

    send_message(bot, 'bot started')

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)

            for work in homeworks:
                message = parse_status(work)
                send_message(bot, message)

            current_timestamp = response.get(
                'current_date',
                int(time.time() - RETRY_TIME)
            )
            log_history = []

        except Exception as error:
            logger.error(error)
            if error.args not in log_history:
                log_history.append(error.args)
                send_message(bot, str(error))

        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
