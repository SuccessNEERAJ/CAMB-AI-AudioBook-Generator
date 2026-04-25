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
# Constants
# ─────────────────────────────────────────────────────────────────────────────
MAX_CHARS    = 4_000
MAX_WORDS    = 500
TTS_URL      = "https://client.camb.ai/apis/tts-stream"
VOICES_URL   = "https://client.camb.ai/apis/list-voices"
SPEECH_MODEL = "mars-pro"          # confirmed valid string per Camb.AI docs
FALLBACK_VOICE_ID = 147320         # confirmed in official Camb.AI docs/examples

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
    "en-us": "English (US)",
    "hi-in": "Hindi (India)",
    "fr-fr": "French (France)",
    "es-es": "Spanish (Spain)",
    "de-de": "German",
    "ja-jp": "Japanese",
    "ar-xa": "Arabic (Modern Standard)",
    "ko-kr": "Korean",
    "zh-cn": "Chinese (Simplified)",
    "it-it": "Italian",
    "pt-br": "Portuguese (Brazil)",
    "id-id": "Indonesian",
    "nl-nl": "Dutch",
    "ru-ru": "Russian",
    "ta-in": "Tamil",
    "te-in": "Telugu",
    "bn-in": "Bengali (India)",
    "mr-in": "Marathi",
    "kn-in": "Kannada",
    "ml-in": "Malayalam",
    "pl-pl": "Polish",
    "tr-tr": "Turkish",
    "pa-in": "Punjabi",
}

