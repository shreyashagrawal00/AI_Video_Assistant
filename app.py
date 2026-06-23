import streamlit as st
import time
from dotenv import load_dotenv

# Load env variables before importing local modules
load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Syne:wght@600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

:root {
    --bg: #03000a;
    --bg-gradient: radial-gradient(circle at 50% 50%, #0c051a 0%, #03000a 100%);
    --surface: rgba(17, 12, 28, 0.65);
    --surface-border: rgba(139, 92, 246, 0.15);
    --surface-hover: rgba(17, 12, 28, 0.85);
    --border-hover: rgba(139, 92, 246, 0.4);
    --accent: #8b5cf6;
    --accent-gradient: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%);
    --accent-glow: #a78bfa;
    --accent-2: #06b6d4;
    --text: #f3f4f6;
    --text-muted: #9ca3af;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
}

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    background-color: var(--bg) !important;
    background: var(--bg-gradient) !important;
    color: var(--text) !important;
}

.stApp {
    background: var(--bg-gradient) !important;
}

/* Background Glowing Orbs */
.stApp::before {
    content: '';
    position: fixed;
    top: -10%; left: -10%;
    width: 50%; height: 50%;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.08) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}
.stApp::after {
    content: '';
    position: fixed;
    bottom: -10%; right: -10%;
    width: 50%; height: 50%;
    background: radial-gradient(circle, rgba(6, 182, 212, 0.06) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: rgba(9, 6, 16, 0.95) !important;
    border-right: 1px solid var(--surface-border) !important;
    backdrop-filter: blur(20px);
    color: var(--text);
}
[data-testid="stSidebar"] .stMarkdown, 
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] h5,
[data-testid="stSidebar"] h6 {
    color: var(--text) !important;
}
div[data-testid="stRadio"] label p {
    color: var(--text) !important;
    font-size: 0.85rem !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] {
    background: rgba(17, 12, 28, 0.4) !important;
    border: 1px solid var(--surface-border) !important;
    border-radius: 10px !important;
    padding: 0.5rem 0.75rem !important;
    gap: 1rem;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    color: var(--text) !important;
}

.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2rem, 5vw, 3.2rem);
    font-weight: 800;
    line-height: 1.1;
    margin: 0;
    background: linear-gradient(135deg, #ffffff 10%, #a78bfa 50%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: 0 0 40px rgba(139, 92, 246, 0.15);
}

.hero-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--text-muted);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 0.5rem;
}

/* Premium Card Design with Glassmorphism */
.card {
    background: var(--surface);
    border: 1px solid var(--surface-border);
    border-radius: 16px;
    padding: 1.75rem;
    margin-bottom: 1.25rem;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.card:hover {
    transform: translateY(-4px);
    border-color: var(--border-hover);
    box-shadow: 0 10px 40px rgba(139, 92, 246, 0.15);
}
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: var(--accent-gradient);
}
.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--accent-glow);
    margin-bottom: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.card-content {
    font-size: 0.9rem;
    line-height: 1.7;
    color: #e5e7eb;
}

/* Onboarding Card specificity */
.onboarding-card {
    background: rgba(17, 12, 28, 0.45) !important;
}
.onboarding-card::before {
    display: none;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 0.3rem 0.75rem;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    backdrop-filter: blur(5px);
}
.badge-purple { background: rgba(139, 92, 246, 0.12); color: var(--accent-glow); border: 1px solid rgba(139, 92, 246, 0.25); }
.badge-cyan   { background: rgba(6, 182, 212, 0.12); color: var(--accent-2); border: 1px solid rgba(6, 182, 212, 0.25); }
.badge-green  { background: rgba(16, 185, 129, 0.12); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.25); }

/* Inputs and Selectors */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: rgba(17, 12, 28, 0.6) !important;
    border: 1px solid var(--surface-border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 0.75rem !important;
    transition: all 0.2s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2) !important;
}

/* Action Button */
.stButton > button {
    background: var(--accent-gradient) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.75rem 1.5rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    text-transform: uppercase !important;
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.2) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.45) !important;
}

/* Secondary Button override */
.stButton > button[kind="secondary"] {
    background: rgba(17, 12, 28, 0.8) !important;
    border: 1px solid var(--surface-border) !important;
    color: var(--text) !important;
    box-shadow: none !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--accent) !important;
}

