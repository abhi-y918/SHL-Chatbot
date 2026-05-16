"""
SHL Assessment Recommender — Streamlit Chat UI
Run: uv run streamlit run streamlit_app.py
"""

import streamlit as st
import httpx

# API_BASE = "http://localhost:8000"
API_BASE = "https://shl.abhinav-yadav.me"

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="SHL Assessment Recommender",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS — ChatGPT-like light theme with SHL brand greens ─
st.markdown("""
<style>
/* ── Import Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Global ── */
html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background-color: #FFFFFF;
}
header[data-testid="stHeader"] {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E5E7EB;
}

/* ── Hide Streamlit defaults ── */
#MainMenu, footer, .stDeployButton { display: none !important; }

/* ── Top bar / logo ── */
.shl-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 0 12px 0;
    border-bottom: 2px solid #E5E7EB;
    margin-bottom: 8px;
}
.shl-logo {
    font-size: 32px;
    font-weight: 700;
    color: #4B8B3B;
    letter-spacing: -1px;
}
.shl-logo span {
    color: #8DC63F;
}
.shl-title {
    font-size: 15px;
    font-weight: 500;
    color: #6B7280;
    line-height: 1.3;
}

/* ── Chat container ── */
.chat-container {
    max-width: 780px;
    margin: 0 auto;
    padding-bottom: 140px;
}

/* ── Messages ── */
.msg-row {
    display: flex;
    gap: 12px;
    margin: 16px 0;
    align-items: flex-start;
}
.msg-row.user { justify-content: flex-end; }
.msg-row.assistant { justify-content: flex-start; }

.avatar {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    font-weight: 600;
    flex-shrink: 0;
}
.avatar.user-av   { background: #E8F5E9; color: #2E7D32; }
.avatar.bot-av    { background: #4B8B3B; color: #FFFFFF; }

.bubble {
    max-width: 72%;
    padding: 12px 18px;
    border-radius: 18px;
    font-size: 14.5px;
    line-height: 1.6;
    color: #1F2937;
    word-wrap: break-word;
}
.bubble.user-bubble {
    background: #F3F4F6;
    border-bottom-right-radius: 4px;
}
.bubble.bot-bubble {
    background: #F0FAF0;
    border: 1px solid #D5E8D5;
    border-bottom-left-radius: 4px;
}

/* ── Recommendation cards ── */
.rec-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
    margin-top: 12px;
}
.rec-card {
    background: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 10px;
    padding: 12px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.rec-card:hover {
    border-color: #4B8B3B;
    box-shadow: 0 2px 8px rgba(75,139,59,0.10);
}
.rec-name {
    font-weight: 600;
    font-size: 14px;
    color: #1F2937;
}
.rec-type {
    display: inline-block;
    background: #E8F5E9;
    color: #2E7D32;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 12px;
    margin-left: 10px;
}
.rec-link {
    color: #4B8B3B;
    font-size: 13px;
    font-weight: 500;
    text-decoration: none;
}
.rec-link:hover { text-decoration: underline; }

/* ── End-of-conversation banner ── */
.eoc-banner {
    text-align: center;
    margin: 18px 0;
    padding: 10px 20px;
    background: #F0FAF0;
    border: 1px solid #B8E0B8;
    border-radius: 10px;
    color: #2E7D32;
    font-size: 13px;
    font-weight: 500;
}

/* ── Input area ── */
.stChatInput > div {
    border: 1.5px solid #D1D5DB !important;
    border-radius: 14px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}
.stChatInput > div:focus-within {
    border-color: #4B8B3B !important;
    box-shadow: 0 0 0 2px rgba(75,139,59,0.12) !important;
}

/* ── Typing indicator ── */
.typing-dot {
    display: inline-block;
    width: 8px; height: 8px;
    margin: 0 2px;
    border-radius: 50%;
    background: #4B8B3B;
    animation: blink 1.4s infinite both;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink {
    0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
    40% { opacity: 1; transform: scale(1); }
}

/* ── Welcome screen ── */
.welcome {
    text-align: center;
    padding: 80px 20px 40px;
}
.welcome h1 {
    font-size: 28px;
    font-weight: 700;
    color: #1F2937;
    margin-bottom: 8px;
}
.welcome p {
    font-size: 15px;
    color: #6B7280;
    max-width: 500px;
    margin: 0 auto 32px;
    line-height: 1.6;
}
.prompt-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
    max-width: 600px;
    margin: 0 auto;
}
.chip {
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 10px 18px;
    font-size: 13px;
    color: #374151;
    cursor: pointer;
    transition: all 0.2s;
}
.chip:hover {
    border-color: #4B8B3B;
    background: #F0FAF0;
    color: #2E7D32;
}
</style>
""", unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────
st.markdown("""
<div class="shl-header">
    <div class="shl-logo">SHL<span>.</span></div>
    <div class="shl-title">Assessment Recommender<br>
        <span style="font-size:12px;color:#9CA3AF;">Powered by AI</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ended" not in st.session_state:
    st.session_state.ended = False


# ── API call ───────────────────────────────────────────────────
def call_chat_api(messages: list[dict]) -> dict:
    """Send messages to the backend and return the response."""
    payload = {"messages": messages}
    try:
        resp = httpx.post(f"{API_BASE}/chat", json=payload, timeout=30.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {
            "reply": f"⚠️ Could not reach the API: {e}",
            "recommendations": [],
            "end_of_conversation": False,
        }


# ── Render a single message ───────────────────────────────────
def render_message(role: str, content: str, recommendations: list | None = None):
    """Render a chat bubble with optional recommendation cards."""
    if role == "user":
        st.markdown(f"""
        <div class="msg-row user">
            <div class="bubble user-bubble">{content}</div>
            <div class="avatar user-av">U</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="msg-row assistant">
            <div class="avatar bot-av">S</div>
            <div class="bubble bot-bubble">{content}""" +
            _render_recs(recommendations or []) +
            """</div>
        </div>
        """, unsafe_allow_html=True)


def _render_recs(recs: list) -> str:
    """Build HTML for recommendation cards."""
    if not recs:
        return ""
    cards = ""
    for r in recs:
        name = r.get("name", "")
        url = r.get("url", "#")
        ttype = r.get("test_type", "")
        cards += f"""
        <div class="rec-card">
            <div>
                <span class="rec-name">{name}</span>
                <span class="rec-type">{ttype}</span>
            </div>
            <a class="rec-link" href="{url}" target="_blank">View →</a>
        </div>"""
    return f'<div class="rec-grid">{cards}</div>'


# ── Welcome screen (empty state) ──────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome">
        <h1>👋 How can I help you today?</h1>
        <p>I'm your SHL Assessment Recommendation Agent. Describe a role you're
        hiring for, and I'll find the right assessments from the SHL catalog.</p>
    </div>
    """, unsafe_allow_html=True)

    # Quick-start chips
    cols = st.columns(2)
    starters = [
        "I'm hiring a Java developer",
        "Need assessments for senior leadership",
        "Screening 500 contact centre agents",
        "What coding simulations do you have?",
    ]
    for i, txt in enumerate(starters):
        if cols[i % 2].button(txt, key=f"chip_{i}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": txt})
            st.rerun()


