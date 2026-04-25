<div align="center">

# 🎙️ AI Powered Audiobook Generator

### High-Quality Text-to-Speech Powered by MARS-Pro · Built with Streamlit

[![Live App](https://img.shields.io/badge/🚀%20Live%20App-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://camb-ai-audiobook-generator.streamlit.app/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-SuccessNEERAJ-181717?style=for-the-badge&logo=github)](https://github.com/SuccessNEERAJ/CAMB-AI-AudioBook-Generator)
[![Powered by Camb.AI](https://img.shields.io/badge/Powered%20by-Camb.AI%20MARS--Pro-orange?style=for-the-badge)](https://camb.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Languages](https://img.shields.io/badge/Languages-30%2B-blue?style=for-the-badge)](https://docs.camb.ai/models)

<br/>

> **Convert any text into professional-quality narrated audio — in 30+ languages — instantly.**  
> Powered by Camb.AI's MARS-Pro model with automatic language detection and voice selection.

<br/>

![App Screenshot](https://raw.githubusercontent.com/SuccessNEERAJ/CAMB-AI-AudioBook-Generator/main/assets/screenshot.png)

</div>

---

## 📋 Table of Contents

1. [✨ What Does This App Do?](#-what-does-this-app-do)
2. [🚀 Try It Live](#-try-it-live)
3. [🏗️ Application Flowchart](#️-application-flowchart)
4. [🏢 About Camb.AI — The Company](#-about-cambai--the-company)
5. [🤖 The MARS Model Family](#-the-mars-model-family)
6. [⭐ Why MARS-Pro? Why Camb.AI?](#-why-mars-pro-why-cambai)
7. [🌍 Supported Languages](#-supported-languages)
8. [📁 Project Structure](#-project-structure)
9. [⚙️ Features](#️-features)
10. [📏 Input Limits](#-input-limits)
11. [🔧 How to Fork & Deploy Your Own Copy](#-how-to-fork--deploy-your-own-copy)
12. [🔑 Getting Your Camb.AI API Key](#-getting-your-cambai-api-key)
13. [🧠 How the Code Works](#-how-the-code-works)
14. [🛠️ Tech Stack](#️-tech-stack)
15. [⚠️ Important Notes](#️-important-notes)
16. [📜 License](#-license)

---

## ✨ What Does This App Do?

The **AI Powered Audiobook Generator** is a web application that transforms written text into natural, human-like narrated audio using state-of-the-art AI. Whether you're a student, content creator, developer, or someone who loves audiobooks — this tool lets you convert any text into a downloadable `.wav` audio file in seconds.

**Key capabilities at a glance:**

- 📝 **Paste text directly** or **upload a file** (`.txt` / `.docx`)
- 🌍 **Auto-detects the language** of your text — no manual selection needed
- 🎤 **Auto-selects the best voice** for the detected language from Camb.AI's voice library
- 🔊 **Generates broadcast-quality audio** using the MARS-Pro model at 48kHz
- ⬇️ **Download the output** as a `.wav` file instantly

---

## 🚀 Try It Live

No installation needed. The app is deployed and ready to use:

### 👉 [https://camb-ai-audiobook-generator.streamlit.app/](https://camb-ai-audiobook-generator.streamlit.app/)

---

## 🏗️ Application Flowchart

The following diagram shows the complete end-to-end flow of the application — from user input to audio output.

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER OPENS THE APP                           │
│              (Streamlit Web Interface)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CHOOSE INPUT METHOD                            │
│                                                                 │
│        ┌──────────────────┐     ┌──────────────────┐           │
│        │  ✏️ Paste Text    │     │  📄 Upload File   │           │
│        │  (text area)     │     │  (.txt / .docx)   │           │
│        └────────┬─────────┘     └────────┬──────────┘           │
└─────────────────┼───────────────────────┼───────────────────────┘
                  │                       │
                  │   ┌───────────────────┘
                  │   │  Extract text from file
                  │   │  (python-docx / utf-8 decode)
                  ▼   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATE INPUT                               │
│                                                                 │
│   • Check character count  ≤ 500                                │
│   • Check word count       ≤ ~80 words                          │
│   • Check minimum length   ≥ 3 characters                       │
│                                                                 │
│        ❌ Fails? → Show error message, stop.                     │
│        ✅ Passes? → Continue.                                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│               AUTO LANGUAGE DETECTION                           │
│                                                                 │
│   Uses `langdetect` library on the input text                   │
│   ISO code → mapped to Camb.AI language code                    │
│   e.g.  "en" → "en-us"  |  "fr" → "fr-fr"  |  "hi" → "hi-in"  │
│                                                                 │
│   Displayed to user as:  🌍 Detected: English (US) → en-us      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│            FETCH AVAILABLE VOICES FROM CAMB.AI                  │
│                                                                 │
│   GET https://client.camb.ai/apis/list-voices                   │
│   Header: x-api-key: <TTS_API_KEY>                              │
│                                                                 │
│   → Cached for 1 hour (st.cache_data)                           │
│   → Best voice matched to detected language                     │
│   → Falls back to voice_id 147320 if no match found             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              CALL CAMB.AI TTS STREAM API                        │
│                                                                 │
│   POST https://client.camb.ai/apis/tts-stream                   │
│                                                                 │
│   Payload:                                                      │
│   {                                                             │
│     "text":         <user text>,                                │
│     "voice_id":     <matched voice>,                            │
│     "language":     <camb language code>,                       │
│     "speech_model": "mars-pro",                                 │
│     "output_configuration": { "format": "wav" }                 │
│   }                                                             │
│                                                                 │
│        ❌ Error? → Show detailed error + debug info              │
│        ✅ Success? → Receive raw WAV bytes                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AUDIO OUTPUT                                 │
│                                                                 │
│   🔊 Play inline audio player in the browser                    │
│   ⬇️  Download button → audiobook_output.wav                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏢 About Camb.AI — The Company

**[Camb.AI](https://camb.ai)** (formerly known as CAMB.AI) is an **AI voice infrastructure company** founded by AI researchers from **Apple (ex-Siri team)** and **Carnegie Mellon University**. Their mission: make every voice count — helping the world's biggest enterprises reach **8 billion fans, customers, and viewers** in their own language.

### 📍 Company Highlights

| Fact | Detail |
|------|--------|
| **Founded** | 2022, San Francisco, CA |
| **Team Background** | Interspeech-published researchers, ex-Siri engineers, CMU alumni |
| **Core Technology** | MARS (speech) + BOLI (translation) proprietary models |
| **Languages Supported** | 140+ languages, covering 99% of the world's speaking population |
| **Users Reached** | 200+ million users through partner deployments |
| **Cloud Presence** | First & only voice AI provider on **AWS Bedrock** AND **Google Cloud Vertex AI** |

### 🏆 Major Milestones

- 🥇 **April 2024** — Became the **first company in the world** to live-translate a Major League Soccer game in real-time across multiple languages
- 🏎️ **NASCAR** — Powers live Spanish-language AI commentary for Motor Racing Network broadcasts
- 🎾 **Australian Open** — Live multilingual sports commentary
- 🎬 **IMAX & Comcast NBCU** — AI dubbing for global entertainment content
- ⚽ **Ligue 1 (2026)** — First European football match with live AI-powered Italian commentary at Trophée des Champions (PSG vs OM)
- 🏏 **FanCode** — Multilingual cricket coverage for 100+ million users
- 🔌 **Broadcom** — On-device TTS running directly on Broadcom SoCs (NPU-integrated chips)
- ☁️ **Google Cloud Vertex AI** — MARS is the only TTS model available on Vertex AI

### 🤝 Enterprise Partners

Comcast NBCUniversal · IMAX · Major League Soccer · NASCAR · Australian Open · FanCode · Eurovision Sport · Maple Leaf Sports & Entertainment · Broadcom · DXC Technology (automotive AI) · Google Cloud · AWS

---

## 🤖 The MARS Model Family

**MARS** stands for **Multilingual Autoregressive Speech** — Camb.AI's flagship family of Text-to-Speech models. The evolution has been rapid:

### The Journey: MARS5 → MARS6 → MARS7 → MARS8

| Version | Year | Key Achievement |
|---------|------|-----------------|
| **MARS5** | 2024 | Open-source, two-stage AR-NAR pipeline, voice cloning from 5 seconds of audio, released on GitHub & Hugging Face |
| **MARS6** | Late 2024 | First speech model on **AWS Bedrock**, enterprise-grade multilingual TTS |
| **MARS7** | 2025 | Deployed on **Google Cloud Vertex AI** for VPC, powered live NASCAR & Australian Open broadcasts |
| **MARS8** | Jan 2026 | First-ever **family** of specialized TTS architectures (Flash, Pro, Instruct, Nano) — ending the "one-size-fits-all" era |

### How MARS5 Was Built (Architecture)

MARS5 introduced a novel **two-stage AR-NAR pipeline**:

```
Input Text + Reference Audio (≥5 seconds)
            │
            ▼
┌───────────────────────────────────────┐
│  Stage 1: Autoregressive (AR) Model   │
│  ~750M parameters                     │
│  Generates coarse L0 encodec speech   │
│  features from text + reference       │
└──────────────────┬────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────┐
│  Stage 2: Non-Autoregressive (NAR)    │
│  ~450M parameters                     │
│  Multinomial DDPM (Diffusion Model)   │
│  Refines features → full audio codes  │
└──────────────────┬────────────────────┘
                   │
                   ▼
            Vocoder → Final 24kHz Audio
```

The model uses a **BPE (Byte-Pair Encoding) tokenizer** trained on raw audio, enabling prosodic control through punctuation and capitalization — e.g. commas introduce pauses, capital letters add emphasis.

### MARS8 — The Current Generation (2026)

MARS8 is the first TTS system designed not as a single model but as **four specialized architectures**:

| Model | Parameters | TTFB | Sample Rate | Best For |
|-------|-----------|------|-------------|----------|
| **mars-flash** | 600M | **~150ms** | 22.05kHz / 48kHz | Real-time agents, call centers, live chat |
| **mars-pro** | 600M | 800ms – 2s | **48kHz** | Audiobooks, dubbing, digital media, narration |
| **mars-instruct** | 1.2B | Higher | 22.05kHz | Film/TV production, director-level emotional control |
| **mars-nano** | 50M | 500ms – 2s | — | On-device, memory-constrained environments |

**Beta models (MARS 8.1):**
- `mars-8.1-flash-beta` — Faster generation with improved accent handling
- `mars-8.1-pro-beta` — Highest fidelity preview, better prosody and high-pitch voice expressiveness

> **"The market forces developers to choose between speed, quality, accuracy, and cost. We realized that was a false choice."**  
> — Akshat Prakash, CTO & Co-founder, Camb.AI

MARS8 launches with a **Compute-First pricing model** — customers run models on their own infrastructure (AWS, Google Cloud, Modal, Baseten, etc.), breaking free from per-character API pricing at scale.

### MARS-Instruct: Expressive Voice Control

`mars-instruct` supports **embedded emotion tags** directly in the text:

```
[speaking slowly] This is very important. Please pay close attention.
[excited] We shipped the feature, and the response has been fantastic!
Let's pause <break time="400ms"/> and continue.
```

---

## ⭐ Why MARS-Pro? Why Camb.AI?

This project specifically uses **`mars-pro`** as the speech model. Here's why:

### Why MARS-Pro for Audiobooks?

| Requirement | How MARS-Pro Delivers |
|-------------|----------------------|
| **Natural narration** | 48kHz high-fidelity audio, indistinguishable from human narrators |
| **Emotional delivery** | Balances fidelity and speed — optimized for expressive, long-form content |
| **Multilingual** | 30+ languages natively, same voice quality across all |
| **Speed** | 800ms–2s TTFB — fast enough for on-demand generation |
| **Audiobook use case** | Explicitly listed as a primary use case in official model docs |

### Why Camb.AI Over Other TTS Providers?

1. **Simplest API in the market** — A single `POST` request returns streaming WAV bytes. No complex setup, no audio pipeline to manage.
2. **No SDK required** — Pure HTTP calls with `requests`. Works in any Python environment without dependency issues.
3. **Production-proven** — The same models powering NASCAR, IMAX, and live sports broadcasts are available via free API keys for developers.
4. **Best multilingual coverage** — 140+ languages in a single model, not separate models per language.
5. **Automatic voice selection** — The `/list-voices` endpoint lets you dynamically fetch and match voices per language.
6. **Free tier available** — Get an API key, start building immediately.

---

## 🌍 Supported Languages

The app auto-detects and supports the following 30+ languages:

| Code | Language | Code | Language |
|------|----------|------|----------|
| `en-us` | English (US) | `hi-in` | Hindi (India) |
| `fr-fr` | French (France) | `es-es` | Spanish (Spain) |
| `de-de` | German | `ja-jp` | Japanese |
| `ar-xa` | Arabic (Modern Standard) | `ko-kr` | Korean |
| `zh-cn` | Chinese (Simplified) | `it-it` | Italian |
| `pt-br` | Portuguese (Brazil) | `id-id` | Indonesian |
| `nl-nl` | Dutch | `ru-ru` | Russian |
| `ta-in` | Tamil | `te-in` | Telugu |
| `bn-in` | Bengali (India) | `mr-in` | Marathi |
| `kn-in` | Kannada | `ml-in` | Malayalam |
| `pl-pl` | Polish | `tr-tr` | Turkish |
| `pa-in` | Punjabi | `fr-ca` | French (Canada) |
| `es-mx` | Spanish (Mexico) | `pt-pt` | Portuguese (Portugal) |
| `ar-sa` | Arabic (Saudi Arabia) | `ar-eg` | Arabic (Egypt) |
| `bn-bd` | Bengali (Bangladesh) | `as-in` | Assamese |

> The MARS model family collectively covers **99% of the world's speaking population**.

---

## 📁 Project Structure

```
CAMB-AI-AudioBook-Generator/
│
├── streamlit_app.py        # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── assets/
    └── screenshot.png      # App screenshot (optional)
```

---

## ⚙️ Features

### 🎯 Core Features

- **Dual Input Modes**
  - **Paste Text** — Type or paste any text directly into the text area
  - **Upload File** — Upload `.txt` or `.docx` files; text is auto-extracted

- **Auto Language Detection**
  - Uses the `langdetect` library to identify the language of your text
  - Automatically maps to the correct Camb.AI language code (e.g., `hi` → `hi-in`)
  - Displays the detected language to the user before generation

- **Dynamic Voice Selection**
  - Fetches real voice IDs from Camb.AI's `/list-voices` endpoint on every session
  - Matches the best available voice for the detected language
  - Falls back gracefully to a known working default voice (`147320`) if no match found
  - Voice list is cached for 1 hour to avoid redundant API calls

- **Audio Playback & Download**
  - Inline audio player directly in the browser
  - One-click download as `audiobook_output.wav`

### 🛡️ Safety & UX Features

- Live character and word counter while typing
- Hard limit enforced at 500 characters (matches free plan)
- Files exceeding the limit are auto-trimmed to 500 characters with a warning
- Detailed error messages when API calls fail, including debug info (voice_id, language, model used)
- API key status badge (green = loaded, red = missing)
- Generate button is disabled until both valid text and API key are present
- Example texts displayed as plain copyable blocks (no button state issues)

---

## 📏 Input Limits

| Limit | Value |
|-------|-------|
| Maximum Characters | **500** |
| Maximum Words | **~80 words** |
| Supported File Formats | `.txt`, `.docx` |
| Audio Format | `.wav` (48kHz) |
| Model Used | `mars-pro` |

> **Note:** The 500-character limit is enforced by the Camb.AI free plan. If you upgrade your Camb.AI plan, you can increase `MAX_CHARS` in `streamlit_app.py` accordingly.

---

## 🔧 How to Fork & Deploy Your Own Copy

Want to run your own instance of this app? It takes less than 5 minutes.

### Step 1: Fork / Clone the Repository

```bash
git clone https://github.com/SuccessNEERAJ/CAMB-AI-AudioBook-Generator.git
cd CAMB-AI-AudioBook-Generator
```

Or click **Fork** on GitHub to create your own copy under your account.

### Step 2: Get Your Camb.AI API Key

See the [next section](#-getting-your-cambai-api-key) for detailed instructions.

### Step 3: Deploy on Streamlit Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub
2. Click **"New app"**
3. Select your forked repository
4. Set the **Main file path** to `streamlit_app.py`
5. Click **"Advanced settings"** → **"Secrets"**
6. Add your API key in the Secrets section:

```toml
TTS_API_KEY = "your_actual_camb_ai_api_key_here"
```

7. Click **"Deploy!"**

That's it. Your own instance will be live at:
`https://your-app-name.streamlit.app`

### Step 4 (Optional): Increase the Character Limit

If you have a paid Camb.AI plan with a higher character limit, open `streamlit_app.py` and update these two constants:

```python
MAX_CHARS = 500    # ← change to your plan's limit, e.g. 4000
MAX_WORDS = 80     # ← update proportionally, e.g. 500
```

---

## 🔑 Getting Your Camb.AI API Key

1. Visit **[studio.camb.ai](https://studio.camb.ai)** and create a free account
2. Once logged in, navigate to **Settings → API Keys**
3. Click **"Create new API key"**
4. Copy the key (you'll only see it once — save it securely)
5. Paste it into your Streamlit Cloud Secrets as `TTS_API_KEY`

> **Free tier includes:** 500 characters per request. Sufficient for short narrations and testing. Upgrade at [camb.ai/pricing](https://camb.ai) for higher limits.

---

## 🧠 How the Code Works

The entire app is a single file (`streamlit_app.py`) with no SDK dependencies — just raw HTTP calls. Here's how the key pieces fit together:

### 1. API Key Loading

```python
def get_api_key():
    try:
        return st.secrets["TTS_API_KEY"]      # Streamlit Cloud Secrets
    except Exception:
        return os.environ.get("TTS_API_KEY")  # Local env variable fallback
```

### 2. Language Detection

```python
from langdetect import detect
raw_code = detect(text)           # e.g. "fr"
camb_code = LANG_TO_CAMB[raw_code]  # e.g. "fr-fr"
```

### 3. Dynamic Voice Fetching

```python
@st.cache_data(ttl=3600)          # Cache for 1 hour
def fetch_voices(api_key):
    resp = requests.get("https://client.camb.ai/apis/list-voices",
                        headers={"x-api-key": api_key})
    return resp.json()
```

### 4. TTS API Call

```python
payload = {
    "text": text,
    "voice_id": voice_id,          # Dynamically resolved
    "language": camb_language,     # Auto-detected
    "speech_model": "mars-pro",
    "output_configuration": {"format": "wav"}
}
resp = requests.post("https://client.camb.ai/apis/tts-stream",
                     headers={"x-api-key": api_key, "Content-Type": "application/json"},
                     json=payload)
audio_bytes = resp.content         # Raw WAV bytes, ready to play/download
```

### 5. Audio Output

```python
st.audio(audio_bytes, format="audio/wav")       # Inline player
st.download_button("⬇️ Download", audio_bytes,  # Download button
                   file_name="audiobook_output.wav",
                   mime="audio/wav")
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Frontend & App Framework** | [Streamlit](https://streamlit.io) |
| **TTS Model** | Camb.AI MARS-Pro (48kHz) |
| **API Communication** | Python `requests` (direct HTTP, no SDK) |
| **Language Detection** | `langdetect` |
| **DOCX Parsing** | `python-docx` |
| **Deployment** | Streamlit Community Cloud |
| **Audio Format** | WAV (PCM, 48kHz) |

### Python Dependencies (`requirements.txt`)

```
streamlit>=1.35.0
requests>=2.31.0
langdetect>=1.0.9
python-docx>=1.1.0
```

---

## ⚠️ Important Notes

- **Character Limit:** The free Camb.AI plan allows **500 characters per API request**. Upgrade your plan at [camb.ai](https://camb.ai) for higher limits.
- **Privacy:** Your text is sent to the Camb.AI API servers for processing. Do not input sensitive or private information.
- **Rate Limits:** Please use the app responsibly to stay within Camb.AI's rate limits.
- **Audio Storage:** Audio files are generated on-demand and are not stored anywhere. Download your file if you want to keep it.
- **Language Detection:** Detection accuracy is best for longer text snippets. Very short inputs (under 20 characters) may default to English if detection is ambiguous.
- **Voice Availability:** The available voices depend on your Camb.AI account and plan. The app dynamically fetches real voice IDs — no hardcoded fake IDs.

---

## 📜 License

```
MIT License

Copyright (c) 2025 SuccessNEERAJ

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<div align="center">

**Built with ❤️ by [SuccessNEERAJ](https://github.com/SuccessNEERAJ)**

Powered by [Camb.AI MARS-Pro](https://camb.ai) · Deployed on [Streamlit Cloud](https://streamlit.io)

⭐ **If you found this useful, please star the repository!** ⭐

[![GitHub stars](https://img.shields.io/github/stars/SuccessNEERAJ/CAMB-AI-AudioBook-Generator?style=social)](https://github.com/SuccessNEERAJ/CAMB-AI-AudioBook-Generator)

</div>