/* Status Bar */
.status-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.8rem 1.1rem;
    background: rgba(17, 12, 28, 0.7);
    border-radius: 10px;
    margin: 0.5rem 0;
    border: 1px solid var(--surface-border);
    font-size: 0.85rem;
    backdrop-filter: blur(10px);
}
.status-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}
.dot-active   { background: var(--accent-2); box-shadow: 0 0 10px var(--accent-2); animation: pulse 1.5s infinite; }
.dot-done     { background: var(--success); box-shadow: 0 0 6px var(--success); }
.dot-pending  { background: rgba(255, 255, 255, 0.1); }

/* Chat Layout */
.chat-container {
    background: rgba(17, 12, 28, 0.4);
    border: 1px solid var(--surface-border);
    border-radius: 16px;
    padding: 1.5rem;
    max-height: 480px;
    overflow-y: auto;
    margin-bottom: 1.25rem;
    backdrop-filter: blur(10px);
}
.chat-msg {
    margin-bottom: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}
.chat-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-left: 0.5rem;
    margin-right: 0.5rem;
}
.chat-bubble {
    display: inline-block;
    padding: 0.8rem 1.25rem;
    border-radius: 14px;
    font-size: 0.9rem;
    line-height: 1.6;
    max-width: 85%;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
}
.user-label  { color: var(--accent-glow); }
.bot-label   { color: var(--accent-2); }

.user-bubble {
    background: rgba(139, 92, 246, 0.18) !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    align-self: flex-end;
    border-bottom-right-radius: 2px;
}
.bot-bubble  {
    background: rgba(17, 12, 28, 0.75) !important;
    border: 1px solid rgba(6, 182, 212, 0.15) !important;
    align-self: flex-start;
    border-top-left-radius: 2px;
}

/* Transcript Box */
.transcript-box {
    background: rgba(9, 6, 16, 0.6);
    border: 1px solid var(--surface-border);
    border-radius: 12px;
    padding: 1.5rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    line-height: 1.8;
    max-height: 350px;
    overflow-y: auto;
    color: var(--text-muted);
    white-space: pre-wrap;
    word-break: break-word;
}

/* Moving Background Glow Orbs */
@keyframes floatOrb1 {
    0% { transform: translate(0px, 0px) scale(1); }
    50% { transform: translate(30px, -50px) scale(1.2); }
    100% { transform: translate(0px, 0px) scale(1); }
}
@keyframes floatOrb2 {
    0% { transform: translate(0px, 0px) scale(1); }
    50% { transform: translate(-30px, 50px) scale(0.8); }
    100% { transform: translate(0px, 0px) scale(1); }
}
.stApp::before {
    animation: floatOrb1 20s infinite ease-in-out;
}
.stApp::after {
    animation: floatOrb2 25s infinite ease-in-out;
}

/* Pulsing Status Dot */
@keyframes pulse {
    0% {
        transform: scale(0.9);
        box-shadow: 0 0 0 0 rgba(6, 182, 212, 0.7);
    }
    70% {
        transform: scale(1.1);
        box-shadow: 0 0 0 10px rgba(6, 182, 212, 0);
    }
    100% {
        transform: scale(0.9);
        box-shadow: 0 0 0 0 rgba(6, 182, 212, 0);
    }
}

/* Premium Scrollbars */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: rgba(17, 12, 28, 0.2);
}
::-webkit-scrollbar-thumb {
    background: rgba(139, 92, 246, 0.35);
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(139, 92, 246, 0.6);
}

