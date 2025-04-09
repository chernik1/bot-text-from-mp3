import os
from os import getenv
import logging
import time
import asyncio

from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.token import TokenValidationError
from dotenv import load_dotenv

from converter import convert_audio_from_video
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
                await message.bot.download_file(file.file_path, destination=download_path)

                logging.info(f"Audio downloaded as: {file_name}")

                response = await self.client.translate_audio(download_path)
                await message.reply(response)
            except Exception as e:
                logging.error(f"Error downloading audio: {e}")
                await message.reply("Can't download audio. Please try again.")

        @self.dp.message(F.video)
        async def handle_video(message: types.Message):
            try:
                video = message.video
                file_id = video.file_id
                file_name = video.file_name or f"video_{file_id}.{video.mime_type.split('/')[-1] if video.mime_type else 'mp4'}"

                if video.file_size > 20 * 1024 * 1024:
                    await message.reply("File size exceeds the 20MB limit. Please send a smaller video.")
                    return

                os.makedirs("downloads", exist_ok=True)
                download_path = os.path.join("downloads", file_name)

                file = await message.bot.get_file(file_id)
                await message.bot.download_file(file.file_path, destination=download_path)

                logging.info(f"Video downloaded successfully: {file_name}")

                try:
                    path_to_audio = await convert_audio_from_video(download_path)
                except Exception as e:
                    logging.error(f"Video-to-audio conversion failed: {e}")
                    await message.reply("Failed to extract audio from the video. The file may be corrupted or unsupported.")
                    return

                try:
                    text = await self.client.translate_audio(path_to_audio)
                    await message.reply(text)
                    logging.info(f"Audio transcription successful: {text[:100]}...")
                except Exception as e:
                    logging.error(f"Audio transcription failed: {e}")
                    await message.reply("Failed to transcribe audio. The audio may be unclear or too short.")
            except Exception as e:
                logging.error(f"Video download error: {e}")
                await message.reply(
                    "Failed to download the video. Ensure the file is sent as a video (not a link or document).")

        @self.dp.message(F.video_note)
        async def handle_video_note(message: types.Message):
            try:
                video_note = message.video_note
                file_id = video_note.file_id
                file_unique_id = video_note.file_unique_id

                os.makedirs("downloads", exist_ok=True)
                download_path = f"downloads/{file_unique_id}.mp4"

                file = await message.bot.get_file(file_id)
                await message.bot.download_file(file.file_path, destination=download_path)

                logging.info(f"Video note saved: {download_path}")

                try:
                    path_to_mp3 = await convert_audio_from_video(download_path)
                    logging.info(f"Path to mp3 from video note: {path_to_mp3}")
                except Exception as e:
                    message.reply("Can't get text from videos. Please, try again.")
                    logging.error(f"ERROR get path mp3 from video note: {e}")

                try:
                    text = await self.client.translate_audio(path_to_mp3)
                    await message.reply(text)
                    logging.info(f"Text from video note: text")
                except Exception as e:
                    message.reply("Can't text from video note. Please, try again.")
                    logging.error(f"ERROR get text from mp3 {e}")
            except Exception as e:
                message.reply("Can't text from video note. Please, try again.")
                logging.error(f"Video note processing error: {e}")
                raise e


    async def run(self):
        logging.debug("Try to start bot")
        await self.dp.start_polling(self.bot)