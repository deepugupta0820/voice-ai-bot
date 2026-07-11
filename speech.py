import os
import uuid
import asyncio
import tempfile
import edge_tts

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# Speech To Text (Whisper)

def speech_to_text(audio_bytes):

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
            ) as temp_audio:

            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name

        with open(temp_audio_path, "rb") as file:

            transcription = client.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3"
            )

        os.remove(temp_audio_path)

        return transcription.text

    except Exception as e:

        return f"Error: {str(e)}"



# Text To Speech (Edge TTS)

async def generate_speech_async(
    text,
    output_file
):

    communicate = edge_tts.Communicate(
        text=text,
        voice="en-US-GuyNeural"
    )

    await communicate.save(
        output_file
    )


def text_to_speech(text):

    try:

        output_file = (
            f"audio_{uuid.uuid4().hex}.mp3"
        )

        loop = asyncio.new_event_loop()

        asyncio.set_event_loop(
            loop
        )

        loop.run_until_complete(
            generate_speech_async(
                text,
                output_file
            )
        )

        loop.close()

        return output_file

    except Exception as e:

        print(
            f"TTS Error: {e}"
        )

        return None