/* Premium File Uploader Overrides */
div[data-testid="stFileUploader"] {
    background: rgba(17, 12, 28, 0.4) !important;
    border: 1px dashed rgba(139, 92, 246, 0.25) !important;
    border-radius: 14px !important;
    padding: 1.5rem !important;
    transition: all 0.3s ease;
}
div[data-testid="stFileUploader"]:hover {
    border-color: rgba(139, 92, 246, 0.6) !important;
    background: rgba(17, 12, 28, 0.5) !important;
}
div[data-testid="stFileUploader"] section {
    background: transparent !important;
    border: none !important;
}
div[data-testid="stFileUploader"] section button {
    background: rgba(139, 92, 246, 0.15) !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
}
div[data-testid="stFileUploader"] section button:hover {
    background: rgba(139, 92, 246, 0.35) !important;
    border-color: var(--accent) !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Demo RAG Chain Helper ──────────────────────────────────────────────────────
class DemoRagChain:
    def invoke(self, question: str) -> str:
        q = question.lower()
        if "action" in q or "task" in q:
            return "According to the transcript, the action items are:\\n1. **Akarsh Vyas** to implement the premium glassmorphic UI stylesheet and layout design (Deadline: Tomorrow).\\n2. **Shreya** to focus on the backend pipeline, setting up Mistral API keys, and integrating ChromaDB (Deadline: Friday).\\n3. **All** to meet on Thursday for a status sync."
        elif "decision" in q:
            return "The team decided to use **Python and Streamlit** for the frontend with custom HTML/CSS overrides, and **LangChain with Mistral AI** for LLM orchestration. They also agreed to use **ChromaDB** locally as the vector database."
        elif "role" in q or "who" in q:
            return "In this meeting:\\n- **Akarsh Vyas** is responsible for UI styling and layout design.\\n- **Shreya** is responsible for the backend integration, including Mistral API and ChromaDB."
        elif "timeline" in q or "deadline" in q or "friday" in q:
            return "The UI design needs to be finished by tomorrow, and the fully integrated backend pipeline is scheduled to be completed by Friday."
        elif "whisper" in q:
            return "The team selected **OpenAI Whisper** (specifically the 'small' model running locally) for transcribing English audio chunks."
        elif "sarvam" in q or "hinglish" in q:
            return "**Sarvam AI's** STT-translate API was selected to transcribe Hinglish audio and automatically translate it to English."
        else:
            return "This is an offline demo RAG chain. The kickoff meeting covered system architecture and roles for the AI Video Assistant project. You can ask me about task owners (Akarsh or Shreya), technologies (Streamlit, LangChain, Mistral, ChromaDB, Whisper, Sarvam), or deadlines!"

# ─── Session State Init ──────────────────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Helpers ────────────────────────────────────────────────────────────────────
def step_status(steps: dict, key: str) -> str:
    s = steps.get(key, "pending")
    if s == "active":  return "dot-active"
    if s == "done":    return "dot-done"
    return "dot-pending"

def render_step_bar(label: str, key: str, icon: str):
    css = step_status(st.session_state.pipeline_steps, key)
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-dot {css}"></div>
        <span>{icon} {label}</span>
    </div>""", unsafe_allow_html=True)

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="hero-title" style="font-size:1.6rem">🎬 AI<br>Video</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Meeting Intelligence</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<span class="badge badge-purple">Input</span>', unsafe_allow_html=True)
    input_type = st.radio("Input Source Type", ["YouTube URL / Local Path", "Upload File"], index=0)

    source = ""
    uploaded_file = None
    if input_type == "YouTube URL / Local Path":
        source = st.text_input("YouTube URL or File Path", placeholder="https://youtube.com/watch?v=... or /path/to/file.mp4")
    else:
        uploaded_file = st.file_uploader("Upload Video or Audio File", type=["mp4", "mkv", "avi", "mov", "mp3", "wav", "m4a"])

    st.markdown('<span class="badge badge-cyan" style="margin-top: 1rem; display: inline-block;">Language</span>', unsafe_allow_html=True)
    language = st.radio("Choose transcription language", ["english", "hinglish"], index=0, horizontal=True, label_visibility="collapsed")

    run_btn = st.button("⚡  Analyse", use_container_width=True)

    sidebar_status_placeholder = st.empty()

def render_sidebar_status():
    if st.session_state.pipeline_done or st.session_state.pipeline_steps:
        with sidebar_status_placeholder.container():
            st.markdown("---")
            st.markdown('<span class="badge badge-green">Pipeline Status</span>', unsafe_allow_html=True)
            for step, icon, label in [
                ("audio",      "🔊", "Audio Processing"),
                ("transcript", "📝", "Transcription"),
                ("title",      "🏷️", "Title Generation"),
                ("summary",    "📋", "Summarisation"),
                ("extract",    "🔍", "Extraction"),
                ("rag",        "🧠", "RAG Engine"),
            ]:
                render_step_bar(label, step, icon)

render_sidebar_status()

# ─── Main Area ──────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">AI Video Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Transcribe · Summarise · Chat with your meetings</div>', unsafe_allow_html=True)
st.markdown("---")

# ── Run Pipeline ────────────────────────────────────────────────────────────────
if run_btn:
    source_path = ""
    if input_type == "YouTube URL / Local Path":
        if source and source.strip():
            source_path = source.strip()
    else:
        if uploaded_file is not None:
            import os
            os.makedirs("downloads", exist_ok=True)
            source_path = os.path.join("downloads", uploaded_file.name)
            with open(source_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

    if not source_path:
        if input_type == "YouTube URL / Local Path":
            st.error("Please enter a YouTube URL or file path.")
        else:
            st.error("Please upload a video or audio file.")
    else:
        st.session_state.pipeline_done = False
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pipeline_steps = {}

        progress_placeholder = st.empty()

        def update_step(key, state):
            st.session_state.pipeline_steps[key] = state
            render_sidebar_status()

        try:
            with progress_placeholder.container():
                st.info("⚙️ Pipeline running — see sidebar for live status…")

            update_step("audio", "active")
            chunks = process_input(source_path)
            update_step("audio", "done")

            update_step("transcript", "active")
            transcription_res = transcribe_all(chunks, language)
            transcript = transcription_res["text"]
            update_step("transcript", "done")

            update_step("title", "active")
            title = generate_title(transcript)
            update_step("title", "done")

            update_step("summary", "active")
            summary = summarize(transcript)
            update_step("summary", "done")

            update_step("extract", "active")
            action_items  = extract_action_items(transcript)
            decisions     = extract_key_decisions(transcript)
            questions     = extract_questions(transcript)
            update_step("extract", "done")

            update_step("rag", "active")
            rag_chain = build_rag_chain(transcript)
            update_step("rag", "done")

            st.session_state.result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "rag_chain": rag_chain,
            }
            st.session_state.pipeline_done = True
            progress_placeholder.success("✅ Analysis complete!")
            time.sleep(0.5)
            progress_placeholder.empty()
            st.rerun()

        except Exception as e:
            for k in ["audio","transcript","title","summary","extract","rag"]:
                if st.session_state.pipeline_steps.get(k) == "active":
                    st.session_state.pipeline_steps[k] = "pending"
            progress_placeholder.error(f"❌ Error: {e}")

# ── Results ──────────────────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result

    # Title banner
    st.markdown(f"""
    <div class="card">
        <div class="card-title">📌 Session Title</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:700;color:var(--text)">
            {r['title']}
        </div>
    </div>""", unsafe_allow_html=True)

    # Top row: summary + transcript
    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">📋 Summary</div>
            <div class="card-content">{r['summary']}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        with st.expander("📝 Full Transcript", expanded=False):
            st.markdown(f'<div class="transcript-box">{r["transcript"]}</div>', unsafe_allow_html=True)

    # Second row: action items | decisions | questions
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">✅ Action Items</div>
            <div class="card-content">{r['action_items']}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">🔑 Key Decisions</div>
            <div class="card-content">{r['key_decisions']}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">❓ Open Questions</div>
            <div class="card-content">{r['open_questions']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── RAG Chat ──────────────────────────────────────────────────────────────
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.2rem;font-weight:700;margin-bottom:1rem">💬 Chat with your Meeting</div>', unsafe_allow_html=True)

    # Chat history display
    if st.session_state.chat_history:
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-end">
                    <span class="chat-label user-label">You</span>
                    <div class="chat-bubble user-bubble">{msg['content']}</div>
                </div>"""
            else:
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-start">
                    <span class="chat-label bot-label">🤖 Assistant</span>
                    <div class="chat-bubble bot-bubble">{msg['content']}</div>
                </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2rem">
            <div style="font-size:2rem;margin-bottom:0.5rem">💬</div>
            <div style="color:var(--text-muted);font-size:0.85rem">Ask anything about your meeting transcript</div>
        </div>""", unsafe_allow_html=True)

    # Chat input
    chat_col1, chat_col2 = st.columns([5, 1], gap="small")
    with chat_col1:
        user_input = st.text_input("Your question", placeholder="What were the main decisions made?", label_visibility="collapsed")
    with chat_col2:
        send_btn = st.button("Send →", use_container_width=True)

    if send_btn and user_input.strip():
        with st.spinner("Thinking…"):
            answer = ask_question(r["rag_chain"], user_input.strip())
        st.session_state.chat_history.append({"role": "user",      "content": user_input.strip()})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

else:
    # Onboarding screen with option to load demo session
    st.markdown("""
    <div class="card onboarding-card" style="text-align: center; max-width: 700px; margin: 3rem auto; padding: 3.5rem 2.5rem;">
        <div style="font-size: 4.5rem; margin-bottom: 1.5rem; filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.45));">🎬</div>
        <h2 style="font-family:'Syne', sans-serif; font-weight:800; font-size:2.2rem; margin-bottom:0.75rem; background: linear-gradient(135deg, #ffffff, #a78bfa, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            AI Video Assistant
        </h2>
        <p style="color:var(--text-muted); font-size:0.95rem; line-height:1.75; margin-bottom:2rem;">
            A premium workspace to transcribe, summarize, and query your meeting recordings. Upload a video/audio file or paste a YouTube URL to get started, or immediately load our pre-configured demo session to see the assistant in action.
        </p>
        <div style="display:flex; justify-content:center; gap:1.25rem; margin-bottom:1.5rem; flex-wrap:wrap;">
            <span class="badge badge-purple">🔊 Audio Processing</span>
            <span class="badge badge-cyan">📝 Transcription</span>
            <span class="badge badge-green">🧠 RAG Chat</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_btn, col_r = st.columns([1.5, 2, 1.5])
    with col_btn:
        if st.button("⚡ Load Demo Session", use_container_width=True):
            st.session_state.result = {
                "title": "🎬 AI Video Assistant - Demo Project Kickoff",
                "transcript": (
                    "Akarsh Vyas: Welcome everyone to the AI Video Assistant kickoff meeting. Today we are designing the architecture and the user interface. We need to decide on our technology stack and layout design.\n\n"
                    "Shreya: Yes, for the tech stack, we will use Python and Streamlit on the frontend, and LangChain with Mistral AI for orchestration. We will run ChromaDB locally as our vector database and HuggingFace for generating embeddings. For local transcription, we'll use OpenAI Whisper.\n\n"
                    "Akarsh Vyas: Perfect. Let's make sure our UI is highly aesthetic and glassmorphic, with deep violet and neon cyan gradients. I will take ownership of implementing the stylesheet and layouts by tomorrow.\n\n"
                    "Shreya: Great, I will focus on the backend pipeline, setting up Mistral API keys, and integrating ChromaDB. Let's aim to have the first integrated demo ready by Friday.\n\n"
                    "Akarsh Vyas: Sounds like a plan. Let's meet again on Thursday to sync."
                ),
                "summary": (
                    "<ul>"
                    "<li><strong>Kickoff Meeting:</strong> The team initiated the AI Video Assistant project, aligning on the system architecture and UI goals.</li>"
                    "<li><strong>Technology Stack:</strong> Agreed to use Python and Streamlit, powered by LangChain and Mistral AI, with ChromaDB for local vector storage.</li>"
                    "<li><strong>UI/UX Design:</strong> Decided on a premium glassmorphic dark-theme UI with deep purple/cyan gradients and subtle neon hover scales.</li>"
                    "<li><strong>Roles & Milestones:</strong> Akarsh Vyas will handle the UI styling (by tomorrow), while Shreya integrates the backend pipeline (by Friday).</li>"
                    "</ul>"
                ),
                "action_items": (
                    "1. 🎨 <strong>UI Stylesheet Implementation</strong><br>Owner: Akarsh Vyas | Deadline: Tomorrow<br><br>"
                    "2. ⚙️ <strong>Backend & RAG Pipeline Integration</strong><br>Owner: Shreya | Deadline: Friday<br><br>"
                    "3. 📅 <strong>Thursday Status Sync</strong><br>Owner: All | Deadline: Thursday"
                ),
                "key_decisions": (
                    "1. <strong>Frontend Framework:</strong> Chosen Streamlit for fast prototyping combined with custom HTML/CSS overrides.<br><br>"
                    "2. <strong>Core LLM Orchestration:</strong> Selected LangChain with Mistral AI for summarization, extracting items, and RAG.<br><br>"
                    "3. <strong>Local DB:</strong> Selected ChromaDB for embedding storage and similarity retrieval."
                ),
                "open_questions": (
                    "1. Do we need to support multi-language translation beyond Hinglish in Phase 2?<br><br>"
                    "2. Should we support cloud vector stores if data size scales up?"
                ),
                "rag_chain": DemoRagChain(),
            }
            st.session_state.pipeline_done = True
            st.session_state.pipeline_steps = {
                "audio": "done",
                "transcript": "done",
                "title": "done",
                "summary": "done",
                "extract": "done",
                "rag": "done"
            }
            st.rerun()