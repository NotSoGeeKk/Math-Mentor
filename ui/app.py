"""
Math Mentor — Streamlit UI
--------------------------
Run with: streamlit run ui/app.py
"""
from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from ui.components import (
    render_extraction_preview,
    render_agent_trace,
    render_rag_panel,
    render_answer_card,
    render_hitl_panel,
    render_feedback_row,
)
from tools.ocr import extract_from_bytes
from tools.asr import transcribe_bytes
from agents.graph import run_graph
from memory.store import save_attempt

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Math Mentor", page_icon="🧮", layout="wide")

# ── Custom CSS for a cleaner look ────────────────────────────────────────────
st.markdown("""
<style>
    /* tighter top padding */
    .block-container { padding-top: 2rem; }

    /* hero header */
    .hero h1 { margin-bottom: 0; }
    .hero p  { color: #888; margin-top: 0; }

    /* tab content area min-height so it doesn't jump */
    .stTabs [data-baseweb="tab-panel"] { min-height: 180px; }

    /* answer box */
    .answer-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
        border: 1px solid #bbf7d0;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
    .answer-box h2 { margin: 0 0 0.3rem 0; font-size: 1.5rem; }
    .answer-box .final { font-size: 1.25rem; font-weight: 600; color: #15803d; }

    /* confidence pill */
    .conf-pill {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .conf-high   { background: #dcfce7; color: #166534; }
    .conf-medium { background: #fef9c3; color: #854d0e; }
    .conf-low    { background: #fee2e2; color: #991b1b; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown('<div class="hero">', unsafe_allow_html=True)
st.markdown("# 🧮 Math Mentor")
st.markdown("Solve JEE-level math problems instantly — type, snap, or speak your question.")
st.markdown('</div>', unsafe_allow_html=True)

# ── Sidebar — settings only ─────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    conf_threshold = st.slider("HITL confidence threshold", 0.5, 1.0, 0.7, 0.05,
                               help="Below this confidence the system asks for human review")
    st.divider()
    st.caption("Powered by Google Gemini + RAG + LangGraph")
    st.caption("12 knowledge base docs · 5 agents · memory layer")

# ── Input tabs — front and center ────────────────────────────────────────────
text_tab, image_tab, audio_tab = st.tabs(["✏️  Type a Question", "🖼️  Upload Image", "🎤  Audio Input"])

raw_text: str = ""
input_type: str = "text"
needs_extraction_preview = False

with text_tab:
    raw_text_typed = st.text_area(
        "Enter your math problem",
        height=110,
        placeholder="e.g.  Find the derivative of x³·sin(x)\n     What is P(exactly 3 heads in 5 fair coin tosses)?\n     Solve: x² − 5x + 6 = 0",
        key="text_input",
    )
    if raw_text_typed.strip():
        raw_text = raw_text_typed
        input_type = "text"

with image_tab:
    uploaded_img = st.file_uploader(
        "Upload a photo or screenshot of a math problem",
        type=["jpg", "jpeg", "png"],
        key="img_upload",
    )
    if uploaded_img:
        col_img, col_preview = st.columns([1, 1])
        with col_img:
            st.image(uploaded_img, width="stretch")
        file_key = f"{uploaded_img.name}_{uploaded_img.size}"
        if st.session_state.get("_ocr_file_key") != file_key:
            with st.spinner("Extracting text from image…"):
                result = extract_from_bytes(uploaded_img.read(), uploaded_img.type)
            st.session_state["ocr_result"] = result
            st.session_state["_ocr_file_key"] = file_key
        with col_preview:
            result = st.session_state["ocr_result"]
            raw_text = render_extraction_preview(result, result.get("low_confidence", False))
        input_type = "image"

with audio_tab:
    audio_col1, audio_col2 = st.columns(2)
    audio_bytes = None
    audio_name = "audio.wav"

    with audio_col1:
        uploaded_audio = st.file_uploader(
            "Upload audio file",
            type=["mp3", "wav", "m4a"],
            key="audio_upload",
        )
        if uploaded_audio:
            audio_bytes = uploaded_audio.read()
            audio_name = uploaded_audio.name

    with audio_col2:
        if hasattr(st, "audio_input"):
            recorded = st.audio_input("Or record your question", key="audio_record")
            if recorded:
                audio_bytes = recorded.read()
                audio_name = "recording.wav"
        else:
            st.info("Audio recording requires Streamlit >= 1.40")

    if audio_bytes:
        file_key = f"audio_{len(audio_bytes)}"
        if st.session_state.get("_asr_file_key") != file_key:
            with st.spinner("Transcribing audio…"):
                result = transcribe_bytes(audio_bytes, audio_name)
            st.session_state["asr_result"] = result
            st.session_state["_asr_file_key"] = file_key
        result = st.session_state["asr_result"]
        raw_text = render_extraction_preview(result, result.get("low_confidence", False))
        input_type = "audio"

# ── Action buttons ───────────────────────────────────────────────────────────
st.markdown("")  # spacing
btn_cols = st.columns([1, 1, 4])
with btn_cols[0]:
    solve_clicked = st.button("🔍  Solve", type="primary", disabled=not raw_text.strip(),
                              width="stretch")
with btn_cols[1]:
    recheck_clicked = st.button("🔄  Re-check", disabled=not st.session_state.get("state"),
                                width="stretch",
                                help="Re-run the solver on the same question")

if (solve_clicked or recheck_clicked) and raw_text.strip():
    st.session_state["solving"] = True
    st.session_state["raw_text"] = raw_text
    st.session_state["input_type"] = input_type
    st.session_state["conf_threshold"] = conf_threshold
    for key in ("state", "row_id", "_feedback_given"):
        st.session_state.pop(key, None)

# ── Run agent graph ──────────────────────────────────────────────────────────
if st.session_state.get("solving"):
    raw_text_to_solve = st.session_state["raw_text"]
    solve_input_type = st.session_state["input_type"]

    with st.status("Running agents…", expanded=True) as status:
        state = run_graph(
            raw_text_to_solve, solve_input_type,
            confidence_threshold=st.session_state.get("conf_threshold", conf_threshold),
        )
        status.update(label="Done!", state="complete")

    st.session_state["state"] = state
    st.session_state["solving"] = False

    if state.get("solution"):
        row_id = save_attempt(
            solve_input_type, raw_text_to_solve,
            state.get("parsed") or {}, state.get("rag_chunks") or [],
            state["solution"], state.get("verification") or {},
        )
        st.session_state["row_id"] = row_id

# ── Results ──────────────────────────────────────────────────────────────────
state = st.session_state.get("state")
if state:
    st.markdown("---")

    # HITL banner
    if state.get("hitl_required"):
        corrected = render_hitl_panel(state.get("hitl_reason", "Review needed"))
        if corrected:
            st.session_state["raw_text"] = corrected
            st.session_state["solving"] = True
            st.rerun()

    # Memory reuse badge
    if state.get("memory_examples"):
        st.info("🧠  Similar problem found in memory — solution pattern reused.")

    # Main answer card (full width)
    if state.get("explanation"):
        render_answer_card(state)

    # Collapsible panels for trace + sources
    detail_col1, detail_col2 = st.columns(2)
    with detail_col1:
        if state.get("agent_trace"):
            render_agent_trace(state["agent_trace"])
    with detail_col2:
        if state.get("rag_chunks"):
            render_rag_panel(state["rag_chunks"])

    # Feedback
    if state.get("solution"):
        render_feedback_row(st.session_state.get("row_id"))
