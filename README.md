# homework_bot
## Description
This Telegram bot sends notifications to your Telegram account when the status of your homework check changes.

## How to run

To run the project, follow these steps:

Clone the repository to your computer using the git clone command.
```
git clone https://github.com/ilyakhakhalkin/homework_bot.git
```

Go to the project directory in terminal:
```
cd homework_bot
```

Create and activate virtual environment:
```
python3 -m venv venv
```
```
source venv/bin/activate
```

Install dependencies from requirements.txt:
```
python3 -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```

To use the bot, you will need the following tokens and identifiers:

- Yandex API authentication token - This is required to access the Yandex API and check the status of your homework.
- Telegram bot token - This is required to access the Telegram API and send messages to your Telegram account.
- Telegram chat ID - This is the unique identifier of the chat between you and your bot, and is used to send messages to your Telegram account.

To configure the bot, you can write these tokens and identifiers into a .env file located in the root directory of your project.
Here's an example of the .env file:
```
YANDEX_API_TOKEN=<your_yandex_api_token>
TELEGRAM_BOT_TOKEN=<your_telegram_bot_token>
TELEGRAM_CHAT_ID=<your_telegram_chat_id>
```

