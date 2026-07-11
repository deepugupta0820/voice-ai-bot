import base64
import os

import streamlit as st
import streamlit.components.v1 as components
from streamlit_mic_recorder import mic_recorder

from speech import (
    speech_to_text,
    text_to_speech
)

from llm import get_response


def encode_audio_file(audio_path):
    try:
        with open(audio_path, 'rb') as file:
            audio_bytes = file.read()
        return base64.b64encode(audio_bytes).decode('utf-8')
    except Exception:
        return None
    finally:
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except OSError:
                pass


def render_audio_player(audio_b64: str, autoplay: bool = False):
    autoplay_attr = 'autoplay' if autoplay else ''
    html = f"""
        <audio controls {autoplay_attr} style='width:100%;'>
            <source src='data:audio/mp3;base64,{audio_b64}' type='audio/mpeg'>
            Your browser does not support the audio element.
        </audio>
    """
    components.html(html, height=100)


def scroll_to_bottom():
    components.html(
        "<script>window.scrollTo({top: document.body.scrollHeight, behavior:'smooth'});</script>",
        height=0,
    )


st.set_page_config(
    page_title='Deepu · AI VoiceBot',
    page_icon='🎤',
    layout='centered'
)


# -----------------------------
# Session State
# -----------------------------
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'last_audio_id' not in st.session_state:
    st.session_state.last_audio_id = None


# -----------------------------
# Header
# -----------------------------
st.title('🎙️ Deepu · AI VoiceBot')

st.markdown(
    '''
Ask me anything about me

'''
)

st.subheader('🎙️ Voice Input')


# -----------------------------
# Clear Chat
# -----------------------------
if st.button('🗑️ Clear Chat'):
    st.session_state.messages = []
    st.session_state.last_audio_id = None
    st.rerun()


# -----------------------------
# Chat History
assistant_indices = [
    idx
    for idx, message in enumerate(st.session_state.messages)
    if message['role'] == 'assistant' and message.get('audio_b64')
]
last_assistant_index = assistant_indices[-1] if assistant_indices else None

for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message['role']):
        st.markdown(message['content'])

        if message['role'] == 'assistant' and message.get('audio_b64'):
            render_audio_player(
                message['audio_b64'],
                autoplay=(idx == last_assistant_index),
            )

if st.session_state.messages:
    scroll_to_bottom()


# -----------------------------
# Voice Recorder
audio = mic_recorder(
    start_prompt='🎤 Start Recording',
    stop_prompt='⏹️ Stop Recording',
    key='recorder'
)


# -----------------------------
# Voice Processing
if audio and audio.get('id') != st.session_state.last_audio_id:
    st.session_state.last_audio_id = audio.get('id')
    audio_bytes = audio.get('bytes')

    if audio_bytes and len(audio_bytes) > 0:
        with st.spinner('Transcribing and generating response...'):
            transcript = speech_to_text(audio_bytes)

            if not transcript.startswith('Error'):
                st.session_state.messages.append(
                    {
                        'role': 'user',
                        'content': transcript
                    }
                )

                response = get_response(transcript)

                audio_file = text_to_speech(response)
                audio_b64 = encode_audio_file(audio_file) if audio_file else None

                st.session_state.messages.append(
                    {
                        'role': 'assistant',
                        'content': response,
                        'audio_b64': audio_b64
                    }
                )

                st.rerun()
            else:
                st.error(transcript)


# -----------------------------
# Text Input
user_input = st.chat_input('Ask a question...')

if user_input:
    with st.spinner('Generating response...'):
        st.session_state.messages.append(
            {
                'role': 'user',
                'content': user_input
            }
        )

        response = get_response(user_input)

        audio_file = text_to_speech(response)
        audio_b64 = encode_audio_file(audio_file) if audio_file else None

        st.session_state.messages.append(
            {
                'role': 'assistant',
                'content': response,
                'audio_b64': audio_b64
            }
        )

        st.rerun()
