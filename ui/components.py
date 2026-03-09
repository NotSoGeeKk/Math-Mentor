"""Reusable Streamlit UI components."""
from __future__ import annotations
from typing import Optional
import streamlit as st
from memory.store import update_feedback


def render_extraction_preview(result: dict, low_confidence_flag: bool = False) -> str:
    """Show OCR/ASR output with editable text area. Returns the (possibly edited) text."""
    if low_confidence_flag:
        st.warning("⚠️  Low confidence — please review and correct if needed.")
    text = st.text_area(
        "📋 Extracted text (you can edit before solving)",
        value=result.get("extracted_text") or result.get("processed_transcript", ""),
        height=90,
        key=f"extraction_preview_{id(result)}",
    )
    return text


def render_agent_trace(trace: list[dict]) -> None:
    with st.expander("🔍 Agent Trace — what ran and why", expanded=False):
        for step in trace:
            agent = step.get("agent", "Unknown")
            out = step.get("output", "")
            st.markdown(f"**{agent}**")
            if isinstance(out, dict):
                st.json(out)
            else:
                st.caption(str(out)[:300])
            st.divider()


def render_rag_panel(chunks: list[dict]) -> None:
    with st.expander(f"📚 Retrieved Sources ({len(chunks)} chunks)", expanded=False):
        for i, chunk in enumerate(chunks):
            source = chunk.get("source", "unknown")
            score = chunk.get("score", 0)
            st.markdown(f"**{source}** — relevance `{score}`")
            st.caption(chunk.get("text", ""))
            if i < len(chunks) - 1:
                st.divider()


def render_answer_card(state: dict) -> None:
    verification = state.get("verification") or {}
    solution = state.get("solution") or {}
    confidence = verification.get("confidence", 0)

    if confidence >= 0.8:
        conf_cls, conf_label = "conf-high", "High"
    elif confidence >= 0.6:
        conf_cls, conf_label = "conf-medium", "Medium"
    else:
        conf_cls, conf_label = "conf-low", "Low"

    final_answer = solution.get("final_answer", "N/A")

    st.markdown(f"""
<div class="answer-box">
    <h2>Answer</h2>
    <span class="conf-pill {conf_cls}">{conf_label} confidence — {confidence:.0%}</span>
    <div class="final" style="margin-top:0.6rem">{final_answer}</div>
</div>
""", unsafe_allow_html=True)

    # Solution steps as a clean numbered list
    steps = solution.get("solution_steps", [])
    if steps:
        with st.expander("📝 Solution Steps", expanded=False):
            for i, step in enumerate(steps, 1):
                st.markdown(f"**{i}.** {step}")

    # Explanation
    explanation = state.get("explanation", "")
    if explanation:
        st.markdown(explanation)

    # Verifier issues
    issues = verification.get("issues")
    if issues:
        st.warning("**Verifier notes:** " + " · ".join(issues))

    # Sources used
    sources = solution.get("sources_used", [])
    if sources:
        st.caption("📎 Sources used: " + ", ".join(sources))


def render_hitl_panel(reason: str) -> Optional[str]:
    """Render HITL banner. Returns corrected text if user submits, else None."""
    st.error(f"🚨  Human review required — {reason}")
    with st.form("hitl_form"):
        corrected = st.text_area(
            "Edit the problem and resubmit:",
            height=100,
            placeholder="Correct or clarify the problem statement here…",
        )
        submitted = st.form_submit_button("🔄 Resubmit", type="primary")
    return corrected if submitted and corrected.strip() else None


def render_feedback_row(row_id: Optional[int]) -> None:
    st.markdown("---")

    if st.session_state.get("_feedback_given"):
        fb = st.session_state["_feedback_given"]
        if fb == "correct":
            st.success("✅ Thanks! Saved to memory — this will improve future answers.")
        else:
            st.warning("❌ Noted — this answer won't be reused in future suggestions.")
        return

    st.markdown("**Was this helpful?**")
    cols = st.columns([1, 1, 3])
    with cols[0]:
        if st.button("👍  Correct", key="fb_correct", use_container_width=True):
            if row_id:
                update_feedback(row_id, "correct")
            st.session_state["_feedback_given"] = "correct"
            st.rerun()
    with cols[1]:
        if st.button("👎  Wrong", key="fb_incorrect", use_container_width=True):
            if row_id:
                comment = st.session_state.get("fb_comment", "")
                update_feedback(row_id, "incorrect", comment)
            st.session_state["_feedback_given"] = "incorrect"
            st.rerun()
    with cols[2]:
        st.text_input("Optional comment", key="fb_comment", placeholder="What was wrong?",
                       label_visibility="collapsed")
