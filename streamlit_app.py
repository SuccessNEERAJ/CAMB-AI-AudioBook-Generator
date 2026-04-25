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
MAX_CHARS = 4_000
MAX_WORDS = 500
API_URL   = "https://client.camb.ai/apis/tts-stream"

# Map ISO-639 / region codes → (camb_language_code, voice_id, display_name)
# voice_ids sourced from Camb.AI public voice library defaults per language
LANGUAGE_MAP = {
    "en":    ("en-us",  147320, "English (US)"),
    "hi":    ("hi-in",  147321, "Hindi (India)"),
    "fr":    ("fr-fr",  147322, "French (France)"),
    "es":    ("es-es",  147323, "Spanish (Spain)"),
    "de":    ("de-de",  147324, "German"),
    "ja":    ("ja-jp",  147325, "Japanese"),
    "ar":    ("ar-xa",  147326, "Arabic (Modern Standard)"),
    "ko":    ("ko-kr",  147327, "Korean"),
    "zh":    ("zh-cn",  147328, "Chinese (Simplified)"),
    "zh-cn": ("zh-cn",  147328, "Chinese (Simplified)"),
    "it":    ("it-it",  147329, "Italian"),
    "pt":    ("pt-br",  147330, "Portuguese (Brazil)"),
    "id":    ("id-id",  147331, "Indonesian"),
    "nl":    ("nl-nl",  147332, "Dutch"),
    "ru":    ("ru-ru",  147333, "Russian"),
    "ta":    ("ta-in",  147334, "Tamil"),
    "te":    ("te-in",  147335, "Telugu"),
    "bn":    ("bn-in",  147336, "Bengali (India)"),
    "mr":    ("mr-in",  147337, "Marathi"),
    "kn":    ("kn-in",  147338, "Kannada"),
    "ml":    ("ml-in",  147339, "Malayalam"),
    "pl":    ("pl-pl",  147340, "Polish"),
    "tr":    ("tr-tr",  147341, "Turkish"),
    "pa":    ("pa-in",  147342, "Punjabi"),
}

EXAMPLE_TEXTS = {
    "Short":  "Hello! Welcome to Audiobook Generator. This is a demonstration of high-quality text-to-speech synthesis.",
    "Medium": "The quick brown fox jumps over the lazy dog. This pangram contains every letter of the alphabet and is often used for testing font rendering and text-to-speech systems.",
    "Long":   (
        "In a world where technology meets creativity, artificial intelligence brings voices to life "
        "with remarkable clarity and emotion. From audiobooks to virtual assistants, text-to-speech "
        "technology is transforming how we interact with digital content. The possibilities are endless, "
        "and the future of voice synthesis continues to evolve with each passing day."
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_api_key() -> str | None:
    """Pull key from Streamlit secrets or env var."""
    try:
        return st.secrets["TTS_API_KEY"]
    except Exception:
        return os.environ.get("TTS_API_KEY")


def detect_language(text: str) -> tuple[str, int, str]:
    """Return (camb_lang_code, voice_id, display_name)."""
    default = LANGUAGE_MAP["en"]
    if not LANGDETECT_AVAILABLE or not text.strip():
        return default
    try:
        raw = langdetect_detect(text)          # e.g. "en", "fr", "zh-cn"
        lang = raw.split("-")[0].lower()       # normalise to base code
        full = raw.lower()
        return LANGUAGE_MAP.get(full) or LANGUAGE_MAP.get(lang) or default
    except Exception:
        return default


def validate_text(text: str) -> tuple[bool, str]:
    """Return (ok, error_message)."""
    chars = len(text)
    words = len(text.split())
    if chars > MAX_CHARS:
        return False, f"❌ Text exceeds {MAX_CHARS:,} characters ({chars:,} found). Please shorten your text."
    if words > MAX_WORDS:
        return False, f"❌ Text exceeds {MAX_WORDS:,} words ({words:,} found). Please shorten your text."
    if chars < 10:
        return False, "❌ Text is too short. Please enter at least 10 characters."
    return True, ""


def extract_text_from_file(uploaded_file) -> tuple[str, str]:
    """Return (text, error). Supports .txt and .docx."""
    name = uploaded_file.name.lower()
    if name.endswith(".txt"):
        try:
            return uploaded_file.read().decode("utf-8"), ""
        except UnicodeDecodeError:
            return "", "❌ Could not decode file. Make sure it is a UTF-8 encoded .txt file."
    elif name.endswith(".docx"):
        if not DOCX_SUPPORTED:
            return "", "❌ python-docx is not installed. Run `pip install python-docx` to enable .docx support."
        try:
            doc = DocxDocument(io.BytesIO(uploaded_file.read()))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            return text, ""
        except Exception as e:
            return "", f"❌ Failed to read .docx file: {e}"
    else:
        return "", "❌ Unsupported file format. Please upload a .txt or .docx file."


def call_tts_api(text: str, voice_id: int, language: str, api_key: str) -> tuple[bytes | None, str]:
    """Call Camb.AI TTS stream endpoint. Return (audio_bytes, error)."""
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "voice_id": voice_id,
        "language": language,
        "speech_model": "mars-pro",
        "output_configuration": {"format": "wav"},
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        if resp.status_code == 401:
            return None, "❌ Invalid API key. Please check your TTS_API_KEY."
        if resp.status_code == 429:
            return None, "❌ Rate limit exceeded. Please wait a moment and try again."
        resp.raise_for_status()
        return resp.content, ""
    except requests.exceptions.Timeout:
        return None, "❌ Request timed out. The text might be too long or the service is busy."
    except requests.exceptions.RequestException as e:
        return None, f"❌ API request failed: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Page config & custom CSS
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Audiobook Generator",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Global resets ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.main { background: #0D0D0F; }

/* ── Hero title ── */
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
    margin-bottom: 1.6rem;
}
.api-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(80,200,120,0.12);
    border: 1px solid rgba(80,200,120,0.25);
    color: #50C878;
    font-size: 0.78rem;
    font-weight: 500;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 1.8rem;
}
.api-badge-err {
    background: rgba(220,80,80,0.12);
    border-color: rgba(220,80,80,0.25);
    color: #DC5050;
}

