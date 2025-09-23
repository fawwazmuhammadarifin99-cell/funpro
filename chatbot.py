import os
import time
import json
import uuid
import requests
import streamlit as st
from datetime import datetime

# =========================
# 🎨 PAGE & STYLES
# =========================
st.set_page_config(page_title="AI Chatbot Bubble Style", page_icon="🧠", layout="wide")

BUBBLE_CSS = """
<style>
/* Main wrappers */
.main-container {max-width: 1150px; margin: 0 auto;}
.chat-container {width:100%; max-width:860px; margin:0 auto; padding-bottom:18px;}

/* ==== Sidebar: rounded gradient card ==== */
.sidebar-card {
  background: linear-gradient(180deg, #5f60ff 0%, #7aa4ff 100%);
  color: #ffffff;
  padding: 16px 18px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0,0,0,.18);
  margin: 8px 6px 16px 6px;
}
.sidebar-card h3 { font-size: 22px; font-weight: 800; margin: 0 0 6px 0; }
.sidebar-card p { margin: 0; opacity: .95; }

/* Inputs rounded */
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stTextInput > div > div input,
[data-testid="stSidebar"] .stSlider > div {
  border-radius: 12px !important;
}

/* ===== Chat bubbles ===== */
.bubble {border-radius:16px; padding:12px 14px; margin:6px 0; display:inline-block; line-height:1.45; word-wrap:break-word; box-shadow:0 1px 1px rgba(0,0,0,0.04);}
.bubble-user {background:#ffecee; color:#111827; border:1px solid #ffd3d8;}
.bubble-ai {background:#f9fafb; color:#111827; border:1px solid #e5e7eb;}
.row {display:flex; gap:8px; align-items:flex-start;}
.row.user {justify-content:flex-start;}
.row.ai {justify-content:flex-start;}
.avatar {width:28px; height:28px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-size:14px; box-shadow:0 1px 2px rgba(0,0,0,.06);}
.avatar-user {background:#f87171; color:#fff;}
.avatar-ai {background:#e5e7eb; color:#111827;}
.typing {display:inline-flex; align-items:center; gap:8px; color:#6b7280; font-size:14px; padding:6px 8px; border-radius:9999px; border:1px solid #e5e7eb; background:#f9fafb; margin-top:8px;}
.dot{width:6px; height:6px; background:#9ca3af; border-radius:50%; animation:blink 1.4s infinite both;}
.dot:nth-child(1){animation-delay:0s;} .dot:nth-child(2){animation-delay:.2s;} .dot:nth-child(3){animation-delay:.4s;}
@keyframes blink{0%{opacity:.2;}20%{opacity:1;}100%{opacity:.2;}}
.powered {font-size:14px; color:#6b7280;}
.model-badge {font-weight:600; color:#10b981;}
.via-badge {font-weight:600; color:#111827;}
.header-title {font-size:40px; font-weight:800; letter-spacing:.3px;}
.chat-input-wrap {margin-top:18px;}

/* ===== Send row like ChatGPT ===== */
.send-row { position: relative; }
.send-row textarea {
  border-radius: 9999px !important;
  padding-right: 64px !important;
  min-height: 56px !important;
}
.send-btn .stButton>button {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 44px; height: 44px;
  border-radius: 9999px;
  background: #111111; color: #ffffff;
  border: none;
  font-size: 18px;
  box-shadow: 0 4px 12px rgba(0,0,0,.2);
}
.send-btn .stButton>button:hover { background: #000000; }
</style>
"""
st.markdown(BUBBLE_CSS, unsafe_allow_html=True)

# =========================
# 🔧 Helpers: conversation ops
# =========================
def _now_iso():
    return datetime.now().isoformat(timespec="seconds")

def _new_conv(title: str = "Percakapan Baru"):
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "created_at": _now_iso(),
        "messages": [
            {"role": "system", "content": "Kamu adalah asisten yang membantu dan sopan. Jawab dalam Bahasa Indonesia baku kecuali diminta lain."}
        ],
    }

def _ensure_state():
    if "conversations" not in st.session_state:
        first = _new_conv("Percakapan 1")
        st.session_state.conversations = {first["id"]: first}
        st.session_state.active_chat_id = first["id"]
    if "active_model" not in st.session_state:
        st.session_state.active_model = None

def _active_conv():
    return st.session_state.conversations[st.session_state.active_chat_id]

def _set_active(chat_id: str):
    if chat_id in st.session_state.conversations:
        st.session_state.active_chat_id = chat_id

def _create_new_chat():
    c = _new_conv(f"Percakapan {len(st.session_state.conversations)+1}")
    st.session_state.conversations[c["id"]] = c
    st.session_state.active_chat_id = c["id"]

def _delete_active_chat():
    if len(st.session_state.conversations) <= 1:
        st.warning("Minimal harus ada 1 chat.")
        return
    cid = st.session_state.active_chat_id
    ids = list(st.session_state.conversations.keys())
    idx = max(0, ids.index(cid)-1)
    st.session_state.conversations.pop(cid, None)
    st.session_state.active_chat_id = ids[idx] if ids[idx] in st.session_state.conversations else list(st.session_state.conversations.keys())[0]

