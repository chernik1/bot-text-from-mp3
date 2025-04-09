from moviepy import VideoFileClip
import asyncio
import logging
import os

async def convert_audio_from_video(path_to_video: str) -> str:
    try:
        output_audio_path = path_to_video[:-4] + ".mp3"

        def __convert():
            with VideoFileClip(path_to_video) as video:
                audio = video.audio
                if audio is None:
                    logging.error(f"Not found audio in video: {path_to_video}")
                audio.write_audiofile(output_audio_path)
                audio.close()

        await asyncio.to_thread(__convert)
        logging.info(f"Audio converted from video: {path_to_video}")
        await __delete_video(path_to_video)
        return output_audio_path
    except Exception as e:
        logging.error(f"ERROR CONVERTING audio from video: {e}")

async def __delete_video(path: str):
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, os.remove, path)
        logging.info(f"Video deleted: {path}")
    except Exception as e:
        logging.error(f"Can't delete video: {path}. ERROR: {e}")
