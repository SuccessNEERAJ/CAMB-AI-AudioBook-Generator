import os
import io
import requests
import streamlit as st

# ── Optional docx support ────────────────────────────────────────────────────
try:
    from docx import Document as DocxDocument
    DOCX_SUPPORTED = True
except ImportError:
    DOCX_SUPPORTED = False

# ── Language detection ────────────────────────────────────────────────────────
try:
    from langdetect import detect as langdetect_detect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# Constants  ← updated to match free-plan limit
# ─────────────────────────────────────────────────────────────────────────────
MAX_CHARS         = 500
MAX_WORDS         = 80          # ~80 words ≈ 500 chars
TTS_URL           = "https://client.camb.ai/apis/tts-stream"
VOICES_URL        = "https://client.camb.ai/apis/list-voices"
SPEECH_MODEL      = "mars-pro"
FALLBACK_VOICE_ID = 147320

LANG_TO_CAMB = {
    "en":    "en-us",
    "hi":    "hi-in",
    "fr":    "fr-fr",
    "es":    "es-es",
    "de":    "de-de",
    "ja":    "ja-jp",
    "ar":    "ar-xa",
    "ko":    "ko-kr",
    "zh":    "zh-cn",
    "zh-cn": "zh-cn",
    "it":    "it-it",
    "pt":    "pt-br",
    "id":    "id-id",
    "nl":    "nl-nl",
    "ru":    "ru-ru",
    "ta":    "ta-in",
    "te":    "te-in",
    "bn":    "bn-in",
    "mr":    "mr-in",
    "kn":    "kn-in",
    "ml":    "ml-in",
    "pl":    "pl-pl",
    "tr":    "tr-tr",
    "pa":    "pa-in",
}

LANG_DISPLAY = {
    "en-us": "English (US)",     "hi-in": "Hindi (India)",
    "fr-fr": "French (France)",  "es-es": "Spanish (Spain)",
    "de-de": "German",           "ja-jp": "Japanese",
    "ar-xa": "Arabic (MSA)",     "ko-kr": "Korean",
    "zh-cn": "Chinese (Simplified)", "it-it": "Italian",
    "pt-br": "Portuguese (Brazil)",  "id-id": "Indonesian",
    "nl-nl": "Dutch",            "ru-ru": "Russian",
    "ta-in": "Tamil",            "te-in": "Telugu",
    "bn-in": "Bengali (India)",  "mr-in": "Marathi",
    "kn-in": "Kannada",          "ml-in": "Malayalam",
    "pl-pl": "Polish",           "tr-tr": "Turkish",
    "pa-in": "Punjabi",
}

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_api_key():
    try:
        return st.secrets["TTS_API_KEY"]
    except Exception:
        return os.environ.get("TTS_API_KEY")


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_voices(api_key: str) -> list:
    try:
        resp = requests.get(VOICES_URL, headers={"x-api-key": api_key}, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def pick_voice_id(voices: list, camb_lang: str) -> int:
    if not voices:
        return FALLBACK_VOICE_ID
    lang_prefix = camb_lang.split("-")[0]
    for v in voices:
        v_lang = v.get("language", "") or ""
        langs  = v_lang if isinstance(v_lang, list) else [str(v_lang)]
        if camb_lang in langs:
            return v["id"]
    for v in voices:
        if lang_prefix in str(v.get("language", "") or ""):
            return v["id"]
    return voices[0].get("id", FALLBACK_VOICE_ID)


def detect_language(text: str):
    default = ("en-us", "English (US)")
    if not LANGDETECT_AVAILABLE or not text.strip():
        return default
    try:
        raw  = langdetect_detect(text)
        lang = raw.split("-")[0].lower()
        code = LANG_TO_CAMB.get(raw.lower()) or LANG_TO_CAMB.get(lang) or "en-us"
        return code, LANG_DISPLAY.get(code, code)
    except Exception:
        return default


def validate_text(text: str):
    chars = len(text)
    words = len(text.split())
    if chars > MAX_CHARS:
        return False, f"❌ Text exceeds {MAX_CHARS} characters ({chars} found). Please shorten your text."
    if words > MAX_WORDS:
        return False, f"❌ Text exceeds {MAX_WORDS} words ({words} found). Please shorten your text."
    if chars < 3:
        return False, "❌ Text is too short. Please enter at least 3 characters."
    return True, ""


def extract_text_from_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".txt"):
        try:
            return uploaded_file.read().decode("utf-8"), ""
        except UnicodeDecodeError:
            return "", "❌ Could not decode file. Make sure it is UTF-8 encoded."
    elif name.endswith(".docx"):
        if not DOCX_SUPPORTED:
            return "", "❌ python-docx not installed. Add it to requirements.txt."
        try:
            doc  = DocxDocument(io.BytesIO(uploaded_file.read()))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            return text, ""
        except Exception as e:
            return "", f"❌ Failed to read .docx: {e}"
    return "", "❌ Unsupported format. Please upload .txt or .docx."


