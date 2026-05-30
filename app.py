import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
import os
import time
import base64  # ← ADD THIS

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Voice Bot",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0f1117; color: #e8eaf0; }

.user-bubble {
    background: #1e2130;
    border: 1px solid #2d3148;
    border-radius: 16px 16px 4px 16px;
    padding: 12px 16px;
    margin: 8px 0 8px 20%;
    font-size: 0.92rem;
    color: #c9d1e8;
    line-height: 1.6;
}
.bot-bubble {
    background: linear-gradient(135deg, #1a2744, #1e1a3a);
    border: 1px solid #3a4a7a;
    border-radius: 16px 16px 16px 4px;
    padding: 12px 16px;
    margin: 8px 20% 8px 0;
    font-size: 0.92rem;
    color: #dde4f5;
    line-height: 1.6;
}
.label-you { font-size: 0.72rem; color: #6b7299; text-align: right; margin-bottom: 2px; }
.label-bot { font-size: 0.72rem; color: #6b7299; margin-bottom: 2px; }

.status-pill {
    display: inline-block;
    background: #1e2130;
    border: 1px solid #3a4a7a;
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 0.8rem;
    color: #8899cc;
    margin: 8px 0;
}
.section-title {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    color: #4a5280;
    text-transform: uppercase;
    margin: 24px 0 8px 0;
}
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='text-align:left;'>🎙️ AI Voice Bot</h1>", unsafe_allow_html=True)
st.markdown('<div class="status-pill">A personalized assistant powered by Groq · Whisper · gTTS</div>', unsafe_allow_html=True)


# ── API Key ───────────────────────────────────────────────────────────────────
api_key = None
try:
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = st.sidebar.text_input(
        "🔑 Groq API Key",
        type="password",
        help="Get your free key at console.groq.com → API Keys"
    )

if not api_key:
    st.info("👈 Add your **Groq API Key** in the sidebar to begin.\n\nGet a free key at [console.groq.com](https://console.groq.com) → API Keys")
    st.stop()

client = Groq(api_key=api_key)

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are the AI digital twin of Deepu Gupta, speaking in a voice conversation.
Respond ONLY as Deepu — never break character or mention being an AI.

### WHO YOU ARE:
- Master's student at IIT (ISM) Dhanbad.
- Expert in Python, SQL, Machine Learning.
- Built projects: heart disease prediction, Olympic data analysis, duplicate question-pair detection.
- Interests: mathematical intuition, data storytelling, bridging stats and business impact.

### PERSONALITY:
- Analytical, confident, humble, curious, growth-oriented.
- Use the "Mathematician's approach": structured, logical, precise.

### VOICE INTERFACE RULES — CRITICAL:
- Keep every answer to 2–4 natural spoken sentences. No bullet points, no headers.
- Sound like a real person talking, not a resume.
- Be warm and conversational; avoid corporate jargon.
- If the user asks a follow-up, build on what was said before — you remember the conversation.

### CORE ANSWERS (adapt naturally, don't recite verbatim):
1. Life Story → Transitioned from pure Mathematics at Delhi University to applied Data Science at IIT Dhanbad. Turning abstract logic into real-world insights is what drives me.
2. Superpower → Mathematical intuition — seeing the statistical structure hiding inside raw data before writing a single line of code.
3. Growth Areas → Machine Learning depth, large-scale data architecture, translating technical metrics into business ROI.
4. Misconceptions → People think I only care about numbers. I actually care deeply about the human story the data is trying to tell.
5. Pushing Boundaries → I take on projects just outside my comfort zone — like duplicate-question-pair detection — and sit with the discomfort until it becomes clarity.
"""

# ── Session State ─────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "groq_messages" not in st.session_state:
    st.session_state.groq_messages = []
if "recorder_key" not in st.session_state:
    st.session_state.recorder_key = 0
if "pending_audio_b64" not in st.session_state:
    st.session_state.pending_audio_b64 = None


# ── Helper Functions ──────────────────────────────────────────────────────────
def transcribe_audio(audio_path: str) -> str:
    with open(audio_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f),
            model="whisper-large-v3",
            language="en",
            response_format="text",
        )
    return transcription.strip() if isinstance(transcription, str) else transcription.text.strip()


def get_text_response(user_text: str) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += st.session_state.groq_messages
    messages.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=300,
        temperature=0.75,
    )
    reply = response.choices[0].message.content.strip()

    st.session_state.groq_messages.append({"role": "user",      "content": user_text})
    st.session_state.groq_messages.append({"role": "assistant", "content": reply})
    return reply


def text_to_speech_b64(text: str) -> str:
    """Convert text to speech and return as a base64-encoded string."""
    tts = gTTS(text=text, lang="en", slow=False)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        tmp_path = fp.name

    with open(tmp_path, "rb") as f:
        audio_bytes = f.read()

    os.unlink(tmp_path)
    return base64.b64encode(audio_bytes).decode("utf-8")


def play_audio_b64(b64_string: str):
    """Render an HTML audio tag with the base64 data URI — survives reruns."""
    audio_html = f"""
    <audio autoplay style="width:100%; margin-top:8px;">
        <source src="data:audio/mp3;base64,{b64_string}" type="audio/mp3">
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)


# ── Chat History ──────────────────────────────────────────────────────────────
if st.session_state.chat_history:
    st.markdown('<div class="section-title">Conversation</div>', unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="label-you">You</div>'
                f'<div class="user-bubble">{msg["text"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="label-bot">Deepu</div>'
                f'<div class="bot-bubble">{msg["text"]}</div>',
                unsafe_allow_html=True
            )

if st.session_state.pending_audio_b64:
    play_audio_b64(st.session_state.pending_audio_b64)
    st.session_state.pending_audio_b64 = None


# ── Audio Input ───────────────────────────────────────────────────────────────
audio_value = st.audio_input(
    "🎤 Tap to record",
    key=f"audio_recorder_{st.session_state.recorder_key}",
)
ask_voice = st.button(
    "Send Voice Message ▶",
    use_container_width=True,
    type="primary",
    key="send_voice",
)

# ── Clear Button ──────────────────────────────────────────────────────────────
if st.session_state.chat_history:
    if st.button("🗑️ Clear conversation"):
        st.session_state.chat_history = []
        st.session_state.groq_messages = []
        st.session_state.pending_audio_b64 = None
        st.session_state.recorder_key += 1
        st.rerun()


# ── Core Pipeline ──────────────────────────────────────────────────────
def process_question(user_text: str):
    st.session_state.chat_history.append({"role": "user", "text": user_text})

    with st.spinner("Thinking…"):
        reply = get_text_response(user_text)

    st.session_state.chat_history.append({"role": "bot", "text": reply})


    with st.spinner("Generating voice…"):
        st.session_state.pending_audio_b64 = text_to_speech_b64(reply)

    st.session_state.recorder_key += 1
    st.rerun()


# ── Voice Flow ────────────────────────────────────────────────────────────────
if ask_voice:
    if audio_value:
        tmp_path = None
        try:
            with st.spinner("Transcribing your voice…"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(audio_value.read())
                    tmp_path = tmp.name
                user_text = transcribe_audio(tmp_path)

            if user_text:
                process_question(user_text)
            else:
                st.warning("Couldn't catch that — please try recording again.")
        except Exception as e:
            st.error(f"Something went wrong: {e}")
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
    else:
        st.warning("⬆️ Please record your voice first using the microphone above.")