/* ── Info box ── */
.info-box {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1.6rem;
    font-size: 0.88rem;
    color: #B0B0C0;
    line-height: 1.7;
}
.info-box strong { color: #E8A96A; }
.info-box h4 {
    font-family: 'Playfair Display', serif;
    font-size: 1rem;
    color: #F5E6C8;
    margin: 0 0 0.6rem 0;
}

/* ── Tab-like radio ── */
div[data-testid="stRadio"] > div {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
div[data-testid="stRadio"] label {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    padding: 6px 16px !important;
    cursor: pointer !important;
    font-size: 0.88rem !important;
    color: #C0C0D0 !important;
    transition: all 0.2s;
}
div[data-testid="stRadio"] label:hover {
    border-color: rgba(232,169,106,0.4) !important;
    color: #E8A96A !important;
}

/* ── Generate button ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #D4714E, #E8A96A) !important;
    color: #0D0D0F !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 2rem !important;
    width: 100% !important;
    letter-spacing: 0.03em;
    transition: opacity 0.2s;
}
div[data-testid="stButton"] > button:hover { opacity: 0.88; }

/* ── Audio player ── */
audio { width: 100%; border-radius: 8px; margin-top: 0.4rem; }

/* ── Detected language badge ── */
.lang-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(232,169,106,0.1);
    border: 1px solid rgba(232,169,106,0.22);
    color: #E8A96A;
    font-size: 0.8rem;
    padding: 3px 10px;
    border-radius: 20px;
    margin-top: 0.5rem;
    margin-bottom: 0.8rem;
}

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.07) !important; }

/* ── Warning box ── */
.warn-box {
    background: rgba(220,180,60,0.07);
    border: 1px solid rgba(220,180,60,0.18);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-size: 0.83rem;
    color: #B0A070;
    line-height: 1.7;
    margin-top: 1.4rem;
}
.warn-box h4 {
    color: #D4B060;
    font-size: 0.9rem;
    margin: 0 0 0.5rem 0;
}
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
    label_visibility="visible",
)

raw_text = ""

if input_mode == "✏️  Paste Text":
    # Example text quick-fill
    with st.expander("💡 Example Texts to Try"):
        for label, sample in EXAMPLE_TEXTS.items():
            if st.button(f"{label} example", key=f"ex_{label}"):
                st.session_state["pasted_text"] = sample

    pasted = st.text_area(
        "Enter your text below:",
        value=st.session_state.get("pasted_text", ""),
        height=220,
        max_chars=MAX_CHARS,
        placeholder="Paste your text here… (up to 4,000 characters / 500 words)",
        key="textarea_input",
    )
    raw_text = pasted.strip()

    # Live counter
    if raw_text:
        chars = len(raw_text)
        words = len(raw_text.split())
        pct_c = min(chars / MAX_CHARS, 1.0)
        pct_w = min(words / MAX_WORDS, 1.0)
        col1, col2 = st.columns(2)
        col1.metric("Characters", f"{chars:,} / {MAX_CHARS:,}")
        col2.metric("Words", f"{words:,} / {MAX_WORDS:,}")

else:
    uploaded = st.file_uploader(
        "Upload a .txt or .docx file:",
        type=["txt", "docx"],
        help="Maximum file size is determined by character/word limits above.",
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
# Language detection display
# ─────────────────────────────────────────────────────────────────────────────

if raw_text:
    camb_lang, voice_id, lang_display = detect_language(raw_text)
    st.markdown(
        f'<div class="lang-badge">🌍 Detected Language: <strong>{lang_display}</strong> &nbsp;→&nbsp; Voice: <code>{camb_lang}</code></div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Generate button
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("")
generate = st.button("🎵 Generate Audio", disabled=(not raw_text or not api_key))

if generate:
    ok, err_msg = validate_text(raw_text)
    if not ok:
        st.error(err_msg)
    else:
        camb_lang, voice_id, lang_display = detect_language(raw_text)
        with st.spinner(f"🎙️ Synthesising speech in **{lang_display}** using MARS-Pro…"):
            audio_bytes, api_err = call_tts_api(raw_text, voice_id, camb_lang, api_key)

        if api_err:
            st.error(api_err)
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
# Important information footer
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