def call_tts_api(text: str, voice_id: int, language: str, api_key: str):
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "voice_id": voice_id,
        "language": language,
        "speech_model": SPEECH_MODEL,
        "output_configuration": {"format": "wav"},
    }
    try:
        resp = requests.post(TTS_URL, headers=headers, json=payload, timeout=120)
        if resp.status_code == 401:
            return None, "❌ Invalid API key. Please check your TTS_API_KEY secret."
        if resp.status_code == 429:
            return None, "❌ Rate limit exceeded. Please wait a moment and try again."
        if not resp.ok:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            return None, f"❌ API error {resp.status_code}: {detail}"
        return resp.content, ""
    except requests.exceptions.Timeout:
        return None, "❌ Request timed out. Try with a shorter text."
    except requests.exceptions.RequestException as e:
        return None, f"❌ Connection error: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Page config & CSS
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Audiobook Generator",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.6rem; font-weight: 700; line-height: 1.15;
    background: linear-gradient(135deg, #F5E6C8 20%, #E8A96A 60%, #D4714E 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}
.hero-sub {
    font-size: 1rem; color: #8A8A9A; font-weight: 300;
    letter-spacing: 0.04em; margin-bottom: 1.2rem;
}
.api-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(80,200,120,0.12); border: 1px solid rgba(80,200,120,0.25);
    color: #50C878; font-size: 0.78rem; font-weight: 500;
    padding: 4px 12px; border-radius: 20px; margin-bottom: 1.6rem;
}
.api-badge-err {
    background: rgba(220,80,80,0.12); border-color: rgba(220,80,80,0.25); color: #DC5050;
}
.info-box {
    background: rgba(255,255,255,0.035); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 1.2rem 1.4rem; margin-bottom: 1.6rem;
    font-size: 0.88rem; color: #B0B0C0; line-height: 1.7;
}
.info-box strong { color: #E8A96A; }
.info-box h4 {
    font-family: 'Playfair Display', serif; font-size: 1rem;
    color: #F5E6C8; margin: 0 0 0.6rem 0;
}
.example-box {
    background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.6rem;
}
.example-label {
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: #E8A96A; margin-bottom: 0.35rem;
}
.example-text {
    font-size: 0.88rem; color: #C8C8D8; line-height: 1.55;
    font-style: italic; user-select: all;
}
.lang-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(232,169,106,0.1); border: 1px solid rgba(232,169,106,0.22);
    color: #E8A96A; font-size: 0.8rem; padding: 3px 10px;
    border-radius: 20px; margin-top: 0.5rem; margin-bottom: 0.8rem;
}
.warn-box {
    background: rgba(220,180,60,0.07); border: 1px solid rgba(220,180,60,0.18);
    border-radius: 10px; padding: 1rem 1.2rem; font-size: 0.83rem;
    color: #B0A070; line-height: 1.7; margin-top: 1.4rem;
}
.warn-box h4 { color: #D4B060; font-size: 0.9rem; margin: 0 0 0.5rem 0; }
audio { width: 100%; border-radius: 8px; margin-top: 0.4rem; }
hr { border-color: rgba(255,255,255,0.07) !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">🎙️ AI Audiobook Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">High-Quality Text-to-Speech · Powered by MARS-Pro</div>', unsafe_allow_html=True)

api_key = get_api_key()
if api_key:
    st.markdown('<div class="api-badge">🟢 API Key Loaded</div>', unsafe_allow_html=True)
else:
    st.markdown(
        '<div class="api-badge api-badge-err">🔴 API Key Missing — set TTS_API_KEY in Streamlit Secrets</div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Instructions
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="info-box">
<h4>📋 How to Use This App</h4>
This application converts your text into natural, professional-quality speech using the <strong>MARS-Pro</strong> model.
The voice and accent are <strong>auto-selected</strong> based on the detected language of your text.<br><br>
<strong>📏 Input Limits</strong><br>
&nbsp;&nbsp;• Maximum Characters: <strong>500</strong><br>
&nbsp;&nbsp;• Maximum Words: <strong>~80 words</strong><br>
&nbsp;&nbsp;• Supported File Formats: <strong>.txt</strong> and <strong>.docx</strong><br><br>
<strong>📂 For Longer Text:</strong> Split your content into chunks of 500 characters and process them one by one.
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Input mode
# ─────────────────────────────────────────────────────────────────────────────
input_mode = st.radio(
    "**Choose input method:**",
    ["✏️  Paste Text", "📄  Upload File"],
    horizontal=True,
)

raw_text = ""

# ── PASTE TEXT ───────────────────────────────────────────────────────────────
if input_mode == "✏️  Paste Text":

    with st.expander("💡 Example Texts to Try"):
        st.caption("Select the text below, copy it, and paste it into the text area.")

        st.markdown("""
<div class="example-box">
  <div class="example-label">Short</div>
  <div class="example-text">Hello! Welcome to Audiobook Generator. This is a demonstration of high-quality text-to-speech synthesis.</div>
</div>
<div class="example-box">
  <div class="example-label">Medium</div>
  <div class="example-text">The quick brown fox jumps over the lazy dog. This pangram contains every letter of the alphabet and is often used for testing font rendering and text-to-speech systems.</div>
</div>
<div class="example-box">
  <div class="example-label">Longer</div>
  <div class="example-text">In a world where technology meets creativity, artificial intelligence brings voices to life with remarkable clarity and emotion. From audiobooks to virtual assistants, text-to-speech technology is transforming how we interact with digital content.</div>
</div>
""", unsafe_allow_html=True)

    raw_text = st.text_area(
        "Enter your text below:",
        height=180,
        max_chars=MAX_CHARS,
        placeholder="Paste your text here… (max 500 characters)",
        key="textarea_input",
    )
    raw_text = raw_text.strip()

    if raw_text:
        chars = len(raw_text)
        words = len(raw_text.split())
        c1, c2 = st.columns(2)
        # Colour the metric red when over limit
        char_label = f"{chars} / {MAX_CHARS}"
        word_label = f"{words} / {MAX_WORDS}"
        c1.metric("Characters", char_label)
        c2.metric("Words",      word_label)

# ── UPLOAD FILE ──────────────────────────────────────────────────────────────
else:
    uploaded = st.file_uploader(
        "Upload a .txt or .docx file:",
        type=["txt", "docx"],
    )
    if uploaded:
        extracted, err = extract_text_from_file(uploaded)
        if err:
            st.error(err)
        else:
            raw_text = extracted.strip()
            chars = len(raw_text)
            words = len(raw_text.split())
            if chars > MAX_CHARS:
                st.warning(
                    f"⚠️ File contains {chars} characters but the limit is {MAX_CHARS}. "
                    "Only the first 500 characters will be used."
                )
                raw_text = raw_text[:MAX_CHARS]
            else:
                st.success(f"✅ File loaded — {chars} characters, {words} words")
            with st.expander("Preview text to be converted"):
                st.text(raw_text)

# ─────────────────────────────────────────────────────────────────────────────
# Language detection badge
# ─────────────────────────────────────────────────────────────────────────────
if raw_text:
    camb_lang, lang_label = detect_language(raw_text)
    st.markdown(
        f'<div class="lang-badge">🌍 Detected Language: <strong>{lang_label}</strong>'
        f'&nbsp;→&nbsp;<code>{camb_lang}</code></div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Generate
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("")
generate = st.button(
    "🎵 Generate Audio",
    disabled=(not bool(raw_text) or not bool(api_key)),
    use_container_width=True,
)

if generate:
    ok, err_msg = validate_text(raw_text)
    if not ok:
        st.error(err_msg)
    else:
        camb_lang, lang_label = detect_language(raw_text)

        with st.spinner("🔍 Selecting best voice for your language…"):
            voices   = fetch_voices(api_key)
            voice_id = pick_voice_id(voices, camb_lang)

        with st.spinner(f"🎙️ Synthesising speech in **{lang_label}** using MARS-Pro…"):
            audio_bytes, api_err = call_tts_api(raw_text, voice_id, camb_lang, api_key)

        if api_err:
            st.error(api_err)
            st.info(
                f"💡 **Debug info** — voice_id: `{voice_id}` | "
                f"language: `{camb_lang}` | model: `{SPEECH_MODEL}` | "
                f"chars: `{len(raw_text)}`"
            )
        else:
            st.success("✅ Audio generated successfully!")
            st.audio(audio_bytes, format="audio/wav")
            st.download_button(
                label="⬇️ Download Audio (.wav)",
                data=audio_bytes,
                file_name="audiobook_output.wav",
                mime="audio/wav",
            )

# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="warn-box">
<h4>⚠️ Important Information</h4>
• <strong>API Usage:</strong> This app uses the Camb.AI MARS-Pro model for text-to-speech generation.<br>
• <strong>Character Limit:</strong> Your current plan allows up to <strong>500 characters per request</strong>.<br>
• <strong>Rate Limits:</strong> Please use responsibly to avoid API rate limits.<br>
• <strong>Privacy:</strong> Your text is sent to the Camb.AI API for processing.<br>
• <strong>Data:</strong> Audio files are generated on-demand and not stored permanently.
</div>
""", unsafe_allow_html=True)