def _rename_active_chat(new_title: str):
    if new_title.strip():
        st.session_state.conversations[st.session_state.active_chat_id]["title"] = new_title.strip()

def _append_msg(role, content):
    st.session_state.conversations[st.session_state.active_chat_id]["messages"].append({"role": role, "content": content})

def _visible_msgs(conv):
    return [m for m in conv["messages"] if m["role"] in ("user","assistant")]

def _auto_title_from_first_user(conv):
    try:
        first_user = next(m for m in conv["messages"] if m["role"] == "user")
        text = first_user["content"].strip().split("\n")[0][:40]
        if text:
            conv["title"] = text + ("…" if len(first_user["content"]) > 40 else "")
    except StopIteration:
        pass

# =========================
# ⚙️ STATE & MODEL LIST
# =========================
_ensure_state()

MODEL_OPTIONS = {
    "DeepSeek V3": "deepseek/deepseek-chat-v3-0324",
    "Mistral 7B": "mistralai/mistral-7b-instruct:free",
    "Grok 3 Mini": "x-ai/grok-3-mini",
    "Llama 3 70B": "meta-llama/llama-3.3-70b-instruct",
}

# === Callback: trigger regen when model changed ===
def _on_model_change():
    new_model_id = MODEL_OPTIONS[st.session_state.model_select]
    prev_model_id = st.session_state.get("active_model")
    conv = _active_conv() if "active_chat_id" in st.session_state else None
    has_assistant_last = bool(conv and conv["messages"] and conv["messages"][-1]["role"] == "assistant")
    if prev_model_id != new_model_id and has_assistant_last:
        st.session_state.regen_due_to_model_change = True
    st.session_state.active_model = new_model_id

# =========================
# ⚙️ SIDEBAR (API & Model) + HISTORY
# =========================
with st.sidebar:
    st.markdown("<div class='sidebar-card'><h3>Pengaturan Chatbot</h3><p>Pilih model terlebih dahulu.</p></div>", unsafe_allow_html=True)

    model_label = st.selectbox(
        "Pilih Model 🧠",
        list(MODEL_OPTIONS.keys()),
        index=0,
        key="model_select",
        on_change=_on_model_change
    )
    model_id = MODEL_OPTIONS[model_label]

    # First-load: set active model tanpa memicu regen
    if st.session_state.get("active_model") is None:
        st.session_state.active_model = model_id

    api_key = st.text_input("OpenRouter API Key", type="password", placeholder="sk-or-...", value=os.getenv("OPENROUTER_API_KEY", ""), key="api_key")
    max_tokens = st.slider("Max tokens", 128, 4096, 1024, 64, key="max_tokens")
    temperature = st.slider("Temperature", 0.0, 1.2, 0.7, 0.1, key="temperature")

    st.markdown("---")
    st.subheader("Riwayat Chat")

    conv_items = [(cid, c["title"]) for cid, c in st.session_state.conversations.items()]
    conv_items = sorted(conv_items, key=lambda x: st.session_state.conversations[x[0]]["created_at"])

    selected_title = st.radio(
        "Pilih percakapan",
        options=[t for _, t in conv_items],
        index=[t for _, t in conv_items].index(st.session_state.conversations[st.session_state.active_chat_id]["title"]) if conv_items else 0,
        label_visibility="collapsed",
    )
    for cid, title in conv_items:
        if title == selected_title:
            _set_active(cid)
            break

    colA, colB = st.columns(2)
    with colA:
        if st.button("➕ New Chat", use_container_width=True):
            _create_new_chat()
            st.rerun()
    with colB:
        if st.button("🗑️ Hapus Chat", use_container_width=True):
            _delete_active_chat()
            st.rerun()

    active = _active_conv()
    new_title = st.text_input("Ganti nama chat", value=active["title"])
    if st.button("Simpan Nama", use_container_width=True):
        _rename_active_chat(new_title)
        st.rerun()

    st.markdown("---")

