import os
import json
import uuid
import tempfile
from datetime import datetime

HISTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history")


def ensure_history_dir():
    """Ensure the chat_history directory exists."""
    os.makedirs(HISTORY_DIR, exist_ok=True)


def auto_generate_title(text, max_length=36):
    """Generate a clean, human-readable session title from the first prompt."""
    cleaned = " ".join(text.strip().split())
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[:max_length].rstrip() + "..."


def create_session(initial_title="New Chat"):
    """Create a new session object with a unique timestamped ID."""
    ensure_history_dir()
    now_iso = datetime.now().isoformat()
    session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    session = {
        "id": session_id,
        "title": initial_title,
        "created_at": now_iso,
        "updated_at": now_iso,
        "messages": []
    }
    save_session(session)
    return session


def get_session_file_path(session_id):
    """Return the absolute path to a session's JSON file."""
    # Sanitize session_id to prevent directory traversal
    safe_id = "".join(c for c in session_id if c.isalnum() or c in ("_", "-"))
    return os.path.join(HISTORY_DIR, f"{safe_id}.json")


def save_session(session):
    """
    Save session data to a JSON file atomically to prevent partial writes
    or corruption during interruptions.
    """
    ensure_history_dir()
    session_id = session.get("id")
    if not session_id:
        return False

    session["updated_at"] = datetime.now().isoformat()
    target_path = get_session_file_path(session_id)

    # Atomic write pattern: write to temporary file in same directory then replace
    try:
        temp_dir = HISTORY_DIR
        with tempfile.NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding="utf-8") as tf:
            json.dump(session, tf, indent=2, ensure_ascii=False)
            temp_path = tf.name

        os.replace(temp_path, target_path)
        return True
    except Exception as e:
        print(f"Error saving session {session_id}: {e}")
        return False


def load_session(session_id):
    """Load a session JSON file from disk."""
    ensure_history_dir()
    file_path = get_session_file_path(session_id)
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"Error loading session {session_id}: {e}")
        return None


def list_sessions():
    """
    List all saved sessions, sorted by last updated timestamp in descending order.
    Returns a list of metadata dicts: id, title, created_at, updated_at, message_count.
    """
    ensure_history_dir()
    sessions = []

    for filename in os.listdir(HISTORY_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(HISTORY_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sessions.append({
                        "id": data.get("id", filename[:-5]),
                        "title": data.get("title", "Untitled Chat"),
                        "created_at": data.get("created_at", ""),
                        "updated_at": data.get("updated_at", ""),
                        "message_count": len(data.get("messages", []))
                    })
            except Exception:
                continue

    sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
    return sessions


def delete_session(session_id):
    """Delete a session JSON file from disk."""
    file_path = get_session_file_path(session_id)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    return False


def clear_session_messages(session_id):
    """Clear all messages in a session while keeping the session file."""
    session = load_session(session_id)
    if session:
        session["messages"] = []
        session["title"] = "New Chat"
        save_session(session)
        return session
    return None