# ── Render conversation history ────────────────────────────────
for msg in st.session_state.messages:
    render_message(
        msg["role"],
        msg["content"],
        msg.get("recommendations"),
    )

# ── End-of-conversation banner ─────────────────────────────────
if st.session_state.ended:
    st.markdown(
        '<div class="eoc-banner">✅ Conversation complete. '
        'Click "New Chat" to start over.</div>',
        unsafe_allow_html=True,
    )
    if st.button("🔄 New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.ended = False
        st.rerun()


# ── Chat input ─────────────────────────────────────────────────
if not st.session_state.ended:
    if user_input := st.chat_input("Describe the role you're hiring for…"):
        # Append user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Show user bubble immediately
        render_message("user", user_input)

        # Show typing indicator
        with st.spinner(""):
            st.markdown("""
            <div class="msg-row assistant">
                <div class="avatar bot-av">S</div>
                <div class="bubble bot-bubble">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Call API
            api_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
            result = call_chat_api(api_messages)

        # Append assistant response
        assistant_msg = {
            "role": "assistant",
            "content": result.get("reply", ""),
            "recommendations": result.get("recommendations", []),
        }
        st.session_state.messages.append(assistant_msg)

        if result.get("end_of_conversation"):
            st.session_state.ended = True

        st.rerun()
