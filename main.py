import logging
import asyncio

from bot import TelegramBot
from gemini import Gemini

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, filename="./logs/main.log", filemode="a",
                        format="%(asctime)s - %(levelname)s - %(message)s", encoding = "UTF-8")

    error_logger = logging.getLogger('error_logger')
    error_logger.setLevel(logging.ERROR)

    error_handler = logging.FileHandler(
        filename='./logs/errors.log',
        mode='a',
        encoding='utf-8'
    )
    error_handler.setFormatter(logging.Formatter('%(asctime)s - ERROR - %(message)s'))
    error_logger.addHandler(error_handler)

    try:
        client_ai = Gemini()
        bot = TelegramBot(client_ai=client_ai)

        asyncio.run(bot.run())
    except Exception as e:
        logging.critical(f"Error: {e}")
        raise e