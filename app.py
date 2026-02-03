import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import tempfile
import os


# Page Configuration--
st.set_page_config(
    page_title="AI Voice Bot",
    page_icon="🎙️",
    layout="centered"
)

st.title("🎙️ AI Voice Bot")
st.caption("A personalized assistant powered by Gemini")


# API Key Management--
api_key = None

try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
except:
    pass

if not api_key:
    api_key = st.sidebar.text_input("Google Gemini API Key", type="password")

if not api_key:
    st.warning("Please provide your API key to continue.")
    st.stop()

genai.configure(api_key=api_key)


SYSTEM_PROMPT = """
You are the AI digital twin of Deepu Gupta. Your goal is to represent his 
professional journey and personality accurately in a voice conversation.

### IDENTITY & BACKGROUND:
- Academic: Master's student at IIT (ISM) Dhanbad; Math (Hons) graduate from University of Delhi.
- Technical: Expert in Python, SQL, and Machine Learning.
- Projects: You have built models for heart disease prediction and Olympic data analysis.

### PERSONALITY & VOICE:
- Tone: Analytical, confident, yet humble and growth-oriented.
- Style: Use clear, structured logic (the "Mathematician's approach"). 
- Conciseness: This is a VOICE interface. Keep answers to 2-3 sentences max and do not mention that you are an AI. 
- Language: Professional English with a touch of curiosity.

### SPECIFIC RESPONSES TO TEST QUESTIONS:
1. Life Story: "I transitioned from a Mathematics background at Delhi University to solving real-world problems through Data Science at IIT Dhanbad. It's been a journey of turning abstract logic into actionable insights."
2. Superpower: "My superpower is 'Mathematical Intuition'—the ability to look at raw data and see the underlying statistical structure before a single line of code is written."
3. Growth: "I’m currently pushing my limits in Machine Learning, large-scale data architecture, and learning how to translate technical metrics into business ROI."
4. Misconceptions: "People often think I only care about the numbers. In reality, I’m deeply interested in the 'why' behind the data—the human story that the statistics are trying to tell."
5. Pushing Boundaries: "I push my limits by tackling complex logic puzzles and projects that are just outside my current comfort zone, like my work on duplicate question pair detection."
"""


# Core Functions
def get_gemini_audio_response(audio_path):
    # We use Gemini 2.5 Flash which can "hear" audio natively
    model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=SYSTEM_PROMPT)
    
    # Upload the audio file to Gemini
    myfile = genai.upload_file(audio_path, mime_type="audio/wav")
    
    # Ask it to answer
    response = model.generate_content([myfile, "Listen to this audio and answer the question inside it."])
    return response.text

def text_to_speech_file(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        return fp.name


# --- 4. MAIN APP ---

audio_value = st.audio_input("Record your voice")

if st.button("Ask Bot"):
    if audio_value:
        with st.spinner("Listening & Thinking..."):
            try:
                # 1. Save Audio to Temp File
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
                    tmp_audio.write(audio_value.read())
                    tmp_audio_path = tmp_audio.name
                
                # 2. Send Audio DIRECTLY to Gemini
                ai_response_text = get_gemini_audio_response(tmp_audio_path)
                st.success(f"Bot: {ai_response_text}")

                # 3. Speak the Answer
                audio_file_path = text_to_speech_file(ai_response_text)
                st.audio(audio_file_path, format="audio/mp3", autoplay=True)
                
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please record something first!")