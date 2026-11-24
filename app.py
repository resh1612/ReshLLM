import os
import streamlit as st
from datetime import datetime

import assistant
import chat_storage

# =====================================================================
# PAGE CONFIGURATION & STYLING
# =====================================================================

st.set_page_config(
    page_title="ReshLLM",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Ensure chat storage directory exists
chat_storage.ensure_history_dir()

# =====================================================================
# SESSION STATE MANAGEMENT
# =====================================================================

# Load or initialize active session ID
if "current_session_id" not in st.session_state:
    all_sessions = chat_storage.list_sessions()
    if all_sessions:
        st.session_state.current_session_id = all_sessions[0]["id"]
    else:
        new_sess = chat_storage.create_session("New Chat")
        st.session_state.current_session_id = new_sess["id"]

current_session = chat_storage.load_session(st.session_state.current_session_id)
if not current_session:
    # Fallback if file was deleted externally
    current_session = chat_storage.create_session("New Chat")
    st.session_state.current_session_id = current_session["id"]

# =====================================================================
# SIDEBAR: NAVIGATION, SESSIONS & SETTINGS
# =====================================================================

with st.sidebar:
    st.markdown("""
        <div class="sidebar-header">
            <span>🤖</span>
            <span>ReshLLM</span>
        </div>
        <div class="model-badge">
            <span class="model-dot"></span>
            <span>qwen2.5:1.5b · Ollama Local</span>
        </div>
    """, unsafe_allow_html=True)

    # New Chat Action Button
    if st.button("➕  New Chat", use_container_width=True, type="primary"):
        new_sess = chat_storage.create_session("New Chat")
        st.session_state.current_session_id = new_sess["id"]
        st.session_state.pop("pending_prompt", None)
        st.rerun()

    st.markdown("### Conversations")
    sessions_list = chat_storage.list_sessions()

    # Session list with selection and deletion
    if sessions_list:
        for s in sessions_list:
            s_id = s["id"]
            is_active = (s_id == st.session_state.current_session_id)
            col_sess, col_del = st.columns([0.84, 0.16])

            with col_sess:
                button_label = f"💬  {s['title']}"
                if is_active:
                    button_label = f"👉  {s['title']}"

                if st.button(
                    button_label,
                    key=f"sess_{s_id}",
                    use_container_width=True,
                    type="secondary" if not is_active else "primary"
                ):
                    st.session_state.current_session_id = s_id
                    st.rerun()

            with col_del:
                if st.button("🗑️", key=f"del_{s_id}", help="Delete chat"):
                    chat_storage.delete_session(s_id)
                    # If active session was deleted, select next available or create new
                    if s_id == st.session_state.current_session_id:
                        remaining = chat_storage.list_sessions()
                        if remaining:
                            st.session_state.current_session_id = remaining[0]["id"]
                        else:
                            fresh = chat_storage.create_session("New Chat")
                            st.session_state.current_session_id = fresh["id"]
                    st.rerun()
    else:
        st.caption("No conversations yet.")

    st.divider()

    # Current Chat Actions
    if st.button("🧹  Clear Current Messages", use_container_width=True):
        chat_storage.clear_session_messages(st.session_state.current_session_id)
        st.rerun()

    # Settings Section
    with st.expander("⚙️  Settings & Search", expanded=False):
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.2,
            step=0.05,
            help="Lower values produce more deterministic answers. Higher values make responses more creative."
        )
        max_tokens = st.slider(
            "Max Response Tokens",
            min_value=256,
            max_value=1500,
            value=700,
            step=64,
            help="Maximum token generation limit for Ollama."
        )
        search_mode = st.selectbox(
            "Web Search Mode",
            options=["auto", "always", "offline"],
            format_func=lambda x: {
                "auto": "Auto-Detect (Smart DDGS)",
                "always": "Always Search Web",
                "offline": "Offline (Local AI Only)"
            }[x],
            help="Controls when the assistant queries live search via DDGS."
        )

    st.caption("Hardware: Local Qwen 1.5B · Windows 11")

# =====================================================================
# MAIN CHAT INTERFACE
# =====================================================================

messages = current_session.get("messages", [])

# Handle prompt if user clicked a suggestion card
prompt_to_process = None
if "pending_prompt" in st.session_state:
    prompt_to_process = st.session_state.pop("pending_prompt")

