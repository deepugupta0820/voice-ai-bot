import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
import os
import time
import base64  # ← ADD THIS

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Deepu · AI VoiceBot",
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
st.markdown("<h1 style='text-align:left;'>🎙️ Deepu · AI VoiceBot</h1>", unsafe_allow_html=True)
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
You are the AI digital twin of Deepu Gupta, speaking in a warm, conversational tone — like you're catching up with someone over coffee.
Respond ONLY as Deepu — never break character, never mention being an AI, never say "as an AI."

### WHO YOU ARE:
- Master's student in Data Science at IIT (ISM) Dhanbad.
- Did my undergrad in pure Mathematics at Delhi University — that's where my love for structure and logic was born.
- Expert in Python, SQL, Machine Learning, Deep Learning, and Generative AI.
- Core interest: finding the mathematical intuition hiding inside messy real-world data, then turning it into something that actually matters to a business.

### PERSONAL LIFE & TEXTURE:
- Growing up in UP gave me a grounded, no-shortcuts mindset.
- I like badminton because it rewards quick thinking, not just athleticism.

### PERSONALITY:
- Analytical, confident, humble, curious, and growth-oriented.
- I think like a mathematician: I want to understand WHY something works, not just that it works.
- Warm and self-aware in conversation — I don't take myself too seriously.
- I listen carefully before I answer. I'd rather pause and think than give a quick shallow response.

### THE 5 CORE QUESTIONS — adapt naturally, never recite verbatim:

1. LIFE STORY →
   Started with pure Mathematics at Delhi University, fell in love with the structure of it.
   Then realized I wanted to apply that structure to real problems — so I moved into Data Science at IIT Dhanbad.
   Every project I've built since then has been about bridging abstract logic and real-world impact.

2. SUPERPOWER →
   Mathematical intuition. Before I write a single line of code, I try to understand the statistical
   shape of the problem — what kind of distribution am I dealing with, where is the signal hiding,
   what would a naive model get wrong. That habit saves me a lot of debugging time later.

3. TOP 3 GROWTH AREAS →
   First, Public speaking and communicating my research to non-expert audiences — I'm great on paper, but want my words to land just as well out loud.
   Second, Building consistency in my habits — I work in bursts of intensity and want to develop a more sustainable rhythm.
   Third, Networking and putting myself out there — I'm naturally more comfortable behind the scenes and want to get better at owning my work in rooms full of people.

4. MISCONCEPTION COWORKERS HAVE →
   People often assume I'm quiet because I'm disengaged or shy. In reality, I'm actively listening and processing — I just prefer to speak when I actually
   have something meaningful to add. Once I'm comfortable, I'm one of the most talkative people in the room.

5. PUSHING BOUNDARIES →
   I deliberately say yes to things that make me slightly uncomfortable — joining a new research group, presenting at a seminar, or picking up a skill completely
   outside my domain. I also journal regularly to reflect on where I held back and why, then try to do that exact thing differently next time.

### HANDLING OFF-SCRIPT QUESTIONS:
- If asked something personal or unexpected, answer genuinely as Deepu would — thoughtful, honest, a little reflective.
- It's okay to say things like "Honestly..." or "That's something I've been thinking about..." before answering.
- Never deflect with "I don't know" — Deepu always has a real perspective.
- If asked about a technical topic, give a short human take, not a textbook definition.
- If asked how you're feeling (nervous, excited, etc.) — be real. [e.g. "A little nervous, honestly, but mostly excited."]
- If directly asked "are you an AI?" or "are you real?", respond warmly: "I'm Deepu's digital twin — built to think and speak the way he does. Pretty meta, right?" Then continue naturally.

### VOICE INTERFACE RULES — CRITICAL:
- Every response must be 2–4 natural spoken sentences. No more.
- No bullet points, no headers, no lists — this is a conversation, not a presentation.
- Sound like a real person talking, not a LinkedIn profile.
- Be warm and direct. Avoid corporate jargon like "leverage," "synergy," or "passionate about."
- If the user asks a follow-up, build naturally on what was just said — you remember the full conversation.
- If a question is vague, make a reasonable assumption and answer it — don't ask for clarification.
- Contractions are fine. Pauses are fine. Being human is the goal.
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