# =========================
# 🔌 CALL OPENROUTER
# =========================
def call_openrouter(messages_payload, model_name: str, api_key_str: str, max_tokens: int, temperature: float):
    if not api_key_str:
        raise RuntimeError("API key belum diisi. Masukkan API key di sidebar.")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Content-Type":"application/json","Authorization":f"Bearer {api_key_str}"}
    body = {"model":model_name,"messages":messages_payload,"max_tokens":max_tokens,"temperature":temperature}
    r = requests.post(url, headers=headers, data=json.dumps(body), timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Gagal memanggil OpenRouter: {r.status_code} {r.text}")
    return r.json()["choices"][0]["message"]["content"]

# =========================
# 🧠 HEADER
# =========================
active_conv = _active_conv()
st.markdown(
    f"""
    <div class="main-container">
      <div class="header-title">🧠 AI Chatbot dengan OpenRouter API</div>
      <div class="powered">Model: <span class="model-badge">{model_label}</span> (<code>{MODEL_OPTIONS[model_label]}</code>)</div>
      <div class="powered">Chat aktif: <strong>{active_conv['title']}</strong> · <span style="opacity:.7">{active_conv['created_at']}</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================
# 💬 RENDER HISTORY (chat aktif)
# =========================
chat_box = st.container()
with chat_box:
    for msg in _visible_msgs(active_conv):
        is_user = msg["role"] == "user"
        avatar_class = "avatar-user" if is_user else "avatar-ai"
        avatar_text = "🧑" if is_user else "🤖"
        bubble_class = "bubble-user" if is_user else "bubble-ai"
        st.markdown(
            f"""
            <div class="row">
              <div class="avatar {avatar_class}">{avatar_text}</div>
              <div class="bubble {bubble_class}">{msg['content']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# =========================
# ⌨️ INPUT (ChatGPT-like: Enter=send, Shift+Enter=newline)
# =========================
st.markdown("<div class='chat-input-wrap send-row'>", unsafe_allow_html=True)
with st.form("chat-input", clear_on_submit=True):
    cols = st.columns([1, 0.0001])
    with cols[0]:
        user_text = st.text_area(
            "Tanyakan segalanya!",
            placeholder="pro tips: klik tombol ➤ atau tekan Enter untuk kirim",
            height=120,
            key="chat_textarea"
        )
    with cols[1]:
        st.markdown("<div class='send-btn'>", unsafe_allow_html=True)
        send_clicked = st.form_submit_button("➤", use_container_width=False)
        st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# JS: Enter to send (tanpa Shift)
st.components.v1.html(
    """
    <script>
    (function() {
      function findTA() {
        const tas = window.parent.document.querySelectorAll('textarea');
        for (const ta of tas) {
          if (ta.placeholder && ta.placeholder.includes('Enter untuk kirim')) return ta;
        }
        return null;
      }
      function findSendBtn() {
        const btns = window.parent.document.querySelectorAll('button');
        for (const b of btns) { if (b.innerText.trim() === '➤') return b; }
        return null;
      }
      function init() {
        const ta = findTA();
        const send = findSendBtn();
        if (!ta || !send) { setTimeout(init, 300); return; }
        if (ta._bound) return;
        ta._bound = true;
        ta.addEventListener('keydown', function(e) {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            send.click();
          }
        });
      }
      init();
    })();
    </script>
    """,
    height=0
)

if send_clicked and user_text and user_text.strip():
    _append_msg("user", user_text.strip())
    if len([m for m in active_conv["messages"] if m["role"] == "user"]) == 1:
        _auto_title_from_first_user(active_conv)
    st.rerun()

# =========================
# 🔁 REGENERATE LAST ANSWER WHEN MODEL CHANGES
# =========================
def regenerate_last_answer_for_new_model():
    conv = _active_conv()
    if not conv["messages"]:
        return False
    if conv["messages"][-1]["role"] != "assistant":
        return False

    payload = conv["messages"][:-1]
    with chat_box:
        typing_holder = st.empty()
        typing_holder.markdown(
            """
            <div class="typing">
              <span>●</span><span>Mengganti jawaban sesuai model…</span>
              <div class="dot"></div><div class="dot"></div><div class="dot"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        try:
            new_reply = call_openrouter(payload, MODEL_OPTIONS[st.session_state.model_select],
                                        st.session_state.api_key, st.session_state.max_tokens, st.session_state.temperature)
        except Exception as e:
            new_reply = f"Maaf, terjadi kesalahan: {e}"
        finally:
            typing_holder.empty()

        conv["messages"][-1]["content"] = new_reply
    return True

if st.session_state.get("regen_due_to_model_change"):
    st.session_state.regen_due_to_model_change = False
    if regenerate_last_answer_for_new_model():
        st.rerun()

# =========================
# ▶️ NORMAL GENERATION (kalau terakhir adalah user di chat aktif)
# =========================
active_conv = _active_conv()
if len(active_conv["messages"]) >= 2 and active_conv["messages"][-1]["role"] == "user":
    with chat_box:
        typing_holder = st.empty()
        typing_holder.markdown(
            """
            <div class="typing">
              <span>●</span>
              <span>Mengetik…</span>
              <div class="dot"></div><div class="dot"></div><div class="dot"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        try:
            assistant_reply = call_openrouter(active_conv["messages"],
                                              MODEL_OPTIONS[st.session_state.model_select],
                                              st.session_state.api_key,
                                              st.session_state.max_tokens,
                                              st.session_state.temperature)
        except Exception as e:
            assistant_reply = f"Maaf, terjadi kesalahan: {e}"
        finally:
            typing_holder.empty()

        placeholder = st.empty()
        shown = ""
        for ch in list(assistant_reply):
            shown += ch
            placeholder.markdown(
                f"""
                <div class="row">
                  <div class="avatar avatar-ai">🤖</div>
                  <div class="bubble bubble-ai">{shown}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            time.sleep(0.008)

        _append_msg("assistant", assistant_reply)
        time.sleep(0.02)
        st.rerun()
