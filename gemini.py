import os
from os import getenv
import logging
import asyncio

from google import genai
from dotenv import load_dotenv

class Gemini:
    def __init__(self):
        load_dotenv()

        try:
            key = getenv("GEMINI_KEY")
            self.client = genai.Client(api_key=key)
            logging.info("Create client")
        except Exception as e:
            logging.critical(f"ERROR: {e}")
            logging.debug(f'Key: {key}')
            raise e

    async def translate_audio(self, path: str) -> str:
        try:
            myfile = await self.client.aio.files.upload(
                file=path,
            )
            logging.info(f"File uploaded successfully. ID: {myfile.name} (from path: {path})")
        except FileNotFoundError:
            logging.error(f"ERROR: File not found at path: {path}")
            return f"Error: Could not find the file '{path}'. Please check the path."
        except PermissionError:
            logging.error(f"ERROR: Permission denied for file: {path}")
            return f"Error: Do not have permission to read the file '{path}'."
        except Exception as e:
            logging.error(f"ERROR during upload for file {path}: {e}")
            return "Don't upload audio. Please try again."

        try:
            response = await self.client.aio.models.generate_content(
              model="gemini-2.0-flash",
              contents=["Write all text from audio. Language: Any", myfile]
            )
            logging.info(f"Audio translated. Response: {response.text}. File: {path}")
        except Exception as e:
            logging.error(f"ERROR: {e}. File: {path}")
            return "Can't translate audio. Please try again."

        await self.__delete_file(myfile, path)
        return response.text

    async def __delete_file(self, file, path):
        try:
            absolute_path = os.path.abspath(path)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, os.remove, absolute_path)
            self.client.files.delete(name=file.name)
            logging.info(f"File deleted: {path}")
        except Exception as e:
            logging.error(f"Can't delete file: {path} or name {file.name}. ERROR: {e}")