EXAMPLE_TEXTS = {
    "Short":  "Hello! Welcome to Audiobook Generator. This is a demonstration of high-quality text-to-speech synthesis.",
    "Medium": "The quick brown fox jumps over the lazy dog. This pangram contains every letter of the alphabet and is often used for testing font rendering and text-to-speech systems.",
    "Long": (
        "In a world where technology meets creativity, artificial intelligence brings voices to life "
        "with remarkable clarity and emotion. From audiobooks to virtual assistants, text-to-speech "
        "technology is transforming how we interact with digital content. The possibilities are endless, "
        "and the future of voice synthesis continues to evolve with each passing day."
    ),
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
    """Fetch and cache all available voices from Camb.AI."""
    try:
        resp = requests.get(VOICES_URL, headers={"x-api-key": api_key}, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def pick_voice_id(voices: list, camb_lang: str) -> int:
    """
    Pick the best voice_id for a language.
    Tries exact language match first, then base-language prefix, then first voice.
    """
    if not voices:
        return FALLBACK_VOICE_ID

    lang_prefix = camb_lang.split("-")[0]

    for v in voices:
        v_lang = v.get("language", "") or ""
        if isinstance(v_lang, list):
            if camb_lang in v_lang:
                return v["id"]
        elif camb_lang in str(v_lang):
            return v["id"]

    for v in voices:
        v_lang = str(v.get("language", "") or "")
        if lang_prefix in v_lang:
            return v["id"]

    return voices[0].get("id", FALLBACK_VOICE_ID)


def detect_language(text: str):
    """Return (camb_lang_code, display_name)."""
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
        return False, f"❌ Text exceeds {MAX_CHARS:,} characters ({chars:,} found). Please shorten your text."
    if words > MAX_WORDS:
        return False, f"❌ Text exceeds {MAX_WORDS:,} words ({words:,} found). Please shorten your text."
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
            return "", "❌ python-docx is not installed. Add it to requirements.txt."
        try:
            doc  = DocxDocument(io.BytesIO(uploaded_file.read()))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            return text, ""
        except Exception as e:
            return "", f"❌ Failed to read .docx: {e}"
    return "", "❌ Unsupported format. Please upload .txt or .docx."


def call_tts_api(text: str, voice_id: int, language: str, api_key: str):
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }
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
    font-size: 2.6rem;
    font-weight: 700;
    line-height: 1.15;
    background: linear-gradient(135deg, #F5E6C8 20%, #E8A96A 60%, #D4714E 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}
.hero-sub {
    font-size: 1rem;
    color: #8A8A9A;
    font-weight: 300;
    letter-spacing: 0.04em;
    margin-bottom: 1.2rem;
}
.api-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(80,200,120,0.12);
    border: 1px solid rgba(80,200,120,0.25);
    color: #50C878; font-size: 0.78rem; font-weight: 500;
    padding: 4px 12px; border-radius: 20px; margin-bottom: 1.6rem;
}
.api-badge-err {
    background: rgba(220,80,80,0.12);
    border-color: rgba(220,80,80,0.25);
    color: #DC5050;
}
.info-box {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 1.2rem 1.4rem;
    margin-bottom: 1.6rem; font-size: 0.88rem;
    color: #B0B0C0; line-height: 1.7;
}
.info-box strong { color: #E8A96A; }
.info-box h4 {
    font-family: 'Playfair Display', serif;
    font-size: 1rem; color: #F5E6C8; margin: 0 0 0.6rem 0;
}
.lang-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(232,169,106,0.1);
    border: 1px solid rgba(232,169,106,0.22);
    color: #E8A96A; font-size: 0.8rem;
    padding: 3px 10px; border-radius: 20px;
    margin-top: 0.5rem; margin-bottom: 0.8rem;
}
.warn-box {
    background: rgba(220,180,60,0.07);
    border: 1px solid rgba(220,180,60,0.18);
    border-radius: 10px; padding: 1rem 1.2rem;
    font-size: 0.83rem; color: #B0A070;
    line-height: 1.7; margin-top: 1.4rem;
}
.warn-box h4 { color: #D4B060; font-size: 0.9rem; margin: 0 0 0.5rem 0; }
audio { width: 100%; border-radius: 8px; margin-top: 0.4rem; }
hr { border-color: rgba(255,255,255,0.07) !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Session state init — must happen before any widget that reads it
# ─────────────────────────────────────────────────────────────────────────────
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""

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
&nbsp;&nbsp;• Maximum Characters: <strong>4,000</strong><br>
&nbsp;&nbsp;• Maximum Words: <strong>500</strong><br>
&nbsp;&nbsp;• Approximate Audio Length: <strong>~4 minutes</strong><br>
&nbsp;&nbsp;• Supported File Formats: <strong>.txt</strong> and <strong>.docx</strong><br><br>
<strong>📂 For Large Documents:</strong> Split your document into smaller chunks and process them one by one.
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

    # Example buttons — use on_click callbacks so session state is updated
    # BEFORE the text_area widget re-renders. This is the correct Streamlit pattern.
    with st.expander("💡 Example Texts to Try"):
        st.caption("Click a button to instantly load an example:")
        col_s, col_m, col_l, _ = st.columns([1, 1, 1, 3])

        def _set_short():
            st.session_state["input_text"] = EXAMPLE_TEXTS["Short"]

        def _set_medium():
            st.session_state["input_text"] = EXAMPLE_TEXTS["Medium"]

        def _set_long():
            st.session_state["input_text"] = EXAMPLE_TEXTS["Long"]

        with col_s:
            st.button("📝 Short",  on_click=_set_short,  key="btn_short")
        with col_m:
            st.button("📄 Medium", on_click=_set_medium, key="btn_medium")
        with col_l:
            st.button("📚 Long",   on_click=_set_long,   key="btn_long")

    # Bind text area to the same session_state key so callbacks take effect
    raw_text = st.text_area(
        "Enter your text below:",
        value=st.session_state["input_text"],
        height=220,
        max_chars=MAX_CHARS,
        placeholder="Paste your text here… (up to 4,000 characters / 500 words)",
        key="textarea_input",
    )
    # Sync back so user edits are preserved across reruns
    st.session_state["input_text"] = raw_text
    raw_text = raw_text.strip()

    if raw_text:
        chars = len(raw_text)
        words = len(raw_text.split())
        c1, c2 = st.columns(2)
        c1.metric("Characters", f"{chars:,} / {MAX_CHARS:,}")
        c2.metric("Words",      f"{words:,} / {MAX_WORDS:,}")

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
            st.success(f"✅ File loaded — {chars:,} characters, {words:,} words")
            with st.expander("Preview extracted text"):
                st.text(raw_text[:800] + ("…" if len(raw_text) > 800 else ""))

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
                f"language: `{camb_lang}` | model: `{SPEECH_MODEL}`"
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
• <strong>Rate Limits:</strong> Please use responsibly to avoid API rate limits.<br>
• <strong>Privacy:</strong> Your text is sent to the Camb.AI API for processing.<br>
• <strong>Data:</strong> Audio files are generated on-demand and not stored permanently.
</div>
""", unsafe_allow_html=True)