# Welcome Hero & Suggested Prompts (when no messages exist)
if not messages and not prompt_to_process:
    st.markdown("""
        <div class="welcome-container">
            <h1 class="welcome-title">What can I help you with?</h1>
            <div class="welcome-subtitle">Ask general knowledge, debug Python code, or query live web news with ReshLLM.</div>
        </div>
    """, unsafe_allow_html=True)

    # 2x2 Interactive Suggested Prompts Grid
    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "🐍  Write a Python program\n\nCreate a script to organize files by extension.",
            key="suggest_python",
            use_container_width=True
        ):
            st.session_state.pending_prompt = "Write a Python script to organize files in a directory by their extension and explain how it works."
            st.rerun()

        if st.button(
            "💡  Explain a concept\n\nExplain Python's asyncio event loop simply.",
            key="suggest_concept",
            use_container_width=True
        ):
            st.session_state.pending_prompt = "Explain how Python's asyncio event loop works with a simple code example."
            st.rerun()

    with col2:
        if st.button(
            "🐛  Debug my Python code\n\nFix a KeyError or TypeError in dictionary access.",
            key="suggest_debug",
            use_container_width=True
        ):
            st.session_state.pending_prompt = "How do I safely handle KeyError and TypeError when navigating nested Python dictionaries?"
            st.rerun()

        if st.button(
            "📰  Summarize today's news\n\nWhat are major Indian and tech news headlines?",
            key="suggest_news",
            use_container_width=True
        ):
            st.session_state.pending_prompt = "What are the latest major news headlines today in India?"
            st.rerun()

# Render Existing Conversation Messages
for msg in messages:
    role = msg.get("role", "assistant")
    content = msg.get("content", "")
    sources = msg.get("sources", [])

    with st.chat_message(role):
        # If this assistant message used web search sources, show the sources expander
        if role == "assistant" and sources:
            with st.expander(f"🌐 Web Sources ({len(sources)} results)", expanded=False):
                for s_item in sources:
                    title = s_item.get("title", "Untitled")
                    url = s_item.get("url", "#")
                    source = s_item.get("source", "Web")
                    date = s_item.get("date", "")
                    date_info = f" · {date[:10]}" if date else ""
                    st.markdown(f"- [{title}]({url}) — *{source}*{date_info}")

        st.markdown(content)

# Input Field at Bottom
chat_input_text = st.chat_input("Message ReshLLM... (Shift+Enter for new line)")
if chat_input_text:
    prompt_to_process = chat_input_text

# =====================================================================
# PROCESS USER INPUT & STREAM AI RESPONSE
# =====================================================================

if prompt_to_process:
    user_prompt = prompt_to_process.strip()

    if user_prompt:
        now_iso = datetime.now().isoformat()

        # Update session title if this is the first message
        if not messages or current_session.get("title") == "New Chat":
            new_title = chat_storage.auto_generate_title(user_prompt)
            current_session["title"] = new_title

        # 1. Append User Message
        user_msg = {
            "role": "user",
            "content": user_prompt,
            "timestamp": now_iso
        }
        messages.append(user_msg)
        current_session["messages"] = messages
        chat_storage.save_session(current_session)

        # 2. Render User Message on Screen
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # 3. Generate and Stream Assistant Response
        with st.chat_message("assistant"):
            try:
                # Prepare pipeline (evaluates date, search, or local AI)
                with st.spinner("Processing request..."):
                    pipeline = assistant.prepare_pipeline(
                        user_prompt,
                        search_mode=search_mode,
                        temperature=temperature,
                        num_predict=max_tokens
                    )

                response_type = pipeline.get("type")
                sources = pipeline.get("sources", [])

                # Render sources expander if search was used
                if sources:
                    query_label = pipeline.get("search_query", "Web")
                    with st.expander(f"🌐 Searched web for: *{query_label}* ({len(sources)} sources)", expanded=False):
                        for s_item in sources:
                            title = s_item.get("title", "Untitled")
                            url = s_item.get("url", "#")
                            source = s_item.get("source", "Web")
                            date = s_item.get("date", "")
                            date_info = f" · {date[:10]}" if date else ""
                            st.markdown(f"- [{title}]({url}) — *{source}*{date_info}")

                # Display Response Content
                if response_type == "date":
                    full_response = pipeline.get("direct_response", "")
                    st.markdown(full_response)
                elif pipeline.get("stream"):
                    # Real-time token streaming with st.write_stream
                    full_response = st.write_stream(pipeline["stream"])
                elif pipeline.get("error"):
                    full_response = f"⚠️ Error: {pipeline['error']}"
                    st.error(full_response)
                else:
                    full_response = "No response could be generated."
                    st.warning(full_response)

                # 4. Save Assistant Message and Persist to Disk
                assistant_msg = {
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": datetime.now().isoformat(),
                    "sources": sources
                }
                messages.append(assistant_msg)
                current_session["messages"] = messages
                chat_storage.save_session(current_session)

                st.rerun()

            except Exception as e:
                error_msg = f"An unexpected error occurred: {str(e)}"
                st.error(error_msg)
                messages.append({
                    "role": "assistant",
                    "content": f"⚠️ {error_msg}",
                    "timestamp": datetime.now().isoformat(),
                    "sources": []
                })
                current_session["messages"] = messages
                chat_storage.save_session(current_session)

