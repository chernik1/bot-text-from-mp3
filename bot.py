import os
from os import getenv
import logging
import time
import asyncio

from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.token import TokenValidationError
from dotenv import load_dotenv

from gemini import Gemini


class TelegramBot:
    def __init__(self, client_ai: Gemini):
        load_dotenv()
        token_key = getenv("BOT_TOKEN")

        if not token_key:
            logging.critical("Bot token not found.")
            raise ValueError("Bot token not found.")
        else:
            logging.info("Bot token found.")


        try:
            self.client = client_ai
            self.bot = Bot(token=str(token_key))
            self.dp = Dispatcher(storage=MemoryStorage())
            self._register_handlers()
            print("Bot started")
            logging.info("Bot started")
        except TokenValidationError as e:
            logging.critical(f"Invalid token: {e} {token_key}")
            raise ValueError(f"Invalid token: {e}")

    def _register_handlers(self):
        @self.dp.message(F.voice)
        async def handle_voice(message: types.Message):
            try:
                voice = message.voice
                file_id = voice.file_id

                file_name = f"voice_{file_id}.mp3"

                os.makedirs("downloads", exist_ok=True)
                download_path = os.path.join("downloads", file_name)

                file = await message.bot.get_file(file_id)
                await message.bot.download(file, destination=download_path)

                logging.info(f"Voice downloaded as: {file_name}")

                response = await self.client.translate_audio(download_path)
                await message.reply(response)
            except Exception as e:
                logging.error(f"Error downloading voice: {e}")
                message.reply(f"Can't download voice. Please try again.")

        @self.dp.message(F.audio)
        async def handle_audio(message: types.Message):
            try:
                audio = message.audio
                file_id = audio.file_id
                file_name = audio.file_name or f"audio_{file_id}.{audio.mime_type.split('/')[-1] if audio.mime_type else 'mp3'}"

                os.makedirs("downloads", exist_ok=True)
                download_path = os.path.join("downloads", file_name)

                file = await message.bot.get_file(file_id)
                await message.bot.download(file, destination=download_path)

                logging.info(f"Audio downloaded as: {file_name}")

                response = await self.client.translate_audio(download_path)
                await message.reply(response)
            except Exception as e:
                logging.error(f"Error downloading audio: {e}")
                message.reply(f"Can't download audio. Please try again.")



    async def run(self):
        logging.debug("Try to start bot")
        await self.dp.start_polling(self.bot)